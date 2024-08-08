import argparse
from decouple import config
from web3 import Web3
import time
import os
import sqlite3
import json

# Connect to Ganache
ganache_url = "http://127.0.0.1:7545"  # Default Ganache URL
web3 = Web3(Web3.HTTPProvider(ganache_url))

if web3.isConnected():
    print("Connected to Ganache")

# Connection to SQLite3 data_owner database
conn = sqlite3.connect('../databases/reader/reader.db')
x = conn.cursor()

# Function to dynamically retrieve authorities addresses and names
def retrieve_authorities():
    authorities_list = []
    authorities_names = []
    count = 1
    # Loop to retrieve all authority addresses and names until no more are found
    while True:
        address_key = f'AUTHORITY{count}_ADDRESS'
        name_key = f'AUTHORITY{count}_NAME'
        
        # Check if the config key exists, if not, break the loop
        if not config(address_key, default=None) or not config(name_key, default=None):
            break
        # Append address and name to respective lists
        authorities_list.append(config(address_key))
        authorities_names.append(config(name_key))
        count += 1
    return authorities_list, authorities_names
    
authorities_list, authorities_names = retrieve_authorities()

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Send key request to specified authority.')
parser.add_argument('-r', '--requester', type=str, required=True, help='The user performing the action (e.g., electronics, mechanics)')
args = parser.parse_args()

# Get process instance ID from config
process_instance_id = config('PROCESS_INSTANCE_ID')

address_requesting = config(f'{args.requester}_ADDRESS')
private_key_requesting = config(f'{args.requester}_PRIVATEKEY')

def send_key_request(authority_address, first_auth):
    start = time.time()
    nonce = web3.eth.getTransactionCount(address_requesting)
    tx = {
        'chainId': 1337,  # Chain ID for Ganache
        'nonce': nonce,
        'to': authority_address,
        'value': 0,
        'gas': 40000,
        'gasPrice': web3.eth.gasPrice,
        'data': web3.toHex(b'generate your part of my key,x,' + process_instance_id.encode())
    }

    signed_tx = web3.eth.account.sign_transaction(tx, private_key_requesting)

    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(f'tx_hash: {web3.toHex(tx_hash)}')
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
    print(tx_receipt)
    end = time.time()
    #print('The time for sending a key request (blockchain execution) is :', (end - start) * 10 ** 3, 'ms')
    if first_auth == 0:
        latest_block = web3.eth.blockNumber + 1
        with open('../src/client2.py', 'r') as file:
            lines = file.readlines()
        for i, line in enumerate(lines):
            if "min_round =" in line:
                lines[i] = f"    min_round = {latest_block}  # Starting block number for Ganache\n"
                break
        with open('../src/client2.py', 'w') as file:
            file.writelines(lines)

if __name__ == "__main__":
    first_auth = 0
    list_auth = []
    for e in authorities_list:
        x.execute("SELECT * FROM authorities_generated_decription_keys WHERE process_instance=? AND authority_address=? AND reader_address=?",
                  (str(process_instance_id), e, address_requesting))
        result = x.fetchall()
        if not result: 
            send_key_request(e, first_auth)
            first_auth = 1
            print(f"Key request sent to authority {authorities_names[authorities_list.index(e)]}!")
            list_auth.append(e)
        else:
            print(f"Key already present for authority {authorities_names[authorities_list.index(e)]}!")
    if list_auth:
        list_auth_str = json.dumps(list_auth)
        os.system(f"python3 ../src/client2.py -r {args.requester} -a '{list_auth_str}'")
    
    
    

