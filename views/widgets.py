"""Componentes visuales reutilizables de la interfaz."""
from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Iterable

from config import COLORS, FONTS

# ---------------------------------------------------------------------------
# Helpers de creación
# ---------------------------------------------------------------------------


def etiqueta(parent, texto: str = "", size: int = 10, bold: bool = False,
             color: str | None = None, bg: str | None = None,
             anchor: str = "w", justify: str = "left", **kwargs) -> tk.Label:
    fuente = (FONTS["family"], size, "bold" if bold else "normal")
    return tk.Label(
        parent, text=texto, font=fuente,
        fg=color or COLORS["text"], bg=bg or parent.cget("bg"),
        anchor=anchor, justify=justify, **kwargs,
    )


def boton(parent, texto: str, comando: Callable, tipo: str = "primary",
          ancho: int | None = None, compacto: bool = False,
          icono: str = "", **kwargs) -> tk.Button:
    estilos = {
        "primary": (COLORS["accent"], COLORS["bg"], COLORS["accent_dark"], COLORS["bg"]),
        "success": (COLORS["success"], COLORS["bg"], "#22C7B4", COLORS["bg"]),
        "danger": (COLORS["danger"], COLORS["bg"], "#F05670", COLORS["bg"]),
        "warning": (COLORS["warning"], COLORS["bg"], "#E6AC18", COLORS["bg"]),
        "secondary": (COLORS["card_alt"], COLORS["text"], COLORS["card_light"], COLORS["text"]),
        "ghost": (COLORS["card"], COLORS["text_soft"], COLORS["card_alt"], COLORS["text"]),
        "purple": (COLORS["purple"], COLORS["bg"], "#9676F2", COLORS["bg"]),
    }
    bg, fg, activo_bg, activo_fg = estilos.get(tipo, estilos["secondary"])
    texto_boton = f"{icono}  {texto}".strip() if icono else texto
    opciones = dict(
        text=texto_boton, command=comando, bg=bg, fg=fg,
        activebackground=activo_bg, activeforeground=activo_fg,
        font=FONTS["body_bold"] if not compacto else FONTS["small"],
        relief="flat", bd=0, cursor="hand2",
        padx=12 if compacto else 16, pady=5 if compacto else 8,
        highlightthickness=1 if tipo in ("secondary", "ghost") else 0,
        highlightbackground=COLORS["border"], highlightcolor=COLORS["border"],
        disabledforeground=COLORS["muted"],
    )
    if ancho:
        opciones["width"] = ancho
    opciones.update(kwargs)
    return tk.Button(parent, **opciones)


def campo(parent, textvariable=None, ancho: int | None = None, show: str | None = None,
          estado: str = "normal") -> ttk.Entry:
    kwargs = {
        "textvariable": textvariable, "state": estado,
        "font": FONTS["body"],
    }
    if ancho:
        kwargs["width"] = ancho
    if show:
        kwargs["show"] = show
    return ttk.Entry(parent, **kwargs)


def combo(parent, values: Iterable[str], textvariable=None, ancho: int | None = None,
          estado: str = "readonly") -> ttk.Combobox:
    kwargs = {
        "values": list(values), "textvariable": textvariable,
        "state": estado, "font": FONTS["body"],
    }
    if ancho:
        kwargs["width"] = ancho
    return ttk.Combobox(parent, **kwargs)


def texto(parent, contenido: str = "", alto: int = 10, ancho: int = 60) -> tk.Text:
    return tk.Text(
        parent, height=alto, width=ancho, bg=COLORS["bg_soft"], fg=COLORS["text"],
        insertbackground=COLORS["accent"], selectbackground=COLORS["accent_soft"],
        relief="flat", bd=0, padx=14, pady=12, wrap="word",
        font=FONTS["mono"], highlightthickness=1,
        highlightbackground=COLORS["border"], highlightcolor=COLORS["accent"],
    )


def separador(parent, color: str | None = None) -> tk.Frame:
    return tk.Frame(parent, bg=color or COLORS["border"], height=1)


