import socket
import json
import threading

HOST = "127.0.0.1"
PORT = 5002

def handle_sync(conn):
    data = conn.recv(4096).decode()
    transaction = json.loads(data)
    print(f"[SERVER 2] Received Ledger Update: {transaction}")  # No local storage
    conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER 2] Listening on {HOST}:{PORT}")

    while True:
        conn, _ = server.accept()
        threading.Thread(target=handle_sync, args=(conn,)).start()

start_server()
