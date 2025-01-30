import hashlib
import json
import socket
import threading
from datetime import datetime

class Block:
    def __init__(self, index, previous_hash, data, timestamp, block_hash=None):
        self.index = index
        self.previous_hash = previous_hash
        self.data = data
        self.timestamp = timestamp
        self.hash = block_hash if block_hash else self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "data": self.data,
            "timestamp": self.timestamp
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = []
        self.load_chain_from_json()  # Load existing chain from JSON

    def load_chain_from_json(self):
        try:
            with open("messages.json", "r") as f:
                existing_data = json.load(f)
                for block_data in existing_data:
                    block = Block(
                        index=block_data["index"],
                        previous_hash=block_data["previous_hash"],
                        data=block_data["data"],
                        timestamp=block_data["timestamp"],
                        block_hash=block_data["hash"]
                    )
                    self.chain.append(block)
                print("Chain loaded from JSON.")
        except (FileNotFoundError, json.JSONDecodeError):
            self.chain = [self.create_genesis_block()]
            self.save_to_json(self.chain[0])

    def create_genesis_block(self):
        return Block(0, "0", "Genesis Block", datetime.now().isoformat())

    def add_block(self, data):
        previous_block = self.chain[-1]
        new_block = Block(
            index=previous_block.index + 1,
            previous_hash=previous_block.hash,
            data=data,
            timestamp=datetime.now().isoformat()
        )
        self.chain.append(new_block)
        self.save_to_json(new_block)
        return new_block

    def save_to_json(self, block):
        block_data = {
            "index": block.index,
            "data": block.data,
            "hash": block.hash,
            "previous_hash": block.previous_hash,
            "timestamp": block.timestamp
        }
        try:
            with open("messages.json", "r") as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []
        existing_data.append(block_data)
        with open("messages.json", "w") as f:
            json.dump(existing_data, f, indent=4)

    def verify_chain(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            if current.hash != current.calculate_hash():
                print(f"Block {current.index} hash mismatch!")
                return False
            if current.previous_hash != previous.hash:
                print(f"Block {current.index} previous hash mismatch!")
                return False
        return True

# Server setup and client handling
HOST = '127.0.0.1'
PORT = 65432
clients = {}
blockchain = Blockchain()

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            message = json.loads(data)
            sender = message['sender']
            content = message['data']

            new_block = blockchain.add_block(content)
            print(f"Block #{new_block.index} added: {content}")
            print(f"Hash: {new_block.hash}")

            # Verify chain after adding block
            is_valid = blockchain.verify_chain()
            print(f"Chain valid: {is_valid}\n")

            receiver = 'B' if sender == 'A' else 'A'
            if receiver in clients:
                clients[receiver].sendall(json.dumps({
                    "sender": sender,
                    "data": content,
                    "hash": new_block.hash
                }).encode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("Server started. Waiting for clients...")
        while True:
            conn, addr = s.accept()
            client_id = conn.recv(1024).decode()
            clients[client_id] = conn
            threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()