def badge(parent, texto: str, color: str, fondo: str | None = None) -> tk.Label:
    return tk.Label(
        parent, text=texto, bg=fondo or COLORS["card_alt"], fg=color,
        font=(FONTS["family"], 8, "bold"), padx=8, pady=3,
    )


def chip_estado(parent, estado: str) -> tk.Label:
    color = {
        "Programado": COLORS["accent"],
        "Check-in abierto": COLORS["purple"],
        "Abordaje": COLORS["warning"],
        "En vuelo": COLORS["success"],
        "Completado": COLORS["muted"],
        "Cancelado": COLORS["danger"],
        "Pendiente": COLORS["warning"],
        "Confirmada": COLORS["success"],
        "Cancelada": COLORS["danger"],
        "Abordado": COLORS["success"],
        "En cola": COLORS["warning"],
        "Check-in": COLORS["accent"],
    }.get(estado, COLORS["muted"])
    fondo = {
        "Programado": COLORS["accent_soft"],
        "Check-in abierto": COLORS["purple_soft"],
        "Abordaje": COLORS["warning_soft"],
        "En vuelo": COLORS["success_soft"],
        "Completado": COLORS["card_alt"],
        "Cancelado": COLORS["danger_soft"],
        "Pendiente": COLORS["warning_soft"],
        "Confirmada": COLORS["success_soft"],
        "Cancelada": COLORS["danger_soft"],
        "Abordado": COLORS["success_soft"],
        "En cola": COLORS["warning_soft"],
        "Check-in": COLORS["accent_soft"],
    }.get(estado, COLORS["card_alt"])
    return badge(parent, estado, color, fondo)


# ---------------------------------------------------------------------------
# Contenedores
# ---------------------------------------------------------------------------
class Card(tk.Frame):
    def __init__(self, parent, padding: int = 16, bg: str | None = None,
                 borde: str | None = None, **kwargs):
        super().__init__(
            parent, bg=bg or COLORS["card"], bd=0,
            highlightthickness=1,
            highlightbackground=borde or COLORS["border"],
            highlightcolor=borde or COLORS["border"], **kwargs,
        )
        self.cuerpo = tk.Frame(self, bg=bg or COLORS["card"], padx=padding, pady=padding)
        self.cuerpo.pack(fill="both", expand=True)
        self._padding = padding


class PageHeader(tk.Frame):
    def __init__(self, parent, titulo: str, subtitulo: str = ""):
        super().__init__(parent, bg=COLORS["bg"])
        izquierda = tk.Frame(self, bg=COLORS["bg"])
        izquierda.pack(side="left", fill="x", expand=True)
        etiqueta(izquierda, titulo, size=21, bold=True).pack(anchor="w")
        if subtitulo:
            etiqueta(izquierda, subtitulo, size=10, color=COLORS["muted"]).pack(
                anchor="w", pady=(2, 0)
            )
        self.acciones = tk.Frame(self, bg=COLORS["bg"])
        self.acciones.pack(side="right", anchor="e")


class StatCard(Card):
    def __init__(self, parent, titulo: str, valor: str = "0", icono: str = "✈",
                 color: str | None = None, detalle: str = ""):
        super().__init__(parent, padding=13)
        self.color = color or COLORS["accent"]
        cabecera = tk.Frame(self.cuerpo, bg=COLORS["card"])
        cabecera.pack(fill="x")
        self.icono = tk.Label(
            cabecera, text=icono, bg=COLORS["card_alt"], fg=self.color,
            font=(FONTS["family"], 12, "bold"), width=3, pady=3,
        )
        self.icono.pack(side="left")
        etiqueta(cabecera, titulo.upper(), size=8, bold=True,
                 color=COLORS["muted"]).pack(side="left", padx=(8, 0))
        self.valor = etiqueta(self.cuerpo, valor, size=23, bold=True, color=COLORS["text"])
        self.valor.pack(anchor="w", pady=(8, 0))
        self.detalle = etiqueta(self.cuerpo, detalle, size=8, color=COLORS["muted"])
        self.detalle.pack(anchor="w")

    def actualizar(self, valor: str | int, detalle: str | None = None) -> None:
        self.valor.configure(text=str(valor))
        if detalle is not None:
            self.detalle.configure(text=detalle)


