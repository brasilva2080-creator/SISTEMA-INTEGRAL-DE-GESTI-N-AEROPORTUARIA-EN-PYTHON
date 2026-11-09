"""Lista doblemente enlazada utilizada para administrar colecciones reales."""
from __future__ import annotations

from typing import Any, Callable, Generic, Iterator, TypeVar

from .ordenamiento import merge_sort

T = TypeVar("T")


class _Nodo(Generic[T]):
    __slots__ = ("dato", "anterior", "siguiente")

    def __init__(self, dato: T) -> None:
        self.dato = dato
        self.anterior: _Nodo[T] | None = None
        self.siguiente: _Nodo[T] | None = None


class ListaDoble(Generic[T]):
    """Contenedor enlazado con operaciones de inserción, búsqueda y orden."""

    def __init__(self, valores: list[T] | None = None) -> None:
        self._cabeza: _Nodo[T] | None = None
        self._cola: _Nodo[T] | None = None
        self._tamano = 0
        if valores:
            for valor in valores:
                self.agregar(valor)

    def __len__(self) -> int:
        return self._tamano

    def __bool__(self) -> bool:
        return self._tamano > 0

    def __iter__(self) -> Iterator[T]:
        actual = self._cabeza
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente

    def __getitem__(self, indice: int) -> T:
        if indice < 0:
            indice += self._tamano
        if indice < 0 or indice >= self._tamano:
            raise IndexError("Índice fuera de rango")
        actual = self._cabeza if indice <= self._tamano // 2 else self._cola
        if indice <= self._tamano // 2:
            for _ in range(indice):
                assert actual is not None
                actual = actual.siguiente
        else:
            for _ in range(self._tamano - 1 - indice):
                assert actual is not None
                actual = actual.anterior
        assert actual is not None
        return actual.dato

    def agregar(self, dato: T) -> None:
        nodo = _Nodo(dato)
        if self._cola is None:
            self._cabeza = self._cola = nodo
        else:
            nodo.anterior = self._cola
            self._cola.siguiente = nodo
            self._cola = nodo
        self._tamano += 1

    append = agregar

    def insertar(self, indice: int, dato: T) -> None:
        if indice <= 0:
            nodo = _Nodo(dato)
            if self._cabeza is None:
                self._cabeza = self._cola = nodo
            else:
                nodo.siguiente = self._cabeza
                self._cabeza.anterior = nodo
                self._cabeza = nodo
            self._tamano += 1
            return
        if indice >= self._tamano:
            self.agregar(dato)
            return
        actual = self._cabeza
        for _ in range(indice):
            assert actual is not None
            actual = actual.siguiente
        assert actual is not None
        nodo = _Nodo(dato)
        nodo.anterior = actual.anterior
        nodo.siguiente = actual
        if actual.anterior:
            actual.anterior.siguiente = nodo
        actual.anterior = nodo
        self._tamano += 1

    def eliminar(self, dato: T) -> bool:
        actual = self._cabeza
        while actual is not None:
            if actual.dato == dato:
                if actual.anterior:
                    actual.anterior.siguiente = actual.siguiente
                else:
                    self._cabeza = actual.siguiente
                if actual.siguiente:
                    actual.siguiente.anterior = actual.anterior
                else:
                    self._cola = actual.anterior
                self._tamano -= 1
                return True
            actual = actual.siguiente
        return False

    def filtrar(self, predicado: Callable[[T], bool]) -> "ListaDoble[T]":
        return ListaDoble([dato for dato in self if predicado(dato)])

    def buscar(self, predicado: Callable[[T], bool]) -> T | None:
        for dato in self:
            if predicado(dato):
                return dato
        return None

    def ordenar(self, clave: Callable[[T], Any] | None = None,
                reverso: bool = False) -> "ListaDoble[T]":
        """Aplica merge sort y reconstruye los enlaces de la lista."""
        ordenados = merge_sort(list(self), clave=clave, reverso=reverso)
        self._cabeza = self._cola = None
        self._tamano = 0
        for dato in ordenados:
            self.agregar(dato)
        return self

    def a_lista(self) -> list[T]:
        return list(self)

    def limpiar(self) -> None:
        self._cabeza = self._cola = None
        self._tamano = 0

    def a_texto(self, separador: str = " → ") -> str:
        return separador.join(str(dato) for dato in self)
