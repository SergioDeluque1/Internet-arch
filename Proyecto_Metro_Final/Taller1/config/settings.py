"""
Configuración del Sistema de Metro Autónomo
"""

SYSTEM_CONFIG = {
    'network': {
        'server_host': '127.0.0.1',
        'server_port': 8080,
        'client_ports': [8081, 8082, 8083],
        'protocol': 'TCP',
        'timeout': 30,
        'max_connections': 10,
        'buffer_size': 1024
    },
    
    'metro': {
        'stations': [
            {'id': 1, 'name': 'Estación Central', 'position': (0, 0)},
            {'id': 2, 'name': 'Estación Norte', 'position': (0, 100)},
            {'id': 3, 'name': 'Estación Sur', 'position': (0, -100)},
            {'id': 4, 'name': 'Estación Este', 'position': (100, 0)},
            {'id': 5, 'name': 'Estación Oeste', 'position': (-100, 0)}
        ],
        'trains': [
            {'id': 1, 'name': 'Tren Alpha', 'capacity': 200, 'speed': 60},
            {'id': 2, 'name': 'Tren Beta', 'capacity': 180, 'speed': 55},
            {'id': 3, 'name': 'Tren Gamma', 'capacity': 220, 'speed': 65}
        ],
        'routes': [
            {'id': 1, 'name': 'Línea 1', 'stations': [1, 2, 3]},
            {'id': 2, 'name': 'Línea 2', 'stations': [4, 1, 5]}
        ],
        'simulation_speed': 1.0,
        'update_interval': 2.0
    },
    
    'control': {
        'update_interval': 1.0,
        'max_wait_time': 300,  # 5 minutos
        'emergency_protocols': True,
        'automatic_scheduling': True,
        'traffic_optimization': True,
        'maintenance_mode': False
    },
    
    'logging': {
        'level': 'INFO',
        'file': 'logs/metro_system.log',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    },
    
    'security': {
        'authentication_required': False,
        'encryption_enabled': False,
        'access_tokens': []
    }
}