class Tabla(tk.Frame):
    """Tabla Treeview con selección y datos asociados a cada fila."""

    TAGS = {
        "success": COLORS["success"],
        "warning": COLORS["warning"],
        "danger": COLORS["danger"],
        "accent": COLORS["accent"],
        "purple": COLORS["purple"],
        "muted": COLORS["muted"],
        "normal": COLORS["text"],
    }

    MAPA_ESTADOS = {
        "Programado": "accent",
        "Check-in abierto": "purple",
        "Abordaje": "warning",
        "En vuelo": "success",
        "Completado": "muted",
        "Cancelado": "danger",
        "Pendiente": "warning",
        "Confirmada": "success",
        "Cancelada": "danger",
        "Disponible": "success",
        "Reservado": "warning",
        "Ocupado": "danger",
        "Abordado": "success",
        "En cola": "warning",
        "Check-in": "accent",
    }

    def __init__(self, parent, columnas: list[tuple], altura: int = 8,
                 on_doble_clic: Callable | None = None, on_seleccion: Callable | None = None):
        super().__init__(parent, bg=COLORS["card"])
        self.columnas = columnas
        self._datos: dict[str, dict] = {}
        claves = [col[0] for col in columnas]
        self.tree = ttk.Treeview(
            self, columns=claves, show="headings", height=altura,
            selectmode="browse",
        )
        for clave, titulo, ancho, alineacion, *resto in columnas:
            estirar = bool(resto[0]) if resto else False
            self.tree.heading(clave, text=titulo, anchor=alineacion)
            self.tree.column(clave, width=ancho, anchor=alineacion,
                             stretch=estirar, minwidth=max(50, int(ancho * 0.55)))
        for nombre, color in self.TAGS.items():
            self.tree.tag_configure(nombre, foreground=color)
        self.tree.tag_configure("even", background=COLORS["card"])
        self.tree.tag_configure("odd", background=COLORS["card_alt"])

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        if on_doble_clic:
            self.tree.bind("<Double-1>", lambda _e: on_doble_clic())
        if on_seleccion:
            self.tree.bind("<<TreeviewSelect>>", lambda _e: on_seleccion())

    def set_filas(self, filas: list[dict], usar_estado: bool = True) -> None:
        seleccion = self.seleccionado_id()
        self.tree.delete(*self.tree.get_children())
        self._datos.clear()
        for indice, fila in enumerate(filas):
            iid = str(fila.get("_iid", indice + 1))
            valores = [fila.get(clave, "") for clave, *_ in self.columnas]
            tag = fila.get("_tag")
            if not tag and usar_estado:
                estado = str(fila.get("estado", ""))
                tag = self.MAPA_ESTADOS.get(estado)
            if not tag:
                tag = "even" if indice % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=iid, values=valores, tags=(tag,))
            self._datos[iid] = fila
        if seleccion in self._datos:
            self.tree.selection_set(seleccion)

    def seleccionado_id(self) -> str | None:
        seleccion = self.tree.selection()
        return seleccion[0] if seleccion else None

    def seleccionado(self) -> dict | None:
        iid = self.seleccionado_id()
        return self._datos.get(iid) if iid else None

    def seleccionar_primero(self) -> None:
        hijos = self.tree.get_children()
        if hijos:
            self.tree.selection_set(hijos[0])
            self.tree.focus(hijos[0])

    def limpiar(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self._datos.clear()

    def contar(self) -> int:
        return len(self._datos)


class ScrollableFrame(tk.Frame):
    """Contenedor con desplazamiento vertical para formularios largos."""

    def __init__(self, parent, bg: str | None = None):
        super().__init__(parent, bg=bg or COLORS["bg"])
        self.canvas = tk.Canvas(self, bg=bg or COLORS["bg"], highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.contenido = tk.Frame(self.canvas, bg=bg or COLORS["bg"])
        self._ventana = self.canvas.create_window((0, 0), window=self.contenido, anchor="nw")
        self.contenido.bind(
            "<Configure>",
            lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self._ventana, width=e.width),
        )
        self.canvas.bind("<Enter>", self._activar_rueda)
        self.canvas.bind("<Leave>", self._desactivar_rueda)

    def _activar_rueda(self, _evento=None) -> None:
        self.canvas.bind_all("<MouseWheel>", self._rueda)

    def _desactivar_rueda(self, _evento=None) -> None:
        self.canvas.unbind_all("<MouseWheel>")

    def _rueda(self, evento) -> None:
        self.canvas.yview_scroll(int(-evento.delta / 120), "units")


# ---------------------------------------------------------------------------
# Ventanas modales
# ---------------------------------------------------------------------------
class Modal(tk.Toplevel):
    def __init__(self, parent, titulo: str, ancho: int = 520, alto: int = 620,
                 redimensionable: bool = False):
        super().__init__(parent)
        self.withdraw()
        self.title(titulo)
        self.configure(bg=COLORS["bg"])
        self.transient(parent.winfo_toplevel())
        self.resizable(redimensionable, redimensionable)
        self.protocol("WM_DELETE_WINDOW", self.cerrar)
        self.bind("<Escape>", lambda _e: self.cerrar())

        cabecera = tk.Frame(self, bg=COLORS["sidebar"], height=58)
        cabecera.pack(fill="x")
        cabecera.pack_propagate(False)
        etiqueta(cabecera, titulo, size=14, bold=True, bg=COLORS["sidebar"]).pack(
            side="left", padx=18, pady=14
        )
        cerrar = tk.Label(
            cabecera, text="✕", bg=COLORS["sidebar"], fg=COLORS["muted"],
            font=(FONTS["family"], 13), cursor="hand2", padx=16,
        )
        cerrar.pack(side="right", fill="y")
        cerrar.bind("<Button-1>", lambda _e: self.cerrar())
        self.cuerpo = tk.Frame(self, bg=COLORS["bg"], padx=22, pady=18)
        self.cuerpo.pack(fill="both", expand=True)
        self.pie = tk.Frame(self, bg=COLORS["sidebar"], padx=18, pady=12)
        self.pie.pack(fill="x", side="bottom")

        self.update_idletasks()
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()
        x = max(10, (ancho_pantalla - ancho) // 2)
        y = max(10, (alto_pantalla - alto) // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.deiconify()
        self.lift()
        try:
            self.grab_set()
        except tk.TclError:
            pass

    def cerrar(self) -> None:
        try:
            self.grab_release()
        except tk.TclError:
            pass
        self.destroy()

    def esperar(self) -> None:
        self.wait_window()


class DocumentoModal(Modal):
    """Muestra un comprobante o tarjeta y permite guardar una copia."""

    def __init__(self, parent, titulo: str, contenido: str, ruta=None):
        super().__init__(parent, titulo, ancho=640, alto=690, redimensionable=True)
        self.contenido = contenido
        self.ruta = ruta
        caja = texto(self.cuerpo, alto=25, ancho=68)
        caja.pack(fill="both", expand=True)
        caja.insert("1.0", contenido)
        caja.configure(state="disabled")
        if ruta:
            etiqueta(self.cuerpo, f"Guardado en: {ruta}", size=8,
                     color=COLORS["muted"]).pack(anchor="w", pady=(8, 0))
        boton(self.pie, "Cerrar", self.cerrar, tipo="ghost",
              compacto=True).pack(side="right", padx=(8, 0))
        boton(self.pie, "Guardar copia...", self._guardar, tipo="secondary",
              compacto=True, icono="⇩").pack(side="right")

    def _guardar(self) -> None:
        from tkinter import filedialog
        from pathlib import Path
        nombre = Path(self.ruta).name if self.ruta else "documento.txt"
        destino = filedialog.asksaveasfilename(
            parent=self, defaultextension=".txt", initialfile=nombre,
            filetypes=[("Archivo de texto", "*.txt"), ("Todos", "*.*")],
        )
        if not destino:
            return
        try:
            Path(destino).write_text(self.contenido, encoding="utf-8")
            etiqueta(self.pie, "Copia guardada", size=8,
                     color=COLORS["success"], bg=COLORS["sidebar"]).pack(side="left")
        except OSError as exc:
            from tkinter import messagebox
            messagebox.showerror("No se pudo guardar", str(exc), parent=self)


# ---------------------------------------------------------------------------
# Mapa de asientos
# ---------------------------------------------------------------------------
class MapaAsientos(tk.Frame):
    """Representación visual de la cabina con selección de asientos."""

    def __init__(self, parent, on_seleccion: Callable[[str], None] | None = None):
        super().__init__(parent, bg=COLORS["card"])
        self.on_seleccion = on_seleccion
        self.mapa = None
        self.seleccionado: str | None = None
        self._items: dict[str, int] = {}
        self.canvas = tk.Canvas(
            self, bg=COLORS["bg_soft"], highlightthickness=0,
            height=320, width=360,
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.bind("<Configure>", self._al_redimensionar)
        self._after_id = None
        self._ultimo_ancho = 0
        self._dibujar_leyenda()

    def _dibujar_leyenda(self) -> None:
        leyenda = tk.Frame(self.canvas.master, bg=COLORS["card"])
        # La leyenda se dibuja en el canvas; este frame no se usa.

    def actualizar(self, mapa, seleccionado: str | None = None) -> None:
        self.mapa = mapa
        self.seleccionado = seleccionado
        self._renderizar()

    def set_seleccion(self, asiento: str | None) -> None:
        self.seleccionado = asiento
        self._renderizar()

    def _al_redimensionar(self, evento) -> None:
        if abs(evento.width - self._ultimo_ancho) < 8:
            return
        self._ultimo_ancho = evento.width
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(80, self._renderizar)

    def _renderizar(self) -> None:
        self.canvas.delete("all")
        self._items.clear()
        if self.mapa is None:
            self.canvas.create_text(
                180, 150, text="Selecciona un vuelo\npara ver los asientos",
                fill=COLORS["muted"], font=(FONTS["family"], 11), justify="center",
            )
            return
        columnas = self.mapa.columnas
        asientos = self.mapa.asientos
        filas = math.ceil(len(asientos) / max(1, columnas))
        ancho = max(330, self.canvas.winfo_width() or 360)
        sw, sh, gap = 34, 28, 5
        aisle = 20
        ancho_total = columnas * sw + (columnas - 1) * gap + aisle + 54
        inicio_x = max(24, (ancho - ancho_total) // 2) + 22
        inicio_y = 52
        alto_total = inicio_y + filas * (sh + gap) + 56

        self.canvas.create_text(
            ancho // 2, 16, text="CABINA · VISTA DE ASIENTOS",
            fill=COLORS["muted"], font=(FONTS["family"], 8, "bold"),
        )
        # Nariz estilizada del avión.
        cx = ancho // 2
        self.canvas.create_polygon(
            cx - 28, 25, cx + 28, 25, cx + 18, 38, cx - 18, 38,
            fill=COLORS["card_alt"], outline=COLORS["border"],
        )
        self.canvas.create_line(
            inicio_x - 24, inicio_y - 9, inicio_x + columnas * (sw + gap) + aisle - gap,
            inicio_y - 9, fill=COLORS["border"],
        )

        for indice, asiento in enumerate(asientos):
            fila = indice // columnas
            columna = indice % columnas
            x = inicio_x + columna * (sw + gap)
            if columna >= columnas // 2:
                x += aisle
            y = inicio_y + fila * (sh + gap)
            estado = self.mapa.estados.get(asiento, "Disponible")
            if asiento == self.seleccionado:
                relleno = COLORS["accent"]
                borde = COLORS["white"]
                color_texto = COLORS["bg"]
            else:
                relleno = {
                    "Disponible": COLORS["card_alt"],
                    "Reservado": COLORS["warning_soft"],
                    "Ocupado": COLORS["danger_soft"],
                }.get(estado, COLORS["card_alt"])
                borde = {
                    "Disponible": COLORS["border"],
                    "Reservado": COLORS["warning"],
                    "Ocupado": COLORS["danger"],
                }.get(estado, COLORS["border"])
                color_texto = {
                    "Disponible": COLORS["text_soft"],
                    "Reservado": COLORS["warning"],
                    "Ocupado": COLORS["danger"],
                }.get(estado, COLORS["text"])
            etiqueta_asiento = f"asiento_{asiento}"
            rect = self.canvas.create_rectangle(
                x, y, x + sw, y + sh, fill=relleno, outline=borde, width=1,
                tags=(etiqueta_asiento,),
            )
            self.canvas.create_text(
                x + sw / 2, y + sh / 2, text=asiento, fill=color_texto,
                font=(FONTS["family"], 7, "bold"), tags=(etiqueta_asiento,),
            )
            self._items[asiento] = rect
            if estado == "Disponible":
                self.canvas.tag_bind(
                    etiqueta_asiento, "<Button-1>",
                    lambda _e, s=asiento: self._seleccionar(s),
                )
                self.canvas.tag_bind(
                    etiqueta_asiento, "<Enter>",
                    lambda _e: self.canvas.configure(cursor="hand2"),
                )
                self.canvas.tag_bind(
                    etiqueta_asiento, "<Leave>",
                    lambda _e: self.canvas.configure(cursor=""),
                )
            if columna == 0:
                self.canvas.create_text(
                    inicio_x - 18, y + sh / 2, text=str(fila + 1),
                    fill=COLORS["muted"], font=(FONTS["family"], 8),
                )

        # Leyenda.
        leyenda_y = inicio_y + filas * (sh + gap) + 16
        elementos = [
            ("Disponible", COLORS["card_alt"], COLORS["border"]),
            ("Reservado", COLORS["warning_soft"], COLORS["warning"]),
            ("Ocupado", COLORS["danger_soft"], COLORS["danger"]),
        ]
        pos_x = max(18, ancho // 2 - 170)
        for texto_leyenda, relleno, borde in elementos:
            self.canvas.create_rectangle(
                pos_x, leyenda_y, pos_x + 12, leyenda_y + 11,
                fill=relleno, outline=borde,
            )
            self.canvas.create_text(
                pos_x + 18, leyenda_y + 6, text=texto_leyenda, anchor="w",
                fill=COLORS["muted"], font=(FONTS["family"], 8),
            )
            pos_x += 92

        self.canvas.configure(scrollregion=(0, 0, ancho, max(alto_total, 300)))
        if alto_total < 300:
            self.canvas.yview_moveto(0)

    def _seleccionar(self, asiento: str) -> None:
        self.seleccionado = asiento
        self._renderizar()
        if self.on_seleccion:
            self.on_seleccion(asiento)


class GrafoCanvas(tk.Frame):
    """Dibuja aeropuertos y rutas sobre un lienzo."""

    def __init__(self, parent, alto: int = 300):
        super().__init__(parent, bg=COLORS["card"])
        self.canvas = tk.Canvas(
            self, bg=COLORS["bg_soft"], highlightthickness=0, height=alto,
        )
        self.canvas.pack(fill="both", expand=True)
        self.grafo = None
        self._after = None
        self.canvas.bind("<Configure>", self._redimensionar)

    def dibujar(self, grafo) -> None:
        self.grafo = grafo
        self._renderizar()

    def _redimensionar(self, _evento) -> None:
        if self._after:
            self.after_cancel(self._after)
        self._after = self.after(100, self._renderizar)

    def _renderizar(self) -> None:
        self.canvas.delete("all")
        ancho = max(420, self.canvas.winfo_width() or 500)
        alto = max(250, self.canvas.winfo_height() or 300)
        if self.grafo is None or not self.grafo.vertices():
            self.canvas.create_text(
                ancho // 2, alto // 2, text="Sin aeropuertos registrados",
                fill=COLORS["muted"], font=(FONTS["family"], 10),
            )
            return

        vertices = self.grafo.vertices()
        datos = [self.grafo.obtener_vertice(v) or {} for v in vertices]
        coordenadas_validas = [
            (d.get("latitud", 0), d.get("longitud", 0)) for d in datos
        ]
        usar_mapa = any(abs(lat) > 0.01 or abs(lon) > 0.01
                        for lat, lon in coordenadas_validas) and len(vertices) >= 2

        posiciones: dict[str, tuple[float, float]] = {}
        margen_x, margen_y = 62, 52
        if usar_mapa:
            lats = [lat for lat, _ in coordenadas_validas]
            lons = [lon for _, lon in coordenadas_validas]
            rango_lat = max(0.01, max(lats) - min(lats))
            rango_lon = max(0.01, max(lons) - min(lons))
            for vertice, (lat, lon) in zip(vertices, coordenadas_validas):
                x = margen_x + (lon - min(lons)) / rango_lon * (ancho - 2 * margen_x)
                y = margen_y + (max(lats) - lat) / rango_lat * (alto - 2 * margen_y)
                posiciones[vertice] = (x, y)
            # Si dos aeropuertos quedan demasiado cerca (p. ej. Cusco y
            # Arequipa), se usa una distribuci?n circular legible.
            for i, codigo_a in enumerate(vertices):
                for codigo_b in vertices[i + 1:]:
                    xa, ya = posiciones[codigo_a]
                    xb, yb = posiciones[codigo_b]
                    if math.hypot(xa - xb, ya - yb) < 92:
                        usar_mapa = False
                        break
                if not usar_mapa:
                    break
        if not usar_mapa:
            centro_x, centro_y = ancho / 2, alto / 2 + 4
            radio_x = min(ancho * 0.36, 230)
            radio_y = min(alto * 0.33, 105)
            for indice, vertice in enumerate(vertices):
                angulo = -math.pi / 2 + 2 * math.pi * indice / len(vertices)
                posiciones[vertice] = (
                    centro_x + radio_x * math.cos(angulo),
                    centro_y + radio_y * math.sin(angulo),
                )

        # Aristas primero.
        for origen, destino, peso in self.grafo.aristas():
            x1, y1 = posiciones[origen]
            x2, y2 = posiciones[destino]
            self.canvas.create_line(
                x1, y1, x2, y2, fill=COLORS["border"], width=2,
            )
            if len(self.grafo.aristas()) <= 5:
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                self.canvas.create_text(
                    mx, my - 7, text=f"{peso:.0f} km", fill=COLORS["muted"],
                    font=(FONTS["family"], 7),
                )

        # Nodos.
        for vertice in vertices:
            x, y = posiciones[vertice]
            info = self.grafo.obtener_vertice(vertice) or {}
            self.canvas.create_oval(
                x - 18, y - 18, x + 18, y + 18,
                fill=COLORS["accent_soft"], outline=COLORS["accent"], width=2,
            )
            self.canvas.create_text(
                x, y, text=vertice, fill=COLORS["white"],
                font=(FONTS["family"], 8, "bold"),
            )
            self.canvas.create_text(
                x, y + 26, text=str(info.get("ciudad", "")), fill=COLORS["text_soft"],
                font=(FONTS["family"], 7),
            )

        self.canvas.create_text(
            14, alto - 14, text="Grafo no dirigido · BFS para rutas más cortas",
            anchor="sw", fill=COLORS["muted"], font=(FONTS["family"], 7),
        )
