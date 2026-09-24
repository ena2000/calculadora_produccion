@echo off
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo Si falta algun paquete, ejecute primero instalar.bat
    pause
)
