import socket

# ==========================================
# Configuración del socket del cliente
# ==========================================
HOST = "localhost"
PORT = 5000

def iniciar_cliente():
    """Establece la conexión con el servidor y gestiona el envío interactivo de mensajes."""
    try:
        # Configuración del socket TCP/IP
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            print(f"[*] Conectado al servidor en {HOST}:{PORT}")
            print("Escribí tus mensajes (ingresá 'éxito' para finalizar la sesión):\n")

            while True:
                mensaje = input("Tu mensaje > ").strip()
                if not mensaje:
                    continue

                # Envío de la cadena codificada en bytes UTF-8
                s.sendall(mensaje.encode("utf-8"))

                # Si el usuario escribe éxito, finaliza sin esperar confirmación
                if mensaje.lower() == "éxito" or mensaje.lower() == "fin":
                    print("Sesión cerrada con éxito.")
                    break

                # Recepción de la confirmación del servidor
                respuesta = s.recv(1024).decode("utf-8")
                print(f"[Servidor]: {respuesta}\n")

    except ConnectionRefusedError:
        print(f"[Error] Conexión rechazada: asegurate de que el servidor esté corriendo en {HOST}:{PORT}.")
    except Exception as e:
        print(f"[Error inesperado]: {e}")

if __name__ == "__main__":
    iniciar_cliente()