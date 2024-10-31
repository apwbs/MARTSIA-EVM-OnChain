import argparse
import time
import rsa
from web3 import Web3
import ipfshttpclient
import sqlite3
import base64
import json
from web3.exceptions import BlockNotFound
from authorities_info import authorities_addresses_and_names_separated
import sys
import io

# Function to retrieve the private key from a transaction
def retrieve_key(transaction):
    # Extract IPFS link and process instance ID from transaction input
    partial = bytes.fromhex(transaction['input'][2:]).decode('utf-8').split(',')
    process_instance_id = partial[1]
    ipfs_link = partial[0]
    
    # Connect to IPFS to retrieve the file
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    getfile = api.cat(ipfs_link)
    getfile = getfile.decode('utf-8').replace(r'\"', r'')
    j2 = json.loads(getfile)
    
    # Decode the base64 data from the IPFS file
    data2 = base64.b64decode(j2)
    x.execute("SELECT * FROM rsa_private_key WHERE reader_address=?", (reader_address,))
    result = x.fetchall()
    
    # Load the RSA private key
    pk = result[0][1]
    privateKey_usable = rsa.PrivateKey.load_pkcs1(pk)
    
    # Split the data into chunks for decryption
    info2 = [data2[i:i + 128] for i in range(0, len(data2), 128)]
    final_bytes = b''
    
    # Decrypt each chunk and concatenate the results
    for j in info2:
        message = rsa.decrypt(j, privateKey_usable)
        final_bytes = final_bytes + message
    
    # Store the decrypted key in the database
    x.execute("INSERT OR REPLACE INTO authorities_generated_decription_keys VALUES (?,?,?,?,?)",
              (str(process_instance_id), transaction['from'], ipfs_link, final_bytes, transaction['to']))
    conn.commit()

# Function to monitor blockchain transactions for key retrieval
def transactions_monitoring(earliest_block):
    min_round = int(earliest_block)
    first = False
    finished = []
    
    while True:
        try:
            # Fetch the block from the blockchain
            block = web3.eth.getBlock(min_round, True)
            print("Analyzing block:", block.number)
            
            # Check each transaction in the block
            for transaction in block.transactions:
                # Verify if the transaction is for the reader and from an Authority
                if transaction['to'] == reader_address and 'input' in transaction and transaction['from'] in list_auth and transaction['from'] not in finished:
                    print(f"✅ Key retrieved from {authorities_names[authorities_addresses.index(transaction['from'])]}!", flush=True)
                    retrieve_key(transaction)  # Retrieve the key
                    finished.append(transaction['from'])
            
            # Exit if keys from all Authorities have been retrieved
            if sorted(finished) == sorted(list_auth):
                break
            
            time.sleep(0.5)  # Pause before the next iteration
            min_round += 1
            first = False
        
        # Handle cases where the block cannot be found
        except BlockNotFound as e:
            if first == False:
                print(f"Waiting for new blocks: Retrying every 1 second...")
                first = True
            # Wait before retrying to fetch the block
            time.sleep(1)  

if __name__ == "__main__":
    # Set up UTF-8 encoding for stdout
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # Parse command-line arguments for the reader, authorities, and earliest block
    parser = argparse.ArgumentParser(description='Retrieve key for the given reader.')
    parser.add_argument('-r', '--reader', type=str, required=True, help='The reader performing the action (e.g., electronics, mechanics)')
    parser.add_argument('-a', '--authority', type=str, required=True, help='The Authorities for which we are waiting the key')
    parser.add_argument('-e', '--earliest_block', type=str, required=True, help='The earliest block to start monitoring from')
    args = parser.parse_args()
    
    reader_address = args.reader
    earliest_block = args.earliest_block
    list_auth = json.loads(args.authority)  # Load Authority list from arguments
    authorities_addresses, authorities_names = authorities_addresses_and_names_separated()
    
    # Connect to Ganache blockchain for transaction monitoring
    ganache_url = "http://127.0.0.1:7545"  # Default Ganache URL
    web3 = Web3(Web3.HTTPProvider(ganache_url))
    
    # Connection to SQLite3 database for reader data
    conn = sqlite3.connect('../databases/reader/reader.db')
    x = conn.cursor()
    
    # Start monitoring transactions for key retrieval
    transactions_monitoring(earliest_block)

