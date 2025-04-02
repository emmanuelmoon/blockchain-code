import json
import hashlib
import random
import time
import threading
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization

LEDGER_FILE = "blockchain_ledger.json"
REWARD = 6.25  # Block reward in BTC
DIFFICULTY = 4  # Number of leading zeros required

# Generate key pair for a user
def generate_keys():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key

# Sign a transaction using the sender's private key
def sign_transaction(private_key, transaction_data):
    signature = private_key.sign(transaction_data.encode(), ec.ECDSA(hashes.SHA256()))
    return signature.hex()

# Verify a transaction's signature
def verify_signature(public_key, transaction_data, signature):
    try:
        public_key.verify(bytes.fromhex(signature), transaction_data.encode(), ec.ECDSA(hashes.SHA256()))
        return True
    except:
        return False

# Create users (Alice and Bob)
alice_private, alice_public = generate_keys()
bob_private, bob_public = generate_keys()

# Simulated transaction
transaction = {
    "sender": "Alice",
    "receiver": "Bob",
    "amount": 5,
}
transaction_data = f"{transaction['sender']}->{transaction['receiver']}:{transaction['amount']}"
transaction["signature"] = sign_transaction(alice_private, transaction_data)

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
    # Verify transaction before mining
    sender_public_key = alice_public if transactions["sender"] == "Alice" else bob_public
    transaction_data = f"{transactions['sender']}->{transactions['receiver']}:{transactions['amount']}"
    
    if not verify_signature(sender_public_key, transaction_data, transactions["signature"]):
        print(f"Miner {miner_id}: Invalid transaction! Rejecting block.")
        return
    
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

# Get the last block hash
previous_hash = blockchain[-1]["hash"] if blockchain else "0" * 64
miners = ["Miner A", "Miner B", "Miner C", "Miner D", "Miner E", "Miner F"]
threads = []
result = {}
lock = threading.Lock()

def start_mining(miner):
    mine_block(miner, previous_hash, transaction, DIFFICULTY, result, lock)

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
else:
    print("No valid block was mined.")