import json
import block_int
from decouple import config
import io
import sqlite3
import ipfshttpclient
from env_manager import authorities_names
        

# The Attribute Certifier saves on the blockchain the IPFS link containing the actors' attributes
def generate_attributes(roles, process_instance_id):
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    authorities_names_value = authorities_names()
    dict_users = {}
    for actor, list_roles in roles.items():
            dict_users[actor] = [str(process_instance_id)+'@'+ name for name in authorities_names_value] + [role for role in list_roles]
    
    f = io.StringIO()
    dict_users_dumped = json.dumps(dict_users)
    print("Roles:", dict_users_dumped)
    
    f.write('"process_instance_id": ' + str(process_instance_id) + '####')
    f.write(dict_users_dumped)
    f.seek(0)
    file_to_str = f.read()
    
    hash_file = api.add_json(file_to_str)
    print(f'ipfs hash: {hash_file}')
    
    # Connection to SQLite3 attribute_certifier database
    conn = sqlite3.connect('../databases/attribute_certifier/attribute_certifier.db')
    x = conn.cursor()
    x.execute("INSERT OR IGNORE INTO user_attributes VALUES (?,?,?)",
              (str(process_instance_id), hash_file, file_to_str))
    conn.commit()
    
    attribute_certifier_address = config('CERTIFIER_ADDRESS')
    private_key = config('CERTIFIER_PRIVATEKEY')
    block_int.send_users_attributes(attribute_certifier_address, private_key, process_instance_id, hash_file)
