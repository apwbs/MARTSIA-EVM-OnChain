from charm.toolbox.pairinggroup import *
from maabe_class import *
from charm.core.engine.util import objectToBytes, bytesToObject
import ipfshttpclient
import block_int
import sqlite3
import json
from authorities_info import authorities_names

def retrieve_public_parameters(authority_number, process_instance_id):
    # Connect to SQLite3 database for the specified Authority
    conn = sqlite3.connect('../databases/authority' + str(authority_number) + '/authority' + str(authority_number) + '.db')
    x = conn.cursor()
    # Fetch public parameters for the specific process instance
    x.execute("SELECT * FROM public_parameters WHERE process_instance=?", (str(process_instance_id),))
    result = x.fetchall()
    public_parameters = result[0][2].encode()
    return public_parameters

def generate_user_key(authority_number, gid, process_instance_id, reader_address):
    # Connect to SQLite3 database for the specified Authority
    conn = sqlite3.connect('../databases/authority' + str(authority_number) + '/authority' + str(authority_number) + '.db')
    x = conn.cursor()
    # Initialize group and MA-ABE scheme
    groupObj = PairingGroup('SS512')
    maabe = MaabeRW15(groupObj)
    # Connect to IPFS API on localhost
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    # Retrieve and deserialize public parameters
    response = retrieve_public_parameters(authority_number, process_instance_id)
    public_parameters = bytesToObject(response, groupObj)
    # Define custom hash functions for the scheme
    H = lambda x: self.group.hash(x, G2)
    F = lambda x: self.group.hash(x, G2)
    public_parameters["H"] = H
    public_parameters["F"] = F
    # Fetch and deserialize private key from database
    x.execute("SELECT * FROM private_keys WHERE process_instance=?", (str(process_instance_id),))
    result = x.fetchall()
    sk1 = result[0][1]
    sk1 = bytesToObject(sk1, groupObj)
    # Retrieve user's attributes from IPFS
    attributes_ipfs_link = block_int.retrieve_users_attributes(process_instance_id)
    getfile = api.cat(attributes_ipfs_link)
    getfile = getfile.replace(b'\\', b'')
    getfile = getfile.decode('utf-8').rstrip('"').lstrip('"')
    getfile = getfile.encode('utf-8')
    getfile = getfile.split(b'####')
    attributes_dict = json.loads(getfile[1].decode('utf-8'))
    # Filter attributes for the specified Authority
    user_attr1 = attributes_dict[reader_address]
    authorities_names_var = authorities_names()
    user_attr1 = [k for k in user_attr1 if k.endswith(authorities_names_var[int(authority_number) - 1])]
    # Generate the user key based on attributes and public/private keys
    user_sk1 = maabe.multiple_attributes_keygen(public_parameters, sk1, gid, user_attr1)
    # Serialize user key for output
    user_sk1_bytes = objectToBytes(user_sk1, groupObj)
    return user_sk1_bytes

