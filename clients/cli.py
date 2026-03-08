import socket
import threading
import sys

HOST = "127.0.0.1"
PORT = 5050


def receive_messages(sock):
    file = sock.makefile("r")

    try:
        for line in file:
            print("\r" + line.strip())
            print("> ", end="", flush=True)
    except:
        pass

    print("\nDisconnected from server.")
    sys.exit()


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    file = sock.makefile("r")

    print(file.readline().strip())
    
    while True:
        username = input("> ")
        if not username:
             continue
             
        sock.sendall((username + "\n").encode())
        
        response = file.readline().strip()
        print(response)
        
        if "Username already taken" in response or "Username cannot be empty" in response:
             # El servidor pedirá de nuevo "Enter username:"
             prompt = file.readline().strip()
             print(prompt)
        else:
             # El servidor no mandó error, asumimos conexión exitosa.
             break

    thread = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    thread.start()

    try:
        while True:
            msg = input("> ")

            if not msg:
                continue

            sock.sendall((msg + "\n").encode())

    except KeyboardInterrupt:
        print("\nExiting...")

    finally:
        sock.close()


if __name__ == "__main__":
    main()
