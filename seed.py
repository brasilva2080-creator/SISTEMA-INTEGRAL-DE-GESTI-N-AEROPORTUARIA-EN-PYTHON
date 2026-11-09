"""Datos ficticios de demostración para el sistema aeroportuario."""
from __future__ import annotations

from datetime import datetime, timedelta

from database import Database


def _fecha(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def _sello(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def cargar_datos_prueba(db: Database) -> bool:
    """Carga aeropuertos, aeronaves, vuelos, pasajeros y reservas de ejemplo.

    Devuelve False si la base ya contiene datos y no se vuelve a sembrar.
    """
    if int(db.escalar("SELECT COUNT(*) FROM aeropuertos")) > 0:
        return False

    ahora = datetime.now().replace(second=0, microsecond=0)
    manana = (ahora + timedelta(days=1)).replace(hour=8, minute=15)
    salida_102 = ahora + timedelta(hours=4)
    salida_104 = ahora + timedelta(hours=2)
    salida_103 = (ahora + timedelta(days=2)).replace(hour=14, minute=0)
    salida_105 = (ahora + timedelta(days=2)).replace(hour=9, minute=0)
    salida_106 = (ahora - timedelta(days=1)).replace(hour=12, minute=0)
    salida_107 = (ahora + timedelta(days=4)).replace(hour=18, minute=20)
    salida_108 = (ahora + timedelta(days=3)).replace(hour=7, minute=30)

    creado = _sello(ahora - timedelta(days=20))
    with db.transaccion():
        # Aeropuertos -----------------------------------------------------
        aeropuertos = [
            ("LIM", "Aeropuerto Internacional Jorge Chávez", "Lima", "Perú", -12.0219, -77.1143),
            ("CUZ", "Aeropuerto Internacional Alejandro Velasco Astete", "Cusco", "Perú", -13.5357, -71.9388),
            ("AQP", "Aeropuerto Internacional Alfredo Rodríguez Ballón", "Arequipa", "Perú", -16.3411, -71.5831),
            ("PIU", "Aeropuerto Capitán FAP Guillermo Concha Iberico", "Piura", "Perú", -5.2057, -80.6164),
            ("TPP", "Aeropuerto Cadete FAP Guillermo del Castillo Paredes", "Tarapoto", "Perú", -6.5087, -76.3732),
        ]
        ids_aeropuerto: dict[str, int] = {}
        for datos in aeropuertos:
            cursor = db.ejecutar(
                "INSERT INTO aeropuertos(codigo, nombre, ciudad, pais, latitud, longitud, creado_en) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)", (*datos, creado),
            )
            ids_aeropuerto[datos[0]] = int(cursor.lastrowid)

        # Aeronaves -------------------------------------------------------
        aeronaves = [
            ("OB-3201", "Airbus A320neo (demo)", 6, 4, 24),
            ("OB-7382", "Boeing 737-800 (demo)", 7, 6, 42),
            ("OB-72A3", "ATR 72-600 (demo)", 5, 4, 20),
            ("OB-3214", "Airbus A321neo (demo)", 7, 6, 42),
        ]
        ids_aeronave: dict[str, int] = {}
        for matricula, modelo, filas, columnas, capacidad in aeronaves:
            cursor = db.ejecutar(
                "INSERT INTO aeronaves(matricula, modelo, filas, asientos_por_fila, capacidad, "
                "activo, creado_en) VALUES (?, ?, ?, ?, ?, 1, ?)",
                (matricula, modelo, filas, columnas, capacidad, creado),
            )
            ids_aeronave[matricula] = int(cursor.lastrowid)

        # Vuelos ----------------------------------------------------------
        vuelos = [
            ("AER101", "LIM", "CUZ", manana, "OB-3201", 24, "A03", 189.90, "Programado"),
            ("AER102", "LIM", "AQP", salida_102, "OB-7382", 42, "B02", 159.50, "Check-in abierto"),
            ("AER103", "CUZ", "LIM", salida_103, "OB-72A3", 20, "A01", 175.00, "Programado"),
            ("AER104", "LIM", "PIU", salida_104, "OB-7382", 42, "C04", 145.00, "Abordaje"),
            ("AER105", "LIM", "TPP", salida_105, "OB-3201", 24, "A05", 199.00, "Programado"),
            ("AER106", "AQP", "LIM", salida_106, "OB-7382", 42, "B01", 165.00, "Completado"),
            ("AER107", "TPP", "LIM", salida_107, "OB-72A3", 20, "A02", 210.00, "Cancelado"),
            ("AER108", "LIM", "CUZ", salida_108, "OB-7382", 42, "B03", 179.90, "Programado"),
        ]
        ids_vuelo: dict[str, int] = {}
        for codigo, origen, destino, salida, matricula, capacidad, puerta, precio, estado in vuelos:
            cursor = db.ejecutar(
                "INSERT INTO vuelos(codigo, origen_id, destino_id, fecha_salida, aeronave_id, "
                "capacidad, puerta, precio, estado, creado_en, actualizado_en) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (codigo, ids_aeropuerto[origen], ids_aeropuerto[destino], _fecha(salida),
                 ids_aeronave[matricula], capacidad, puerta, precio, estado, creado, creado),
            )
            ids_vuelo[codigo] = int(cursor.lastrowid)

        # Pasajeros ficticios --------------------------------------------
        pasajeros = [
            ("PAS-0001", "Ana Lucía", "Quispe Rojas", "71000001", "ana.quispe@example.com", "999111001"),
            ("PAS-0002", "Diego Alonso", "Ramírez Torres", "71000002", "diego.ramirez@example.com", "999111002"),
            ("PAS-0003", "Camila Fernanda", "Flores Vargas", "71000003", "camila.flores@example.com", "999111003"),
            ("PAS-0004", "Mateo Sebastián", "Rojas Mendoza", "71000004", "mateo.rojas@example.com", "999111004"),
            ("PAS-0005", "Valeria Nicole", "Castro León", "71000005", "valeria.castro@example.com", "999111005"),
            ("PAS-0006", "Joaquín Andrés", "Salazar Paredes", "71000006", "joaquin.salazar@example.com", "999111006"),
            ("PAS-0007", "Luciana Isabel", "Mendoza Cruz", "71000007", "luciana.mendoza@example.com", "999111007"),
            ("PAS-0008", "Renato Fabricio", "Huamán Silva", "71000008", "renato.huaman@example.com", "999111008"),
            ("PAS-0009", "Ariana Belén", "Torres Ríos", "71000009", "ariana.torres@example.com", "999111009"),
            ("PAS-0010", "Santiago Emilio", "Pacheco Ruiz", "71000010", "santiago.pacheco@example.com", "999111010"),
            ("PAS-0011", "María José", "Chávez Medina", "71000011", "maria.chavez@example.com", "999111011"),
            ("PAS-0012", "Gabriel Ignacio", "Núñez Soto", "71000012", "gabriel.nunez@example.com", "999111012"),
        ]
        ids_pasajero: dict[str, int] = {}
        for codigo, nombres, apellidos, documento, email, telefono in pasajeros:
            cursor = db.ejecutar(
                "INSERT INTO pasajeros(codigo, nombres, apellidos, documento, email, telefono, creado_en) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (codigo, nombres, apellidos, documento, email, telefono, creado),
            )
            ids_pasajero[codigo] = int(cursor.lastrowid)

        # Reservas --------------------------------------------------------
        reservas = [
            # código, vuelo, pasajero, asiento, estado, horas antes
            ("RES-100001", "AER101", "PAS-0001", "1A", "Confirmada", 50),
            ("RES-100002", "AER101", "PAS-0002", "1B", "Confirmada", 48),
            ("RES-100003", "AER101", "PAS-0003", "2A", "Pendiente", 30),
            ("RES-100004", "AER101", "PAS-0004", "2B", "Cancelada", 24),
            ("RES-100005", "AER102", "PAS-0005", "1A", "Confirmada", 22),
            ("RES-100006", "AER102", "PAS-0006", "1B", "Confirmada", 20),
            ("RES-100007", "AER102", "PAS-0007", "2A", "Confirmada", 18),
            ("RES-100008", "AER102", "PAS-0008", "2B", "Confirmada", 16),
            ("RES-100009", "AER104", "PAS-0009", "1A", "Confirmada", 14),
            ("RES-100010", "AER104", "PAS-0010", "1B", "Confirmada", 13),
            ("RES-100011", "AER104", "PAS-0011", "2A", "Confirmada", 12),
            ("RES-100012", "AER104", "PAS-0012", "2B", "Confirmada", 11),
            ("RES-100013", "AER105", "PAS-0001", "3A", "Confirmada", 9),
            ("RES-100014", "AER105", "PAS-0003", "3B", "Pendiente", 8),
            ("RES-100015", "AER106", "PAS-0002", "1A", "Confirmada", 46),
            ("RES-100016", "AER106", "PAS-0005", "1B", "Confirmada", 45),
            ("RES-100017", "AER103", "PAS-0006", "1A", "Confirmada", 7),
            ("RES-100018", "AER103", "PAS-0008", "1B", "Pendiente", 6),
            ("RES-100019", "AER107", "PAS-0004", "1A", "Cancelada", 5),
        ]
        ids_reserva: dict[str, int] = {}
        precios = {
            "AER101": 189.90, "AER102": 159.50, "AER103": 175.00, "AER104": 145.00,
            "AER105": 199.00, "AER106": 165.00, "AER107": 210.00, "AER108": 179.90,
        }
        for codigo, vuelo, pasajero, asiento, estado, horas in reservas:
            fecha_reserva = _sello(max(ahora - timedelta(hours=horas), creado_dt(creado)))
            cursor = db.ejecutar(
                "INSERT INTO reservas(codigo, vuelo_id, pasajero_id, asiento, precio, estado, "
                "fecha_reserva) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (codigo, ids_vuelo[vuelo], ids_pasajero[pasajero], asiento,
                 precios[vuelo], estado, fecha_reserva),
            )
            ids_reserva[codigo] = int(cursor.lastrowid)

        # Check-in y equipaje --------------------------------------------
        checkins = [
            ("RES-100005", "TB-100005", 1, 18.5, ahora - timedelta(hours=3)),
            ("RES-100006", "TB-100006", 2, 30.0, ahora - timedelta(hours=3, minutes=10)),
            ("RES-100007", "TB-100007", 0, 0.0, ahora - timedelta(hours=2, minutes=50)),
            ("RES-100008", "TB-100008", 1, 12.2, ahora - timedelta(hours=2, minutes=40)),
            ("RES-100009", "TB-100009", 2, 25.0, ahora - timedelta(hours=5)),
            ("RES-100010", "TB-100010", 1, 14.0, ahora - timedelta(hours=4, minutes=50)),
            ("RES-100011", "TB-100011", 1, 20.0, ahora - timedelta(hours=4, minutes=30)),
            ("RES-100012", "TB-100012", 2, 31.5, ahora - timedelta(hours=4, minutes=20)),
            ("RES-100015", "TB-100015", 1, 16.0, ahora - timedelta(days=1, hours=6)),
            ("RES-100016", "TB-100016", 2, 22.0, ahora - timedelta(days=1, hours=5)),
        ]
        ids_checkin: dict[str, int] = {}
        for reserva, tarjeta, cantidad, peso, fecha in checkins:
            cursor = db.ejecutar(
                "INSERT INTO checkins(reserva_id, tarjeta_embarque, cantidad_equipaje, "
                "peso_total, fecha_checkin) VALUES (?, ?, ?, ?, ?)",
                (ids_reserva[reserva], tarjeta, cantidad, peso, _sello(fecha)),
            )
            checkin_id = int(cursor.lastrowid)
            ids_checkin[reserva] = checkin_id
            if cantidad > 0:
                db.ejecutar(
                    "INSERT INTO equipajes(checkin_id, cantidad, peso_total, descripcion) "
                    "VALUES (?, ?, ?, 'Equipaje facturado')",
                    (checkin_id, cantidad, peso),
                )

        # Abordajes completados ------------------------------------------
        for reserva, posicion, fecha in [
            ("RES-100009", 1, ahora - timedelta(minutes=80)),
            ("RES-100010", 2, ahora - timedelta(minutes=75)),
            ("RES-100015", 1, salida_106 + timedelta(minutes=25)),
            ("RES-100016", 2, salida_106 + timedelta(minutes=27)),
        ]:
            db.ejecutar(
                "INSERT INTO abordajes(reserva_id, vuelo_id, posicion, fecha_abordaje) "
                "VALUES (?, ?, ?, ?)",
                (ids_reserva[reserva], ids_vuelo["AER104"] if reserva in
                 ("RES-100009", "RES-100010") else ids_vuelo["AER106"],
                 posicion, _sello(fecha)),
            )

        # Cola de abordaje del vuelo AER104 ------------------------------
        for reserva, fecha in [
            ("RES-100011", ahora - timedelta(minutes=20)),
            ("RES-100012", ahora - timedelta(minutes=18)),
        ]:
            db.ejecutar(
                "INSERT INTO cola_abordaje(vuelo_id, reserva_id, estado, creado_en) "
                "VALUES (?, ?, 'En cola', ?)",
                (ids_vuelo["AER104"], ids_reserva[reserva], _sello(fecha)),
            )

        # Rutas -----------------------------------------------------------
        rutas = [
            ("LIM", "CUZ", 586, 75),
            ("LIM", "AQP", 767, 90),
            ("LIM", "PIU", 850, 100),
            ("LIM", "TPP", 618, 80),
            ("CUZ", "AQP", 315, 55),
            ("CUZ", "TPP", 780, 105),
            ("AQP", "PIU", 1180, 150),
        ]
        for origen, destino, distancia, duracion in rutas:
            db.ejecutar(
                "INSERT INTO rutas(origen_id, destino_id, distancia_km, duracion_min, creado_en) "
                "VALUES (?, ?, ?, ?, ?)",
                (ids_aeropuerto[origen], ids_aeropuerto[destino], distancia, duracion, creado),
            )
    return True


def creado_dt(texto: str) -> datetime:
    return datetime.strptime(texto, "%Y-%m-%d %H:%M:%S")
