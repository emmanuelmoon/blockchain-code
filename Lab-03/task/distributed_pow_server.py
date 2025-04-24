# Language: python
# filepath: lab3/task/distributed_pow_server.py
import socket
import threading
import time
import json
import datetime
from pow import proof_of_work  # see [lab3/task/pow.py](lab3/task/pow.py)

# Global variables for winner notification and ledger updates
winner_event = threading.Event()
ledger_lock = threading.Lock()
ledger_file = "ledger.json"

def append_to_ledger(entry):
    with ledger_lock:
        try:
            with open(ledger_file, "r") as f:
                ledger = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            ledger = []
        ledger.append(entry)
        with open(ledger_file, "w") as f:
            json.dump(ledger, f, indent=4)
    print("Ledger updated with:", entry)

def handle_pow(node_name, tx_data, difficulty=2):
    # Use microsecond precision for times
    start_dt = datetime.datetime.now()
    start_time_formatted = start_dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    print(f"{node_name} started POW at {start_time_formatted}")
    
    # Each node starts working on the proof of work.
    nonce, final_hash, time_taken = proof_of_work(tx_data, difficulty)
    
    end_dt = datetime.datetime.now()
    end_time_formatted = end_dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    print(f"{node_name} completed POW at {end_time_formatted}")
    
    # Check if another node has already won
    if not winner_event.is_set():
        winner_event.set()  # Mark that this node is the winner
        result = {
            "node": node_name,
            "transaction_data": tx_data,
            "nonce": nonce,
            "hash": final_hash,
            "time_taken": time_taken,
            "start_time": start_time_formatted,
            "end_time": end_time_formatted
        }
        print(f"{node_name} wins the POW competition!")
        append_to_ledger(result)
    else:
        print(f"{node_name} finished POW, but another node already won.")

def node_server(port, node_name):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", port))
    server.listen(1)
    print(f"{node_name} started on port {port}")

    while True:
        conn, addr = server.accept()
        print(f"{node_name} got connection from {addr}")
        tx_data = conn.recv(1024).decode().strip()
        if tx_data:
            print(f"{node_name} received transaction: {tx_data}")
            # Reset the winner event if a new transaction arrives
            if winner_event.is_set():
                winner_event.clear()
            # Start POW on this node (each node works concurrently)
            threading.Thread(target=handle_pow, args=(node_name, tx_data, 2)).start()
        conn.sendall("Transaction received. Processing POW...".encode())
        conn.close()

# Start decentralized nodes (threads)
nodes = [("Node1", 5000), ("Node2", 5001), ("Node3", 5002)]
for node_name, port in nodes:
    threading.Thread(target=node_server, args=(port, node_name), daemon=True).start()

# Keep the main thread alive indefinitely
while True:
    time.sleep(1)