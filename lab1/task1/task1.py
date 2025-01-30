import hashlib
import json
import socket
import threading
import time

# Blockchain Implementation
class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_block("Genesis Block")
        self.save_chain()

    def create_block(self, data, previous_hash="0"):
        index = len(self.chain)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        hash_value = self.calculate_hash(index, data, previous_hash, timestamp)
        block = {
            "index": index,
            "data": data,
            "hash": hash_value,
            "previous_hash": previous_hash,
            "timestamp": timestamp
        }
        self.chain.append(block)
        self.save_chain()
        return block
    
    def calculate_hash(self, index, data, previous_hash, timestamp):
        block_string = f"{index}{data}{previous_hash}{timestamp}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            prev_block = self.chain[i - 1]
            current_block = self.chain[i]
            if current_block["previous_hash"] != prev_block["hash"]:
                return False
            if self.calculate_hash(current_block["index"], current_block["data"],
                                   current_block["previous_hash"], current_block["timestamp"]) != current_block["hash"]:
                return False
        return True

    def save_chain(self):
        with open("blockchain.json", "w") as f:
            json.dump(self.chain, f, indent=4)

    def tamper_test(self):
        with open("blockchain.json", "r") as f:
            chain = json.load(f)
        
        if len(chain) > 1:
            chain[1]["data"] = "Tampered Data"
            
        with open("blockchain.json", "w") as f:
            json.dump(chain, f, indent=4)
        
        print("Tampered with blockchain.json. Checking validity...")
        with open("blockchain.json", "r") as f:
            self.chain = json.load(f)
        print("Blockchain valid:", self.is_chain_valid())

# Server Implementation
class Server:
    def __init__(self, host="127.0.0.1", port=5000):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.clients = []
        self.blockchain = Blockchain()
        print("Server started, waiting for connections...")

    def broadcast(self, message, sender):
        for client in self.clients:
            if client != sender:
                try:
                    client.send(message.encode())
                except:
                    self.clients.remove(client)

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if message:
                    print("Received:", message)
                    block = self.blockchain.create_block(message, self.blockchain.chain[-1]["hash"])
                    self.broadcast(json.dumps(block), client_socket)
            except:
                self.clients.remove(client_socket)
                break

    def start(self):
        while True:
            client_socket, addr = self.server.accept()
            self.clients.append(client_socket)
            print(f"Client {addr} connected")
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

# Client Implementation
class Client:
    def __init__(self, host="127.0.0.1", port=5000):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))
        threading.Thread(target=self.receive_messages).start()

    def receive_messages(self):
        while True:
            try:
                message = self.client.recv(1024).decode()
                print("New Block Received:", message)
            except:
                break

    def send_message(self, message):
        self.client.send(message.encode())

# Running the Server
server = Server()
threading.Thread(target=server.start).start()

# Running Clients
client_A = Client()
client_B = Client()

# Sending Messages
client_A.send_message("Hello, Shahbaz Siddiqui, NuFAST")
time.sleep(1)
client_B.send_message("Hello, Shahbaz Siddiqui1, NuFAST")
time.sleep(1)
client_A.send_message("Hello, Shahbaz Siddiqui2, NuFAST")

# Testing Immutability
time.sleep(2)
server.blockchain.tamper_test()
