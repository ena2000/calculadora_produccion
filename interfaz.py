"""Interfaz gráfica de la Calculadora de Producción con CustomTkinter."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import List, Optional

import customtkinter as ctk

from calculos import (
    COLORES_TINTA,
    FilaTinta,
    ReferenciaOrden,
    SegmentoTiempo,
    calcular_consumo_tintas,
    calcular_division_orden,
    calcular_division_tiempos,
    calcular_distribucion_valor,
    formatear_kg,
    formatear_porcentaje,
    formatear_tinta,
    formatear_valor_distribuido,
    formato_tiempo_hms,
    parse_lista_cantidades,
    texto_excel_orden,
    texto_excel_orden_tintas,
    texto_excel_tiempos,
    texto_excel_tintas,
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
        self.geometry("920x780")
        self.minsize(820, 680)

        self._cantidad_entries: List[ctk.CTkEntry] = []
        self._segmentos_tiempo: List[SegmentoTiempo] = []
        self._filas_tinta: List[FilaTinta] = []
        self._valores_distribuidos: List = []
        self._referencias_orden: List[ReferenciaOrden] = []

        self._ink_entries: dict[str, ctk.CTkEntry] = {}
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

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=2, column=0, padx=20, pady=(0, 16), sticky="nsew")
        self.grid_rowconfigure(2, weight=1)

        self.tab_orden = self.tabview.add("📦 División de órdenes")
        self.tab_tiempos = self.tabview.add("⏱️ División de tiempos")
        self.tab_tintas = self.tabview.add("🎨 Consumo de tintas")
        self.tab_valores = self.tabview.add("🧮 Distribución de valores")

        self._construir_tab_orden()
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
    def _construir_tab_orden(self) -> None:
        tab = self.tab_orden
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(8, weight=1)

        ctk.CTkLabel(tab, text="Número de orden:").grid(
            row=0, column=0, padx=12, pady=(12, 6), sticky="w"
        )
        self.entry_orden = ctk.CTkEntry(tab, placeholder_text="202608004113")
        self.entry_orden.grid(row=0, column=1, padx=12, pady=(12, 6), sticky="ew")

        ctk.CTkLabel(tab, text="KG total:").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        self.entry_kg_total = ctk.CTkEntry(tab, placeholder_text="Ej: 15.4")
        self.entry_kg_total.grid(row=1, column=1, padx=12, pady=6, sticky="ew")

        ctk.CTkLabel(tab, text="DIG total (opcional):").grid(
            row=2, column=0, padx=12, pady=6, sticky="w"
        )
        self.entry_dig_total = ctk.CTkEntry(tab, placeholder_text="Opcional")
        self.entry_dig_total.grid(row=2, column=1, padx=12, pady=6, sticky="ew")

        tiempo_frame = ctk.CTkFrame(tab, fg_color="transparent")
        tiempo_frame.grid(row=3, column=0, columnspan=2, padx=12, pady=6, sticky="ew")
        tiempo_frame.grid_columnconfigure(1, weight=1)
        tiempo_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(tiempo_frame, text="Tiempo total (HH:MM:SS):").grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )
        self.entry_tiempo_total = ctk.CTkEntry(tiempo_frame, placeholder_text="03:30:00")
        self.entry_tiempo_total.grid(row=0, column=1, sticky="ew")

        ctk.CTkLabel(tiempo_frame, text="  o  Inicio:").grid(row=0, column=2, padx=8, sticky="w")
        self.entry_orden_inicio = ctk.CTkEntry(tiempo_frame, width=80, placeholder_text="11:30")
        self.entry_orden_inicio.grid(row=0, column=3, sticky="w")

        ctk.CTkLabel(tiempo_frame, text="Fin:").grid(row=0, column=4, padx=8, sticky="w")
        self.entry_orden_fin = ctk.CTkEntry(tiempo_frame, width=80, placeholder_text="15:00")
        self.entry_orden_fin.grid(row=0, column=5, sticky="w")
        ctk.CTkLabel(
            tab,
            text="Si fin < inicio (ej. 19:00 → 01:00) se asume cruce de medianoche.",
            text_color="gray60",
        ).grid(row=4, column=0, columnspan=2, padx=12, pady=(0, 4), sticky="w")

        tintas_frame = ctk.CTkFrame(tab)
        tintas_frame.grid(row=5, column=0, columnspan=2, padx=12, pady=6, sticky="ew")
        tintas_frame.grid_columnconfigure((1, 3, 5), weight=1)

        ctk.CTkLabel(
            tintas_frame,
            text="Tintas totales (opcional, ÷1000 automático):",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, columnspan=6, padx=8, pady=(8, 4), sticky="w")

        ink_defaults = {
            "cyan": "11.34", "magenta": "30.75", "yellow": "36.86",
            "black": "17.52", "orange": "25.67", "violet": "3.11",
        }
        for i, (nombre, clave) in enumerate(COLORES_TINTA):
            fila, col = divmod(i, 3)
            base_col = col * 2
            ctk.CTkLabel(tintas_frame, text=f"{nombre.split()[1]}:").grid(
                row=fila + 1, column=base_col, padx=(8, 4), pady=3, sticky="w"
            )
            entry = ctk.CTkEntry(tintas_frame, placeholder_text="0")
            entry.grid(row=fila + 1, column=base_col + 1, padx=(0, 8), pady=3, sticky="ew")
            if clave in ink_defaults:
                entry.insert(0, ink_defaults[clave])
            self._orden_ink_entries[clave] = entry

        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.grid(row=6, column=0, columnspan=2, padx=12, pady=8, sticky="w")

        ctk.CTkButton(btn_frame, text="CALCULAR", width=140, height=40, command=self._calcular_orden).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(
            btn_frame, text="LIMPIAR", width=140, height=40, fg_color="gray40", hover_color="gray30",
            command=self._limpiar_orden,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_frame, text="📋 COPIAR PARA EXCEL", width=180, height=40,
            command=self._copiar_orden,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btn_frame, text="📋 COPIAR TINTAS", width=160, height=40,
            command=self._copiar_orden_tintas,
        ).pack(side="left")

        self.lbl_resumen_orden = ctk.CTkLabel(tab, text="Referencias: —", font=ctk.CTkFont(weight="bold"))
        self.lbl_resumen_orden.grid(row=7, column=0, columnspan=2, padx=12, pady=(0, 6), sticky="w")

        self.text_orden = ctk.CTkTextbox(tab, height=240, font=ctk.CTkFont(family="Consolas", size=12))
        self.text_orden.grid(row=8, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="nsew")
        tab.grid_rowconfigure(8, weight=1)
        self.text_orden.insert(
            "1.0",
            "Referencia\tCantidad\tKG\tInicio\tFin\tDuración\tDIG\n",
        )
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
            kg = self.entry_kg_total.get().strip() or None
            dig = self.entry_dig_total.get().strip() or None
            tiempo_total = self.entry_tiempo_total.get().strip() or None
            hora_ini = self.entry_orden_inicio.get().strip() or None
            hora_fin = self.entry_orden_fin.get().strip() or None
            consumos = self._obtener_consumos_orden()

            referencias, total = calcular_division_orden(
                self.entry_orden.get(),
                self._obtener_cantidades(),
                kg_total=kg,
                tiempo_total=tiempo_total,
                hora_inicio=hora_ini,
                hora_fin=hora_fin,
                dig_total=dig,
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

            lineas = ["Referencia\tCantidad\tKG\tInicio\tFin\tDuración\tDIG"]
            for ref in referencias:
                kg_txt = formatear_kg(ref.kg) if ref.kg is not None else "—"
                dig_txt = formatear_valor_distribuido(ref.dig) if ref.dig is not None else "—"
                cant_txt = str(int(ref.cantidad) if ref.cantidad == int(ref.cantidad) else ref.cantidad)
                ini_txt = ref.tiempo_inicio or "—"
                fin_txt = ref.tiempo_fin or "—"
                lineas.append(
                    f"{ref.referencia}\t{cant_txt}\t{kg_txt}\t{ini_txt}\t{fin_txt}\t"
                    f"{ref.tiempo_hms}\t{dig_txt}"
                )

            self.text_orden.configure(state="normal")
            self.text_orden.delete("1.0", "end")
            self.text_orden.insert("1.0", "\n".join(lineas))
            self.text_orden.configure(state="disabled")
        except ValueError as exc:
            messagebox.showerror("Error de validación", str(exc))

    def _limpiar_orden(self) -> None:
        self.entry_orden.delete(0, "end")
        self.entry_kg_total.delete(0, "end")
        self.entry_dig_total.delete(0, "end")
        self.entry_tiempo_total.delete(0, "end")
        self.entry_orden_inicio.delete(0, "end")
        self.entry_orden_fin.delete(0, "end")
        for entry in self._orden_ink_entries.values():
            entry.delete(0, "end")
        self._referencias_orden = []
        self.lbl_resumen_orden.configure(text="Referencias: —")
        self.text_orden.configure(state="normal")
        self.text_orden.delete("1.0", "end")
        self.text_orden.insert(
            "1.0",
            "Referencia\tCantidad\tKG\tInicio\tFin\tDuración\tDIG\n",
        )
        self.text_orden.configure(state="disabled")

    def _copiar_orden(self) -> None:
        if not self._referencias_orden:
            messagebox.showinfo("Sin datos", "Calcule primero la división de la orden.")
            return
        incluir_kg = any(r.kg is not None for r in self._referencias_orden)
        texto = texto_excel_orden(self._referencias_orden, incluir_kg=incluir_kg)
        copiar_al_portapapeles(texto, self)
        messagebox.showinfo("Copiado", "Tabla de orden copiada al portapapeles (sin encabezados).")

    def _copiar_orden_tintas(self) -> None:
        if not self._referencias_orden:
            messagebox.showinfo("Sin datos", "Calcule primero la división de la orden.")
            return
        if not any(r.tintas for r in self._referencias_orden):
            messagebox.showinfo("Sin tintas", "Ingrese valores de tinta antes de calcular.")
            return
        texto = texto_excel_orden_tintas(self._referencias_orden)
        copiar_al_portapapeles(texto, self)
        messagebox.showinfo("Copiado", "Tintas por referencia copiadas al portapapeles.")

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

        ctk.CTkLabel(tab, text="Hora final (HH:MM, cruce de día si fin < inicio):").grid(
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
        self.text_tiempos.insert("1.0", "Inicio\tFin\tDuración\tCantidad\t%\n")
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

            lineas = ["Inicio\tFin\tDuración\tCantidad\t%"]
            for seg_obj in segmentos:
                lineas.append(
                    f"{seg_obj.inicio}\t{seg_obj.fin}\t{seg_obj.duracion_hms}\t"
                    f"{seg_obj.cantidad}\t{formatear_porcentaje(seg_obj.porcentaje)}"
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
        self.text_tiempos.insert("1.0", "Inicio\tFin\tDuración\tCantidad\t%\n")
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
