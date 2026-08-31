"""Interfaz gráfica de la Calculadora de Producción con CustomTkinter."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import List, Optional

import customtkinter as ctk

from calculos import (
    COLORES_TINTA,
    FilaTinta,
    SegmentoTiempo,
    calcular_consumo_tintas,
    calcular_division_tiempos,
    calcular_distribucion_valor,
    formatear_porcentaje,
    formatear_tinta,
    formatear_valor_distribuido,
    texto_excel_tiempos,
    texto_excel_tintas,
    texto_excel_valores,
)
from portapapeles import copiar_al_portapapeles


class CalculadoraProduccionApp(ctk.CTk):
    """Ventana principal de la aplicación."""

    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title("Calculadora de Producción")
        self.geometry("920x780")
        self.minsize(820, 680)

        self._cantidad_entries: List[ctk.CTkEntry] = []
        self._segmentos_tiempo: List[SegmentoTiempo] = []
        self._filas_tinta: List[FilaTinta] = []
        self._valores_distribuidos: List = []

        self._ink_entries: dict[str, ctk.CTkEntry] = {}

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

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=2, column=0, padx=20, pady=(0, 16), sticky="nsew")
        self.grid_rowconfigure(2, weight=1)

        self.tab_tiempos = self.tabview.add("⏱️ División de tiempos")
        self.tab_tintas = self.tabview.add("🎨 Consumo de tintas")
        self.tab_valores = self.tabview.add("🧮 Distribución de valores")

        self._construir_tab_tiempos()
        self._construir_tab_tintas()
        self._construir_tab_valores()

    def _construir_seccion_cantidades(self) -> None:
        encabezado = ctk.CTkLabel(
            self._frame_cantidades,
            text="Cantidades de producción (compartidas)",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        encabezado.grid(row=0, column=0, columnspan=3, padx=12, pady=(12, 8), sticky="w")

        self._contenedor_cantidades = ctk.CTkFrame(self._frame_cantidades, fg_color="transparent")
        self._contenedor_cantidades.grid(row=1, column=0, columnspan=3, padx=12, sticky="ew")
        self._contenedor_cantidades.grid_columnconfigure(1, weight=1)

        btn_frame = ctk.CTkFrame(self._frame_cantidades, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=3, padx=12, pady=(8, 12), sticky="w")

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
        ).pack(side="left")

        for valor in ("10000", "10000", "5000"):
            self._agregar_cantidad(valor)

    def _agregar_cantidad(self, valor: str = "") -> None:
        idx = len(self._cantidad_entries)
        fila = ctk.CTkFrame(self._contenedor_cantidades, fg_color="transparent")
        fila.grid(row=idx, column=0, columnspan=2, sticky="ew", pady=3)
        fila.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(fila, text=f"Cantidad {idx + 1}:", width=100, anchor="w").grid(
            row=0, column=0, padx=(0, 8)
        )
        entry = ctk.CTkEntry(fila, placeholder_text="Ej: 10000")
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
            entry.master.grid(row=i, column=0, columnspan=2, sticky="ew", pady=3)
            label = entry.master.winfo_children()[0]
            label.configure(text=f"Cantidad {i + 1}:")

    def _obtener_cantidades(self) -> List[str]:
        return [e.get() for e in self._cantidad_entries]

    # ------------------------------------------------------------------ Tab Tiempos
    def _construir_tab_tiempos(self) -> None:
        tab = self.tab_tiempos
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(tab, text="Hora inicio (HH:MM):").grid(
            row=0, column=0, padx=12, pady=(12, 6), sticky="w"
        )
        self.entry_inicio = ctk.CTkEntry(tab, placeholder_text="16:20")
        self.entry_inicio.grid(row=0, column=1, padx=12, pady=(12, 6), sticky="ew")
        self.entry_inicio.insert(0, "16:20")

        ctk.CTkLabel(tab, text="Hora final (HH:MM):").grid(
            row=1, column=0, padx=12, pady=6, sticky="w"
        )
        self.entry_fin = ctk.CTkEntry(tab, placeholder_text="19:00")
        self.entry_fin.grid(row=1, column=1, padx=12, pady=6, sticky="ew")
        self.entry_fin.insert(0, "19:00")

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, padx=12, pady=12, sticky="w")

        ctk.CTkButton(btn_frame, text="CALCULAR", width=140, height=40, command=self._calcular_tiempos).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(
            btn_frame, text="LIMPIAR", width=140, height=40, fg_color="gray40", hover_color="gray30",
            command=self._limpiar_tiempos,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_frame, text="📋 COPIAR PARA EXCEL", width=180, height=40,
            command=self._copiar_tiempos,
        ).pack(side="left")

        self.lbl_total_tiempos = ctk.CTkLabel(tab, text="Total cantidades: —", font=ctk.CTkFont(weight="bold"))
        self.lbl_total_tiempos.grid(row=3, column=0, columnspan=2, padx=12, pady=(0, 6), sticky="w")

        self.text_tiempos = ctk.CTkTextbox(tab, height=220, font=ctk.CTkFont(family="Consolas", size=13))
        self.text_tiempos.grid(row=4, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="nsew")
        self.text_tiempos.insert("1.0", "Inicio\tFin\tCantidad\t%\n")
        self.text_tiempos.configure(state="disabled")

    def _calcular_tiempos(self) -> None:
        try:
            segmentos, total = calcular_division_tiempos(
                self.entry_inicio.get(),
                self.entry_fin.get(),
                self._obtener_cantidades(),
            )
            self._segmentos_tiempo = segmentos
            self.lbl_total_tiempos.configure(text=f"Total cantidades: {total}")

            lineas = ["Inicio\tFin\tCantidad\t%"]
            for seg in segmentos:
                lineas.append(
                    f"{seg.inicio}\t{seg.fin}\t{seg.cantidad}\t{formatear_porcentaje(seg.porcentaje)}"
                )

            self.text_tiempos.configure(state="normal")
            self.text_tiempos.delete("1.0", "end")
            self.text_tiempos.insert("1.0", "\n".join(lineas))
            self.text_tiempos.configure(state="disabled")
        except ValueError as exc:
            messagebox.showerror("Error de validación", str(exc))

    def _limpiar_tiempos(self) -> None:
        self.entry_inicio.delete(0, "end")
        self.entry_fin.delete(0, "end")
        self.lbl_total_tiempos.configure(text="Total cantidades: —")
        self._segmentos_tiempo = []
        self.text_tiempos.configure(state="normal")
        self.text_tiempos.delete("1.0", "end")
        self.text_tiempos.insert("1.0", "Inicio\tFin\tCantidad\t%\n")
        self.text_tiempos.configure(state="disabled")

    def _copiar_tiempos(self) -> None:
        if not self._segmentos_tiempo:
            messagebox.showinfo("Sin datos", "Calcule primero la división de tiempos.")
            return
        texto = texto_excel_tiempos(self._segmentos_tiempo)
        copiar_al_portapapeles(texto, self)
        messagebox.showinfo("Copiado", "Resultados de tiempos copiados al portapapeles.")

    # ------------------------------------------------------------------ Tab Tintas
    def _construir_tab_tintas(self) -> None:
        tab = self.tab_tintas
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        frame_inks = ctk.CTkFrame(tab)
        frame_inks.grid(row=0, column=0, columnspan=2, padx=12, pady=12, sticky="ew")
        frame_inks.grid_columnconfigure(1, weight=1)

        defaults = {
            "cyan": "236.39",
            "magenta": "666.89",
            "yellow": "706.20",
            "black": "994.07",
            "orange": "441.15",
            "violet": "42.08",
        }

        for i, (nombre, clave) in enumerate(COLORES_TINTA):
            ctk.CTkLabel(frame_inks, text=f"{nombre}:").grid(
                row=i, column=0, padx=(12, 8), pady=4, sticky="w"
            )
            entry = ctk.CTkEntry(frame_inks, placeholder_text="0.00")
            entry.grid(row=i, column=1, padx=(0, 12), pady=4, sticky="ew")
            entry.insert(0, defaults.get(clave, ""))
            self._ink_entries[clave] = entry

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="w")

        ctk.CTkButton(btn_frame, text="CALCULAR", width=140, height=40, command=self._calcular_tintas).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(
            btn_frame, text="LIMPIAR", width=140, height=40, fg_color="gray40", hover_color="gray30",
            command=self._limpiar_tintas,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_frame, text="📋 COPIAR PARA EXCEL", width=180, height=40,
            command=self._copiar_tintas,
        ).pack(side="left")

        self.text_tintas = ctk.CTkTextbox(tab, height=260, font=ctk.CTkFont(family="Consolas", size=12))
        self.text_tintas.grid(row=2, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="nsew")
        self.text_tintas.insert("1.0", "Calcule para ver los resultados de consumo de tintas.\n")
        self.text_tintas.configure(state="disabled")

    def _obtener_consumos_tinta(self) -> dict:
        from decimal import Decimal
        from calculos import validar_valor_tinta

        consumos = {}
        for nombre, clave in COLORES_TINTA:
            consumos[clave] = validar_valor_tinta(self._ink_entries[clave].get(), nombre)
        return consumos

    def _calcular_tintas(self) -> None:
        try:
            consumos = self._obtener_consumos_tinta()
            filas, _ = calcular_consumo_tintas(consumos, self._obtener_cantidades())
            self._filas_tinta = filas

            lineas: List[str] = []
            for fila in filas:
                partes = []
                for nombre, valor in fila.valores:
                    partes.append(f"{nombre}  {formatear_tinta(valor)}")
                lineas.append("    ".join(partes))

            self.text_tintas.configure(state="normal")
            self.text_tintas.delete("1.0", "end")
            self.text_tintas.insert("1.0", "\n".join(lineas))
            self.text_tintas.configure(state="disabled")
        except ValueError as exc:
            messagebox.showerror("Error de validación", str(exc))

    def _limpiar_tintas(self) -> None:
        for entry in self._ink_entries.values():
            entry.delete(0, "end")
        self._filas_tinta = []
        self.text_tintas.configure(state="normal")
        self.text_tintas.delete("1.0", "end")
        self.text_tintas.insert("1.0", "Calcule para ver los resultados de consumo de tintas.\n")
        self.text_tintas.configure(state="disabled")

    def _copiar_tintas(self) -> None:
        if not self._filas_tinta:
            messagebox.showinfo("Sin datos", "Calcule primero el consumo de tintas.")
            return
        texto = texto_excel_tintas(self._filas_tinta)
        copiar_al_portapapeles(texto, self)
        messagebox.showinfo("Copiado", "Resultados de tintas copiados al portapapeles.")

    # ------------------------------------------------------------------ Tab Valores
    def _construir_tab_valores(self) -> None:
        tab = self.tab_valores
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(tab, text="Valor a distribuir:").grid(
            row=0, column=0, padx=12, pady=(12, 6), sticky="w"
        )
        self.entry_valor = ctk.CTkEntry(tab, placeholder_text="Ej: 118.14")
        self.entry_valor.grid(row=0, column=1, padx=12, pady=(12, 6), sticky="ew")
        self.entry_valor.insert(0, "118.14")

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=2, padx=12, pady=12, sticky="w")

        ctk.CTkButton(btn_frame, text="CALCULAR", width=140, height=40, command=self._calcular_valores).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(
            btn_frame, text="LIMPIAR", width=140, height=40, fg_color="gray40", hover_color="gray30",
            command=self._limpiar_valores,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_frame, text="📋 COPIAR PARA EXCEL", width=180, height=40,
            command=self._copiar_valores,
        ).pack(side="left")

        ctk.CTkLabel(
            tab,
            text="Distribuye el valor ingresado según los porcentajes de las cantidades compartidas.",
            text_color="gray60",
        ).grid(row=2, column=0, columnspan=2, padx=12, pady=(0, 6), sticky="w")

        self.text_valores = ctk.CTkTextbox(tab, height=280, font=ctk.CTkFont(family="Consolas", size=14))
        self.text_valores.grid(row=3, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="nsew")
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
