"""Ventana principal y navegación del sistema aeroportuario."""
from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

from config import APP_TITLE, APP_VERSION, COLORS, DB_PATH, FONTS
from database import Database
from modules.abordaje import Abordaje
from modules.actividad import Historial
from modules.checkin import Checkin
from modules.dashboard import Dashboard
from modules.gestion_pasajeros import GestionPasajeros
from modules.gestion_vuelos import GestionVuelos
from modules.reservas import Reservas
from modules.rutas import Rutas
from seed import cargar_datos_prueba
from views.actividad_view import ActividadView
from views.abordaje_view import AbordajeView
from views.checkin_view import CheckinView
from views.dashboard import DashboardView
from views.pasajeros_view import PasajerosView
from views.reservas_view import ReservasView
from views.rutas_view import RutasView
from views.theme import configurar_tema
from views.vuelos_view import VuelosView


TITULOS = {
    "dashboard": ("Panel principal", "Resumen operativo del aeropuerto"),
    "vuelos": ("Gestión de vuelos", "Programación y estados operativos"),
    "pasajeros": ("Gestión de pasajeros", "Directorio e historial"),
    "reservas": ("Reservas", "Venta de boletos y asientos"),
    "checkin": ("Check-in", "Equipaje y tarjetas de embarque"),
    "abordaje": ("Abordaje", "Cola FIFO y embarque"),
    "rutas": ("Rutas y destinos", "Grafo de conexiones aéreas"),
    "actividad": ("Actividad", "Bitácora y pila de deshacer"),
}

NAVEGACION = [
    ("dashboard", "◫", "Panel principal"),
    ("vuelos", "✈", "Vuelos"),
    ("pasajeros", "◉", "Pasajeros"),
    ("reservas", "▤", "Reservas"),
    ("checkin", "✓", "Check-in"),
    ("abordaje", "⇥", "Abordaje"),
    ("rutas", "◈", "Rutas y destinos"),
    ("actividad", "↶", "Actividad"),
]


