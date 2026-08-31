"""Lógica matemática para la Calculadora de Producción."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Sequence, Tuple

# Colores de tinta en orden fijo para resultados
COLORES_TINTA: Tuple[Tuple[str, str], ...] = (
    ("DIG CYAN", "cyan"),
    ("DIG MAGENTA", "magenta"),
    ("DIG YELLOW", "yellow"),
    ("DIG BLACK", "black"),
    ("DIG ORANGE", "orange"),
    ("DIG VIOLET", "violet"),
)


@dataclass(frozen=True)
class SegmentoTiempo:
    inicio: str
    fin: str
    cantidad: Decimal
    porcentaje: Decimal


@dataclass(frozen=True)
class FilaTinta:
    valores: Tuple[Tuple[str, Decimal], ...]


def _parse_hora(hora: str) -> datetime:
    """Convierte 'HH:MM' a datetime base (fecha arbitraria)."""
    hora = hora.strip()
    try:
        return datetime.strptime(hora, "%H:%M")
    except ValueError as exc:
        raise ValueError(f"Hora inválida '{hora}'. Use el formato HH:MM (ej: 16:20).") from exc


def _formato_hora(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def validar_rango_tiempo(hora_inicio: str, hora_fin: str) -> Tuple[datetime, datetime]:
    inicio = _parse_hora(hora_inicio)
    fin = _parse_hora(hora_fin)
    if fin <= inicio:
        raise ValueError("La hora final debe ser posterior a la hora de inicio.")
    return inicio, fin


def validar_cantidades(cantidades: Sequence[str | float | int]) -> List[Decimal]:
    if not cantidades:
        raise ValueError("Debe ingresar al menos una cantidad de producción.")

    resultado: List[Decimal] = []
    for i, raw in enumerate(cantidades, start=1):
        texto = str(raw).strip()
        if not texto:
            raise ValueError(f"La cantidad #{i} está vacía.")
        try:
            valor = Decimal(texto)
        except Exception as exc:
            raise ValueError(f"Cantidad inválida en fila #{i}: '{texto}'.") from exc
        if valor <= 0:
            raise ValueError(f"La cantidad #{i} debe ser mayor que 0.")
        resultado.append(valor)
    return resultado


def calcular_porcentajes(cantidades: Sequence[Decimal]) -> List[Decimal]:
    total = sum(cantidades, Decimal("0"))
    if total == 0:
        raise ValueError("La suma de cantidades no puede ser cero.")
    return [c / total for c in cantidades]


def calcular_division_tiempos(
    hora_inicio: str,
    hora_fin: str,
    cantidades: Sequence[str | float | int],
) -> Tuple[List[SegmentoTiempo], Decimal]:
    inicio, fin = validar_rango_tiempo(hora_inicio, hora_fin)
    cantidades_dec = validar_cantidades(cantidades)
    porcentajes = calcular_porcentajes(cantidades_dec)

    duracion_total = fin - inicio
    duracion_segundos = Decimal(str(duracion_total.total_seconds()))

    segmentos: List[SegmentoTiempo] = []
    cursor = inicio

    for cantidad, pct in zip(cantidades_dec, porcentajes):
        segundos_segmento = duracion_segundos * pct
        delta = timedelta(seconds=float(segundos_segmento))
        fin_segmento = cursor + delta
        segmentos.append(
            SegmentoTiempo(
                inicio=_formato_hora(cursor),
                fin=_formato_hora(fin_segmento),
                cantidad=cantidad,
                porcentaje=pct,
            )
        )
        cursor = fin_segmento

    # Ajustar último segmento para coincidir exactamente con hora final
    if segmentos:
        ultimo = segmentos[-1]
        segmentos[-1] = SegmentoTiempo(
            inicio=ultimo.inicio,
            fin=_formato_hora(fin),
            cantidad=ultimo.cantidad,
            porcentaje=ultimo.porcentaje,
        )

    total = sum(cantidades_dec, Decimal("0"))
    return segmentos, total


def formatear_porcentaje(pct: Decimal) -> str:
    valor = (pct * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    texto = format(valor.normalize(), "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return f"{texto}%"


def validar_valor_tinta(valor: str, nombre: str) -> Decimal:
    texto = valor.strip()
    if not texto:
        return Decimal("0")
    try:
        dec = Decimal(texto)
    except Exception as exc:
        raise ValueError(f"Valor inválido para {nombre}: '{texto}'.") from exc
    if dec < 0:
        raise ValueError(f"El valor de {nombre} no puede ser negativo.")
    return dec


def calcular_consumo_tintas(
    consumos: dict[str, Decimal],
    cantidades: Sequence[str | float | int],
) -> Tuple[List[FilaTinta], List[Decimal]]:
    cantidades_dec = validar_cantidades(cantidades)
    porcentajes = calcular_porcentajes(cantidades_dec)

    filas: List[FilaTinta] = []
    for pct in porcentajes:
        fila_valores: List[Tuple[str, Decimal]] = []
        for nombre, clave in COLORES_TINTA:
            consumo = consumos.get(clave, Decimal("0"))
            base = consumo / Decimal("1000")
            valor = base * pct
            fila_valores.append((nombre, valor))
        filas.append(FilaTinta(valores=tuple(fila_valores)))

    return filas, porcentajes


def formatear_tinta(valor: Decimal) -> str:
    """Formatea valor de tinta con hasta 6 decimales, sin ceros finales."""
    redondeado = valor.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    texto = format(redondeado, "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto


def calcular_distribucion_valor(
    valor: str | float | int,
    cantidades: Sequence[str | float | int],
) -> Tuple[List[Decimal], List[Decimal]]:
    texto = str(valor).strip()
    if not texto:
        raise ValueError("Debe ingresar un valor para distribuir.")
    try:
        valor_dec = Decimal(texto)
    except Exception as exc:
        raise ValueError(f"Valor inválido: '{texto}'.") from exc

    cantidades_dec = validar_cantidades(cantidades)
    porcentajes = calcular_porcentajes(cantidades_dec)
    resultados = [valor_dec * pct for pct in porcentajes]
    return resultados, porcentajes


def formatear_valor_distribuido(valor: Decimal) -> str:
    redondeado = valor.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
    texto = format(redondeado, "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto


def texto_excel_tiempos(segmentos: Sequence[SegmentoTiempo]) -> str:
    lineas = [f"{s.inicio}\t{s.fin}" for s in segmentos]
    return "\n".join(lineas)


def texto_excel_tintas(filas: Sequence[FilaTinta]) -> str:
    lineas: List[str] = []
    for fila in filas:
        partes: List[str] = []
        for nombre, valor in fila.valores:
            partes.append(nombre)
            partes.append(formatear_tinta(valor))
        lineas.append("\t".join(partes))
    return "\n".join(lineas)


def texto_excel_valores(valores: Sequence[Decimal]) -> str:
    return "\n".join(formatear_valor_distribuido(v) for v in valores)
