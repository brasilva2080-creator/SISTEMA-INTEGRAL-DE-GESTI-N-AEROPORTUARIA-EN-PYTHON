"""Pruebas integrales de los servicios y reglas del sistema aeroportuario."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import modules.checkin as checkin_module
import modules.reservas as reservas_module
from database import Database
from modules.abordaje import Abordaje
from modules.actividad import Historial
from modules.checkin import Checkin
from modules.dashboard import Dashboard
from modules.gestion_pasajeros import GestionPasajeros
from modules.gestion_vuelos import GestionVuelos
from modules.reservas import Reservas
from modules.rutas import Rutas
from seed import cargar_datos_prueba


class BaseSistema(unittest.TestCase):
    """Crea una base SQLite aislada y sembrada para cada prueba."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)
        self.db = Database(self.tmp_path / "aeropuerto_test.db")
        self.assertTrue(cargar_datos_prueba(self.db))

        self.historial = Historial(self.db)
        self.vuelos = GestionVuelos(self.db, self.historial)
        self.pasajeros = GestionPasajeros(self.db, self.historial)
        self.reservas = Reservas(self.db, self.historial, self.vuelos, self.pasajeros)
        self.checkin = Checkin(self.db, self.historial, self.reservas, self.vuelos)
        self.abordaje = Abordaje(self.db, self.checkin, self.reservas, self.vuelos)
        self.rutas = Rutas(self.db, self.historial)
        self.dashboard = Dashboard(self.db, self.vuelos)

        self._docs_reservas = reservas_module.COMPROBANTES_DIR
        self._docs_checkin = checkin_module.COMPROBANTES_DIR
        self.docs = self.tmp_path / "comprobantes"
        self.docs.mkdir()
        reservas_module.COMPROBANTES_DIR = self.docs
        checkin_module.COMPROBANTES_DIR = self.docs

        self.aeronave = next(
            a for a in self.vuelos.listar_aeronaves() if a["capacidad"] >= 10
        )

    def tearDown(self) -> None:
        reservas_module.COMPROBANTES_DIR = self._docs_reservas
        checkin_module.COMPROBANTES_DIR = self._docs_checkin
        self.db.cerrar()
        self._tmp.cleanup()

    # ------------------------------------------------------------------
    def crear_pasajero(self, documento: str, nombres: str = "Pasajero",
                       apellidos: str = "De Prueba"):
        return self.pasajeros.registrar(
            nombres, apellidos, documento, f"{documento}@example.com", "999888777"
        )

    def crear_vuelo(self, capacidad: int = 10):
        salida = datetime.now() + timedelta(days=6)
        return self.vuelos.registrar(
            "LIM", "CUZ", salida.strftime("%Y-%m-%d"), "09:15",
            self.aeronave["id"], capacidad, "A09", 250.00,
        )


