"""Módulo de negocio para la gestión de vuelos."""
from __future__ import annotations

from datetime import datetime, timedelta
from sqlite3 import IntegrityError
from typing import Any

from config import ESTADOS_VUELO, ahora, fecha_iso
from database import Database
from models import Vuelo
from structures import ListaDoble, busqueda_lineal, merge_sort
from .actividad import Historial

SQL_VUELO = """
SELECT v.id, v.codigo, v.origen_id, v.destino_id, v.fecha_salida,
       v.aeronave_id, v.capacidad, v.puerta, v.precio, v.estado,
       o.codigo AS origen_codigo, o.ciudad AS origen_ciudad,
       d.codigo AS destino_codigo, d.ciudad AS destino_ciudad,
       a.modelo AS aeronave_modelo, a.matricula,
       a.asientos_por_fila,
       COALESCE((SELECT COUNT(*) FROM reservas r
                 WHERE r.vuelo_id = v.id AND r.estado <> 'Cancelada'), 0) AS ocupados
FROM vuelos v
JOIN aeropuertos o ON o.id = v.origen_id
JOIN aeropuertos d ON d.id = v.destino_id
JOIN aeronaves a ON a.id = v.aeronave_id
"""


class GestionVuelos:
    """Reglas de negocio y consultas de vuelos.

    Los vuelos se cargan en una ``ListaDoble`` y se ordenan con merge sort.
    Además, un diccionario mantiene el índice código → vuelo para consultas
    O(1), tal como exige el módulo de diccionarios.
    """

    TRANSICIONES = {
        "Programado": {"Check-in abierto", "Abordaje", "Cancelado"},
        "Check-in abierto": {"Programado", "Abordaje", "Cancelado"},
        "Abordaje": {"Check-in abierto", "En vuelo", "Cancelado"},
        "En vuelo": {"Completado"},
        "Completado": set(),
        "Cancelado": set(),
    }

    def __init__(self, db: Database, historial: Historial) -> None:
        self.db = db
        self.historial = historial
        self._cache_codigo: dict[str, Vuelo] = {}
        self._cache_id: dict[int, Vuelo] = {}
        self.refrescar_cache()

    # ------------------------------------------------------------------
    # Consultas y estructuras
    # ------------------------------------------------------------------
    def refrescar_cache(self) -> None:
        vuelos = [Vuelo.desde_fila(fila) for fila in self.db.consultar(SQL_VUELO)]
        self._cache_codigo = {vuelo.codigo.upper(): vuelo for vuelo in vuelos}
        self._cache_id = {vuelo.id: vuelo for vuelo in vuelos}

    def listar(self, texto: str = "", estado: str = "", destino: str = "") -> list[Vuelo]:
        """Carga los vuelos en una lista enlazada, filtra y ordena por salida."""
        self.refrescar_cache()
        lista = ListaDoble(self._cache_id.values())
        texto = (texto or "").strip().lower()
        estado = (estado or "").strip()
        destino = (destino or "").strip().upper()

        if texto:
            lista = lista.filtrar(lambda v: (
                texto in v.codigo.lower()
                or texto in v.ruta.lower()
                or texto in v.origen_ciudad.lower()
                or texto in v.destino_ciudad.lower()
                or texto in v.aeronave_modelo.lower()
            ))
        if estado:
            lista = lista.filtrar(lambda v: v.estado == estado)
        if destino:
            lista = lista.filtrar(lambda v: v.destino_codigo.upper() == destino)

        lista.ordenar(clave=lambda v: v.fecha_salida)
        return lista.a_lista()

    def obtener_por_codigo(self, codigo: str, usar_cache: bool = True) -> Vuelo | None:
        codigo = (codigo or "").strip().upper()
        if usar_cache and codigo in self._cache_codigo:
            return self._cache_codigo[codigo]
        self.refrescar_cache()
        return self._cache_codigo.get(codigo)

    def obtener(self, vuelo_id: int) -> Vuelo | None:
        if vuelo_id in self._cache_id:
            return self._cache_id[vuelo_id]
        fila = self.db.consultar_uno(SQL_VUELO + " WHERE v.id = ?", (vuelo_id,))
        return Vuelo.desde_fila(fila) if fila else None

    def obtener_por_codigo_o_error(self, codigo: str) -> Vuelo:
        vuelo = self.obtener_por_codigo(codigo)
        if not vuelo:
            raise ValueError(f"No existe el vuelo {codigo}.")
        return vuelo

    def buscar_lineal(self, texto: str) -> Vuelo | None:
        """Búsqueda secuencial sobre la colección de vuelos."""
        return busqueda_lineal(self.listar(), lambda v: (
            texto.lower() in v.codigo.lower() or texto.lower() in v.ruta.lower()
        ))

    def vuelos_disponibles(self, texto: str = "", destino: str = "") -> list[Vuelo]:
        disponibles = [v for v in self.listar(texto=texto, destino=destino)
                       if v.estado in ("Programado", "Check-in abierto")
                       and v.fecha_dt >= ahora() - timedelta(minutes=30)]
        return merge_sort(disponibles, clave=lambda v: v.fecha_salida)

    def proximas_salidas(self, limite: int = 6) -> list[Vuelo]:
        ahora_dt = ahora()
        activos = [v for v in self.listar()
                   if v.estado not in ("Completado", "Cancelado")
                   and v.fecha_dt >= ahora_dt - timedelta(hours=1)]
        return activos[:limite]

    def listar_aeropuertos(self) -> list[dict]:
        filas = self.db.consultar(
            "SELECT id, codigo, ciudad, nombre, pais, latitud, longitud "
            "FROM aeropuertos ORDER BY ciudad"
        )
        return [dict(fila) for fila in filas]

    def listar_aeronaves(self) -> list[dict]:
        filas = self.db.consultar(
            "SELECT id, matricula, modelo, filas, asientos_por_fila, capacidad "
            "FROM aeronaves WHERE activo = 1 ORDER BY modelo"
        )
        return [dict(fila) for fila in filas]

    def asientos_ocupados(self, vuelo_id: int) -> int:
        return int(self.db.escalar(
            "SELECT COUNT(*) FROM reservas WHERE vuelo_id = ? AND estado <> 'Cancelada'",
            (vuelo_id,),
        ))

    def verificar_codigo(self, codigo: str) -> bool:
        return self.db.consultar_uno(
            "SELECT 1 FROM vuelos WHERE codigo = ? COLLATE NOCASE", (codigo,)
        ) is not None

    # ------------------------------------------------------------------
    # Generación de código
    # ------------------------------------------------------------------
    def generar_codigo(self) -> str:
        """Genera un código único con la forma AER101, AER102, etc."""
        filas = self.db.consultar(
            "SELECT codigo FROM vuelos WHERE codigo LIKE 'AER%'"
        )
        usados: set[int] = set()
        for fila in filas:
            sufijo = str(fila["codigo"])[3:]
            if sufijo.isdigit():
                usados.add(int(sufijo))
        numero = 101
        while numero in usados:
            numero += 1
        return f"AER{numero}"

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------
    @staticmethod
    def _validar_fecha_hora(fecha: str, hora: str) -> str:
        try:
            salida = datetime.strptime(f"{fecha.strip()} {hora.strip()}", "%Y-%m-%d %H:%M")
        except (ValueError, AttributeError) as exc:
            raise ValueError("Indica una fecha y hora válidas (AAAA-MM-DD y HH:MM).") from exc
        if salida < ahora() - timedelta(minutes=5):
            raise ValueError("La fecha de salida no puede estar en el pasado.")
        if salida > ahora() + timedelta(days=365):
            raise ValueError("La fecha de salida no puede superar un año de anticipación.")
        return fecha_iso(salida)

    @staticmethod
    def _validar_texto(valor: str, campo: str, maximo: int = 80) -> str:
        valor = (valor or "").strip()
        if not valor:
            raise ValueError(f"El campo {campo} es obligatorio.")
        if len(valor) > maximo:
            raise ValueError(f"El campo {campo} no puede superar {maximo} caracteres.")
        return valor

    def _datos_relacionados(self, origen_codigo: str, destino_codigo: str,
                            aeronave_id: int, capacidad: Any, puerta: str,
                            precio: Any) -> tuple[int, int, int, int, str, float]:
        origen = self.db.consultar_uno(
            "SELECT id FROM aeropuertos WHERE codigo = ? COLLATE NOCASE",
            ((origen_codigo or "").strip().upper(),),
        )
        destino = self.db.consultar_uno(
            "SELECT id FROM aeropuertos WHERE codigo = ? COLLATE NOCASE",
            ((destino_codigo or "").strip().upper(),),
        )
        if not origen or not destino:
            raise ValueError("Selecciona un aeropuerto de origen y destino válidos.")
        if int(origen["id"]) == int(destino["id"]):
            raise ValueError("El origen y el destino deben ser diferentes.")

        aeronave = self.db.consultar_uno(
            "SELECT id, capacidad FROM aeronaves WHERE id = ? AND activo = 1",
            (int(aeronave_id),),
        )
        if not aeronave:
            raise ValueError("Selecciona una aeronave válida.")
        try:
            capacidad_int = int(capacidad)
            precio_float = round(float(precio), 2)
        except (ValueError, TypeError) as exc:
            raise ValueError("La capacidad y el precio deben ser numéricos.") from exc
        if capacidad_int <= 0:
            raise ValueError("La capacidad debe ser mayor que cero.")
        if capacidad_int > int(aeronave["capacidad"]):
            raise ValueError(
                f"La capacidad no puede superar la de la aeronave ({aeronave['capacidad']})."
            )
        if precio_float <= 0:
            raise ValueError("El precio del boleto debe ser mayor que cero.")
        puerta_limpia = self._validar_texto(puerta, "puerta", 12).upper()
        return (int(origen["id"]), int(destino["id"]), int(aeronave["id"]),
                capacidad_int, puerta_limpia, precio_float)

    # ------------------------------------------------------------------
    # Operaciones de escritura
    # ------------------------------------------------------------------
    def registrar(self, origen_codigo: str, destino_codigo: str, fecha: str, hora: str,
                  aeronave_id: int, capacidad: Any, puerta: str,
                  precio: Any) -> Vuelo:
        fecha_salida = self._validar_fecha_hora(fecha, hora)
        origen_id, destino_id, aeronave, capacidad_int, puerta_limpia, precio_float = \
            self._datos_relacionados(
                origen_codigo, destino_codigo, aeronave_id, capacidad, puerta, precio
            )
        codigo = self.generar_codigo()
        sello = ahora().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.db.transaccion():
                cursor = self.db.ejecutar(
                    "INSERT INTO vuelos(codigo, origen_id, destino_id, fecha_salida, "
                    "aeronave_id, capacidad, puerta, precio, estado, creado_en, actualizado_en) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Programado', ?, ?)",
                    (codigo, origen_id, destino_id, fecha_salida, aeronave,
                     capacidad_int, puerta_limpia, precio_float, sello, sello),
                )
                vuelo_id = int(cursor.lastrowid)
        except IntegrityError as exc:
            raise ValueError("No se pudo generar un código de vuelo único.") from exc

        self.refrescar_cache()
        vuelo = self.obtener(vuelo_id)
        assert vuelo is not None

        def deshacer() -> None:
            dependencias = self.db.escalar(
                "SELECT (SELECT COUNT(*) FROM reservas WHERE vuelo_id = ?) + "
                "(SELECT COUNT(*) FROM checkins c JOIN reservas r ON r.id = c.reserva_id "
                " WHERE r.vuelo_id = ?) + "
                "(SELECT COUNT(*) FROM abordajes WHERE vuelo_id = ?)",
                (vuelo_id, vuelo_id, vuelo_id),
            )
            if dependencias:
                raise ValueError(
                    "No se puede deshacer: el vuelo ya tiene reservas, check-in o abordajes."
                )
            self.db.ejecutar("DELETE FROM vuelos WHERE id = ?", (vuelo_id,))
            self.refrescar_cache()

        self.historial.registrar(
            "Vuelo", f"Vuelo {codigo} registrado ({vuelo.ruta})", deshacer,
            f"id={vuelo_id}",
        )
        return vuelo

    def actualizar(self, vuelo_id: int, origen_codigo: str, destino_codigo: str,
                   fecha: str, hora: str, aeronave_id: int, capacidad: Any,
                   puerta: str, precio: Any) -> Vuelo:
        anterior = self.obtener(vuelo_id)
        if not anterior:
            raise ValueError("El vuelo seleccionado no existe.")
        if anterior.estado in ("En vuelo", "Completado", "Cancelado"):
            raise ValueError("No se puede editar un vuelo en vuelo, completado o cancelado.")

        fecha_salida = self._validar_fecha_hora(fecha, hora)
        origen_id, destino_id, aeronave, capacidad_int, puerta_limpia, precio_float = \
            self._datos_relacionados(
                origen_codigo, destino_codigo, aeronave_id, capacidad, puerta, precio
            )
        ocupados = self.asientos_ocupados(vuelo_id)
        if capacidad_int < ocupados:
            raise ValueError(
                f"La capacidad no puede ser menor que los {ocupados} asientos ya reservados."
            )
        if ocupados and (origen_id != anterior.origen_id or destino_id != anterior.destino_id):
            raise ValueError("No se puede cambiar la ruta de un vuelo con reservas activas.")
        if ocupados and aeronave != anterior.aeronave_id:
            raise ValueError("No se puede cambiar la aeronave de un vuelo con reservas activas.")

        fila_anterior = dict(self.db.consultar_uno("SELECT * FROM vuelos WHERE id = ?", (vuelo_id,)))
        sello = ahora().strftime("%Y-%m-%d %H:%M:%S")
        self.db.ejecutar(
            "UPDATE vuelos SET origen_id=?, destino_id=?, fecha_salida=?, aeronave_id=?, "
            "capacidad=?, puerta=?, precio=?, actualizado_en=? WHERE id=?",
            (origen_id, destino_id, fecha_salida, aeronave, capacidad_int,
             puerta_limpia, precio_float, sello, vuelo_id),
        )
        self.refrescar_cache()

        def deshacer() -> None:
            en_operacion = self.db.escalar(
                "SELECT (SELECT COUNT(*) FROM abordajes WHERE vuelo_id=?) + "
                "(SELECT COUNT(*) FROM cola_abordaje WHERE vuelo_id=? AND estado='En cola')",
                (vuelo_id, vuelo_id),
            )
            if en_operacion:
                raise ValueError("No se puede deshacer: el vuelo ya tiene abordaje en curso.")
            self.db.ejecutar(
                "UPDATE vuelos SET origen_id=?, destino_id=?, fecha_salida=?, aeronave_id=?, "
                "capacidad=?, puerta=?, precio=?, actualizado_en=? WHERE id=?",
                (fila_anterior["origen_id"], fila_anterior["destino_id"],
                 fila_anterior["fecha_salida"], fila_anterior["aeronave_id"],
                 fila_anterior["capacidad"], fila_anterior["puerta"],
                 fila_anterior["precio"], fila_anterior["actualizado_en"], vuelo_id),
            )
            self.refrescar_cache()

        self.historial.registrar(
            "Vuelo", f"Vuelo {anterior.codigo} actualizado", deshacer,
            f"id={vuelo_id}",
        )
        vuelo = self.obtener(vuelo_id)
        assert vuelo is not None
        return vuelo

    def cambiar_estado(self, vuelo_id: int, nuevo_estado: str) -> Vuelo:
        vuelo = self.obtener(vuelo_id)
        if not vuelo:
            raise ValueError("El vuelo seleccionado no existe.")
        if nuevo_estado not in ESTADOS_VUELO:
            raise ValueError("Estado de vuelo no válido.")
        if nuevo_estado == "Cancelado":
            raise ValueError("Utiliza la acción 'Cancelar vuelo' para anular reservas asociadas.")
        if nuevo_estado == vuelo.estado:
            raise ValueError("El vuelo ya se encuentra en ese estado.")
        permitidos = self.TRANSICIONES.get(vuelo.estado, set())
        if nuevo_estado not in permitidos:
            raise ValueError(
                f"No se puede pasar de '{vuelo.estado}' a '{nuevo_estado}'. "
                f"Estados permitidos: {', '.join(sorted(permitidos)) or 'ninguno'}."
            )
        anterior = vuelo.estado
        sello = ahora().strftime("%Y-%m-%d %H:%M:%S")
        self.db.ejecutar(
            "UPDATE vuelos SET estado = ?, actualizado_en = ? WHERE id = ?",
            (nuevo_estado, sello, vuelo_id),
        )
        self.refrescar_cache()

        def deshacer() -> None:
            estado_actual = self.db.escalar(
                "SELECT estado FROM vuelos WHERE id = ?", (vuelo_id,), defecto=""
            )
            en_operacion = self.db.escalar(
                "SELECT (SELECT COUNT(*) FROM abordajes WHERE vuelo_id=?) + "
                "(SELECT COUNT(*) FROM cola_abordaje WHERE vuelo_id=? AND estado='En cola')",
                (vuelo_id, vuelo_id),
            )
            if estado_actual != nuevo_estado:
                raise ValueError("No se puede deshacer: el estado del vuelo cambi? despu?s.")
            if en_operacion:
                raise ValueError("No se puede deshacer: el vuelo ya tiene abordaje en curso.")
            self.db.ejecutar("UPDATE vuelos SET estado = ? WHERE id = ?",
                             (anterior, vuelo_id))
            self.refrescar_cache()

        self.historial.registrar(
            "Estado de vuelo",
            f"Vuelo {vuelo.codigo}: {anterior} → {nuevo_estado}",
            deshacer, f"id={vuelo_id}",
        )
        actualizado = self.obtener(vuelo_id)
        assert actualizado is not None
        return actualizado

    def cancelar(self, vuelo_id: int) -> Vuelo:
        vuelo = self.obtener(vuelo_id)
        if not vuelo:
            raise ValueError("El vuelo seleccionado no existe.")
        if vuelo.estado == "Cancelado":
            raise ValueError("El vuelo ya está cancelado.")
        if vuelo.estado in ("En vuelo", "Completado"):
            raise ValueError("No se puede cancelar un vuelo en vuelo o completado.")
        abordados = int(self.db.escalar(
            "SELECT COUNT(*) FROM abordajes WHERE vuelo_id = ?", (vuelo_id,)
        ))
        if abordados:
            raise ValueError("No se puede cancelar un vuelo con pasajeros ya abordados.")
        en_cola = int(self.db.escalar(
            "SELECT COUNT(*) FROM cola_abordaje WHERE vuelo_id = ? AND estado = 'En cola'",
            (vuelo_id,),
        ))
        if en_cola:
            raise ValueError("No se puede cancelar un vuelo con pasajeros en cola de abordaje.")

        reservas_anteriores = [dict(fila) for fila in self.db.consultar(
            "SELECT id, estado FROM reservas WHERE vuelo_id = ? AND estado <> 'Cancelada'",
            (vuelo_id,),
        )]
        estado_anterior = vuelo.estado
        sello = ahora().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.db.transaccion():
                self.db.ejecutar(
                    "UPDATE vuelos SET estado='Cancelado', actualizado_en=? WHERE id=?",
                    (sello, vuelo_id),
                )
                self.db.ejecutar(
                    "UPDATE reservas SET estado='Cancelada' "
                    "WHERE vuelo_id=? AND estado <> 'Cancelada'", (vuelo_id,),
                )
        except IntegrityError as exc:
            raise ValueError("No se pudo cancelar el vuelo por una restricción de datos.") from exc
        self.refrescar_cache()

        def deshacer() -> None:
            with self.db.transaccion():
                self.db.ejecutar(
                    "UPDATE vuelos SET estado = ?, actualizado_en = ? WHERE id = ?",
                    (estado_anterior, sello, vuelo_id),
                )
                for reserva in reservas_anteriores:
                    self.db.ejecutar(
                        "UPDATE reservas SET estado = ? WHERE id = ?",
                        (reserva["estado"], reserva["id"]),
                    )
            self.refrescar_cache()

        self.historial.registrar(
            "Cancelación", f"Vuelo {vuelo.codigo} cancelado",
            deshacer, f"id={vuelo_id}, reservas={len(reservas_anteriores)}",
        )
        cancelado = self.obtener(vuelo_id)
        assert cancelado is not None
        return cancelado
