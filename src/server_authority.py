import time
import argparse
from decouple import config
import authority_key_generation  # Assuming this module can be dynamically adapted for multiple authorities
import rsa
import block_int
from web3 import Web3
import ipfshttpclient
import io
import json
import base64
from web3.exceptions import BlockNotFound

# Connect to IPFS
api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Run authority script for specified authority number.')
parser.add_argument('-a', '--authority', type=int, required=True, help='Authority number')
args = parser.parse_args()

# Get authority configuration
authority_number = args.authority
authority_address = config(f'AUTHORITY{authority_number}_ADDRESS')
authority_private_key = config(f'AUTHORITY{authority_number}_PRIVATEKEY')

# Configure web3 provider for Ganache
ganache_url = "http://127.0.0.1:7545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

if web3.isConnected():
    print(f"Connected to Ganache for Authority {authority_number}")

def send_ipfs_link(reader_address, process_instance_id, hash_file):
    start = time.time()
    nonce = web3.eth.getTransactionCount(authority_address)

    tx = {
        'chainId': 1337,  # Chain ID for Ganache
        'nonce': nonce,
        'to': reader_address,
        'value': 0,
        'gas': 40000,
        'gasPrice': web3.eth.gasPrice,
        'data': web3.toHex(hash_file.encode() + b',' + str(process_instance_id).encode())
    }

    signed_tx = web3.eth.account.sign_transaction(tx, authority_private_key)

    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(f'tx_hash: {web3.toHex(tx_hash)}')
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
    print(tx_receipt)
    end = time.time()
    #print('The time for blockchain execution is :', (end - start) * 10 ** 3, 'ms')

def generate_key(x):
    #gid = bytes.fromhex(x['input'][2:]).decode('utf-8').split(',')[1]
    gid = x['from']
    process_instance_id = int(bytes.fromhex(x['input'][2:]).decode('utf-8').split(',')[2])
    reader_address = x['from']
    key = authority_key_generation.generate_user_key(authority_number, gid, process_instance_id, reader_address)
    cipher_generated_key(reader_address, process_instance_id, key)

def cipher_generated_key(reader_address, process_instance_id, generated_ma_key):
    public_key_ipfs_link = block_int.retrieve_publicKey_readers(reader_address)
    retrieve_pub_ke_time = time.time()
    getfile = api.cat(public_key_ipfs_link)
    getfile = getfile.split(b'###')
    if getfile[0].split(b': ')[1].decode('utf-8') == reader_address:
        publicKey_usable = rsa.PublicKey.load_pkcs1(getfile[1].rstrip(b'"').replace(b'\\n', b'\n'))

        info = [generated_ma_key[i:i + 117] for i in range(0, len(generated_ma_key), 117)]
        #print(info)
        f = io.BytesIO()
        for part in info:
            crypto = rsa.encrypt(part, publicKey_usable)
            f.write(crypto)
        f.seek(0)

        file_to_str = f.read()
        j = base64.b64encode(file_to_str).decode('ascii')
        s = json.dumps(j)
        hash_file = api.add_json(s)
        print(f'ipfs hash: {hash_file}')

        send_ipfs_link(reader_address, process_instance_id, hash_file)

def transactions_monitoring():
    latest_block = web3.eth.blockNumber + 1
    min_round = latest_block  # Starting block number for Ganache
    note = 'generate your part of my key'
    first = False
    while True:
        try:
            start = time.time()
            block = web3.eth.getBlock(min_round, True)
            get_block_time = time.time()
            #print('The time for retrieving a block is :', (get_block_time - start) * 10 ** 3, 'ms')
            print("Analyzing block:", block.number)
            for transaction in block.transactions:
                if 'to' in transaction:
                    if transaction['to'] == authority_address and 'input' in transaction:
                        if bytes.fromhex(transaction['input'][2:]).decode('utf-8').split(',')[0] == note:
                            generate_key(transaction)
            time.sleep(0.5)
            min_round = min_round + 1
            end = time.time()
            first = False
            #print('Time for an entire run is: ', (end - start) * 10 ** 3, 'ms')
            #time.sleep(1)
        except BlockNotFound as e:
            if first == False:
                print(f"Waiting for new blocks: Retrying every 1 second...")
                first = True
            time.sleep(1)  # Wait for 1 second before retrying

if __name__ == "__main__":
    transactions_monitoring()

