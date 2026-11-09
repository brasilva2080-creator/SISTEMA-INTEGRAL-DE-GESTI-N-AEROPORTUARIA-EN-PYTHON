"""Rutas y destinos representados mediante un grafo."""
from __future__ import annotations

import re
from sqlite3 import IntegrityError

from config import ahora
from database import Database
from models import Aeropuerto, Ruta
from structures import Grafo
from .actividad import Historial

SQL_RUTA = """
SELECT r.*, o.codigo AS origen_codigo, o.ciudad AS origen_ciudad,
       d.codigo AS destino_codigo, d.ciudad AS destino_ciudad
FROM rutas r
JOIN aeropuertos o ON o.id = r.origen_id
JOIN aeropuertos d ON d.id = r.destino_id
"""


class Rutas:
    """CRUD de aeropuertos/rutas y cálculo de caminos con BFS."""

    def __init__(self, db: Database, historial: Historial) -> None:
        self.db = db
        self.historial = historial

    def listar_aeropuertos(self) -> list[Aeropuerto]:
        filas = self.db.consultar(
            "SELECT * FROM aeropuertos ORDER BY ciudad, codigo"
        )
        return [Aeropuerto.desde_fila(fila) for fila in filas]

    def obtener_aeropuerto(self, codigo: str) -> Aeropuerto | None:
        fila = self.db.consultar_uno(
            "SELECT * FROM aeropuertos WHERE codigo = ? COLLATE NOCASE",
            ((codigo or "").strip().upper(),),
        )
        return Aeropuerto.desde_fila(fila) if fila else None

    def listar_rutas(self) -> list[Ruta]:
        filas = self.db.consultar(SQL_RUTA + " ORDER BY o.ciudad, d.ciudad")
        return [Ruta.desde_fila(fila) for fila in filas]

    # ------------------------------------------------------------------
    # Aeropuertos
    # ------------------------------------------------------------------
    def registrar_aeropuerto(self, codigo: str, nombre: str, ciudad: str,
                             pais: str = "Perú", latitud="", longitud="") -> Aeropuerto:
        codigo = (codigo or "").strip().upper()
        nombre = (nombre or "").strip()
        ciudad = (ciudad or "").strip()
        pais = (pais or "Perú").strip() or "Perú"
        if not re.fullmatch(r"[A-Z]{3}", codigo):
            raise ValueError("El código IATA debe tener exactamente 3 letras (ej. LIM).")
        if len(nombre) < 3 or len(ciudad) < 3:
            raise ValueError("El nombre y la ciudad del aeropuerto son obligatorios.")
        if len(nombre) > 100 or len(ciudad) > 60 or len(pais) > 60:
            raise ValueError("Los datos del aeropuerto son demasiado largos.")
        if self.obtener_aeropuerto(codigo):
            raise ValueError("Ya existe un aeropuerto con ese código.")
        try:
            lat = float(str(latitud).replace(",", ".")) if str(latitud).strip() else 0.0
            lon = float(str(longitud).replace(",", ".")) if str(longitud).strip() else 0.0
        except ValueError as exc:
            raise ValueError("La latitud y longitud deben ser numéricas.") from exc
        if not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError("Las coordenadas están fuera del rango válido.")
        try:
            with self.db.transaccion():
                cursor = self.db.ejecutar(
                    "INSERT INTO aeropuertos(codigo, nombre, ciudad, pais, latitud, longitud, "
                    "creado_en) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (codigo, nombre, ciudad, pais, lat, lon,
                     ahora().strftime("%Y-%m-%d %H:%M:%S")),
                )
                aeropuerto_id = int(cursor.lastrowid)
        except IntegrityError as exc:
            raise ValueError("El código de aeropuerto ya está registrado.") from exc
        aeropuerto = self.obtener_aeropuerto(codigo)
        assert aeropuerto is not None

        def deshacer() -> None:
            dependencias = self.db.escalar(
                "SELECT (SELECT COUNT(*) FROM vuelos WHERE origen_id=? OR destino_id=?) + "
                "(SELECT COUNT(*) FROM rutas WHERE origen_id=? OR destino_id=?)",
                (aeropuerto_id, aeropuerto_id, aeropuerto_id, aeropuerto_id),
            )
            if dependencias:
                raise ValueError("No se puede deshacer: el aeropuerto ya está en uso.")
            self.db.ejecutar("DELETE FROM aeropuertos WHERE id=?", (aeropuerto_id,))

        self.historial.registrar(
            "Aeropuerto", f"Aeropuerto {codigo} registrado ({ciudad})", deshacer,
            f"id={aeropuerto_id}",
        )
        return aeropuerto

    # ------------------------------------------------------------------
    # Rutas
    # ------------------------------------------------------------------
    def registrar_ruta(self, origen_codigo: str, destino_codigo: str,
                       distancia_km, duracion_min) -> Ruta:
        origen = self.obtener_aeropuerto(origen_codigo)
        destino = self.obtener_aeropuerto(destino_codigo)
        if not origen or not destino:
            raise ValueError("Selecciona aeropuertos de origen y destino válidos.")
        if origen.id == destino.id:
            raise ValueError("El origen y el destino deben ser diferentes.")
        try:
            distancia = round(float(str(distancia_km).replace(",", ".")), 1)
            duracion = int(duracion_min)
        except (TypeError, ValueError) as exc:
            raise ValueError("La distancia y la duración deben ser numéricas.") from exc
        if distancia <= 0 or duracion <= 0:
            raise ValueError("La distancia y la duración deben ser mayores que cero.")
        if distancia > 20000 or duracion > 1440:
            raise ValueError("La distancia o duración ingresada no es realista.")
        existente = self.db.consultar_uno(
            "SELECT id FROM rutas WHERE (origen_id=? AND destino_id=?) "
            "OR (origen_id=? AND destino_id=?)",
            (origen.id, destino.id, destino.id, origen.id),
        )
        if existente:
            raise ValueError("Ya existe una conexión entre esos aeropuertos.")
        try:
            with self.db.transaccion():
                cursor = self.db.ejecutar(
                    "INSERT INTO rutas(origen_id, destino_id, distancia_km, duracion_min, "
                    "creado_en) VALUES (?, ?, ?, ?, ?)",
                    (origen.id, destino.id, distancia, duracion,
                     ahora().strftime("%Y-%m-%d %H:%M:%S")),
                )
                ruta_id = int(cursor.lastrowid)
        except IntegrityError as exc:
            raise ValueError("La conexión ya existe.") from exc
        ruta = next((r for r in self.listar_rutas() if r.id == ruta_id), None)
        if not ruta:
            raise ValueError("No se pudo recuperar la ruta registrada.")

        def deshacer() -> None:
            self.db.ejecutar("DELETE FROM rutas WHERE id=?", (ruta_id,))

        self.historial.registrar(
            "Ruta", f"Ruta {origen.codigo} ↔ {destino.codigo} registrada", deshacer,
            f"id={ruta_id}, distancia={distancia}",
        )
        return ruta

    # ------------------------------------------------------------------
    # Grafo
    # ------------------------------------------------------------------
    def construir_grafo(self) -> Grafo:
        grafo = Grafo()
        aeropuertos = self.listar_aeropuertos()
        for aeropuerto in aeropuertos:
            grafo.agregar_vertice(aeropuerto.codigo, {
                "ciudad": aeropuerto.ciudad,
                "nombre": aeropuerto.nombre,
                "latitud": aeropuerto.latitud,
                "longitud": aeropuerto.longitud,
            })
        for ruta in self.listar_rutas():
            grafo.agregar_arista(
                ruta.origen_codigo, ruta.destino_codigo,
                peso=ruta.distancia_km,
                datos={"duracion_min": ruta.duracion_min, "ruta_id": ruta.id},
            )
        return grafo

    def calcular_ruta(self, origen_codigo: str, destino_codigo: str) -> dict:
        origen_codigo = (origen_codigo or "").strip().upper()
        destino_codigo = (destino_codigo or "").strip().upper()
        if not origen_codigo or not destino_codigo:
            raise ValueError("Selecciona un origen y un destino.")
        if origen_codigo == destino_codigo:
            raise ValueError("El origen y el destino deben ser diferentes.")
        grafo = self.construir_grafo()
        if not grafo.tiene_vertice(origen_codigo) or not grafo.tiene_vertice(destino_codigo):
            raise ValueError("Uno de los aeropuertos no existe en el grafo.")
        camino = grafo.bfs(origen_codigo, destino_codigo)
        if not camino:
            raise ValueError("No existe una ruta conectada entre esos aeropuertos.")
        distancia = grafo.distancia(camino)
        duracion = 0
        for a, b in zip(camino, camino[1:]):
            datos = grafo.vecinos(a).get(b, {})
            duracion += int(datos.get("duracion_min", 0))
        ciudades = []
        for codigo in camino:
            datos = grafo.obtener_vertice(codigo) or {}
            ciudades.append(f"{codigo} · {datos.get('ciudad', codigo)}")
        return {
            "camino": camino,
            "ciudades": ciudades,
            "distancia_km": round(distancia, 1),
            "duracion_min": duracion,
            "escalas": max(0, len(camino) - 2),
            "texto": " → ".join(camino),
        }

    def conexiones(self, codigo: str) -> list[tuple[str, float]]:
        return self.construir_grafo().conexiones_de((codigo or "").strip().upper())

    def resumen(self) -> dict:
        grafo = self.construir_grafo()
        return {
            "aeropuertos": len(self.listar_aeropuertos()),
            "rutas": len(self.listar_rutas()),
            "conexo": grafo.es_conexo(),
        }
