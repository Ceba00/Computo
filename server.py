import socket  # Importamos la librería de sockets (para la comunicación de red TCP/IP)
import threading  # Importamos threading para manejar cada cliente en un hilo separado concurrentemente

HOST = "0.0.0.0"  # Escucha en todas las interfaces de red disponibles de la máquina
PORT = 5050  # Puerto en el que el servidor aceptará las conexiones entrantes

clients = {}  # Diccionario global para guardar a los clientes conectados: { 'nombre_usuario': objeto_socket }
groups = {}  # Diccionario global para los grupos: { 'nombre_grupo': ['usuario1', 'usuario2'] }
clients_lock = threading.Lock()  # Mutex (Lock) para evitar condiciones de carrera al modificar los diccionarios simultáneamente


def send(sock, msg):
    """Función auxiliar para enviar un mensaje a un socket específico."""
    try:
        # Añadimos un salto de línea al final y codificamos el texto de String a bytes (UTF-8) para enviarlo a través de red
        sock.sendall((msg + "\n").encode())
    except:
        # Si falla el envío (ej. si el socket de destino se cerró abruptamente), lo silenciamos e ignoramos aquí.
        pass


def broadcast(msg, sender=None):
    """Envía un mensaje a todos los clientes conectados, con la opción de omitir al remitente original."""
    dead = []  # Lista temporal para ir recolectando los usuarios que se desconectaron o cuyo socket falló
    with clients_lock:  # Adquirimos el candado global para evitar que la lista de clientes cambie mientras recorremos el for
        items = list(clients.items())  # Obtenemos una copia paralela/estática de la tupla (usuario, socket)

    for user, sock in items:  # Ciclo para recorrer a todos los usuarios vigentes y sus respectivos objetos
        if user == sender:  # Si el usuario evaluado actual resultó ser el remitente original (el que manda el mensaje)...
            continue        # ...pasamos a la siguiente iteración para no mostrarle de vuelta su propio mensaje, evitando efecto eco
        try:
            send(sock, msg)  # Invocamos try/except con nuestra func "send" para mandar la info
        except:
            dead.append(user)  # Si revienta un error al enviar, significa que algo anduvo mal, lo registramos como desconectado (muerto)

    for user in dead:  # Recorremos la lista de usuarios zombies/caídos
        remove_client(user)  # Pasamos por nuestra función removedora cada usuario extinto


def send_to_self(msg, sender):
    """Busca el socket de un usuario remitente para enviarle un mensaje directo (normalmente usado para comandos fallidos)."""
    with clients_lock:  # Bloqueamos en modo seguro de hilos
        sock = clients.get(sender)  # Tratamos de recuperar el socket buscando por el nombre string (sender)
    if sock:  # Si el socket efectivamente no era None (existe)...
        send(sock, msg)  # ...le disparamos el mensaje de vuelta en su conexión


def broadcast_state():
    """ Envia la lista de usuarios y grupos a todos para que tengan la interfaz (UI) de lista actualizada. """
    with clients_lock:  # Entramos a la zona de candado por seguridad interbloqueos
        # Creamos una cadena string delimitada por comas usando las llaves (nombres) ej: "user1,user2,user3"
        user_list = ",".join(clients.keys())
        
        # Igualmente, obtenemos una listita de los nombres de los grupos existentes en string y separados por comas.
        group_list = ",".join(groups.keys())
        
        # Juntamos lo extraido antes, formando la cadena oficial: STATE:usuarios|grupos
        state_msg = f"STATE:{user_list}|{group_list}"
        
        for sock in clients.values():  # Con un for loop, navegamos por los objetos de conexión
            send(sock, state_msg)  # Despachamos el Estado completo recien hecho a todos y cada uno.


