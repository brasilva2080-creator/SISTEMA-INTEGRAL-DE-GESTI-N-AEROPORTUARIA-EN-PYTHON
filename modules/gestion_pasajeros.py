"""Módulo de negocio para la gestión de pasajeros."""
from __future__ import annotations

import re
from sqlite3 import IntegrityError

from config import ahora
from database import Database
from models import Pasajero
from structures import ListaDoble, busqueda_lineal
from .actividad import Historial

SQL_PASAJERO = """
SELECT p.*,
       (SELECT COUNT(*) FROM reservas r WHERE r.pasajero_id = p.id) AS reservas
FROM pasajeros p
"""


class GestionPasajeros:
    """CRUD de pasajeros con índices por diccionario y búsquedas."""

    def __init__(self, db: Database, historial: Historial) -> None:
        self.db = db
        self.historial = historial
        self._cache_codigo: dict[str, Pasajero] = {}
        self._cache_documento: dict[str, Pasajero] = {}
        self._cache_id: dict[int, Pasajero] = {}
        self.refrescar_cache()

    def refrescar_cache(self) -> None:
        pasajeros = [Pasajero.desde_fila(fila) for fila in self.db.consultar(SQL_PASAJERO)]
        self._cache_codigo = {p.codigo.upper(): p for p in pasajeros}
        self._cache_documento = {p.documento.upper(): p for p in pasajeros}
        self._cache_id = {p.id: p for p in pasajeros}

    def listar(self, texto: str = "") -> list[Pasajero]:
        self.refrescar_cache()
        lista = ListaDoble(self._cache_id.values())
        texto = (texto or "").strip().lower()
        if texto:
            lista = lista.filtrar(lambda p: (
                texto in p.codigo.lower()
                or texto in p.nombre_completo.lower()
                or texto in p.documento.lower()
                or texto in p.email.lower()
            ))
        lista.ordenar(clave=lambda p: (p.apellidos.lower(), p.nombres.lower()))
        return lista.a_lista()

    def buscar_lineal(self, texto: str) -> Pasajero | None:
        """Búsqueda secuencial por código, nombre o documento."""
        texto = (texto or "").strip().lower()
        return busqueda_lineal(self.listar(), lambda p: (
            texto == p.codigo.lower()
            or texto == p.documento.lower()
            or texto in p.nombre_completo.lower()
        ))

    def obtener_por_codigo(self, codigo: str) -> Pasajero | None:
        codigo = (codigo or "").strip().upper()
        if codigo not in self._cache_codigo:
            self.refrescar_cache()
        return self._cache_codigo.get(codigo)

    def obtener_por_documento(self, documento: str) -> Pasajero | None:
        documento = (documento or "").strip().upper()
        if documento not in self._cache_documento:
            self.refrescar_cache()
        return self._cache_documento.get(documento)

    def obtener(self, pasajero_id: int) -> Pasajero | None:
        if pasajero_id not in self._cache_id:
            self.refrescar_cache()
        return self._cache_id.get(pasajero_id)

    def generar_codigo(self) -> str:
        filas = self.db.consultar("SELECT codigo FROM pasajeros WHERE codigo LIKE 'PAS-%'")
        numeros: set[int] = set()
        for fila in filas:
            sufijo = str(fila["codigo"]).split("-")[-1]
            if sufijo.isdigit():
                numeros.add(int(sufijo))
        numero = 1
        while numero in numeros:
            numero += 1
        return f"PAS-{numero:04d}"

    def _validar(self, nombres: str, apellidos: str, documento: str,
                 email: str, telefono: str) -> tuple[str, str, str, str, str]:
        nombres = (nombres or "").strip()
        apellidos = (apellidos or "").strip()
        documento = (documento or "").strip().upper()
        email = (email or "").strip().lower()
        telefono = (telefono or "").strip()
        if len(nombres) < 2 or len(apellidos) < 2:
            raise ValueError("Nombres y apellidos son obligatorios.")
        if len(nombres) > 60 or len(apellidos) > 60:
            raise ValueError("Nombres y apellidos no pueden superar 60 caracteres.")
        if not re.fullmatch(r"[A-Z0-9\-]{6,15}", documento):
            raise ValueError("El documento debe tener entre 6 y 15 caracteres alfanuméricos.")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Ingresa un correo electrónico válido.")
        if not re.fullmatch(r"\+?[0-9\s\-]{6,18}", telefono):
            raise ValueError("Ingresa un teléfono válido (6 a 18 caracteres).")
        return nombres, apellidos, documento, email, telefono

    def registrar(self, nombres: str, apellidos: str, documento: str,
                  email: str, telefono: str) -> Pasajero:
        nombres, apellidos, documento, email, telefono = self._validar(
            nombres, apellidos, documento, email, telefono
        )
        if self.obtener_por_documento(documento):
            raise ValueError("Ya existe un pasajero con ese documento.")
        codigo = self.generar_codigo()
        try:
            with self.db.transaccion():
                cursor = self.db.ejecutar(
                    "INSERT INTO pasajeros(codigo, nombres, apellidos, documento, email, "
                    "telefono, creado_en) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (codigo, nombres, apellidos, documento, email, telefono,
                     ahora().strftime("%Y-%m-%d %H:%M:%S")),
                )
                pasajero_id = int(cursor.lastrowid)
        except IntegrityError as exc:
            raise ValueError("El documento o código de pasajero ya está registrado.") from exc

        self.refrescar_cache()
        pasajero = self.obtener(pasajero_id)
        assert pasajero is not None

        def deshacer() -> None:
            reservas = self.db.escalar(
                "SELECT COUNT(*) FROM reservas WHERE pasajero_id = ?", (pasajero_id,)
            )
            if reservas:
                raise ValueError("No se puede deshacer: el pasajero ya tiene reservas.")
            self.db.ejecutar("DELETE FROM pasajeros WHERE id = ?", (pasajero_id,))
            self.refrescar_cache()

        self.historial.registrar(
            "Pasajero", f"Pasajero {codigo} registrado ({pasajero.nombre_completo})",
            deshacer, f"id={pasajero_id}",
        )
        return pasajero

    def actualizar(self, pasajero_id: int, nombres: str, apellidos: str,
                   documento: str, email: str, telefono: str) -> Pasajero:
        anterior = self.obtener(pasajero_id)
        if not anterior:
            raise ValueError("El pasajero seleccionado no existe.")
        nombres, apellidos, documento, email, telefono = self._validar(
            nombres, apellidos, documento, email, telefono
        )
        duplicado = self.obtener_por_documento(documento)
        if duplicado and duplicado.id != pasajero_id:
            raise ValueError("Ese documento pertenece a otro pasajero.")
        snapshot = dict(self.db.consultar_uno(
            "SELECT nombres, apellidos, documento, email, telefono FROM pasajeros WHERE id = ?",
            (pasajero_id,),
        ))
        try:
            self.db.ejecutar(
                "UPDATE pasajeros SET nombres=?, apellidos=?, documento=?, email=?, telefono=? "
                "WHERE id=?", (nombres, apellidos, documento, email, telefono, pasajero_id),
            )
        except IntegrityError as exc:
            raise ValueError("No se pudo actualizar: el documento ya está en uso.") from exc
        self.refrescar_cache()

        def deshacer() -> None:
            self.db.ejecutar(
                "UPDATE pasajeros SET nombres=?, apellidos=?, documento=?, email=?, telefono=? "
                "WHERE id=?",
                (snapshot["nombres"], snapshot["apellidos"], snapshot["documento"],
                 snapshot["email"], snapshot["telefono"], pasajero_id),
            )
            self.refrescar_cache()

        self.historial.registrar(
            "Pasajero", f"Pasajero {anterior.codigo} actualizado", deshacer,
            f"id={pasajero_id}",
        )
        actualizado = self.obtener(pasajero_id)
        assert actualizado is not None
        return actualizado

    def historial_reservas(self, pasajero_id: int) -> list[dict]:
        filas = self.db.consultar(
            "SELECT r.codigo, r.asiento, r.precio, r.estado, r.fecha_reserva, "
            "v.codigo AS vuelo, v.fecha_salida, o.codigo AS origen, d.codigo AS destino, "
            "CASE WHEN c.id IS NULL THEN 'Sin check-in' ELSE 'Check-in realizado' END AS checkin "
            "FROM reservas r "
            "JOIN vuelos v ON v.id = r.vuelo_id "
            "JOIN aeropuertos o ON o.id = v.origen_id "
            "JOIN aeropuertos d ON d.id = v.destino_id "
            "LEFT JOIN checkins c ON c.reserva_id = r.id "
            "WHERE r.pasajero_id = ? ORDER BY v.fecha_salida DESC",
            (pasajero_id,),
        )
        return [dict(fila) for fila in filas]
