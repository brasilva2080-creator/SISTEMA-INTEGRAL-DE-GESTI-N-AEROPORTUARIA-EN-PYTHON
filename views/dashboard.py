"""Panel principal con tarjetas estadísticas y gráficos."""
from __future__ import annotations

import tkinter as tk

from config import COLORS, ESTADOS_VUELO, dinero, fecha_corta, fecha_humana
from views.base import VistaBase
from views.widgets import Card, StatCard, Tabla, boton, etiqueta, separador

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_DISPONIBLE = True
except Exception:  # pragma: no cover - depende del entorno
    MATPLOTLIB_DISPONIBLE = False


class DashboardView(VistaBase):
    def construir(self) -> None:
        cab = self.encabezado(
            "Panel de control",
            "Visión general de la operación aeroportuaria en tiempo real",
        )
        boton(cab.acciones, "Actualizar", self.refrescar, tipo="secondary",
              compacto=True, icono="↻").pack(side="right", padx=(8, 0))
        boton(cab.acciones, "Abrir abordaje", lambda: self.app.abrir_vista("abordaje"),
              tipo="primary", compacto=True, icono="➜").pack(side="right")

        self.cards: dict[str, StatCard] = {}
        contenedor_cards = tk.Frame(self, bg=COLORS["bg"])
        contenedor_cards.pack(fill="x", padx=20, pady=(2, 12))
        definiciones = [
            ("total_vuelos", "Total de vuelos", "✈", COLORS["accent"], "Registrados en el sistema"),
            ("programados", "Programados", "◷", COLORS["success"], "Listos para operar"),
            ("abordaje", "En abordaje", "⇥", COLORS["warning"], "Embarque en curso"),
            ("completados", "Completados", "✓", COLORS["purple"], "Vuelos finalizados"),
            ("total_pasajeros", "Pasajeros", "◉", COLORS["accent"], "Registrados en la aerolínea"),
            ("total_reservas", "Reservas", "▤", COLORS["success"], "Ventas registradas"),
            ("pendientes_abordar", "Pendientes de abordar", "⌛", COLORS["danger"], "Con reserva activa"),
            ("proxima", "Próxima salida", "➜", COLORS["warning"], "Sin salidas próximas"),
        ]
        for indice, (clave, titulo, icono, color, detalle) in enumerate(definiciones):
            card = StatCard(contenedor_cards, titulo, "0", icono, color, detalle)
            card.grid(row=indice // 4, column=indice % 4, sticky="nsew", padx=5, pady=5)
            self.cards[clave] = card
        for columna in range(4):
            contenedor_cards.grid_columnconfigure(columna, weight=1, uniform="card")

        cuerpo = tk.Frame(self, bg=COLORS["bg"])
        cuerpo.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=2)
        cuerpo.grid_rowconfigure(0, weight=1)

        # Tabla de próximas salidas --------------------------------------
        card_salidas = Card(cuerpo, padding=15)
        card_salidas.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        encabezado_tabla = tk.Frame(card_salidas.cuerpo, bg=COLORS["card"])
        encabezado_tabla.pack(fill="x", pady=(0, 10))
        etiqueta(encabezado_tabla, "Próximas salidas", size=13, bold=True).pack(side="left")
        self.lbl_salidas = etiqueta(encabezado_tabla, "", size=9, color=COLORS["muted"])
        self.lbl_salidas.pack(side="right")
        self.tabla_salidas = Tabla(card_salidas.cuerpo, [
            ("codigo", "VUELO", 75, "center", False),
            ("ruta", "RUTA", 105, "center", False),
            ("salida", "SALIDA", 120, "center", False),
            ("puerta", "PUERTA", 70, "center", False),
            ("ocupacion", "OCUPACIÓN", 110, "center", False),
            ("estado", "ESTADO", 120, "center", True),
        ], altura=7)
        self.tabla_salidas.pack(fill="both", expand=True)
        boton(card_salidas.cuerpo, "Ver todos los vuelos",
              lambda: self.app.abrir_vista("vuelos"), tipo="ghost", compacto=True,
              icono="→").pack(anchor="e", pady=(10, 0))

        # Gráficos --------------------------------------------------------
        card_graficos = Card(cuerpo, padding=12)
        card_graficos.grid(row=0, column=1, sticky="nsew")
        etiqueta(card_graficos.cuerpo, "Analítica operativa", size=13,
                 bold=True).pack(anchor="w", padx=4)
        etiqueta(card_graficos.cuerpo, "Distribución de vuelos y ocupación",
                 size=8, color=COLORS["muted"]).pack(anchor="w", padx=4, pady=(1, 6))
        separador(card_graficos.cuerpo).pack(fill="x", padx=4, pady=(0, 4))
        if MATPLOTLIB_DISPONIBLE:
            self.figura = Figure(figsize=(4.1, 5.0), dpi=100)
            self.figura.patch.set_facecolor(COLORS["card"])
            self.lienzo = FigureCanvasTkAgg(self.figura, master=card_graficos.cuerpo)
            widget = self.lienzo.get_tk_widget()
            widget.configure(bg=COLORS["card"], highlightthickness=0)
            widget.pack(fill="both", expand=True)
        else:  # pragma: no cover
            etiqueta(
                card_graficos.cuerpo,
                "Matplotlib no está instalado.\nEjecuta: pip install -r requirements.txt",
                size=10, color=COLORS["warning"], anchor="center", justify="center",
            ).pack(fill="both", expand=True)
            self.figura = None

    def refrescar(self) -> None:
        metricas = self.app.dashboard.metricas()
        self.cards["total_vuelos"].actualizar(metricas["total_vuelos"],
                                              f"{metricas['en_vuelo']} en vuelo")
        self.cards["programados"].actualizar(metricas["programados"],
                                             f"{metricas['checkin']} con check-in abierto")
        self.cards["abordaje"].actualizar(metricas["abordaje"],
                                          f"{metricas['checkins']} check-in registrados")
        self.cards["completados"].actualizar(metricas["completados"],
                                             f"{metricas['cancelados']} cancelados")
        self.cards["total_pasajeros"].actualizar(metricas["total_pasajeros"],
                                                 "Base de datos de pasajeros")
        self.cards["total_reservas"].actualizar(metricas["total_reservas"],
                                                f"{metricas['reservas_confirmadas']} confirmadas")
        self.cards["pendientes_abordar"].actualizar(metricas["pendientes_abordar"],
                                                    "Reservas activas sin abordar")
        proxima = metricas["proxima"]
        if proxima:
            self.cards["proxima"].actualizar(
                fecha_corta(proxima.fecha_salida),
                f"{proxima.codigo} · {proxima.ruta} · {proxima.puerta}",
            )
        else:
            self.cards["proxima"].actualizar("—", "Sin salidas próximas")

        salidas = self.app.dashboard.proximas_salidas(8)
        filas = []
        for vuelo in salidas:
            filas.append({
                "_iid": str(vuelo.id),
                "codigo": vuelo.codigo,
                "ruta": vuelo.ruta,
                "salida": fecha_humana(vuelo.fecha_salida),
                "puerta": vuelo.puerta,
                "ocupacion": f"{vuelo.ocupados}/{vuelo.capacidad} · {round(vuelo.ocupados / vuelo.capacidad * 100)}%",
                "estado": vuelo.estado,
            })
        self.tabla_salidas.set_filas(filas)
        self.lbl_salidas.configure(text=f"{len(salidas)} salidas próximas")

        if self.figura is not None:
            self._dibujar_graficos(
                self.app.dashboard.estados_vuelos(),
                self.app.dashboard.ocupacion_vuelos(6),
                self.app.dashboard.reservas_por_estado(),
            )

    def _dibujar_graficos(self, estados: dict, ocupacion: list[dict],
                          reservas: dict) -> None:
        self.figura.clear()
        self.figura.patch.set_facecolor(COLORS["card"])
        ax1 = self.figura.add_subplot(211)
        ax2 = self.figura.add_subplot(212)

        # Donut de estados.
        etiquetas = []
        valores = []
        colores = []
        mapa_colores = {
            "Programado": COLORS["accent"],
            "Check-in abierto": COLORS["purple"],
            "Abordaje": COLORS["warning"],
            "En vuelo": COLORS["success"],
            "Completado": "#7DD3FC",
            "Cancelado": COLORS["danger"],
        }
        for estado in ESTADOS_VUELO:
            cantidad = estados.get(estado, 0)
            if cantidad:
                etiquetas.append(estado)
                valores.append(cantidad)
                colores.append(mapa_colores[estado])
        ax1.set_facecolor(COLORS["card"])
        if valores:
            wedges, _ = ax1.pie(
                valores, colors=colores, startangle=90,
                wedgeprops={"width": 0.38, "edgecolor": COLORS["card"], "linewidth": 2},
            )
            total = sum(valores)
            ax1.text(0, 0.08, str(total), ha="center", va="center",
                     color=COLORS["text"], fontsize=20, fontweight="bold")
            ax1.text(0, -0.16, "vuelos", ha="center", va="center",
                     color=COLORS["muted"], fontsize=8)
            ax1.legend(
                wedges, [f"{e} ({v})" for e, v in zip(etiquetas, valores)],
                loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False,
                labelcolor=COLORS["text_soft"], fontsize=7,
            )
        else:
            ax1.text(0.5, 0.5, "Sin vuelos", ha="center", va="center",
                     color=COLORS["muted"], fontsize=10)
        ax1.set_title("Distribución por estado", color=COLORS["text"],
                      fontsize=9, fontweight="bold", loc="left", pad=6)
        ax1.set_aspect("equal")

        # Barras de ocupación.
        ax2.set_facecolor(COLORS["card"])
        if ocupacion:
            codigos = [d["codigo"] for d in ocupacion][::-1]
            porcentajes = [d["porcentaje"] for d in ocupacion][::-1]
            colores_barra = [COLORS["accent"] if p < 70 else COLORS["warning"]
                             if p < 95 else COLORS["danger"] for p in porcentajes]
            barras = ax2.barh(codigos, porcentajes, color=colores_barra, height=0.55)
            for barra, item in zip(barras, list(reversed(ocupacion))):
                ax2.text(
                    min(96, barra.get_width() + 2), barra.get_y() + barra.get_height() / 2,
                    f"{item['porcentaje']:.0f}%",
                    va="center", color=COLORS["text_soft"], fontsize=7,
                )
            ax2.set_xlim(0, 100)
            ax2.set_xlabel("Ocupación (%)", color=COLORS["muted"], fontsize=7)
            ax2.tick_params(axis="x", colors=COLORS["muted"], labelsize=7)
            ax2.tick_params(axis="y", colors=COLORS["text_soft"], labelsize=7)
            ax2.grid(axis="x", color=COLORS["border"], alpha=0.35, linewidth=0.6)
            for borde in ax2.spines.values():
                borde.set_color(COLORS["border"])
        else:
            ax2.text(0.5, 0.5, "Sin vuelos activos", ha="center", va="center",
                     color=COLORS["muted"], fontsize=9, transform=ax2.transAxes)
            ax2.set_xticks([])
            ax2.set_yticks([])
        ax2.set_title("Ocupación de próximos vuelos", color=COLORS["text"],
                      fontsize=9, fontweight="bold", loc="left", pad=6)

        self.figura.tight_layout(pad=1.3)
        self.lienzo.draw_idle()
