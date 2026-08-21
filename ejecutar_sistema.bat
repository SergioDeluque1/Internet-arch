@echo off
echo ====================================
echo SISTEMA DE METRO AUTONOMO - EAFIT
echo ====================================
echo.
echo Instrucciones:
echo 1. Ejecutar el servidor del metro
echo 2. Ejecutar el cliente GUI
echo.
echo Presiona cualquier tecla para continuar...
pause > nul

echo.
echo Iniciando servidor del metro...
cd /d "c:\General\Eafit\Semestre6\Telematica\Proyecto_Metro_Actualizado\Taller1"
start "Servidor Metro" cmd /k "python main.py"

echo.
echo Esperando 3 segundos para que inicie el servidor...
timeout /t 3 > nul

echo.
echo Iniciando cliente GUI...
cd /d "c:\General\Eafit\Semestre6\Telematica\Proyecto_Metro_Actualizado"
start "Cliente Metro GUI" cmd /k "python client_metro_json.py"

echo.
echo Sistema iniciado! Verifica las ventanas del servidor y cliente.
echo Presiona cualquier tecla para salir...
pause > nul