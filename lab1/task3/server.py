import socket
import threading
import json
import hashlib
import hmac

class GoofyCoin:
    def __init__(self, coin_id, value, owner):
        self.coin_id = coin_id
        self.value = value
        self.owner = owner
        self.signature = self.sign_coin()

    def sign_coin(self):
        # Symmetric encryption using HMAC
        message = f"{self.coin_id}{self.value}{self.owner}".encode()
        secret_key = b'secret_key'  # In practice, this should be securely stored
        return hmac.new(secret_key, message, hashlib.sha256).hexdigest()

    def verify_coin(self):
        # Verify the coin's signature
        message = f"{self.coin_id}{self.value}{self.owner}".encode()
        secret_key = b'secret_key'
        expected_signature = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
        return self.signature == expected_signature

    def to_dict(self):
        return {
            "coin_id": self.coin_id,
            "value": self.value,
            "owner": self.owner,
            "signature": self.signature
        }

class Server:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.coins = {}
        self.lock = threading.Lock()

    def handle_client(self, conn, addr):
        print(f"Connected by {addr}")
        try:
            while True:
                data = conn.recv(1024).decode()
                if not data:
                    break

                request = json.loads(data)
                action = request.get("action")

                if action == "create_coin":
                    coin_id = request.get("coin_id")
                    value = request.get("value")
                    owner = request.get("owner")
                    coin = GoofyCoin(coin_id, value, owner)
                    with self.lock:
                        self.coins[coin_id] = coin
                    response = {"status": "success", "coin": coin.to_dict()}
                    conn.send(json.dumps(response).encode())

                elif action == "send_coin":
                    coin_id = request.get("coin_id")
                    new_owner = request.get("new_owner")
                    with self.lock:
                        if coin_id in self.coins:
                            coin = self.coins[coin_id]
                            if coin.verify_coin():
                                coin.owner = new_owner
                                coin.signature = coin.sign_coin()
                                response = {"status": "success", "coin": coin.to_dict()}
                            else:
                                response = {"status": "error", "message": "Invalid coin signature"}
                        else:
                            response = {"status": "error", "message": "Coin not found"}
                    conn.send(json.dumps(response).encode())

                elif action == "verify_coin":
                    coin_id = request.get("coin_id")
                    with self.lock:
                        if coin_id in self.coins:
                            coin = self.coins[coin_id]
                            is_valid = coin.verify_coin()
                            response = {"status": "success", "is_valid": is_valid}
                        else:
                            response = {"status": "error", "message": "Coin not found"}
                    conn.send(json.dumps(response).encode())

        finally:
            conn.close()
            print(f"Connection closed by {addr}")

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"Server listening on {self.host}:{self.port}")
            while True:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    server = Server()
    server.start()
