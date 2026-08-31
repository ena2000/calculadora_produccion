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


@dataclass(frozen=True)
class ReferenciaOrden:
    referencia: str
    cantidad: Decimal
    porcentaje: Decimal
    kg: Decimal | None
    tiempo_segundos: int
    tiempo_hms: str
    dig: Decimal | None
    tintas: FilaTinta | None


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


def generar_referencia(numero_orden: str, indice: int) -> str:
    """Genera referencia con dos dígitos: ORDEN.01, ORDEN.02, ..."""
    orden = numero_orden.strip()
    if not orden:
        raise ValueError("Debe ingresar el número de orden.")
    if indice < 1:
        raise ValueError("El índice de referencia debe ser mayor que cero.")
    return f"{orden}.{indice:02d}"


def parse_lista_cantidades(texto: str) -> List[str]:
    """Parsea cantidades separadas por comas, espacios o saltos de línea."""
    texto = texto.strip()
    if not texto:
        raise ValueError("No se encontraron cantidades en el texto pegado.")
    separadores = texto.replace("\n", ",").replace(";", ",").replace("\t", ",")
    partes = [p.strip() for p in separadores.split(",") if p.strip()]
    if not partes:
        raise ValueError("No se encontraron cantidades válidas.")
    return partes


def parse_tiempo_duracion(tiempo: str) -> int:
    """Convierte HH:MM:SS o HH:MM a segundos totales."""
    tiempo = tiempo.strip()
    if not tiempo:
        raise ValueError("Debe ingresar un tiempo total.")
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            parsed = datetime.strptime(tiempo, fmt)
            return parsed.hour * 3600 + parsed.minute * 60 + parsed.second
        except ValueError:
            continue
    raise ValueError(
        f"Tiempo inválido '{tiempo}'. Use HH:MM:SS (ej: 03:30:00) o HH:MM (ej: 03:30)."
    )


def formato_tiempo_hms(segundos: int) -> str:
    """Formatea segundos a HH:MM:SS."""
    if segundos < 0:
        raise ValueError("Los segundos no pueden ser negativos.")
    horas, resto = divmod(segundos, 3600)
    minutos, segs = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segs:02d}"


def duracion_entre_horas(hora_inicio: str, hora_fin: str) -> int:
    """Calcula duración total en segundos entre dos horas HH:MM."""
    inicio, fin = validar_rango_tiempo(hora_inicio, hora_fin)
    delta = fin - inicio
    return int(delta.total_seconds())


def distribuir_proporcional(
    valor_total: Decimal,
    cantidades: Sequence[Decimal],
    decimales: int | None = None,
) -> List[Decimal]:
    """
    Distribuye valor_total proporcionalmente.
    Si decimales está definido, ajusta la última referencia para cuadrar el total.
    """
    porcentajes = calcular_porcentajes(cantidades)
    exactos = [valor_total * pct for pct in porcentajes]

    if decimales is None:
        return exactos

    cuantizacion = Decimal("1").scaleb(-decimales)
    resultados: List[Decimal] = []
    acumulado = Decimal("0")

    for i, exacto in enumerate(exactos):
        if i == len(exactos) - 1:
            resultados.append(valor_total - acumulado)
        else:
            redondeado = exacto.quantize(cuantizacion, rounding=ROUND_HALF_UP)
            resultados.append(redondeado)
            acumulado += redondeado

    return resultados


