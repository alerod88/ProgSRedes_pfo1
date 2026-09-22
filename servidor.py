import socket
import threading
import sqlite3
from datetime import datetime

# ==========================================
# Configuración del servidor y base de datos
# ==========================================
HOST = "localhost"
PORT = 5000
DB_NAME = "chat.db"

# Lock para sincronizar el acceso concurrente a la base de datos
db_lock = threading.Lock()

def inicializar_db():
    """Crea la base de datos y la tabla de mensajes si no existen."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mensajes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contenido TEXT NOT NULL,
                    fecha_envio TEXT NOT NULL,
                    ip_cliente TEXT NOT NULL
                )
            """)
            conn.commit()
        print("[DB] Base de datos inicializada correctamente.")
    except sqlite3.Error as e:
        print(f"[Error DB] Error al inicializar la base de datos: {e}")
        raise

def guardar_mensaje(contenido, ip_cliente):
    """Inserta un nuevo mensaje en la tabla SQLite de forma sincronizada."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with db_lock:  # Sección crítica para evitar conflictos de escritura entre hilos
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO mensajes (contenido, fecha_envio, ip_cliente)
                    VALUES (?, ?, ?)
                """, (contenido, timestamp, ip_cliente))
                conn.commit()
        return timestamp
    except sqlite3.Error as e:
        print(f"[Error DB] No se pudo guardar el mensaje: {e}")
        return None

def manejar_cliente(conn, addr):
    """Maneja la recepción de mensajes continuos de un cliente en un hilo independiente."""
    ip_cliente = addr[0]
    print(f"[+] Nueva conexión establecida desde {addr}")
    
    with conn:
        while True:
            try:
                # Recibir hasta 1024 bytes
                data = conn.recv(1024)
                if not data:
                    break  # Conexión cerrada de forma remota

                mensaje = data.decode("utf-8").strip()
                
                # Cierre de sesión solicitado por el cliente
                if mensaje.lower() == "fin" or mensaje.lower() == "FIN":
                    print(f"[-] El cliente {addr} finalizó la sesión.")
                    break

                print(f"[{addr}] Mensaje recibido: {mensaje}")
                
                # Persistencia en SQLite
                timestamp = guardar_mensaje(mensaje, ip_cliente)
                
                if timestamp:
                    respuesta = f"Mensaje recibido: {timestamp}"
                else:
                    respuesta = "Error al guardar el mensaje en la base de datos."

                conn.sendall(respuesta.encode("utf-8"))
            except ConnectionResetError:
                break
            except Exception as e:
                print(f"[Error] Fallo en la comunicación con {addr}: {e}")
                break

    print(f"[-] Conexión cerrada con {addr}")

def inicializar_socket():
    """Configura, vincula y activa el socket TCP del servidor."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Permite reutilizar la dirección de inmediato si el servidor se reinicia
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[*] Servidor escuchando en {HOST}:{PORT}...")
        return s
    except OSError as e:
        print(f"[Error Socket] No se pudo vincular al puerto {PORT} (posiblemente en uso): {e}")
        s.close()
        return None

def iniciar_servidor():
    """Punto de entrada principal para orquestar los componentes."""
    try:
        inicializar_db()
    except Exception:
        print("[Fatal] Servidor detenido por error en base de datos.")
        return

    servidor_socket = inicializar_socket()
    if not servidor_socket:
        return

    try:
        with servidor_socket:
            while True:
                conn, addr = servidor_socket.accept()
                # Delegar cada cliente a un hilo para permitir múltiples conexiones simultáneas
                hilo = threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True)
                hilo.start()
    except KeyboardInterrupt:
        print("\n[!] Apagando el servidor...")

if __name__ == "__main__":
    iniciar_servidor()