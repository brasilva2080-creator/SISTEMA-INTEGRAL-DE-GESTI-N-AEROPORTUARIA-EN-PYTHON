"""Capa de acceso a SQLite para el sistema aeroportuario."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence

from config import DB_PATH


ESQUEMA_SQL = """
CREATE TABLE IF NOT EXISTS aeropuertos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nombre TEXT NOT NULL,
    ciudad TEXT NOT NULL,
    pais TEXT NOT NULL DEFAULT 'Perú',
    latitud REAL NOT NULL DEFAULT 0,
    longitud REAL NOT NULL DEFAULT 0,
    creado_en TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS aeronaves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula TEXT NOT NULL UNIQUE COLLATE NOCASE,
    modelo TEXT NOT NULL,
    filas INTEGER NOT NULL CHECK (filas > 0),
    asientos_por_fila INTEGER NOT NULL CHECK (asientos_por_fila BETWEEN 2 AND 6),
    capacidad INTEGER NOT NULL CHECK (capacidad > 0),
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vuelos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    origen_id INTEGER NOT NULL REFERENCES aeropuertos(id) ON DELETE RESTRICT,
    destino_id INTEGER NOT NULL REFERENCES aeropuertos(id) ON DELETE RESTRICT,
    fecha_salida TEXT NOT NULL,
    aeronave_id INTEGER NOT NULL REFERENCES aeronaves(id) ON DELETE RESTRICT,
    capacidad INTEGER NOT NULL CHECK (capacidad > 0),
    puerta TEXT NOT NULL,
    precio REAL NOT NULL CHECK (precio >= 0),
    estado TEXT NOT NULL DEFAULT 'Programado' CHECK (
        estado IN ('Programado', 'Check-in abierto', 'Abordaje', 'En vuelo', 'Completado', 'Cancelado')
    ),
    creado_en TEXT NOT NULL,
    actualizado_en TEXT NOT NULL,
    CHECK (origen_id <> destino_id)
);

CREATE TABLE IF NOT EXISTS pasajeros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    nombres TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    documento TEXT NOT NULL UNIQUE COLLATE NOCASE,
    email TEXT NOT NULL,
    telefono TEXT NOT NULL,
    creado_en TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reservas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE COLLATE NOCASE,
    vuelo_id INTEGER NOT NULL REFERENCES vuelos(id) ON DELETE RESTRICT,
    pasajero_id INTEGER NOT NULL REFERENCES pasajeros(id) ON DELETE RESTRICT,
    asiento TEXT NOT NULL,
    precio REAL NOT NULL CHECK (precio >= 0),
    estado TEXT NOT NULL DEFAULT 'Pendiente' CHECK (
        estado IN ('Pendiente', 'Confirmada', 'Cancelada')
    ),
    fecha_reserva TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_reserva_asiento_activo
    ON reservas(vuelo_id, asiento) WHERE estado <> 'Cancelada';
CREATE UNIQUE INDEX IF NOT EXISTS ux_reserva_pasajero_vuelo_activo
    ON reservas(vuelo_id, pasajero_id) WHERE estado <> 'Cancelada';
CREATE INDEX IF NOT EXISTS ix_reservas_vuelo ON reservas(vuelo_id);
CREATE INDEX IF NOT EXISTS ix_reservas_pasajero ON reservas(pasajero_id);

CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reserva_id INTEGER NOT NULL UNIQUE REFERENCES reservas(id) ON DELETE RESTRICT,
    tarjeta_embarque TEXT NOT NULL UNIQUE COLLATE NOCASE,
    cantidad_equipaje INTEGER NOT NULL DEFAULT 0 CHECK (cantidad_equipaje BETWEEN 0 AND 10),
    peso_total REAL NOT NULL DEFAULT 0 CHECK (peso_total >= 0),
    fecha_checkin TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS equipajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checkin_id INTEGER NOT NULL REFERENCES checkins(id) ON DELETE CASCADE,
    cantidad INTEGER NOT NULL,
    peso_total REAL NOT NULL,
    descripcion TEXT NOT NULL DEFAULT 'Equipaje facturado'
);

