import json
import hashlib
import random
import time
import threading
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization

# Constants
LEDGER_FILE = "blockchain_ledger.json"
REWARD = 6.25  # Block reward in BTC
DIFFICULTY = 4  # Mining difficulty

class BlockchainNode:
    def __init__(self):
        self.lock = threading.Lock()
        self.result = {}
        self.load_blockchain()

    def load_blockchain(self):
        """Initialize or load existing blockchain"""
        try:
            with open(LEDGER_FILE, "r") as file:
                self.blockchain = json.load(file)
        except FileNotFoundError:
            self.blockchain = []

    def save_blockchain(self):
        """Save blockchain to file"""
        with open(LEDGER_FILE, "w") as file:
            json.dump(self.blockchain, file, indent=4)

    @staticmethod
    def generate_keys():
        """Generate public-private key pair"""
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def sign_transaction(private_key, transaction_data):
        """Sign transaction with private key"""
        signature = private_key.sign(transaction_data.encode(), ec.ECDSA(hashes.SHA256()))
        return signature.hex()

    @staticmethod
    def verify_signature(public_key, transaction_data, signature):
        """Verify transaction signature"""
        try:
            public_key.verify(
                bytes.fromhex(signature),
                transaction_data.encode(),
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except:
            return False

    @staticmethod
    def calculate_hash(block_header):
        """Calculate SHA256 hash"""
        return hashlib.sha256(block_header.encode()).hexdigest()

    def proof_of_work(self, previous_hash, transactions, difficulty=DIFFICULTY):
        """Perform proof of work"""
        nonce = 0
        while True:
            block_header = f"{previous_hash}{transactions}{nonce}"
            block_hash = self.calculate_hash(block_header)
            if block_hash[:difficulty] == "0" * difficulty:
                return nonce, block_hash
            nonce += 1

    def validate_pow(self, block, difficulty=DIFFICULTY):
        """Validate proof of work of a block"""
        previous_hash = block["previous_hash"]
        transactions = f"{block['transactions']['sender']}->{block['transactions']['receiver']}:{block['transactions']['amount']}"
        nonce = block["nonce"]
        
        block_header = f"{previous_hash}{transactions}{nonce}"
        calculated_hash = self.calculate_hash(block_header)
        
        if calculated_hash != block["hash"]:
            return False, f"Hash mismatch! Calculated: {calculated_hash}, Stored: {block['hash']}"
        
        if not calculated_hash.startswith("0" * difficulty):
            return False, f"Hash doesn't meet difficulty requirement of {difficulty} leading zeros"
        
        return True, "Valid PoW"

    def mine_block(self, miner_id, previous_hash, transactions, difficulty):
        """Mine a new block"""
        # Verify transaction before mining
        sender_public_key = alice_public if transactions["sender"] == "Alice" else bob_public
        transaction_data = f"{transactions['sender']}->{transactions['receiver']}:{transactions['amount']}"
        
        if not self.verify_signature(sender_public_key, transaction_data, transactions["signature"]):
            print(f"{miner_id}: Invalid transaction! Rejecting block.")
            return
        
        print(f"{miner_id} is mining...")
        start_time = time.time()
        nonce, block_hash = self.proof_of_work(previous_hash, transaction_data, difficulty)
        end_time = time.time()
        print(f"{miner_id} found a block! Nonce: {nonce}, Hash: {block_hash} (Time: {end_time - start_time:.2f}s)")
        
        with self.lock:
            if "winner" not in self.result:
                self.result["winner"] = {
                    "miner": miner_id,
                    "previous_hash": previous_hash,
                    "transactions": transactions,
                    "reward": {"miner": miner_id, "amount": REWARD},
                    "nonce": nonce,
                    "hash": block_hash,
                    "timestamp": time.time()
                }

    def start_mining_competition(self, transaction):
        """Start mining competition with multiple miners"""
        previous_hash = self.blockchain[-1]["hash"] if self.blockchain else "0" * 64
        miners = ["Miner A", "Miner B", "Miner C", "Miner D", "Miner E", "Miner F"]
        threads = []

        for miner in miners:
            thread = threading.Thread(
                target=self.mine_block,
                args=(miner, previous_hash, transaction, DIFFICULTY)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Validate winning block by other nodes
        if "winner" in self.result:
            winning_block = self.result["winner"]
            print("\n=== Other Nodes Validating Winning Block ===")
            
            for miner in [m for m in miners if m != winning_block["miner"]]:
                is_valid, message = self.validate_pow(winning_block)
                if is_valid:
                    print(f"{miner}: ✅ Block is valid - {message}")
                else:
                    print(f"{miner}: ❌ Block validation failed - {message}")

            # Add block to blockchain if valid
            self.blockchain.append(winning_block)
            self.save_blockchain()
            print(f"\nBlockchain updated! Transaction confirmed. {winning_block['miner']} received {REWARD} BTC as reward.")
        else:
            print("No valid block was mined.")

def main():
    # Create blockchain node
    node = BlockchainNode()

    # Create users
    global alice_public, alice_private, bob_public, bob_private
    alice_private, alice_public = node.generate_keys()
    bob_private, bob_public = node.generate_keys()

    # Create sample transaction
    transaction = {
        "sender": "Alice",
        "receiver": "Bob",
        "amount": 5,
    }
    transaction_data = f"{transaction['sender']}->{transaction['receiver']}:{transaction['amount']}"
    transaction["signature"] = node.sign_transaction(alice_private, transaction_data)

    # Start mining competition
    node.start_mining_competition(transaction)

if __name__ == "__main__":
    main()