"""Check-in, equipaje y tarjetas de embarque."""
from __future__ import annotations

import secrets
import string
from pathlib import Path

from config import APP_NAME, COMPROBANTES_DIR, ahora, fecha_humana
from database import Database
from models import RegistroCheckin, Reserva
from .actividad import Historial
from .gestion_vuelos import GestionVuelos
from .reservas import Reservas

SQL_CHECKIN = """
SELECT c.*, r.codigo AS reserva_codigo, r.asiento,
       p.nombres || ' ' || p.apellidos AS pasajero, p.documento,
       v.id AS vuelo_id, v.codigo AS vuelo_codigo,
       o.codigo || ' → ' || d.codigo AS ruta,
       v.puerta, v.fecha_salida,
       CASE WHEN a.id IS NULL THEN 0 ELSE 1 END AS abordado,
       CASE WHEN q.id IS NULL THEN 0 ELSE 1 END AS en_cola
FROM checkins c
JOIN reservas r ON r.id = c.reserva_id
JOIN pasajeros p ON p.id = r.pasajero_id
JOIN vuelos v ON v.id = r.vuelo_id
JOIN aeropuertos o ON o.id = v.origen_id
JOIN aeropuertos d ON d.id = v.destino_id
LEFT JOIN abordajes a ON a.reserva_id = r.id
LEFT JOIN cola_abordaje q ON q.reserva_id = r.id AND q.estado = 'En cola'
"""


