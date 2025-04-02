import base64
import hmac
import hashlib
import json
import socket
import time
from cryptography.fernet import Fernet

# Generate a Fernet key (shared secret)
key = Fernet.generate_key()
cipher = Fernet(key)

# HMAC signing key (shared secret)
hmac_key = b"super_secret_hmac_key"

# Store processed transactions to prevent double spending
processed_transactions = set()

def sign_message(message: str) -> str:
    """Create an HMAC signature for a message."""
    signature = hmac.new(hmac_key, message.encode(), hashlib.sha256).hexdigest()
    return signature

def verify_signature(message: str, signature: str) -> bool:
    """Verify the HMAC signature."""
    expected_signature = sign_message(message)
    return hmac.compare_digest(expected_signature, signature)

def encrypt_message(message: str) -> str:
    """Encrypts the message with Fernet."""
    return cipher.encrypt(message.encode()).decode()

def decrypt_message(encrypted_message: str) -> str:
    """Decrypts the message with Fernet."""
    return cipher.decrypt(encrypted_message.encode()).decode()

def retry_connection(target, retries=5, delay=1):
    """Retry connecting to the server with a delay."""
    for _ in range(retries):
        try:
            target()
            return
        except ConnectionRefusedError:
            time.sleep(delay)
    print("Failed to connect after retries.")

def client1():
    """Client 1: Creates, signs, encrypts, and sends a message."""
    message = "coin: 10"
    signature = sign_message(message)
    data = json.dumps({"message": message, "signature": signature})
    encrypted_data = encrypt_message(data)

    def send_message():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("localhost", 12345))
            s.sendall(encrypted_data.encode())
            print("Client 1 sent encrypted message.")

    retry_connection(send_message)

def client2():
    """Client 2: Receives, decrypts, verifies, re-signs, and displays the message."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 12345))
        s.listen()
        print("Client 2 is listening...")
        while True:
            conn, _ = s.accept()
            with conn:
                encrypted_data = conn.recv(1024).decode()
                decrypted_data = decrypt_message(encrypted_data)
                data = json.loads(decrypted_data)
                message, received_signature = data["message"], data["signature"]

                if verify_signature(message, received_signature):
                    if message in processed_transactions:
                        print("Double spending detected! Rejecting transaction.")
                    else:
                        processed_transactions.add(message)
                        print("Client 2 verified signature.")
                        new_signature = sign_message(message)
                        print(f"Received message: {message}, Signed again: {new_signature}")
                else:
                    print("Signature verification failed!")


if __name__ == "__main__":
    import threading
    t1 = threading.Thread(target=client2)
    t1.start()
    time.sleep(1)  # Ensure the server starts first
    t2 = threading.Thread(target=client1)
    t2.start()
    t2.join()
