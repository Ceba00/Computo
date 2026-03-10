import socket  # Importamos la librería para conectar y usar redes (sockets)
import threading  # Importamos threading para leer mensajes de fondo mientras escribimos nosotros en terminal
import sys  # Importamos sys para poder salir del programa limpiamente (sys.exit)

HOST = "127.0.0.1"  # Dirección IP a conectarnos (Localhost - nuestra propia máquina local)
PORT = 5050  # El mismo puerto donde sabemos que escucha nuestro servidor


def receive_messages(sock):
    """Función independiente que correrá en un Hilo para recibir mensajes del servidor constantemente."""
    file = sock.makefile("r")  # Creamos un envoltorio 'File-like' en modo de solo lectura ('r') para usar 'readline()' cómodamente

    try:
        for line in file:  # Bucle for pasivo que lee de facto línea por línea lo que entra nuevo desde el servidor
            print("\r" + line.strip())  # Imprime limpiando saltos invisibles. '\r' o Retorno de Carro nos ayuda a limpiar la línea actual para que no se arruine con nuestro prompt actual de la terminal.
            print("> ", end="", flush=True)  # Vuelve a pintar el prefijo '> ' de inserción de texto sin salto nuevo. flush=True lo dibuja instantáneo.
    except:
        pass  # Si ocurre un error de lectura repentino (ej. el servidor nos bota o muere de pronto), callarlo y saltar fuera del ciclo.

    print("\nDisconnected from server.")  # Imprimir localmente que perdimos la red.
    sys.exit()  # Matar y finiquitar los procesos que quedan de este hilo al 100%.


def main():
    """Función de arranque principal para el cliente en Consola Command Line."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Creamos el ducto o socket usando TCP (SOCK_STREAM) y familia IPv4 (AF_INET)
    sock.connect((HOST, PORT))  # Forzamos ejecutar la Conexión en Base A la info Constante declarada arriba

    file = sock.makefile("r")  # Abrimos la lectura del socket y la almacenamos referenciada como un Archivo virtual.

    print(file.readline().strip())  # Lee inmediatamente la primera línea escupida por el Servidor (Usualmente debe ser el aviso "Enter username:")
    
    # Bucle de Registro: Nos encierra acá preguntándanos info hasta que la base de datos se trague nuestro Alias.
    while True:
        username = input("> ")  # Detiene la cónsola esperando un texto tipeado desde el teclado humano
        if not username:  # Control: Condición para evitar procesar espacios vacíos puramente mandados por el Enter.
             continue  # Salta esta iteracion y vuelve a la línea del While
             
        sock.sendall((username + "\n").encode())  # Mandamos empaquetado como binario UTF-8 nuestra propuesta de Nombre
        
        response = file.readline().strip()  # El script frena leyendo al puerto, a esperar qué demonios respondió el server
        print(response)  # Imprimimos en cara dicha respuesta
        
        # Lógica Check: Evaluamos literal el texto de error típico.
        if "Username already taken" in response or "Username cannot be empty" in response:
             # Como fallamos, el servidor por su lado pedirá de nuevo "Enter username:". Recogemos esa línea.
             prompt = file.readline().strip()
             print(prompt)  # Mostramos en pantalla el prompt re-solicitado.
        else:
             # Ninguno de esos Strings estuvo envuelto o falló. Asumimos con gracia que conectó exitoso!
             break  # Salva nuestro progreso botandonos del infierno iterativo del While

    # ¡Felicidades ya registrados! 
    # Iniciamos el Sub-Proceso Paralelo. Su misión es estar pasivo alerta escuchando descargas al tiempo que andamos insertando texto en main.
    thread = threading.Thread(target=receive_messages, args=(sock,), daemon=True)  # Agregamos target, le inyectamos los argumentos tipo tuple '(sock,)'. Y lo hacemos daemon para no oponer vida una vez la funcion general muera.
    thread.start()  # Le da cuerda y despacha a la concurrencia a correr la funcion 'receive_messages'

    try:
        # Bucle Infinito Vital del humano dedicado ÚNICAMENTE a capturar nuestras letras del TECLADO y enviarlas.
        while True:
            msg = input("> ")  # Se atora frenando todo el Hilo Principal a que tú redactes algo con Return

            if not msg:  # Escribió en blanco (spam enter).
                continue  # Pasa a la siguiente recarga silencioso

            sock.sendall((msg + "\n").encode())  # Despide este valioso mensaje hacia las entrañas del servidor en bytes

    except KeyboardInterrupt:  # Intercepción física: Atrapa la clásica combinación Ctrl+C que suele detener las Scripts.
        print("\nExiting...")  # Mensajito amigable de escape.

    finally:
        # Se detone por Try o Except exitoso, finalizará obligatoriamente llamando esta porción de código:
        sock.close()  # Cerramos el canal cliente de lado operativo, limpiando memoria.


if __name__ == "__main__":
    # Truco genérico oficial que dictamina la zona cero. Si se llamó la app de forma directa:
    main()  # Lanzar principal.
