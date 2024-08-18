from flask import Flask, request, jsonify
from decouple import config
from hashlib import sha512
from flask_cors import CORS, cross_origin

from env_manager import authorities_count
import reader_public_key
import attribute_certifier
import data_owner
import client
import reader

import os
import subprocess
import signal
import atexit

import re


# Used to reset the local databases
os.system(f"sh ../sh_files/reset_db.sh")

app = Flask(__name__)
CORS(app)

#Retrieve the number of authorities from the ".env" file
numberOfAuthorities  = authorities_count()

# Store the subprocesses globally to access them in the signal handler
processes = []


# To close automatically subprocesses (attribute_certification())
def handle_exit():
    for process in processes:
        # Send SIGTERM to the process group
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        

# Ensure subprocesses are killed on exit
atexit.register(handle_exit)


# Check if a string is a valid ERC20 address
def is_valid_erc20_address(address):
    # Check if the address is a string
    if not isinstance(address, str):
        return True
    # Check length (42 characters: 2 for '0x' and 40 for the address)
    if len(address) != 42:
        return True
    # Check if it starts with '0x'
    if not address.startswith('0x'):
        return True
    # Check if the remaining 40 characters are hexadecimal
    if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
        return True
    return False


# Check if the process_id is valid
def is_process_id_valid(process_id):
    # Define the maximum value (2^64)
    max_value = 2**64
    # Check if the number is in the range 1 to 2^64
    if 1 <= int(process_id) <= max_value:
        return False
    else:
        return True

# Check if the message_id is valid
def is_message_id_valid(message_id):
    # Define the maximum value (2^64)
    max_value = 2**64
    # Check if the number is in the range 1 to 2^64
    if 1 <= int(message_id) <= max_value:
        return False
    else:
        return True


@app.route('/certification/generate_rsa_key_pair/', methods=['POST'], strict_slashes=False)
def generate_rsa_key_pair():
    """ Generate the public and private RSA keys for an actor

    This function is used to generate the public and private keys RSA for an actor
    that is involved in a process
    
    Args:
        actor: actor address involved in the process

    Returns:
        The status of the request, 200 if the keys are generated correctly
    
    Example:
        An execution test is saved in /src/test/test1.py
        
    """
    actor = request.json.get('actor')
    
    if is_valid_erc20_address(actor):
        return f"Missing or wrong parameter 'actor'!", 400
        
    transaction_data = reader_public_key.generate_keys(actor)
    return f"Public and private RSA keys generated for actor {actor}!\n {transaction_data}",  200
    

@app.route('/certification/attributes_certification_and_authorities/', methods=['POST'], strict_slashes=False)
def attributes_certification_and_authorities():
    """ Certificate the actors and start the authorities

    This function is used to certificate the actors
    that are involved in a given process id and to initialize and
    put on hold the authorities to answer for decryption keys
    
    Args:
        process_id: an integer from 1 to 2**64 to identify the process
        roles: a dictionary that contains for each actor address the list of roles associated
        
    Returns:
        200 if the certification is completed and the authorities are ready
        
    Example:
        An execution test is saved in /src/test/test2.py
        
    """
    process_id = request.json.get('process_id')
    roles = request.json.get('roles')
    
    if is_process_id_valid(process_id):
        return f"Wrong parameter 'process_id'!", 400
    if roles == None or roles == "":
        return f"Wrong parameter 'roles'!", 400

    attribute_certifier.generate_attributes(roles, process_id)
    # Initialization of the authorities through a subprocess in the same console of the API
    commands = []
    for i in range(1, numberOfAuthorities + 1):
        commands.append(f"python3 authority.py -p {process_id} -a {i}")
    command_string = " & ".join(commands)
    process = subprocess.Popen(
        ["bash", "-c", command_string],
        # Create a new process group
        preexec_fn=os.setsid  
    )
    # Wait until the authorities' initialization is complete (subprocess finishes)
    process.wait()
    # Start another subprocess to put on hold the authorities to answer for decryption keys
    commands = []
    for i in range(1, numberOfAuthorities + 1):
        commands.append(f"python3 server_authority.py -a {i}")
    # Join the commands with ' & ' to run them in parallel
    command_string = " & ".join(commands)
    process = subprocess.Popen(
        ["bash", "-c", command_string],
        #Creates a new process group
        preexec_fn=os.setsid
    )
    processes.append(process)
    return "Actors' attributes certified and Authorities ready!", 200


@app.route('/encrypt/', methods=['POST'], strict_slashes=False)
def encrypt():
    """ This function is used to encrypt a message, setting the policy
    of the decryption

    Args:
        actor: the actor address who is performing the encryption
        message: the message to encrypt (base64 format)
        policy: dictionary name of the message with its policy
        process_id: integer from 1 to 2**64 to identify the process
        
    Returns:
        The status of the request, 200 if the encryption is completed
        
    Example:
        An execution test is saved in /src/test/test3.py
        
    """
    actor = request.json.get('actor')
    message = request.json.get('message')
    policy = request.json.get('policy')
    process_id = request.json.get('process_id')
    
    if is_valid_erc20_address(actor):
        return f"Wrong parameter 'actor'!", 400
    if message == None or message == "":
        return f"Wrong parameter 'message'!", 400
    if policy == None or policy == "":
        return f"Wrong parameter 'policy'!", 400
    if is_process_id_valid(process_id):
        return f"Wrong parameter 'process_id'!", 400

    # Encrypt the message
    message_id, transaction_data = data_owner.encrypt_data(actor, message, policy, process_id)
    data = transaction_data
    data['message_id'] = message_id
    return jsonify(data), 200
    

@app.route('/decrypt/', methods=['POST'], strict_slashes=False)
def decrypt():
    """ This function is used by an actor to decrypt a message
    
    Args:
        actor: the actor address who is performing the decryption
        message_id: the id of the message that the actor wants to decrypt
        process_id: integer from 1 to 2**64 to identify the process
    
    Returns:
        The status of the request, 200 if the decryption is completed.
        The output is in base64 format
    
    Example:
        An execution test is saved in /src/test/test4.py
        
    """
    actor = request.json.get('actor')
    message_id = request.json.get('message_id')
    process_id = request.json.get('process_id')
    
    if is_valid_erc20_address(actor):
        return f"Wrong parameter 'actor'!", 400
    if is_message_id_valid(message_id):
        return f"Wrong parameter 'message_id'!", 400
    if is_process_id_valid(process_id):
        return f"Wrong parameter 'process_id'!", 400
    
    client.client_main(process_id, message_id, actor)
    base64_output = reader.start(process_id, message_id, None, actor)
    return f"Message correctly retrieved:\n {base64_output}", 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="8888")
