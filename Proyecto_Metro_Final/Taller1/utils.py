#!/usr/bin/env python3
"""
Utilidades para el Sistema de Metro Autónomo
"""

import os
import sys
import subprocess
import time
import signal

def check_python_version():
    """Verifica que Python sea la versión correcta"""
    if sys.version_info < (3, 7):
        print("ERROR: Se requiere Python 3.7 o superior")
        print(f"Versión actual: {sys.version}")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def run_system():
    """Ejecuta el sistema principal"""
    print("🚀 Iniciando Sistema de Metro Autónomo...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Sistema detenido por el usuario")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando el sistema: {e}")

def run_tests():
    """Ejecuta todas las pruebas del sistema"""
    print("🧪 Ejecutando pruebas del sistema...")
    try:
        result = subprocess.run([sys.executable, "tests/test_metro_system.py"], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("ERRORES:")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error ejecutando pruebas: {e}")
        return False

def run_client_simulator(num_clients=3):
    """Ejecuta el simulador de clientes"""
    print(f"👥 Iniciando {num_clients} clientes simulados...")
    try:
        subprocess.run([sys.executable, "src/communication/client_simulator.py", str(num_clients)], 
                      check=True)
    except KeyboardInterrupt:
        print("\n🛑 Clientes detenidos por el usuario")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando clientes: {e}")

def show_system_info():
    """Muestra información del sistema"""
    print("📊 Información del Sistema")
    print("=" * 50)
    print(f"Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"Plataforma: {sys.platform}")
    print(f"Directorio actual: {os.getcwd()}")
    print(f"Archivos principales:")
    
    important_files = [
        "main.py",
        "config/settings.py", 
        "src/metro/metro_system.py",
        "src/communication/network_manager.py",
        "src/control/central_controller.py"
    ]
    
    for file in important_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ❌ {file} (FALTANTE)")

def show_network_info():
    """Muestra información de configuración de red"""
    try:
        from config.settings import SYSTEM_CONFIG
        network_config = SYSTEM_CONFIG['network']
        
        print("🌐 Configuración de Red")
        print("=" * 30)
        print(f"Servidor: {network_config['server_host']}:{network_config['server_port']}")
        print(f"Protocolo: {network_config['protocol']}")
        print(f"Máx. conexiones: {network_config['max_connections']}")
        print(f"Timeout: {network_config['timeout']}s")
        
    except ImportError:
        print("❌ No se pudo cargar la configuración")

def main():
    """Función principal del utilitario"""
    if len(sys.argv) < 2:
        print("🚇 Sistema de Metro Autónomo - Utilidades")
        print("=" * 50)
        print("Uso: python utils.py <comando>")
        print("\nComandos disponibles:")
        print("  run        - Ejecutar sistema principal")
        print("  test       - Ejecutar pruebas")
        print("  client [N] - Ejecutar N clientes (por defecto: 3)")
        print("  info       - Mostrar información del sistema")
        print("  network    - Mostrar configuración de red")
        print("  check      - Verificar instalación")
        return
    
    command = sys.argv[1].lower()
    
    if command == "run":
        if check_python_version():
            run_system()
    
    elif command == "test":
        if check_python_version():
            success = run_tests()
            if success:
                print("✅ Todas las pruebas pasaron")
            else:
                print("❌ Algunas pruebas fallaron")
    
    elif command == "client":
        if check_python_version():
            num_clients = 3
            if len(sys.argv) > 2:
                try:
                    num_clients = int(sys.argv[2])
                except ValueError:
                    print("❌ Número de clientes debe ser un entero")
                    return
            run_client_simulator(num_clients)
    
    elif command == "info":
        show_system_info()
    
    elif command == "network":
        show_network_info()
    
    elif command == "check":
        print("🔍 Verificando instalación...")
        if check_python_version():
            show_system_info()
            print("\n✅ Sistema listo para usar")
            print("💡 Ejecuta: python utils.py run")
    
    else:
        print(f"❌ Comando desconocido: {command}")
        print("💡 Usa: python utils.py para ver ayuda")

if __name__ == "__main__":
    main()