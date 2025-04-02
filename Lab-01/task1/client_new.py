import socket
import hashlib
import json

# Blockchain-inspired hashing function
def hash_message(data):
    message_json = json.dumps(data, sort_keys=True)
    return hashlib.sha256(message_json.encode()).hexdigest()

class BlockchainClient:
    def __init__(self, name, host="127.0.0.1", port=5000):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))
        self.name = name
        print(f"✅ Connected to server as {name}")

    def send_message(self, receiver, content):
        message = {
            "sender": self.name,
            "receiver": receiver,
            "content": content
        }
        self.client.send(json.dumps(message).encode())

    def receive_messages(self):
        while True:
            try:
                data = self.client.recv(1024).decode()
                if not data:
                    break

                # Load received message
                message = json.loads(data)
                received_hash = message["msg_hash"]
                content = message["content"]

                # Verify integrity
                original_message = {"sender": "Unknown", "receiver": self.name, "content": content}
                computed_hash = hash_message(original_message)

                if received_hash == computed_hash:
                    print(f"📨 Verified Message Received: {content}")
                else:
                    print(f"⚠️ ERROR: Message tampered! Hash mismatch.")

            except Exception as e:
                print(f"❌ Error: {e}")
                break

    def start_receiving(self):
        import threading
        threading.Thread(target=self.receive_messages, daemon=True).start()

# Run the client
if __name__ == "__main__":
    name = input("Enter your name (A/B): ").strip()
    client = BlockchainClient(name)

    # Start receiving messages in the background
    client.start_receiving()

    while True:
        receiver = input("Enter receiver (A/B): ").strip()
        content = input("Enter message: ")
        client.send_message(receiver, content)
