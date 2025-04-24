import socket
import json
import threading

def client_actions(client_id, actions):
    host = '127.0.0.1'
    port = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        for action in actions:
            s.send(json.dumps(action).encode())
            data = s.recv(1024).decode()
            response = json.loads(data)
            print(f"Client {client_id} received: {response}")

# Define actions for each client
user1_actions = [
    {"action": "create_coin", "coin_id": "coin_1", "value": 100, "owner": "User1"},
    {"action": "send_coin", "coin_id": "coin_1", "new_owner": "User2"},
    {"action": "send_coin", "coin_id": "coin_1", "new_owner": "User3"}
]

user2_actions = [
    {"action": "verify_coin", "coin_id": "coin_1"}
]

user3_actions = [
    {"action": "verify_coin", "coin_id": "coin_1"}
]

# Create and start threads for each client
threading.Thread(target=client_actions, args=("User1", user1_actions)).start()
threading.Thread(target=client_actions, args=("User2", user2_actions)).start()
threading.Thread(target=client_actions, args=("User3", user3_actions)).start()
