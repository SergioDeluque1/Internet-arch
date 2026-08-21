#!/usr/bin/env python3
"""
Cliente GUI compatible con el servidor Python del metro aut        tk.Button(cmd_buttons_row2, text="🚄 Status Sistema", command=self.request_system_status).pack(side=tk.LEFT, padx=2)nomo
Protocolo: JSON en lugar de MATP
"""
import socket, threading, sys, tkinter as tk, tkinter.messagebox as messagebox
import json, time

if len(sys.argv) < 3:
    SERVER_IP = "127.0.0.1"
    SERVER_PORT = 8080  # Puerto del servidor Python
else:
    SERVER_IP = sys.argv[1]
    SERVER_PORT = int(sys.argv[2])

class MetroClientApp:
    def __init__(self, master, server_ip, server_port):
        self.master = master
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = None
        self.connected = False
        self.role = tk.StringVar(value="observer")
        self.authenticated = True  # Para el servidor Python no hay autenticación compleja
        self.client_id = f"gui_client_{int(time.time())}"

        master.title("Cliente Metro - Python (JSON)")
        master.geometry("600x400")
        
        # Frame superior para conexión
        top_frame = tk.Frame(master)
        top_frame.pack(pady=10, fill=tk.X, padx=10)
        
        tk.Label(top_frame, text="Rol:").pack(side=tk.LEFT)
        tk.Radiobutton(top_frame, text="Observer", variable=self.role, value="observer").pack(side=tk.LEFT)
        tk.Radiobutton(top_frame, text="Admin", variable=self.role, value="admin").pack(side=tk.LEFT)
        tk.Button(top_frame, text="Conectar", command=self.connect, bg="green", fg="white").pack(side=tk.LEFT, padx=10)
        
        # Frame para información del sistema
        info_frame = tk.LabelFrame(master, text="Estado del Sistema Metro", font=("Arial", 12, "bold"))
        info_frame.pack(pady=10, fill=tk.X, padx=10)
        
        info_grid = tk.Frame(info_frame)
        info_grid.pack(pady=5)
        
        tk.Label(info_grid, text="Estado Servidor:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky='w')
        self.server_status = tk.StringVar(value="Desconectado")
        tk.Label(info_grid, textvariable=self.server_status, fg="red").grid(row=0, column=1, sticky='w')
        
        tk.Label(info_grid, text="Trenes Activos:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky='w')
        self.trains_active = tk.StringVar(value="0")
        tk.Label(info_grid, textvariable=self.trains_active, fg="blue").grid(row=1, column=1, sticky='w')
        
        tk.Label(info_grid, text="Estaciones:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky='w')
        self.stations_count = tk.StringVar(value="0")
        tk.Label(info_grid, textvariable=self.stations_count, fg="blue").grid(row=2, column=1, sticky='w')
        
        # Información de telemetría como en el cliente original
        tk.Label(info_grid, text="Velocidad:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky='w')
        self.speed_var = tk.StringVar(value="-")
        tk.Label(info_grid, textvariable=self.speed_var, fg="purple").grid(row=3, column=1, sticky='w')
        
        tk.Label(info_grid, text="Batería:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky='w')
        self.batt_var = tk.StringVar(value="-")
        tk.Label(info_grid, textvariable=self.batt_var, fg="red").grid(row=4, column=1, sticky='w')
        
        tk.Label(info_grid, text="Dirección:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky='w')
        self.dir_var = tk.StringVar(value="-")
        tk.Label(info_grid, textvariable=self.dir_var, fg="brown").grid(row=5, column=1, sticky='w')
        
        # Frame para comandos (solo admin)
        self.cmd_frame = tk.LabelFrame(master, text="Comandos de Control (Solo Admin)")
        self.cmd_frame.pack(pady=10, fill=tk.X, padx=10)
        
        # Primera fila de botones - Controles de velocidad y operación
        cmd_buttons_row1 = tk.Frame(self.cmd_frame)
        cmd_buttons_row1.pack(pady=5)
        
        tk.Button(cmd_buttons_row1, text="⬆️ SPEEDUP", command=lambda: self.send_command("SPEEDUP"), bg="lightgreen").pack(side=tk.LEFT, padx=2)
        tk.Button(cmd_buttons_row1, text="⬇️ SLOWDOWN", command=lambda: self.send_command("SLOWDOWN"), bg="orange").pack(side=tk.LEFT, padx=2)
        tk.Button(cmd_buttons_row1, text="� STOPNOW", command=lambda: self.send_command("STOPNOW"), bg="red", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(cmd_buttons_row1, text="▶️ STARTNOW", command=lambda: self.send_command("STARTNOW"), bg="green", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(cmd_buttons_row1, text="👥 LISTUSERS", command=lambda: self.send_command("LISTUSERS"), bg="lightblue").pack(side=tk.LEFT, padx=2)
        
        # Segunda fila de botones - Información del sistema
        cmd_buttons_row2 = tk.Frame(self.cmd_frame)
        cmd_buttons_row2.pack(pady=5)
        
        tk.Button(cmd_buttons_row2, text="�🚄 Status Sistema", command=lambda: self.send_command("system_status")).pack(side=tk.LEFT, padx=2)
        tk.Button(cmd_buttons_row2, text="🚇 Info Trenes", command=lambda: self.send_command("train_info")).pack(side=tk.LEFT, padx=2)
        tk.Button(cmd_buttons_row2, text="🏢 Info Estaciones", command=lambda: self.send_command("station_info")).pack(side=tk.LEFT, padx=2)
        tk.Button(cmd_buttons_row2, text="⚠️ Alertas", command=lambda: self.send_command("alerts")).pack(side=tk.LEFT, padx=2)
        tk.Button(cmd_buttons_row2, text="📊 Estadísticas", command=lambda: self.send_command("stats")).pack(side=tk.LEFT, padx=2)
        
        # Log area
        log_frame = tk.LabelFrame(master, text="Log de Comunicación")
        log_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=10)
        
        self.log = tk.Text(log_frame, height=10, width=70, wrap=tk.WORD)
        scrollbar = tk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log.yview)
        self.log.configure(yscrollcommand=scrollbar.set)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.running = True
        self.update_ui_state()

    def connect(self):
        if self.connected:
            messagebox.showinfo("Info", "Ya está conectado al servidor")
            return
            
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)  # Timeout de 10 segundos
            self.sock.connect((self.server_ip, self.server_port))
            self.connected = True
            self.server_status.set("Conectado")
            self.log_insert(f"✅ Conectado al servidor del metro en {self.server_ip}:{self.server_port}")
            
            # Enviar mensaje de registro del cliente
            register_msg = {
                "type": "client_register",
                "client_id": self.client_id,
                "role": self.role.get(),
                "timestamp": time.time(),
                "capabilities": ["monitoring", "control"] if self.role.get() == "admin" else ["monitoring"]
            }
            self.send_json_message(register_msg)
            
            # Iniciar hilo receptor
            threading.Thread(target=self.receiver_thread, daemon=True).start()
            
            # Solo solicitar estado inicial una vez
            self.request_system_status()
            self.update_ui_state()
            
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar al servidor:\n{str(e)}")
            self.log_insert(f"❌ Error de conexión: {e}")

    def send_json_message(self, message_dict):
        """Envía un mensaje JSON al servidor"""
        try:
            message_json = json.dumps(message_dict).encode('utf-8')
            self.sock.send(message_json)
            self.log_insert(f"📤 Enviado: {message_dict['type']}")
        except Exception as e:
            self.log_insert(f"❌ Error enviando mensaje: {e}")

    def receiver_thread(self):
        """Hilo para recibir mensajes del servidor"""
        try:
            while self.running and self.connected:
                data = self.sock.recv(4096)
                if not data:
                    self.log_insert("📡 Desconectado del servidor")
                    self.connected = False
                    self.server_status.set("Desconectado")
                    break
                    
                try:
                    message = json.loads(data.decode('utf-8'))
                    self.handle_json_message(message)
                except json.JSONDecodeError:
                    self.log_insert(f"⚠️ Mensaje no-JSON recibido: {data.decode('utf-8')[:100]}...")
                    
        except Exception as e:
            self.log_insert(f"❌ Error en receptor: {e}")
            self.connected = False
            self.server_status.set("Desconectado")

    def handle_json_message(self, message):
        """Maneja mensajes JSON del servidor"""
        msg_type = message.get('type', 'unknown')
        self.log_insert(f"📨 Recibido: {msg_type}")
        
        if msg_type == 'system_status':
            data = message.get('data', {})
            self.trains_active.set(str(data.get('active_trains', 0)))
            self.stations_count.set(str(data.get('total_stations', 0)))
            
        elif msg_type == 'train_status':
            data = message.get('data', {})
            self.log_insert(f"🚄 Tren {data.get('train_id', '?')}: {data.get('status', 'unknown')}")
            
        elif msg_type == 'station_update':
            data = message.get('data', {})
            self.log_insert(f"🏢 Estación {data.get('station_id', '?')}: {data.get('passengers', 0)} pasajeros")
            
        elif msg_type == 'telemetry':
            # Manejo de telemetría como en el cliente original
            data = message.get('data', {})
            if 'speed' in data:
                self.speed_var.set(f"{data['speed']} km/h")
            if 'battery' in data:
                self.batt_var.set(f"{data['battery']} %")
            if 'direction' in data:
                self.dir_var.set(data['direction'])
            self.log_insert(f"📊 Telemetría actualizada")
            
        elif msg_type == 'alert':
            data = message.get('data', {})
            alert_msg = data.get('message', 'Alerta del sistema')
            self.log_insert(f"⚠️ ALERTA: {alert_msg}")
            
        elif msg_type == 'command_response':
            # Respuesta a comandos enviados
            command = message.get('command', 'unknown')
            status = message.get('status', 'unknown')
            self.log_insert(f"✅ Comando {command}: {status}")
            
        elif msg_type == 'response':
            response = message.get('response', 'OK')
            self.log_insert(f"✅ Respuesta: {response}")
            
        elif msg_type == 'users_list':
            # Lista de usuarios conectados
            users = message.get('users', [])
            count = message.get('count', 0)
            user_list = ', '.join(users) if users else 'Ninguno'
            messagebox.showinfo("Usuarios Conectados", f"Total: {count}\nUsuarios: {user_list}")
            
        elif msg_type == 'registration_confirmed':
            # Confirmación de registro
            role = message.get('role', 'unknown')
            self.log_insert(f"✅ Registrado exitosamente como {role}")
            
        else:
            # Mensaje no reconocido
            self.log_insert(f"❓ Mensaje desconocido: {msg_type}")

    def send_command(self, command):
        """Envía un comando al servidor"""
        if not self.connected:
            messagebox.showwarning("No Conectado", "Debe conectarse al servidor primero")
            return
            
        if self.role.get() != "admin":
            messagebox.showwarning("Sin Permisos", "Solo los administradores pueden enviar comandos")
            return
            
        command_msg = {
            "type": "control_command",
            "client_id": self.client_id,
            "command": command,
            "timestamp": time.time()
        }
        self.send_json_message(command_msg)

    def request_system_status(self):
        """Solicita el estado del sistema"""
        if self.connected:
            status_msg = {
                "type": "status_request",
                "client_id": self.client_id,
                "timestamp": time.time()
            }
            self.send_json_message(status_msg)

    def update_ui_state(self):
        """Actualiza el estado de la interfaz"""
        if self.role.get() == "admin" and self.connected:
            # Habilitar todos los botones para admin conectado
            for widget in self.cmd_frame.winfo_children():
                if isinstance(widget, tk.Frame):
                    for btn in widget.winfo_children():
                        if isinstance(btn, tk.Button):
                            btn.config(state=tk.NORMAL)
        else:
            # Deshabilitar todos los botones si no es admin o no está conectado
            for widget in self.cmd_frame.winfo_children():
                if isinstance(widget, tk.Frame):
                    for btn in widget.winfo_children():
                        if isinstance(btn, tk.Button):
                            btn.config(state=tk.DISABLED)

    def log_insert(self, txt):
        """Inserta texto en el log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log.insert(tk.END, f"[{timestamp}] {txt}\n")
        self.log.see(tk.END)

    def close(self):
        """Cierra la aplicación"""
        self.running = False
        if self.connected and self.sock:
            try:
                disconnect_msg = {
                    "type": "client_disconnect",
                    "client_id": self.client_id,
                    "timestamp": time.time()
                }
                self.send_json_message(disconnect_msg)
                self.sock.close()
            except:
                pass
        self.master.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = MetroClientApp(root, SERVER_IP, SERVER_PORT)
    root.protocol("WM_DELETE_WINDOW", app.close)
    
    def on_role_change():
        app.update_ui_state()
    
    app.role.trace('w', lambda *args: on_role_change())
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.close()