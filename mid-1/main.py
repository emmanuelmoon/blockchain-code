import json
import hashlib
import random
import time
import threading

# Ledger file to store blockchain data
LEDGER_FILE = "blockchain_ledger.json"
REWARD = 6.25  # Block reward in BTC

# Simulated transaction
transaction = {
    "sender": "Alice",
    "receiver": "Bob",
    "amount": 5,
    "signature": "Alice_signed_tx"
}

# Initialize blockchain ledger
try:
    with open(LEDGER_FILE, "r") as file:
        blockchain = json.load(file)
except FileNotFoundError:
    blockchain = []

def calculate_hash(block_header):
    return hashlib.sha256(block_header.encode()).hexdigest()

def proof_of_work(previous_hash, transactions, difficulty=4):
    nonce = 0
    while True:
        block_header = f"{previous_hash}{transactions}{nonce}"
        block_hash = calculate_hash(block_header)
        if block_hash[:difficulty] == "0" * difficulty:
            return nonce, block_hash
        nonce += 1

def mine_block(miner_id, previous_hash, transactions, difficulty, result, lock):
    print(f"Miner {miner_id} is mining...")
    start_time = time.time()
    nonce, block_hash = proof_of_work(previous_hash, transactions, difficulty)
    end_time = time.time()
    print(f"Miner {miner_id} found a block! Nonce: {nonce}, Hash: {block_hash} (Time: {end_time - start_time:.2f}s)")
    
    with lock:
        if "winner" not in result:  # Ensure only the first miner to solve PoW wins
            result["winner"] = {
                "miner": miner_id,
                "previous_hash": previous_hash,
                "transactions": transactions,
                "reward": {"miner": miner_id, "amount": REWARD},
                "nonce": nonce,
                "hash": block_hash,
                "timestamp": time.time()
            }

# Simulate mining competition with multithreading
previous_hash = blockchain[-1]["hash"] if blockchain else "0" * 64
miners = ["Miner A", "Miner B", "Miner C", "Miner D", "Miner E", "Miner F"]
threads = []
result = {}
lock = threading.Lock()

def start_mining(miner):
    mine_block(miner, previous_hash, transaction, 4, result, lock)

for miner in miners:
    thread = threading.Thread(target=start_mining, args=(miner,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

new_block = result["winner"]

# Add block to blockchain
blockchain.append(new_block)
with open(LEDGER_FILE, "w") as file:
    json.dump(blockchain, file, indent=4)

print(f"Blockchain updated! Transaction confirmed. {new_block['miner']} received {REWARD} BTC as a reward.")
