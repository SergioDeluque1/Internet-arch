# 🎯 INSTRUCCIONES DE USO - Sistema de Metro Autónomo

## ✅ Sistema Creado Exitosamente

He creado un sistema completo de metro autónomo con todas las características necesarias para tu proyecto de Telemática. El sistema incluye:

### 📁 Estructura Completa del Proyecto
```
Taller1/
├── 🚀 main.py                    # ARCHIVO PRINCIPAL - Ejecuta aquí
├── 📦 requirements.txt           
├── 📖 README.md                  
├── 🛠️ utils.py                   # Utilidades del sistema
├── ⚡ run.bat                    # Ejecutor para Windows
├── config/
│   └── ⚙️ settings.py           # Configuración completa
├── src/
│   ├── communication/
│   │   ├── 🌐 network_manager.py     
│   │   └── 👥 client_simulator.py    
│   ├── control/
│   │   └── 🎛️ central_controller.py  
│   └── metro/
│       └── 🚇 metro_system.py        
├── tests/
│   └── 🧪 test_metro_system.py      
├── docs/
│   └── 📚 README.md              
└── logs/                         # Directorio para logs
```

## 🚀 CÓMO EJECUTAR EL SISTEMA

### Método 1: Ejecutor Automático (Recomendado para Windows)
```bash
# Doble clic en el archivo
run.bat
```

### Método 2: Comando Directo
```bash
# Navegar al directorio del proyecto
cd "c:\General\Eafit\Semestre6\Telematica\Taller1"

# Ejecutar el sistema principal
python main.py
```

### Método 3: Usando Utilidades
```bash
# Verificar instalación
python utils.py check

# Ejecutar sistema
python utils.py run

# Ejecutar pruebas
python utils.py test

# Ejecutar clientes simulados
python utils.py client 5
```

## 🎮 INSTRUCCIONES PASO A PASO

### 1. Ejecutar el Sistema Principal
```bash
cd "c:\General\Eafit\Semestre6\Telematica\Taller1"
python main.py
```

**Lo que verás:**
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

### 2. En Una Segunda Terminal - Ejecutar Clientes
```bash
# Abrir nueva terminal PowerShell
cd "c:\General\Eafit\Semestre6\Telematica\Taller1"
python src/communication/client_simulator.py
```

**Lo que verás:**
```
Iniciando 3 clientes simulados...
Cliente Cliente_1 conectado al servidor
Cliente Cliente_2 conectado al servidor
Cliente Cliente_3 conectado al servidor
Clientes ejecutándose... Presiona Ctrl+C para detener
```

### 3. Observar la Simulación
El sistema mostrará información en tiempo real como:
```
Tren Tren Alpha se dirige a estación 2
Nueva conexión de cliente: 127.0.0.1:52841
[Cliente_1] Estado del sistema:
  Trenes activos: 2
  Pasajeros esperando: 23
Tren Tren Beta llegó a Estación Norte
Estación Estación Norte: 3 bajaron, 8 subieron
```

## 🧪 EJECUTAR PRUEBAS

```bash
cd "c:\General\Eafit\Semestre6\Telematica\Taller1"
python tests/test_metro_system.py
```

**Resultado esperado:**
```
Ejecutando pruebas del Sistema de Metro Autónomo...
============================================================
test_station_creation ... ok
test_train_creation ... ok
test_passenger_boarding ... ok
...
============================================================
Pruebas ejecutadas: 12
Errores: 0
Fallos: 0
Éxito: True
```

## ⚙️ CONFIGURACIÓN PERSONALIZADA

### Modificar Estaciones y Trenes
Editar `config/settings.py`:

```python
'metro': {
    'stations': [
        {'id': 1, 'name': 'Tu Estación', 'position': (0, 0)},
        # Añadir más estaciones
    ],
    'trains': [
        {'id': 1, 'name': 'Tu Tren', 'capacity': 250, 'speed': 70},
        # Añadir más trenes
    ]
}
```

### Cambiar Puerto de Red
```python
'network': {
    'server_port': 8081,  # Cambiar si 8080 está ocupado
}
```

## 🔧 SOLUCIÓN DE PROBLEMAS

### Error: "Puerto en uso"
```bash
# Cambiar puerto en config/settings.py
'server_port': 8081
```

### Error: "Módulo no encontrado"
```bash
# Asegúrate de estar en el directorio correcto
cd "c:\General\Eafit\Semestre6\Telematica\Taller1"
```

### Error: Python no encontrado
```bash
# Verificar instalación de Python
python --version
# Debe mostrar Python 3.7 o superior
```

## 📊 CARACTERÍSTICAS IMPLEMENTADAS

### ✅ Sistema de Metro
- [x] 🚇 Simulación de 3 trenes autónomos
- [x] 🏢 Red de 5 estaciones interconectadas  
- [x] 🛤️ Rutas automáticas entre estaciones
- [x] 👥 Generación automática de pasajeros
- [x] ⚡ Movimiento en tiempo real

### ✅ Sistema de Comunicación
- [x] 🌐 Servidor TCP/IP en puerto 8080
- [x] 📡 Protocolo de mensajes JSON
- [x] 📢 Broadcasting de estado del sistema
- [x] 🔄 Múltiples clientes simultáneos
- [x] 🔗 Conexiones concurrentes

### ✅ Control Central
- [x] 📊 Monitoreo en tiempo real
- [x] 🚨 Sistema de alertas automáticas
- [x] ⚠️ Protocolo de emergencia
- [x] 🎯 Optimización de rutas
- [x] 📈 Estadísticas del sistema

## 🎓 INFORMACIÓN ACADÉMICA

**Asignatura**: Telemática  
**Universidad**: EAFIT  
**Proyecto**: Sistema de Metro Autónomo  

### Conceptos Implementados:
- **TCP/IP**: Comunicación cliente-servidor
- **Concurrencia**: Threading para múltiples procesos
- **Protocolos**: Mensajes JSON estructurados
- **Sistemas Distribuidos**: Componentes independientes
- **Control Automático**: Algoritmos de optimización
- **Simulación**: Modelado de sistemas reales

## 🎯 LO QUE TIENES QUE HACER

### 1. ✅ Ejecutar el Sistema
```bash
cd "c:\General\Eafit\Semestre6\Telematica\Taller1"
python main.py
```

### 2. ✅ Probar con Clientes (en otra terminal)
```bash
python src/communication/client_simulator.py
```

### 3. ✅ Ejecutar Pruebas
```bash
python tests/test_metro_system.py
```

### 4. ✅ Documentar tu Experiencia
- Observar el comportamiento del sistema
- Anotar los mensajes de comunicación
- Probar diferentes configuraciones
- Verificar las funcionalidades implementadas

### 5. ✅ Personalizar (Opcional)
- Modificar configuraciones en `config/settings.py`
- Añadir nuevas estaciones o trenes
- Cambiar parámetros de simulación

## 🚀 ¡TODO LISTO PARA USAR!

El sistema está completamente funcional y listo para tu presentación. Incluye todas las características necesarias para un proyecto de Telemática avanzado con comunicaciones TCP/IP, control distribuido y simulación en tiempo real.

**¡Solo tienes que ejecutar `python main.py` y disfrutar del sistema funcionando!** 🎉