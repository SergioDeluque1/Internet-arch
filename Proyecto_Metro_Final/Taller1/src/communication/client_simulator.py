"""
Cliente Simulador - Simula clientes que se conectan al sistema de metro
"""

import socket
import json
import time
import threading
import random
from typing import Dict, Any

class MetroClient:
    """Cliente que se conecta al sistema de metro"""
    
    def __init__(self, client_id: str, server_host: str = '127.0.0.1', server_port: int = 8080):
        self.client_id = client_id
        self.server_host = server_host
        self.server_port = server_port
        self.socket: socket.socket = None
        self.connected = False
        self.running = False
        
    def connect(self) -> bool:
        """Conecta al servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.connected = True
            print(f"Cliente {self.client_id} conectado al servidor")
            return True
        except Exception as e:
            print(f"Error conectando cliente {self.client_id}: {e}")
            return False
    
    def disconnect(self):
        """Desconecta del servidor"""
        self.running = False
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print(f"Cliente {self.client_id} desconectado")
    
    def send_message(self, message: Dict[str, Any]) -> bool:
        """Envía un mensaje al servidor"""
        if not self.connected or not self.socket:
            return False
        
        try:
            message_json = json.dumps(message).encode('utf-8')
            self.socket.send(message_json)
            return True
        except Exception as e:
            print(f"Error enviando mensaje desde {self.client_id}: {e}")
            self.connected = False
            return False
    
    def listen_for_messages(self):
        """Escucha mensajes del servidor"""
        buffer = ""
        
        while self.running and self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                
                # Procesar mensajes completos
                while '\n' in buffer or len(buffer) > 0:
                    try:
                        message = json.loads(buffer)
                        self._handle_received_message(message)
                        buffer = ""
                        break
                    except json.JSONDecodeError:
                        # Si no es JSON válido, esperar más datos
                        if '\n' in buffer:
                            lines = buffer.split('\n')
                            buffer = lines[-1]
                            for line in lines[:-1]:
                                if line.strip():
                                    try:
                                        message = json.loads(line)
                                        self._handle_received_message(message)
                                    except json.JSONDecodeError:
                                        pass
                        else:
                            break
                            
            except Exception as e:
                if self.running:
                    print(f"Error recibiendo mensaje en {self.client_id}: {e}")
                break
        
        self.connected = False
    
    def _handle_received_message(self, message: Dict[str, Any]):
        """Maneja un mensaje recibido del servidor"""
        msg_type = message.get('type', 'unknown')
        
        if msg_type == 'system_status':
            self._handle_system_status(message.get('data', {}))
        elif msg_type == 'emergency_alert':
            self._handle_emergency_alert(message.get('data', {}))
        else:
            print(f"Cliente {self.client_id} recibió: {msg_type}")
    
    def _handle_system_status(self, data: Dict[str, Any]):
        """Maneja actualizaciones de estado del sistema"""
        trains = data.get('trains', {})
        stations = data.get('stations', {})
        
        print(f"[{self.client_id}] Estado del sistema:")
        print(f"  Trenes activos: {len([t for t in trains.values() if t.get('status') == 'moving'])}")
        print(f"  Pasajeros esperando: {sum(s.get('waiting_passengers', 0) for s in stations.values())}")
    
    def _handle_emergency_alert(self, data: Dict[str, Any]):
        """Maneja alertas de emergencia"""
        print(f"[{self.client_id}] ¡ALERTA DE EMERGENCIA!: {data}")
    
    def run(self):
        """Ejecuta el cliente"""
        if not self.connect():
            return
        
        self.running = True
        
        # Iniciar hilo para escuchar mensajes
        listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        listen_thread.start()
        
        # Simular comportamiento del cliente
        self._simulate_client_behavior()
    
    def _simulate_client_behavior(self):
        """Simula el comportamiento de un cliente"""
        while self.running:
            try:
                # Enviar mensaje aleatorio ocasionalmente
                if random.random() < 0.1:  # 10% probabilidad
                    self._send_random_message()
                
                time.sleep(5)  # Esperar 5 segundos
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error en simulación de cliente {self.client_id}: {e}")
                break
    
    def _send_random_message(self):
        """Envía un mensaje aleatorio al servidor"""
        message_types = [
            {
                'type': 'station_update',
                'data': {
                    'station_id': random.randint(1, 5),
                    'passenger_count': random.randint(0, 50)
                }
            },
            {
                'type': 'train_status',
                'data': {
                    'train_id': random.randint(1, 3),
                    'position': (random.uniform(-100, 100), random.uniform(-100, 100)),
                    'speed': random.uniform(0, 70)
                }
            }
        ]
        
        message = random.choice(message_types)
        self.send_message(message)

def simulate_multiple_clients(num_clients: int = 3):
    """Simula múltiples clientes conectándose al sistema"""
    clients = []
    threads = []
    
    print(f"Iniciando {num_clients} clientes simulados...")
    
    for i in range(num_clients):
        client = MetroClient(f"Cliente_{i+1}")
        clients.append(client)
        
        # Crear hilo para cada cliente
        client_thread = threading.Thread(target=client.run, daemon=True)
        threads.append(client_thread)
        client_thread.start()
        
        time.sleep(1)  # Esperar un poco entre conexiones
    
    try:
        print("Clientes ejecutándose... Presiona Ctrl+C para detener")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo clientes...")
        for client in clients:
            client.disconnect()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        num_clients = int(sys.argv[1])
    else:
        num_clients = 3
    
    simulate_multiple_clients(num_clients)