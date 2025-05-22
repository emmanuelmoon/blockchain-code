import json
import hashlib
import random
import time
import threading

LEDGER_FILE = "blockchain_ledger.json"
REWARD = 6.25  # Block reward in BTC
DIFFICULTY = 4  # Number of leading zeros required

# Initialize blockchain ledger
try:
    with open(LEDGER_FILE, "r") as file:
        blockchain = json.load(file)
except FileNotFoundError:
    blockchain = []

def calculate_hash(block_header):
    return hashlib.sha256(block_header.encode()).hexdigest()

def proof_of_work(previous_hash, transactions, difficulty):
    nonce = 0
    while True:
        block_header = f"{previous_hash}{json.dumps(transactions)}{nonce}"
        block_hash = calculate_hash(block_header)
        if block_hash[:difficulty] == "0" * difficulty:
            return nonce, block_hash
        nonce += 1

def verify_block(block, difficulty):
    block_header = f"{block['previous_hash']}{json.dumps(block['transactions'])}{block['nonce']}"
    block_hash = calculate_hash(block_header)
    return block_hash[:difficulty] == "0" * difficulty and block_hash == block["hash"]

def mine_block(miner_id, previous_hash, transactions, difficulty, result, lock):
    print(f"Miner {miner_id} is mining...")
    start_time = time.time()
    
    if miner_id == "Miner E":  # Miner E sends an invalid nonce
        nonce = random.randint(1, 1000000)  # Arbitrary invalid nonce
        block_hash = calculate_hash(f"{previous_hash}{json.dumps(transactions)}{nonce}")
    else:
        nonce, block_hash = proof_of_work(previous_hash, transactions, difficulty)
    
    end_time = time.time()
    print(f"Miner {miner_id} found a block! Nonce: {nonce}, Hash: {block_hash} (Time: {end_time - start_time:.2f}s)")
    
    with lock:
        if "winner" not in result and verify_block({
            "previous_hash": previous_hash,
            "transactions": transactions,
            "nonce": nonce,
            "hash": block_hash
        }, difficulty):
            result["winner"] = {
                "miner": miner_id,
                "previous_hash": previous_hash,
                "transactions": transactions,
                "reward": {"miner": miner_id, "amount": REWARD},
                "nonce": nonce,
                "hash": block_hash,
                "timestamp": time.time()
            }

# Generate random transactions
def generate_transactions(num=5):
    users = ["Alice", "Bob", "Charlie", "Dave", "Eve"]
    transactions = []
    for _ in range(num):
        sender, receiver = random.sample(users, 2)
        amount = round(random.uniform(0.1, 5), 2)
        transactions.append({"sender": sender, "receiver": receiver, "amount": amount})
    return transactions

# Get the last block hash
previous_hash = blockchain[-1]["hash"] if blockchain else "0" * 64
miners = ["Miner A", "Miner B", "Miner C", "Miner D", "Miner E"]
threads = []
result = {}
lock = threading.Lock()
transactions = generate_transactions()

def start_mining(miner):
    mine_block(miner, previous_hash, transactions, DIFFICULTY, result, lock)

for miner in miners:
    thread = threading.Thread(target=start_mining, args=(miner,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

if "winner" in result:
    new_block = result["winner"]
    
    # Block verification by network
    if verify_block(new_block, DIFFICULTY):
        blockchain.append(new_block)
        with open(LEDGER_FILE, "w") as file:
            json.dump(blockchain, file, indent=4)
        print(f"Blockchain updated! Transaction confirmed. {new_block['miner']} received {REWARD} BTC as a reward.")
    else:
        print(f"Block mined by {new_block['miner']} is invalid and rejected by the network.")
