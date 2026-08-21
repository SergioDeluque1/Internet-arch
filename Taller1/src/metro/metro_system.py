"""
Sistema de Metro - Componente principal que maneja trenes y estaciones
"""

import time
import threading
import math
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Station:
    """Representa una estación de metro"""
    id: int
    name: str
    position: Tuple[float, float]
    waiting_passengers: int = 0
    platform_capacity: int = 300
    
    def add_passengers(self, count: int):
        """Añade pasajeros a la estación"""
        self.waiting_passengers = min(self.waiting_passengers + count, self.platform_capacity)
    
    def remove_passengers(self, count: int) -> int:
        """Remueve pasajeros de la estación y retorna cuántos fueron removidos"""
        removed = min(count, self.waiting_passengers)
        self.waiting_passengers -= removed
        return removed

@dataclass
class Train:
    """Representa un tren del metro"""
    id: int
    name: str
    capacity: int
    speed: float
    position: Tuple[float, float] = (0.0, 0.0)
    passengers: int = 0
    current_station: Optional[int] = None
    destination_station: Optional[int] = None
    status: str = "stopped"  # stopped, moving, boarding, maintenance
    route: List[int] = None
    route_index: int = 0
    
    def __post_init__(self):
        if self.route is None:
            self.route = []
    
    def board_passengers(self, count: int) -> int:
        """Sube pasajeros al tren y retorna cuántos subieron"""
        available_space = self.capacity - self.passengers
        boarded = min(count, available_space)
        self.passengers += boarded
        return boarded
    
    def alight_passengers(self, count: int) -> int:
        """Baja pasajeros del tren y retorna cuántos bajaron"""
        alighted = min(count, self.passengers)
        self.passengers -= alighted
        return alighted
    
    def move_towards(self, target_pos: Tuple[float, float], delta_time: float):
        """Mueve el tren hacia una posición objetivo"""
        dx = target_pos[0] - self.position[0]
        dy = target_pos[1] - self.position[1]
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 1.0:  # No ha llegado al destino
            # Normalizar vector de dirección
            direction_x = dx / distance
            direction_y = dy / distance
            
            # Mover según velocidad
            move_distance = self.speed * delta_time
            if move_distance > distance:
                move_distance = distance
            
            self.position = (
                self.position[0] + direction_x * move_distance,
                self.position[1] + direction_y * move_distance
            )
            return False  # No ha llegado
        else:
            self.position = target_pos
            return True  # Ha llegado

