# Calculadora de Producción

Aplicación de escritorio 100% en Python para calcular divisiones proporcionales de tiempos de producción, consumo de tintas y distribución de valores. Diseñada para copiar resultados directamente en Excel.

## Requisitos

- Python 3.10 o superior
- Windows (probado), Linux o macOS

## Instalación

1. Clona o descarga este repositorio:

```bash
git clone https://github.com/TU_USUARIO/calculadora_produccion.git
cd calculadora_produccion
```

2. Crea un entorno virtual (recomendado):

```bash
python -m venv venv
venv\Scripts\activate
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Ejecutar la aplicación

```bash
python main.py
```

## Funcionalidades

### Pantalla principal

Divide la producción en referencias (`.01`, `.02`, …) con distribución proporcional de:

- **Cantidades** (arriba: generar referencias o pegar lista)
- **KG total** por referencia
- **Horario** solo con **inicio** y **fin** (HH:MM); cada referencia recibe su tramo
- **Tintas** del lote (valor crudo ÷ 1000 → reparto por cantidad). Los nombres **DIG CYAN**, **DIG MAGENTA**, etc. son etiquetas de Excel para tintas, no un campo “DIG total” aparte.

Use **📋 PEGAR CANTIDADES** para cargar listas separadas por comas.

Botones **COPIAR HORAS / KG / TINTAS** pegan en Excel solo la columna o fila que necesitas.

### 📋 Copiar para Excel

Cada módulo incluye un botón para copiar resultados al portapapeles usando tabulaciones (`\t`), listos para pegar en Excel sin encabezados.

## Estructura del proyecto

```
calculadora_produccion/
├── main.py              # Punto de entrada
├── calculos.py          # Lógica matemática
├── interfaz.py          # Interfaz gráfica (CustomTkinter)
├── portapapeles.py      # Copiar al portapapeles
├── test_calculos.py     # Pruebas de cálculos
├── requirements.txt
└── README.md
```

## Ejecutar pruebas

```bash
python test_calculos.py
```

## Crear ejecutable (.exe) para Windows

1. Instala PyInstaller:

```bash
pip install pyinstaller
```

2. Genera el ejecutable:

```bash
pyinstaller --onefile --windowed --name "CalculadoraProduccion" main.py
```

3. El archivo `.exe` estará en la carpeta `dist/`.

Para incluir el icono personalizado:

```bash
pyinstaller --onefile --windowed --icon=icono.ico --name "CalculadoraProduccion" main.py
```

## Validaciones

La aplicación valida:

- Formato de horas (HH:MM)
- Hora final posterior a hora inicial
- Cantidades vacías o menores/iguales a cero
- Valores de tinta inválidos
- División entre cero

## Precisión

Los cálculos mantienen precisión completa internamente usando `Decimal`. Los resultados se redondean solo al mostrarse en pantalla o al copiar.

## Licencia

Uso libre para fines personales y laborales.
