import json
import time
import multichain

###################################### Server Connection ############################
# Update these values to match your chain’s configuration:
rpcuser = "multichainrpc"
rpcpassword = "DiYjvAYu8FpmCBKsRd5Pvp6mSqUpPizZpdNbFbcS8an8"
rpchost = "127.0.0.1"       # Use localhost if running on the same machine
rpcport = "7204"            # Must match the "Listening for API requests" port from your daemon output
chainname = "mychain"       # The chain name as created with multichain-util

# Initialize MultiChain client
mc = multichain.MultiChainClient(rpchost, rpcport, rpcuser, rpcpassword)
mc.setoption("chainname", chainname)

###################################### Helper: Grant Permissions ############################
def grant_permissions(address):
    # Grant 'send,receive' permissions to the address.
    grant_txid = mc.grant(address, "send,receive")
    print(f"Granted permissions to {address}: {grant_txid}")
    # Allow time for the permission to take effect
    time.sleep(1)

###################################### Step 1: Create a Stream ############################
def create_stream(stream_name):
    # Check if the stream already exists
    streams = mc.liststreams()
    if not any(stream['name'] == stream_name for stream in streams):
        print(f"Creating stream: {stream_name}")
        txid = mc.create('stream', stream_name, True)  # Create a new stream (open to writes)
        print(f"Stream created with TXID: {txid}")
        # Wait briefly for the chain to process the creation
        time.sleep(2)
    else:
        print(f"Stream '{stream_name}' already exists.")
    # Subscribe to the stream
    mc.subscribe([stream_name])
    print(f"Subscribed to stream: {stream_name}")

###################################### Step 2: Create Three Addresses ############################
def create_addresses():
    address1 = mc.getnewaddress()
    address2 = mc.getnewaddress()
    address3 = mc.getnewaddress()

    print("Address 1:", address1)
    print("Address 2:", address2)
    print("Address 3:", address3)
    
    # Grant send and receive permissions to each address
    grant_permissions(address1)
    grant_permissions(address2)
    grant_permissions(address3)

    return address1, address2, address3

###################################### Step 3: Perform Transactions and Publish to Stream ############################
def perform_transaction(sender, receiver, amount, stream_name):
    # Issue asset to sender before sending, if needed.
    # Note: In a production scenario, you would issue the asset once.
    print(f"Issuing asset 'coin' to {sender} (if not already issued)...")
    issue_txid = mc.issue(sender, 'coin', amount, 1)
    print("Issue TXID:", issue_txid)
    # Wait for issuance confirmation (polling would be preferred in production)
    time.sleep(2)

    # Send asset from sender to receiver
    print(f"Sending {amount} of 'coin' from {sender} to {receiver}...")
    txid = mc.sendassetfrom(sender, receiver, 'coin', amount)
    if not txid:
        print("Asset transaction failed!")
        print("RPC Error code:", mc.errorcode())
        print("RPC Error message:", mc.errormessage())
        return None
    print("Asset transaction initiated, txid:", txid)

    # Wait for the transaction to be confirmed (adjust as needed)
    time.sleep(5)

    # Publish transaction details to the stream (global ledger)
    transaction_details = {
        'TxId': txid,
        'sender': sender,
        'receiver': receiver,
        'amount': amount,
        'timestamp': int(time.time())
    }
    pub_txid = mc.publish(stream_name, 'transactions', {'json': transaction_details})
    print(f"Transaction published to stream '{stream_name}' with TXID: {pub_txid}")
    return txid

###################################### Step 4: Maintain Private Ledgers ############################
def get_private_ledger(address, stream_name):
    # Retrieve all transactions (using key 'transactions') from the stream
    transactions = mc.liststreamkeyitems(stream_name, 'transactions')
    # Filter transactions involving the address (as sender or receiver)
    private_ledger = []
    for tx in transactions:
        try:
            data = tx['data']['json']
        except Exception as e:
            print("Error parsing transaction data:", e)
            continue
        if data.get('sender') == address or data.get('receiver') == address:
            private_ledger.append(tx)
    return private_ledger

###################################### Step 5: Design a Global Ledger System ############################
def update_global_ledger(stream_name):
    # Retrieve all transactions from the stream keyed under 'transactions'
    transactions = mc.liststreamkeyitems(stream_name, 'transactions')
    # Extract and return transaction summaries
    global_ledger = [tx['data']['json'] for tx in transactions if 'data' in tx and 'json' in tx['data']]
    return global_ledger

###################################### Bonus Challenge: View Transaction History ############################
def view_transaction_history(address, stream_name):
    global_ledger = update_global_ledger(stream_name)
    history = [tx for tx in global_ledger if tx.get('sender') == address or tx.get('receiver') == address]
    return history

###################################### Main Execution ############################
if __name__ == "__main__":
    # Display chain info and wallet addresses
    chain_info = mc.getinfo()
    print("Chain info:", chain_info)
    
    wallet_addresses = mc.getaddresses()
    print("Wallet Addresses:", wallet_addresses)
    
    # Step 1: Create a stream for transaction summaries (global ledger)
    stream_name = "GlobalStream"
    create_stream(stream_name)

    # Step 2: Create three addresses (you can comment this out to use existing addresses)
    address1, address2, address3 = create_addresses()

    # Step 3: Perform asset transactions and publish details to the stream
    print("\nPerforming transactions...")
    txid1 = perform_transaction(address1, address2, 10, stream_name)
    txid2 = perform_transaction(address2, address3, 5, stream_name)
    txid3 = perform_transaction(address3, address1, 3, stream_name)

    print("Transaction 1 ID:", txid1)
    print("Transaction 2 ID:", txid2)
    print("Transaction 3 ID:", txid3)

    # Step 4: Retrieve and display each address’s private ledger (filtered transactions)
    print("\nPrivate Ledgers:")
    ledger1 = get_private_ledger(address1, stream_name)
    ledger2 = get_private_ledger(address2, stream_name)
    ledger3 = get_private_ledger(address3, stream_name)

    print("Private Ledger for Address 1:", json.dumps(ledger1, indent=4))
    print("Private Ledger for Address 2:", json.dumps(ledger2, indent=4))
    print("Private Ledger for Address 3:", json.dumps(ledger3, indent=4))

    # Step 5: Update and display the global ledger (all transaction summaries)
    print("\nGlobal Ledger:")
    global_ledger = update_global_ledger(stream_name)
    print(json.dumps(global_ledger, indent=4))

    # Bonus Challenge: View transaction history for each address
    print("\nTransaction History per Address:")
    history1 = view_transaction_history(address1, stream_name)
    history2 = view_transaction_history(address2, stream_name)
    history3 = view_transaction_history(address3, stream_name)

    print("Transaction History for Address 1:", json.dumps(history1, indent=4))
    print("Transaction History for Address 2:", json.dumps(history2, indent=4))
    print("Transaction History for Address 3:", json.dumps(history3, indent=4))

