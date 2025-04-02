# clientB.py
import socket
import json
import hashlib

HOST = '127.0.0.1'
PORT = 65432

def client_program():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    client_socket.sendall("B".encode())  # Identify as Client B

    # Send Data 2 (example)
    data2 = "Hello, Shahbaz Siddiqui3, NuFAST"
    client_socket.sendall(json.dumps({
        "sender": "B",
        "data": data2
    }).encode())

    # Receive messages from server
    while True:
        response = client_socket.recv(1024).decode()
        if not response:
            break
        message = json.loads(response)
        print(f"Received from {message['sender']}: {message['data']}")
        # Verify hash
        calculated_hash = hashlib.sha256(json.dumps({
            "data": message['data']
        }).encode()).hexdigest()
        if calculated_hash != message['hash']:
            print("Warning: Data tampered!")

    client_socket.close()

if __name__ == "__main__":
    client_program()