from web3 import Web3
import os
import sqlite3
import json
from env_manager import authorities_addresses_and_names_separated

# This function should be performed through MetaMask, for testing purposes now is set to "MANUFACTURER"
# ("0x7364cc4E7F136a16a7c38DE7205B7A5b18f17258") with private key
# "0x2e78ccaac0156ec23652b710c05e3076de558a12addbeb6949817b93c557e857"
def send_key_request(authority_address, actor_address, process_id):
    ganache_url = "http://127.0.0.1:7545"  # Default Ganache URL
    web3 = Web3(Web3.HTTPProvider(ganache_url))
    nonce = web3.eth.getTransactionCount(actor_address)
    tx = {
        'chainId': 1337,  # Chain ID for Ganache
        'nonce': nonce,
        'to': authority_address,
        'value': 0,
        'gas': 40000,
        'gasPrice': web3.eth.gasPrice,
        'data': web3.toHex(b'generate your part of my key,x,' + process_id.encode())
    }
    
    # "MANUFACTURER" private key ("0x2e78ccaac0156ec23652b710c05e3076de558a12addbeb6949817b93c557e857")
    signed_tx = web3.eth.account.sign_transaction(tx, "0x2e78ccaac0156ec23652b710c05e3076de558a12addbeb6949817b93c557e857")
    
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(f'tx_hash: {web3.toHex(tx_hash)}')
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
    print(tx_receipt)
    latest_block = web3.eth.blockNumber + 1
    print(latest_block)
    return latest_block

def client_main(process_id, message_id, actor_address):
    # Connect to Ganache
    ganache_url = "http://127.0.0.1:7545"
    web3 = Web3(Web3.HTTPProvider(ganache_url))

    # Connection to SQLite3 reader database
    conn = sqlite3.connect('../databases/reader/reader.db')
    x = conn.cursor()
    
    authorities_addresses, authorities_names = authorities_addresses_and_names_separated()
    
    latest_block = 0
    list_auth = []
    send_index = 0
    for authority_address in authorities_addresses:
        x.execute("SELECT * FROM authorities_generated_decription_keys WHERE process_instance=? AND authority_address=? AND reader_address=?",
                  (str(process_id), authority_address, actor_address))
        result = x.fetchall()
        if not result:
            latest_block_value = send_key_request(authority_address, actor_address, process_id)
            if send_index == 0:
                latest_block = latest_block_value
            send_index +=1
            print(f"Key request sent to authority {authorities_names[authorities_addresses.index(authority_address)]}!")
            list_auth.append(authority_address)
        else:
            print(f"Key already present for authority {authorities_names[authorities_addresses.index(authority_address)]}!")
    if list_auth:
        list_auth_str = json.dumps(list_auth)
        os.system(f"python3 ../src/client2.py -r {actor_address} -a '{list_auth_str}' -l {latest_block}")
