"""Pila LIFO para el historial de operaciones y la función deshacer."""
from __future__ import annotations

from typing import Generic, Iterator, TypeVar

T = TypeVar("T")


class _NodoPila(Generic[T]):
    __slots__ = ("dato", "siguiente")

    def __init__(self, dato: T) -> None:
        self.dato = dato
        self.siguiente: _NodoPila[T] | None = None


class Pila(Generic[T]):
    """Pila LIFO: la última operación apilada es la primera en deshacerse."""

    def __init__(self) -> None:
        self._cima: _NodoPila[T] | None = None
        self._tamano = 0

    def __len__(self) -> int:
        return self._tamano

    def __bool__(self) -> bool:
        return self._tamano > 0

    def __iter__(self) -> Iterator[T]:
        actual = self._cima
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente

    def apilar(self, dato: T) -> None:
        nodo = _NodoPila(dato)
        nodo.siguiente = self._cima
        self._cima = nodo
        self._tamano += 1

    push = apilar

    def desapilar(self) -> T:
        if self._cima is None:
            raise IndexError("La pila está vacía.")
        nodo = self._cima
        self._cima = nodo.siguiente
        self._tamano -= 1
        return nodo.dato

    pop = desapilar

    def cima(self) -> T:
        if self._cima is None:
            raise IndexError("La pila está vacía.")
        return self._cima.dato

    peek = cima

    def esta_vacia(self) -> bool:
        return self._tamano == 0

    def a_lista(self) -> list[T]:
        return list(self)

    def limpiar(self) -> None:
        self._cima = None
        self._tamano = 0
