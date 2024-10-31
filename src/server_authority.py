import time
import argparse
from decouple import config
import authority_key_generation
import rsa
import block_int
from web3 import Web3
import ipfshttpclient
import io
import json
import base64
from web3.exceptions import BlockNotFound

# Generates a key for the specified process instance and Reader address
def generate_key(process_instance_id, reader_address):
    key = authority_key_generation.generate_user_key(authority_number, reader_address, process_instance_id, reader_address)
    cipher_generated_key(reader_address, process_instance_id, key)

# Encrypts the generated key and stores it in IPFS
def cipher_generated_key(reader_address, process_instance_id, generated_ma_key):
    # Retrieves the public key from IPFS
    public_key_ipfs_link = block_int.retrieve_publicKey_readers(reader_address)
    getfile = api.cat(public_key_ipfs_link)
    getfile = getfile.split(b'###')
    # Checks if the retrieved public key belongs to the correct reader
    if getfile[0].split(b': ')[1].decode('utf-8') == reader_address:
        publicKey_usable = rsa.PublicKey.load_pkcs1(getfile[1].rstrip(b'"').replace(b'\\n', b'\n'))
        info = [generated_ma_key[i:i + 117] for i in range(0, len(generated_ma_key), 117)]
        f = io.BytesIO()
        # Encrypts each part of the generated key
        for part in info:
            crypto = rsa.encrypt(part, publicKey_usable)
            f.write(crypto)
        f.seek(0)
        file_to_str = f.read()
        j = base64.b64encode(file_to_str).decode('ascii')
        s = json.dumps(j)
        # Adds the encrypted key to IPFS
        hash_file = api.add_json(s)
        # Sends the IPFS link to the specified Reader
        block_int.send_ipfs_link(reader_address, process_instance_id, hash_file, authority_address, authority_private_key)
        print(f'Authority {authority_number} sent the key segment to {reader_address}')

# Checks if a block exists in the blockchain
def check_block_exists(block_number):
    try:
        block = web3.eth.getBlock(block_number, full_transactions=False)
        if block is None:
            return False
        return True
    except BlockNotFound:
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

# Monitors blockchain transactions for key request events
def transactions_monitoring():
    # Loads the smart contract ABI and address
    compiled_contract_path = '../blockchain/build/contracts/MARTSIAEth.json'
    deployed_contract_address = config('CONTRACT_ADDRESS_MARTSIA')
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    # Get the latest block number
    latest_block = web3.eth.blockNumber + 1
    event_filter = contract.events.AuthoritiesNotified.createFilter(
        fromBlock=latest_block
    )
    first = False
    while True:
        # Checks if the latest block exists
        if not check_block_exists(latest_block):
            if not first:
                print(f"Waiting for new blocks: Retrying every 1 second... Authority {authority_number}")
                first = True
            # Wait for 1 second before retrying
            time.sleep(1) 
        else:
            # Get new events emitted by the contract
            events = event_filter.get_new_entries()
            for event in events:
                authorities_list = event['args']['authorities']
                # Checks if the Authority's address is in the list
                if authority_address in authorities_list:
                    process_id = event['args']['process_id']
                    sender = event['args']['user']
                    generate_key(process_id, sender)
            # Update the block range for the next iteration
            latest_block = latest_block + 1
            event_filter = contract.events.AuthoritiesNotified.createFilter(
                fromBlock=latest_block
            )
            first = False

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run authority script for specified authority number.')
    parser.add_argument('-a', '--authority', type=int, required=True, help='Authority number')
    args = parser.parse_args()
    # Connect to IPFS
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    # Get Authority configuration
    authority_number = args.authority
    authority_address = config(f'AUTHORITY{authority_number}_ADDRESS')
    authority_private_key = config(f'AUTHORITY{authority_number}_PRIVATEKEY')
    # Configure web3 provider for Ganache
    ganache_url = "http://127.0.0.1:7545"
    web3 = Web3(Web3.HTTPProvider(ganache_url))
    # Start monitoring transactions
    transactions_monitoring()

