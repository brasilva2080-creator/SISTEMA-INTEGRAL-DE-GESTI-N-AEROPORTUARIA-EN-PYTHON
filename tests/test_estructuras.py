"""Pruebas de las estructuras de datos implementadas desde cero."""
from __future__ import annotations

import unittest

from structures import (Cola, Grafo, ListaDoble, Pila, busqueda_binaria,
                        busqueda_lineal, merge_sort, quick_sort)


class PruebasListaDoble(unittest.TestCase):
    def test_operaciones_basicas(self):
        lista = ListaDoble([3, 1, 2])
        self.assertEqual(len(lista), 3)
        self.assertEqual(lista[0], 3)
        self.assertEqual(lista[-1], 2)
        lista.insertar(1, 99)
        self.assertEqual(lista.a_lista(), [3, 99, 1, 2])
        self.assertTrue(lista.eliminar(1))
        self.assertEqual(lista.a_lista(), [3, 99, 2])
        self.assertFalse(lista.eliminar(1234))

    def test_filtrar_y_ordenar(self):
        lista = ListaDoble([5, 2, 9, 1, 7])
        pares = lista.filtrar(lambda n: n % 2 == 0)
        self.assertEqual(pares.a_lista(), [2])
        lista.ordenar()
        self.assertEqual(lista.a_lista(), [1, 2, 5, 7, 9])
        lista.ordenar(reverso=True)
        self.assertEqual(lista.a_lista(), [9, 7, 5, 2, 1])


class PruebasCola(unittest.TestCase):
    def test_fifo(self):
        cola = Cola()
        for valor in ("primero", "segundo", "tercero"):
            cola.encolar(valor)
        self.assertEqual(len(cola), 3)
        self.assertEqual(cola.frente(), "primero")
        self.assertEqual(cola.desencolar(), "primero")
        self.assertEqual(cola.desencolar(), "segundo")
        cola.encolar("cuarto")
        self.assertEqual(cola.a_lista(), ["tercero", "cuarto"])
        self.assertEqual(cola.desencolar(), "tercero")
        self.assertEqual(cola.desencolar(), "cuarto")
        self.assertTrue(cola.esta_vacia())
        with self.assertRaises(IndexError):
            cola.desencolar()


class PruebasPila(unittest.TestCase):
    def test_lifo(self):
        pila = Pila()
        pila.apilar("uno")
        pila.apilar("dos")
        pila.apilar("tres")
        self.assertEqual(pila.cima(), "tres")
        self.assertEqual(pila.desapilar(), "tres")
        self.assertEqual(pila.desapilar(), "dos")
        pila.apilar("cuatro")
        self.assertEqual(pila.a_lista(), ["cuatro", "uno"])
        self.assertEqual(len(pila), 2)
        pila.limpiar()
        self.assertTrue(pila.esta_vacia())
        with self.assertRaises(IndexError):
            pila.desapilar()


class PruebasGrafo(unittest.TestCase):
    def setUp(self):
        self.grafo = Grafo()
        for codigo in ("LIM", "CUZ", "AQP", "PIU", "TPP"):
            self.grafo.agregar_vertice(codigo, {"ciudad": codigo.title()})
        self.grafo.agregar_arista("LIM", "CUZ", 586)
        self.grafo.agregar_arista("CUZ", "AQP", 315)
        self.grafo.agregar_arista("LIM", "AQP", 767)
        self.grafo.agregar_arista("LIM", "PIU", 850)
        self.grafo.agregar_arista("TPP", "LIM", 618)

    def test_bfs_ruta_mas_corta_por_conexiones(self):
        ruta = self.grafo.bfs("CUZ", "PIU")
        self.assertEqual(ruta, ["CUZ", "LIM", "PIU"])
        self.assertEqual(self.grafo.distancia(ruta), 1436.0)

    def test_dfs_encuentra_una_ruta(self):
        ruta = self.grafo.dfs("TPP", "AQP")
        self.assertEqual(ruta[0], "TPP")
        self.assertEqual(ruta[-1], "AQP")
        self.assertIn("LIM", ruta)

    def test_conexiones_y_recorrido(self):
        vecinos = dict(self.grafo.conexiones_de("LIM"))
        self.assertIn("CUZ", vecinos)
        self.assertIn("PIU", vecinos)
        self.assertEqual(set(self.grafo.recorrido_bfs("LIM")), set(self.grafo.vertices()))
        self.assertTrue(self.grafo.es_conexo())

    def test_ruta_inexistente(self):
        self.grafo.agregar_vertice("IQT")
        self.assertEqual(self.grafo.bfs("LIM", "IQT"), [])
        self.assertEqual(self.grafo.bfs("XXX", "LIM"), [])


class PruebasOrdenamientoBusqueda(unittest.TestCase):
    def test_merge_sort_estable_y_quick_sort(self):
        datos = [("A", 3), ("B", 1), ("C", 3), ("D", 2)]
        ordenados = merge_sort(datos, clave=lambda x: x[1])
        self.assertEqual([x[0] for x in ordenados], ["B", "D", "A", "C"])
        self.assertEqual([x[1] for x in quick_sort(datos, clave=lambda x: x[1])],
                         [1, 2, 3, 3])

    def test_busqueda_lineal_y_binaria(self):
        datos = [1, 3, 5, 7, 9]
        self.assertEqual(busqueda_lineal(datos, lambda n: n == 7), 7)
        self.assertIsNone(busqueda_lineal(datos, lambda n: n == 8))
        self.assertEqual(busqueda_binaria(datos, 9), 4)
        self.assertEqual(busqueda_binaria(datos, 2), -1)


if __name__ == "__main__":
    unittest.main()