class PruebasVuelos(BaseSistema):
    def test_registro_de_vuelo_con_codigo_automatico(self):
        vuelo = self.crear_vuelo()
        self.assertEqual(vuelo.codigo, "AER109")
        self.assertEqual(vuelo.estado, "Programado")
        self.assertEqual(vuelo.origen_codigo, "LIM")
        self.assertEqual(vuelo.destino_codigo, "CUZ")
        self.assertEqual(vuelo.puerta, "A09")
        self.assertEqual(self.historial.tamano_pila(), 1)

        encontrado = self.vuelos.listar(texto="AER109")
        self.assertEqual([v.codigo for v in encontrado], ["AER109"])
        self.assertIsNotNone(self.vuelos.obtener_por_codigo("aer109"))

    def test_registro_de_vuelo_valida_datos(self):
        fecha = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")
        with self.assertRaises(ValueError):
            self.vuelos.registrar(
                "LIM", "LIM", fecha, "08:00", self.aeronave["id"], 10, "A01", 100
            )
        with self.assertRaises(ValueError):
            self.vuelos.registrar(
                "LIM", "CUZ", fecha, "08:00", self.aeronave["id"],
                int(self.aeronave["capacidad"]) + 1, "A01", 100,
            )
        with self.assertRaises(ValueError):
            self.vuelos.registrar(
                "LIM", "CUZ", "2020-01-01", "08:00", self.aeronave["id"], 10,
                "A01", 100,
            )
        with self.assertRaises(ValueError):
            self.vuelos.registrar(
                "LIM", "CUZ", fecha, "08:00", self.aeronave["id"], 10, "A01", -10
            )

    def test_deshacer_registro_de_vuelo(self):
        vuelo = self.crear_vuelo()
        self.historial.deshacer_ultima()
        self.assertIsNone(self.vuelos.obtener_por_codigo(vuelo.codigo))
        self.assertEqual(self.db.escalar(
            "SELECT COUNT(*) FROM vuelos WHERE codigo = ?", (vuelo.codigo,)
        ), 0)

    def test_edicion_de_vuelo_y_deshacer(self):
        vuelo = self.vuelos.obtener_por_codigo("AER101")
        assert vuelo
        fecha = (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d")
        actualizado = self.vuelos.actualizar(
            vuelo.id, "LIM", "CUZ", fecha, "11:45", vuelo.aeronave_id,
            vuelo.capacidad, "A11", 225.50,
        )
        self.assertEqual(actualizado.puerta, "A11")
        self.assertEqual(actualizado.precio, 225.50)
        self.assertEqual(actualizado.fecha_salida, f"{fecha} 11:45")

        self.historial.deshacer_ultima()
        restaurado = self.vuelos.obtener(vuelo.id)
        assert restaurado
        self.assertEqual(restaurado.puerta, "A03")
        self.assertEqual(restaurado.precio, 189.90)

    def test_edicion_no_permite_capacidad_menor_a_reservas(self):
        vuelo = self.vuelos.obtener_por_codigo("AER101")
        assert vuelo
        fecha, hora = vuelo.fecha_salida.split()
        with self.assertRaises(ValueError):
            self.vuelos.actualizar(
                vuelo.id, "LIM", "CUZ", fecha, hora, vuelo.aeronave_id,
                1, vuelo.puerta, vuelo.precio,
            )

    def test_cambio_de_estado_y_transiciones_invalidas(self):
        vuelo = self.vuelos.obtener_por_codigo("AER101")
        assert vuelo
        self.vuelos.cambiar_estado(vuelo.id, "Check-in abierto")
        self.assertEqual(self.vuelos.obtener(vuelo.id).estado, "Check-in abierto")
        with self.assertRaises(ValueError):
            self.vuelos.cambiar_estado(vuelo.id, "Completado")
        self.historial.deshacer_ultima()
        self.assertEqual(self.vuelos.obtener(vuelo.id).estado, "Programado")

    def test_undo_protegido_por_abordaje_en_curso(self):
        vuelo = self.vuelos.obtener_por_codigo("AER104")
        assert vuelo
        self.vuelos.cambiar_estado(vuelo.id, "En vuelo")
        with self.assertRaises(ValueError):
            self.historial.deshacer_ultima()
        self.assertEqual(self.vuelos.obtener(vuelo.id).estado, "En vuelo")
        self.assertEqual(self.historial.tamano_pila(), 1)

    def test_cancelacion_de_vuelo_cancela_reservas_y_se_deshace(self):
        vuelo = self.vuelos.obtener_por_codigo("AER105")
        assert vuelo
        self.vuelos.cancelar(vuelo.id)
        self.assertEqual(self.vuelos.obtener(vuelo.id).estado, "Cancelado")
        self.assertEqual(self.reservas.obtener_por_codigo("RES-100013").estado, "Cancelada")
        self.assertEqual(self.reservas.obtener_por_codigo("RES-100014").estado, "Cancelada")

        self.historial.deshacer_ultima()
        self.assertEqual(self.vuelos.obtener(vuelo.id).estado, "Programado")
        self.assertEqual(self.reservas.obtener_por_codigo("RES-100013").estado, "Confirmada")
        self.assertEqual(self.reservas.obtener_por_codigo("RES-100014").estado, "Pendiente")

    def test_no_cancela_vuelo_con_pasajeros_abordados(self):
        vuelo = self.vuelos.obtener_por_codigo("AER104")
        assert vuelo
        with self.assertRaises(ValueError):
            self.vuelos.cancelar(vuelo.id)


class PruebasPasajeros(BaseSistema):
    def test_registro_y_busqueda_de_pasajero(self):
        pasajero = self.crear_pasajero("71999001", "Lucía", "Mendoza Paz")
        self.assertEqual(pasajero.codigo, "PAS-0013")
        self.assertEqual(pasajero.nombre_completo, "Lucía Mendoza Paz")
        self.assertEqual(self.pasajeros.obtener_por_documento("71999001").id, pasajero.id)
        self.assertEqual(self.pasajeros.buscar_lineal("71999001").id, pasajero.id)
        self.assertEqual(self.pasajeros.buscar_lineal("Lucía").id, pasajero.id)

    def test_documento_duplicado_y_correo_invalido(self):
        self.crear_pasajero("71999002")
        with self.assertRaises(ValueError):
            self.crear_pasajero("71999002", "Otro", "Pasajero")
        with self.assertRaises(ValueError):
            self.pasajeros.registrar(
                "Nombre", "Apellido", "71999003", "correo-invalido", "999888777"
            )

    def test_historial_lifo_actualiza_y_elimina(self):
        pasajero = self.crear_pasajero("71999004")
        original = self.pasajeros.obtener(pasajero.id).email
        self.pasajeros.actualizar(
            pasajero.id, "Nombre", "Actualizado", "71999004",
            "nuevo@example.com", "988777666",
        )
        self.assertEqual(self.pasajeros.obtener(pasajero.id).email, "nuevo@example.com")
        self.assertEqual(self.historial.tamano_pila(), 2)

        self.historial.deshacer_ultima()
        self.assertEqual(self.pasajeros.obtener(pasajero.id).email, original)
        self.historial.deshacer_ultima()
        self.assertIsNone(self.pasajeros.obtener(pasajero.id))
        self.assertEqual(self.historial.tamano_pila(), 0)

    def test_historial_de_reservas_del_pasajero(self):
        pasajero = self.pasajeros.obtener_por_documento("71000001")
        assert pasajero
        historial = self.pasajeros.historial_reservas(pasajero.id)
        self.assertEqual(len(historial), 2)
        self.assertTrue(all("vuelo" in fila for fila in historial))


class PruebasReservas(BaseSistema):
    def test_venta_de_reserva_y_asiento_unico(self):
        vuelo = self.vuelos.obtener_por_codigo("AER108")
        assert vuelo
        self.assertEqual(self.reservas.mapa_asientos(vuelo.id).disponibles, 42)

        pasajero = self.pasajeros.obtener_por_documento("71000001")
        otro = self.pasajeros.obtener_por_documento("71000002")
        assert pasajero and otro
        reserva = self.reservas.registrar(vuelo.id, pasajero.id, "1A")
        self.assertEqual(reserva.estado, "Confirmada")
        self.assertEqual(reserva.asiento, "1A")
        mapa = self.reservas.mapa_asientos(vuelo.id)
        self.assertEqual(mapa.disponibles, 41)
        self.assertEqual(mapa.estados["1A"], "Ocupado")

        with self.assertRaises(ValueError):
            self.reservas.registrar(vuelo.id, otro.id, "1A")
        with self.assertRaises(ValueError):
            self.reservas.registrar(vuelo.id, pasajero.id, "1B")
        with self.assertRaises(ValueError):
            self.reservas.registrar(vuelo.id, otro.id, "99Z")

    def test_cancelar_reserva_libera_asiento_y_pasajero(self):
        vuelo = self.vuelos.obtener_por_codigo("AER108")
        pasajero = self.pasajeros.obtener_por_documento("71000001")
        otro = self.pasajeros.obtener_por_documento("71000002")
        assert vuelo and pasajero and otro
        reserva = self.reservas.registrar(vuelo.id, pasajero.id, "2A")
        self.reservas.cancelar(reserva.id)
        self.assertEqual(self.reservas.obtener_por_codigo(reserva.codigo).estado, "Cancelada")
        self.assertEqual(self.reservas.mapa_asientos(vuelo.id).estados["2A"], "Disponible")

        nueva = self.reservas.registrar(vuelo.id, otro.id, "2A")
        self.assertNotEqual(nueva.codigo, reserva.codigo)
        self.assertEqual(self.reservas.mapa_asientos(vuelo.id).estados["2A"], "Ocupado")

    def test_reserva_pendiente_debe_confirmarse_antes_del_checkin(self):
        vuelo = self.vuelos.obtener_por_codigo("AER108")
        pasajero = self.pasajeros.obtener_por_documento("71000003")
        assert vuelo and pasajero
        reserva = self.reservas.registrar(vuelo.id, pasajero.id, "3A", confirmar=False)
        self.assertEqual(reserva.estado, "Pendiente")
        with self.assertRaises(ValueError):
            self.checkin.registrar(reserva.codigo, 1, 10)
        self.reservas.confirmar(reserva.id)
        registro = self.checkin.registrar(reserva.codigo, 1, 10)
        self.assertEqual(registro.reserva_id, reserva.id)

    def test_no_reserva_en_vuelo_cancelado_o_en_abordaje(self):
        pasajero = self.pasajeros.obtener_por_documento("71000004")
        cancelado = self.vuelos.obtener_por_codigo("AER107")
        abordaje = self.vuelos.obtener_por_codigo("AER104")
        assert pasajero and cancelado and abordaje
        with self.assertRaises(ValueError):
            self.reservas.registrar(cancelado.id, pasajero.id, "1A")
        with self.assertRaises(ValueError):
            self.reservas.registrar(abordaje.id, pasajero.id, "9A")

    def test_limite_de_capacidad(self):
        vuelo = self.crear_vuelo(capacidad=4)
        pasajeros = [
            self.pasajeros.obtener_por_documento(f"7100000{i}") for i in range(1, 6)
        ]
        for asiento, pasajero in zip(("1A", "1B", "1C", "1D"), pasajeros[:4]):
            assert pasajero
            self.reservas.registrar(vuelo.id, pasajero.id, asiento)
        self.assertEqual(self.vuelos.obtener(vuelo.id).ocupados, 4)
        assert pasajeros[4]
        with self.assertRaises(ValueError):
            self.reservas.registrar(vuelo.id, pasajeros[4].id, "2A")

    def test_comprobante_de_reserva(self):
        vuelo = self.vuelos.obtener_por_codigo("AER108")
        pasajero = self.pasajeros.obtener_por_documento("71000001")
        assert vuelo and pasajero
        reserva = self.reservas.registrar(vuelo.id, pasajero.id, "4A")
        texto, ruta = self.reservas.comprobante(reserva.codigo)
        self.assertTrue(ruta.exists())
        self.assertEqual(ruta.parent, self.docs)
        self.assertIn(reserva.codigo, texto)
        self.assertIn("aeroandes", texto.lower())
        self.assertIn("No procesa pagos reales", texto)


class PruebasCheckin(BaseSistema):
    def test_checkin_equipaje_y_tarjeta(self):
        registro = self.checkin.registrar("RES-100001", 2, 25.5)
        self.assertEqual(registro.reserva_codigo, "RES-100001")
        self.assertEqual(registro.cantidad_equipaje, 2)
        self.assertEqual(registro.peso_total, 25.5)
        self.assertTrue(registro.tarjeta_embarque.startswith("TB-"))
        vuelo = self.vuelos.obtener_por_codigo("AER101")
        assert vuelo
        self.assertEqual(vuelo.estado, "Check-in abierto")
        self.assertEqual(self.db.escalar(
            "SELECT COUNT(*) FROM equipajes WHERE checkin_id = ?", (registro.id,)
        ), 1)

        texto, ruta, _ = self.checkin.tarjeta_embarque("RES-100001")
        self.assertTrue(ruta.exists())
        self.assertIn("TARJETA DE EMBARQUE", texto)
        self.assertIn("RES-100001", self.reservas.obtener_por_codigo("RES-100001").codigo)

    def test_checkin_rechaza_pendiente_duplicado_y_cancelado(self):
        with self.assertRaises(ValueError):
            self.checkin.registrar("RES-100003", 1, 10)
        with self.assertRaises(ValueError):
            self.checkin.registrar("RES-100005", 1, 10)
        with self.assertRaises(ValueError):
            self.checkin.registrar("RES-100019", 1, 10)
        with self.assertRaises(ValueError):
            self.checkin.registrar("RES-INEXISTENTE", 1, 10)

    def test_checkin_valida_equipaje(self):
        with self.assertRaises(ValueError):
            self.checkin.registrar("RES-100001", 0, 10)
        with self.assertRaises(ValueError):
            self.checkin.registrar("RES-100001", 2, 0)
        with self.assertRaises(ValueError):
            self.checkin.registrar("RES-100001", 1, 40)
        with self.assertRaises(ValueError):
            self.checkin.registrar("RES-100001", "muchas", 10)
        self.assertEqual(self.checkin.obtener_por_reserva(
            self.reservas.obtener_por_codigo("RES-100001").id
        ), None)

    def test_deshacer_checkin_restaura_vuelo_y_equipaje(self):
        registro = self.checkin.registrar("RES-100001", 1, 14)
        self.historial.deshacer_ultima()
        self.assertIsNone(self.checkin.obtener_por_reserva(registro.reserva_id))
        self.assertEqual(self.db.escalar(
            "SELECT COUNT(*) FROM equipajes WHERE checkin_id = ?", (registro.id,)
        ), 0)
        self.assertEqual(self.vuelos.obtener_por_codigo("AER101").estado, "Programado")
        self.assertEqual(self.historial.listar(1)[0]["deshecho"], 1)


class PruebasAbordaje(BaseSistema):
    def test_cola_fifo_y_orden_de_abordaje(self):
        vuelo = self.vuelos.obtener_por_codigo("AER104")
        assert vuelo
        cola = self.abordaje.obtener_cola(vuelo.id)
        self.assertEqual(
            [fila["reserva_codigo"] for fila in cola],
            ["RES-100011", "RES-100012"],
        )
        self.assertEqual([fila["posicion"] for fila in cola], [1, 2])
        resumen = self.abordaje.resumen(vuelo.id)
        self.assertEqual(resumen["total_checkin"], 4)
        self.assertEqual(resumen["abordados"], 2)
        self.assertEqual(resumen["en_cola"], 2)
        self.assertEqual(resumen["porcentaje"], 50.0)

        primero = self.abordaje.procesar_siguiente(vuelo.id)
        self.assertEqual(primero["reserva_codigo"], "RES-100011")
        segundo = self.abordaje.procesar_siguiente(vuelo.id)
        self.assertEqual(segundo["reserva_codigo"], "RES-100012")
        self.assertEqual(segundo["posicion_abordaje"], 4)
        with self.assertRaises(ValueError):
            self.abordaje.procesar_siguiente(vuelo.id)

        resumen = self.abordaje.resumen(vuelo.id)
        self.assertEqual(resumen["abordados"], 4)
        self.assertEqual(resumen["en_cola"], 0)

    def test_validaciones_de_la_cola(self):
        vuelo = self.vuelos.obtener_por_codigo("AER104")
        assert vuelo
        abordado = self.reservas.obtener_por_codigo("RES-100009")
        sin_checkin = self.reservas.obtener_por_codigo("RES-100013")
        assert abordado and sin_checkin
        with self.assertRaises(ValueError):
            self.abordaje.agregar_a_cola(abordado.id)
        with self.assertRaises(ValueError):
            self.abordaje.agregar_a_cola(sin_checkin.id)

    def test_agregar_todos_y_cerrar_abordaje(self):
        vuelo = self.vuelos.obtener_por_codigo("AER102")
        assert vuelo
        agregados, omitidos = self.abordaje.agregar_todos(vuelo.id)
        self.assertEqual((agregados, omitidos), (4, 0))
        self.assertEqual(self.vuelos.obtener(vuelo.id).estado, "Abordaje")
        cola = self.abordaje.obtener_cola(vuelo.id)
        self.assertEqual(len(cola), 4)
        self.assertEqual(cola[0]["reserva_codigo"], "RES-100006")

        for _ in range(4):
            self.abordaje.procesar_siguiente(vuelo.id)
        self.assertEqual(self.abordaje.resumen(vuelo.id)["abordados"], 4)
        self.abordaje.finalizar(vuelo.id)
        self.assertEqual(self.vuelos.obtener(vuelo.id).estado, "En vuelo")

    def test_finalizar_protege_pendientes_y_cola(self):
        vuelo = self.vuelos.obtener_por_codigo("AER104")
        assert vuelo
        with self.assertRaises(ValueError):
            self.abordaje.finalizar(vuelo.id)
        resultado = self.abordaje.finalizar(vuelo.id, forzar=True)
        self.assertTrue(resultado["forzado"])
        self.assertEqual(self.vuelos.obtener(vuelo.id).estado, "En vuelo")


class PruebasRutas(BaseSistema):
    def test_resumen_y_ruta_bfs(self):
        resumen = self.rutas.resumen()
        self.assertEqual(resumen["aeropuertos"], 5)
        self.assertEqual(resumen["rutas"], 7)
        self.assertTrue(resumen["conexo"])

        resultado = self.rutas.calcular_ruta("CUZ", "PIU")
        self.assertEqual(resultado["camino"], ["CUZ", "AQP", "PIU"])
        self.assertEqual(resultado["distancia_km"], 1495.0)
        self.assertEqual(resultado["duracion_min"], 205)
        self.assertEqual(resultado["escalas"], 1)
        self.assertIn("Cusco", resultado["ciudades"][0])
        self.assertEqual(self.rutas.calcular_ruta("LIM", "CUZ")["escalas"], 0)

    def test_registro_de_aeropuerto_y_ruta(self):
        self.rutas.registrar_aeropuerto(
            "IQT", "Aeropuerto Internacional Coronel FAP Francisco Secada Vignetta",
            "Iquitos", "Perú", -3.7847, -73.3088,
        )
        ruta = self.rutas.registrar_ruta("LIM", "IQT", 900, 95)
        self.assertEqual(ruta.distancia_km, 900)
        grafo = self.rutas.construir_grafo()
        self.assertEqual(dict(grafo.conexiones_de("LIM"))["IQT"], 900.0)
        self.assertEqual(
            self.rutas.calcular_ruta("IQT", "CUZ")["camino"],
            ["IQT", "LIM", "CUZ"],
        )
        with self.assertRaises(ValueError):
            self.rutas.registrar_ruta("IQT", "LIM", 900, 95)
        with self.assertRaises(ValueError):
            self.rutas.registrar_aeropuerto("IQT", "Duplicado", "Iquitos")

    def test_ruta_inexistente_y_validaciones(self):
        self.rutas.registrar_aeropuerto(
            "IQT", "Aeropuerto de Iquitos", "Iquitos", "Perú", -3.78, -73.30
        )
        with self.assertRaises(ValueError):
            self.rutas.calcular_ruta("IQT", "CUZ")
        with self.assertRaises(ValueError):
            self.rutas.registrar_ruta("LIM", "LIM", 10, 10)
        with self.assertRaises(ValueError):
            self.rutas.registrar_ruta("LIM", "IQT", -1, 10)
        with self.assertRaises(ValueError):
            self.rutas.registrar_ruta("LIM", "XXX", 900, 95)

    def test_deshacer_ruta_y_aeropuerto_en_orden_lifo(self):
        self.rutas.registrar_aeropuerto(
            "IQT", "Aeropuerto de Iquitos", "Iquitos", "Perú", -3.78, -73.30
        )
        self.rutas.registrar_ruta("LIM", "IQT", 900, 95)
        self.assertEqual(self.rutas.resumen()["rutas"], 8)

        self.historial.deshacer_ultima()
        self.assertEqual(self.rutas.resumen()["rutas"], 7)
        self.assertIsNotNone(self.rutas.obtener_aeropuerto("IQT"))
        self.historial.deshacer_ultima()
        self.assertIsNone(self.rutas.obtener_aeropuerto("IQT"))


class PruebasDashboard(BaseSistema):
    def test_metricas_y_graficos(self):
        metricas = self.dashboard.metricas()
        self.assertEqual(metricas["total_vuelos"], 8)
        self.assertEqual(metricas["programados"], 4)
        self.assertEqual(metricas["checkin"], 1)
        self.assertEqual(metricas["abordaje"], 1)
        self.assertEqual(metricas["completados"], 1)
        self.assertEqual(metricas["cancelados"], 1)
        self.assertEqual(metricas["total_pasajeros"], 12)
        self.assertEqual(metricas["total_reservas"], 19)
        self.assertEqual(metricas["reservas_confirmadas"], 14)
        self.assertEqual(metricas["checkins"], 10)
        self.assertIsNotNone(metricas["proxima"])

    def test_distribuciones_y_ocupacion(self):
        por_estado = self.dashboard.estados_vuelos()
        self.assertEqual(sum(por_estado.values()), 8)
        reservas = self.dashboard.reservas_por_estado()
        self.assertEqual(reservas["Pendiente"], 3)
        self.assertEqual(reservas["Confirmada"], 14)
        self.assertEqual(reservas["Cancelada"], 2)

        ocupacion = self.dashboard.ocupacion_vuelos()
        self.assertTrue(ocupacion)
        for fila in ocupacion:
            self.assertGreaterEqual(fila["porcentaje"], 0)
            self.assertLessEqual(fila["porcentaje"], 100)
            self.assertLessEqual(fila["ocupados"], fila["capacidad"])

    def test_semilla_es_idempotente(self):
        self.assertFalse(cargar_datos_prueba(self.db))
        self.assertEqual(self.db.escalar("SELECT COUNT(*) FROM pasajeros"), 12)


if __name__ == "__main__":
    unittest.main()
