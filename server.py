import socket
import threading
import json

HOST = "0.0.0.0"
PORT = 5000

clients = {}
clients_lock = threading.Lock()


def broadcast(message, sender):
    with clients_lock:
        for user, client in clients.items():
            if user != sender:
                try:
                    client.sendall(message.encode())
                except:
                    pass


def private_message(target, message):
    with clients_lock:
        if target in clients:
            try:
                clients[target].sendall(message.encode())
            except:
                pass


def handle_client(conn, addr):
    username = None
    try:
        login_data = conn.recv(1024).decode()
        data = json.loads(login_data)

        if data["type"] != "login":
            conn.close()
            return

        if not data["name"]:
            conn.close()
            return
        username = data["name"]

        with clients_lock:
            clients[username] = conn

        print(f"{username} connected from {addr}")

        broadcast(
            json.dumps({"type": "system", "message": f"{username} joined the chat"}),
            username,
        )

        while True:
            msg = conn.recv(1024).decode()
            if not msg:
                break

            data = json.loads(msg)
            message = data.get("message", "")

            if message == "/users":
                with clients_lock:
                    user_list = ", ".join(clients.keys())

                conn.sendall(
                    json.dumps(
                        {
                            "type": "system",
                            "message": f"Connected users: {user_list}",
                        }
                    ).encode()
                )

                continue

            if message.startswith("/msg "):
                parts = data["message"].split(" ", 2)

                if len(parts) < 3:
                    continue

                target = parts[1]
                message = parts[2]

                with clients_lock:
                    if target in clients:
                        clients[target].sendall(
                            json.dumps(
                                {
                                    "type": "private",
                                    "from": username,
                                    "message": message,
                                }
                            ).encode()
                        )

                continue

            if data["type"] == "broadcast":
                broadcast(
                    json.dumps(
                        {
                            "type": "message",
                            "from": username,
                            "message": data["message"],
                        }
                    ),
                    username,
                )

            elif data["type"] == "private":
                private_message(
                    data["to"],
                    json.dumps(
                        {
                            "type": "private",
                            "from": username,
                            "message": data["message"],
                        }
                    ),
                )

    except Exception as e:
        print(e)

    finally:
        with clients_lock:
            if username in clients:
                del clients[username]

        broadcast(
            json.dumps({"type": "system", "message": f"{username} left the chat"}),
            username,
        )

        conn.close()
        print(f"{username} disconnected")


def start_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind((HOST, PORT))
    srv.listen()

    print(f"Server running on {HOST}:{PORT}")

    while True:
        conn, addr = srv.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


if __name__ == "__main__":
    start_server()
