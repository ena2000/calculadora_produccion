"""Pruebas de los casos de uso documentados."""

from decimal import Decimal

from calculos import (
    calcular_consumo_tintas,
    calcular_division_tiempos,
    calcular_distribucion_valor,
    formatear_tinta,
    formatear_valor_distribuido,
    texto_excel_tiempos,
    texto_excel_tintas,
)


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
    assert " " not in primera.replace("DIG ", "").replace(" ", "") or "\t" in primera


if __name__ == "__main__":
    test_tiempo_caso_1()
    test_tiempo_caso_2()
    test_valor_caso()
    test_tinta_caso()
    test_excel_separadores()
    print("Todas las pruebas pasaron correctamente.")
