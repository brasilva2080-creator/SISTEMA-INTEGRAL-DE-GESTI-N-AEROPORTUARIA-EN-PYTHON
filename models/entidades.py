"""Modelos de dominio del sistema aeroportuario."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from config import parse_fecha


@dataclass(slots=True)
class Aeropuerto:
    id: int
    codigo: str
    nombre: str
    ciudad: str
    pais: str
    latitud: float = 0.0
    longitud: float = 0.0

    @classmethod
    def desde_fila(cls, fila) -> "Aeropuerto":
        return cls(
            id=fila["id"], codigo=fila["codigo"], nombre=fila["nombre"],
            ciudad=fila["ciudad"], pais=fila["pais"],
            latitud=float(fila["latitud"] or 0), longitud=float(fila["longitud"] or 0),
        )

    @property
    def etiqueta(self) -> str:
        return f"{self.codigo} · {self.ciudad}"


@dataclass(slots=True)
class Aeronave:
    id: int
    matricula: str
    modelo: str
    filas: int
    asientos_por_fila: int
    capacidad: int

    @classmethod
    def desde_fila(cls, fila) -> "Aeronave":
        return cls(
            id=fila["id"], matricula=fila["matricula"], modelo=fila["modelo"],
            filas=int(fila["filas"]), asientos_por_fila=int(fila["asientos_por_fila"]),
            capacidad=int(fila["capacidad"]),
        )

    @property
    def etiqueta(self) -> str:
        return f"{self.modelo} · {self.matricula} ({self.capacidad} asientos)"


@dataclass(slots=True)
class Vuelo:
    id: int
    codigo: str
    origen_id: int
    destino_id: int
    origen_codigo: str
    origen_ciudad: str
    destino_codigo: str
    destino_ciudad: str
    fecha_salida: str
    aeronave_id: int
    aeronave_modelo: str
    matricula: str
    asientos_por_fila: int
    capacidad: int
    puerta: str
    precio: float
    estado: str
    ocupados: int = 0

    @classmethod
    def desde_fila(cls, fila) -> "Vuelo":
        return cls(
            id=fila["id"], codigo=fila["codigo"],
            origen_id=fila["origen_id"], destino_id=fila["destino_id"],
            origen_codigo=fila["origen_codigo"], origen_ciudad=fila["origen_ciudad"],
            destino_codigo=fila["destino_codigo"], destino_ciudad=fila["destino_ciudad"],
            fecha_salida=fila["fecha_salida"], aeronave_id=fila["aeronave_id"],
            aeronave_modelo=fila["aeronave_modelo"], matricula=fila["matricula"],
            asientos_por_fila=int(fila["asientos_por_fila"]),
            capacidad=int(fila["capacidad"]), puerta=fila["puerta"],
            precio=float(fila["precio"]), estado=fila["estado"],
            ocupados=int(fila["ocupados"] or 0),
        )

    @property
    def ruta(self) -> str:
        return f"{self.origen_codigo} → {self.destino_codigo}"

    @property
    def ruta_ciudades(self) -> str:
        return f"{self.origen_ciudad} → {self.destino_ciudad}"

    @property
    def fecha_dt(self) -> datetime:
        return parse_fecha(self.fecha_salida)

    @property
    def asientos_disponibles(self) -> int:
        return max(0, self.capacidad - self.ocupados)

    @property
    def etiqueta(self) -> str:
        return f"{self.codigo} · {self.ruta} · {self.fecha_salida}"

    @property
    def activo_para_reserva(self) -> bool:
        return self.estado in ("Programado", "Check-in abierto")


@dataclass(slots=True)
class Pasajero:
    id: int
    codigo: str
    nombres: str
    apellidos: str
    documento: str
    email: str
    telefono: str
    creado_en: str = ""
    reservas: int = 0

    @classmethod
    def desde_fila(cls, fila) -> "Pasajero":
        claves = fila.keys()
        return cls(
            id=fila["id"], codigo=fila["codigo"], nombres=fila["nombres"],
            apellidos=fila["apellidos"], documento=fila["documento"],
            email=fila["email"], telefono=fila["telefono"],
            creado_en=fila["creado_en"] if "creado_en" in claves else "",
            reservas=int(fila["reservas"] if "reservas" in claves and fila["reservas"] else 0),
        )

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}".strip()

    @property
    def etiqueta(self) -> str:
        return f"{self.codigo} · {self.nombre_completo} · {self.documento}"


@dataclass(slots=True)
class Reserva:
    id: int
    codigo: str
    vuelo_id: int
    pasajero_id: int
    asiento: str
    precio: float
    estado: str
    fecha_reserva: str
    pasajero_codigo: str = ""
    pasajero_nombre: str = ""
    documento: str = ""
    vuelo_codigo: str = ""
    origen_codigo: str = ""
    destino_codigo: str = ""
    fecha_salida: str = ""
    puerta: str = ""
    estado_vuelo: str = ""
    checkin_id: int | None = None
    tarjeta_embarque: str | None = None
    abordado: int = 0

    @classmethod
    def desde_fila(cls, fila) -> "Reserva":
        claves = fila.keys()
        return cls(
            id=fila["id"], codigo=fila["codigo"], vuelo_id=fila["vuelo_id"],
            pasajero_id=fila["pasajero_id"], asiento=fila["asiento"],
            precio=float(fila["precio"]), estado=fila["estado"],
            fecha_reserva=fila["fecha_reserva"],
            pasajero_codigo=fila["pasajero_codigo"] if "pasajero_codigo" in claves else "",
            pasajero_nombre=fila["pasajero_nombre"] if "pasajero_nombre" in claves else "",
            documento=fila["documento"] if "documento" in claves else "",
            vuelo_codigo=fila["vuelo_codigo"] if "vuelo_codigo" in claves else "",
            origen_codigo=fila["origen_codigo"] if "origen_codigo" in claves else "",
            destino_codigo=fila["destino_codigo"] if "destino_codigo" in claves else "",
            fecha_salida=fila["fecha_salida"] if "fecha_salida" in claves else "",
            puerta=fila["puerta"] if "puerta" in claves else "",
            estado_vuelo=fila["estado_vuelo"] if "estado_vuelo" in claves else "",
            checkin_id=fila["checkin_id"] if "checkin_id" in claves else None,
            tarjeta_embarque=fila["tarjeta_embarque"] if "tarjeta_embarque" in claves else None,
            abordado=int(fila["abordado"] or 0) if "abordado" in claves else 0,
        )

    @property
    def nombre_pasajero(self) -> str:
        return self.pasajero_nombre

    @property
    def ruta(self) -> str:
        return f"{self.origen_codigo} → {self.destino_codigo}"

    @property
    def checkin_realizado(self) -> bool:
        return self.checkin_id is not None


@dataclass(slots=True)
class RegistroCheckin:
    id: int
    reserva_id: int
    tarjeta_embarque: str
    cantidad_equipaje: int
    peso_total: float
    fecha_checkin: str
    reserva_codigo: str = ""
    pasajero: str = ""
    documento: str = ""
    vuelo_id: int = 0
    vuelo_codigo: str = ""
    ruta: str = ""
    asiento: str = ""
    puerta: str = ""
    fecha_salida: str = ""
    abordado: int = 0
    en_cola: int = 0

    @classmethod
    def desde_fila(cls, fila) -> "RegistroCheckin":
        claves = fila.keys()
        return cls(
            id=fila["id"], reserva_id=fila["reserva_id"],
            tarjeta_embarque=fila["tarjeta_embarque"],
            cantidad_equipaje=int(fila["cantidad_equipaje"]),
            peso_total=float(fila["peso_total"]), fecha_checkin=fila["fecha_checkin"],
            reserva_codigo=fila["reserva_codigo"] if "reserva_codigo" in claves else "",
            pasajero=fila["pasajero"] if "pasajero" in claves else "",
            documento=fila["documento"] if "documento" in claves else "",
            vuelo_id=fila["vuelo_id"] if "vuelo_id" in claves else 0,
            vuelo_codigo=fila["vuelo_codigo"] if "vuelo_codigo" in claves else "",
            ruta=fila["ruta"] if "ruta" in claves else "",
            asiento=fila["asiento"] if "asiento" in claves else "",
            puerta=fila["puerta"] if "puerta" in claves else "",
            fecha_salida=fila["fecha_salida"] if "fecha_salida" in claves else "",
            abordado=int(fila["abordado"] or 0) if "abordado" in claves else 0,
            en_cola=int(fila["en_cola"] or 0) if "en_cola" in claves else 0,
        )

    @property
    def estado_abordaje(self) -> str:
        if self.abordado:
            return "Abordado"
        if self.en_cola:
            return "En cola"
        return "Check-in"


@dataclass(slots=True)
class Ruta:
    id: int
    origen_id: int
    destino_id: int
    origen_codigo: str
    origen_ciudad: str
    destino_codigo: str
    destino_ciudad: str
    distancia_km: float
    duracion_min: int

    @classmethod
    def desde_fila(cls, fila) -> "Ruta":
        return cls(
            id=fila["id"], origen_id=fila["origen_id"], destino_id=fila["destino_id"],
            origen_codigo=fila["origen_codigo"], origen_ciudad=fila["origen_ciudad"],
            destino_codigo=fila["destino_codigo"], destino_ciudad=fila["destino_ciudad"],
            distancia_km=float(fila["distancia_km"]), duracion_min=int(fila["duracion_min"]),
        )

    @property
    def trayecto(self) -> str:
        return f"{self.origen_codigo} ↔ {self.destino_codigo}"
