"""Arranque local: abre el navegador y ejecuta la aplicación Flask."""
import os
import socket
import threading
import webbrowser

from app import app


def abrir_navegador():
    webbrowser.open('http://127.0.0.1:5000')


def esperar_servidor():
    import time
    for _ in range(80):
        try:
            with socket.create_connection(('127.0.0.1', 5000), timeout=0.3):
                abrir_navegador()
                return
        except OSError:
            time.sleep(0.25)
    print('Abre manualmente http://127.0.0.1:5000')


if __name__ == '__main__':
    print('\nGATO NUMÉRICO')
    print('Computadora: http://127.0.0.1:5000')
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if not ip.startswith('127.'):
            print('Celular en la misma Wi-Fi: http://%s:5000' % ip)
    except OSError:
        pass
    print('Deja esta ventana abierta mientras juegas. Ctrl+C para terminar.\n')
    threading.Thread(target=esperar_servidor, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
