"""Algoritmos de ordenamiento y búsqueda implementados desde cero."""
from __future__ import annotations

from typing import Any, Callable, Iterable, Sequence, TypeVar

T = TypeVar("T")


def merge_sort(valores: Sequence[T], clave: Callable[[T], Any] | None = None,
               reverso: bool = False) -> list[T]:
    """Ordenamiento por mezcla estable O(n log n).

    Se utiliza en las listas enlazadas y en la preparación de reportes.
    """
    clave = clave or (lambda valor: valor)
    datos = list(valores)
    if len(datos) <= 1:
        return datos

    mitad = len(datos) // 2
    izquierda = merge_sort(datos[:mitad], clave, reverso)
    derecha = merge_sort(datos[mitad:], clave, reverso)
    resultado: list[T] = []
    i = j = 0

    while i < len(izquierda) and j < len(derecha):
        comparacion = clave(izquierda[i]) <= clave(derecha[j])
        if comparacion != reverso:
            resultado.append(izquierda[i])
            i += 1
        else:
            resultado.append(derecha[j])
            j += 1

    resultado.extend(izquierda[i:])
    resultado.extend(derecha[j:])
    return resultado


def quick_sort(valores: Sequence[T], clave: Callable[[T], Any] | None = None,
               reverso: bool = False) -> list[T]:
    """Ordenamiento rápido con pivote central. Se incluye como alternativa."""
    clave = clave or (lambda valor: valor)
    datos = list(valores)
    if len(datos) <= 1:
        return datos
    pivote = clave(datos[len(datos) // 2])
    menores = [x for x in datos if clave(x) < pivote]
    iguales = [x for x in datos if clave(x) == pivote]
    mayores = [x for x in datos if clave(x) > pivote]
    ordenado = quick_sort(menores, clave) + iguales + quick_sort(mayores, clave)
    return list(reversed(ordenado)) if reverso else ordenado


def busqueda_lineal(valores: Iterable[T], predicado: Callable[[T], bool]) -> T | None:
    """Recorre la colección y devuelve el primer elemento que cumple el criterio."""
    for valor in valores:
        if predicado(valor):
            return valor
    return None


def busqueda_binaria(valores: Sequence[T], objetivo: T,
                     clave: Callable[[T], Any] | None = None) -> int:
    """Devuelve el índice del objetivo en una secuencia ordenada, o -1."""
    clave = clave or (lambda valor: valor)
    bajo, alto = 0, len(valores) - 1
    while bajo <= alto:
        medio = (bajo + alto) // 2
        valor_medio = clave(valores[medio])
        if valor_medio == objetivo:
            return medio
        if valor_medio < objetivo:
            bajo = medio + 1
        else:
            alto = medio - 1
    return -1
