"""
Administrador de Red - Maneja la comunicación entre componentes del sistema
"""

import socket
import threading
import json
import time
from typing import Dict, List, Any, Optional

class NetworkManager:
    """Administrador de comunicaciones de red para el sistema de metro"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.server_socket: Optional[socket.socket] = None
        self.client_connections: Dict[str, socket.socket] = {}
        self.message_queue: List[Dict[str, Any]] = []
        self.running = False
        self.lock = threading.Lock()
        
    def initialize(self):
        """Inicializa el servidor de red"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.config['server_host'], self.config['server_port']))
            self.server_socket.listen(self.config['max_connections'])
            print(f"Servidor de red iniciado en {self.config['server_host']}:{self.config['server_port']}")
            return True
        except Exception as e:
            print(f"Error inicializando servidor de red: {e}")
            return False
    
    def run(self):
        """Ejecuta el servidor de red"""
        self.running = True
        
        # Iniciar hilo para aceptar conexiones
        accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
        accept_thread.start()
        
        # Procesar mensajes en cola
        while self.running:
            self._process_message_queue()
            time.sleep(0.1)
    
    def stop(self):
        """Detiene el servidor de red"""
        self.running = False
        
        # Cerrar conexiones de clientes
        with self.lock:
            for client_id, conn in self.client_connections.items():
                try:
                    conn.close()
                except:
                    pass
            self.client_connections.clear()
        
        # Cerrar servidor
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("Servidor de red detenido")
    
    def _accept_connections(self):
        """Acepta nuevas conexiones de clientes"""
        while self.running:
            try:
                if self.server_socket:
                    conn, addr = self.server_socket.accept()
                    client_id = f"{addr[0]}:{addr[1]}"
                    
                    with self.lock:
                        self.client_connections[client_id] = conn
                    
                    print(f"Nueva conexión de cliente: {client_id}")
                    
                    # Crear hilo para manejar este cliente
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_id, conn),
                        daemon=True
                    )
                    client_thread.start()
                    
            except Exception as e:
                if self.running:
                    print(f"Error aceptando conexión: {e}")
                break
    
    def _handle_client(self, client_id: str, conn: socket.socket):
        """Maneja la comunicación con un cliente específico"""
        try:
            while self.running:
                data = conn.recv(self.config['buffer_size'])
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode('utf-8'))
                    message['client_id'] = client_id
                    message['timestamp'] = time.time()
                    
                    with self.lock:
                        self.message_queue.append(message)
                    
                    print(f"Mensaje recibido de {client_id}: {message.get('type', 'unknown')}")
                    
                except json.JSONDecodeError:
                    print(f"Mensaje inválido de {client_id}")
                
        except Exception as e:
            print(f"Error manejando cliente {client_id}: {e}")
        finally:
            # Limpiar conexión
            with self.lock:
                if client_id in self.client_connections:
                    del self.client_connections[client_id]
            try:
                conn.close()
            except:
                pass
            print(f"Cliente desconectado: {client_id}")
    
    def _process_message_queue(self):
        """Procesa los mensajes en cola"""
        with self.lock:
            messages_to_process = self.message_queue.copy()
            self.message_queue.clear()
        
        for message in messages_to_process:
            self._route_message(message)
    
    def _route_message(self, message: Dict[str, Any]):
        """Enruta un mensaje al destino apropiado"""
        msg_type = message.get('type', '')
        
        if msg_type == 'train_status':
            self._handle_train_status(message)
        elif msg_type == 'station_update':
            self._handle_station_update(message)
        elif msg_type == 'control_command':
            self._handle_control_command(message)
        elif msg_type == 'emergency':
            self._handle_emergency(message)
        elif msg_type == 'client_register':
            self._handle_client_register(message)
        elif msg_type == 'status_request':
            self._handle_status_request(message)
        else:
            print(f"Tipo de mensaje desconocido: {msg_type}")
    
    def _handle_train_status(self, message: Dict[str, Any]):
        """Maneja actualizaciones de estado de trenes"""
        print(f"Estado de tren: {message.get('data', {})}")
    
    def _handle_station_update(self, message: Dict[str, Any]):
        """Maneja actualizaciones de estaciones"""
        print(f"Actualización de estación: {message.get('data', {})}")
    
    def _handle_control_command(self, message: Dict[str, Any]):
        """Maneja comandos de control"""
        command = message.get('command', '')
        client_id = message.get('client_id', 'unknown')
        
        print(f"🎛️ Comando de control recibido: {command} de {client_id}")
        
        # Procesar diferentes comandos
        if command == 'SPEEDUP':
            self._execute_speedup()
        elif command == 'SLOWDOWN':
            self._execute_slowdown()
        elif command == 'STOPNOW':
            self._execute_stopnow()
        elif command == 'STARTNOW':
            self._execute_startnow()
        elif command == 'LISTUSERS':
            self._execute_listusers(client_id)
        elif command == 'system_status':
            self._send_system_status(client_id)
        else:
            print(f"❓ Comando no reconocido: {command}")
            
    def _execute_speedup(self):
        """Ejecuta comando de acelerar"""
        print("⬆️ COMANDO: Aumentando velocidad de trenes...")
        # Simular aumento de velocidad
        self.broadcast_message({
            'type': 'telemetry',
            'data': {'speed': 75, 'battery': 85, 'direction': 'Norte'},
            'timestamp': time.time()
        })
        
    def _execute_slowdown(self):
        """Ejecuta comando de desacelerar"""
        print("⬇️ COMANDO: Reduciendo velocidad de trenes...")
        self.broadcast_message({
            'type': 'telemetry',
            'data': {'speed': 45, 'battery': 90, 'direction': 'Sur'},
            'timestamp': time.time()
        })
        
    def _execute_stopnow(self):
        """Ejecuta comando de parada de emergencia"""
        print("🛑 COMANDO: PARADA DE EMERGENCIA ejecutada!")
        self.broadcast_message({
            'type': 'alert',
            'data': {'message': 'PARADA DE EMERGENCIA ACTIVADA', 'level': 'critical'},
            'timestamp': time.time()
        })
        self.broadcast_message({
            'type': 'telemetry',
            'data': {'speed': 0, 'battery': 95, 'direction': 'Parado'},
            'timestamp': time.time()
        })
        
    def _execute_startnow(self):
        """Ejecuta comando de iniciar sistema"""
        print("▶️ COMANDO: Iniciando sistema de trenes...")
        self.broadcast_message({
            'type': 'telemetry',
            'data': {'speed': 60, 'battery': 88, 'direction': 'Este'},
            'timestamp': time.time()
        })
        self.broadcast_message({
            'type': 'alert',
            'data': {'message': 'Sistema reiniciado exitosamente', 'level': 'info'},
            'timestamp': time.time()
        })
        
    def _execute_listusers(self, requesting_client_id):
        """Lista usuarios conectados"""
        print(f"👥 COMANDO: Listando usuarios para {requesting_client_id}")
        users = list(self.client_connections.keys())
        
        # Enviar solo al cliente que lo solicitó
        user_message = {
            'type': 'users_list',
            'users': users,
            'count': len(users),
            'timestamp': time.time()
        }
        self._send_to_client(requesting_client_id, user_message)
        
    def _send_system_status(self, client_id):
        """Envía estado del sistema a un cliente específico"""
        status_data = {
            'type': 'system_status',
            'data': {
                'active_trains': 3,
                'total_stations': 5,
                'system_health': 'operational'
            },
            'timestamp': time.time()
        }
        self._send_to_client(client_id, status_data)
        
    def _send_to_client(self, client_id, message):
        """Envía mensaje a un cliente específico"""
        try:
            if client_id in self.client_connections:
                message_json = json.dumps(message).encode('utf-8')
                self.client_connections[client_id].send(message_json)
                print(f"📤 Mensaje enviado a {client_id}: {message['type']}")
        except Exception as e:
            print(f"❌ Error enviando mensaje a {client_id}: {e}")
            
    def _handle_client_register(self, message: Dict[str, Any]):
        """Maneja registro de nuevos clientes"""
        client_id = message.get('client_id', 'unknown')
        role = message.get('role', 'observer')
        print(f"📝 Cliente registrado: {client_id} como {role}")
        
        # Enviar confirmación de registro
        welcome_msg = {
            'type': 'registration_confirmed',
            'client_id': client_id,
            'role': role,
            'timestamp': time.time()
        }
        self._send_to_client(client_id, welcome_msg)
        
    def _handle_status_request(self, message: Dict[str, Any]):
        """Maneja solicitudes de estado del sistema"""
        client_id = message.get('client_id', 'unknown')
        print(f"📊 Solicitud de estado de: {client_id}")
        self._send_system_status(client_id)
    
    def _handle_emergency(self, message: Dict[str, Any]):
        """Maneja mensajes de emergencia"""
        print(f"EMERGENCIA: {message.get('data', {})}")
        self.broadcast_message({
            'type': 'emergency_alert',
            'data': message.get('data', {}),
            'timestamp': time.time()
        })
    
    def broadcast_message(self, message: Dict[str, Any]):
        """Envía un mensaje a todos los clientes conectados"""
        message_json = json.dumps(message).encode('utf-8')
        
        with self.lock:
            disconnected_clients = []
            
            for client_id, conn in self.client_connections.items():
                try:
                    conn.send(message_json)
                except Exception as e:
                    print(f"Error enviando mensaje a {client_id}: {e}")
                    disconnected_clients.append(client_id)
            
            # Limpiar conexiones fallidas
            for client_id in disconnected_clients:
                del self.client_connections[client_id]
    
    def send_message(self, client_id: str, message: Dict[str, Any]):
        """Envía un mensaje a un cliente específico"""
        with self.lock:
            if client_id in self.client_connections:
                try:
                    message_json = json.dumps(message).encode('utf-8')
                    self.client_connections[client_id].send(message_json)
                    return True
                except Exception as e:
                    print(f"Error enviando mensaje a {client_id}: {e}")
                    del self.client_connections[client_id]
                    return False
            else:
                print(f"Cliente {client_id} no encontrado")
                return False
    
    def get_connected_clients(self) -> List[str]:
        """Retorna la lista de clientes conectados"""
        with self.lock:
            return list(self.client_connections.keys())
    
    def get_connection_count(self) -> int:
        """Retorna el número de conexiones activas"""
        with self.lock:
            return len(self.client_connections)