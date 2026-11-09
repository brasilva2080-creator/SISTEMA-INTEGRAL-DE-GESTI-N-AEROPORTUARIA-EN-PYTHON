"""Clase base para las vistas del sistema."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from config import COLORS
from views.widgets import PageHeader, etiqueta


class VistaBase(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.app = app
        self.db = app.db
        self.construir()

    # ------------------------------------------------------------------
    def construir(self) -> None:  # pragma: no cover - interfaz
        raise NotImplementedError

    def refrescar(self) -> None:  # pragma: no cover - interfaz
        pass

    # ------------------------------------------------------------------
    def encabezado(self, titulo: str, subtitulo: str = "") -> PageHeader:
        cabecera = PageHeader(self, titulo, subtitulo)
        cabecera.pack(fill="x", padx=24, pady=(20, 12))
        self._cabecera_actual = cabecera
        return cabecera

    def notificar(self, mensaje: str, error: bool = False) -> None:
        self.app.estado(mensaje, error=error)

    def error(self, exc: Exception | str) -> None:
        mensaje = str(exc)
        self.notificar(mensaje, error=True)
        messagebox.showerror("No se pudo completar la operación", mensaje, parent=self)

    def info(self, titulo: str, mensaje: str) -> None:
        self.notificar(mensaje)
        messagebox.showinfo(titulo, mensaje, parent=self)

    def confirmar(self, titulo: str, mensaje: str) -> bool:
        return messagebox.askyesno(titulo, mensaje, parent=self)

    @staticmethod
    def vacio(parent, texto: str = "No hay registros para mostrar") -> tk.Label:
        return etiqueta(parent, texto, size=9, color=COLORS["muted"],
                        anchor="center", justify="center")