class Checkin:
    """Registro de check-in y equipaje con validaciones de reserva."""

    def __init__(self, db: Database, historial: Historial,
                 reservas: Reservas, vuelos: GestionVuelos) -> None:
        self.db = db
        self.historial = historial
        self.reservas = reservas
        self.vuelos = vuelos

    def buscar_reserva(self, codigo: str) -> Reserva | None:
        return self.reservas.obtener_por_codigo(codigo)

    def obtener_por_reserva(self, reserva_id: int) -> RegistroCheckin | None:
        fila = self.db.consultar_uno(SQL_CHECKIN + " WHERE c.reserva_id = ?", (reserva_id,))
        return RegistroCheckin.desde_fila(fila) if fila else None

    def listar(self, texto: str = "", vuelo_id: int | None = None) -> list[RegistroCheckin]:
        filas = self.db.consultar(SQL_CHECKIN + " ORDER BY c.fecha_checkin DESC, c.id DESC")
        checkins = [RegistroCheckin.desde_fila(fila) for fila in filas]
        texto = (texto or "").strip().lower()
        if texto:
            checkins = [c for c in checkins if (
                texto in c.tarjeta_embarque.lower() or texto in c.pasajero.lower()
                or texto in c.reserva_codigo.lower() or texto in c.documento.lower()
                or texto in c.vuelo_codigo.lower()
            )]
        if vuelo_id is not None:
            checkins = [c for c in checkins if c.vuelo_id == vuelo_id]
        return checkins

    @staticmethod
    def _generar_tarjeta() -> str:
        alfabeto = string.ascii_uppercase + string.digits
        return "TB-" + "".join(secrets.choice(alfabeto) for _ in range(7))

    def _tarjeta_unica(self) -> str:
        for _ in range(20):
            codigo = self._generar_tarjeta()
            if not self.db.consultar_uno(
                "SELECT 1 FROM checkins WHERE tarjeta_embarque = ?", (codigo,)
            ):
                return codigo
        raise ValueError("No se pudo generar un código único de tarjeta de embarque.")

    def registrar(self, codigo_reserva: str, cantidad_equipaje,
                  peso_total) -> RegistroCheckin:
        reserva = self.buscar_reserva(codigo_reserva)
        if not reserva:
            raise ValueError("No existe una reserva con ese código.")
        if reserva.estado != "Confirmada":
            raise ValueError(
                f"La reserva está en estado '{reserva.estado}'. Solo se admite check-in de reservas confirmadas."
            )
        if reserva.estado_vuelo in ("Cancelado", "Completado", "En vuelo"):
            raise ValueError("El vuelo ya no permite realizar check-in.")
        if reserva.checkin_realizado:
            raise ValueError("Esta reserva ya tiene check-in registrado.")
        try:
            cantidad = int(cantidad_equipaje)
            peso = round(float(str(peso_total).replace(",", ".")), 2)
        except (TypeError, ValueError) as exc:
            raise ValueError("La cantidad y el peso del equipaje deben ser numéricos.") from exc
        if cantidad < 0 or cantidad > 10:
            raise ValueError("La cantidad de equipaje debe estar entre 0 y 10 piezas.")
        if cantidad == 0:
            if peso < 0:
                raise ValueError("El peso del equipaje no puede ser negativo.")
            if peso > 0:
                raise ValueError("Si no registras piezas, el peso del equipaje debe ser 0.")
            peso = 0.0
        else:
            if peso <= 0:
                raise ValueError("Indica el peso total del equipaje.")
            if peso > cantidad * 32:
                raise ValueError(f"El peso máximo permitido es 32 kg por pieza ({cantidad * 32} kg).")
        if peso > 0 and peso < cantidad * 0.5:
            raise ValueError("El peso ingresado no es coherente con la cantidad de piezas.")

        tarjeta = self._tarjeta_unica()
        sello = ahora().strftime("%Y-%m-%d %H:%M:%S")
        estado_vuelo_anterior = reserva.estado_vuelo
        try:
            with self.db.transaccion():
                cursor = self.db.ejecutar(
                    "INSERT INTO checkins(reserva_id, tarjeta_embarque, cantidad_equipaje, "
                    "peso_total, fecha_checkin) VALUES (?, ?, ?, ?, ?)",
                    (reserva.id, tarjeta, cantidad, peso, sello),
                )
                checkin_id = int(cursor.lastrowid)
                if cantidad > 0:
                    self.db.ejecutar(
                        "INSERT INTO equipajes(checkin_id, cantidad, peso_total, descripcion) "
                        "VALUES (?, ?, ?, 'Equipaje facturado')",
                        (checkin_id, cantidad, peso),
                    )
                if estado_vuelo_anterior == "Programado":
                    self.db.ejecutar(
                        "UPDATE vuelos SET estado='Check-in abierto', actualizado_en=? WHERE id=?",
                        (sello, reserva.vuelo_id),
                    )
        except Exception as exc:
            if "UNIQUE" in str(exc).upper():
                raise ValueError("La reserva ya tiene check-in o la tarjeta ya existe.") from exc
            raise
        self.vuelos.refrescar_cache()
        checkin = self.obtener_por_reserva(reserva.id)
        assert checkin is not None

        def deshacer() -> None:
            bloqueo = self.db.consultar_uno(
                "SELECT 1 FROM abordajes WHERE reserva_id = ? UNION "
                "SELECT 1 FROM cola_abordaje WHERE reserva_id = ? AND estado='En cola'",
                (reserva.id, reserva.id),
            )
            if bloqueo:
                raise ValueError("No se puede deshacer: el pasajero ya está en abordaje.")
            with self.db.transaccion():
                self.db.ejecutar("DELETE FROM equipajes WHERE checkin_id = ?", (checkin_id,))
                self.db.ejecutar("DELETE FROM checkins WHERE id = ?", (checkin_id,))
                if estado_vuelo_anterior == "Programado":
                    restantes = self.db.escalar(
                        "SELECT COUNT(*) FROM checkins c JOIN reservas r ON r.id=c.reserva_id "
                        "WHERE r.vuelo_id = ?", (reserva.vuelo_id,),
                    )
                    if not restantes:
                        self.db.ejecutar(
                            "UPDATE vuelos SET estado='Programado' WHERE id=?", (reserva.vuelo_id,)
                        )
            self.vuelos.refrescar_cache()

        self.historial.registrar(
            "Check-in", f"Check-in {tarjeta} · reserva {reserva.codigo} · asiento {reserva.asiento}",
            deshacer, f"id={checkin_id}, reserva={reserva.id}",
        )
        return checkin

    def tarjeta_embarque(self, codigo_reserva: str) -> tuple[str, Path, RegistroCheckin]:
        reserva = self.buscar_reserva(codigo_reserva)
        if not reserva:
            raise ValueError("No existe una reserva con ese código.")
        checkin = self.obtener_por_reserva(reserva.id)
        if not checkin:
            raise ValueError("La reserva todavía no tiene check-in.")
        lineas = [
            "=" * 58,
            f"{APP_NAME.upper()} · TARJETA DE EMBARQUE",
            "=" * 58,
            f"Pasajero      : {checkin.pasajero}",
            f"Documento     : {checkin.documento}",
            f"Vuelo         : {checkin.vuelo_codigo}",
            f"Ruta          : {checkin.ruta}",
            f"Salida        : {fecha_humana(checkin.fecha_salida)}",
            f"Puerta        : {checkin.puerta}",
            f"Asiento       : {checkin.asiento}",
            f"Tarjeta       : {checkin.tarjeta_embarque}",
            f"Equipaje      : {checkin.cantidad_equipaje} pieza(s) · {checkin.peso_total:.1f} kg",
            "-" * 58,
            "Preséntate en la puerta 30 minutos antes de la salida.",
            "Documento de simulación académica.",
            "=" * 58,
        ]
        texto = "\n".join(lineas)
        destino = COMPROBANTES_DIR / f"TARJETA_{checkin.tarjeta_embarque}.txt"
        destino.write_text(texto, encoding="utf-8")
        return texto, destino, checkin
