"""Pruebas de los casos de uso documentados."""

from decimal import Decimal

from calculos import (
    calcular_consumo_tintas,
    calcular_division_orden,
    calcular_division_tiempos,
    calcular_distribucion_valor,
    calcular_intervalos_tiempo,
    duracion_entre_horas,
    formatear_kg,
    formatear_tinta,
    formatear_valor_distribuido,
    generar_referencia,
    texto_excel_orden,
    texto_excel_tiempos,
    texto_excel_tintas,
)

CANTIDADES_32 = [
    200, 100, 100, 200, 200, 200, 200, 200, 100, 200, 200, 300, 100, 100, 300, 400,
    300, 100, 100, 100, 100, 200, 100, 100, 100, 300, 300, 200, 100, 100, 100, 100,
]

CANTIDADES_4 = [200, 100, 100, 200]


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise AssertionError(f"{msg}\n  Esperado: {expected}\n  Obtenido: {actual}")


def test_tiempo_caso_1():
    segs, total = calcular_division_tiempos("16:20", "19:00", [10000, 10000, 5000])
    assert_eq(total, Decimal("25000"))
    assert_eq([(s.inicio, s.fin) for s in segs], [
        ("16:20:00", "17:24:00"),
        ("17:24:00", "18:28:00"),
        ("18:28:00", "19:00:00"),
    ], "Caso tiempo 16:20-19:00 acumulativo")


def test_tiempo_caso_2():
    segs, _ = calcular_division_tiempos("14:20", "16:50", [10000, 5000, 10000])
    assert_eq([(s.inicio, s.fin) for s in segs], [
        ("14:20:00", "15:20:00"),
        ("15:20:00", "15:50:00"),
        ("15:50:00", "16:50:00"),
    ], "Caso tiempo 14:20-16:50 acumulativo")


def test_valor_caso():
    valores, _ = calcular_distribucion_valor("118.14", [10000, 10000, 5000])
    texto = [formatear_valor_distribuido(v) for v in valores]
    assert_eq(texto, ["47.256", "47.256", "23.628"], "Caso valor 118.14")


def test_tinta_caso():
    consumos = {
        "cyan": Decimal("236.39"),
        "magenta": Decimal("666.89"),
        "yellow": Decimal("706.20"),
        "black": Decimal("994.07"),
        "orange": Decimal("441.15"),
        "violet": Decimal("42.08"),
    }
    filas, _ = calcular_consumo_tintas(consumos, [10000, 10000, 5000])

    cyan = [formatear_tinta(f.valores[0][1]) for f in filas]
    assert_eq(cyan, ["0.094556", "0.094556", "0.047278"], "Cyan")


def test_orden_32_referencias():
    consumos = {
        "cyan": Decimal("11.34"),
        "magenta": Decimal("30.75"),
        "yellow": Decimal("36.86"),
        "black": Decimal("17.52"),
        "orange": Decimal("25.67"),
        "violet": Decimal("3.11"),
    }
    refs, total = calcular_division_orden(
        "202608004113",
        CANTIDADES_32,
        kg_total="14.76",
        hora_inicio="11:30",
        hora_fin="15:00",
        consumos_tinta=consumos,
    )

    assert_eq(len(refs), 32)
    assert_eq(total, Decimal("5500"))
    assert_eq(refs[0].referencia, "202608004113.01")
    assert_eq(refs[31].referencia, "202608004113.32")
    assert_eq(refs[0].cantidad, Decimal("200"))
    assert_eq(refs[0].tiempo_inicio, "11:30:00")
    assert_eq(refs[31].tiempo_fin, "15:00:00")
    assert_eq(refs[0].tiempo_hms, "00:07:38")
    assert_eq(formatear_kg(sum(r.kg for r in refs)), "14.76")


def test_orden_4_referencias():
    refs, total = calcular_division_orden(
        "202608004113",
        CANTIDADES_4,
        kg_total="10",
        hora_inicio="15:50",
        hora_fin="18:00",
    )
    assert_eq(len(refs), 4)
    assert_eq(total, Decimal("600"))
    assert_eq(refs[0].referencia, "202608004113.01")
    assert_eq(refs[3].referencia, "202608004113.04")
    assert_eq(refs[0].tiempo_inicio, "15:50:00")
    assert_eq(refs[3].tiempo_fin, "18:00:00")
    assert_eq(sum(r.tiempo_segundos for r in refs), 7800)


def test_cambio_de_dia():
    assert_eq(duracion_entre_horas("19:00", "01:00"), 21600)
    segs, _ = calcular_intervalos_tiempo("19:00", "01:00", CANTIDADES_4)
    assert_eq(segs[0].inicio, "19:00:00")
    assert_eq(segs[-1].fin, "01:00:00")
    assert_eq(segs[1].inicio, segs[0].fin)
    dur_100 = 360 * 60 * 100 / 600
    assert abs(segs[1].duracion_segundos - dur_100) <= 1


def test_intervalos_consecutivos_32():
    segs, _ = calcular_intervalos_tiempo("15:50", "18:00", CANTIDADES_32)
    assert_eq(segs[0].inicio, "15:50:00")
    assert_eq(segs[-1].fin, "18:00:00")
    for i in range(len(segs) - 1):
        if segs[i].fin != segs[i + 1].inicio:
            raise AssertionError(f"Hueco entre ref {i+1} y {i+2}: {segs[i].fin} != {segs[i+1].inicio}")
    assert_eq(sum(s.duracion_segundos for s in segs), 7800)


def test_kg_698():
    refs, _ = calcular_division_orden(
        "202608004113", CANTIDADES_32, kg_total="6.98", tiempo_total="02:10:00"
    )
    assert_eq(formatear_kg(sum(r.kg for r in refs)), "6.98")


def test_excel_separadores():
    segs, _ = calcular_division_tiempos("16:20", "19:00", [10000, 10000, 5000])
    texto = texto_excel_tiempos(segs)
    assert "\t" in texto
    assert "Inicio" not in texto

    refs, _ = calcular_division_orden(
        "202608004113", CANTIDADES_4, kg_total="10", hora_inicio="15:50", hora_fin="18:00"
    )
    excel = texto_excel_orden(refs)
    assert excel.split("\t")[0] == "202608004113.01"
    assert "15:50:00" in excel.split("\n")[0]


if __name__ == "__main__":
    test_tiempo_caso_1()
    test_tiempo_caso_2()
    test_valor_caso()
    test_tinta_caso()
    test_orden_32_referencias()
    test_orden_4_referencias()
    test_cambio_de_dia()
    test_intervalos_consecutivos_32()
    test_kg_698()
    test_excel_separadores()
    print("Todas las pruebas pasaron correctamente.")
