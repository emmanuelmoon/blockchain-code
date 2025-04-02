import hashlib
import json

class BlockchainMessenger:
    def __init__(self):
        self.chain = []
    
    def hash_data(self, data):
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def add_message(self, sender, receiver, message):
        prev_hash = self.chain[-1]["hash"] if self.chain else None
        data = {
            "sender": sender,
            "receiver": receiver,
            "message": message
        }
        message_hash = self.hash_data(data)
        block = {
            "data": data,
            "hash": message_hash,
            "prev_hash": prev_hash
        }
        self.chain.append(block)
        return block
    
    def get_message_by_hash(self, target_hash):
        for block in self.chain:
            if block["hash"] == target_hash:
                return block
        return None
    
    def verify_integrity(self):
        for i in range(1, len(self.chain)):
            expected_hash = self.hash_data(self.chain[i]["data"])
            if expected_hash != self.chain[i]["hash"] or self.chain[i]["prev_hash"] != self.chain[i-1]["hash"]:
                return False
        return True
    
    def save_messages_to_json(self, filename="messages.json"):
        with open(filename, "w") as file:
            json.dump(self.chain, file, indent=4)

messenger = BlockchainMessenger()

msg1 = messenger.add_message("A", "Server", "Hello, Shahbaz Siddiqui, NuFAST")
msg2 = messenger.add_message("Server", "B", "Hello, Shahbaz Siddiqui3, NuFAST")
msg3 = messenger.add_message("B", "A", "Hello, Shahbaz Siddiqui2, NuFAST")

retrieved_data2 = messenger.get_message_by_hash(msg2["hash"])
print("Retrieved Data 2:", retrieved_data2)

print("Blockchain Integrity Verified:", messenger.verify_integrity())

if(messenger.verify_integrity()):
    messenger.save_messages_to_json()

messenger.chain[1]["data"]["message"] = "Tampered Message"

print("Blockchain Integrity After Tampering:", messenger.verify_integrity())

if(messenger.verify_integrity()):
    messenger.save_messages_to_json()
