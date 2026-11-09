"""Vista de gestión de pasajeros e historial de reservas."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from config import COLORS, dinero, fecha_humana
from views.base import VistaBase
from views.widgets import (Card, Modal, Tabla, boton, campo, etiqueta,
                           separador, chip_estado)


class PasajerosView(VistaBase):
    def construir(self) -> None:
        cab = self.encabezado(
            "Gestión de pasajeros",
            "Registro de identidad ficticia, consulta y trazabilidad de reservas",
        )
        boton(cab.acciones, "Actualizar", self.refrescar, tipo="secondary",
              compacto=True, icono="↻").pack(side="right", padx=(8, 0))
        boton(cab.acciones, "Nuevo pasajero", self.nuevo_pasajero, tipo="primary",
              compacto=True, icono="+").pack(side="right")

        filtros = Card(self, padding=12)
        filtros.pack(fill="x", padx=24, pady=(0, 12))
        cont = filtros.cuerpo
        etiqueta(cont, "Buscar por código, nombre, documento o correo", size=8,
                 bold=True, color=COLORS["muted"]).pack(anchor="w")
        fila = tk.Frame(cont, bg=COLORS["card"])
        fila.pack(fill="x", pady=(4, 0))
        self.var_busqueda = tk.StringVar()
        entrada = campo(fila, self.var_busqueda)
        entrada.pack(side="left", fill="x", expand=True)
        entrada.bind("<Return>", lambda _e: self.refrescar())
        boton(fila, "Buscar", self.refrescar, compacto=True,
              icono="⌕").pack(side="left", padx=(8, 0))
        boton(fila, "Limpiar", self.limpiar, tipo="ghost",
              compacto=True).pack(side="left", padx=(6, 0))

        card = Card(self, padding=0)
        card.pack(fill="both", expand=True, padx=24, pady=(0, 12))
        cab_tabla = tk.Frame(card.cuerpo, bg=COLORS["card"], padx=16, pady=12)
        cab_tabla.pack(fill="x")
        etiqueta(cab_tabla, "Directorio de pasajeros", size=13, bold=True).pack(side="left")
        self.lbl_conteo = etiqueta(cab_tabla, "", size=9, color=COLORS["muted"])
        self.lbl_conteo.pack(side="right")
        separador(card.cuerpo).pack(fill="x")
        self.tabla = Tabla(card.cuerpo, [
            ("codigo", "CÓDIGO", 92, "center", False),
            ("nombre", "NOMBRE COMPLETO", 220, "w", True),
            ("documento", "DOCUMENTO", 110, "center", False),
            ("email", "CORREO", 220, "w", True),
            ("telefono", "TELÉFONO", 110, "center", False),
            ("reservas", "RESERVAS", 100, "center", False),
        ], altura=14, on_doble_clic=self.editar_pasajero)
        self.tabla.pack(fill="both", expand=True, padx=8, pady=8)

        barra = tk.Frame(card.cuerpo, bg=COLORS["card"], padx=16, pady=10)
        barra.pack(fill="x")
        boton(barra, "Editar datos", self.editar_pasajero, tipo="secondary",
              compacto=True, icono="✎").pack(side="left", padx=(0, 6))
        boton(barra, "Historial de reservas", self.ver_historial, tipo="purple",
              compacto=True, icono="▤").pack(side="left")
        etiqueta(barra, "Doble clic sobre una fila para editar", size=8,
                 color=COLORS["muted"]).pack(side="right")

    def refrescar(self) -> None:
        pasajeros = self.app.pasajeros.listar(self.var_busqueda.get())
        filas = []
        for p in pasajeros:
            filas.append({
                "_iid": str(p.id),
                "codigo": p.codigo,
                "nombre": p.nombre_completo,
                "documento": p.documento,
                "email": p.email,
                "telefono": p.telefono,
                "reservas": p.reservas,
            })
        self.tabla.set_filas(filas)
        self.lbl_conteo.configure(text=f"{len(pasajeros)} pasajero(s)")

    def limpiar(self) -> None:
        self.var_busqueda.set("")
        self.refrescar()

    def _seleccionado(self):
        fila = self.tabla.seleccionado()
        if not fila:
            self.error("Selecciona un pasajero en la tabla.")
            return None
        pasajero = self.app.pasajeros.obtener(int(fila["_iid"]))
        if not pasajero:
            self.error("El pasajero ya no existe.")
        return pasajero

    def nuevo_pasajero(self) -> None:
        self._formulario(None)

    def editar_pasajero(self) -> None:
        pasajero = self._seleccionado()
        if pasajero:
            self._formulario(pasajero)

    def _formulario(self, pasajero) -> None:
        modal = Modal(self, "Editar pasajero" if pasajero else "Registrar pasajero",
                      ancho=560, alto=610)
        cuerpo = modal.cuerpo
        cuerpo.grid_columnconfigure(0, weight=1)
        cuerpo.grid_columnconfigure(1, weight=1)

        def agregar(fila: int, col: int, texto: str, variable: tk.StringVar,
                    colspan: int = 1) -> None:
            contenedor = tk.Frame(cuerpo, bg=COLORS["bg"])
            contenedor.grid(row=fila, column=col, columnspan=colspan, sticky="ew",
                            padx=(0, 10) if col == 0 else (10, 0), pady=(0, 12))
            etiqueta(contenedor, texto.upper(), size=8, bold=True,
                     color=COLORS["muted"]).pack(anchor="w", pady=(0, 4))
            campo(contenedor, variable).pack(fill="x")

        var_nombres = tk.StringVar(value=pasajero.nombres if pasajero else "")
        var_apellidos = tk.StringVar(value=pasajero.apellidos if pasajero else "")
        var_documento = tk.StringVar(value=pasajero.documento if pasajero else "")
        var_email = tk.StringVar(value=pasajero.email if pasajero else "")
        var_telefono = tk.StringVar(value=pasajero.telefono if pasajero else "")
        agregar(0, 0, "Nombres", var_nombres)
        agregar(0, 1, "Apellidos", var_apellidos)
        agregar(1, 0, "Documento ficticio", var_documento)
        agregar(1, 1, "Teléfono", var_telefono)
        agregar(2, 0, "Correo electrónico", var_email, colspan=2)
        etiqueta(
            cuerpo,
            "Los datos son ficticios y se usan únicamente con fines académicos. "
            "El código de pasajero se genera automáticamente.",
            size=8, color=COLORS["muted"], wraplength=480, justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))

        def guardar() -> None:
            try:
                if pasajero:
                    self.app.pasajeros.actualizar(
                        pasajero.id, var_nombres.get(), var_apellidos.get(),
                        var_documento.get(), var_email.get(), var_telefono.get(),
                    )
                    mensaje = f"Pasajero {pasajero.codigo} actualizado."
                else:
                    nuevo = self.app.pasajeros.registrar(
                        var_nombres.get(), var_apellidos.get(), var_documento.get(),
                        var_email.get(), var_telefono.get(),
                    )
                    mensaje = f"Pasajero {nuevo.codigo} registrado correctamente."
                modal.cerrar()
                self.refrescar()
                self.info("Pasajeros", mensaje)
            except Exception as exc:
                self.error(exc)

        boton(modal.pie, "Cancelar", modal.cerrar, tipo="ghost",
              compacto=True).pack(side="right", padx=(8, 0))
        boton(modal.pie, "Guardar", guardar, tipo="primary",
              compacto=True, icono="✓").pack(side="right")
        modal.esperar()

    def ver_historial(self) -> None:
        pasajero = self._seleccionado()
        if not pasajero:
            return
        historial = self.app.pasajeros.historial_reservas(pasajero.id)
        modal = Modal(self, "Historial de reservas", ancho=880, alto=580,
                      redimensionable=True)
        etiqueta(modal.cuerpo, pasajero.nombre_completo, size=18, bold=True).pack(anchor="w")
        etiqueta(modal.cuerpo, f"{pasajero.codigo} · Documento {pasajero.documento}",
                 size=9, color=COLORS["muted"]).pack(anchor="w", pady=(2, 12))
        tabla = Tabla(modal.cuerpo, [
            ("codigo", "RESERVA", 95, "center", False),
            ("vuelo", "VUELO", 80, "center", False),
            ("ruta", "RUTA", 90, "center", False),
            ("salida", "SALIDA", 130, "center", False),
            ("asiento", "ASIENTO", 70, "center", False),
            ("precio", "TARIFA", 85, "e", False),
            ("checkin", "CHECK-IN", 130, "center", False),
            ("estado", "ESTADO", 100, "center", True),
        ], altura=12)
        tabla.pack(fill="both", expand=True)
        filas = []
        for i, fila in enumerate(historial):
            filas.append({
                "_iid": str(i),
                "codigo": fila["codigo"],
                "vuelo": fila["vuelo"],
                "ruta": f"{fila['origen']} → {fila['destino']}",
                "salida": fecha_humana(fila["fecha_salida"]),
                "asiento": fila["asiento"],
                "precio": dinero(fila["precio"]),
                "checkin": fila["checkin"],
                "estado": fila["estado"],
            })
        tabla.set_filas(filas)
        if not historial:
            etiqueta(modal.cuerpo, "Este pasajero aún no tiene reservas registradas.",
                     size=9, color=COLORS["muted"]).pack(anchor="w", pady=(10, 0))
        etiqueta(modal.cuerpo, f"{len(historial)} reserva(s) en el historial",
                 size=9, color=COLORS["muted"]).pack(anchor="w", pady=(8, 0))
        boton(modal.pie, "Cerrar", modal.cerrar, tipo="secondary",
              compacto=True).pack(side="right")
        modal.esperar()
