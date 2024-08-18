
from charm.toolbox.pairinggroup import *
from charm.core.engine.util import objectToBytes, bytesToObject
import cryptocode
import block_int
import ipfshttpclient
import json
from maabe_class import *
from datetime import datetime
import random
import sqlite3
from env_manager import authorities_names_and_addresses
import time

def retrieve_data(authority_address, process_instance_id):
    while True:
        try:
            authorities = block_int.retrieve_authority_names(authority_address, process_instance_id)
            public_parameters = block_int.retrieve_parameters_link(authority_address, process_instance_id)
            public_key = block_int.retrieve_publicKey_link(authority_address, process_instance_id)
            return authorities, public_parameters, public_key
        except Exception as e:
            time.sleep(0.5)
    
# Generate the public parameters of the authorities to perform the encryption
def generate_pp_pk(process_instance_id):
    while True:
        try:
            api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
            check_authorities = []
            check_parameters = []
            conn = sqlite3.connect('../databases/data_owner/data_owner.db')
            x = conn.cursor()
            for authority_name, authority_address in authorities_names_and_addresses():
                data = retrieve_data(authority_address, process_instance_id)
                check_authorities.append(data[0])
                check_parameters.append(data[1])
                pk1 = api.cat(data[2])
                pk1 = pk1.decode('utf-8').rstrip('"').lstrip('"')
                pk1 = pk1.encode('utf-8')
                x.execute("INSERT OR IGNORE INTO authorities_public_keys VALUES (?,?,?,?)",
                          (str(process_instance_id), f"Auth-{authority_name[4:]}", data[2], pk1))
                conn.commit()
            if len(set(check_authorities)) == 1 and len(set(check_parameters)) == 1:
                getfile = api.cat(check_parameters[0])
                getfile = getfile.decode('utf-8').rstrip('"').lstrip('"')
                getfile = getfile.encode('utf-8')
                x.execute("INSERT OR IGNORE INTO public_parameters VALUES (?,?,?)",
                          (str(process_instance_id), check_parameters[0], getfile))
                conn.commit()
            break
        except Exception as e:
                time.sleep(0.5)

# Check if the data_owner has the public parameters of the authorities to perform the encryption
def retrieve_public_parameters(process_instance_id):
    conn = sqlite3.connect('../databases/data_owner/data_owner.db')
    x = conn.cursor()
    x.execute("SELECT * FROM public_parameters WHERE process_instance=?", (str(process_instance_id),))
    result = x.fetchall()
    try:
        public_parameters = result[0][2]
    except IndexError:
        generate_pp_pk(process_instance_id)
        x.execute("SELECT * FROM public_parameters WHERE process_instance=?", (str(process_instance_id),))
        result = x.fetchall()
        public_parameters = result[0][2]
    return public_parameters

# Encrypt a message
def encrypt_data(sender_address, file_to_encrypt, input_policies, process_instance_id):
    conn = sqlite3.connect('../databases/data_owner/data_owner.db')
    x = conn.cursor()
    groupObj = PairingGroup('SS512')
    maabe = MaabeRW15(groupObj)
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    response = retrieve_public_parameters(process_instance_id)
    public_parameters = bytesToObject(response, groupObj)
    H = lambda x: self.group.hash(x, G2)
    F = lambda x: self.group.hash(x, G2)
    public_parameters["H"] = H
    public_parameters["F"] = F
    pk = {}
    for authority_name, authority_address in authorities_names_and_addresses():
        x.execute("SELECT * FROM authorities_public_keys WHERE process_instance=? AND authority_name=?",
                  (str(process_instance_id), f"Auth-{authority_name[4:]}"))
        result = x.fetchall()
        pk1 = result[0][3]
        pk1 = bytesToObject(pk1, groupObj)
        pk[authority_name] = pk1
    file_contents = {}
    access_policy = {}
    file_name, policy = next(iter(input_policies.items()))
    file_contents[file_name] = file_to_encrypt
    temporal = ""
    for authority_name, authority_address in authorities_names_and_addresses():
        temporal = temporal + str(process_instance_id) + '@' + authority_name + ' and '
    access_policy[file_name] = ('(' + temporal[:-5] + ') and ' + policy)
    header = []
    key_group = groupObj.random(GT)
    key_encrypt = groupObj.serialize(key_group)
    key_encrypt_deser = groupObj.deserialize(key_encrypt)
    print(access_policy[file_name])
    ciphered_key = maabe.encrypt(public_parameters, pk, key_encrypt_deser, access_policy[file_name])
    ciphered_key_bytes = objectToBytes(ciphered_key, groupObj)
    ciphered_key_bytes_string = ciphered_key_bytes.decode('utf-8')
    cipher = cryptocode.encrypt(file_contents[file_name], str(key_encrypt))
    dict_pol = {'CipheredKey': ciphered_key_bytes_string, "FileName": file_name, "EncryptedFile": cipher}
    header.append(dict_pol)
    now = datetime.now()
    now = int(now.strftime("%Y%m%d%H%M%S%f"))
    random.seed(now)
    message_id = random.randint(1, 2 ** 64)
    metadata = {'sender': sender_address, 'process_instance_id': int(process_instance_id),
                'message_id': message_id}
    print(f'message id: {message_id}')       
    json_total = {'metadata': metadata, 'header': header}
    hash_file = api.add_json(json_total)
    print(f'ipfs hash: {hash_file}')
    x.execute("INSERT OR IGNORE INTO messages VALUES (?,?,?,?)",
              (str(process_instance_id), str(message_id), hash_file, str(json_total)))
    conn.commit()
    
    # "block_int.send_MessageIPFSLink" for testing purposes is set to INTERNATIONAL SUPPLIER! The function
    # should be edited to interact with MetaMask!
    transaction_data = block_int.send_MessageIPFSLink(message_id, hash_file)
    
    return message_id, transaction_data
