import socket
import threading

HOST = "0.0.0.0"
PORT = 5050

clients = {}
clients_lock = threading.Lock()


def send(sock, msg):
    sock.sendall((msg + "\n").encode())


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
        try:
            send(sock, msg)
        except:
            pass


def remove_client(username):
    with clients_lock:
        if username in clients:
            del clients[username]

    broadcast(f"* {username} left the chat")


def private_message(target, msg):
    with clients_lock:
        sock = clients.get(target)

    if sock:
        try:
            send(sock, msg)
        except:
            remove_client(target)


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

        for line in file:
            msg = line.strip()

            if not msg:
                continue

            if msg == "/users":
                with clients_lock:
                    users = ", ".join(clients.keys())

                send(conn, f"Users: {users}")
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

                private_message(target, f"[PM from {username}] {text}")
                continue

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