CREATE TABLE IF NOT EXISTS abordajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reserva_id INTEGER NOT NULL UNIQUE REFERENCES reservas(id) ON DELETE RESTRICT,
    vuelo_id INTEGER NOT NULL REFERENCES vuelos(id) ON DELETE RESTRICT,
    posicion INTEGER NOT NULL,
    fecha_abordaje TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_abordajes_vuelo ON abordajes(vuelo_id);

CREATE TABLE IF NOT EXISTS cola_abordaje (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vuelo_id INTEGER NOT NULL REFERENCES vuelos(id) ON DELETE RESTRICT,
    reserva_id INTEGER NOT NULL REFERENCES reservas(id) ON DELETE RESTRICT,
    estado TEXT NOT NULL DEFAULT 'En cola' CHECK (estado IN ('En cola', 'Procesado', 'Retirado')),
    creado_en TEXT NOT NULL,
    procesado_en TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_cola_activa
    ON cola_abordaje(vuelo_id, reserva_id) WHERE estado = 'En cola';
CREATE INDEX IF NOT EXISTS ix_cola_vuelo ON cola_abordaje(vuelo_id, estado, id);

CREATE TABLE IF NOT EXISTS rutas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origen_id INTEGER NOT NULL REFERENCES aeropuertos(id) ON DELETE RESTRICT,
    destino_id INTEGER NOT NULL REFERENCES aeropuertos(id) ON DELETE RESTRICT,
    distancia_km REAL NOT NULL CHECK (distancia_km > 0),
    duracion_min INTEGER NOT NULL CHECK (duracion_min > 0),
    creado_en TEXT NOT NULL,
    CHECK (origen_id <> destino_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_ruta_directa ON rutas(origen_id, destino_id);

CREATE TABLE IF NOT EXISTS operaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    detalles TEXT NOT NULL DEFAULT '',
    fecha TEXT NOT NULL,
    deshecho INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_operaciones_fecha ON operaciones(id DESC);

CREATE INDEX IF NOT EXISTS ix_vuelos_fecha ON vuelos(fecha_salida);
CREATE INDEX IF NOT EXISTS ix_vuelos_estado ON vuelos(estado);
CREATE INDEX IF NOT EXISTS ix_pasajeros_documento ON pasajeros(documento);
"""


class Database:
    """Envoltorio pequeño y explícito alrededor de sqlite3."""

    def __init__(self, ruta: str | Path | None = None) -> None:
        self.ruta = Path(ruta) if ruta else DB_PATH
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.ruta), timeout=15, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.executescript(ESQUEMA_SQL)
        self.conn.execute("PRAGMA user_version = 1")

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def ejecutar(self, sql: str, parametros: Sequence[Any] = ()) -> sqlite3.Cursor:
        return self.conn.execute(sql, parametros)

    def ejecutar_muchos(self, sql: str, filas: Sequence[Sequence[Any]]) -> sqlite3.Cursor:
        return self.conn.executemany(sql, filas)

    def consultar(self, sql: str, parametros: Sequence[Any] = ()) -> list[sqlite3.Row]:
        return list(self.conn.execute(sql, parametros).fetchall())

    def consultar_uno(self, sql: str, parametros: Sequence[Any] = ()) -> sqlite3.Row | None:
        return self.conn.execute(sql, parametros).fetchone()

    def escalar(self, sql: str, parametros: Sequence[Any] = (), defecto: Any = 0) -> Any:
        fila = self.consultar_uno(sql, parametros)
        if fila is None:
            return defecto
        valor = fila[0]
        return defecto if valor is None else valor

    def ultimo_id(self) -> int:
        return int(self.conn.execute("SELECT last_insert_rowid()").fetchone()[0])

    @contextmanager
    def transaccion(self) -> Iterator["Database"]:
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield self
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        else:
            self.conn.execute("COMMIT")

    def cerrar(self) -> None:
        try:
            self.conn.close()
        except sqlite3.Error:
            pass

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.cerrar()
