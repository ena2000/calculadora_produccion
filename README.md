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

### ⏱️ División de tiempos

Ingresa hora de inicio, hora final y las cantidades producidas. La aplicación calcula automáticamente los intervalos de tiempo proporcionales a cada cantidad.

**Ejemplo:** 16:20 → 19:00 con cantidades 10000, 10000, 5000:

```
16:20 → 17:24  (40%)
17:24 → 18:28  (40%)
18:28 → 19:00  (20%)
```

### 🎨 Consumo de tintas

Ingresa los consumos totales de DIG CYAN, MAGENTA, YELLOW, BLACK, ORANGE y VIOLET. Usa las mismas cantidades de producción para distribuir proporcionalmente cada tinta.

### 🧮 Distribución de valores

Distribuye un valor numérico (ej: 118.14) según los porcentajes de las cantidades.

### Cantidades compartidas

Las cantidades de producción se ingresan una sola vez en la parte superior y se reutilizan en las tres pestañas. Puedes agregar o eliminar cantidades dinámicamente.

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
