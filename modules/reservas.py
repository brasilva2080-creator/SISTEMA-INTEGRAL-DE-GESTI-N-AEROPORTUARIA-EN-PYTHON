"""Reservas, venta de boletos y mapa de asientos."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from sqlite3 import IntegrityError

from config import (APP_NAME, COMPROBANTES_DIR, ahora, dinero, fecha_humana,
                    generar_asientos, letras_asientos)
from database import Database
from models import Pasajero, Reserva, Vuelo
from structures import ListaDoble
from .actividad import Historial
from .gestion_pasajeros import GestionPasajeros
from .gestion_vuelos import GestionVuelos

SQL_RESERVA = """
SELECT r.*, p.codigo AS pasajero_codigo,
       p.nombres || ' ' || p.apellidos AS pasajero_nombre,
       p.documento, v.codigo AS vuelo_codigo,
       o.codigo AS origen_codigo, d.codigo AS destino_codigo,
       v.fecha_salida, v.puerta, v.estado AS estado_vuelo,
       c.id AS checkin_id, c.tarjeta_embarque,
       CASE WHEN a.id IS NULL THEN 0 ELSE 1 END AS abordado
FROM reservas r
JOIN pasajeros p ON p.id = r.pasajero_id
JOIN vuelos v ON v.id = r.vuelo_id
JOIN aeropuertos o ON o.id = v.origen_id
JOIN aeropuertos d ON d.id = v.destino_id
LEFT JOIN checkins c ON c.reserva_id = r.id
LEFT JOIN abordajes a ON a.reserva_id = r.id
"""


@dataclass(slots=True)
class MapaAsientos:
    vuelo: Vuelo
    columnas: int
    filas: int
    asientos: list[str]
    estados: dict[str, str]

    @property
    def disponibles(self) -> int:
        return sum(1 for estado in self.estados.values() if estado == "Disponible")


class Reservas:
    """Reglas de negocio para reservas, asientos y comprobantes."""

    def __init__(self, db: Database, historial: Historial,
                 vuelos: GestionVuelos, pasajeros: GestionPasajeros) -> None:
        self.db = db
        self.historial = historial
        self.vuelos = vuelos
        self.pasajeros = pasajeros

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def listar(self, texto: str = "", estado: str = "",
               vuelo_id: int | None = None) -> list[Reserva]:
        filas = self.db.consultar(SQL_RESERVA + " ORDER BY r.fecha_reserva DESC, r.id DESC")
        lista = ListaDoble([Reserva.desde_fila(fila) for fila in filas])
        texto = (texto or "").strip().lower()
        if texto:
            lista = lista.filtrar(lambda r: (
                texto in r.codigo.lower()
                or texto in r.pasajero_nombre.lower()
                or texto in r.documento.lower()
                or texto in r.vuelo_codigo.lower()
                or texto in r.ruta.lower()
            ))
        if estado:
            lista = lista.filtrar(lambda r: r.estado == estado)
        if vuelo_id is not None:
            lista = lista.filtrar(lambda r: r.vuelo_id == vuelo_id)
        return lista.a_lista()

    def obtener_por_codigo(self, codigo: str) -> Reserva | None:
        fila = self.db.consultar_uno(
            SQL_RESERVA + " WHERE r.codigo = ? COLLATE NOCASE",
            ((codigo or "").strip().upper(),),
        )
        return Reserva.desde_fila(fila) if fila else None

    def obtener_por_id(self, reserva_id: int) -> Reserva | None:
        fila = self.db.consultar_uno(SQL_RESERVA + " WHERE r.id = ?", (reserva_id,))
        return Reserva.desde_fila(fila) if fila else None

    def generar_codigo(self) -> str:
        filas = self.db.consultar("SELECT codigo FROM reservas WHERE codigo LIKE 'RES-%'")
        numeros: set[int] = set()
        for fila in filas:
            sufijo = str(fila["codigo"]).split("-")[-1]
            if sufijo.isdigit():
                numeros.add(int(sufijo))
        numero = 100001
        while numero in numeros:
            numero += 1
        return f"RES-{numero}"

    def mapa_asientos(self, vuelo_id: int) -> MapaAsientos:
        vuelo = self.vuelos.obtener(vuelo_id)
        if not vuelo:
            raise ValueError("El vuelo seleccionado no existe.")
        asientos = generar_asientos(vuelo.capacidad, vuelo.asientos_por_fila)
        estados = {asiento: "Disponible" for asiento in asientos}
        filas = self.db.consultar(
            "SELECT asiento, estado FROM reservas "
            "WHERE vuelo_id = ? AND estado <> 'Cancelada'", (vuelo_id,),
        )
        for fila in filas:
            asiento = str(fila["asiento"]).upper()
            if asiento in estados:
                estados[asiento] = "Reservado" if fila["estado"] == "Pendiente" else "Ocupado"
        filas_visuales = math.ceil(vuelo.capacidad / max(1, vuelo.asientos_por_fila))
        return MapaAsientos(
            vuelo=vuelo, columnas=vuelo.asientos_por_fila,
            filas=filas_visuales, asientos=asientos, estados=estados,
        )

    def asientos_por_estado(self, vuelo_id: int) -> dict[str, int]:
        mapa = self.mapa_asientos(vuelo_id)
        resumen = {"Disponible": 0, "Reservado": 0, "Ocupado": 0}
        for estado in mapa.estados.values():
            resumen[estado] = resumen.get(estado, 0) + 1
        return resumen

    def reservas_confirmadas_sin_checkin(self, texto: str = "") -> list[Reserva]:
        filas = self.db.consultar(
            SQL_RESERVA +
            " WHERE r.estado = 'Confirmada' AND c.id IS NULL "
            "AND v.estado NOT IN ('Cancelado', 'Completado', 'En vuelo') "
            "ORDER BY v.fecha_salida, r.id"
        )
        reservas = [Reserva.desde_fila(fila) for fila in filas]
        texto = (texto or "").strip().lower()
        if texto:
            reservas = [r for r in reservas if (
                texto in r.codigo.lower() or texto in r.pasajero_nombre.lower()
                or texto in r.documento.lower() or texto in r.vuelo_codigo.lower()
            )]
        return reservas

    # ------------------------------------------------------------------
    # Validación
    # ------------------------------------------------------------------
    def _validar_para_venta(self, vuelo_id: int, pasajero_id: int, asiento: str) -> tuple[Vuelo, Pasajero, str]:
        vuelo = self.vuelos.obtener(vuelo_id)
        if not vuelo:
            raise ValueError("Selecciona un vuelo válido.")
        if vuelo.estado not in ("Programado", "Check-in abierto"):
            raise ValueError("El vuelo no está disponible para nuevas reservas.")
        if vuelo.fecha_dt < ahora() - timedelta(minutes=15):
            raise ValueError("No se puede reservar un vuelo cuya salida ya pasó.")
        pasajero = self.pasajeros.obtener(pasajero_id)
        if not pasajero:
            raise ValueError("Selecciona un pasajero válido.")
        if vuelo.ocupados >= vuelo.capacidad:
            raise ValueError("El vuelo alcanzó su capacidad máxima.")
        asiento = (asiento or "").strip().upper()
        asientos_validos = set(generar_asientos(vuelo.capacidad, vuelo.asientos_por_fila))
        if asiento not in asientos_validos:
            raise ValueError("Selecciona un asiento válido del mapa.")
        existente = self.db.consultar_uno(
            "SELECT 1 FROM reservas WHERE vuelo_id = ? AND asiento = ? "
            "AND estado <> 'Cancelada'", (vuelo_id, asiento),
        )
        if existente:
            raise ValueError(f"El asiento {asiento} ya está ocupado o reservado.")
        duplicada = self.db.consultar_uno(
            "SELECT 1 FROM reservas WHERE vuelo_id = ? AND pasajero_id = ? "
            "AND estado <> 'Cancelada'", (vuelo_id, pasajero_id),
        )
        if duplicada:
            raise ValueError("El pasajero ya tiene una reserva activa en este vuelo.")
        return vuelo, pasajero, asiento

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------
    def registrar(self, vuelo_id: int, pasajero_id: int, asiento: str,
                  confirmar: bool = True) -> Reserva:
        vuelo, pasajero, asiento = self._validar_para_venta(vuelo_id, pasajero_id, asiento)
        estado = "Confirmada" if confirmar else "Pendiente"
        codigo = self.generar_codigo()
        sello = ahora().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.db.transaccion():
                # Verificación final dentro de la transacción.
                ocupado = self.db.consultar_uno(
                    "SELECT 1 FROM reservas WHERE vuelo_id = ? AND asiento = ? "
                    "AND estado <> 'Cancelada'", (vuelo_id, asiento),
                )
                if ocupado:
                    raise ValueError(f"El asiento {asiento} acaba de ser ocupado.")
                cursor = self.db.ejecutar(
                    "INSERT INTO reservas(codigo, vuelo_id, pasajero_id, asiento, precio, "
                    "estado, fecha_reserva) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (codigo, vuelo_id, pasajero_id, asiento, vuelo.precio, estado, sello),
                )
                reserva_id = int(cursor.lastrowid)
        except IntegrityError as exc:
            raise ValueError(
                "No se pudo registrar: el asiento o el pasajero ya tienen una reserva activa."
            ) from exc
        self.vuelos.refrescar_cache()
        reserva = self.obtener_por_id(reserva_id)
        assert reserva is not None

        def deshacer() -> None:
            dependencias = self.db.escalar(
                "SELECT (SELECT COUNT(*) FROM checkins WHERE reserva_id = ?) + "
                "(SELECT COUNT(*) FROM abordajes WHERE reserva_id = ?)",
                (reserva_id, reserva_id),
            )
            if dependencias:
                raise ValueError("No se puede deshacer: la reserva ya tiene check-in o abordaje.")
            self.db.ejecutar("DELETE FROM reservas WHERE id = ?", (reserva_id,))
            self.vuelos.refrescar_cache()

        self.historial.registrar(
            "Reserva",
            f"Reserva {codigo} creada: {pasajero.nombre_completo} · {vuelo.codigo} · asiento {asiento}",
            deshacer, f"id={reserva_id}, vuelo={vuelo_id}",
        )
        return reserva

    def confirmar(self, reserva_id: int) -> Reserva:
        reserva = self.obtener_por_id(reserva_id)
        if not reserva:
            raise ValueError("La reserva no existe.")
        if reserva.estado == "Confirmada":
            raise ValueError("La reserva ya está confirmada.")
        if reserva.estado == "Cancelada":
            raise ValueError("No se puede confirmar una reserva cancelada.")
        vuelo = self.vuelos.obtener(reserva.vuelo_id)
        if not vuelo or vuelo.estado in ("Cancelado", "Completado", "En vuelo"):
            raise ValueError("El vuelo ya no permite confirmar reservas.")
        self.db.ejecutar("UPDATE reservas SET estado='Confirmada' WHERE id=?", (reserva_id,))

        def deshacer() -> None:
            checkin = self.db.escalar(
                "SELECT COUNT(*) FROM checkins WHERE reserva_id = ?", (reserva_id,)
            )
            if checkin:
                raise ValueError("No se puede volver a pendiente: ya se realizó el check-in.")
            self.db.ejecutar("UPDATE reservas SET estado='Pendiente' WHERE id=?", (reserva_id,))

        self.historial.registrar(
            "Reserva", f"Reserva {reserva.codigo} confirmada", deshacer,
            f"id={reserva_id}",
        )
        actualizada = self.obtener_por_id(reserva_id)
        assert actualizada is not None
        return actualizada

    def cancelar(self, reserva_id: int) -> Reserva:
        reserva = self.obtener_por_id(reserva_id)
        if not reserva:
            raise ValueError("La reserva no existe.")
        if reserva.estado == "Cancelada":
            raise ValueError("La reserva ya está cancelada.")
        if reserva.checkin_realizado:
            raise ValueError("No se puede cancelar una reserva con check-in realizado.")
        if reserva.abordado:
            raise ValueError("No se puede cancelar una reserva con abordaje registrado.")
        anterior = reserva.estado
        self.db.ejecutar("UPDATE reservas SET estado='Cancelada' WHERE id=?", (reserva_id,))
        self.vuelos.refrescar_cache()

        def deshacer() -> None:
            self.db.ejecutar("UPDATE reservas SET estado=? WHERE id=?", (anterior, reserva_id))
            self.vuelos.refrescar_cache()

        self.historial.registrar(
            "Reserva", f"Reserva {reserva.codigo} cancelada", deshacer,
            f"id={reserva_id}, anterior={anterior}",
        )
        cancelada = self.obtener_por_id(reserva_id)
        assert cancelada is not None
        return cancelada

    # ------------------------------------------------------------------
    # Documentos
    # ------------------------------------------------------------------
    def comprobante(self, codigo: str) -> tuple[str, Path]:
        reserva = self.obtener_por_codigo(codigo)
        if not reserva:
            raise ValueError("No existe la reserva indicada.")
        lineas = [
            "=" * 62,
            f"{APP_NAME.upper()} · COMPROBANTE DE RESERVA",
            "=" * 62,
            f"Código de reserva : {reserva.codigo}",
            f"Fecha de emisión  : {ahora().strftime('%d/%m/%Y %H:%M')}",
            f"Pasajero          : {reserva.pasajero_nombre}",
            f"Documento         : {reserva.documento}",
            "-" * 62,
            f"Vuelo             : {reserva.vuelo_codigo}",
            f"Ruta              : {reserva.ruta}",
            f"Salida            : {fecha_humana(reserva.fecha_salida)}",
            f"Puerta            : {reserva.puerta}",
            f"Asiento           : {reserva.asiento}",
            f"Tarifa            : {dinero(reserva.precio)}",
            f"Estado            : {reserva.estado}",
            "-" * 62,
            "Este comprobante simula una compra académica. No procesa pagos reales.",
            "Presenta tu documento y este código en el counter de check-in.",
            "=" * 62,
        ]
        texto = "\n".join(lineas)
        destino = COMPROBANTES_DIR / f"{reserva.codigo}.txt"
        destino.write_text(texto, encoding="utf-8")
        return texto, destino
