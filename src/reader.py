from charm.toolbox.pairinggroup import *
from charm.core.engine.util import bytesToObject
import cryptocode
import block_int
import ipfshttpclient
import json
from maabe_class import *
import sqlite3
from env_manager import authorities_addresses_and_names_separated


def merge_dicts(*dict_args):
    """
    Given any number of dicts, shallow copy and merge into a new dict,
    precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


def retrieve_data(authority_address, process_instance_id):
    authorities = block_int.retrieve_authority_names(authority_address, process_instance_id)
    public_parameters = block_int.retrieve_parameters_link(authority_address, process_instance_id)
    return authorities, public_parameters


def generate_public_parameters(process_instance_id):
    # Connection to SQLite3 reader database
    conn = sqlite3.connect('../databases/reader/reader.db')
    x = conn.cursor()
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    check_authorities = []
    check_parameters = []
    authorities_addresses, authorities_names = authorities_addresses_and_names_separated()
    for authority_address in authorities_addresses:
        data = retrieve_data(authority_address, process_instance_id)
        check_authorities.append(data[0])
        check_parameters.append(data[1])
    if len(set(check_authorities)) == 1 and len(set(check_parameters)) == 1:
        getfile = api.cat(check_parameters[0])
        x.execute("INSERT OR IGNORE INTO public_parameters VALUES (?,?,?)",
                  (str(process_instance_id), check_parameters[0], getfile))
        conn.commit()


def retrieve_public_parameters(process_instance_id):
    # Connection to SQLite3 reader database
    conn = sqlite3.connect('../databases/reader/reader.db')
    x = conn.cursor()
    x.execute("SELECT * FROM public_parameters WHERE process_instance=?", (str(process_instance_id),))
    result = x.fetchall()
    try:
        public_parameters = result[0][2]
    except IndexError:
        generate_public_parameters(process_instance_id)
        x.execute("SELECT * FROM public_parameters WHERE process_instance=?", (str(process_instance_id),))
        result = x.fetchall()
        public_parameters = result[0][2]
    return public_parameters


def actual_decryption(remaining, public_parameters, user_sk):
    groupObj = PairingGroup('SS512')
    maabe = MaabeRW15(groupObj)
    test = remaining['CipheredKey'].encode('utf-8')
    ct = bytesToObject(test, groupObj)
    v2 = maabe.decrypt(public_parameters, user_sk, ct)
    v2 = groupObj.serialize(v2)
    decryptedFile = cryptocode.decrypt(remaining['EncryptedFile'], str(v2))
    return decryptedFile


def start(process_instance_id, message_id, slice_id, sender_address):
    authorities_addresses, authorities_names = authorities_addresses_and_names_separated()
    groupObj = PairingGroup('SS512')
    maabe = MaabeRW15(groupObj)
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    # Connection to SQLite3 reader database
    conn = sqlite3.connect('../databases/reader/reader.db')
    x = conn.cursor()
    merged={}
    response = retrieve_public_parameters(process_instance_id)
    public_parameters = bytesToObject(response, groupObj)
    H = lambda x: self.group.hash(x, G2)
    F = lambda x: self.group.hash(x, G2)
    public_parameters["H"] = H
    public_parameters["F"] = F
    for authority_address in authorities_addresses:
        x.execute("SELECT * FROM authorities_generated_decription_keys WHERE process_instance=? AND authority_address=? AND reader_address=?",
                  (str(process_instance_id), authority_address, sender_address))
        result = x.fetchall()
        user_sk1 = result[0][3]
        user_sk1 = bytesToObject(user_sk1, groupObj)
        merged = merge_dicts(merged, user_sk1)
    user_sk = {'GID': sender_address, 'keys': merged}
    # decrypt
    response = block_int.retrieve_MessageIPFSLink(message_id)
    ciphertext_link = response[0]
    getfile = api.cat(ciphertext_link)
    ciphertext_dict = json.loads(getfile)
    output = ""
    if ciphertext_dict['metadata']['process_instance_id'] == int(process_instance_id) \
            and ciphertext_dict['metadata']['message_id'] == int(message_id):
        slice_check = ciphertext_dict['header']
        if len(slice_check) == 1:
            output = actual_decryption(ciphertext_dict['header'][0], public_parameters, user_sk)
        elif len(slice_check) > 1:
            for remaining in slice_check:
                if remaining['Slice_id'] == slice_id:
                    actual_decryption(remaining, public_parameters, user_sk)
    return output
