"""
Pruebas para el Sistema de Metro Autónomo
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch
import sys
import os

# Añadir el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.metro.metro_system import MetroSystem, Station, Train
from src.communication.network_manager import NetworkManager
from src.control.central_controller import CentralController
from config.settings import SYSTEM_CONFIG

class TestMetroSystem(unittest.TestCase):
    """Pruebas para el sistema de metro"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.mock_network = Mock()
        self.mock_controller = Mock()
        self.metro_system = MetroSystem(
            SYSTEM_CONFIG['metro'],
            self.mock_network,
            self.mock_controller
        )
        self.metro_system.initialize()
    
    def test_station_creation(self):
        """Prueba la creación de estaciones"""
        self.assertEqual(len(self.metro_system.stations), 5)
        
        # Verificar que las estaciones tienen los datos correctos
        station = self.metro_system.stations[1]
        self.assertEqual(station.name, "Estación Central")
        self.assertEqual(station.position, (0, 0))
    
    def test_train_creation(self):
        """Prueba la creación de trenes"""
        self.assertEqual(len(self.metro_system.trains), 3)
        
        # Verificar que los trenes tienen los datos correctos
        train = self.metro_system.trains[1]
        self.assertEqual(train.name, "Tren Alpha")
        self.assertEqual(train.capacity, 200)
    
    def test_passenger_boarding(self):
        """Prueba el proceso de subida de pasajeros"""
        train = self.metro_system.trains[1]
        station = self.metro_system.stations[1]
        
        # Añadir pasajeros a la estación
        station.add_passengers(50)
        self.assertEqual(station.waiting_passengers, 50)
        
        # Simular subida de pasajeros
        boarded = train.board_passengers(30)
        station.remove_passengers(boarded)
        
        self.assertEqual(train.passengers, 30)
        self.assertEqual(station.waiting_passengers, 20)
    
    def test_train_movement(self):
        """Prueba el movimiento de trenes"""
        train = self.metro_system.trains[1]
        target_position = (100, 0)
        
        # Configurar tren para moverse
        train.status = "moving"
        train.speed = 60  # 60 unidades por segundo
        
        # Simular movimiento durante 1 segundo
        arrived = train.move_towards(target_position, 1.0)
        
        # El tren debería haberse movido hacia el objetivo
        self.assertNotEqual(train.position, (0, 0))
        
        # Si la velocidad es suficiente, debería haber llegado
        if train.speed >= 100:  # Distancia es 100
            self.assertTrue(arrived)
            self.assertEqual(train.position, target_position)
    
    def test_route_assignment(self):
        """Prueba la asignación de rutas a trenes"""
        result = self.metro_system.assign_route_to_train(1, 1)
        self.assertTrue(result)
        
        train = self.metro_system.trains[1]
        self.assertEqual(train.route, [1, 2, 3])  # Estaciones de la Línea 1
    
    def test_emergency_stop(self):
        """Prueba la parada de emergencia"""
        # Configurar algunos trenes en movimiento
        for train in self.metro_system.trains.values():
            train.status = "moving"
            train.speed = 60
        
        # Ejecutar parada de emergencia
        self.metro_system.emergency_stop_all_trains()
        
        # Verificar que todos los trenes están detenidos
        for train in self.metro_system.trains.values():
            self.assertEqual(train.status, "stopped")
            self.assertEqual(train.speed, 0)

