"""Historial de operaciones basado en una pila LIFO."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from config import ahora
from database import Database
from structures import Pila


@dataclass(slots=True)
class Operacion:
    id: int
    tipo: str
    descripcion: str
    fecha: str
    detalles: str = ""
    deshacer: Callable[[], None] | None = field(default=None, repr=False)


class Historial:
    """Registra acciones administrativas y permite deshacer la más reciente.

    La pila conserva las operaciones de la sesión actual. La tabla
    ``operaciones`` conserva la bitácora completa para auditoría.
    """

    def __init__(self, db: Database) -> None:
        self.db = db
        self._pila: Pila[Operacion] = Pila()

    def registrar(self, tipo: str, descripcion: str,
                  deshacer: Callable[[], None] | None = None,
                  detalles: str = "") -> Operacion:
        fecha = ahora().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.db.ejecutar(
            "INSERT INTO operaciones(tipo, descripcion, detalles, fecha, deshecho) "
            "VALUES (?, ?, ?, ?, 0)",
            (tipo, descripcion, detalles, fecha),
        )
        operacion = Operacion(
            id=int(cursor.lastrowid), tipo=tipo, descripcion=descripcion,
            fecha=fecha, detalles=detalles, deshacer=deshacer,
        )
        if deshacer is not None:
            self._pila.apilar(operacion)
        return operacion

    def deshacer_ultima(self) -> Operacion:
        if self._pila.esta_vacia():
            raise ValueError(
                "No hay operaciones deshacibles en esta sesión. "
                "Las operaciones anteriores al reinicio solo se conservan en la bitácora."
            )
        operacion = self._pila.desapilar()
        try:
            if operacion.deshacer is None:
                raise ValueError("Esta operación no se puede deshacer.")
            operacion.deshacer()
            self.db.ejecutar("UPDATE operaciones SET deshecho = 1 WHERE id = ?", (operacion.id,))
        except Exception:
            # Si falla la reversión, la operación vuelve a la cima para no perderla.
            self._pila.apilar(operacion)
            raise
        return operacion

    def pila_actual(self) -> list[Operacion]:
        return self._pila.a_lista()

    def tamano_pila(self) -> int:
        return len(self._pila)

    def listar(self, limite: int = 100) -> list[dict]:
        filas = self.db.consultar(
            "SELECT id, tipo, descripcion, detalles, fecha, deshecho "
            "FROM operaciones ORDER BY id DESC LIMIT ?", (limite,),
        )
        return [dict(fila) for fila in filas]
