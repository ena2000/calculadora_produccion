"""Convierte un PDF de asistencia a Excel desde la linea de comandos."""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convierte PDF de asistencia a Excel con recargos 50%%, 25%% y 100%%."
    )
    parser.add_argument("pdf", help="Ruta del archivo PDF")
    parser.add_argument(
        "-o",
        "--salida",
        help="Ruta del Excel de salida (opcional, mismo nombre que el PDF)",
    )
    args = parser.parse_args()

    try:
        from asistencia_calculos import procesar_pdf_completo

        ruta, resumen = procesar_pdf_completo(args.pdf, args.salida)
        print(f"Excel creado: {ruta}")
        print(f"Operarios en resumen: {len(resumen)}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
