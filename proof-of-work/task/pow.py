# Language: python
# filepath: lab3/task/pow.py
import hashlib
import time

def proof_of_work(data, difficulty=2):
    """
    A simple Proof of Work function that finds a nonce
    such that the hash has 'difficulty' leading zero pairs.
    
    :param data: The transaction data or block data to be hashed.
    :param difficulty: Number of leading zero pairs (e.g., difficulty=2 means "0000")
    :return: (nonce, hash_value, time_taken)
    """
    nonce = 0
    prefix = '0' * (difficulty * 2)  # Two zeros per difficulty level
    # print(f"Using prefix: {prefix}")  # Debug print removed
    start_time = time.time()

    while True:
        text = f"{data}{nonce}".encode()
        hash_value = hashlib.sha256(text).hexdigest()
        # Comment out the hash printing
        # print(hash_value)
        
        if hash_value.startswith(prefix):
            end_time = time.time()
            # Return with full precision (without rounding)
            return nonce, hash_value, (end_time - start_time)
        nonce += 1  # Increment nonce and retry

# Example Usage remains unchanged if you run pow.py directly.
if __name__ == '__main__':
    data = "Shahbaz"
    difficulty = 2  # Require two pairs of leading zeros (i.e., "0000")
    nonce, final_hash, time_taken = proof_of_work(data, difficulty)
    print("✅ Proof of Work Completed!")
    print(f"Nonce Found: {nonce}")
    print(f"Hash: {final_hash}")
    print(f"Time Taken: {time_taken} seconds")