def remove_client(username):
    """Remueve sistemáticamente todo rastro dejado en el servidor por un usuario."""
    with clients_lock:  # Usamos candado, para mutar los datos globales tranquilamente
        if username in clients:  # Condicional de ver si esta realmente en lista
            del clients[username]  # Comando oficial de Python para borrar una 'Key' del diccionario

        # Quitar el usuario de todos los grupos y rastros posibles en memoria
        for g_name, members in groups.items():  # Recorremos cada grupo activo junto con todos quienes lo habitan
            if username in members:  # Buscamos en su interior su existencia
                members.remove(username)  # Eliminamos su aparición con sintaxis de arrays

    broadcast(f"* {username} left the chat")  # Usamos broadcast indicando mundialmente lo que pasó (* es tipo admin sys)
    broadcast_state()  # Finalmente repintamos/reenviamos estados ya que los valores han decaido (un usuario fue substraido)


def private_message(target, msg):
    """Envia un mensaje confidencial 1a1."""
    with clients_lock:  # Bloque seguro...
        sock = clients.get(target)  # Obtenemos su socket a través de dicc clients pasandole el nombre apuntativo target.

    if sock:  # Confirmamos que el receptor existe (no es nulo o desconectado)
        send(sock, msg)  # Por último, simplemente lo arrojamos allá enviando los bytes directo


