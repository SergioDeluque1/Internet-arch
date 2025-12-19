Actualizaciones realizadas al proyecto original Taller1:
- Se mantuvieron los módulos Python originales (en src/) como apoyo a la simulación.
- Se añadió un servidor real en C (server.c) que implementa el protocolo MATP y maneja clientes reales via TCP/IP.
- Se añadieron dos clientes con GUI (Python Tkinter y Java Swing) que cumplen los roles observer/admin.
- Se incluyó Protocolo_Metro_Autonomo.docx y CHECKLIST.txt para la entrega.
- Se añadió Makefile para compilar el servidor y README con pasos de ejecución.

Instrucciones rápidas:
1. Compilar servidor: make
2. Ejecutar servidor: ./server 5000 server.log
3. Ejecutar cliente Python: python3 client_python.py 127.0.0.1 5000
4. Ejecutar cliente Java: javac ClientGUI.java && java ClientGUI 127.0.0.1 5000
