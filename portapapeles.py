"""Utilidades para copiar resultados al portapapeles."""

from __future__ import annotations

import tkinter as tk
from typing import Optional


def copiar_al_portapapeles(texto: str, ventana: Optional[tk.Misc] = None) -> None:
    """Copia texto al portapapeles del sistema."""
    if ventana is not None:
        ventana.clipboard_clear()
        ventana.clipboard_append(texto)
        ventana.update()
        return

    root = tk.Tk()
    root.withdraw()
    root.clipboard_clear()
    root.clipboard_append(texto)
    root.update()
    root.destroy()