def handle_client(conn, addr):
    """Función principal a nivel de red para manejar un solo cliente (se ejecuta en un Hilo independiente)."""
    username = None  # Inicializamos la variable que contendrá su nombre en Nulo.
    file = conn.makefile("r")  # Creamos un objeto envoltorio parecido a un Archivo (File-like) que ayuda a leer líneas de manera fácil (readline)

    try:
        # Bucle de autenticación para asegurar que elijan un usuario válido y no repetido
        while True:
            send(conn, "Enter username:")  # Pedimos con mensaje que inserten su nombre
            username = file.readline().strip()  # Esperamos a que el cliente responda y removemos los espacios de los lados '\n'
            
            if not username:  # Condición si manda una cadena vacía (apretar enter sin escribir nada)
                send(conn, "Username cannot be empty")  # Regañamos al usuario informando mal uso
                continue  # Salta a inicio del While (le volvemos a preguntar su estado desde 0)

            with clients_lock:  # Cerramos ambiente (candado de hilos)
                if username in clients:  # Condición verificando si ese "username" ya forma parte de las llaves en el diccionario global clientes
                    send(conn, "Username already taken")  # Informamos problema redundante
                    continue  # Volvemos a pedir al principio

                clients[username] = conn  # Si paso acá, todo es valido. Procedemos de insertarlo a nuestra 'BBDD' global como usuario oficial.
                break  # Rompemos While porque la verificación fué exitosa

        print(f"{username} connected from {addr}")  # Log interno en la consola terminal del servidor físico (Para los creadores del program/SysAdmins)
        broadcast(f"* {username} joined the chat", username)  # Se avisa globalmente su presencia (Excepto él, con el parametro sender=username)
        broadcast_state()  # Re-lanzamos estado de conexión con las barritas completas para reflejar cambios

        # Bucle central para mantenerse escuchando toda la vida útil de su estado online. Aquí entra todo el trafico base.
        for line in file:
            msg = line.strip()  # Recolectamos el mensaje que haya entrado desde la computadora el cliente (limpio sin \n)

            if not msg:  # Si por un caso es espacio blanco se salta a recargar el for.
                continue

            if msg == "/users":  # Manejo del comando legacy: pedir manual usuarios
                with clients_lock:
                    users = ", ".join(clients.keys())  # Une a todos los clientes a string puro
                send(conn, f"Users: {users}")  # Devuelve a tí mismo quién anda listado
                continue  # Avanzamos y saltamos condicionales siguientes (Break/continue es clave para no leer ifs posteriores)
                
            if msg == "/groups":  # Manejo del comando legacy: pedir manual los grupos creados
                with clients_lock:
                    grps = ", ".join(groups.keys()) if groups else "No groups"  # Extrae llaves, sino pone mensaje default "No groups"
                send(conn, f"Groups: {grps}")  # Manda informe
                continue

            if msg.startswith("/creategroup "):  # Si el usuario mandó la instrucción que empieza con /creategroup
                g_name = msg.split(" ")[1]  # Cortamos el mensaje en cachos usando el espacio en blanco -> ('/creategroup', 'miGrupo'). El indice 1 tiene la palabra
                with clients_lock:  # Bloque seguro para accesar dict
                    if g_name in groups:  # Validamos doble existencia
                        send(conn, "Error: Group already exists")  # Respondemos que falló
                    else:
                        groups[g_name] = [username]  # Inicializamos dentro de grupos, la key del grupo teniendo su única array con nuestro username inicial ("Dueño").
                        send(conn, f"Group '{g_name}' created. You joined.")  # Avisamos con gusto de que lo hemos logrado uniendo 1ero
                broadcast_state()  # Mandamos refrescar el Panel lateral UI
                continue
                
            if msg.startswith("/join "):  # Si el usuario solicitó accesar
                g_name = msg.split(" ")[1]  # Partimos a pedazos por espacio para extraer solo el valor clave (ej: /join gatos) -> 'gatos'
                with clients_lock:
                    if g_name not in groups:  # Validamos existencia global de grupo
                        send(conn, "Error: Group does not exist")  # Mensaje fallido
                    else:
                        if username not in groups[g_name]:  # Buscamos en su array si no estoy integrado
                            groups[g_name].append(username)  # Me empujo con ".append(io)" dentro de la party list.
                            send(conn, f"Joined group '{g_name}'")  # Me congratulo por DM
                            # Notificar a los miembros del grupo actualizando
                            for member in groups[g_name]:  # Iteramos en el diccionario de grupos -> keys (member list)
                                if member != username and member in clients:  # Filtra que no sea de vuelta a nosotros (el que unió) ni un muerto online.
                                    send(clients[member], f"[{g_name}] * {username} joined the group")  # Envia global status sys.
                        else:
                            send(conn, "Error: Already in group")  # Rebote que dice 'Ya estas adentro'
                continue

            if msg.startswith("/gmsg "):  # Mandar Mensaje a Grupos ("/gmsg grupo hey gente como va")
                parts = msg.split(" ", 2)  # Cortaremos en exactamente 3 pedazos de esta forma: -> ["/gmsg", "grupo", "el resto del super largo mensaje x"]
                if len(parts) < 3:  # Validacion de falta de partes lógicas. Si la longitud total que se extrajo de arriba es menor de lo esperado (< 3)
                    send(conn, "Usage: /gmsg GROUP MESSAGE")  # Respondemos instrucción
                    continue
                g_name = parts[1]  # En el array extraemos como Variable el nombre de destino ("grupo") a apuntar.
                text = parts[2]    # En el array extraemos el texto extenso y el contenido purist.
                
                with clients_lock:
                    if g_name not in groups:  # Validar existencia de ese room de grupo
                        send(conn, "Error: Group does not exist")
                        continue
                    if username not in groups[g_name]:  # Validar si uno está unido para hablar
                        send(conn, "Error: You are not in this group")
                        continue
                    
                    # Mandar el mensaje en el server interno a todos los usuarios del grupito
                    for member in groups[g_name]:
                        if member in clients:  # Siempre y cuando este conéctado/disponible en clientes generales.
                            send(clients[member], f"[# {g_name}] {username}: {text}")  # Mandamos con prefix '[# nombregrupo] nombre: text'
                continue

            if msg.startswith("/msg "):  # Comando oficial de Private Messaging a alguien ('/msg pablo holo!')
                parts = msg.split(" ", 2)  # Separamos en -> ["/msg", "pablo", "holo!"]

                if len(parts) < 3:  # Validamos misma estructura requerida
                    send(conn, "Usage: /msg USER MESSAGE")
                    continue

                target = parts[1]  # target es la index 1 -> 'pablo'
                text = parts[2]  # index 2 -> mensaje
                with clients_lock:
                    exists = target in clients  # Busqueda ligera en clientes para devolver variable Boolean

                if not exists:  # Si isFalse que esta conectado..
                    send_to_self("User does not exist", username)  # Notificamelo a mi mismo
                    continue

                private_message(target, f"[@ {username}] {text}")  # Formato DM (Private Msg): le mandamos con decorativa de '[arroba Remitente] msj'
                continue

            # Default / Global (Cuando nada se pone - Ni Slash commands.. se asume escritura llana/normal)
            broadcast(f"[{username}] {msg}", username)  # Esparce en el viento este texto a cada conector vivo en todos los puertos.

    except Exception as e:
        print(f"Error con {addr}: {e}")  # Manejo de fallos pesados. (Conexion Perdida (BrokenPipe), Lag extremo, Disconect por Wifi etc). Imprime hacia terminal servidor.

    finally:
        # Se activa el bloque Finally invariablemente por sobre lo anterior. Sea que falló en except o cerro manual, ocurrirá lo que hay a continuación.
        if username:  # Condicional de si este pobre alma sin conexion habia alcanzado ya a nombrar su usuario antes de explotar
            remove_client(username)  # Le metemos al verdugo removedor y lo desintegramos globalmente.

        conn.close()  # Matamos el Socket Físico como tal liberando el Port file/descriptor en memoria red TCP de Linux/Windows.
        print(f"{username} disconnected")  # Log para el administrador


