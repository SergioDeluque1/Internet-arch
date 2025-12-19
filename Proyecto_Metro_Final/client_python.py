#!/usr/bin/env python3
import socket, threading, sys, tkinter as tk, tkinter.messagebox as messagebox

if len(sys.argv) < 3:
    SERVER_IP = "127.0.0.1"
    SERVER_PORT = 5000
else:
    SERVER_IP = sys.argv[1]
    SERVER_PORT = int(sys.argv[2])

class ClientApp:
    def __init__(self, master, server_ip, server_port):
        self.master = master
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = None
        self.connected = False
        self.role = tk.StringVar(value="observer")
        self.authenticated = False

        master.title("Cliente Metro - Python")
        tk.Label(master, text="Role:").grid(row=0,column=0)
        tk.Radiobutton(master, text="Observer", variable=self.role, value="observer").grid(row=0,column=1)
        tk.Radiobutton(master, text="Admin", variable=self.role, value="admin").grid(row=0,column=2)
        tk.Button(master, text="Conectar", command=self.connect).grid(row=0,column=3)

        tk.Label(master, text="Velocidad:").grid(row=1,column=0)
        self.speed_var = tk.StringVar(value="-"); tk.Label(master, textvariable=self.speed_var).grid(row=1,column=1)
        tk.Label(master, text="Batería:").grid(row=2,column=0)
        self.batt_var = tk.StringVar(value="-"); tk.Label(master, textvariable=self.batt_var).grid(row=2,column=1)
        tk.Label(master, text="Dirección:").grid(row=3,column=0)
        self.dir_var = tk.StringVar(value="-"); tk.Label(master, textvariable=self.dir_var).grid(row=3,column=1)

        self.cmd_frame = tk.Frame(master); self.cmd_frame.grid(row=4, column=0, columnspan=4, pady=10)
        tk.Button(self.cmd_frame, text="SPEEDUP", command=lambda: self.send_command("SPEEDUP")).pack(side=tk.LEFT)
        tk.Button(self.cmd_frame, text="SLOWDOWN", command=lambda: self.send_command("SLOWDOWN")).pack(side=tk.LEFT)
        tk.Button(self.cmd_frame, text="STOPNOW", command=lambda: self.send_command("STOPNOW")).pack(side=tk.LEFT)
        tk.Button(self.cmd_frame, text="STARTNOW", command=lambda: self.send_command("STARTNOW")).pack(side=tk.LEFT)
        tk.Button(self.cmd_frame, text="LISTUSERS", command=self.listusers).pack(side=tk.LEFT)

        self.log = tk.Text(master, height=8, width=60); self.log.grid(row=5, column=0, columnspan=4)
        self.running = True

    def connect(self):
        if self.connected:
            messagebox.showinfo("Info", "Ya conectado"); return
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); self.sock.connect((self.server_ip, self.server_port))
            self.connected = True
            self.log_insert("Conectado a %s:%d" % (self.server_ip, self.server_port))
            role_msg = f"ROLE|{self.role.get()}\\n"; self.sock.sendall(role_msg.encode())
            if self.role.get() == "admin":
                self.prompt_auth()
            threading.Thread(target=self.receiver_thread, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error conexión", str(e))

    def prompt_auth(self):
        authwin = tk.Toplevel(self.master); authwin.title("Autenticación admin")
        tk.Label(authwin, text="Usuario").grid(row=0,column=0); user_ent = tk.Entry(authwin); user_ent.grid(row=0,column=1)
        tk.Label(authwin, text="Pass").grid(row=1,column=0); pass_ent = tk.Entry(authwin, show="*"); pass_ent.grid(row=1,column=1)
        def do_auth():
            user = user_ent.get().strip(); pw = pass_ent.get().strip(); msg = f"AUTH|user={user};pass={pw}\\n"
            try: self.sock.sendall(msg.encode())
            except Exception as e: messagebox.showerror("Error", str(e))
            authwin.destroy()
        tk.Button(authwin, text="Enviar", command=do_auth).grid(row=2,column=0,columnspan=2)

    def receiver_thread(self):
        try:
            buffer = ""
            while self.running:
                data = self.sock.recv(4096)
                if not data:
                    self.log_insert("Desconectado del servidor"); self.connected = False; break
                buffer += data.decode()
                while "\\n" in buffer:
                    line, buffer = buffer.split("\\n",1)
                    if line: self.handle_message(line)
        except Exception as e:
            self.log_insert("Receiver error: " + str(e)); self.connected = False

    def handle_message(self, msg):
        self.log_insert("Recibido: " + msg)
        if msg.startswith("RESPONSE|OK"):
            self.authenticated = True
        elif msg.startswith("RESPONSE|ERROR"):
            self.authenticated = False
        elif msg.startswith("TELEMETRY|"):
            body = msg[len("TELEMETRY|"):]; kvs = body.split(";")
            for kv in kvs:
                if '=' in kv:
                    k,v = kv.split("=",1)
                    if k == "speed": self.speed_var.set(v + " km/h")
                    elif k == "battery": self.batt_var.set(v + " %")
                    elif k == "direction": self.dir_var.set(v)
        elif msg.startswith("RESPONSE|USERS;"):
            users = msg[len("RESPONSE|USERS;"):]; messagebox.showinfo("Usuarios conectados", users)

    def send_command(self, cmd):
        if not self.connected:
            messagebox.showwarning("No conectado", "Conéctate primero"); return
        if self.role.get() != "admin" or not self.authenticated:
            messagebox.showwarning("No autorizado", "Debes autenticarte como admin"); return
        msg = f"COMMAND|{cmd}\\n"
        try:
            self.sock.sendall(msg.encode()); self.log_insert("Enviado: " + msg.strip())
        except Exception as e: self.log_insert("Error al enviar comando: " + str(e))

    def listusers(self):
        if not self.connected:
            messagebox.showwarning("No conectado", "Conéctate primero"); return
        if self.role.get() != "admin" or not self.authenticated:
            messagebox.showwarning("No autorizado", "Debes autenticarte como admin"); return
        try: self.sock.sendall(b"LISTUSERS\\n")
        except Exception as e: self.log_insert("Error LISTUSERS: " + str(e))

    def log_insert(self, txt):
        self.log.insert(tk.END, txt + "\\n"); self.log.see(tk.END)

    def close(self):
        self.running = False
        try:
            if self.sock: self.sock.close()
        except: pass
        self.master.quit()

if __name__ == "__main__":
    root = tk.Tk(); app = ClientApp(root, SERVER_IP, SERVER_PORT)
    root.protocol("WM_DELETE_WINDOW", app.close); root.mainloop()
