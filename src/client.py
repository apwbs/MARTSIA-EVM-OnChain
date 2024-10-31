import argparse
from decouple import config
from web3 import Web3
import os
import sqlite3
import json
from authorities_info import authorities_addresses_and_names_separated
import block_int
import sys
import io

if __name__ == "__main__":
    # Set up UTF-8 encoding for stdout
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Send key request to specified Authority.')
    parser.add_argument('-r', '--requester', type=str, required=True, help='The user performing the action (e.g., electronics, mechanics)')
    args = parser.parse_args()
    
    # Get the requester's address and private key from environment variables
    address_requesting = config(f'{args.requester}_ADDRESS')
    private_key_requesting = config(f'{args.requester}_PRIVATEKEY')
    
    # Get process instance ID from environment variables
    process_instance_id = config('PROCESS_INSTANCE_ID')
    
    # Connection to SQLite3 data_owner database
    conn = sqlite3.connect('../databases/reader/reader.db')
    x = conn.cursor()
    
    # Get the list of Authority addresses and names
    authorities_addresses, authorities_names = authorities_addresses_and_names_separated()
    
    list_auth = []
    
    # Check each Authority to see if a key has already been generated
    for authority_address in authorities_addresses:
        # Query database for existing keys for the current Authority
        x.execute("SELECT * FROM authorities_generated_decription_keys WHERE process_instance=? AND authority_address=? AND reader_address=?",
                  (str(process_instance_id), authority_address, address_requesting))
        result = x.fetchall()
        
        # If no key exists, add the Authority to the request list
        if not result:
            list_auth.append(authority_address)
        else:
            # Inform that the key is already present for the Authority
            print(f"✅ Key already present for {authorities_names[authorities_addresses.index(authority_address)]}!", flush=True)
    
    # If there are Authorities to request keys from
    if list_auth:
        # Send key request to the Authorities and get the earliest block
        earliest_block = block_int.send_key_request(address_requesting, int(process_instance_id), list_auth, private_key_requesting)
        print(f"✅ Key request sent to the Authorities!", flush=True)
        
        # Convert the list of Authorities to a JSON string
        list_auth_str = json.dumps(list_auth)
        
        # Execute client2.py to process the key retrieve
        os.system(f"python3 ../src/client2.py -r {address_requesting} -a '{list_auth_str}' -e {earliest_block}")

