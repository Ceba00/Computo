import socket
import threading
import sys

HOST = "127.0.0.1"
PORT = 5000


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

    username = input("> ")
    sock.sendall((username + "\n").encode())

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
