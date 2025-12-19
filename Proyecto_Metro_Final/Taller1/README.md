# Sistema de Metro Autónomo - Proyecto de Telemática

## 📋 Descripción
Sistema de metro autónomo que simula la operación de trenes en una red de estaciones con comunicación en tiempo real entre componentes usando TCP/IP.

## 🚀 Instalación y Ejecución

### Prerrequisitos
- Python 3.7 o superior
- Sistema Operativo: Windows, Linux o macOS

### Pasos de Instalación

1. **Clonar/Descargar el proyecto**
   ```bash
   # Si tienes el proyecto en un repositorio
   git clone <url-repositorio>
   cd Taller1
   ```

2. **Verificar Python**
   ```bash
   python --version
   # Debe mostrar Python 3.7 o superior
   ```

3. **Instalar dependencias** (opcional, usa bibliotecas estándar)
   ```bash
   pip install -r requirements.txt
   ```

## 🎮 Uso del Sistema

### Ejecutar el Sistema Principal
```bash
python main.py
```

Esto iniciará:
- Servidor de red en puerto 8080
- Sistema de metro con 5 estaciones y 3 trenes
- Controlador central de monitoreo
- Simulación automática de pasajeros

### Ejecutar Clientes Simulados (en otra terminal)
```bash
python src/communication/client_simulator.py
```

O para múltiples clientes:
```bash
python src/communication/client_simulator.py 5
```

### Ejecutar Pruebas
```bash
python tests/test_metro_system.py
```

## 📊 Interfaz del Sistema

El sistema mostrará información como:
```
==============================================================
SISTEMA DE METRO AUTÓNOMO
Proyecto de Telemática - EAFIT
==============================================================
Inicializando sistema...
Servidor de red iniciado en 127.0.0.1:8080
Inicializando controlador central...
Estación creada: Estación Central en (0, 0)
Estación creada: Estación Norte en (0, 100)
...
Sistema inicializado correctamente
Todos los servicios están ejecutándose...
Presiona Ctrl+C para detener el sistema
```

## 🔧 Configuración

Editar `config/settings.py` para modificar:

### Configuración de Red
```python
'network': {
    'server_host': '127.0.0.1',
    'server_port': 8080,
    'max_connections': 10
}
```

### Configuración de Metro
```python
'metro': {
    'stations': [...],  # Definir estaciones
    'trains': [...],    # Definir trenes
    'routes': [...]     # Definir rutas
}
```

## 📁 Estructura de Archivos

```
Taller1/
├── main.py                    # 🚀 Ejecutar aquí
├── requirements.txt           # 📦 Dependencias
├── README.md                 # 📖 Este archivo
├── config/
│   └── settings.py           # ⚙️ Configuración
├── src/
│   ├── communication/
│   │   ├── network_manager.py      # 🌐 Red
│   │   └── client_simulator.py     # 👥 Clientes
│   ├── control/
│   │   └── central_controller.py   # 🎛️ Control
│   └── metro/
│       └── metro_system.py         # 🚇 Metro
├── tests/
│   └── test_metro_system.py       # 🧪 Pruebas
└── docs/
    └── README.md               # 📚 Documentación
```

## 🎯 Funcionalidades Principales

### ✅ Sistema de Metro
- [x] Simulación de 3 trenes autónomos
- [x] Red de 5 estaciones interconectadas
- [x] Movimiento automático con rutas
- [x] Gestión realista de pasajeros

### ✅ Sistema de Comunicación  
- [x] Servidor TCP/IP multi-cliente
- [x] Protocolo de mensajes JSON
- [x] Broadcasting de estado en tiempo real
- [x] Manejo de conexiones concurrentes

### ✅ Control Central
- [x] Monitoreo en tiempo real
- [x] Sistema de alertas
- [x] Protocolos de emergencia
- [x] Optimización automática de tráfico

## 🚨 Comandos de Control

Durante la ejecución, el sistema responde a:
- **Ctrl+C**: Detener sistema ordenadamente
- **Modificar configuración**: Editar `config/settings.py` y reiniciar

## 📈 Monitoreo del Sistema

El sistema muestra información como:
```
[Cliente_1] Estado del sistema:
  Trenes activos: 2
  Pasajeros esperando: 45
  
Tren Tren Alpha llegó a Estación Norte
Estación Estación Norte: 5 bajaron, 12 subieron
ALERTA [station_crowded]: Estación 3 con alta congestión
```

## 🔍 Resolución de Problemas

### Error: "Puerto en uso"
```bash
# Cambiar puerto en config/settings.py
'server_port': 8081  # En lugar de 8080
```

### Error: "Módulo no encontrado"
```bash
# Ejecutar desde el directorio raíz del proyecto
cd Taller1
python main.py
```

### Error: "No se puede conectar"
```bash
# Verificar que el servidor principal esté ejecutándose
# Luego ejecutar los clientes
```

## 📧 Soporte

Para preguntas sobre el proyecto:
1. Revisar la documentación en `docs/README.md`
2. Ejecutar las pruebas: `python tests/test_metro_system.py`
3. Verificar logs del sistema en consola

## 🎓 Proyecto Académico

**Universidad**: EAFIT  
**Materia**: Telemática  
**Proyecto**: Sistema de Metro Autónomo  
**Enfoque**: Comunicaciones TCP/IP, Sistemas Distribuidos, Control Automático