class TestNetworkManager(unittest.TestCase):
    """Pruebas para el administrador de red"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.network_manager = NetworkManager(SYSTEM_CONFIG['network'])
    
    def test_initialization(self):
        """Prueba la inicialización del servidor de red"""
        result = self.network_manager.initialize()
        self.assertTrue(result)
        
        # Limpiar
        self.network_manager.stop()
    
    def test_message_routing(self):
        """Prueba el enrutamiento de mensajes"""
        # Crear mensaje de prueba
        test_message = {
            'type': 'train_status',
            'data': {'train_id': 1, 'status': 'moving'},
            'client_id': 'test_client',
            'timestamp': time.time()
        }
        
        # Probar enrutamiento
        with patch.object(self.network_manager, '_handle_train_status') as mock_handler:
            self.network_manager._route_message(test_message)
            mock_handler.assert_called_once_with(test_message)

class TestCentralController(unittest.TestCase):
    """Pruebas para el controlador central"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.controller = CentralController(SYSTEM_CONFIG['control'])
        self.controller.initialize()
    
    def test_initialization(self):
        """Prueba la inicialización del controlador"""
        self.assertEqual(len(self.controller.station_statuses), 5)
        self.assertEqual(len(self.controller.train_statuses), 3)
    
    def test_alert_system(self):
        """Prueba el sistema de alertas"""
        initial_alerts = len(self.controller.alerts)
        
        # Añadir una alerta
        self.controller._add_alert("test_alert", "Mensaje de prueba")
        
        self.assertEqual(len(self.controller.alerts), initial_alerts + 1)
        
        # Verificar contenido de la alerta
        latest_alert = self.controller.alerts[-1]
        self.assertEqual(latest_alert['type'], "test_alert")
        self.assertEqual(latest_alert['message'], "Mensaje de prueba")
        self.assertFalse(latest_alert['resolved'])
    
    def test_train_status_update(self):
        """Prueba la actualización de estado de trenes"""
        # Actualizar estado de un tren
        self.controller.update_train_status(1, speed=50.0, passengers=100)
        
        # Verificar actualización
        train_status = self.controller.train_statuses[1]
        self.assertEqual(train_status.speed, 50.0)
        self.assertEqual(train_status.passengers, 100)
    
    def test_system_status_retrieval(self):
        """Prueba la obtención del estado del sistema"""
        status = self.controller.get_system_status()
        
        self.assertIn('system_state', status)
        self.assertIn('trains', status)
        self.assertIn('stations', status)
        self.assertIn('timestamp', status)

class TestIntegration(unittest.TestCase):
    """Pruebas de integración del sistema completo"""
    
    def setUp(self):
        """Configuración inicial para pruebas de integración"""
        self.network_manager = NetworkManager(SYSTEM_CONFIG['network'])
        self.central_controller = CentralController(SYSTEM_CONFIG['control'])
        self.metro_system = MetroSystem(
            SYSTEM_CONFIG['metro'],
            self.network_manager,
            self.central_controller
        )
        
        # Inicializar componentes
        self.network_manager.initialize()
        self.central_controller.initialize()
        self.metro_system.initialize()
    
    def tearDown(self):
        """Limpieza después de las pruebas"""
        self.network_manager.stop()
        self.central_controller.stop()
        self.metro_system.stop()
    
    def test_system_startup(self):
        """Prueba el inicio del sistema completo"""
        # Verificar que todos los componentes están inicializados
        self.assertTrue(len(self.metro_system.stations) > 0)
        self.assertTrue(len(self.metro_system.trains) > 0)
        self.assertTrue(len(self.central_controller.station_statuses) > 0)
        self.assertTrue(len(self.central_controller.train_statuses) > 0)
    
    def test_communication_flow(self):
        """Prueba el flujo de comunicación entre componentes"""
        # Simular actualización de estado de tren
        train_id = 1
        new_position = (50, 50)
        
        # Actualizar en el sistema de metro
        if train_id in self.metro_system.trains:
            self.metro_system.trains[train_id].position = new_position
        
        # Verificar que se puede obtener el estado actualizado
        status = self.central_controller.get_system_status()
        self.assertIn('trains', status)

def run_all_tests():
    """Ejecuta todas las pruebas"""
    print("Ejecutando pruebas del Sistema de Metro Autónomo...")
    print("=" * 60)
    
    # Crear suite de pruebas
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Añadir clases de prueba
    suite.addTests(loader.loadTestsFromTestCase(TestMetroSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCentralController))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Ejecutar pruebas
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print(f"Pruebas ejecutadas: {result.testsRun}")
    print(f"Errores: {len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Éxito: {result.wasSuccessful()}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)