def distribuir_tiempo_segundos(
    total_segundos: int,
    cantidades: Sequence[Decimal],
) -> List[int]:
    """Distribuye segundos proporcionalmente; la última referencia absorbe el ajuste."""
    if total_segundos <= 0:
        raise ValueError("El tiempo total debe ser mayor que cero.")

    porcentajes = calcular_porcentajes(cantidades)
    total_dec = Decimal(str(total_segundos))
    exactos = [total_dec * pct for pct in porcentajes]

    segundos: List[int] = []
    acumulado = 0

    for i, exacto in enumerate(exactos):
        if i == len(exactos) - 1:
            segundos.append(total_segundos - acumulado)
        else:
            sec = int(exacto.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            segundos.append(sec)
            acumulado += sec

    return segundos


def calcular_division_orden(
    numero_orden: str,
    cantidades: Sequence[str | float | int],
    kg_total: str | float | int | None = None,
    tiempo_total: str | None = None,
    hora_inicio: str | None = None,
    hora_fin: str | None = None,
    dig_total: str | float | int | None = None,
    consumos_tinta: dict[str, Decimal] | None = None,
    decimales_kg: int = 2,
    decimales_dig: int = 3,
) -> Tuple[List[ReferenciaOrden], Decimal]:
    """
    Divide una orden en referencias con cantidad, KG, tiempo y tintas proporcionales.
    """
    cantidades_dec = validar_cantidades(cantidades)
    porcentajes = calcular_porcentajes(cantidades_dec)
    total_cantidades = sum(cantidades_dec, Decimal("0"))

    # Tiempo total en segundos
    if tiempo_total and tiempo_total.strip():
        segundos_total = parse_tiempo_duracion(tiempo_total)
    elif hora_inicio and hora_fin:
        segundos_total = duracion_entre_horas(hora_inicio, hora_fin)
    else:
        raise ValueError("Debe ingresar tiempo total (HH:MM:SS) o rango inicio/fin.")

    segundos_por_ref = distribuir_tiempo_segundos(segundos_total, cantidades_dec)

    # KG
    kgs: List[Decimal | None]
    if kg_total is not None and str(kg_total).strip():
        try:
            kg_dec = Decimal(str(kg_total).strip())
        except Exception as exc:
            raise ValueError(f"KG total inválido: '{kg_total}'.") from exc
        if kg_dec < 0:
            raise ValueError("El KG total no puede ser negativo.")
        kgs = distribuir_proporcional(kg_dec, cantidades_dec, decimales_kg)
    else:
        kgs = [None] * len(cantidades_dec)

    # DIG
    digs: List[Decimal | None]
    if dig_total is not None and str(dig_total).strip():
        try:
            dig_dec = Decimal(str(dig_total).strip())
        except Exception as exc:
            raise ValueError(f"DIG total inválido: '{dig_total}'.") from exc
        digs = distribuir_proporcional(dig_dec, cantidades_dec, decimales_dig)
    else:
        digs = [None] * len(cantidades_dec)

    # Tintas
    filas_tinta: List[FilaTinta | None]
    if consumos_tinta:
        filas_tinta_list, _ = calcular_consumo_tintas(consumos_tinta, cantidades_dec)
        filas_tinta = list(filas_tinta_list)
    else:
        filas_tinta = [None] * len(cantidades_dec)

    referencias: List[ReferenciaOrden] = []
    for i, (cant, pct, seg, kg, dig, tinta) in enumerate(
        zip(cantidades_dec, porcentajes, segundos_por_ref, kgs, digs, filas_tinta),
        start=1,
    ):
        referencias.append(
            ReferenciaOrden(
                referencia=generar_referencia(numero_orden, i),
                cantidad=cant,
                porcentaje=pct,
                kg=kg,
                tiempo_segundos=seg,
                tiempo_hms=formato_tiempo_hms(seg),
                dig=dig,
                tintas=tinta,
            )
        )

    return referencias, total_cantidades


def formatear_kg(valor: Decimal) -> str:
    redondeado = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    texto = format(redondeado, "f")
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto


def texto_excel_orden(referencias: Sequence[ReferenciaOrden], incluir_kg: bool = True) -> str:
    """Genera texto tabulado REFERENCIA | CANTIDAD | KG | TIEMPO para Excel."""
    lineas: List[str] = []
    for ref in referencias:
        partes = [ref.referencia, str(int(ref.cantidad) if ref.cantidad == int(ref.cantidad) else ref.cantidad)]
        if incluir_kg and ref.kg is not None:
            partes.append(formatear_kg(ref.kg))
        elif incluir_kg:
            partes.append("")
        partes.append(ref.tiempo_hms)
        lineas.append("\t".join(partes))
    return "\n".join(lineas)


def texto_excel_orden_tintas(referencias: Sequence[ReferenciaOrden]) -> str:
    lineas: List[str] = []
    for ref in referencias:
        if ref.tintas is None:
            continue
        partes: List[str] = []
        for nombre, valor in ref.tintas.valores:
            partes.append(nombre)
            partes.append(formatear_tinta(valor))
        lineas.append("\t".join(partes))
    return "\n".join(lineas)


def calcular_division_tiempos(
    hora_inicio: str,
    hora_fin: str,
    cantidades: Sequence[str | float | int],
) -> Tuple[List[SegmentoTiempo], Decimal]:
    inicio, fin = validar_rango_tiempo(hora_inicio, hora_fin)
    cantidades_dec = validar_cantidades(cantidades)
    porcentajes = calcular_porcentajes(cantidades_dec)

    segundos_total = duracion_entre_horas(hora_inicio, hora_fin)
    segundos_por_ref = distribuir_tiempo_segundos(segundos_total, cantidades_dec)

    segmentos: List[SegmentoTiempo] = []
    cursor = inicio

    for cantidad, pct, seg in zip(cantidades_dec, porcentajes, segundos_por_ref):
        delta = timedelta(seconds=seg)
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
    resultados = distribuir_proporcional(valor_dec, cantidades_dec, decimales=3)
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