class AplicacionAeropuerto:
    def __init__(self, ruta_db: str | Path | None = None) -> None:
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.minsize(1160, 760)
        self._configurar_ventana()
        configurar_tema(self.root)

        self.db = Database(ruta_db or DB_PATH)
        self.datos_sembrados = cargar_datos_prueba(self.db)
        self.historial = Historial(self.db)
        self.vuelos = GestionVuelos(self.db, self.historial)
        self.pasajeros = GestionPasajeros(self.db, self.historial)
        self.reservas = Reservas(self.db, self.historial, self.vuelos, self.pasajeros)
        self.checkin = Checkin(self.db, self.historial, self.reservas, self.vuelos)
        self.abordaje = Abordaje(self.db, self.checkin, self.reservas, self.vuelos)
        self.rutas = Rutas(self.db, self.historial)
        self.dashboard = Dashboard(self.db, self.vuelos)

        self._vistas: dict[str, tk.Frame] = {}
        self._vista_actual: tk.Frame | None = None
        self._vista_actual_clave: str | None = None
        self._nav_items: dict[str, tuple[tk.Frame, tk.Frame, tk.Button]] = {}
        self._estado_after = None
        self._construir_shell()
        self.abrir_vista("dashboard")
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.root.bind("<F5>", lambda _e: self.refrescar_vista_actual())
        self._actualizar_reloj()
        if self.datos_sembrados:
            self.estado("Datos de demostración cargados correctamente.")

    # ------------------------------------------------------------------
    def _configurar_ventana(self) -> None:
        pantalla_w = self.root.winfo_screenwidth()
        pantalla_h = self.root.winfo_screenheight()
        ancho = min(1480, max(1160, pantalla_w - 120))
        alto = min(940, max(760, pantalla_h - 100))
        x = max(0, (pantalla_w - ancho) // 2)
        y = max(0, (pantalla_h - alto) // 2)
        self.root.geometry(f"{ancho}x{alto}+{x}+{y}")

    # ------------------------------------------------------------------
    def _construir_shell(self) -> None:
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        sidebar = tk.Frame(self.root, bg=COLORS["sidebar"], width=238)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.pack_propagate(False)
        self.root.grid_columnconfigure(0, weight=0, minsize=238)

        principal = tk.Frame(self.root, bg=COLORS["bg"])
        principal.grid(row=0, column=1, sticky="nsew")
        self.root.grid_columnconfigure(1, weight=1)
        principal.grid_rowconfigure(1, weight=1)
        principal.grid_columnconfigure(0, weight=1)

        self._construir_sidebar(sidebar)
        self._construir_topbar(principal)
        self.contenedor = tk.Frame(principal, bg=COLORS["bg"])
        self.contenedor.grid(row=1, column=0, sticky="nsew")
        self._construir_statusbar(principal)

    def _construir_sidebar(self, sidebar: tk.Frame) -> None:
        marca = tk.Frame(sidebar, bg=COLORS["sidebar"])
        marca.pack(fill="x", padx=18, pady=(22, 18))
        icono = tk.Label(
            marca, text="✈", bg=COLORS["accent"], fg=COLORS["sidebar"],
            font=(FONTS["family"], 19, "bold"), width=2, height=1,
        )
        icono.pack(side="left")
        textos = tk.Frame(marca, bg=COLORS["sidebar"])
        textos.pack(side="left", padx=(11, 0))
        tk.Label(
            textos, text="AeroAndes", bg=COLORS["sidebar"], fg=COLORS["text"],
            font=(FONTS["family"], 15, "bold"), anchor="w",
        ).pack(anchor="w")
        tk.Label(
            textos, text="AIRPORT OPERATIONS", bg=COLORS["sidebar"],
            fg=COLORS["muted"], font=(FONTS["family"], 7, "bold"), anchor="w",
        ).pack(anchor="w")

        tk.Frame(sidebar, bg=COLORS["border"], height=1).pack(fill="x", padx=14)
        tk.Label(
            sidebar, text="OPERACIONES", bg=COLORS["sidebar"], fg=COLORS["muted"],
            font=(FONTS["family"], 7, "bold"), anchor="w",
        ).pack(fill="x", padx=22, pady=(16, 5))

        for clave, icono_txt, texto in NAVEGACION:
            if clave == "actividad":
                tk.Frame(sidebar, bg=COLORS["border"], height=1).pack(
                    fill="x", padx=14, pady=(10, 4)
                )
                tk.Label(
                    sidebar, text="SISTEMA", bg=COLORS["sidebar"],
                    fg=COLORS["muted"], font=(FONTS["family"], 7, "bold"),
                    anchor="w",
                ).pack(fill="x", padx=22, pady=(6, 4))
            self._crear_nav_item(sidebar, clave, icono_txt, texto)

        pie = tk.Frame(sidebar, bg=COLORS["sidebar"])
        pie.pack(side="bottom", fill="x", padx=16, pady=16)
        estado_db = tk.Frame(pie, bg=COLORS["card_alt"], padx=11, pady=9)
        estado_db.pack(fill="x")
        tk.Label(estado_db, text="●", bg=COLORS["card_alt"], fg=COLORS["success"],
                 font=(FONTS["family"], 10)).pack(side="left")
        tk.Label(estado_db, text=" SQLite conectada", bg=COLORS["card_alt"],
                 fg=COLORS["text_soft"], font=(FONTS["family"], 8, "bold")).pack(side="left")
        tk.Label(estado_db, text="aeropuerto.db", bg=COLORS["card_alt"],
                 fg=COLORS["muted"], font=(FONTS["family"], 7)).pack(side="right")
        tk.Label(
            pie, text=f"Versión {APP_VERSION} · Proyecto académico",
            bg=COLORS["sidebar"], fg=COLORS["muted"], font=(FONTS["family"], 7),
        ).pack(anchor="w", pady=(9, 0))

    def _crear_nav_item(self, sidebar: tk.Frame, clave: str, icono: str,
                        texto: str) -> None:
        contenedor = tk.Frame(sidebar, bg=COLORS["sidebar"])
        contenedor.pack(fill="x", padx=12, pady=1)
        indicador = tk.Frame(contenedor, bg=COLORS["sidebar"], width=3)
        indicador.pack(side="left", fill="y")
        boton_nav = tk.Button(
            contenedor, text=f"  {icono}    {texto}", anchor="w",
            bg=COLORS["sidebar"], fg=COLORS["text_soft"],
            activebackground=COLORS["sidebar_hover"], activeforeground=COLORS["text"],
            font=(FONTS["family"], 10, "bold"), relief="flat", bd=0,
            cursor="hand2", padx=12, pady=8,
        )
        boton_nav.pack(side="left", fill="x", expand=True)
        boton_nav.configure(command=lambda k=clave: self.abrir_vista(k))
        boton_nav.bind("<Enter>", lambda _e, k=clave: self._hover_nav(k, True))
        boton_nav.bind("<Leave>", lambda _e, k=clave: self._hover_nav(k, False))
        self._nav_items[clave] = (contenedor, indicador, boton_nav)

    def _hover_nav(self, clave: str, dentro: bool) -> None:
        if clave == self._vista_actual_clave:
            return
        _, _, boton_nav = self._nav_items[clave]
        boton_nav.configure(bg=COLORS["sidebar_hover"] if dentro else COLORS["sidebar"])

    def _construir_topbar(self, principal: tk.Frame) -> None:
        topbar = tk.Frame(principal, bg=COLORS["bg_soft"], height=68)
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)
        topbar.grid_columnconfigure(0, weight=1)

        izq = tk.Frame(topbar, bg=COLORS["bg_soft"])
        izq.grid(row=0, column=0, sticky="w", padx=24, pady=12)
        self.lbl_top_titulo = tk.Label(
            izq, text="Centro de operaciones", bg=COLORS["bg_soft"],
            fg=COLORS["text"], font=(FONTS["family"], 13, "bold"), anchor="w",
        )
        self.lbl_top_titulo.pack(anchor="w")
        tk.Label(
            izq, text="Sistema Integral de Gestión de Vuelos, Reservas y Abordaje",
            bg=COLORS["bg_soft"], fg=COLORS["muted"],
            font=(FONTS["family"], 8), anchor="w",
        ).pack(anchor="w")

        der = tk.Frame(topbar, bg=COLORS["bg_soft"])
        der.grid(row=0, column=1, sticky="e", padx=24)
        tk.Label(
            der, text="MODO DEMO", bg=COLORS["accent_soft"], fg=COLORS["accent"],
            font=(FONTS["family"], 7, "bold"), padx=9, pady=4,
        ).pack(side="left", padx=(0, 14))
        reloj = tk.Frame(der, bg=COLORS["bg_soft"])
        reloj.pack(side="left")
        self.lbl_reloj = tk.Label(
            reloj, text="", bg=COLORS["bg_soft"], fg=COLORS["text"],
            font=(FONTS["family"], 10, "bold"), anchor="e",
        )
        self.lbl_reloj.pack(anchor="e")
        self.lbl_fecha = tk.Label(
            reloj, text="", bg=COLORS["bg_soft"], fg=COLORS["muted"],
            font=(FONTS["family"], 7), anchor="e",
        )
        self.lbl_fecha.pack(anchor="e")

    def _construir_statusbar(self, principal: tk.Frame) -> None:
        barra = tk.Frame(principal, bg=COLORS["sidebar"], height=29)
        barra.grid(row=2, column=0, sticky="ew")
        barra.grid_propagate(False)
        self.lbl_estado = tk.Label(
            barra, text="Listo.", bg=COLORS["sidebar"], fg=COLORS["text_soft"],
            font=(FONTS["family"], 8), anchor="w",
        )
        self.lbl_estado.pack(side="left", padx=18)
        tk.Label(
            barra, text="SQLite · Datos persistentes · F5 para actualizar",
            bg=COLORS["sidebar"], fg=COLORS["muted"],
            font=(FONTS["family"], 8),
        ).pack(side="right", padx=18)

    # ------------------------------------------------------------------
    def _crear_vista(self, clave: str) -> tk.Frame:
        clases = {
            "dashboard": DashboardView,
            "vuelos": VuelosView,
            "pasajeros": PasajerosView,
            "reservas": ReservasView,
            "checkin": CheckinView,
            "abordaje": AbordajeView,
            "rutas": RutasView,
            "actividad": ActividadView,
        }
        if clave not in clases:
            raise ValueError(f"Vista desconocida: {clave}")
        vista = clases[clave](self.contenedor, self)
        self._vistas[clave] = vista
        return vista

    def abrir_vista(self, clave: str) -> None:
        if clave not in TITULOS:
            return
        if self._vista_actual is not None:
            self._vista_actual.pack_forget()
        vista = self._vistas.get(clave) or self._crear_vista(clave)
        vista.pack(fill="both", expand=True)
        self._vista_actual = vista
        self._vista_actual_clave = clave
        self._actualizar_navegacion()
        titulo, subtitulo = TITULOS[clave]
        self.lbl_top_titulo.configure(text=titulo)
        try:
            vista.refrescar()
        except Exception as exc:
            messagebox.showerror(
                "Error al actualizar la vista",
                f"No se pudo cargar {titulo}:\n{exc}", parent=self.root,
            )
        self.estado(f"{titulo} · {subtitulo}")

    def _actualizar_navegacion(self) -> None:
        for clave, (contenedor, indicador, boton_nav) in self._nav_items.items():
            activo = clave == self._vista_actual_clave
            bg = COLORS["sidebar_hover"] if activo else COLORS["sidebar"]
            fg = COLORS["accent"] if activo else COLORS["text_soft"]
            contenedor.configure(bg=bg)
            boton_nav.configure(bg=bg, fg=fg)
            indicador.configure(bg=COLORS["accent"] if activo else bg)

    def refrescar_vista_actual(self) -> None:
        if self._vista_actual is not None:
            try:
                self._vista_actual.refrescar()
                self.estado("Vista actualizada.")
            except Exception as exc:
                messagebox.showerror(
                    "Error al actualizar", str(exc), parent=self.root,
                )

    def estado(self, mensaje: str, error: bool = False) -> None:
        self.lbl_estado.configure(
            text=mensaje, fg=COLORS["danger"] if error else COLORS["success"]
        )
        if self._estado_after:
            try:
                self.root.after_cancel(self._estado_after)
            except Exception:
                pass
        self._estado_after = self.root.after(9000, self._estado_base)

    def _estado_base(self) -> None:
        self.lbl_estado.configure(text="Listo.", fg=COLORS["text_soft"])
        self._estado_after = None

    def _actualizar_reloj(self) -> None:
        ahora = datetime.now()
        dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                 "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        self.lbl_reloj.configure(text=ahora.strftime("%H:%M:%S"))
        self.lbl_fecha.configure(
            text=f"{dias[ahora.weekday()].capitalize()} {ahora.day} de "
                 f"{meses[ahora.month - 1]} de {ahora.year}"
        )
        self.root.after(1000, self._actualizar_reloj)

    def cerrar(self) -> None:
        self.db.cerrar()
        self.root.destroy()

    def ejecutar(self) -> None:
        self.root.mainloop()
