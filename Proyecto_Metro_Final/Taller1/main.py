#!/usr/bin/env python3
"""
Metro Autónomo - Sistema de Control y Comunicación
Proyecto de Telemática - EAFIT
"""

import sys
import threading
import time
from src.metro.metro_system import MetroSystem
from src.communication.network_manager import NetworkManager
from src.control.central_controller import CentralController
from config.settings import SYSTEM_CONFIG

def main():
    """Función principal del sistema de metro autónomo"""
    print("=" * 60)
    print("SISTEMA DE METRO AUTÓNOMO")
    print("Proyecto de Telemática - EAFIT")
    print("=" * 60)
    
    try:
        # Inicializar componentes del sistema
        print("Inicializando sistema...")
        
        # Crear instancias de los componentes principales
        network_manager = NetworkManager(SYSTEM_CONFIG['network'])
        central_controller = CentralController(SYSTEM_CONFIG['control'])
        metro_system = MetroSystem(SYSTEM_CONFIG['metro'], network_manager, central_controller)
        
        # Inicializar componentes
        network_manager.initialize()
        central_controller.initialize()
        metro_system.initialize()
        
        print("Sistema inicializado correctamente")
        
        # Iniciar hilos de ejecución
        threads = []
        
        # Hilo para el sistema de metro
        metro_thread = threading.Thread(target=metro_system.run, daemon=True)
        metro_thread.start()
        threads.append(metro_thread)
        
        # Hilo para el controlador central
        control_thread = threading.Thread(target=central_controller.run, daemon=True)
        control_thread.start()
        threads.append(control_thread)
        
        # Hilo para el administrador de red
        network_thread = threading.Thread(target=network_manager.run, daemon=True)
        network_thread.start()
        threads.append(network_thread)
        
        print("Todos los servicios están ejecutándose...")
        print("Presiona Ctrl+C para detener el sistema")
        
        # Mantener el programa ejecutándose
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nDeteniendo sistema...")
        metro_system.stop()
        central_controller.stop()
        network_manager.stop()
        print("Sistema detenido correctamente")
        
    except Exception as e:
        print(f"Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()