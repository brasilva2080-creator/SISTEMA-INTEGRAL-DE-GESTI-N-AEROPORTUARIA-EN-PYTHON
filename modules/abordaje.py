"""Proceso de abordaje con cola FIFO persistente."""
from __future__ import annotations

from sqlite3 import IntegrityError

from config import ahora
from database import Database
from models import Vuelo
from structures import Cola
from .checkin import Checkin
from .gestion_vuelos import GestionVuelos
from .reservas import Reservas

SQL_COLA = """
SELECT q.id AS cola_id, q.reserva_id, q.creado_en,
       c.tarjeta_embarque, r.asiento, r.codigo AS reserva_codigo,
       p.nombres || ' ' || p.apellidos AS pasajero, p.documento,
       v.codigo AS vuelo_codigo
FROM cola_abordaje q
JOIN reservas r ON r.id = q.reserva_id
JOIN pasajeros p ON p.id = r.pasajero_id
JOIN checkins c ON c.reserva_id = r.id
JOIN vuelos v ON v.id = q.vuelo_id
WHERE q.vuelo_id = ? AND q.estado = 'En cola'
ORDER BY q.id
"""


class Abordaje:
    """Gestiona la cola FIFO de pasajeros y el embarque efectivo."""

    def __init__(self, db: Database, checkin: Checkin,
                 reservas: Reservas, vuelos: GestionVuelos) -> None:
        self.db = db
        self.checkin = checkin
        self.reservas = reservas
        self.vuelos = vuelos

    def vuelos_operables(self) -> list[Vuelo]:
        return [v for v in self.vuelos.listar()
                if v.estado in ("Programado", "Check-in abierto", "Abordaje")]

    def listar_pasajeros(self, vuelo_id: int) -> list[dict]:
        pasajeros = []
        for registro in self.checkin.listar(vuelo_id=vuelo_id):
            pasajeros.append({
                "checkin_id": registro.id,
                "reserva_id": registro.reserva_id,
                "reserva_codigo": registro.reserva_codigo,
                "pasajero": registro.pasajero,
                "documento": registro.documento,
                "tarjeta": registro.tarjeta_embarque,
                "asiento": registro.asiento,
                "puerta": registro.puerta,
                "estado": registro.estado_abordaje,
                "abordado": bool(registro.abordado),
                "en_cola": bool(registro.en_cola),
                "fecha_checkin": registro.fecha_checkin,
            })
        orden = {"En cola": 0, "Check-in": 1, "Abordado": 2}
        pasajeros.sort(key=lambda p: (orden.get(p["estado"], 3), p["fecha_checkin"]))
        return pasajeros

    def _cargar_cola(self, vuelo_id: int) -> Cola[dict]:
        cola: Cola[dict] = Cola()
        for fila in self.db.consultar(SQL_COLA, (vuelo_id,)):
            cola.encolar(dict(fila))
        return cola

    def obtener_cola(self, vuelo_id: int) -> list[dict]:
        cola = self._cargar_cola(vuelo_id)
        items = []
        for posicion, item in enumerate(cola, start=1):
            item["posicion"] = posicion
            items.append(item)
        return items

    def resumen(self, vuelo_id: int) -> dict:
        checkins = self.checkin.listar(vuelo_id=vuelo_id)
        total = len(checkins)
        abordados = sum(1 for c in checkins if c.abordado)
        en_cola = sum(1 for c in checkins if c.en_cola)
        pendientes = max(0, total - abordados - en_cola)
        return {
            "total_checkin": total,
            "abordados": abordados,
            "en_cola": en_cola,
            "pendientes": pendientes,
            "porcentaje": round(abordados / total * 100, 1) if total else 0.0,
        }

    def agregar_a_cola(self, reserva_id: int) -> dict:
        reserva = self.reservas.obtener_por_id(reserva_id)
        if not reserva:
            raise ValueError("La reserva indicada no existe.")
        if reserva.estado != "Confirmada":
            raise ValueError("Solo pueden abordar pasajeros con reservas confirmadas.")
        if reserva.estado_vuelo in ("Cancelado", "Completado", "En vuelo"):
            raise ValueError("El vuelo no admite más pasajeros en la cola.")
        checkin = self.checkin.obtener_por_reserva(reserva_id)
        if not checkin:
            raise ValueError("El pasajero no tiene check-in realizado.")
        if checkin.abordado:
            raise ValueError("El pasajero ya está abordado.")
        existente = self.db.consultar_uno(
            "SELECT 1 FROM cola_abordaje WHERE vuelo_id=? AND reserva_id=? AND estado='En cola'",
            (reserva.vuelo_id, reserva_id),
        )
        if existente:
            raise ValueError("El pasajero ya está en la cola de abordaje.")
        sello = ahora().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.db.transaccion():
                cursor = self.db.ejecutar(
                    "INSERT INTO cola_abordaje(vuelo_id, reserva_id, estado, creado_en) "
                    "VALUES (?, ?, 'En cola', ?)", (reserva.vuelo_id, reserva_id, sello),
                )
                if reserva.estado_vuelo in ("Programado", "Check-in abierto"):
                    self.db.ejecutar(
                        "UPDATE vuelos SET estado='Abordaje', actualizado_en=? WHERE id=?",
                        (sello, reserva.vuelo_id),
                    )
        except IntegrityError as exc:
            raise ValueError("El pasajero ya se encuentra en la cola de abordaje.") from exc
        self.vuelos.refrescar_cache()
        return {
            "cola_id": int(cursor.lastrowid), "reserva_id": reserva_id,
            "pasajero": reserva.pasajero_nombre, "reserva_codigo": reserva.codigo,
            "asiento": reserva.asiento,
        }

    def agregar_todos(self, vuelo_id: int) -> tuple[int, int]:
        agregados = 0
        omitidos = 0
        candidatos = [p for p in self.listar_pasajeros(vuelo_id) if p["estado"] == "Check-in"]
        for pasajero in candidatos:
            try:
                self.agregar_a_cola(int(pasajero["reserva_id"]))
                agregados += 1
            except ValueError:
                omitidos += 1
        return agregados, omitidos

    def procesar_siguiente(self, vuelo_id: int) -> dict:
        vuelo = self.vuelos.obtener(vuelo_id)
        if not vuelo:
            raise ValueError("El vuelo seleccionado no existe.")
        if vuelo.estado in ("Cancelado", "Completado", "En vuelo"):
            raise ValueError("El vuelo no se encuentra en proceso de abordaje.")
        cola = self._cargar_cola(vuelo_id)
        if cola.esta_vacia():
            raise ValueError("No hay pasajeros en la cola de abordaje.")
        descartados = 0
        while not cola.esta_vacia():
            item = cola.desencolar()
            reserva = self.reservas.obtener_por_id(int(item["reserva_id"]))
            checkin = self.checkin.obtener_por_reserva(int(item["reserva_id"]))
            motivo = None
            if not reserva or reserva.estado != "Confirmada":
                motivo = "Reserva no confirmada"
            elif not checkin:
                motivo = "Sin check-in"
            elif checkin.abordado:
                motivo = "Ya abordado"
            if motivo:
                self.db.ejecutar(
                    "UPDATE cola_abordaje SET estado='Retirado', procesado_en=? "
                    "WHERE id=? AND estado='En cola'",
                    (ahora().strftime("%Y-%m-%d %H:%M:%S"), item["cola_id"]),
                )
                descartados += 1
                continue

            posicion = int(self.db.escalar(
                "SELECT COALESCE(MAX(posicion), 0) + 1 FROM abordajes WHERE vuelo_id=?",
                (vuelo_id,),
            ))
            sello = ahora().strftime("%Y-%m-%d %H:%M:%S")
            try:
                with self.db.transaccion():
                    self.db.ejecutar(
                        "INSERT INTO abordajes(reserva_id, vuelo_id, posicion, fecha_abordaje) "
                        "VALUES (?, ?, ?, ?)",
                        (item["reserva_id"], vuelo_id, posicion, sello),
                    )
                    self.db.ejecutar(
                        "UPDATE cola_abordaje SET estado='Procesado', procesado_en=? "
                        "WHERE id=? AND estado='En cola'", (sello, item["cola_id"]),
                    )
                    if vuelo.estado in ("Programado", "Check-in abierto"):
                        self.db.ejecutar(
                            "UPDATE vuelos SET estado='Abordaje', actualizado_en=? WHERE id=?",
                            (sello, vuelo_id),
                        )
            except IntegrityError as exc:
                raise ValueError("El pasajero ya fue registrado como abordado.") from exc
            self.vuelos.refrescar_cache()
            return {
                **item,
                "posicion_abordaje": posicion,
                "fecha_abordaje": sello,
                "descartados_antes": descartados,
            }
        self.vuelos.refrescar_cache()
        raise ValueError(
            "No se pudo abordar a ningún pasajero: la cola solo contenía registros inválidos."
        )

    def finalizar(self, vuelo_id: int, forzar: bool = False) -> dict:
        vuelo = self.vuelos.obtener(vuelo_id)
        if not vuelo:
            raise ValueError("El vuelo seleccionado no existe.")
        if vuelo.estado != "Abordaje":
            raise ValueError("El vuelo debe estar en estado 'Abordaje' para finalizar.")
        resumen = self.resumen(vuelo_id)
        if resumen["total_checkin"] == 0:
            raise ValueError("No hay pasajeros con check-in para cerrar el abordaje.")
        if resumen["en_cola"] and not forzar:
            raise ValueError(
                f"Aún hay {resumen['en_cola']} pasajero(s) en la cola. Procesa la cola "
                "o confirma el cierre forzado."
            )
        if resumen["pendientes"] and not forzar:
            raise ValueError(
                f"Aún hay {resumen['pendientes']} pasajero(s) con check-in sin abordar."
            )
        sello = ahora().strftime("%Y-%m-%d %H:%M:%S")
        with self.db.transaccion():
            if forzar:
                self.db.ejecutar(
                    "UPDATE cola_abordaje SET estado='Retirado', procesado_en=? "
                    "WHERE vuelo_id=? AND estado='En cola'", (sello, vuelo_id),
                )
            self.db.ejecutar(
                "UPDATE vuelos SET estado='En vuelo', actualizado_en=? WHERE id=?",
                (sello, vuelo_id),
            )
        self.vuelos.refrescar_cache()
        return {**resumen, "forzado": forzar}