def start_srv():
    """Esta es la semilla/función matriz principal para configurar e iniciar la escucha central TCP/IP (El arranque inicial del Servidor entero)."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # En la familia AF_INET (IPv4), de tipo SOCK_STREAM (TCP) armaremos el ente superior.
    # SetSockOpt a opcion REUSEADDR en True: Le indica al OS Kernel que deje reciclar el puerto si acaba de reiniciarse. Combate "Address Already In Use".
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    srv.bind((HOST, PORT))  # Amarramos este socket a que escuche en nuestra IP ("0.0.0.0" interfaces disp) y el Puerto especifico (5050).
    srv.listen()  # Modificamos de stand-by, a modo centínal. Escuchando como pasivo y aceptando request formales futuros.

    print(f"Server running on {HOST}:{PORT}")  # Output log formal para la consola del admin visual.

    try:
        while True:  # Este while se queda congelado corriendo eternamente prestando oído.
            # .accept() es una funcion bloqueante. Detiene todo en la tupla actual aquí hasta que ALGUIEN mande una Solicitud y lo acepta abriendo paso devolviendo la (conx, ip)
            conn, addr = srv.accept()
            
            # Una vez destrabado por algun foraneo entrando... Inicia un Thread (Subproceso Ligero/Hilo Virtual). 
            # Apunta el target al motor principal (handle_client) con las caracteristicas de variables en arguments.
            # Y se invoca '.start()' de dicho objeto para mandarlo a correr detrás de escena paralelo mientras este While principal retoma estar de vuelta al '.accept()' .
            threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True,  # daemon=True Indica que una vez caiga abajo el proceso central maestro del App (ctrl+c), el resto de los hilitos hijos no oponga resistencias y muera junto a ella auto-mágicamente
            ).start()

    except KeyboardInterrupt:  # Intercepción física en base a señales OS. Si tú, el Admin, aprietas Control + C.. Detiene el flujo While True hacia acá.
        print("\nShutting down server...")  # Aviso en consola y entra al finally

    finally:
        with clients_lock:  # Con candadó aseguramos list de conexiones..
            sockets = list(clients.values())  # Extrae un extracto local listado en memoria

        for s in sockets:  # Navega a todo usuario y cliente del universo...
            try:
                send(s, "Server shutting down")  # Avisa una cadena simple explicativa del cataclismo. Esto sale sin formato como error base a las terminales clientes
                s.close()  # Desintegra la conx abruptamente ya que ni modo.. lo matamos local.
            except:
                pass  # Si el usuario matado fallo ignoralo.

        srv.close()  # Matamos al papá/srv. El socket general principal tcp que nos albergaba detendrá la escucha a puerto por fin.


if __name__ == "__main__":
    # Convención estándar de punto de origen de ejecución en Python. Si el archivo se corrió 'Directamente', se procede a prender el servidor y llamar start_srv().
    start_srv()
