#  Sistema de Metro Autónomo. Aplicación Protocolo TCP/IP con un AWS EC2

## ✅ PROBLEMA SOLUCIONADO

Los botones **SPEEDUP**, **SLOWDOWN**, **STOPNOW**, **STARTNOW** y **LISTUSERS** ahora están disponibles en el cliente GUI mejorado.

## 🚀 Cómo Ejecutar el Sistema Completo

### Opción 1: Ejecución Automática
```batch
ejecutar_sistema.bat
```

### Opción 2: Ejecución Manual

1. **Iniciar el Servidor:**
   ```bash
   cd Taller1
   python main.py
   ```

2. **Iniciar el Cliente GUI:**
   ```bash
   python client_metro_json.py
   ```

## 🎛️ Funcionalidades del Cliente GUI

### 📊 **Panel de Estado del Sistema**
- **Estado Servidor**: Conectado/Desconectado
- **Trenes Activos**: Número de trenes en operación
- **Estaciones**: Total de estaciones
- **Velocidad**: Velocidad actual del sistema
- **Batería**: Nivel de batería promedio
- **Dirección**: Dirección de operación

### 🎮 **Controles de Operación (Solo Admin)**

#### **Primera Fila - Controles Principales:**
- **⬆️ SPEEDUP**: Aumentar velocidad de los trenes
- **⬇️ SLOWDOWN**: Reducir velocidad de los trenes  
- **🛑 STOPNOW**: Parada inmediata de emergencia
- **▶️ STARTNOW**: Iniciar operación de trenes
- **👥 LISTUSERS**: Listar usuarios conectados

#### **Segunda Fila - Información del Sistema:**
- **🚄 Status Sistema**: Estado general del sistema
- **🚇 Info Trenes**: Información detallada de trenes
- **🏢 Info Estaciones**: Estado de las estaciones
- **⚠️ Alertas**: Ver alertas del sistema
- **📊 Estadísticas**: Estadísticas de operación

## 👤 **Roles de Usuario**

### 🔍 **Observer (Observador)**
- ✅ Ver estado del sistema
- ✅ Recibir alertas
- ✅ Monitoreo en tiempo real
- ❌ No puede enviar comandos

### 👨‍💼 **Admin (Administrador)**
- ✅ Todas las funciones de Observer
- ✅ Enviar comandos de control
- ✅ Modificar velocidad de trenes
- ✅ Parar/iniciar sistema
- ✅ Ver lista de usuarios

## 🌐 **Configuración de Red**

- **Servidor**: 127.0.0.1:8080
- **Protocolo**: JSON sobre TCP/IP
- **Cliente Compatible**: `client_metro_json.py`

## 📋 **Estado del Sistema**

### ✅ **Componentes Funcionando:**
- Sistema de metro con 5 estaciones
- 3 trenes operativos (Alpha, Beta, Gamma)
- 2 líneas de metro
- Servidor de red en puerto 8080
- Cliente GUI con todos los botones
- Sistema de alertas en tiempo real
- Detección de congestión
- Control de tráfico automático

### 🔧 **Comandos Disponibles:**
- `SPEEDUP` - Incrementar velocidad
- `SLOWDOWN` - Decrementar velocidad
- `STOPNOW` - Parada de emergencia
- `STARTNOW` - Iniciar operación
- `LISTUSERS` - Listar usuarios conectados

## 📝 **Log de Comunicación**

El cliente muestra todos los mensajes intercambiados:
- 📤 Mensajes enviados al servidor
- 📨 Mensajes recibidos del servidor
- ⚠️ Alertas del sistema
- ✅ Confirmaciones de comandos

## 🆘 **Solución de Problemas**

### **Si no aparecen los botones:**
1. Usar `client_metro_json.py` (NO `client_python.py`)
2. Verificar que esté seleccionado el rol "Admin"
3. Confirmar conexión al servidor

### **Si no se conecta:**
1. Verificar que el servidor esté ejecutándose
2. Confirmar puerto 8080 (no 5000)
3. Usar el cliente JSON mejorado

## 🎯 **Resumen de la Solución**

**✅ BOTONES RESTAURADOS**: SPEEDUP, SLOWDOWN, STOPNOW, STARTNOW, LISTUSERS
**✅ PROTOCOLO COMPATIBLE**: JSON en lugar de MATP
**✅ INTERFAZ MEJORADA**: Panel de estado completo
**✅ ROLES FUNCIONALES**: Observer y Admin
**✅ COMUNICACIÓN BIDIRECCIONAL**: Tiempo real

¡El sistema de metro autónomo está completamente funcional! 🚇✨
