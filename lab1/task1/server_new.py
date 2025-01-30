import socket
import hashlib
import json
import threading

# Blockchain-inspired message hashing
def hash_message(data):
    message_json = json.dumps(data, sort_keys=True)
    return hashlib.sha256(message_json.encode()).hexdigest()

class BlockchainServer:
    def __init__(self, host="127.0.0.1", port=5000):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.clients = {}  # Stores connected clients
        self.messages = {}  # Stores message hashes

    def handle_client(self, conn, addr):
        print(f"🔗 Client connected from {addr}")
        self.clients[addr] = conn

        while True:
            try:
                data = conn.recv(1024).decode()
                if not data:
                    break

                # Load JSON data
                message = json.loads(data)
                sender = message["sender"]
                receiver = message["receiver"]
                content = message["content"]

                # Hash message and store it
                msg_hash = hash_message(message)
                self.messages[msg_hash] = message

                print(f"📩 Received from {sender}: {content} (Hash: {msg_hash})")

                # Send message to the intended recipient
                for client_addr, client_conn in self.clients.items():
                    if client_addr != addr:  # Send to the other client
                        client_conn.send(json.dumps({"msg_hash": msg_hash, "content": content}).encode())

            except Exception as e:
                print(f"❌ Error: {e}")
                break

        print(f"🔌 Client {addr} disconnected.")
        conn.close()
        del self.clients[addr]

    def start(self):
        print("🚀 Server started, waiting for connections...")
        while True:
            conn, addr = self.server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr)).start()

# Run the server
if __name__ == "__main__":
    BlockchainServer().start()
