"""Vista de bitácora y pila LIFO de operaciones deshacibles."""
from __future__ import annotations

import tkinter as tk

from config import COLORS, fecha_corta
from views.base import VistaBase
from views.widgets import Card, Tabla, boton, etiqueta, separador


class ActividadView(VistaBase):
    def construir(self) -> None:
        cab = self.encabezado(
            "Actividad y deshacer",
            "Bitácora persistente y pila LIFO de operaciones administrativas de la sesión",
        )
        boton(cab.acciones, "Actualizar", self.refrescar, tipo="secondary",
              compacto=True, icono="↻").pack(side="right", padx=(8, 0))
        boton(cab.acciones, "Deshacer última", self.deshacer, tipo="warning",
              compacto=True, icono="↶").pack(side="right")

        cuerpo = tk.Frame(self, bg=COLORS["bg"])
        cuerpo.pack(fill="both", expand=True, padx=24, pady=(0, 14))
        cuerpo.grid_columnconfigure(0, weight=3, uniform="act")
        cuerpo.grid_columnconfigure(1, weight=2, uniform="act")
        cuerpo.grid_rowconfigure(0, weight=1)

        card_bitacora = Card(cuerpo, padding=0)
        card_bitacora.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        cab_b = tk.Frame(card_bitacora.cuerpo, bg=COLORS["card"], padx=14, pady=11)
        cab_b.pack(fill="x")
        etiqueta(cab_b, "Bitácora de operaciones", size=12, bold=True).pack(side="left")
        self.lbl_bitacora = etiqueta(cab_b, "", size=8, color=COLORS["muted"])
        self.lbl_bitacora.pack(side="right")
        separador(card_bitacora.cuerpo).pack(fill="x")
        self.tabla = Tabla(card_bitacora.cuerpo, [
            ("id", "ID", 40, "center", False),
            ("fecha", "FECHA", 120, "center", False),
            ("tipo", "TIPO", 100, "w", False),
            ("descripcion", "DESCRIPCIÓN", 300, "w", True),
            ("estado", "ESTADO", 85, "center", False),
        ], altura=16)
        self.tabla.pack(fill="both", expand=True, padx=8, pady=8)

        card_pila = Card(cuerpo, padding=15)
        card_pila.grid(row=0, column=1, sticky="nsew")
        etiqueta(card_pila.cuerpo, "Pila de deshacer", size=13, bold=True).pack(anchor="w")
        etiqueta(card_pila.cuerpo, "LIFO · la cima se deshace primero",
                 size=8, color=COLORS["muted"]).pack(anchor="w", pady=(1, 6))
        self.lbl_tamano = etiqueta(card_pila.cuerpo, "0 operaciones apiladas", size=9,
                                    color=COLORS["accent"])
        self.lbl_tamano.pack(anchor="w", pady=(0, 9))
        self.tabla_pila = Tabla(card_pila.cuerpo, [
            ("posicion", "POS", 42, "center", False),
            ("tipo", "TIPO", 100, "w", False),
            ("descripcion", "OPERACIÓN", 250, "w", True),
        ], altura=10)
        self.tabla_pila.pack(fill="both", expand=True)
        boton(card_pila.cuerpo, "Deshacer operación de la cima", self.deshacer,
              tipo="warning", compacto=False, icono="↶").pack(fill="x", pady=(12, 6))
        etiqueta(
            card_pila.cuerpo,
            "La pila se conserva mientras la aplicación esté abierta. "
            "La bitácora de la izquierda permanece en SQLite entre sesiones; "
            "las operaciones antiguas no se pueden deshacer tras reiniciar.",
            size=8, color=COLORS["muted"], wraplength=310, justify="left",
        ).pack(anchor="w")

    def refrescar(self) -> None:
        operaciones = self.app.historial.listar(100)
        filas = []
        for op in operaciones:
            filas.append({
                "_iid": str(op["id"]),
                "id": op["id"],
                "fecha": fecha_corta(op["fecha"]),
                "tipo": op["tipo"],
                "descripcion": op["descripcion"],
                "estado": "Deshecha" if op["deshecho"] else "Vigente",
                "_tag": "muted" if op["deshecho"] else "success",
            })
        self.tabla.set_filas(filas, usar_estado=False)
        self.lbl_bitacora.configure(text=f"{len(operaciones)} registro(s)")

        pila = self.app.historial.pila_actual()
        filas_pila = []
        for posicion, op in enumerate(pila, start=1):
            filas_pila.append({
                "_iid": f"pila_{op.id}",
                "posicion": posicion,
                "tipo": op.tipo,
                "descripcion": op.descripcion,
                "_tag": "accent" if posicion == 1 else "normal",
            })
        self.tabla_pila.set_filas(filas_pila, usar_estado=False)
        self.lbl_tamano.configure(text=f"{len(pila)} operación(es) apilada(s)")

    def deshacer(self) -> None:
        if self.app.historial.tamano_pila() == 0:
            self.info(
                "Pila vacía",
                "No hay operaciones para deshacer en esta sesión. "
                "Las operaciones anteriores al reinicio solo están en la bitácora.",
            )
            return
        cima = self.app.historial.pila_actual()[0]
        if not self.confirmar(
            "Deshacer operación",
            f"Se deshará la operación más reciente:\n\n{cima.descripcion}\n\n"
            "¿Continuar?",
        ):
            return
        try:
            operacion = self.app.historial.deshacer_ultima()
            self.app.refrescar_vista_actual()
            self.info("Operación deshecha", f"Se deshizo: {operacion.descripcion}")
        except Exception as exc:
            self.error(exc)
