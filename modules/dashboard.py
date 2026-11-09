"""Servicio de métricas para el panel principal."""
from __future__ import annotations

from config import ESTADOS_VUELO
from database import Database
from .gestion_vuelos import GestionVuelos


class Dashboard:
    def __init__(self, db: Database, vuelos: GestionVuelos) -> None:
        self.db = db
        self.vuelos = vuelos

    def metricas(self) -> dict:
        total_vuelos = int(self.db.escalar("SELECT COUNT(*) FROM vuelos"))
        por_estado = {
            estado: int(self.db.escalar(
                "SELECT COUNT(*) FROM vuelos WHERE estado = ?", (estado,)
            ))
            for estado in ESTADOS_VUELO
        }
        total_pasajeros = int(self.db.escalar("SELECT COUNT(*) FROM pasajeros"))
        total_reservas = int(self.db.escalar("SELECT COUNT(*) FROM reservas"))
        reservas_confirmadas = int(self.db.escalar(
            "SELECT COUNT(*) FROM reservas WHERE estado = 'Confirmada'"
        ))
        pendientes_abordar = int(self.db.escalar(
            "SELECT COUNT(*) FROM reservas r JOIN vuelos v ON v.id = r.vuelo_id "
            "WHERE r.estado = 'Confirmada' "
            "AND v.estado IN ('Programado', 'Check-in abierto', 'Abordaje') "
            "AND NOT EXISTS (SELECT 1 FROM abordajes a WHERE a.reserva_id = r.id)"
        ))
        checkins = int(self.db.escalar("SELECT COUNT(*) FROM checkins"))
        proximas = self.vuelos.proximas_salidas(6)
        proxima = proximas[0] if proximas else None
        return {
            "total_vuelos": total_vuelos,
            "programados": por_estado["Programado"],
            "checkin": por_estado["Check-in abierto"],
            "abordaje": por_estado["Abordaje"],
            "en_vuelo": por_estado["En vuelo"],
            "completados": por_estado["Completado"],
            "cancelados": por_estado["Cancelado"],
            "total_pasajeros": total_pasajeros,
            "total_reservas": total_reservas,
            "reservas_confirmadas": reservas_confirmadas,
            "pendientes_abordar": pendientes_abordar,
            "checkins": checkins,
            "proxima": proxima,
        }

    def estados_vuelos(self) -> dict[str, int]:
        return {
            estado: int(self.db.escalar(
                "SELECT COUNT(*) FROM vuelos WHERE estado = ?", (estado,)
            ))
            for estado in ESTADOS_VUELO
        }

    def reservas_por_estado(self) -> dict[str, int]:
        return {
            estado: int(self.db.escalar(
                "SELECT COUNT(*) FROM reservas WHERE estado = ?", (estado,)
            ))
            for estado in ("Pendiente", "Confirmada", "Cancelada")
        }

    def ocupacion_vuelos(self, limite: int = 6) -> list[dict]:
        activos = [v for v in self.vuelos.proximas_salidas(limite + 2)
                   if v.estado not in ("Completado", "Cancelado", "En vuelo")]
        return [
            {
                "codigo": v.codigo,
                "ruta": v.ruta,
                "ocupados": v.ocupados,
                "capacidad": v.capacidad,
                "porcentaje": round(v.ocupados / v.capacidad * 100, 1) if v.capacidad else 0,
            }
            for v in activos[:limite]
        ]

    def proximas_salidas(self, limite: int = 6):
        return self.vuelos.proximas_salidas(limite)
