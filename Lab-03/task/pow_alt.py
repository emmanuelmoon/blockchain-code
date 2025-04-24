import socket
import threading
import hashlib
import time
import random
import json


def format_time(timestamp):
    # Include microseconds
    return time.strftime('%H:%M:%S', time.localtime(timestamp)) + f".{int((timestamp % 1) * 1e6):06d}"


def proof_of_work(data, difficulty=2):
    """
    A simple Proof of Work function that finds a nonce
    such that the hash has 'difficulty' leading zero pairs.
    """
    nonce = 0
    prefix = '0' * (difficulty * 2)  # Two zeros per difficulty level
    start_time = time.time()

    while True:
        text = f"{data}{nonce}".encode()
        hash_value = hashlib.sha256(text).hexdigest()

        if hash_value.startswith(prefix):
            end_time = time.time()
            # Return nonce, hash, time taken, start and end time
            return nonce, hash_value, end_time - start_time, start_time, end_time

        nonce += 1  # Increment nonce and retry


def start_server(port, result_dict):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", port))
    server.listen(1)
    print(f"Server started on port {port}")

    data = "ProofOfWorkTask"
    difficulty = 2  # Adjust difficulty as needed
    nonce, final_hash, time_taken, start_time, end_time = proof_of_work(
        data, difficulty)
    server_hash = hashlib.sha256(f"Server{port}{data}".encode()).hexdigest()
    print(f"Port: {port}, Hash: {server_hash}")
    result_dict[port] = (time_taken, start_time, end_time,
                         nonce, final_hash, server_hash, data)


def client():
    user_data = input("Enter transaction data: ")
    server_ports = [5000, 5001, 5002]
    results = {}

    threads = []
    for port in server_ports:
        thread = threading.Thread(target=start_server, args=(port, results))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    if results:
        fastest_port = min(results, key=lambda x: results[x][0])
        fastest_data = results[fastest_port]
        ledger_entry = {
            "port": fastest_port,
            "nonce": fastest_data[3],
            "hash": fastest_data[4],
            "time_taken": fastest_data[0],
            "start_time": format_time(fastest_data[1]),
            "end_time": format_time(fastest_data[2]),
            "server_hash": fastest_data[5],
            "message": fastest_data[6]
        }
        try:
            with open("ledger.json", "r") as ledger_file:
                ledger = json.load(ledger_file)
                if not isinstance(ledger, list):
                    ledger = []
        except (FileNotFoundError, json.JSONDecodeError):
            ledger = []

        ledger.append(ledger_entry)

        with open("ledger.json", "w") as ledger_file:
            json.dump(ledger, ledger_file, indent=4)

        print(
            f"Fastest Server: {fastest_port}, Time: {fastest_data[0]:.6f} seconds")
        print(
            f"Start Time: {ledger_entry['start_time']}, End Time: {ledger_entry['end_time']}")
        print(
            f"Server Hash: {ledger_entry['server_hash']}, Message: {ledger_entry['message']}")
    else:
        print("No Proof of Work was performed.")


# Start the client to find the fastest server
client()
