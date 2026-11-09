"""Vista de reservas, venta de boletos y mapa de asientos."""
from __future__ import annotations

import tkinter as tk

from config import COLORS, dinero, fecha_corta, truncar
from views.base import VistaBase
from views.widgets import (Card, DocumentoModal, MapaAsientos, Tabla, boton,
                           campo, combo, etiqueta, separador)

ESTADOS_FILTRO = ["Todos los estados", "Pendiente", "Confirmada", "Cancelada"]


class ReservasView(VistaBase):
    def construir(self) -> None:
        self._mapa_pasajeros = {}
        self._mapa_vuelos = {}
        self.var_asiento = tk.StringVar(value="—")
        cab = self.encabezado(
            "Reservas y venta de boletos",
            "Selección de vuelo, asignación visual de asiento y comprobantes",
        )
        boton(cab.acciones, "Actualizar", self.refrescar, tipo="secondary",
              compacto=True, icono="↻").pack(side="right")

        cuerpo = tk.Frame(self, bg=COLORS["bg"])
        cuerpo.pack(fill="both", expand=True, padx=24, pady=(0, 14))
        cuerpo.grid_columnconfigure(0, weight=5, uniform="reserva")
        cuerpo.grid_columnconfigure(1, weight=4, uniform="reserva")
        cuerpo.grid_rowconfigure(0, weight=0)
        cuerpo.grid_rowconfigure(1, weight=1)

        # Venta -----------------------------------------------------------
        venta = Card(cuerpo, padding=15)
        venta.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 10))
        encabezado = tk.Frame(venta.cuerpo, bg=COLORS["card"])
        encabezado.pack(fill="x", pady=(0, 10))
        etiqueta(encabezado, "Nueva reserva", size=13, bold=True).pack(side="left")
        etiqueta(encabezado, "Compra simulada · sin pagos reales", size=8,
                 color=COLORS["muted"]).pack(side="right")
        separador(venta.cuerpo).pack(fill="x", pady=(0, 10))

        etiqueta(venta.cuerpo, "PASAJERO", size=8, bold=True,
                 color=COLORS["muted"]).pack(anchor="w")
        self.var_pasajero = tk.StringVar()
        self.combo_pasajero = combo(venta.cuerpo, [], self.var_pasajero)
        self.combo_pasajero.pack(fill="x", pady=(3, 8))
        self.combo_pasajero.bind("<<ComboboxSelected>>", lambda _e: self._cambiar_pasajero())
        etiqueta(venta.cuerpo, "VUELO DISPONIBLE", size=8, bold=True,
                 color=COLORS["muted"]).pack(anchor="w")
        self.var_vuelo = tk.StringVar()
        self.combo_vuelo = combo(venta.cuerpo, [], self.var_vuelo)
        self.combo_vuelo.pack(fill="x", pady=(3, 10))
        self.combo_vuelo.bind("<<ComboboxSelected>>", lambda _e: self._cambiar_vuelo())

        info = tk.Frame(venta.cuerpo, bg=COLORS["bg"])
        info.pack(fill="x", pady=(0, 10))
        for col in range(3):
            info.grid_columnconfigure(col, weight=1, uniform="info")
        self.lbl_precio = self._mini_info(info, 0, "TARIFA", "—")
        self.lbl_disponibles = self._mini_info(info, 1, "DISPONIBLES", "—")
        self.lbl_asiento = self._mini_info(info, 2, "ASIENTO", "—", COLORS["accent"])

        self.var_confirmar = tk.BooleanVar(value=True)
        check = tk.Checkbutton(
            venta.cuerpo, text="Confirmar la reserva al registrarla",
            variable=self.var_confirmar, bg=COLORS["card"], fg=COLORS["text_soft"],
            activebackground=COLORS["card"], activeforeground=COLORS["accent"],
            selectcolor=COLORS["bg_soft"], bd=0, highlightthickness=0,
            font=("Segoe UI", 9), cursor="hand2",
        )
        check.pack(anchor="w", pady=(0, 8))
        fila_botones = tk.Frame(venta.cuerpo, bg=COLORS["card"])
        fila_botones.pack(fill="x")
        boton(fila_botones, "Registrar reserva", self.registrar_reserva,
              tipo="primary", compacto=True, icono="✓").pack(side="left")
        boton(fila_botones, "Limpiar asiento", self.limpiar_asiento, tipo="ghost",
              compacto=True).pack(side="left", padx=(8, 0))
        etiqueta(venta.cuerpo, "Haz clic en un asiento disponible del mapa.",
                 size=8, color=COLORS["muted"]).pack(anchor="w", pady=(8, 0))

        # Mapa ------------------------------------------------------------
        card_mapa = Card(cuerpo, padding=12)
        card_mapa.grid(row=0, column=1, sticky="nsew", pady=(0, 10))
        cab_mapa = tk.Frame(card_mapa.cuerpo, bg=COLORS["card"])
        cab_mapa.pack(fill="x", pady=(0, 6))
        etiqueta(cab_mapa, "Mapa de asientos", size=13, bold=True).pack(side="left")
        self.lbl_mapa = etiqueta(cab_mapa, "", size=8, color=COLORS["muted"])
        self.lbl_mapa.pack(side="right")
        self.mapa = MapaAsientos(card_mapa.cuerpo, on_seleccion=self.seleccionar_asiento)
        self.mapa.pack(fill="both", expand=True)
        self.mapa.canvas.configure(height=232)

        # Tabla de reservas ----------------------------------------------
        card_tabla = Card(cuerpo, padding=0)
        card_tabla.grid(row=1, column=0, columnspan=2, sticky="nsew")
        barra_sup = tk.Frame(card_tabla.cuerpo, bg=COLORS["card"], padx=14, pady=10)
        barra_sup.pack(fill="x")
        etiqueta(barra_sup, "Reservas registradas", size=13, bold=True).pack(side="left")
        self.lbl_conteo = etiqueta(barra_sup, "", size=8, color=COLORS["muted"])
        self.lbl_conteo.pack(side="left", padx=(8, 0))
        self.var_busqueda = tk.StringVar()
        entrada = campo(barra_sup, self.var_busqueda, ancho=26)
        entrada.pack(side="right", padx=(8, 0))
        entrada.bind("<Return>", lambda _e: self.refrescar())
        self.var_estado = tk.StringVar(value="Todos los estados")
        combo_estado = combo(barra_sup, ESTADOS_FILTRO, self.var_estado, ancho=16)
        combo_estado.pack(side="right")
        combo_estado.bind("<<ComboboxSelected>>", lambda _e: self.refrescar())
        boton(barra_sup, "Buscar", self.refrescar, tipo="ghost", compacto=True,
              icono="⌕").pack(side="right", padx=(8, 0))
        separador(card_tabla.cuerpo).pack(fill="x")
        self.tabla = Tabla(card_tabla.cuerpo, [
            ("codigo", "RESERVA", 88, "center", False),
            ("pasajero", "PASAJERO", 175, "w", True),
            ("vuelo", "VUELO", 72, "center", False),
            ("ruta", "RUTA", 90, "center", False),
            ("asiento", "ASIENTO", 78, "center", False),
            ("precio", "TARIFA", 78, "e", False),
            ("fecha", "SALIDA", 105, "center", False),
            ("estado", "ESTADO", 95, "center", True),
        ], altura=5, on_doble_clic=self.ver_comprobante)
        self.tabla.pack(fill="both", expand=True, padx=8, pady=8)
        barra = tk.Frame(card_tabla.cuerpo, bg=COLORS["card"], padx=14, pady=9)
        barra.pack(fill="x")
        boton(barra, "Confirmar reserva", self.confirmar_reserva, tipo="success",
              compacto=True, icono="✓").pack(side="left", padx=(0, 6))
        boton(barra, "Cancelar reserva", self.cancelar_reserva, tipo="danger",
              compacto=True, icono="✕").pack(side="left", padx=(0, 6))
        boton(barra, "Ver comprobante", self.ver_comprobante, tipo="secondary",
              compacto=True, icono="▤").pack(side="left")
        etiqueta(barra, "Doble clic para ver el comprobante", size=8,
                 color=COLORS["muted"]).pack(side="right")

    # ------------------------------------------------------------------
    def _mini_info(self, parent, columna: int, titulo: str, valor: str,
                   color: str | None = None) -> tk.Label:
        caja = tk.Frame(parent, bg=COLORS["card_alt"], padx=10, pady=7)
        caja.grid(row=0, column=columna, sticky="ew",
                  padx=(0, 5) if columna == 0 else (5, 0) if columna == 1 else (5, 0))
        etiqueta(caja, titulo, size=7, bold=True,
                 color=COLORS["muted"]).pack(anchor="w")
        etiqueta_valor = etiqueta(caja, valor, size=11, bold=True,
                                  color=color or COLORS["text"])
        etiqueta_valor.pack(anchor="w")
        return etiqueta_valor

    def refrescar(self) -> None:
        pasajeros = self.app.pasajeros.listar()
        vuelos = self.app.vuelos.vuelos_disponibles()
        pasajero_actual = getattr(self, "_codigo_pasajero_actual", None)
        vuelo_actual = getattr(self, "_codigo_vuelo_actual", None)

        self._mapa_pasajeros = {
            f"{p.codigo} · {p.nombre_completo} · {p.documento}": p for p in pasajeros
        }
        self._mapa_vuelos = {
            f"{v.codigo} · {v.ruta} · {fecha_corta(v.fecha_salida)} · {v.asientos_disponibles} cupos": v
            for v in vuelos
        }
        valores_pasajeros = list(self._mapa_pasajeros.keys())
        valores_vuelos = list(self._mapa_vuelos.keys())
        self.combo_pasajero.configure(values=valores_pasajeros)
        self.combo_vuelo.configure(values=valores_vuelos)

        etiqueta_pasajero = next(
            (k for k, v in self._mapa_pasajeros.items() if v.codigo == pasajero_actual),
            valores_pasajeros[0] if valores_pasajeros else "",
        )
        etiqueta_vuelo = next(
            (k for k, v in self._mapa_vuelos.items() if v.codigo == vuelo_actual),
            valores_vuelos[0] if valores_vuelos else "",
        )
        self.var_pasajero.set(etiqueta_pasajero)
        self.var_vuelo.set(etiqueta_vuelo)
        vuelo = self._mapa_vuelos.get(etiqueta_vuelo)
        self._codigo_vuelo_actual = vuelo.codigo if vuelo else None
        pasajero = self._mapa_pasajeros.get(etiqueta_pasajero)
        self._codigo_pasajero_actual = pasajero.codigo if pasajero else None
        self._actualizar_mapa()

        filtro_estado = "" if self.var_estado.get() == "Todos los estados" else self.var_estado.get()
        reservas = self.app.reservas.listar(
            texto=self.var_busqueda.get(), estado=filtro_estado
        )
        filas = []
        for reserva in reservas:
            filas.append({
                "_iid": str(reserva.id),
                "codigo": reserva.codigo,
                "pasajero": reserva.pasajero_nombre,
                "vuelo": reserva.vuelo_codigo,
                "ruta": reserva.ruta,
                "asiento": reserva.asiento,
                "precio": dinero(reserva.precio),
                "fecha": fecha_corta(reserva.fecha_salida),
                "estado": reserva.estado,
            })
        self.tabla.set_filas(filas)
        self.lbl_conteo.configure(text=f"{len(reservas)} reserva(s)")

    def _cambiar_pasajero(self) -> None:
        pasajero = self._mapa_pasajeros.get(self.var_pasajero.get())
        self._codigo_pasajero_actual = pasajero.codigo if pasajero else None

    def _cambiar_vuelo(self) -> None:
        vuelo = self._mapa_vuelos.get(self.var_vuelo.get())
        self._codigo_vuelo_actual = vuelo.codigo if vuelo else None
        self.limpiar_asiento(render=False)
        self._actualizar_mapa()

    def _actualizar_mapa(self) -> None:
        vuelo = self._mapa_vuelos.get(self.var_vuelo.get())
        if not vuelo:
            self.mapa.actualizar(None)
            self.lbl_mapa.configure(text="Sin vuelos disponibles")
            self.lbl_precio.configure(text="—")
            self.lbl_disponibles.configure(text="—")
            return
        try:
            mapa = self.app.reservas.mapa_asientos(vuelo.id)
        except Exception as exc:
            self.error(exc)
            return
        seleccionado = self.var_asiento.get() if hasattr(self, "var_asiento") else None
        if seleccionado and mapa.estados.get(seleccionado) != "Disponible":
            seleccionado = None
        self.var_asiento = getattr(self, "var_asiento", tk.StringVar(value="—"))
        self.var_asiento.set(seleccionado or "—")
        self.mapa.actualizar(mapa, seleccionado)
        self.lbl_mapa.configure(text=f"{vuelo.codigo} · {vuelo.ruta}")
        self.lbl_precio.configure(text=dinero(vuelo.precio))
        self.lbl_disponibles.configure(text=f"{mapa.disponibles}/{vuelo.capacidad}")
        self.lbl_asiento.configure(text=seleccionado or "—")
        self._codigo_vuelo_actual = vuelo.codigo

    def seleccionar_asiento(self, asiento: str) -> None:
        self.var_asiento.set(asiento)
        self.lbl_asiento.configure(text=asiento)

    def limpiar_asiento(self, render: bool = True) -> None:
        if hasattr(self, "var_asiento"):
            self.var_asiento.set("—")
        if hasattr(self, "lbl_asiento"):
            self.lbl_asiento.configure(text="—")
        if render and hasattr(self, "mapa"):
            self.mapa.set_seleccion(None)

    # ------------------------------------------------------------------
    def registrar_reserva(self) -> None:
        pasajero = self._mapa_pasajeros.get(self.var_pasajero.get())
        vuelo = self._mapa_vuelos.get(self.var_vuelo.get())
        asiento = self.var_asiento.get()
        if not pasajero:
            self.error("Selecciona un pasajero. Si no existe, regístralo en el módulo Pasajeros.")
            return
        if not vuelo:
            self.error("Selecciona un vuelo disponible.")
            return
        if not asiento or asiento == "—":
            self.error("Selecciona un asiento disponible en el mapa.")
            return
        try:
            reserva = self.app.reservas.registrar(
                vuelo.id, pasajero.id, asiento, confirmar=self.var_confirmar.get()
            )
            self._codigo_pasajero_actual = pasajero.codigo
            self._codigo_vuelo_actual = vuelo.codigo
            self.var_asiento = tk.StringVar(value="—")
            self.refrescar()
            self.info(
                "Reserva registrada",
                f"Reserva {reserva.codigo} creada para {pasajero.nombre_completo}.\n"
                f"Vuelo {vuelo.codigo} · Asiento {reserva.asiento} · {dinero(reserva.precio)}\n"
                f"Estado: {reserva.estado}",
            )
        except Exception as exc:
            self.error(exc)

    def _reserva_seleccionada(self):
        fila = self.tabla.seleccionado()
        if not fila:
            self.error("Selecciona una reserva en la tabla.")
            return None
        reserva = self.app.reservas.obtener_por_id(int(fila["_iid"]))
        if not reserva:
            self.error("La reserva ya no existe.")
        return reserva

    def confirmar_reserva(self) -> None:
        reserva = self._reserva_seleccionada()
        if not reserva:
            return
        if reserva.estado != "Pendiente":
            self.error("Solo se pueden confirmar reservas en estado Pendiente.")
            return
        try:
            self.app.reservas.confirmar(reserva.id)
            self.refrescar()
            self.info("Reserva confirmada", f"La reserva {reserva.codigo} fue confirmada.")
        except Exception as exc:
            self.error(exc)

    def cancelar_reserva(self) -> None:
        reserva = self._reserva_seleccionada()
        if not reserva:
            return
        if not self.confirmar(
            "Cancelar reserva",
            f"¿Cancelar la reserva {reserva.codigo} del pasajero {reserva.pasajero_nombre}?\n"
            "El asiento quedará disponible nuevamente.",
        ):
            return
        try:
            self.app.reservas.cancelar(reserva.id)
            self.refrescar()
            self.info("Reserva cancelada", f"La reserva {reserva.codigo} fue cancelada.")
        except Exception as exc:
            self.error(exc)

    def ver_comprobante(self) -> None:
        reserva = self._reserva_seleccionada()
        if not reserva:
            return
        try:
            contenido, ruta = self.app.reservas.comprobante(reserva.codigo)
            modal = DocumentoModal(self, f"Comprobante {reserva.codigo}",
                                   contenido, ruta)
            modal.esperar()
        except Exception as exc:
            self.error(exc)
