import socket
import threading

SERVERS = [("127.0.0.1", 5001), ("127.0.0.1", 5002)]
CLIENT_NAME = "Client1"
MESSAGE = "Hello from Client1"

def send_message(server_host, server_port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((server_host, server_port))
        client.send(f"{CLIENT_NAME}: {MESSAGE}".encode())
        response = client.recv(1024).decode()
        print(f"[CLIENT 1] Response from {server_host}:{server_port} -> {response}")
    except ConnectionRefusedError:
        print(f"[CLIENT 1] Could not connect to {server_host}:{server_port}")
    finally:
        client.close()

threads = []
for host, port in SERVERS:
    thread = threading.Thread(target=send_message, args=(host, port))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()
