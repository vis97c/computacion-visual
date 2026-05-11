"""
Servidor Simple de Recepción OSC (Para pruebas locales)
=======================================================
Este script escucha en 127.0.0.1:5005 e imprime cualquier
mensaje que llegue. Útil para verificar que el comando de voz
esté enviando correctamente la información por OSC antes de pasar a Unity.
"""

from pythonosc import dispatcher
from pythonosc import osc_server

def print_handler(addr, *args):
    print(f"[RECEPTOR OSC] Recibido en la dirección {addr}: {args}")

if __name__ == "__main__":
    ip = "127.0.0.1"
    port = 5005
    
    # Configurar el dispatcher para atrapar cualquier ruta (/voz/color, /voz/girar, etc)
    disp = dispatcher.Dispatcher()
    disp.set_default_handler(print_handler)
    
    server = osc_server.ThreadingOSCUDPServer((ip, port), disp)
    print("="*50)
    print(f"📡 Escuchando mensajes OSC en {ip}:{port}")
    print("="*50)
    print("Mantén este script abierto y luego habla en el script principal.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando receptor OSC...")
