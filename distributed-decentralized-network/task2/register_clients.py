import json
import hashlib

LEDGER_FILE = "ledger.json"

def hash_client(client_name):
    """Generate SHA-256 hash for a given client name."""
    return hashlib.sha256(client_name.encode()).hexdigest()

def load_ledger():
    """Load ledger from JSON file, or create a new one if missing."""
    try:
        with open(LEDGER_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"clients": {}, "transactions": []}

def save_ledger(ledger):
    """Save updated ledger back to JSON file."""
    with open(LEDGER_FILE, "w") as file:
        json.dump(ledger, file, indent=4)

def register_clients(client_names):
    """Register new clients by hashing their names and storing them in the ledger."""
    ledger = load_ledger()

    for client in client_names:
        client_hash = hash_client(client)
        if client_hash not in ledger["clients"]:
            ledger["clients"][client_hash] = client
            print(f"[REGISTER] Added {client} with hash: {client_hash}")
        else:
            print(f"[INFO] {client} is already registered.")

    save_ledger(ledger)
    print("[SUCCESS] Ledger updated with new clients.")

if __name__ == "__main__":
    clients = ["Client1", "Client2"]
    register_clients(clients)
