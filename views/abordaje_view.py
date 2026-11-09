"""Vista del proceso de abordaje con cola FIFO."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from config import COLORS, fecha_humana
from views.base import VistaBase
from views.widgets import (Card, Tabla, boton, chip_estado, combo, etiqueta,
                           separador)


class AbordajeView(VistaBase):
    def construir(self) -> None:
        self._mapa_vuelos = {}
        self._codigo_vuelo_actual = None
        cab = self.encabezado(
            "Proceso de abordaje",
            "Cola FIFO, validación de check-in y control visual del embarque",
        )
        boton(cab.acciones, "Actualizar", self.refrescar, tipo="secondary",
              compacto=True, icono="↻").pack(side="right")

        # Selector de vuelo ----------------------------------------------
        selector = Card(self, padding=12)
        selector.pack(fill="x", padx=24, pady=(0, 12))
        cont = selector.cuerpo
        cont.grid_columnconfigure(1, weight=1)
        etiqueta(cont, "VUELO EN OPERACIÓN", size=8, bold=True,
                 color=COLORS["muted"]).grid(row=0, column=0, sticky="w")
        self.var_vuelo = tk.StringVar()
        self.combo_vuelo = combo(cont, [], self.var_vuelo)
        self.combo_vuelo.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))
        self.combo_vuelo.bind("<<ComboboxSelected>>", lambda _e: self._cambiar_vuelo())
        self.info_vuelo = tk.Frame(cont, bg=COLORS["card"])
        self.info_vuelo.grid(row=0, column=2, rowspan=2, sticky="e", padx=(20, 0))
        self.lbl_ruta = etiqueta(self.info_vuelo, "—", size=12, bold=True)
        self.lbl_ruta.pack(anchor="e")
        self.lbl_salida = etiqueta(self.info_vuelo, "", size=8, color=COLORS["muted"])
        self.lbl_salida.pack(anchor="e")
        self.lbl_estado_vuelo = etiqueta(self.info_vuelo, "", size=8,
                                         color=COLORS["muted"])
        self.lbl_estado_vuelo.pack(anchor="e")

        cuerpo = tk.Frame(self, bg=COLORS["bg"])
        cuerpo.pack(fill="both", expand=True, padx=24, pady=(0, 14))
        cuerpo.grid_columnconfigure(0, weight=3, uniform="abordaje")
        cuerpo.grid_columnconfigure(1, weight=2, uniform="abordaje")
        cuerpo.grid_rowconfigure(0, weight=1)

        # Pasajeros con check-in -----------------------------------------
        card_pasajeros = Card(cuerpo, padding=0)
        card_pasajeros.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        cab_p = tk.Frame(card_pasajeros.cuerpo, bg=COLORS["card"], padx=14, pady=11)
        cab_p.pack(fill="x")
        etiqueta(cab_p, "Pasajeros con check-in", size=12, bold=True).pack(side="left")
        self.lbl_pasajeros = etiqueta(cab_p, "", size=8, color=COLORS["muted"])
        self.lbl_pasajeros.pack(side="left", padx=(8, 0))
        separador(card_pasajeros.cuerpo).pack(fill="x")
        self.tabla_pasajeros = Tabla(card_pasajeros.cuerpo, [
            ("pasajero", "PASAJERO", 185, "w", True),
            ("documento", "DOCUMENTO", 110, "center", False),
            ("reserva", "RESERVA", 92, "center", False),
            ("asiento", "ASIENTO", 75, "center", False),
            ("tarjeta", "TARJETA", 98, "center", False),
            ("estado", "ESTADO", 82, "center", False),
        ], altura=12, on_doble_clic=self.agregar_seleccionado)
        self.tabla_pasajeros.pack(fill="both", expand=True, padx=8, pady=8)
        barra_p = tk.Frame(card_pasajeros.cuerpo, bg=COLORS["card"], padx=14, pady=9)
        barra_p.pack(fill="x")
        boton(barra_p, "Agregar a la cola", self.agregar_seleccionado,
              tipo="primary", compacto=True, icono="+").pack(side="left", padx=(0, 6))
        boton(barra_p, "Agregar todos", self.agregar_todos, tipo="secondary",
              compacto=True, icono="⇥").pack(side="left")
        etiqueta(barra_p, "Solo pasajeros con check-in válido", size=8,
                 color=COLORS["muted"]).pack(side="right")

        # Cola FIFO -------------------------------------------------------
        card_cola = Card(cuerpo, padding=15)
        card_cola.grid(row=0, column=1, sticky="nsew")
        etiqueta(card_cola.cuerpo, "Cola de abordaje", size=13, bold=True).pack(anchor="w")
        etiqueta(card_cola.cuerpo, "FIFO · primero en entrar, primero en abordar",
                 size=8, color=COLORS["muted"]).pack(anchor="w", pady=(1, 9))

        estadisticas = tk.Frame(card_cola.cuerpo, bg=COLORS["card"])
        estadisticas.pack(fill="x")
        for col in range(4):
            estadisticas.grid_columnconfigure(col, weight=1, uniform="mini")
        self.stats = {}
        for col, (clave, titulo, color) in enumerate([
            ("total_checkin", "CHECK-IN", COLORS["accent"]),
            ("en_cola", "EN COLA", COLORS["warning"]),
            ("abordados", "ABORDADOS", COLORS["success"]),
            ("pendientes", "PENDIENTES", COLORS["danger"]),
        ]):
            caja = tk.Frame(estadisticas, bg=COLORS["card_alt"], padx=7, pady=6)
            caja.grid(row=0, column=col, sticky="ew",
                      padx=(0, 3) if col < 3 else 0)
            etiqueta(caja, titulo, size=6, bold=True,
                     color=COLORS["muted"]).pack(anchor="w")
            valor = etiqueta(caja, "0", size=15, bold=True, color=color)
            valor.pack(anchor="w")
            self.stats[clave] = valor

        progreso = tk.Frame(card_cola.cuerpo, bg=COLORS["card"])
        progreso.pack(fill="x", pady=(12, 2))
        self.lbl_progreso = etiqueta(progreso, "0% abordado", size=9,
                                     bold=True, color=COLORS["text_soft"])
        self.lbl_progreso.pack(side="left")
        self.lbl_progreso_cantidad = etiqueta(progreso, "0 de 0", size=8,
                                              color=COLORS["muted"])
        self.lbl_progreso_cantidad.pack(side="right")
        self.var_progreso = tk.DoubleVar(value=0)
        barra = ttk.Progressbar(card_cola.cuerpo, variable=self.var_progreso,
                                maximum=100)
        barra.pack(fill="x", pady=(4, 12))

        self.tabla_cola = Tabla(card_cola.cuerpo, [
            ("posicion", "#", 32, "center", False),
            ("pasajero", "PASAJERO", 145, "w", True),
            ("asiento", "ASIENTO", 78, "center", False),
            ("reserva", "RESERVA", 92, "center", False),
        ], altura=6)
        self.tabla_cola.pack(fill="both", expand=True)
        boton(card_cola.cuerpo, "Procesar siguiente", self.procesar_siguiente,
              tipo="success", compacto=False, icono="➜").pack(fill="x", pady=(12, 5))
        boton(card_cola.cuerpo, "Finalizar abordaje", self.finalizar_abordaje,
              tipo="warning", compacto=True, icono="✓").pack(fill="x")

    # ------------------------------------------------------------------
    def refrescar(self) -> None:
        vuelos = self.app.abordaje.vuelos_operables()
        self._mapa_vuelos = {
            f"{v.codigo} · {v.ruta} · {fecha_humana(v.fecha_salida)} · {v.puerta}": v
            for v in vuelos
        }
        valores = list(self._mapa_vuelos.keys())
        self.combo_vuelo.configure(values=valores)
        etiqueta_actual = next(
            (k for k, v in self._mapa_vuelos.items() if v.codigo == self._codigo_vuelo_actual),
            valores[0] if valores else "",
        )
        self.var_vuelo.set(etiqueta_actual)
        vuelo = self._mapa_vuelos.get(etiqueta_actual)
        self._codigo_vuelo_actual = vuelo.codigo if vuelo else None
        if not vuelo:
            self.lbl_ruta.configure(text="Sin vuelos operables")
            self.lbl_salida.configure(text="Registra vuelos o abre el check-in")
            self.lbl_estado_vuelo.configure(text="")
            self.tabla_pasajeros.limpiar()
            self.tabla_cola.limpiar()
            self.lbl_pasajeros.configure(text="0 pasajeros")
            for valor in self.stats.values():
                valor.configure(text="0")
            self.var_progreso.set(0)
            self.lbl_progreso.configure(text="0% abordado")
            self.lbl_progreso_cantidad.configure(text="0 de 0")
            return

        self.lbl_ruta.configure(text=f"{vuelo.codigo} · {vuelo.ruta}")
        self.lbl_salida.configure(
            text=f"{fecha_humana(vuelo.fecha_salida)} · Puerta {vuelo.puerta} · "
                 f"{vuelo.aeronave_modelo}"
        )
        self.lbl_estado_vuelo.configure(text=f"Estado: {vuelo.estado}",
                                         fg=COLORS["warning"] if vuelo.estado == "Abordaje"
                                         else COLORS["accent"])

        pasajeros = self.app.abordaje.listar_pasajeros(vuelo.id)
        filas = []
        for p in pasajeros:
            filas.append({
                "_iid": str(p["reserva_id"]),
                "pasajero": p["pasajero"],
                "documento": p["documento"],
                "reserva": p["reserva_codigo"],
                "asiento": p["asiento"],
                "tarjeta": p["tarjeta"],
                "estado": p["estado"],
            })
        self.tabla_pasajeros.set_filas(filas)
        self.lbl_pasajeros.configure(text=f"{len(pasajeros)} pasajero(s)")

        cola = self.app.abordaje.obtener_cola(vuelo.id)
        filas_cola = []
        for item in cola:
            filas_cola.append({
                "_iid": str(item["cola_id"]),
                "posicion": item["posicion"],
                "pasajero": item["pasajero"],
                "asiento": item["asiento"],
                "reserva": item["reserva_codigo"],
                "estado": "En cola",
            })
        self.tabla_cola.set_filas(filas_cola, usar_estado=False)

        resumen = self.app.abordaje.resumen(vuelo.id)
        for clave, valor in resumen.items():
            if clave in self.stats:
                self.stats[clave].configure(text=str(valor))
        self.var_progreso.set(resumen["porcentaje"])
        self.lbl_progreso.configure(text=f"{resumen['porcentaje']:.0f}% abordado")
        self.lbl_progreso_cantidad.configure(
            text=f"{resumen['abordados']} de {resumen['total_checkin']}"
        )

    def _cambiar_vuelo(self) -> None:
        vuelo = self._mapa_vuelos.get(self.var_vuelo.get())
        self._codigo_vuelo_actual = vuelo.codigo if vuelo else None
        self.refrescar()

    def _vuelo(self):
        vuelo = self._mapa_vuelos.get(self.var_vuelo.get())
        if not vuelo:
            self.error("Selecciona un vuelo con check-in habilitado.")
        return vuelo

    def agregar_seleccionado(self) -> None:
        if not self._vuelo():
            return
        fila = self.tabla_pasajeros.seleccionado()
        if not fila:
            self.error("Selecciona un pasajero con check-in en la tabla.")
            return
        try:
            item = self.app.abordaje.agregar_a_cola(int(fila["_iid"]))
            self.refrescar()
            self.notificar(
                f"{item['pasajero']} agregado a la cola FIFO (asiento {item['asiento']})."
            )
        except Exception as exc:
            self.error(exc)

    def agregar_todos(self) -> None:
        vuelo = self._vuelo()
        if not vuelo:
            return
        try:
            agregados, omitidos = self.app.abordaje.agregar_todos(vuelo.id)
            self.refrescar()
            if agregados:
                self.info(
                    "Cola de abordaje",
                    f"{agregados} pasajero(s) agregados a la cola FIFO."
                    + (f" {omitidos} omitido(s)." if omitidos else ""),
                )
            else:
                self.info(
                    "Cola de abordaje",
                    "No hay pasajeros pendientes de agregar. Todos ya están en cola o abordados.",
                )
        except Exception as exc:
            self.error(exc)

    def procesar_siguiente(self) -> None:
        vuelo = self._vuelo()
        if not vuelo:
            return
        try:
            item = self.app.abordaje.procesar_siguiente(vuelo.id)
            self.refrescar()
            self.info(
                "Abordaje registrado",
                f"Turno #{item['posicion_abordaje']} · {item['pasajero']}\n"
                f"Reserva {item['reserva_codigo']} · Asiento {item['asiento']}",
            )
        except Exception as exc:
            self.error(exc)

    def finalizar_abordaje(self) -> None:
        vuelo = self._vuelo()
        if not vuelo:
            return
        resumen = self.app.abordaje.resumen(vuelo.id)
        if resumen["total_checkin"] == 0:
            self.error("No hay pasajeros con check-in para este vuelo.")
            return
        if vuelo.estado != "Abordaje":
            self.error(
                "El abordaje aún no ha iniciado. Agrega pasajeros a la cola y procesa al menos uno."
            )
            return
        forzar = False
        if resumen["en_cola"] or resumen["pendientes"]:
            if not self.confirmar(
                "Cerrar abordaje con pendientes",
                f"Hay {resumen['en_cola']} pasajero(s) en cola y "
                f"{resumen['pendientes']} pendiente(s) sin abordar.\n\n"
                "¿Finalizar de todos modos? Se marcarán los turnos en cola como retirados. "
                "El vuelo pasará a estado 'En vuelo'.",
            ):
                return
            forzar = True
        try:
            resultado = self.app.abordaje.finalizar(vuelo.id, forzar=forzar)
            self.refrescar()
            self.info(
                "Abordaje finalizado",
                f"Vuelo {vuelo.codigo} cerrado con {resultado['abordados']} pasajero(s) "
                f"a bordo. Estado actual: En vuelo.",
            )
        except Exception as exc:
            self.error(exc)
