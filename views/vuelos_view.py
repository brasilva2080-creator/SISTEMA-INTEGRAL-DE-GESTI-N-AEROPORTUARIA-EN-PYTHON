"""Vista de gestión de vuelos."""
from __future__ import annotations

import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk

from config import COLORS, ESTADOS_VUELO, FONTS, ahora, dinero, fecha_humana
from views.base import VistaBase
from views.widgets import (Card, Modal, Tabla, boton, campo, combo, etiqueta,
                           separador)


def _etiqueta_aeropuerto(aeropuerto: dict) -> str:
    return f"{aeropuerto['codigo']} · {aeropuerto['ciudad']}"


class VuelosView(VistaBase):
    def construir(self) -> None:
        cab = self.encabezado(
            "Gestión de vuelos",
            "Programación, aeronaves, tarifas, puertas y estados operativos",
        )
        boton(cab.acciones, "Actualizar", self.refrescar, tipo="secondary",
              compacto=True, icono="↻").pack(side="right", padx=(8, 0))
        boton(cab.acciones, "Nuevo vuelo", self.nuevo_vuelo, tipo="primary",
              compacto=True, icono="+").pack(side="right")

        # Filtros ---------------------------------------------------------
        filtros = Card(self, padding=12)
        filtros.pack(fill="x", padx=24, pady=(0, 12))
        cont = filtros.cuerpo
        cont.grid_columnconfigure(0, weight=2)
        cont.grid_columnconfigure(1, weight=1)
        cont.grid_columnconfigure(2, weight=1)
        etiqueta(cont, "Buscar vuelo", size=8, bold=True,
                 color=COLORS["muted"]).grid(row=0, column=0, sticky="w")
        etiqueta(cont, "Estado", size=8, bold=True,
                 color=COLORS["muted"]).grid(row=0, column=1, sticky="w", padx=(10, 0))
        etiqueta(cont, "Destino", size=8, bold=True,
                 color=COLORS["muted"]).grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.var_busqueda = tk.StringVar()
        self.var_estado = tk.StringVar(value="Todos los estados")
        self.var_destino = tk.StringVar(value="Todos los destinos")
        entrada = campo(cont, self.var_busqueda)
        entrada.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        entrada.bind("<Return>", lambda _e: self.refrescar())
        self.combo_estado = combo(cont, ["Todos los estados", *ESTADOS_VUELO],
                                  self.var_estado)
        self.combo_estado.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(3, 0))
        self.combo_estado.bind("<<ComboboxSelected>>", lambda _e: self.refrescar())
        self.combo_destino = combo(cont, ["Todos los destinos"], self.var_destino)
        self.combo_destino.grid(row=1, column=2, sticky="ew", padx=(10, 0), pady=(3, 0))
        self.combo_destino.bind("<<ComboboxSelected>>", lambda _e: self.refrescar())
        acciones_filtro = tk.Frame(cont, bg=COLORS["card"])
        acciones_filtro.grid(row=1, column=3, sticky="e", padx=(12, 0), pady=(3, 0))
        boton(acciones_filtro, "Filtrar", self.refrescar, compacto=True,
              icono="⌕").pack(side="left", padx=(0, 6))
        boton(acciones_filtro, "Limpiar", self.limpiar_filtros, tipo="ghost",
              compacto=True).pack(side="left")

        # Tabla -----------------------------------------------------------
        card = Card(self, padding=0)
        card.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        cab_tabla = tk.Frame(card.cuerpo, bg=COLORS["card"], padx=16, pady=12)
        cab_tabla.pack(fill="x")
        etiqueta(cab_tabla, "Vuelos registrados", size=13, bold=True).pack(side="left")
        self.lbl_conteo = etiqueta(cab_tabla, "", size=9, color=COLORS["muted"])
        self.lbl_conteo.pack(side="right")
        separador(card.cuerpo).pack(fill="x")
        self.tabla = Tabla(card.cuerpo, [
            ("codigo", "CÓDIGO", 78, "center", False),
            ("ruta", "RUTA", 110, "center", False),
            ("salida", "SALIDA", 135, "center", False),
            ("aeronave", "AERONAVE", 190, "w", True),
            ("ocupacion", "ASIENTOS", 100, "center", False),
            ("puerta", "PUERTA", 70, "center", False),
            ("precio", "TARIFA", 80, "e", False),
            ("estado", "ESTADO", 125, "center", False),
        ], altura=12, on_doble_clic=self.editar_vuelo)
        self.tabla.pack(fill="both", expand=True, padx=8, pady=8)

        barra = tk.Frame(card.cuerpo, bg=COLORS["card"], padx=16, pady=10)
        barra.pack(fill="x")
        boton(barra, "Editar vuelo", self.editar_vuelo, tipo="secondary",
              compacto=True, icono="✎").pack(side="left", padx=(0, 6))
        boton(barra, "Cambiar estado", self.cambiar_estado, tipo="warning",
              compacto=True, icono="⇄").pack(side="left", padx=(0, 6))
        boton(barra, "Cancelar vuelo", self.cancelar_vuelo, tipo="danger",
              compacto=True, icono="✕").pack(side="left")
        etiqueta(barra, "Doble clic sobre una fila para editar", size=8,
                 color=COLORS["muted"]).pack(side="right")

    # ------------------------------------------------------------------
    def refrescar(self) -> None:
        aeropuertos = self.app.vuelos.listar_aeropuertos()
        valores_destino = ["Todos los destinos"] + [a["codigo"] for a in aeropuertos]
        self.combo_destino.configure(values=valores_destino)
        if self.var_destino.get() not in valores_destino:
            self.var_destino.set("Todos los destinos")

        vuelos = self.app.vuelos.listar(
            texto=self.var_busqueda.get(),
            estado="" if self.var_estado.get() == "Todos los estados" else self.var_estado.get(),
            destino="" if self.var_destino.get() == "Todos los destinos" else self.var_destino.get(),
        )
        filas = []
        for vuelo in vuelos:
            filas.append({
                "_iid": str(vuelo.id),
                "codigo": vuelo.codigo,
                "ruta": vuelo.ruta,
                "salida": fecha_humana(vuelo.fecha_salida),
                "aeronave": f"{vuelo.aeronave_modelo} · {vuelo.matricula}",
                "ocupacion": f"{vuelo.ocupados}/{vuelo.capacidad}",
                "puerta": vuelo.puerta,
                "precio": dinero(vuelo.precio),
                "estado": vuelo.estado,
            })
        self.tabla.set_filas(filas)
        self.lbl_conteo.configure(text=f"{len(vuelos)} vuelo(s)")

    def limpiar_filtros(self) -> None:
        self.var_busqueda.set("")
        self.var_estado.set("Todos los estados")
        self.var_destino.set("Todos los destinos")
        self.refrescar()

    def _vuelo_seleccionado(self):
        fila = self.tabla.seleccionado()
        if not fila:
            self.error("Selecciona un vuelo en la tabla.")
            return None
        vuelo = self.app.vuelos.obtener(int(fila["_iid"]))
        if not vuelo:
            self.error("El vuelo ya no existe.")
            return None
        return vuelo

    # ------------------------------------------------------------------
    # Formulario
    # ------------------------------------------------------------------
    def nuevo_vuelo(self) -> None:
        self._abrir_formulario(None)

    def editar_vuelo(self) -> None:
        vuelo = self._vuelo_seleccionado()
        if vuelo:
            if vuelo.estado in ("En vuelo", "Completado", "Cancelado"):
                self.error("No se puede editar un vuelo en vuelo, completado o cancelado.")
                return
            self._abrir_formulario(vuelo)

    def _abrir_formulario(self, vuelo) -> None:
        aeropuertos = self.app.vuelos.listar_aeropuertos()
        aeronaves = self.app.vuelos.listar_aeronaves()
        if not aeropuertos or not aeronaves:
            self.error("Primero deben existir aeropuertos y aeronaves registrados.")
            return
        mapa_aeropuertos = {_etiqueta_aeropuerto(a): a for a in aeropuertos}
        mapa_aeronaves = {
            f"{a['modelo']} · {a['matricula']} · cap. {a['capacidad']}": a
            for a in aeronaves
        }
        modal = Modal(self, "Editar vuelo" if vuelo else "Registrar nuevo vuelo",
                      ancho=610, alto=690)
        cuerpo = modal.cuerpo
        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(1, weight=1)

        def fila_form(fila: int, texto: str, widget, columna: int = 0,
                      colspan: int = 1) -> None:
            contenedor = tk.Frame(cuerpo, bg=COLORS["bg"])
            contenedor.grid(row=fila, column=columna, columnspan=colspan,
                            sticky="ew", padx=(0, 10) if columna == 0 else (10, 0),
                            pady=(0, 11))
            etiqueta(contenedor, texto.upper(), size=8, bold=True,
                     color=COLORS["muted"]).pack(anchor="w", pady=(0, 4))
            widget.pack(fill="x")

        var_codigo = tk.StringVar(value=vuelo.codigo if vuelo else self.app.vuelos.generar_codigo())
        var_origen = tk.StringVar(
            value=next((k for k, v in mapa_aeropuertos.items()
                        if vuelo and v["codigo"] == vuelo.origen_codigo),
                       next(iter(mapa_aeropuertos)))
        )
        opciones_destino = list(mapa_aeropuertos.keys())
        var_destino = tk.StringVar(
            value=next((k for k, v in mapa_aeropuertos.items()
                        if vuelo and v["codigo"] == vuelo.destino_codigo),
                       opciones_destino[1] if len(opciones_destino) > 1 else opciones_destino[0])
        )
        fecha_default = (ahora() + timedelta(days=1)).strftime("%Y-%m-%d")
        hora_default = "08:00"
        if vuelo:
            fecha_default, hora_default = vuelo.fecha_salida.split(" ", 1)
        var_fecha = tk.StringVar(value=fecha_default)
        var_hora = tk.StringVar(value=hora_default)
        etiqueta_aeronave = next(
            (k for k, v in mapa_aeronaves.items() if vuelo and v["id"] == vuelo.aeronave_id),
            next(iter(mapa_aeronaves)),
        )
        var_aeronave = tk.StringVar(value=etiqueta_aeronave)
        var_capacidad = tk.StringVar(value=str(vuelo.capacidad if vuelo else
                                               mapa_aeronaves[etiqueta_aeronave]["capacidad"]))
        var_puerta = tk.StringVar(value=vuelo.puerta if vuelo else "A01")
        var_precio = tk.StringVar(value=f"{vuelo.precio:.2f}" if vuelo else "150.00")

        entrada_codigo = campo(cuerpo, var_codigo, estado="readonly")
        # readonly ttk entry remains legible en el tema oscuro
        fila_form(0, "Código de vuelo (automático)", entrada_codigo)
        fila_form(0, "Aeronave", combo(cuerpo, list(mapa_aeronaves),
                                        var_aeronave, estado="readonly"), columna=1)
        fila_form(1, "Aeropuerto de origen", combo(cuerpo, list(mapa_aeropuertos),
                                                    var_origen), columna=0)
        fila_form(1, "Aeropuerto de destino", combo(cuerpo, list(mapa_aeropuertos),
                                                     var_destino), columna=1)
        fila_form(2, "Fecha de salida (AAAA-MM-DD)", campo(cuerpo, var_fecha), columna=0)
        fila_form(2, "Hora de salida (HH:MM)", campo(cuerpo, var_hora), columna=1)
        fila_form(3, "Capacidad de pasajeros", campo(cuerpo, var_capacidad), columna=0)
        fila_form(3, "Puerta de embarque", campo(cuerpo, var_puerta), columna=1)
        fila_form(4, "Tarifa del boleto (S/)", campo(cuerpo, var_precio), columna=0)

        lbl_limite = etiqueta(cuerpo, "", size=8, color=COLORS["muted"])
        lbl_limite.grid(row=4, column=1, sticky="w", padx=(10, 0), pady=(18, 0))

        def actualizar_aeronave(_evento=None) -> None:
            datos = mapa_aeronaves.get(var_aeronave.get())
            if datos:
                lbl_limite.configure(
                    text=f"Capacidad máxima: {datos['capacidad']} · {datos['asientos_por_fila']} asientos por fila"
                )
                if not vuelo:
                    var_capacidad.set(str(datos["capacidad"]))
        var_aeronave.trace_add("write", lambda *_: actualizar_aeronave())
        actualizar_aeronave()

        etiqueta(
            cuerpo,
            "La capacidad se distribuye automáticamente en el mapa de asientos. "
            "No se puede reducir por debajo de los asientos ya reservados.",
            size=8, color=COLORS["muted"], wraplength=530, justify="left",
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(4, 0))

        def guardar() -> None:
            try:
                origen = mapa_aeropuertos[var_origen.get()]["codigo"]
                destino = mapa_aeropuertos[var_destino.get()]["codigo"]
                aeronave_id = mapa_aeronaves[var_aeronave.get()]["id"]
                if vuelo:
                    self.app.vuelos.actualizar(
                        vuelo.id, origen, destino, var_fecha.get(), var_hora.get(),
                        aeronave_id, var_capacidad.get(), var_puerta.get(), var_precio.get(),
                    )
                    mensaje = f"Vuelo {vuelo.codigo} actualizado correctamente."
                else:
                    nuevo = self.app.vuelos.registrar(
                        origen, destino, var_fecha.get(), var_hora.get(), aeronave_id,
                        var_capacidad.get(), var_puerta.get(), var_precio.get(),
                    )
                    mensaje = f"Vuelo {nuevo.codigo} registrado correctamente."
                modal.cerrar()
                self.refrescar()
                self.info("Vuelos", mensaje)
            except Exception as exc:
                self.error(exc)

        boton(modal.pie, "Cancelar", modal.cerrar, tipo="ghost",
              compacto=True).pack(side="right", padx=(8, 0))
        boton(modal.pie, "Guardar vuelo", guardar, tipo="primary",
              compacto=True, icono="✓").pack(side="right")
        modal.esperar()

    # ------------------------------------------------------------------
    def cambiar_estado(self) -> None:
        vuelo = self._vuelo_seleccionado()
        if not vuelo:
            return
        permitidos = [
            estado for estado in ESTADOS_VUELO
            if estado in self.app.vuelos.TRANSICIONES.get(vuelo.estado, set())
            and estado != "Cancelado"
        ]
        if not permitidos:
            self.error(f"El vuelo {vuelo.codigo} está en un estado final ({vuelo.estado}).")
            return
        modal = Modal(self, "Cambiar estado del vuelo", ancho=460, alto=320)
        etiqueta(modal.cuerpo, vuelo.codigo, size=20, bold=True).pack(anchor="w")
        etiqueta(modal.cuerpo, f"{vuelo.ruta_ciudades} · {fecha_humana(vuelo.fecha_salida)}",
                 size=9, color=COLORS["muted"]).pack(anchor="w", pady=(2, 14))
        fila_estado = tk.Frame(modal.cuerpo, bg=COLORS["bg"])
        fila_estado.pack(fill="x")
        etiqueta(fila_estado, "Estado actual", size=8, bold=True,
                 color=COLORS["muted"]).pack(side="left")
        from views.widgets import chip_estado
        chip_estado(fila_estado, vuelo.estado).pack(side="left", padx=(8, 0))
        etiqueta(modal.cuerpo, "Nuevo estado", size=8, bold=True,
                 color=COLORS["muted"]).pack(anchor="w", pady=(18, 4))
        var_estado = tk.StringVar(value=permitidos[0])
        combo_estado = combo(modal.cuerpo, permitidos, var_estado)
        combo_estado.pack(fill="x")
        etiqueta(
            modal.cuerpo,
            "Transiciones permitidas según el flujo operativo del aeropuerto.",
            size=8, color=COLORS["muted"],
        ).pack(anchor="w", pady=(8, 0))

        def aplicar() -> None:
            try:
                actualizado = self.app.vuelos.cambiar_estado(vuelo.id, var_estado.get())
                modal.cerrar()
                self.refrescar()
                self.info("Estado actualizado",
                          f"{actualizado.codigo} ahora está en estado '{actualizado.estado}'.")
            except Exception as exc:
                self.error(exc)

        boton(modal.pie, "Cancelar", modal.cerrar, tipo="ghost",
              compacto=True).pack(side="right", padx=(8, 0))
        boton(modal.pie, "Aplicar cambio", aplicar, tipo="warning",
              compacto=True, icono="⇄").pack(side="right")
        modal.esperar()

    def cancelar_vuelo(self) -> None:
        vuelo = self._vuelo_seleccionado()
        if not vuelo:
            return
        if not self.confirmar(
            "Cancelar vuelo",
            f"¿Cancelar el vuelo {vuelo.codigo} ({vuelo.ruta})?\n\n"
            "Las reservas activas también serán canceladas. Esta acción se puede "
            "deshacer desde el historial mientras la sesión siga abierta.",
        ):
            return
        try:
            self.app.vuelos.cancelar(vuelo.id)
            self.refrescar()
            self.info("Vuelo cancelado", f"El vuelo {vuelo.codigo} fue cancelado.")
        except Exception as exc:
            self.error(exc)
