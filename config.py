"""Configuración general y utilidades compartidas del sistema aeroportuario."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

# ---------------------------------------------------------------------------
# Rutas del proyecto
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "aeropuerto.db"
COMPROBANTES_DIR = ROOT_DIR / "comprobantes"
ASSETS_DIR = ROOT_DIR / "assets"
COMPROBANTES_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = "AeroAndes"
APP_TITLE = "AeroAndes · Sistema Integral de Gestión Aeroportuaria"
APP_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Paleta visual (tema oscuro elegante)
# ---------------------------------------------------------------------------
COLORS = {
    "bg": "#070F1B",
    "bg_soft": "#0A1626",
    "sidebar": "#0B1728",
    "sidebar_hover": "#12243B",
    "card": "#102238",
    "card_alt": "#142B45",
    "card_light": "#193552",
    "border": "#213A57",
    "border_soft": "#193149",
    "text": "#F3F7FD",
    "text_soft": "#C5D3E5",
    "muted": "#8EA5C2",
    "accent": "#38BDF8",
    "accent_dark": "#0EA5E9",
    "accent_soft": "#0B3A55",
    "success": "#2DD4BF",
    "success_soft": "#0B3B37",
    "warning": "#FBBF24",
    "warning_soft": "#4A3608",
    "danger": "#FB7185",
    "danger_soft": "#4A1724",
    "purple": "#A78BFA",
    "purple_soft": "#2D2350",
    "white": "#FFFFFF",
}

FONTS = {
    "family": "Segoe UI",
    "title": ("Segoe UI", 22, "bold"),
    "subtitle": ("Segoe UI", 13, "bold"),
    "card_title": ("Segoe UI", 9, "bold"),
    "card_value": ("Segoe UI", 24, "bold"),
    "body": ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10, "bold"),
    "small": ("Segoe UI", 9),
    "tiny": ("Segoe UI", 8),
    "mono": ("Consolas", 10),
}

ESTADOS_VUELO = [
    "Programado",
    "Check-in abierto",
    "Abordaje",
    "En vuelo",
    "Completado",
    "Cancelado",
]

ESTADOS_RESERVA = ["Pendiente", "Confirmada", "Cancelada"]

COLORES_ESTADO = {
    "Programado": COLORS["accent"],
    "Check-in abierto": COLORS["purple"],
    "Abordaje": COLORS["warning"],
    "En vuelo": COLORS["success"],
    "Completado": "#7DD3FC",
    "Cancelado": COLORS["danger"],
    "Pendiente": COLORS["warning"],
    "Confirmada": COLORS["success"],
    "Cancelada": COLORS["danger"],
    "Disponible": COLORS["card_light"],
    "Reservado": COLORS["warning"],
    "Ocupado": COLORS["danger"],
    "Abordado": COLORS["success"],
    "En cola": COLORS["warning"],
    "Check-in": COLORS["accent"],
}

FORMATO_FECHA = "%Y-%m-%d %H:%M"
FORMATO_FECHA_SEGUNDOS = "%Y-%m-%d %H:%M:%S"
FORMATO_FECHA_HUMANO = "%d/%m/%Y %H:%M"


def ahora() -> datetime:
    return datetime.now().replace(second=0, microsecond=0)


def fecha_iso(dt: datetime) -> str:
    return dt.strftime(FORMATO_FECHA)


def parse_fecha(texto: str) -> datetime:
    """Convierte el formato persistido en un datetime, con mensaje amigable."""
    try:
        return datetime.strptime(texto.strip(), FORMATO_FECHA)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("La fecha debe tener el formato AAAA-MM-DD HH:MM.") from exc


def fecha_humana(texto: str | None) -> str:
    if not texto:
        return "—"
    for formato in (FORMATO_FECHA, FORMATO_FECHA_SEGUNDOS):
        try:
            return datetime.strptime(texto, formato).strftime(FORMATO_FECHA_HUMANO)
        except (ValueError, TypeError):
            continue
    return str(texto)


def fecha_corta(texto: str | None) -> str:
    if not texto:
        return "—"
    for formato in (FORMATO_FECHA, FORMATO_FECHA_SEGUNDOS):
        try:
            return datetime.strptime(texto, formato).strftime("%d/%m %H:%M")
        except (ValueError, TypeError):
            continue
    return str(texto)


def dinero(valor: float | int | None) -> str:
    return f"S/ {float(valor or 0):,.2f}"


def letras_asientos(columnas: int) -> str:
    return "ABCDEF"[: max(1, int(columnas))]


def generar_asientos(capacidad: int, columnas: int) -> list[str]:
    """Distribuye la capacidad en filas y columnas, respetando el límite."""
    asientos: list[str] = []
    letras = letras_asientos(columnas)
    fila = 1
    while len(asientos) < max(0, int(capacidad)):
        for letra in letras:
            if len(asientos) >= int(capacidad):
                break
            asientos.append(f"{fila}{letra}")
        fila += 1
    return asientos


def truncar(texto: str, largo: int = 35) -> str:
    texto = str(texto or "")
    return texto if len(texto) <= largo else texto[: largo - 1] + "…"


def slug_documento(codigo: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in codigo)


def limites_lista(valores: Iterable, maximo: int = 4) -> str:
    valores = list(valores)
    if len(valores) <= maximo:
        return ", ".join(str(v) for v in valores)
    return ", ".join(str(v) for v in valores[:maximo]) + f" +{len(valores) - maximo}"
