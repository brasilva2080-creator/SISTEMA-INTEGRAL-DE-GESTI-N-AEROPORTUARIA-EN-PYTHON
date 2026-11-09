"""Cola FIFO enlazada para el proceso de abordaje."""
from __future__ import annotations

from typing import Generic, Iterator, TypeVar

T = TypeVar("T")


class _NodoCola(Generic[T]):
    __slots__ = ("dato", "siguiente")

    def __init__(self, dato: T) -> None:
        self.dato = dato
        self.siguiente: _NodoCola[T] | None = None


class Cola(Generic[T]):
    """Cola FIFO: el primero en entrar es el primero en salir."""

    def __init__(self) -> None:
        self._frente: _NodoCola[T] | None = None
        self._final: _NodoCola[T] | None = None
        self._tamano = 0

    def __len__(self) -> int:
        return self._tamano

    def __bool__(self) -> bool:
        return self._tamano > 0

    def __iter__(self) -> Iterator[T]:
        actual = self._frente
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente

    def encolar(self, dato: T) -> None:
        nodo = _NodoCola(dato)
        if self._final is None:
            self._frente = self._final = nodo
        else:
            self._final.siguiente = nodo
            self._final = nodo
        self._tamano += 1

    enqueue = encolar

    def desencolar(self) -> T:
        if self._frente is None:
            raise IndexError("La cola está vacía.")
        nodo = self._frente
        self._frente = nodo.siguiente
        if self._frente is None:
            self._final = None
        self._tamano -= 1
        return nodo.dato

    dequeue = desencolar

    def frente(self) -> T:
        if self._frente is None:
            raise IndexError("La cola está vacía.")
        return self._frente.dato

    peek = frente

    def esta_vacia(self) -> bool:
        return self._tamano == 0

    def contiene(self, predicado) -> bool:
        return any(predicado(dato) for dato in self)

    def a_lista(self) -> list[T]:
        return list(self)

    def limpiar(self) -> None:
        self._frente = self._final = None
        self._tamano = 0
