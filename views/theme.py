"""Tema visual oscuro y configuración global de ttk."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from config import COLORS, FONTS


def configurar_tema(root: tk.Tk) -> ttk.Style:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=COLORS["bg"])
    root.option_add("*Font", FONTS["body"])
    root.option_add("*TCombobox*Listbox.background", COLORS["card"])
    root.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", COLORS["accent_soft"])
    root.option_add("*TCombobox*Listbox.selectForeground", COLORS["text"])
    root.option_add("*Menu.background", COLORS["card"])
    root.option_add("*Menu.foreground", COLORS["text"])
    root.option_add("*Menu.activeBackground", COLORS["accent_soft"])
    root.option_add("*Menu.activeForeground", COLORS["text"])

    style.configure(
        ".", background=COLORS["bg"], foreground=COLORS["text"],
        fieldbackground=COLORS["bg_soft"], font=FONTS["body"],
    )
    style.configure(
        "TEntry",
        fieldbackground=COLORS["bg_soft"],
        foreground=COLORS["text"],
        insertcolor=COLORS["accent"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        padding=(8, 6),
    )
    style.map(
        "TEntry",
        bordercolor=[("focus", COLORS["accent"])],
        lightcolor=[("focus", COLORS["accent"])],
        darkcolor=[("focus", COLORS["accent"])],
        fieldbackground=[("disabled", COLORS["card_alt"])],
        foreground=[("disabled", COLORS["muted"])],
    )
    style.configure(
        "TCombobox",
        fieldbackground=COLORS["bg_soft"],
        background=COLORS["card_alt"],
        foreground=COLORS["text"],
        arrowcolor=COLORS["accent"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        padding=(8, 5),
        selectbackground=COLORS["accent_soft"],
        selectforeground=COLORS["text"],
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLORS["bg_soft"])],
        foreground=[("readonly", COLORS["text"])],
        bordercolor=[("focus", COLORS["accent"])],
        arrowcolor=[("active", COLORS["accent"])],
    )
    style.configure(
        "Treeview",
        background=COLORS["card"],
        fieldbackground=COLORS["card"],
        foreground=COLORS["text"],
        borderwidth=0,
        rowheight=30,
        font=FONTS["body"],
    )
    style.map(
        "Treeview",
        background=[("selected", COLORS["accent_soft"])],
        foreground=[("selected", COLORS["white"])],
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["card_alt"],
        foreground=COLORS["muted"],
        relief="flat",
        borderwidth=0,
        padding=(8, 8),
        font=FONTS["body_bold"],
    )
    style.map(
        "Treeview.Heading",
        background=[("active", COLORS["card_light"])],
        foreground=[("active", COLORS["text"])],
    )
    style.configure(
        "Vertical.TScrollbar",
        background=COLORS["card_alt"],
        troughcolor=COLORS["bg_soft"],
        bordercolor=COLORS["bg_soft"],
        arrowcolor=COLORS["muted"],
        darkcolor=COLORS["card_alt"],
        lightcolor=COLORS["card_alt"],
    )
    style.map("Vertical.TScrollbar", background=[("active", COLORS["border"])])
    style.configure(
        "Horizontal.TScrollbar",
        background=COLORS["card_alt"],
        troughcolor=COLORS["bg_soft"],
        bordercolor=COLORS["bg_soft"],
        arrowcolor=COLORS["muted"],
    )
    style.configure(
        "TProgressbar",
        troughcolor=COLORS["bg_soft"],
        background=COLORS["accent"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["accent"],
        darkcolor=COLORS["accent"],
        thickness=10,
    )
    style.configure(
        "TCheckbutton",
        background=COLORS["card"],
        foreground=COLORS["text"],
        focuscolor=COLORS["card"],
        indicatorcolor=COLORS["bg_soft"],
        font=FONTS["body"],
    )
    style.map(
        "TCheckbutton",
        background=[("active", COLORS["card"])],
        foreground=[("active", COLORS["accent"])],
        indicatorcolor=[("selected", COLORS["accent"])],
    )
    style.configure(
        "TRadiobutton",
        background=COLORS["card"],
        foreground=COLORS["text"],
        focuscolor=COLORS["card"],
    )
    style.configure(
        "TSpinbox",
        fieldbackground=COLORS["bg_soft"],
        foreground=COLORS["text"],
        insertcolor=COLORS["accent"],
        arrowcolor=COLORS["accent"],
        bordercolor=COLORS["border"],
        padding=(8, 5),
    )
    return style
