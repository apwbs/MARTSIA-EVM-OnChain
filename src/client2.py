import argparse
import time
import rsa
from web3 import Web3
import ipfshttpclient
import sqlite3
import base64
import json
from web3.exceptions import BlockNotFound
from env_manager import authorities_addresses_and_names_separated


def retrieve_key(transaction):
    # Connection to SQLite3 data_owner database
    conn = sqlite3.connect('../databases/reader/reader.db')
    x = conn.cursor()
    # Connect to IPFS
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
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

def transactions_monitoring(latest_block):
    # Connect to Ganache
    ganache_url = "http://127.0.0.1:7545"  # Default Ganache URL
    web3 = Web3(Web3.HTTPProvider(ganache_url))
    # The value of "min_round" is edited automatically by "client.py" with the block of the first message sent to the authorities 
    min_round = int(latest_block)  # Starting block number for Ganache
    first = False
    finished = []
    while True:
        try:
            block = web3.eth.getBlock(min_round, True)
            for transaction in block.transactions:
                if transaction['to'] == reader_address and 'input' in transaction and transaction['from'] in list_auth and transaction['from'] not in finished:
                    print(f"Key retrieved from {authorities_names[authorities_addresses.index(transaction['from'])]}!")
                    retrieve_key(transaction)
                    finished.append(transaction['from'])
            if sorted(finished) == sorted(list_auth):
                break
            min_round += 1
            first = False
        except BlockNotFound as e:
            if first == False:
                    print(f"Waiting for new blocks: Retrying every 1 second...")
                    first = True
            # Wait for 1 second before retrying
            time.sleep(1)  

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Retrieve key for the given reader.')
    parser.add_argument('-r', '--reader', type=str, required=True, help='The reader performing the action (e.g., electronics, mechanics)')
    parser.add_argument('-a', '--authority', type=str, required=True, help='The authorities for which we are waiting the key')
    parser.add_argument('-l', '--latest_block', type=str, required=True, help='The authorities for which we are waiting the key')
    args = parser.parse_args()
    reader_address = args.reader
    latest_block = args.latest_block
    list_auth = json.loads(args.authority)
    authorities_addresses, authorities_names = authorities_addresses_and_names_separated()
    transactions_monitoring(latest_block)
