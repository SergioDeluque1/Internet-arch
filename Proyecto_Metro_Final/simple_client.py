#!/usr/bin/env python3
"""
Cliente simple para probar la conexión con el servidor Python del metro
"""
import socket
import json
import threading
import time

def client_listener(sock):
    """Escucha mensajes del servidor"""
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            message = json.loads(data.decode('utf-8'))
            print(f"📨 Mensaje del servidor: {message}")
        except Exception as e:
            print(f"❌ Error recibiendo mensaje: {e}")
            break

def main():
    # Conectar al servidor
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('127.0.0.1', 8080))
        print("✅ Conectado al servidor del metro en 127.0.0.1:8080")
        
        # Iniciar hilo para escuchar mensajes
        listener_thread = threading.Thread(target=client_listener, args=(sock,), daemon=True)
        listener_thread.start()
        
        # Enviar mensaje de prueba
        test_message = {
            "type": "client_info",
            "client_id": "test_client_1",
            "role": "observer",
            "timestamp": time.time()
        }
        
        message_json = json.dumps(test_message).encode('utf-8')
        sock.send(message_json)
        print(f"📤 Enviado: {test_message}")
        
        # Mantener la conexión activa
        while True:
            try:
                # Enviar ping cada 5 segundos
                ping_message = {
                    "type": "ping",
                    "timestamp": time.time()
                }
                message_json = json.dumps(ping_message).encode('utf-8')
                sock.send(message_json)
                print(f"🏓 Ping enviado")
                time.sleep(5)
                
            except KeyboardInterrupt:
                print("\n👋 Desconectando...")
                break
                
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    main()