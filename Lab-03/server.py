import socket
import threading

def start_server(port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", port))
    server.listen(1)
    print(f"Server started on port {port}")

    while True:
        conn, addr = server.accept()
        print(f"Connected by {addr} on port {port}")
        conn.sendall(f"Hello from Server {port}".encode())
        conn.close()

# Creating three server threads
server_ports = [5000, 5001, 5002]
for port in server_ports:
    threading.Thread(target=start_server, args=(port,), daemon=True).start()
