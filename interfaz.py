"""Interfaz gráfica de la Calculadora de Producción con CustomTkinter."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import List, Optional

import customtkinter as ctk

from calculos import (
    COLORES_TINTA,
    ReferenciaOrden,
    calcular_division_orden,
    calcular_distribucion_valor,
    formatear_kg,
    formatear_porcentaje,
    formatear_valor_distribuido,
    formato_tiempo_hms,
    parse_lista_cantidades,
    texto_excel_orden,
    texto_excel_orden_horas,
    texto_excel_orden_kg,
    texto_excel_orden_tintas,
    texto_excel_valores,
    validar_valor_tinta,
)
from portapapeles import copiar_al_portapapeles


class CalculadoraProduccionApp(ctk.CTk):
    """Ventana principal de la aplicación."""

    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("Calculadora de Producción")
        self.geometry("880x720")
        self.minsize(780, 620)

        self._cantidad_entries: List[ctk.CTkEntry] = []
        self._valores_distribuidos: List = []
        self._referencias_orden: List[ReferenciaOrden] = []

        self._orden_ink_entries: dict[str, ctk.CTkEntry] = {}

        self._construir_ui()

    # ------------------------------------------------------------------ UI
    def _construir_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        titulo = ctk.CTkLabel(
            self,
            text="Calculadora de Producción",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        titulo.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")

        self._frame_cantidades = ctk.CTkFrame(self)
        self._frame_cantidades.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="ew")
        self._frame_cantidades.grid_columnconfigure(0, weight=1)
        self._construir_seccion_cantidades()

        self._frame_principal = ctk.CTkFrame(self, fg_color="transparent")
        self._frame_principal.grid(row=2, column=0, padx=20, pady=(0, 12), sticky="nsew")
        self._frame_principal.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._construir_seccion_orden()
        self._construir_seccion_valores()

    def _construir_seccion_cantidades(self) -> None:
        encabezado = ctk.CTkLabel(
            self._frame_cantidades,
            text="Cantidades por referencia (compartidas)",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        encabezado.grid(row=0, column=0, columnspan=4, padx=12, pady=(8, 4), sticky="w")

        ref_frame = ctk.CTkFrame(self._frame_cantidades, fg_color="transparent")
        ref_frame.grid(row=1, column=0, columnspan=4, padx=12, pady=(0, 8), sticky="ew")
        ref_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(ref_frame, text="Número de referencias:").grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )
        self.entry_num_referencias = ctk.CTkEntry(ref_frame, width=80, placeholder_text="Ej: 32")
        self.entry_num_referencias.grid(row=0, column=1, sticky="w")
        ctk.CTkButton(
            ref_frame,
            text="GENERAR REFERENCIAS",
            width=200,
            height=36,
            command=self._generar_referencias_cantidades,
        ).grid(row=0, column=2, padx=(12, 0), sticky="w")
        ctk.CTkLabel(
            ref_frame,
            text="Crea un campo de cantidad por referencia (.01, .02, …)",
            text_color="gray60",
        ).grid(row=0, column=3, padx=(12, 0), sticky="w")

        self._contenedor_cantidades = ctk.CTkScrollableFrame(
            self._frame_cantidades,
            height=110,
            label_text="",
        )
        self._contenedor_cantidades.grid(row=2, column=0, columnspan=4, padx=12, sticky="ew")
        for col in range(3):
            self._contenedor_cantidades.grid_columnconfigure(col, weight=1)
        self._fuente_ref = ctk.CTkFont(size=11)

        btn_frame = ctk.CTkFrame(self._frame_cantidades, fg_color="transparent")
        btn_frame.grid(row=3, column=0, columnspan=4, padx=12, pady=(8, 12), sticky="w")

        ctk.CTkButton(
            btn_frame,
            text="+ AGREGAR CANTIDAD",
            width=180,
            height=36,
            command=self._agregar_cantidad,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="− ELIMINAR CANTIDAD",
            width=180,
            height=36,
            fg_color="#8B0000",
            hover_color="#A52A2A",
            command=self._eliminar_cantidad,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="📋 PEGAR CANTIDADES",
            width=180,
            height=36,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            command=self._pegar_cantidades,
        ).pack(side="left")

    def _agregar_cantidad(self, valor: str = "") -> None:
        idx = len(self._cantidad_entries)
        fila, col = divmod(idx, 3)
        celda = ctk.CTkFrame(self._contenedor_cantidades, fg_color="transparent")
        celda.grid(row=fila, column=col, sticky="ew", padx=4, pady=2)
        celda.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            celda, text=f".{idx + 1:02d}", width=36, anchor="w", font=self._fuente_ref
        ).grid(row=0, column=0, padx=(0, 4))
        entry = ctk.CTkEntry(celda, placeholder_text="Cant.", height=28, font=self._fuente_ref)
        entry.grid(row=0, column=1, sticky="ew")
        if valor:
            entry.insert(0, valor)
        self._cantidad_entries.append(entry)

    def _eliminar_cantidad(self) -> None:
        if len(self._cantidad_entries) <= 1:
            messagebox.showwarning("Aviso", "Debe mantener al menos una cantidad.")
            return
        entry = self._cantidad_entries.pop()
        entry.master.destroy()
        self._renumerar_cantidades()

    def _renumerar_cantidades(self) -> None:
        for i, entry in enumerate(self._cantidad_entries):
            fila, col = divmod(i, 3)
            entry.master.grid(row=fila, column=col, sticky="ew", padx=4, pady=2)
            label = entry.master.winfo_children()[0]
            label.configure(text=f".{i + 1:02d}")

    def _generar_referencias_cantidades(self) -> None:
        texto = self.entry_num_referencias.get().strip()
        if not texto:
            messagebox.showwarning("Referencias", "Ingrese el número de referencias.")
            return
        try:
            cantidad_refs = int(texto)
        except ValueError:
            messagebox.showerror("Referencias", "El número de referencias debe ser un entero.")
            return
        if cantidad_refs < 1 or cantidad_refs > 999:
            messagebox.showerror("Referencias", "Use un valor entre 1 y 999 referencias.")
            return
        self._establecer_cantidades([""] * cantidad_refs)
        messagebox.showinfo(
            "Listo",
            f"Se generaron {cantidad_refs} campos (Ref .01 a Ref .{cantidad_refs:02d}).\n"
            "Ingrese la cantidad de cada referencia.",
        )

    def _validar_conteo_referencias(self) -> None:
        texto = self.entry_num_referencias.get().strip()
        if not texto:
            return
        try:
            esperadas = int(texto)
        except ValueError as exc:
            raise ValueError("El número de referencias debe ser un entero válido.") from exc
        actuales = len(self._cantidad_entries)
        if actuales != esperadas:
            raise ValueError(
                f"Indicó {esperadas} referencias pero hay {actuales} cantidades. "
                "Use GENERAR REFERENCIAS o ajuste el número."
            )

    def _obtener_cantidades(self) -> List[str]:
        return [e.get() for e in self._cantidad_entries]

    def _limpiar_cantidades(self) -> None:
        while len(self._cantidad_entries) > 0:
            entry = self._cantidad_entries.pop()
            entry.master.destroy()

    def _establecer_cantidades(self, valores: List[str]) -> None:
        self._limpiar_cantidades()
        for valor in valores:
            self._agregar_cantidad(valor)

    def _pegar_cantidades(self) -> None:
        dialogo = ctk.CTkInputDialog(
            text="Pegue las cantidades separadas por comas o saltos de línea:",
            title="Pegar cantidades",
        )
        texto = dialogo.get_input()
        if not texto:
            return
        try:
            valores = parse_lista_cantidades(texto)
            self._establecer_cantidades(valores)
            messagebox.showinfo("Listo", f"Se cargaron {len(valores)} cantidades.")
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))

    # ------------------------------------------------------------------ Tab Orden
    def _construir_seccion_orden(self) -> None:
        parent = self._frame_principal
        parent.grid_columnconfigure(1, weight=1)
        parent.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(parent, text="KG total:").grid(row=0, column=0, padx=4, pady=(4, 4), sticky="w")
        self.entry_kg_total = ctk.CTkEntry(parent, placeholder_text="Ej: 15.4")
        self.entry_kg_total.grid(row=0, column=1, padx=4, pady=(4, 4), sticky="ew")

        tiempo_frame = ctk.CTkFrame(parent, fg_color="transparent")
        tiempo_frame.grid(row=1, column=0, columnspan=2, padx=4, pady=4, sticky="ew")

        ctk.CTkLabel(tiempo_frame, text="Inicio (HH:MM):").grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.entry_orden_inicio = ctk.CTkEntry(tiempo_frame, width=88, placeholder_text="15:00")
        self.entry_orden_inicio.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(tiempo_frame, text="Fin (HH:MM):").grid(row=0, column=2, padx=(16, 8), sticky="w")
        self.entry_orden_fin = ctk.CTkEntry(tiempo_frame, width=88, placeholder_text="20:00")
        self.entry_orden_fin.grid(row=0, column=3, sticky="w")
        ctk.CTkLabel(
            parent,
            text="El tiempo del lote sale de inicio → fin; cada referencia recibe su tramo proporcional. "
            "Si fin < inicio (19:00 → 01:00) se asume cruce de medianoche.",
            text_color="gray60",
            font=ctk.CTkFont(size=11),
            wraplength=820,
            justify="left",
        ).grid(row=2, column=0, columnspan=2, padx=4, pady=(0, 4), sticky="w")

        tintas_frame = ctk.CTkFrame(parent)
        tintas_frame.grid(row=3, column=0, columnspan=2, padx=4, pady=4, sticky="ew")
        tintas_frame.grid_columnconfigure((1, 3, 5, 7), weight=1)

        ctk.CTkLabel(
            tintas_frame,
            text="Tintas totales del lote (valor crudo → ÷1000 → distribución por referencia):",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, columnspan=8, padx=8, pady=(8, 4), sticky="w")

        ink_defaults = {
            "cyan": "11.34", "magenta": "30.75", "yellow": "36.86",
            "black": "17.52", "orange": "25.67", "violet": "3.11", "white": "0",
        }
        for i, (nombre, clave) in enumerate(COLORES_TINTA):
            fila, col = divmod(i, 4)
            base_col = col * 2
            ctk.CTkLabel(tintas_frame, text=f"{nombre.split()[1]}:").grid(
                row=fila + 1, column=base_col, padx=(8, 4), pady=3, sticky="w"
            )
            entry = ctk.CTkEntry(tintas_frame, placeholder_text="0")
            entry.grid(row=fila + 1, column=base_col + 1, padx=(0, 8), pady=3, sticky="ew")
            if clave in ink_defaults:
                entry.insert(0, ink_defaults[clave])
            self._orden_ink_entries[clave] = entry

        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=4, column=0, columnspan=2, padx=4, pady=4, sticky="w")

        ctk.CTkButton(btn_frame, text="CALCULAR", width=120, height=40, command=self._calcular_orden).pack(
            side="left", padx=(0, 6)
        )
        ctk.CTkButton(
            btn_frame, text="LIMPIAR", width=100, height=40, fg_color="gray40", hover_color="gray30",
            command=self._limpiar_orden,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btn_frame, text="📋 COPIAR TODO", width=130, height=40,
            command=self._copiar_orden,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btn_frame, text="📋 COPIAR HORAS", width=140, height=40,
            command=self._copiar_orden_horas,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btn_frame, text="📋 COPIAR KG", width=120, height=40,
            command=self._copiar_orden_kg,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            btn_frame, text="📋 COPIAR TINTAS", width=140, height=40,
            command=self._copiar_orden_tintas,
        ).pack(side="left")

        self.lbl_resumen_orden = ctk.CTkLabel(
            parent, text="Referencias: —", font=ctk.CTkFont(size=10, weight="bold")
        )
        self.lbl_resumen_orden.grid(row=5, column=0, columnspan=2, padx=4, pady=(0, 2), sticky="w")

        self._fuente_resultado = ctk.CTkFont(family="Consolas", size=9)
        self.text_orden = ctk.CTkTextbox(parent, height=115, font=self._fuente_resultado)
        self.text_orden.grid(row=6, column=0, columnspan=2, padx=4, pady=(0, 6), sticky="nsew")
        parent.grid_rowconfigure(6, weight=1)
        self.text_orden.insert("1.0", "Calcule para ver el resumen compacto.\n")
        self.text_orden.configure(state="disabled")

    def _obtener_consumos_orden(self) -> dict | None:
        from decimal import Decimal

        consumos = {}
        tiene_valor = False
        for nombre, clave in COLORES_TINTA:
            texto = self._orden_ink_entries[clave].get().strip()
            if texto:
                consumos[clave] = validar_valor_tinta(texto, nombre)
                tiene_valor = True
            else:
                consumos[clave] = Decimal("0")
        return consumos if tiene_valor else None

    def _calcular_orden(self) -> None:
        try:
            self._validar_conteo_referencias()
            kg = self.entry_kg_total.get().strip() or None
            hora_ini = self.entry_orden_inicio.get().strip() or None
            hora_fin = self.entry_orden_fin.get().strip() or None
            consumos = self._obtener_consumos_orden()

            referencias, total = calcular_division_orden(
                "",
                self._obtener_cantidades(),
                kg_total=kg,
                hora_inicio=hora_ini,
                hora_fin=hora_fin,
                consumos_tinta=consumos,
            )
            self._referencias_orden = referencias

            suma_kg = sum(r.kg for r in referencias if r.kg is not None)
            suma_tiempo = sum(r.tiempo_segundos for r in referencias)
            self.lbl_resumen_orden.configure(
                text=f"Referencias: {len(referencias)} | Total cantidades: {total} | "
                f"Suma KG: {formatear_kg(suma_kg) if kg else '—'} | "
                f"Suma tiempo: {formato_tiempo_hms(suma_tiempo)}"
            )

            lineas = ["Ref\tCant\tKG\tInicio\tFin\tDur"]
            for ref in referencias:
                kg_txt = formatear_kg(ref.kg) if ref.kg is not None else ""
                cant_txt = str(int(ref.cantidad) if ref.cantidad == int(ref.cantidad) else ref.cantidad)
                ini_txt = ref.tiempo_inicio or ""
                fin_txt = ref.tiempo_fin or ""
                lineas.append(
                    f"{ref.referencia}\t{cant_txt}\t{kg_txt}\t{ini_txt}\t{fin_txt}\t{ref.tiempo_hms}"
                )

            self.text_orden.configure(state="normal")
            self.text_orden.delete("1.0", "end")
            self.text_orden.insert("1.0", "\n".join(lineas))
            self.text_orden.configure(state="disabled")
        except ValueError as exc:
            messagebox.showerror("Error de validación", str(exc))

    def _limpiar_orden(self) -> None:
        self.entry_kg_total.delete(0, "end")
        self.entry_orden_inicio.delete(0, "end")
        self.entry_orden_fin.delete(0, "end")
        for entry in self._orden_ink_entries.values():
            entry.delete(0, "end")
        self._referencias_orden = []
        self.lbl_resumen_orden.configure(text="Referencias: —")
        self.text_orden.configure(state="normal")
        self.text_orden.delete("1.0", "end")
        self.text_orden.insert("1.0", "Calcule para ver el resumen compacto.\n")
        self.text_orden.configure(state="disabled")

    def _copiar_orden(self) -> None:
        if not self._referencias_orden:
            messagebox.showinfo("Sin datos", "Calcule primero la división de la orden.")
            return
        incluir_kg = any(r.kg is not None for r in self._referencias_orden)
        texto = texto_excel_orden(self._referencias_orden, incluir_kg=incluir_kg)
        copiar_al_portapapeles(texto, self)
        messagebox.showinfo("Copiado", "Tabla completa copiada al portapapeles (sin encabezados).")

    def _copiar_orden_horas(self) -> None:
        if not self._referencias_orden:
            messagebox.showinfo("Sin datos", "Calcule primero la división de la orden.")
            return
        texto = texto_excel_orden_horas(self._referencias_orden)
        copiar_al_portapapeles(texto, self)
        messagebox.showinfo(
            "Copiado",
            "Horas distribuidas copiadas (Inicio\\tFin o duración, sin encabezados).",
        )

    def _copiar_orden_kg(self) -> None:
        if not self._referencias_orden:
            messagebox.showinfo("Sin datos", "Calcule primero la división de la orden.")
            return
        if not any(r.kg is not None for r in self._referencias_orden):
            messagebox.showinfo("Sin KG", "Ingrese el KG total antes de calcular.")
            return
        texto = texto_excel_orden_kg(self._referencias_orden)
        copiar_al_portapapeles(texto, self)
        messagebox.showinfo("Copiado", "KG distribuidos copiados (una columna, sin encabezados).")

    def _copiar_orden_tintas(self) -> None:
        if not self._referencias_orden:
            messagebox.showinfo("Sin datos", "Calcule primero la división de la orden.")
            return
        if not any(r.tintas for r in self._referencias_orden):
            messagebox.showinfo("Sin tintas", "Ingrese valores de tinta antes de calcular.")
            return
        texto = texto_excel_orden_tintas(self._referencias_orden)
        copiar_al_portapapeles(texto, self)
        messagebox.showinfo(
            "Copiado",
            "Tintas por referencia: DIG CYAN | valor | … | DIG WHITE | valor (tabulaciones).",
        )

    def _construir_seccion_valores(self) -> None:
        """Opcional: repartir un monto fijo (costo, etc.) — no es lo mismo que tintas DIG."""
        parent = self._frame_principal
        sep = ctk.CTkFrame(parent, height=2, fg_color="gray40")
        sep.grid(row=7, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 6))

        ctk.CTkLabel(
            parent,
            text="Distribución de un valor (opcional)",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=8, column=0, columnspan=2, padx=4, sticky="w")
        ctk.CTkLabel(
            parent,
            text="Ej.: repartir 118.14 entre referencias según cantidades (independiente de KG y tintas).",
            text_color="gray60",
            font=ctk.CTkFont(size=11),
            wraplength=820,
            justify="left",
        ).grid(row=9, column=0, columnspan=2, padx=4, pady=(0, 4), sticky="w")

        val_frame = ctk.CTkFrame(parent, fg_color="transparent")
        val_frame.grid(row=10, column=0, columnspan=2, padx=4, sticky="ew")
        val_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(val_frame, text="Valor:").grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.entry_valor = ctk.CTkEntry(val_frame, width=120, placeholder_text="118.14")
        self.entry_valor.grid(row=0, column=1, sticky="w")

        ctk.CTkButton(
            val_frame, text="CALCULAR", width=100, height=32, command=self._calcular_valores
        ).grid(row=0, column=2, padx=(8, 4))
        ctk.CTkButton(
            val_frame,
            text="📋 COPIAR",
            width=100,
            height=32,
            command=self._copiar_valores,
        ).grid(row=0, column=3, padx=4)

        self.text_valores = ctk.CTkTextbox(
            parent, height=72, font=ctk.CTkFont(family="Consolas", size=9)
        )
        self.text_valores.grid(row=11, column=0, columnspan=2, padx=4, pady=(4, 0), sticky="ew")
        self.text_valores.insert("1.0", "Valor\t%\n")
        self.text_valores.configure(state="disabled")

    def _calcular_valores(self) -> None:
        try:
            resultados, porcentajes = calcular_distribucion_valor(
                self.entry_valor.get(),
                self._obtener_cantidades(),
            )
            self._valores_distribuidos = resultados

            lineas = ["Valor\t%"]
            for valor, pct in zip(resultados, porcentajes):
                lineas.append(f"{formatear_valor_distribuido(valor)}\t{formatear_porcentaje(pct)}")

            self.text_valores.configure(state="normal")
            self.text_valores.delete("1.0", "end")
            self.text_valores.insert("1.0", "\n".join(lineas))
            self.text_valores.configure(state="disabled")
        except ValueError as exc:
            messagebox.showerror("Error de validación", str(exc))

    def _limpiar_valores(self) -> None:
        self.entry_valor.delete(0, "end")
        self._valores_distribuidos = []
        self.text_valores.configure(state="normal")
        self.text_valores.delete("1.0", "end")
        self.text_valores.insert("1.0", "Valor\t%\n")
        self.text_valores.configure(state="disabled")

    def _copiar_valores(self) -> None:
        if not self._valores_distribuidos:
            messagebox.showinfo("Sin datos", "Calcule primero la distribución de valores.")
            return
        texto = texto_excel_valores(self._valores_distribuidos)
        copiar_al_portapapeles(texto, self)
        messagebox.showinfo("Copiado", "Valores distribuidos copiados al portapapeles.")


def iniciar_aplicacion() -> None:
    app = CalculadoraProduccionApp()
    app.mainloop()
