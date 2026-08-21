@echo off
echo =====================================
echo   Sistema de Metro Autonomo - EAFIT
echo =====================================
echo.

echo Verificando Python...
python --version
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    echo Por favor instala Python 3.7 o superior desde https://www.python.org/
    pause
    exit /b 1
)

echo.
echo Opciones disponibles:
echo 1. Ejecutar sistema principal
echo 2. Ejecutar pruebas
echo 3. Ejecutar clientes simulados
echo 4. Mostrar informacion del sistema
echo 5. Salir
echo.

set /p choice="Selecciona una opcion (1-5): "

if "%choice%"=="1" (
    echo Iniciando sistema principal...
    python main.py
) else if "%choice%"=="2" (
    echo Ejecutando pruebas...
    python tests/test_metro_system.py
    pause
) else if "%choice%"=="3" (
    echo Ejecutando clientes simulados...
    python src/communication/client_simulator.py
) else if "%choice%"=="4" (
    echo Mostrando informacion del sistema...
    python utils.py info
    pause
) else if "%choice%"=="5" (
    echo Saliendo...
    exit /b 0
) else (
    echo Opcion invalida
    pause
)

echo.
echo Presiona cualquier tecla para continuar...
pause