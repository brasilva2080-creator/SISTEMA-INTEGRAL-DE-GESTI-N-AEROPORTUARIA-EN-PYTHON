"""Vista de rutas y destinos con grafo de conexiones."""
from __future__ import annotations

import tkinter as tk

from config import COLORS
from views.base import VistaBase
from views.widgets import (Card, GrafoCanvas, Modal, Tabla, boton, campo, combo,
                           etiqueta, separador)


class RutasView(VistaBase):
    def construir(self) -> None:
        self._mapa_aeropuertos = {}
        cab = self.encabezado(
            "Rutas y destinos",
            "Aeropuertos como vértices, conexiones como aristas y cálculo BFS de rutas",
        )
        boton(cab.acciones, "Actualizar", self.refrescar, tipo="secondary",
              compacto=True, icono="↻").pack(side="right", padx=(8, 0))
        boton(cab.acciones, "Nuevo aeropuerto", self.nuevo_aeropuerto, tipo="secondary",
              compacto=True, icono="+").pack(side="right", padx=(8, 0))
        boton(cab.acciones, "Nueva ruta", self.nueva_ruta, tipo="primary",
              compacto=True, icono="+").pack(side="right")

        cuerpo = tk.Frame(self, bg=COLORS["bg"])
        cuerpo.pack(fill="both", expand=True, padx=24, pady=(0, 14))
        cuerpo.grid_columnconfigure(0, weight=3, uniform="rutas")
        cuerpo.grid_columnconfigure(1, weight=2, uniform="rutas")
        cuerpo.grid_rowconfigure(0, weight=3)
        cuerpo.grid_rowconfigure(1, weight=2)

        # Aeropuertos -----------------------------------------------------
        card_aeropuertos = Card(cuerpo, padding=0)
        card_aeropuertos.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 10))
        cab_a = tk.Frame(card_aeropuertos.cuerpo, bg=COLORS["card"], padx=14, pady=11)
        cab_a.pack(fill="x")
        etiqueta(cab_a, "Aeropuertos registrados", size=12, bold=True).pack(side="left")
        self.lbl_aeropuertos = etiqueta(cab_a, "", size=8, color=COLORS["muted"])
        self.lbl_aeropuertos.pack(side="right")
        separador(card_aeropuertos.cuerpo).pack(fill="x")
        self.tabla_aeropuertos = Tabla(card_aeropuertos.cuerpo, [
            ("codigo", "IATA", 60, "center", False),
            ("ciudad", "CIUDAD", 100, "w", False),
            ("nombre", "AEROPUERTO", 280, "w", True),
            ("pais", "PAÍS", 90, "center", False),
        ], altura=7)
        self.tabla_aeropuertos.pack(fill="both", expand=True, padx=8, pady=7)

        # Grafo -----------------------------------------------------------
        card_grafo = Card(cuerpo, padding=12)
        card_grafo.grid(row=0, column=1, sticky="nsew", pady=(0, 10))
        cab_g = tk.Frame(card_grafo.cuerpo, bg=COLORS["card"])
        cab_g.pack(fill="x", pady=(0, 5))
        etiqueta(cab_g, "Red de conexiones", size=12, bold=True).pack(side="left")
        self.lbl_conexo = etiqueta(cab_g, "", size=8, color=COLORS["muted"])
        self.lbl_conexo.pack(side="right")
        self.grafo_canvas = GrafoCanvas(card_grafo.cuerpo, alto=250)
        self.grafo_canvas.pack(fill="both", expand=True)

        # Rutas -----------------------------------------------------------
        card_rutas = Card(cuerpo, padding=0)
        card_rutas.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        cab_r = tk.Frame(card_rutas.cuerpo, bg=COLORS["card"], padx=14, pady=10)
        cab_r.pack(fill="x")
        etiqueta(cab_r, "Conexiones directas", size=12, bold=True).pack(side="left")
        self.lbl_rutas = etiqueta(cab_r, "", size=8, color=COLORS["muted"])
        self.lbl_rutas.pack(side="right")
        separador(card_rutas.cuerpo).pack(fill="x")
        self.tabla_rutas = Tabla(card_rutas.cuerpo, [
            ("trayecto", "TRAYECTO", 150, "center", False),
            ("ciudades", "CIUDADES", 220, "w", True),
            ("distancia", "DISTANCIA", 105, "center", False),
            ("duracion", "DURACIÓN", 100, "center", False),
        ], altura=5)
        self.tabla_rutas.pack(fill="both", expand=True, padx=8, pady=7)

        # Cálculo de ruta -------------------------------------------------
        card_calculo = Card(cuerpo, padding=15)
        card_calculo.grid(row=1, column=1, sticky="nsew")
        etiqueta(card_calculo.cuerpo, "Calcular ruta", size=12, bold=True).pack(anchor="w")
        etiqueta(card_calculo.cuerpo, "Búsqueda en anchura (BFS) sobre el grafo",
                 size=8, color=COLORS["muted"]).pack(anchor="w", pady=(1, 9))
        etiqueta(card_calculo.cuerpo, "ORIGEN", size=8, bold=True,
                 color=COLORS["muted"]).pack(anchor="w")
        self.var_origen = tk.StringVar()
        self.combo_origen = combo(card_calculo.cuerpo, [], self.var_origen)
        self.combo_origen.pack(fill="x", pady=(3, 7))
        etiqueta(card_calculo.cuerpo, "DESTINO", size=8, bold=True,
                 color=COLORS["muted"]).pack(anchor="w")
        self.var_destino = tk.StringVar()
        self.combo_destino = combo(card_calculo.cuerpo, [], self.var_destino)
        self.combo_destino.pack(fill="x", pady=(3, 9))
        boton(card_calculo.cuerpo, "Buscar mejor ruta", self.calcular_ruta,
              tipo="primary", compacto=True, icono="⌕").pack(fill="x")
        separador(card_calculo.cuerpo).pack(fill="x", pady=(12, 9))
        self.lbl_resultado = etiqueta(
            card_calculo.cuerpo, "Selecciona origen y destino",
            size=14, bold=True, color=COLORS["accent"], wraplength=310,
        )
        self.lbl_resultado.pack(anchor="w")
        self.lbl_detalle_ruta = etiqueta(
            card_calculo.cuerpo, "", size=9, color=COLORS["muted"],
            wraplength=310, justify="left",
        )
        self.lbl_detalle_ruta.pack(anchor="w", pady=(4, 0))

    # ------------------------------------------------------------------
    def refrescar(self) -> None:
        aeropuertos = self.app.rutas.listar_aeropuertos()
        self._mapa_aeropuertos = {f"{a.codigo} · {a.ciudad}": a for a in aeropuertos}
        valores = list(self._mapa_aeropuertos.keys())
        actual_origen = getattr(self, "_origen_actual", None)
        actual_destino = getattr(self, "_destino_actual", None)
        self.combo_origen.configure(values=valores)
        self.combo_destino.configure(values=valores)
        origen = next((k for k, a in self._mapa_aeropuertos.items()
                       if a.codigo == actual_origen), valores[0] if valores else "")
        destino = next((k for k, a in self._mapa_aeropuertos.items()
                        if a.codigo == actual_destino),
                       valores[1] if len(valores) > 1 else valores[0] if valores else "")
        self.var_origen.set(origen)
        self.var_destino.set(destino)
        if origen:
            self._origen_actual = self._mapa_aeropuertos[origen].codigo
        if destino:
            self._destino_actual = self._mapa_aeropuertos[destino].codigo

        filas = []
        for a in aeropuertos:
            filas.append({
                "_iid": str(a.id),
                "codigo": a.codigo,
                "ciudad": a.ciudad,
                "nombre": a.nombre,
                "pais": a.pais,
            })
        self.tabla_aeropuertos.set_filas(filas, usar_estado=False)
        self.lbl_aeropuertos.configure(text=f"{len(aeropuertos)} aeropuerto(s)")

        rutas = self.app.rutas.listar_rutas()
        filas_r = []
        for r in rutas:
            filas_r.append({
                "_iid": str(r.id),
                "trayecto": r.trayecto,
                "ciudades": f"{r.origen_ciudad} ↔ {r.destino_ciudad}",
                "distancia": f"{r.distancia_km:,.0f} km",
                "duracion": self._duracion(r.duracion_min),
            })
        self.tabla_rutas.set_filas(filas_r, usar_estado=False)
        self.lbl_rutas.configure(text=f"{len(rutas)} conexion(es)")

        grafo = self.app.rutas.construir_grafo()
        self.grafo_canvas.dibujar(grafo)
        resumen = self.app.rutas.resumen()
        self.lbl_conexo.configure(
            text=f"{resumen['rutas']} aristas · "
                 + ("red conexa" if resumen["conexo"] else "red fragmentada")
        )

    @staticmethod
    def _duracion(minutos: int) -> str:
        horas, mins = divmod(int(minutos), 60)
        return f"{horas} h {mins:02d} min" if horas else f"{mins} min"

    def calcular_ruta(self) -> None:
        origen = self._mapa_aeropuertos.get(self.var_origen.get())
        destino = self._mapa_aeropuertos.get(self.var_destino.get())
        if not origen or not destino:
            self.error("Selecciona un aeropuerto de origen y otro de destino.")
            return
        try:
            resultado = self.app.rutas.calcular_ruta(origen.codigo, destino.codigo)
            self._origen_actual = origen.codigo
            self._destino_actual = destino.codigo
            self.lbl_resultado.configure(text=resultado["texto"], fg=COLORS["accent"])
            detalle = (
                f"{resultado['distancia_km']:,.0f} km · "
                f"{self._duracion(resultado['duracion_min'])} · "
                f"{resultado['escalas']} escala(s)\n"
                + " · ".join(resultado["ciudades"])
            )
            self.lbl_detalle_ruta.configure(text=detalle, fg=COLORS["text_soft"])
            self.notificar(f"Ruta calculada: {resultado['texto']}")
        except Exception as exc:
            self.lbl_resultado.configure(text="Sin ruta disponible", fg=COLORS["danger"])
            self.lbl_detalle_ruta.configure(text=str(exc), fg=COLORS["danger"])
            self.error(exc)

    # ------------------------------------------------------------------
    def nuevo_aeropuerto(self) -> None:
        modal = Modal(self, "Registrar aeropuerto", ancho=540, alto=610)
        cuerpo = modal.cuerpo
        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(1, weight=1)

        def agregar(fila, col, texto, variable, colspan=1):
            caja = tk.Frame(cuerpo, bg=COLORS["bg"])
            caja.grid(row=fila, column=col, columnspan=colspan, sticky="ew",
                      padx=(0, 10) if col == 0 else (10, 0), pady=(0, 12))
            etiqueta(caja, texto.upper(), size=8, bold=True,
                     color=COLORS["muted"]).pack(anchor="w", pady=(0, 4))
            campo(caja, variable).pack(fill="x")

        var_codigo = tk.StringVar()
        var_nombre = tk.StringVar()
        var_ciudad = tk.StringVar()
        var_pais = tk.StringVar(value="Perú")
        var_lat = tk.StringVar()
        var_lon = tk.StringVar()
        agregar(0, 0, "Código IATA (3 letras)", var_codigo)
        agregar(0, 1, "País", var_pais)
        agregar(1, 0, "Ciudad", var_ciudad)
        agregar(1, 1, "Latitud (opcional)", var_lat)
        agregar(2, 0, "Nombre del aeropuerto", var_nombre, colspan=2)
        agregar(3, 1, "Longitud (opcional)", var_lon)
        etiqueta(
            cuerpo,
            "Las coordenadas permiten ubicar el aeropuerto en el mapa del grafo. "
            "Si se omiten, se usará una distribución circular.",
            size=8, color=COLORS["muted"], wraplength=460, justify="left",
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))

        def guardar():
            try:
                aeropuerto = self.app.rutas.registrar_aeropuerto(
                    var_codigo.get(), var_nombre.get(), var_ciudad.get(),
                    var_pais.get(), var_lat.get(), var_lon.get(),
                )
                modal.cerrar()
                self.refrescar()
                self.info("Aeropuerto registrado",
                          f"{aeropuerto.codigo} · {aeropuerto.ciudad} agregado al grafo.")
            except Exception as exc:
                self.error(exc)

        boton(modal.pie, "Cancelar", modal.cerrar, tipo="ghost",
              compacto=True).pack(side="right", padx=(8, 0))
        boton(modal.pie, "Guardar", guardar, tipo="primary",
              compacto=True, icono="✓").pack(side="right")
        modal.esperar()

    def nueva_ruta(self) -> None:
        aeropuertos = self.app.rutas.listar_aeropuertos()
        if len(aeropuertos) < 2:
            self.error("Se necesitan al menos dos aeropuertos para crear una ruta.")
            return
        modal = Modal(self, "Registrar conexión aérea", ancho=500, alto=480)
        mapa = {f"{a.codigo} · {a.ciudad}": a for a in aeropuertos}
        valores = list(mapa.keys())
        etiqueta(modal.cuerpo, "ORIGEN", size=8, bold=True,
                 color=COLORS["muted"]).pack(anchor="w")
        var_origen = tk.StringVar(value=valores[0])
        combo(modal.cuerpo, valores, var_origen).pack(fill="x", pady=(3, 12))
        etiqueta(modal.cuerpo, "DESTINO", size=8, bold=True,
                 color=COLORS["muted"]).pack(anchor="w")
        var_destino = tk.StringVar(value=valores[1])
        combo(modal.cuerpo, valores, var_destino).pack(fill="x", pady=(3, 12))
        fila = tk.Frame(modal.cuerpo, bg=COLORS["bg"])
        fila.pack(fill="x")
        caja_d = tk.Frame(fila, bg=COLORS["bg"])
        caja_d.pack(side="left", fill="x", expand=True, padx=(0, 6))
        etiqueta(caja_d, "DISTANCIA (KM)", size=8, bold=True,
                 color=COLORS["muted"]).pack(anchor="w")
        var_distancia = tk.StringVar()
        campo(caja_d, var_distancia).pack(fill="x", pady=(3, 0))
        caja_t = tk.Frame(fila, bg=COLORS["bg"])
        caja_t.pack(side="left", fill="x", expand=True, padx=(6, 0))
        etiqueta(caja_t, "DURACIÓN (MIN)", size=8, bold=True,
                 color=COLORS["muted"]).pack(anchor="w")
        var_duracion = tk.StringVar()
        campo(caja_t, var_duracion).pack(fill="x", pady=(3, 0))
        etiqueta(
            modal.cuerpo,
            "La conexión se representa como una arista no dirigida. No se permiten duplicados.",
            size=8, color=COLORS["muted"], wraplength=430, justify="left",
        ).pack(anchor="w", pady=(14, 0))

        def guardar():
            try:
                origen = mapa[var_origen.get()]
                destino = mapa[var_destino.get()]
                ruta = self.app.rutas.registrar_ruta(
                    origen.codigo, destino.codigo,
                    var_distancia.get(), var_duracion.get(),
                )
                modal.cerrar()
                self.refrescar()
                self.info("Ruta registrada",
                          f"Conexión {ruta.trayecto} agregada al grafo.")
            except Exception as exc:
                self.error(exc)

        boton(modal.pie, "Cancelar", modal.cerrar, tipo="ghost",
              compacto=True).pack(side="right", padx=(8, 0))
        boton(modal.pie, "Guardar conexión", guardar, tipo="primary",
              compacto=True, icono="✓").pack(side="right")
        modal.esperar()
