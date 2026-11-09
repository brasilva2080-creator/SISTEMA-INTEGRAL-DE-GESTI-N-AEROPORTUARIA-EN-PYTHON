"""Grafo no dirigido ponderado y búsqueda de rutas con BFS/DFS."""
from __future__ import annotations

from collections import deque
from typing import Any


class Grafo:
    """Grafo de aeropuertos (vértices) y rutas aéreas (aristas).

    La representación interna es un diccionario de adyacencia. Cada vértice
    guarda sus vecinos y el peso (distancia) de la conexión.
    """

    def __init__(self) -> None:
        self._adyacencia: dict[str, dict[str, dict[str, Any]]] = {}

    def __len__(self) -> int:
        return len(self._adyacencia)

    def agregar_vertice(self, vertice: str, datos: dict[str, Any] | None = None) -> None:
        self._adyacencia.setdefault(vertice, {})
        if datos is not None:
            self._adyacencia[vertice]["__datos__"] = datos

    def obtener_vertice(self, vertice: str) -> dict[str, Any] | None:
        return self._adyacencia.get(vertice, {}).get("__datos__")

    def tiene_vertice(self, vertice: str) -> bool:
        return vertice in self._adyacencia

    def agregar_arista(self, origen: str, destino: str, peso: float = 1.0,
                       datos: dict[str, Any] | None = None) -> None:
        if origen not in self._adyacencia or destino not in self._adyacencia:
            raise ValueError("Ambos vértices deben existir en el grafo.")
        if origen == destino:
            raise ValueError("Una ruta no puede unir un aeropuerto consigo mismo.")
        conexion = datos or {}
        conexion["peso"] = float(peso)
        self._adyacencia[origen][destino] = dict(conexion)
        self._adyacencia[destino][origen] = dict(conexion)

    def vecinos(self, vertice: str) -> dict[str, dict[str, Any]]:
        return {
            vecino: datos
            for vecino, datos in self._adyacencia.get(vertice, {}).items()
            if vecino != "__datos__"
        }

    def vertices(self) -> list[str]:
        return list(self._adyacencia.keys())

    def aristas(self) -> list[tuple[str, str, float]]:
        vistas: set[tuple[str, str]] = set()
        resultado: list[tuple[str, str, float]] = []
        for origen in self._adyacencia:
            for destino, datos in self.vecinos(origen).items():
                clave = tuple(sorted((origen, destino)))
                if clave not in vistas:
                    vistas.add(clave)
                    resultado.append((origen, destino, float(datos.get("peso", 1))))
        return resultado

    def bfs(self, inicio: str, fin: str) -> list[str]:
        """Ruta con menos conexiones (anchura). Devuelve [] si no existe."""
        if inicio not in self._adyacencia or fin not in self._adyacencia:
            return []
        if inicio == fin:
            return [inicio]

        visitados = {inicio}
        cola: deque[str] = deque([inicio])
        anterior: dict[str, str] = {}

        while cola:
            actual = cola.popleft()
            for vecino in self.vecinos(actual):
                if vecino in visitados:
                    continue
                visitados.add(vecino)
                anterior[vecino] = actual
                if vecino == fin:
                    return self._reconstruir(anterior, inicio, fin)
                cola.append(vecino)
        return []

    def dfs(self, inicio: str, fin: str) -> list[str]:
        """Ruta encontrada mediante búsqueda en profundidad."""
        if inicio not in self._adyacencia or fin not in self._adyacencia:
            return []
        pila = [inicio]
        visitados: set[str] = set()
        anterior: dict[str, str] = {}
        while pila:
            actual = pila.pop()
            if actual in visitados:
                continue
            visitados.add(actual)
            if actual == fin:
                return self._reconstruir(anterior, inicio, fin)
            for vecino in self.vecinos(actual):
                if vecino not in visitados:
                    anterior.setdefault(vecino, actual)
                    pila.append(vecino)
        return []

    def recorrido_bfs(self, inicio: str) -> list[str]:
        """Recorrido completo por niveles, útil para mostrar conexiones."""
        if inicio not in self._adyacencia:
            return []
        visitados = {inicio}
        cola: deque[str] = deque([inicio])
        orden: list[str] = []
        while cola:
            actual = cola.popleft()
            orden.append(actual)
            for vecino in self.vecinos(actual):
                if vecino not in visitados:
                    visitados.add(vecino)
                    cola.append(vecino)
        return orden

    def distancia(self, ruta: list[str]) -> float:
        total = 0.0
        for origen, destino in zip(ruta, ruta[1:]):
            datos = self.vecinos(origen).get(destino, {})
            total += float(datos.get("peso", 0))
        return total

    @staticmethod
    def _reconstruir(anterior: dict[str, str], inicio: str, fin: str) -> list[str]:
        ruta = [fin]
        actual = fin
        while actual != inicio:
            actual = anterior.get(actual, "")
            if not actual:
                return []
            ruta.append(actual)
        return list(reversed(ruta))

    def conexiones_de(self, vertice: str) -> list[tuple[str, float]]:
        return [(destino, float(datos.get("peso", 0)))
                for destino, datos in self.vecinos(vertice).items()]

    def es_conexo(self) -> bool:
        if not self._adyacencia:
            return True
        inicio = next(iter(self._adyacencia))
        return len(self.recorrido_bfs(inicio)) == len(self._adyacencia)
