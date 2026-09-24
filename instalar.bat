@echo off
cd /d "%~dp0"
echo Instalando dependencias...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error al instalar. Verifique que Python este instalado.
    pause
    exit /b 1
)
echo.
echo Listo. Ejecute ejecutar.bat para abrir la aplicacion.
pause