class MetroSystem:
    """Sistema principal del metro que coordina trenes y estaciones"""
    
    def __init__(self, config: Dict[str, Any], network_manager, central_controller):
        self.config = config
        self.network_manager = network_manager
        self.central_controller = central_controller
        
        self.stations: Dict[int, Station] = {}
        self.trains: Dict[int, Train] = {}
        self.routes: Dict[int, Dict[str, Any]] = {}
        
        self.running = False
        self.simulation_time = 0.0
        self.lock = threading.Lock()
        
    def initialize(self):
        """Inicializa el sistema de metro"""
        print("Inicializando sistema de metro...")
        
        # Crear estaciones
        for station_config in self.config['stations']:
            station = Station(
                id=station_config['id'],
                name=station_config['name'],
                position=station_config['position']
            )
            self.stations[station.id] = station
            print(f"Estación creada: {station.name} en {station.position}")
        
        # Crear trenes
        for train_config in self.config['trains']:
            train = Train(
                id=train_config['id'],
                name=train_config['name'],
                capacity=train_config['capacity'],
                speed=train_config['speed']
            )
            # Posicionar tren en la primera estación
            if self.stations:
                first_station = list(self.stations.values())[0]
                train.position = first_station.position
                train.current_station = first_station.id
            
            self.trains[train.id] = train
            print(f"Tren creado: {train.name} (capacidad: {train.capacity})")
        
        # Crear rutas
        for route_config in self.config['routes']:
            self.routes[route_config['id']] = route_config
            print(f"Ruta creada: {route_config['name']} - Estaciones: {route_config['stations']}")
        
        print("Sistema de metro inicializado")
        return True
    
    def run(self):
        """Ejecuta la simulación del sistema de metro"""
        self.running = True
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            delta_time = (current_time - last_time) * self.config['simulation_speed']
            last_time = current_time
            
            self.simulation_time += delta_time
            
            try:
                self._update_passenger_generation()
                self._update_trains(delta_time)
                self._update_stations()
                self._send_status_updates()
                
                time.sleep(self.config['update_interval'])
                
            except Exception as e:
                print(f"Error en simulación de metro: {e}")
    
    def stop(self):
        """Detiene el sistema de metro"""
        self.running = False
        print("Sistema de metro detenido")
    
    def _update_passenger_generation(self):
        """Genera pasajeros en las estaciones de manera aleatoria"""
        for station in self.stations.values():
            # Generar pasajeros aleatoriamente (simulación simple)
            if random.random() < 0.3:  # 30% probabilidad cada actualización
                new_passengers = random.randint(1, 10)
                station.add_passengers(new_passengers)
    
    def _update_trains(self, delta_time: float):
        """Actualiza el estado de todos los trenes"""
        with self.lock:
            for train in self.trains.values():
                if train.status == "moving":
                    self._move_train(train, delta_time)
                elif train.status == "stopped":
                    self._handle_stopped_train(train)
                elif train.status == "boarding":
                    self._handle_boarding(train)
    
    def _move_train(self, train: Train, delta_time: float):
        """Mueve un tren hacia su destino"""
        if train.destination_station is None:
            train.status = "stopped"
            return
        
        if train.destination_station not in self.stations:
            print(f"Estación destino {train.destination_station} no existe para tren {train.id}")
            train.status = "stopped"
            return
        
        target_station = self.stations[train.destination_station]
        arrived = train.move_towards(target_station.position, delta_time)
        
        if arrived:
            train.current_station = train.destination_station
            train.destination_station = None
            train.status = "boarding"
            print(f"Tren {train.name} llegó a {target_station.name}")
            
            # Actualizar controlador central
            self.central_controller.update_train_status(
                train.id,
                position=train.position,
                status=train.status,
                current_station=train.current_station
            )
    
    def _handle_stopped_train(self, train: Train):
        """Maneja un tren que está detenido"""
        # Asignar nueva ruta si no tiene destino
        if train.destination_station is None and train.route:
            self._assign_next_destination(train)
    
    def _assign_next_destination(self, train: Train):
        """Asigna el siguiente destino en la ruta del tren"""
        if not train.route:
            return
        
        # Avanzar al siguiente índice en la ruta
        train.route_index = (train.route_index + 1) % len(train.route)
        next_station_id = train.route[train.route_index]
        
        if next_station_id != train.current_station:
            train.destination_station = next_station_id
            train.status = "moving"
            print(f"Tren {train.name} se dirige a estación {next_station_id}")
    
    def _handle_boarding(self, train: Train):
        """Maneja el proceso de subida y bajada de pasajeros"""
        if train.current_station is None:
            train.status = "stopped"
            return
        
        station = self.stations[train.current_station]
        
        # Simular bajada de pasajeros (algunos bajan en cada estación)
        passengers_alighting = random.randint(0, min(train.passengers, 20))
        train.alight_passengers(passengers_alighting)
        
        # Simular subida de pasajeros
        passengers_boarding = random.randint(0, min(station.waiting_passengers, 30))
        actual_boarded = train.board_passengers(passengers_boarding)
        station.remove_passengers(actual_boarded)
        
        if passengers_alighting > 0 or actual_boarded > 0:
            print(f"Estación {station.name}: {passengers_alighting} bajaron, {actual_boarded} subieron")
        
        # Esperar un momento y luego continuar
        time.sleep(1)  # Simular tiempo de boarding
        
        # Asignar siguiente destino
        self._assign_next_destination(train)
        
        if train.status == "boarding":  # Si no se asignó destino
            train.status = "stopped"
    
    def _update_stations(self):
        """Actualiza el estado de las estaciones"""
        with self.lock:
            for station in self.stations.values():
                # Actualizar controlador central con estado de estación
                self.central_controller.update_station_status(
                    station.id,
                    waiting_passengers=station.waiting_passengers
                )
    
    def _send_status_updates(self):
        """Envía actualizaciones de estado a través de la red"""
        if not self.network_manager:
            return
        
        # Crear mensaje de estado del sistema
        status_message = {
            'type': 'system_status',
            'data': {
                'trains': {tid: {
                    'id': train.id,
                    'name': train.name,
                    'position': train.position,
                    'passengers': train.passengers,
                    'status': train.status,
                    'current_station': train.current_station,
                    'destination_station': train.destination_station
                } for tid, train in self.trains.items()},
                'stations': {sid: {
                    'id': station.id,
                    'name': station.name,
                    'waiting_passengers': station.waiting_passengers,
                    'position': station.position
                } for sid, station in self.stations.items()},
                'simulation_time': self.simulation_time
            },
            'timestamp': time.time()
        }
        
        # Enviar a todos los clientes conectados
        self.network_manager.broadcast_message(status_message)
    
    def assign_route_to_train(self, train_id: int, route_id: int):
        """Asigna una ruta específica a un tren"""
        if train_id not in self.trains:
            print(f"Tren {train_id} no encontrado")
            return False
        
        if route_id not in self.routes:
            print(f"Ruta {route_id} no encontrada")
            return False
        
        train = self.trains[train_id]
        route = self.routes[route_id]
        
        train.route = route['stations'].copy()
        train.route_index = 0
        
        print(f"Ruta {route['name']} asignada a tren {train.name}")
        
        # Si el tren está parado, asignar primer destino
        if train.status == "stopped":
            self._assign_next_destination(train)
        
        return True
    
    def emergency_stop_all_trains(self):
        """Detiene todos los trenes en caso de emergencia"""
        with self.lock:
            for train in self.trains.values():
                train.status = "stopped"
                train.destination_station = None
                train.speed = 0
        
        print("EMERGENCIA: Todos los trenes detenidos")
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas del sistema"""
        with self.lock:
            total_passengers_in_trains = sum(train.passengers for train in self.trains.values())
            total_waiting_passengers = sum(station.waiting_passengers for station in self.stations.values())
            active_trains = sum(1 for train in self.trains.values() if train.status == "moving")
            
            return {
                'total_passengers_in_system': total_passengers_in_trains + total_waiting_passengers,
                'passengers_in_trains': total_passengers_in_trains,
                'passengers_waiting': total_waiting_passengers,
                'active_trains': active_trains,
                'total_trains': len(self.trains),
                'total_stations': len(self.stations),
                'simulation_time': self.simulation_time,
                'system_running': self.running
            }