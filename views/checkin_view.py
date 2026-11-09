"""Vista de check-in, equipaje y tarjetas de embarque."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from config import COLORS, dinero, fecha_corta, fecha_humana
from views.base import VistaBase
from views.widgets import (Card, DocumentoModal, Tabla, boton, campo, chip_estado,
                           etiqueta, separador)


class CheckinView(VistaBase):
    def construir(self) -> None:
        self.reserva_actual = None
        cab = self.encabezado(
            "Check-in y equipaje",
            "Validación de reservas, registro de maletas y emisión de tarjetas de embarque",
        )
        boton(cab.acciones, "Actualizar", self.refrescar, tipo="secondary",
              compacto=True, icono="↻").pack(side="right")

        cuerpo = tk.Frame(self, bg=COLORS["bg"])
        cuerpo.pack(fill="both", expand=True, padx=24, pady=(0, 14))
        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_rowconfigure(0, weight=3)
        cuerpo.grid_rowconfigure(1, weight=2)

        superior = tk.Frame(cuerpo, bg=COLORS["bg"])
        superior.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        superior.grid_columnconfigure(0, weight=3, uniform="check")
        superior.grid_columnconfigure(1, weight=2, uniform="check")
        superior.grid_rowconfigure(0, weight=1)

        # Reservas pendientes de check-in ---------------------------------
        card_lista = Card(superior, padding=0)
        card_lista.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        cab_lista = tk.Frame(card_lista.cuerpo, bg=COLORS["card"], padx=14, pady=11)
        cab_lista.pack(fill="x")
        etiqueta(cab_lista, "Reservas listas para check-in", size=12,
                 bold=True).pack(side="left")
        self.lbl_lista = etiqueta(cab_lista, "", size=8, color=COLORS["muted"])
        self.lbl_lista.pack(side="right")
        fila_busqueda = tk.Frame(card_lista.cuerpo, bg=COLORS["card"], padx=14)
        fila_busqueda.pack(fill="x", pady=(0, 8))
        self.var_busqueda = tk.StringVar()
        entrada = campo(fila_busqueda, self.var_busqueda)
        entrada.pack(side="left", fill="x", expand=True)
        entrada.bind("<Return>", lambda _e: self.buscar_codigo())
        boton(fila_busqueda, "Buscar código", self.buscar_codigo, compacto=True,
              icono="⌕").pack(side="left", padx=(8, 0))
        separador(card_lista.cuerpo).pack(fill="x")
        self.tabla_pendientes = Tabla(card_lista.cuerpo, [
            ("codigo", "RESERVA", 90, "center", False),
            ("pasajero", "PASAJERO", 165, "w", True),
            ("vuelo", "VUELO", 70, "center", False),
            ("ruta", "RUTA", 85, "center", False),
            ("asiento", "ASIENTO", 80, "center", False),
            ("salida", "SALIDA", 100, "center", False),
        ], altura=6, on_doble_clic=self.seleccionar_pendiente,
            on_seleccion=self.seleccionar_pendiente)
        self.tabla_pendientes.pack(fill="both", expand=True, padx=8, pady=7)

        # Detalle y registro ----------------------------------------------
        card_detalle = Card(superior, padding=15)
        card_detalle.grid(row=0, column=1, sticky="nsew")
        etiqueta(card_detalle.cuerpo, "Detalle de la reserva", size=13,
                 bold=True).pack(anchor="w")
        self.lbl_codigo = etiqueta(card_detalle.cuerpo, "Sin selección", size=19,
                                   bold=True, color=COLORS["accent"])
        self.lbl_codigo.pack(anchor="w", pady=(2, 4))
        self.lbl_estado = etiqueta(card_detalle.cuerpo, "—", size=9,
                                    color=COLORS["muted"])
        self.lbl_estado.pack(anchor="w", pady=(0, 8))
        separador(card_detalle.cuerpo).pack(fill="x", pady=(0, 8))
        self.detalle = {}
        for clave, titulo in [
            ("pasajero", "Pasajero"),
            ("documento", "Documento"),
            ("vuelo", "Vuelo / ruta"),
            ("salida", "Salida"),
            ("puerta", "Puerta"),
            ("asiento", "Asiento"),
            ("tarifa", "Tarifa"),
        ]:
            fila = tk.Frame(card_detalle.cuerpo, bg=COLORS["card"])
            fila.pack(fill="x", pady=1)
            etiqueta(fila, titulo, size=8, color=COLORS["muted"], width=12,
                     anchor="w").pack(side="left")
            valor = etiqueta(fila, "—", size=9, color=COLORS["text_soft"])
            valor.pack(side="left", fill="x", expand=True)
            self.detalle[clave] = valor

        separador(card_detalle.cuerpo).pack(fill="x", pady=(8, 8))
        equipaje = tk.Frame(card_detalle.cuerpo, bg=COLORS["card"])
        equipaje.pack(fill="x")
        col_cantidad = tk.Frame(equipaje, bg=COLORS["card"])
        col_cantidad.pack(side="left", fill="x", expand=True)
        etiqueta(col_cantidad, "PIEZAS DE EQUIPAJE", size=8, bold=True,
                 color=COLORS["muted"]).pack(anchor="w")
        self.var_cantidad = tk.StringVar(value="0")
        spin = ttk.Spinbox(col_cantidad, from_=0, to=10, textvariable=self.var_cantidad,
                           width=8, font=("Segoe UI", 10))
        spin.pack(anchor="w", pady=(3, 0))
        col_peso = tk.Frame(equipaje, bg=COLORS["card"])
        col_peso.pack(side="left", fill="x", expand=True, padx=(10, 0))
        etiqueta(col_peso, "PESO TOTAL (KG)", size=8, bold=True,
                 color=COLORS["muted"]).pack(anchor="w")
        self.var_peso = tk.StringVar(value="0.0")
        campo(col_peso, self.var_peso, ancho=8).pack(anchor="w", pady=(3, 0))
        etiqueta(card_detalle.cuerpo, "Máximo 32 kg por pieza · 0 piezas si viaja solo con equipaje de mano.",
                 size=7, color=COLORS["muted"]).pack(anchor="w", pady=(4, 8))
        fila_botones = tk.Frame(card_detalle.cuerpo, bg=COLORS["card"])
        fila_botones.pack(fill="x")
        self.btn_checkin = boton(fila_botones, "Registrar check-in", self.registrar_checkin,
                                 tipo="primary", compacto=True, icono="✓")
        self.btn_checkin.pack(side="left")
        boton(fila_botones, "Ver tarjeta", self.ver_tarjeta, tipo="secondary",
              compacto=True, icono="▤").pack(side="left", padx=(8, 0))

        # Check-ins registrados ------------------------------------------
        card_historial = Card(cuerpo, padding=0)
        card_historial.grid(row=1, column=0, sticky="nsew")
        cab_hist = tk.Frame(card_historial.cuerpo, bg=COLORS["card"], padx=14, pady=10)
        cab_hist.pack(fill="x")
        etiqueta(cab_hist, "Check-ins registrados", size=12, bold=True).pack(side="left")
        self.lbl_historial = etiqueta(cab_hist, "", size=8, color=COLORS["muted"])
        self.lbl_historial.pack(side="left", padx=(8, 0))
        boton(cab_hist, "Ver tarjeta seleccionada", self.ver_tarjeta_historial,
              tipo="ghost", compacto=True, icono="▤").pack(side="right")
        separador(card_historial.cuerpo).pack(fill="x")
        self.tabla_checkins = Tabla(card_historial.cuerpo, [
            ("tarjeta", "TARJETA", 95, "center", False),
            ("pasajero", "PASAJERO", 175, "w", True),
            ("vuelo", "VUELO", 70, "center", False),
            ("ruta", "RUTA", 85, "center", False),
            ("asiento", "ASIENTO", 80, "center", False),
            ("equipaje", "EQUIPAJE", 105, "center", False),
            ("fecha", "CHECK-IN", 110, "center", False),
            ("estado", "ESTADO", 95, "center", True),
        ], altura=5, on_doble_clic=self.ver_tarjeta_historial)
        self.tabla_checkins.pack(fill="both", expand=True, padx=8, pady=7)

    # ------------------------------------------------------------------
    def refrescar(self) -> None:
        pendientes = self.app.reservas.reservas_confirmadas_sin_checkin(
            self.var_busqueda.get()
        )
        filas = []
        for reserva in pendientes:
            filas.append({
                "_iid": str(reserva.id),
                "codigo": reserva.codigo,
                "pasajero": reserva.pasajero_nombre,
                "vuelo": reserva.vuelo_codigo,
                "ruta": reserva.ruta,
                "asiento": reserva.asiento,
                "salida": fecha_corta(reserva.fecha_salida),
            })
        self.tabla_pendientes.set_filas(filas, usar_estado=False)
        self.lbl_lista.configure(text=f"{len(pendientes)} pendiente(s)")

        checkins = self.app.checkin.listar()
        filas_hist = []
        for checkin in checkins:
            filas_hist.append({
                "_iid": str(checkin.reserva_id),
                "tarjeta": checkin.tarjeta_embarque,
                "pasajero": checkin.pasajero,
                "vuelo": checkin.vuelo_codigo,
                "ruta": checkin.ruta,
                "asiento": checkin.asiento,
                "equipaje": f"{checkin.cantidad_equipaje} · {checkin.peso_total:.1f} kg",
                "fecha": fecha_corta(checkin.fecha_checkin),
                "estado": checkin.estado_abordaje,
            })
        self.tabla_checkins.set_filas(filas_hist)
        self.lbl_historial.configure(text=f"{len(checkins)} check-in(s)")

        if self.reserva_actual:
            actualizada = self.app.reservas.obtener_por_id(self.reserva_actual.id)
            if actualizada:
                self._mostrar_reserva(actualizada)
            else:
                self.reserva_actual = None

    def _mostrar_reserva(self, reserva) -> None:
        self.reserva_actual = reserva
        self.lbl_codigo.configure(text=reserva.codigo)
        estado_texto = f"{reserva.estado} · vuelo {reserva.estado_vuelo}"
        if reserva.checkin_realizado:
            estado_texto += " · check-in realizado"
        self.lbl_estado.configure(text=estado_texto)
        self.detalle["pasajero"].configure(text=reserva.pasajero_nombre)
        self.detalle["documento"].configure(text=reserva.documento)
        self.detalle["vuelo"].configure(text=f"{reserva.vuelo_codigo} · {reserva.ruta}")
        self.detalle["salida"].configure(text=fecha_humana(reserva.fecha_salida))
        self.detalle["puerta"].configure(text=reserva.puerta)
        self.detalle["asiento"].configure(text=reserva.asiento)
        self.detalle["tarifa"].configure(text=dinero(reserva.precio))
        self.btn_checkin.configure(
            state="disabled" if reserva.checkin_realizado else "normal"
        )

    def seleccionar_pendiente(self) -> None:
        fila = self.tabla_pendientes.seleccionado()
        if not fila:
            return
        reserva = self.app.reservas.obtener_por_id(int(fila["_iid"]))
        if reserva:
            self._mostrar_reserva(reserva)

    def buscar_codigo(self) -> None:
        codigo = self.var_busqueda.get().strip()
        if not codigo:
            self.error("Ingresa un código de reserva (ej. RES-100001).")
            return
        reserva = self.app.checkin.buscar_reserva(codigo)
        if not reserva:
            self.error("No se encontró una reserva con ese código.")
            return
        self._mostrar_reserva(reserva)
        self.notificar(f"Reserva {reserva.codigo} cargada para check-in.")

    def registrar_checkin(self) -> None:
        if not self.reserva_actual:
            self.error("Selecciona o busca una reserva primero.")
            return
        try:
            checkin = self.app.checkin.registrar(
                self.reserva_actual.codigo, self.var_cantidad.get(), self.var_peso.get()
            )
            actualizada = self.app.reservas.obtener_por_id(self.reserva_actual.id)
            if actualizada:
                self._mostrar_reserva(actualizada)
            self.refrescar()
            self.info(
                "Check-in registrado",
                f"Check-in completado para {checkin.pasajero}.\n"
                f"Tarjeta: {checkin.tarjeta_embarque} · Asiento {checkin.asiento} · "
                f"Puerta {checkin.puerta}",
            )
            self._abrir_tarjeta(actualizada.codigo if actualizada else self.reserva_actual.codigo)
        except Exception as exc:
            self.error(exc)

    def ver_tarjeta(self) -> None:
        if not self.reserva_actual:
            self.error("Selecciona una reserva con check-in.")
            return
        self._abrir_tarjeta(self.reserva_actual.codigo)

    def ver_tarjeta_historial(self) -> None:
        fila = self.tabla_checkins.seleccionado()
        if not fila:
            self.error("Selecciona un check-in en la tabla inferior.")
            return
        reserva = self.app.reservas.obtener_por_id(int(fila["_iid"]))
        if not reserva:
            self.error("No se pudo recuperar la reserva del check-in.")
            return
        self._abrir_tarjeta(reserva.codigo)

    def _abrir_tarjeta(self, codigo_reserva: str) -> None:
        try:
            contenido, ruta, _checkin = self.app.checkin.tarjeta_embarque(codigo_reserva)
            modal = DocumentoModal(self, "Tarjeta de embarque", contenido, ruta)
            modal.esperar()
        except Exception as exc:
            self.error(exc)
