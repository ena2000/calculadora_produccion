@echo off
cd /d "%~dp0"
if "%~1"=="" (
    echo Uso: convertir_asistencia.bat "ruta\al\archivo.pdf"
    echo Ejemplo:
    echo   convertir_asistencia.bat "C:\RRHH\ASISTENCIA AGOSTO 2026.pdf"
    pause
    exit /b 1
)
python convertir_asistencia.py %*
pause
