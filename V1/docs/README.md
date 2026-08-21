# Sistema de Metro Autónomo

## Descripción del Proyecto

Este proyecto implementa un sistema de metro autónomo con capacidades de comunicación, control y monitoreo en tiempo real. El sistema simula la operación de múltiples trenes en una red de estaciones de metro, con comunicación entre componentes mediante sockets TCP/IP.

## Características Principales

### 🚇 Sistema de Metro
- **Simulación de Trenes**: Múltiples trenes con capacidades y velocidades diferentes
- **Red de Estaciones**: Sistema de estaciones interconectadas con rutas definidas
- **Gestión de Pasajeros**: Simulación realista de subida y bajada de pasajeros
- **Movimiento Autónomo**: Los trenes se mueven automáticamente siguiendo rutas asignadas

### 🌐 Sistema de Comunicación
- **Servidor TCP/IP**: Comunicación en tiempo real entre componentes
- **Protocolo de Mensajes**: Sistema de mensajes JSON para intercambio de información
- **Múltiples Clientes**: Soporte para conexiones simultáneas de múltiples clientes
- **Broadcast de Estado**: Difusión del estado del sistema a todos los clientes conectados

### 🎛️ Control Central
- **Monitoreo en Tiempo Real**: Seguimiento continuo del estado de trenes y estaciones
- **Sistema de Alertas**: Detección y notificación de eventos importantes
- **Control de Tráfico**: Optimización automática del flujo de trenes
- **Modo de Emergencia**: Protocolo de parada de emergencia para toda la red

## Estructura del Proyecto

```
Taller1/
├── main.py                              # Punto de entrada principal
├── requirements.txt                     # Dependencias del proyecto
├── README.md                           # Documentación principal
├── config/
│   └── settings.py                     # Configuración del sistema
├── src/
│   ├── communication/
│   │   ├── network_manager.py          # Administrador de red
│   │   └── client_simulator.py         # Simulador de clientes
│   ├── control/
│   │   └── central_controller.py       # Controlador central
│   └── metro/
│       └── metro_system.py             # Sistema principal de metro
├── tests/
│   └── test_metro_system.py            # Pruebas unitarias
└── docs/
    └── README.md                        # Esta documentación
```

## Componentes del Sistema

### 1. Sistema de Metro (`metro_system.py`)
- **Clases**: `MetroSystem`, `Train`, `Station`
- **Funcionalidades**:
  - Simulación de movimiento de trenes
  - Gestión de estaciones y pasajeros
  - Asignación de rutas
  - Generación automática de pasajeros

### 2. Administrador de Red (`network_manager.py`)
- **Clase**: `NetworkManager`
- **Funcionalidades**:
  - Servidor TCP/IP multi-cliente
  - Enrutamiento de mensajes
  - Broadcast de estado del sistema
  - Manejo de conexiones cliente

### 3. Controlador Central (`central_controller.py`)
- **Clase**: `CentralController`
- **Funcionalidades**:
  - Monitoreo del estado del sistema
  - Sistema de alertas y emergencias
  - Programación automática de trenes
  - Optimización de tráfico

### 4. Simulador de Clientes (`client_simulator.py`)
- **Clase**: `MetroClient`
- **Funcionalidades**:
  - Conexión al servidor del sistema
  - Simulación de múltiples clientes
  - Envío y recepción de mensajes
  - Monitoreo del estado del sistema

## Configuración

El archivo `config/settings.py` contiene toda la configuración del sistema:

- **Red**: Puertos, direcciones IP, timeouts
- **Metro**: Estaciones, trenes, rutas, velocidades de simulación
- **Control**: Intervalos de actualización, protocolos de emergencia
- **Logging**: Configuración de registros del sistema

## Tipos de Mensajes

El sistema utiliza mensajes JSON con los siguientes tipos:

1. **`train_status`**: Estado actual de un tren
2. **`station_update`**: Actualización de estado de estación
3. **`control_command`**: Comando de control del sistema
4. **`emergency`**: Mensaje de emergencia
5. **`system_status`**: Estado completo del sistema

## Características Técnicas

### Protocolos de Comunicación
- **TCP/IP**: Comunicación fiable entre componentes
- **JSON**: Formato de mensajes estructurado
- **Threading**: Procesamiento concurrente de múltiples conexiones

### Algoritmos Implementados
- **Pathfinding**: Movimiento de trenes entre estaciones
- **Load Balancing**: Distribución de trenes según demanda
- **Traffic Optimization**: Optimización del flujo de tráfico
- **Emergency Protocols**: Protocolos de seguridad y emergencia

### Simulación Realista
- **Física Básica**: Movimiento con velocidad y posición
- **Capacidades Limitadas**: Trenes y estaciones con límites realistas
- **Generación de Eventos**: Pasajeros y situaciones aleatorias
- **Tiempo Real**: Simulación con escalas de tiempo configurables

## Casos de Uso

### 1. **Monitoreo Operacional**
- Visualización en tiempo real del estado de todos los trenes
- Seguimiento de pasajeros en el sistema
- Alertas de congestión en estaciones

### 2. **Control de Tráfico**
- Asignación automática de rutas a trenes
- Optimización del flujo según demanda
- Prevención de congestiones

### 3. **Gestión de Emergencias**
- Detección automática de situaciones de emergencia
- Parada coordenada de toda la red
- Notificación inmediata a todos los componentes

### 4. **Análisis y Estadísticas**
- Recolección de datos operacionales
- Análisis de eficiencia del sistema
- Estadísticas de uso y rendimiento

## Extensibilidad

El sistema está diseñado para ser fácilmente extensible:

- **Nuevos Tipos de Mensaje**: Fácil adición de protocolos de comunicación
- **Algoritmos de Control**: Intercambio de algoritmos de optimización
- **Interfaces de Usuario**: Conexión de interfaces gráficas o web
- **Sensores Virtuales**: Integración de sensores simulados adicionales