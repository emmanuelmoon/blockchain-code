import hashlib
import os
import requests
import json
import uuid

RPC_USER = 'multichainrpc'
RPC_PASSWORD = '7dWxr6kW94nRAfzAhNTw2XRRTsdnnEEu4UQ9zJKK8wsS'
RPC_HOST = '127.0.0.1'
RPC_PORT = '7206'
BASE_URL = f'http://{RPC_HOST}:{RPC_PORT}'
HEADERS = {'content-type': 'application/json'}

ASSET_NAME = 'ANONBOND'
ISSUE_QTY = 10
UNIT_QTY = 1

def rpc_call(method, params=[]):
    payload = {'method': method, 'params': params, 'id': 1}
    resp = requests.post(BASE_URL, headers=HEADERS, data=json.dumps(payload), auth=(RPC_USER, RPC_PASSWORD))
    result = resp.json()
    if result.get('error'):
        raise Exception(result['error'])
    return result['result']

def asset_exists(name):
    assets = rpc_call('listassets')
    return any(asset['name'] == name for asset in assets)

def setup_streams():
    try:
        rpc_call('create', ['stream', 'commitments', True])
        rpc_call('create', ['stream', 'nullifiers', True])
    except:
        pass
    rpc_call('subscribe', ['commitments'])
    rpc_call('subscribe', ['nullifiers'])

def issue_asset(address, asset, qty, units):
    return rpc_call('issue', [address, asset, qty, units])

def hash_commitment(serial, randomness):
    return hashlib.sha256(f'{serial}{randomness}'.encode()).hexdigest()

def burn_and_mint(address, serial, randomness):
    commitment = hash_commitment(serial, randomness)
    data_hex = json.dumps({'address': address}).encode().hex()
    rpc_call('publish', ['commitments', commitment, data_hex])
    return commitment

def redeem(address, serial, randomness):
    serial_hash = hashlib.sha256(serial.encode()).hexdigest()
    commitment = hash_commitment(serial, randomness)
    if rpc_call('liststreamkeyitems', ['nullifiers', serial_hash]):
        raise Exception('Serial already used')
    if not rpc_call('liststreamkeyitems', ['commitments', commitment]):
        raise Exception('Commitment not found')
    data_hex = json.dumps({'redeemed_by': address}).encode().hex()
    rpc_call('publish', ['nullifiers', serial_hash, data_hex])
    return True

def main():
    setup_streams()

    # Generate 3 addresses
    addresses = [rpc_call('getnewaddress') for _ in range(3)]
    print('Addresses:', addresses)

    # Grant receive permission to Address #1
    print(f"Granting 'receive' permission to Address #1: {addresses[0]}")
    rpc_call('grant', [addresses[0], 'receive'])

    # Issue asset only if it doesn't already exist
    if not asset_exists(ASSET_NAME):
        print(f"Issuing {ISSUE_QTY} units of {ASSET_NAME} to Address #1: {addresses[0]}")
        txid = issue_asset(addresses[0], ASSET_NAME, ISSUE_QTY, UNIT_QTY)
        print('Issue transaction ID:', txid, "\n")
    else:
        print(f"Asset {ASSET_NAME} already exists. Skipping issue.\n")

    # Shared serial/randomness
    serial = uuid.uuid4().hex
    randomness = os.urandom(16).hex()
    print(f"Serial: {serial}\nRandomness: {randomness}\n")

    # Burn by Address #1
    print(f"--- Burn by Address #1: {addresses[0]} ---")
    commitment = burn_and_mint(addresses[0], serial, randomness)
    print(f"Commitment: {commitment}\n")

    # Redeem by Address #2
    print(f"--- Redeem by Address #2: {addresses[1]} ---")
    try:
        redeem(addresses[1], serial, randomness)
        print("Redeem successful by Address #2\n")
    except Exception as e:
        print("Redeem failed by Address #2:", e, "\n")

    # Redeem by Address #3 (should fail)
    print(f"--- Redeem by Address #3: {addresses[2]} ---")
    try:
        redeem(addresses[2], serial, randomness)
        print("Redeem successful by Address #3")
    except Exception as e:
        print("Redeem failed by Address #3:", e)

if __name__ == '__main__':
    main()
