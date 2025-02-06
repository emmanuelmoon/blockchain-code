import socket
import json
import hashlib
import threading

HOST = "127.0.0.1"
PORT = 5001
LEDGER_FILE = "ledger.json"

# Load or create the ledger
def load_ledger():
    try:
        with open(LEDGER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"clients": {}, "transactions": []}

def save_ledger(ledger):
    with open(LEDGER_FILE, "w") as file:
        json.dump(ledger, file, indent=4)

def hash_client(client_name):
    return hashlib.sha256(client_name.encode()).hexdigest()

def validate_client(client_hash):
    ledger = load_ledger()
    return client_hash in ledger["clients"]

def log_transaction(client_hash, message):
    ledger = load_ledger()
    ledger["transactions"].append({"client": client_hash, "message": message})
    save_ledger(ledger)

def sync_with_server2(transaction):
    try:
        conn = socket.create_connection(("127.0.0.1", 5002))
        conn.send(json.dumps(transaction).encode())
        conn.close()
    except ConnectionRefusedError:
        print("[ERROR] Could not sync with Server 2")

def handle_client(conn):
    data = conn.recv(1024).decode()
    client_name, message = data.split(": ")
    client_hash = hash_client(client_name)

    if validate_client(client_hash):
        transaction = {"client": client_hash, "message": message}
        log_transaction(client_hash, message)  # Record in ledger
        sync_with_server2(transaction)  # Send update to Server 2
        response = "[SERVER 1] Transaction verified and recorded."
    else:
        response = "[SERVER 1] Unauthorized client!"

    conn.send(response.encode())
    conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER 1] Listening on {HOST}:{PORT}")

    while True:
        conn, _ = server.accept()
        threading.Thread(target=handle_client, args=(conn,)).start()

start_server()
