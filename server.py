import socket
import threading

HOST = "0.0.0.0"
PORT = 5050

clients = {}
groups = {}  # { group_name: [user_list] }
clients_lock = threading.Lock()


def send(sock, msg):
    try:
        sock.sendall((msg + "\n").encode())
    except:
        pass


def broadcast(msg, sender=None):
    dead = []
    with clients_lock:
        items = list(clients.items())

    for user, sock in items:
        if user == sender:
            continue
        try:
            send(sock, msg)
        except:
            dead.append(user)

    for user in dead:
        remove_client(user)


def send_to_self(msg, sender):
    with clients_lock:
        sock = clients.get(sender)
    if sock:
        send(sock, msg)


def broadcast_state():
    """ Envia la lista de usuarios y grupos a todos """
    with clients_lock:
        user_list = ",".join(clients.keys())
        group_list = ",".join(groups.keys())
        state_msg = f"STATE:{user_list}|{group_list}"
        
        for sock in clients.values():
            send(sock, state_msg)


def remove_client(username):
    with clients_lock:
        if username in clients:
            del clients[username]
        # Quitar el usuario de todos los grupos
        for g_name, members in groups.items():
            if username in members:
                members.remove(username)

    broadcast(f"* {username} left the chat")
    broadcast_state()


def private_message(target, msg):
    with clients_lock:
        sock = clients.get(target)

    if sock:
        send(sock, msg)


def handle_client(conn, addr):
    username = None
    file = conn.makefile("r")

    try:
        while True:
            send(conn, "Enter username:")
            username = file.readline().strip()
            
            if not username:
                send(conn, "Username cannot be empty")
                continue

            with clients_lock:
                if username in clients:
                    send(conn, "Username already taken")
                    continue
                clients[username] = conn
                break

        print(f"{username} connected from {addr}")
        broadcast(f"* {username} joined the chat", username)
        broadcast_state()

        for line in file:
            msg = line.strip()

            if not msg:
                continue

            if msg == "/users":
                with clients_lock:
                    users = ", ".join(clients.keys())
                send(conn, f"Users: {users}")
                continue
                
            if msg == "/groups":
                with clients_lock:
                    grps = ", ".join(groups.keys()) if groups else "No groups"
                send(conn, f"Groups: {grps}")
                continue

            if msg.startswith("/creategroup "):
                g_name = msg.split(" ")[1]
                with clients_lock:
                    if g_name in groups:
                        send(conn, "Error: Group already exists")
                    else:
                        groups[g_name] = [username]
                        send(conn, f"Group '{g_name}' created. You joined.")
                broadcast_state()
                continue
                
            if msg.startswith("/join "):
                g_name = msg.split(" ")[1]
                with clients_lock:
                    if g_name not in groups:
                        send(conn, "Error: Group does not exist")
                    else:
                        if username not in groups[g_name]:
                            groups[g_name].append(username)
                            send(conn, f"Joined group '{g_name}'")
                            # Notify group members
                            for member in groups[g_name]:
                                if member != username and member in clients:
                                    send(clients[member], f"[{g_name}] * {username} joined the group")
                        else:
                            send(conn, "Error: Already in group")
                continue

            if msg.startswith("/gmsg "):
                parts = msg.split(" ", 2)
                if len(parts) < 3:
                    send(conn, "Usage: /gmsg GROUP MESSAGE")
                    continue
                g_name = parts[1]
                text = parts[2]
                
                with clients_lock:
                    if g_name not in groups:
                        send(conn, "Error: Group does not exist")
                        continue
                    if username not in groups[g_name]:
                        send(conn, "Error: You are not in this group")
                        continue
                    
                    # Mandar a todos los miembros del grupo
                    for member in groups[g_name]:
                        if member in clients:
                            send(clients[member], f"[# {g_name}] {username}: {text}")
                continue

            if msg.startswith("/msg "):
                parts = msg.split(" ", 2)

                if len(parts) < 3:
                    send(conn, "Usage: /msg USER MESSAGE")
                    continue

                target = parts[1]
                text = parts[2]
                with clients_lock:
                    exists = target in clients

                if not exists:
                    send_to_self("User does not exist", username)
                    continue

                private_message(target, f"[@ {username}] {text}")
                continue

            # Default: Broadcast global
            broadcast(f"[{username}] {msg}", username)

    except Exception as e:
        print(f"Error with {addr}: {e}")

    finally:
        if username:
            remove_client(username)

        conn.close()
        print(f"{username} disconnected")


def start_srv():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen()

    print(f"Server running on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = srv.accept()
            threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True,
            ).start()

    except KeyboardInterrupt:
        print("\nShutting down server...")

    finally:
        with clients_lock:
            sockets = list(clients.values())

        for s in sockets:
            try:
                send(s, "Server shutting down")
                s.close()
            except:
                pass

        srv.close()


if __name__ == "__main__":
    start_srv()
