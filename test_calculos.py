"""Pruebas de los casos de uso documentados."""

from decimal import Decimal

from calculos import (
    calcular_consumo_tintas,
    calcular_division_orden,
    calcular_division_tiempos,
    calcular_distribucion_valor,
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


def assert_eq(actual, expected, msg=""):
    if actual != expected:
        raise AssertionError(f"{msg}\n  Esperado: {expected}\n  Obtenido: {actual}")


def test_tiempo_caso_1():
    segs, total = calcular_division_tiempos("16:20", "19:00", [10000, 10000, 5000])
    assert_eq(total, Decimal("25000"))
    assert_eq([(s.inicio, s.fin) for s in segs], [
        ("16:20", "17:24"),
        ("17:24", "18:28"),
        ("18:28", "19:00"),
    ], "Caso tiempo 16:20-19:00")


def test_tiempo_caso_2():
    segs, _ = calcular_division_tiempos("14:20", "16:50", [10000, 5000, 10000])
    assert_eq([(s.inicio, s.fin) for s in segs], [
        ("14:20", "15:20"),
        ("15:20", "15:50"),
        ("15:50", "16:50"),
    ], "Caso tiempo 14:20-16:50")


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
    magenta = [formatear_tinta(f.valores[1][1]) for f in filas]
    yellow = [formatear_tinta(f.valores[2][1]) for f in filas]
    black = [formatear_tinta(f.valores[3][1]) for f in filas]
    orange = [formatear_tinta(f.valores[4][1]) for f in filas]
    violet = [formatear_tinta(f.valores[5][1]) for f in filas]

    assert_eq(cyan, ["0.094556", "0.094556", "0.047278"], "Cyan")
    assert_eq(magenta, ["0.266756", "0.266756", "0.133378"], "Magenta")
    assert_eq(yellow, ["0.28248", "0.28248", "0.14124"], "Yellow")
    assert_eq(black, ["0.397628", "0.397628", "0.198814"], "Black")
    assert_eq(orange, ["0.17646", "0.17646", "0.08823"], "Orange")
    assert_eq(violet, ["0.016832", "0.016832", "0.008416"], "Violet")


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
        kg_total="15.4",
        hora_inicio="11:30",
        hora_fin="15:00",
        consumos_tinta=consumos,
    )

    assert_eq(len(refs), 32, "Debe haber 32 referencias")
    assert_eq(total, Decimal("5500"), "Total cantidades")
    assert_eq(refs[0].referencia, "202608004113.01")
    assert_eq(refs[31].referencia, "202608004113.32")
    assert_eq(refs[0].cantidad, Decimal("200"))
    assert_eq(refs[1].cantidad, Decimal("100"))
    assert_eq(refs[2].cantidad, Decimal("100"))

    suma_tiempo = sum(r.tiempo_segundos for r in refs)
    assert_eq(suma_tiempo, 12600, "Suma tiempo = 3h30m")

    assert_eq(refs[0].tiempo_hms, "00:07:38", "Tiempo ref .01")
    assert_eq(refs[1].tiempo_hms, "00:03:49", "Tiempo ref .02")

    suma_kg = sum(r.kg for r in refs)
    assert_eq(formatear_kg(suma_kg), "15.4", "Suma KG")

    cyan = [formatear_tinta(r.tintas.valores[0][1]) for r in refs]
    assert_eq(cyan[0], "0.000412")
    assert_eq(cyan[31], formatear_tinta(Decimal("11.34") / 1000 * Decimal("100") / Decimal("5500")))

    for i in range(32):
        assert_eq(refs[i].referencia, generar_referencia("202608004113", i + 1))


def test_excel_separadores():
    segs, _ = calcular_division_tiempos("16:20", "19:00", [10000, 10000, 5000])
    texto = texto_excel_tiempos(segs)
    assert "\t" in texto
    assert "Inicio" not in texto

    consumos = {"cyan": Decimal("236.39"), "magenta": Decimal("666.89"),
                "yellow": Decimal("706.20"), "black": Decimal("994.07"),
                "orange": Decimal("441.15"), "violet": Decimal("42.08")}
    filas, _ = calcular_consumo_tintas(consumos, [10000, 10000, 5000])
    texto_tinta = texto_excel_tintas(filas)
    primera = texto_tinta.split("\n")[0]
    assert "\t" in primera

    refs, _ = calcular_division_orden(
        "202608004113", CANTIDADES_32, kg_total="15.4", tiempo_total="03:30:00"
    )
    excel = texto_excel_orden(refs)
    assert excel.count("\n") == 31
    assert excel.split("\t")[0] == "202608004113.01"


if __name__ == "__main__":
    test_tiempo_caso_1()
    test_tiempo_caso_2()
    test_valor_caso()
    test_tinta_caso()
    test_orden_32_referencias()
    test_excel_separadores()
    print("Todas las pruebas pasaron correctamente.")
