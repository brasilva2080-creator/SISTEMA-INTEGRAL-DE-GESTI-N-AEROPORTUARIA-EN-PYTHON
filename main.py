"""Punto de entrada del Sistema Integral de Gestión Aeroportuaria."""
from __future__ import annotations

import sys
import traceback
from tkinter import messagebox


def main() -> int:
    try:
        from app import AplicacionAeropuerto
        aplicacion = AplicacionAeropuerto()
        aplicacion.ejecutar()
        return 0
    except Exception as exc:  # pragma: no cover - arranque de la aplicación
        traceback.print_exc()
        try:
            messagebox.showerror(
                "Error al iniciar AeroAndes",
                f"No se pudo iniciar la aplicación:\n\n{exc}\n\n"
                "Verifica que Python, Tkinter y Matplotlib estén instalados.",
            )
        except Exception:
            print(f"Error al iniciar: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
