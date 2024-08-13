import argparse
import time
from decouple import config
import rsa
from web3 import Web3
import ipfshttpclient
import sqlite3
import base64
import json
from web3.exceptions import BlockNotFound

# Connect to IPFS
api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

# Connect to Ganache
ganache_url = "http://127.0.0.1:7545"  # Default Ganache URL
web3 = Web3(Web3.HTTPProvider(ganache_url))

if web3.isConnected():
    print("Connected to Ganache")

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Retrieve key for the given reader.')
parser.add_argument('-r', '--reader', type=str, required=True, help='The reader performing the action (e.g., electronics, mechanics)')
parser.add_argument('-a', '--authority', type=str, required=True, help='The authorities for which we are waiting the key')
args = parser.parse_args()

reader_address = config(f'{args.reader}_ADDRESS')

list_auth = json.loads(args.authority)

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

# Connection to SQLite3 data_owner database
conn = sqlite3.connect('../databases/reader/reader.db')
x = conn.cursor()

def retrieve_key(transaction):
    partial = bytes.fromhex(transaction['input'][2:]).decode('utf-8').split(',')
    process_instance_id = partial[1]
    ipfs_link = partial[0]
    getfile = api.cat(ipfs_link)
    getfile = getfile.decode('utf-8').replace(r'\"', r'')
    j2 = json.loads(getfile)
    data2 = base64.b64decode(j2)

    x.execute("SELECT * FROM rsa_private_key WHERE reader_address=?", (reader_address,))
    result = x.fetchall()
    pk = result[0][1]
    privateKey_usable = rsa.PrivateKey.load_pkcs1(pk)

    info2 = [data2[i:i + 128] for i in range(0, len(data2), 128)]
    final_bytes = b''

    for j in info2:
        message = rsa.decrypt(j, privateKey_usable)
        final_bytes = final_bytes + message
    #print(final_bytes)
    x.execute("INSERT OR REPLACE INTO authorities_generated_decription_keys VALUES (?,?,?,?,?)",
              (str(process_instance_id), transaction['from'], ipfs_link, final_bytes, transaction['to']))
    conn.commit()

def transactions_monitoring():
    min_round = 6468  # Starting block number for Ganache
    first = False
    finished = []
    while True:
        try:
            block = web3.eth.getBlock(min_round, True)
            print("Analyzing block:", block.number)
            for transaction in block.transactions:
                if transaction['to'] == reader_address and 'input' in transaction and transaction['from'] in list_auth and transaction['from'] not in finished:
                    print(f"Key retrieved from {authorities_names[authorities_list.index(transaction['from'])]}!")
                    retrieve_key(transaction)
                    finished.append(transaction['from'])
            if sorted(finished) == sorted(list_auth):
                break
            time.sleep(0.5)
            min_round += 1
            first = False
        except BlockNotFound as e:
            if first == False:
                    print(f"Waiting for new blocks: Retrying every 1 second...")
                    first = True
            time.sleep(1)  # Wait for 1 second before retrying

if __name__ == "__main__":
    transactions_monitoring()
    

