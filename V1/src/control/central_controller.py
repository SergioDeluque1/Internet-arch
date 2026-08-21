"""
Controlador Central - Coordina las operaciones del sistema de metro
"""

import time
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class SystemState(Enum):
    """Estados del sistema"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"

@dataclass
class TrainStatus:
    """Estado de un tren"""
    train_id: int
    position: tuple
    speed: float
    passengers: int
    destination_station: int
    status: str
    last_update: float

@dataclass
class StationStatus:
    """Estado de una estación"""
    station_id: int
    waiting_passengers: int
    platform_status: str
    last_maintenance: float
    alerts: List[str]

class CentralController:
    """Controlador central del sistema de metro"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.system_state = SystemState.INITIALIZING
        self.train_statuses: Dict[int, TrainStatus] = {}
        self.station_statuses: Dict[int, StationStatus] = {}
        self.schedule: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        self.running = False
        self.lock = threading.Lock()
        
    def initialize(self):
        """Inicializa el controlador central"""
        print("Inicializando controlador central...")
        
        # Inicializar estados de estaciones (ejemplo)
        for i in range(1, 6):  # 5 estaciones
            self.station_statuses[i] = StationStatus(
                station_id=i,
                waiting_passengers=0,
                platform_status="available",
                last_maintenance=time.time(),
                alerts=[]
            )
        
        # Inicializar estados de trenes (ejemplo)
        for i in range(1, 4):  # 3 trenes
            self.train_statuses[i] = TrainStatus(
                train_id=i,
                position=(0, 0),
                speed=0.0,
                passengers=0,
                destination_station=1,
                status="stopped",
                last_update=time.time()
            )
        
        self.system_state = SystemState.RUNNING
        print("Controlador central inicializado")
        return True
    
    def run(self):
        """Ejecuta el controlador central"""
        self.running = True
        
        while self.running:
            try:
                self._update_system_state()
                self._process_schedules()
                self._check_alerts()
                self._optimize_traffic()
                
                time.sleep(self.config['update_interval'])
                
            except Exception as e:
                print(f"Error en controlador central: {e}")
                self._add_alert("system_error", f"Error del controlador: {e}")
    
    def stop(self):
        """Detiene el controlador central"""
        self.running = False
        self.system_state = SystemState.SHUTDOWN
        print("Controlador central detenido")
    
    def _update_system_state(self):
        """Actualiza el estado general del sistema"""
        current_time = time.time()
        
        with self.lock:
            # Verificar estado de trenes
            for train_id, status in self.train_statuses.items():
                if current_time - status.last_update > 30:  # 30 segundos sin actualización
                    self._add_alert("train_communication", f"Pérdida de comunicación con tren {train_id}")
            
            # Verificar estado de estaciones
            for station_id, status in self.station_statuses.items():
                if status.waiting_passengers > 100:  # Muchos pasajeros esperando
                    self._add_alert("station_crowded", f"Estación {station_id} con alta congestión")
    
    def _process_schedules(self):
        """Procesa los horarios programados"""
        if not self.config.get('automatic_scheduling', False):
            return
        
        current_time = time.time()
        
        # Implementar lógica de programación automática
        with self.lock:
            for train_id, status in self.train_statuses.items():
                if status.status == "stopped" and status.passengers == 0:
                    # Asignar nueva ruta si el tren está parado y vacío
                    self._assign_route(train_id)
    
    def _assign_route(self, train_id: int):
        """Asigna una nueva ruta a un tren"""
        # Lógica simple: ir a la estación con más pasajeros esperando
        max_passengers = 0
        target_station = 1
        
        for station_id, status in self.station_statuses.items():
            if status.waiting_passengers > max_passengers:
                max_passengers = status.waiting_passengers
                target_station = station_id
        
        if train_id in self.train_statuses:
            self.train_statuses[train_id].destination_station = target_station
            self.train_statuses[train_id].status = "moving"
            print(f"Tren {train_id} asignado a estación {target_station}")
    
    def _check_alerts(self):
        """Verifica y procesa alertas del sistema"""
        current_time = time.time()
        
        # Limpiar alertas antiguas (más de 1 hora)
        self.alerts = [alert for alert in self.alerts 
                      if current_time - alert['timestamp'] < 3600]
        
        # Verificar condiciones de emergencia
        if any(alert['type'] == 'emergency' for alert in self.alerts):
            if self.system_state != SystemState.EMERGENCY:
                self._enter_emergency_mode()
    
    def _optimize_traffic(self):
        """Optimiza el tráfico de trenes"""
        if not self.config.get('traffic_optimization', False):
            return
        
        with self.lock:
            # Implementar algoritmo simple de optimización
            # Por ejemplo, redistribuir trenes según demanda
            self._balance_train_distribution()
    
    def _balance_train_distribution(self):
        """Balancea la distribución de trenes"""
        # Implementar lógica de balanceo
        # Por ahora, solo un placeholder
        pass
    
    def _add_alert(self, alert_type: str, message: str):
        """Añade una nueva alerta al sistema"""
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': time.time(),
            'resolved': False
        }
        
        self.alerts.append(alert)
        print(f"ALERTA [{alert_type}]: {message}")
    
    def _enter_emergency_mode(self):
        """Entra en modo de emergencia"""
        self.system_state = SystemState.EMERGENCY
        print("SISTEMA EN MODO DE EMERGENCIA")
        
        # Detener todos los trenes
        with self.lock:
            for train_id, status in self.train_statuses.items():
                if status.status == "moving":
                    status.status = "emergency_stop"
                    status.speed = 0.0
        
        # Notificar a todas las estaciones
        self._add_alert("emergency", "Sistema en modo de emergencia - Todos los trenes detenidos")
    
    def update_train_status(self, train_id: int, **kwargs):
        """Actualiza el estado de un tren"""
        with self.lock:
            if train_id in self.train_statuses:
                status = self.train_statuses[train_id]
                
                for key, value in kwargs.items():
                    if hasattr(status, key):
                        setattr(status, key, value)
                
                status.last_update = time.time()
                print(f"Estado de tren {train_id} actualizado")
            else:
                print(f"Tren {train_id} no encontrado")
    
    def update_station_status(self, station_id: int, **kwargs):
        """Actualiza el estado de una estación"""
        with self.lock:
            if station_id in self.station_statuses:
                status = self.station_statuses[station_id]
                
                for key, value in kwargs.items():
                    if hasattr(status, key):
                        setattr(status, key, value)
                
                print(f"Estado de estación {station_id} actualizado")
            else:
                print(f"Estación {station_id} no encontrada")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna el estado general del sistema"""
        with self.lock:
            return {
                'system_state': self.system_state.value,
                'trains': {tid: {
                    'train_id': status.train_id,
                    'position': status.position,
                    'speed': status.speed,
                    'passengers': status.passengers,
                    'destination_station': status.destination_station,
                    'status': status.status
                } for tid, status in self.train_statuses.items()},
                'stations': {sid: {
                    'station_id': status.station_id,
                    'waiting_passengers': status.waiting_passengers,
                    'platform_status': status.platform_status,
                    'alerts': status.alerts
                } for sid, status in self.station_statuses.items()},
                'active_alerts': len([a for a in self.alerts if not a['resolved']]),
                'timestamp': time.time()
            }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Retorna todas las alertas activas"""
        return [alert for alert in self.alerts if not alert['resolved']]
    
    def resolve_alert(self, alert_index: int):
        """Marca una alerta como resuelta"""
        if 0 <= alert_index < len(self.alerts):
            self.alerts[alert_index]['resolved'] = True
            print(f"Alerta {alert_index} marcada como resuelta")
    
    def send_control_command(self, target: str, command: str, params: Dict[str, Any] = None):
        """Envía un comando de control"""
        command_data = {
            'target': target,
            'command': command,
            'params': params or {},
            'timestamp': time.time()
        }
        
        print(f"Comando enviado: {command_data}")
        # Aquí se integraría con el NetworkManager para enviar el comando