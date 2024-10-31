from web3 import Web3
from decouple import config
import json
import base64

# Connect to Ganache
ganache_url = "http://127.0.0.1:7545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Path to compiled contract and deployed address
compiled_contract_path = '../blockchain/build/contracts/MARTSIAEth.json'
deployed_contract_address = config('CONTRACT_ADDRESS_MARTSIA')

# Flag for verbose output
verbose = False

# Get the transaction nonce for an address
def get_nonce(ETH_address):
    return web3.eth.get_transaction_count(ETH_address)

# Activate contract function with required parameters
def activate_contract(attribute_certifier_address, private_key):
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    
    # Transaction setup for activating contract
    tx = {
        'nonce': get_nonce(attribute_certifier_address),
        'gasPrice': web3.eth.gas_price,
        'from': attribute_certifier_address
    }
    # Build and sign transaction
    message = contract.functions.updateMajorityCount().buildTransaction(tx)
    signed_transaction = web3.eth.account.sign_transaction(message, private_key)
    transaction_hash = __send_txt__(signed_transaction.rawTransaction)
    print(f'tx_hash: {web3.toHex(transaction_hash)}')
    
    # Wait for transaction receipt if verbose is True
    tx_receipt = web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=600)
    if verbose:
        print(tx_receipt)

# Send a signed transaction to the blockchain
def __send_txt__(signed_transaction_type):
    try:
        transaction_hash = web3.eth.send_raw_transaction(signed_transaction_type)
        return transaction_hash
    except Exception as e:
        print(e)
        if input("Do you want to try again (y/n)?") == 'y':
            __send_txt__(signed_transaction_type)
        else:
            raise Exception("Transaction failed")

# Send Authority names to the contract
def send_authority_names(authority_address, private_key, process_instance_id, hash_file):
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    
    # Transaction setup for sending Authority names
    tx = {
        'nonce': get_nonce(authority_address),
        'gasPrice': web3.eth.gas_price,
        'from': authority_address
    }
    # Encode and build transaction with Authority names
    message_bytes = hash_file.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    message = contract.functions.setAuthoritiesNames(int(process_instance_id), base64_bytes[:32],
                                                     base64_bytes[32:]).buildTransaction(tx)
    signed_transaction = web3.eth.account.sign_transaction(message, private_key)
    transaction_hash = __send_txt__(signed_transaction.rawTransaction)
    print(f'tx_hash: {web3.toHex(transaction_hash)}')
    tx_receipt = web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=600)
    if verbose:
        print(tx_receipt)

# Retrieve Authority names from the contract
def retrieve_authority_names(authority_address, process_instance_id):
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    # Fetch Authority names from the contract
    message = contract.functions.getAuthoritiesNames(authority_address, int(process_instance_id)).call()
    message_bytes = base64.b64decode(message)
    message = message_bytes.decode('ascii')
    return message

# Send hashed elements to the contract
def sendHashedElements(authority_address, private_key, process_instance_id, elements):
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    
    # Transaction setup for sending hashed elements
    tx = {
        'nonce': get_nonce(authority_address),
        'gasPrice': web3.eth.gas_price,
        'from': authority_address
    }
    # Encode and build transaction for hashed elements
    hashPart1 = elements[0].encode('utf-8')
    hashPart2 = elements[1].encode('utf-8')
    message = contract.functions.setElementHashed(process_instance_id, hashPart1[:32], hashPart1[32:], hashPart2[:32],
                                                  hashPart2[32:]).buildTransaction(tx)
    signed_transaction = web3.eth.account.sign_transaction(message, private_key)
    transaction_hash = __send_txt__(signed_transaction.rawTransaction)
    print(f'tx_hash: {web3.toHex(transaction_hash)}')
    tx_receipt = web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=600)
    if verbose:
        print(tx_receipt)

# Retrieve hashed elements from the contract
def retrieveHashedElements(eth_address, process_instance_id):
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    # Fetch hashed elements
    message = contract.functions.getElementHashed(eth_address, process_instance_id).call()
    hashedg11 = message[0].decode('utf-8')
    hashedg21 = message[1].decode('utf-8')
    return hashedg11, hashedg21

# Send elements to the contract in raw form
def sendElements(authority_address, private_key, process_instance_id, elements):
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    
    # Transaction setup for sending raw elements
    tx = {
        'nonce': get_nonce(authority_address),
        'gasPrice': web3.eth.gas_price,
        'from': authority_address
    }
    # Build transaction with encoded elements
    hashPart1 = elements[0]
    hashPart2 = elements[1]
    message = contract.functions.setElement(process_instance_id, hashPart1[:32], hashPart1[32:64],
                                            hashPart1[64:] + b'000000', hashPart2[:32], hashPart2[32:64],
                                            hashPart2[64:] + b'000000').buildTransaction(tx)
    signed_transaction = web3.eth.account.sign_transaction(message, private_key)
    transaction_hash = __send_txt__(signed_transaction.rawTransaction)
    print(f'tx_hash: {web3.toHex(transaction_hash)}')
    tx_receipt = web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=600)
    if verbose:
        print(tx_receipt)

# Retrieve raw elements from the contract
def retrieveElements(eth_address, process_instance_id):
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    # Fetch raw elements
    message = contract.functions.getElement(eth_address, process_instance_id).call()
    g11 = message[0] + message[1]
    g11 = g11[:90]
    g21 = message[2] + message[3]
    g21 = g21[:90]
    return g11, g21

# Send public parameters link to the contract
def send_parameters_link(authority_address, private_key, process_instance_id, hash_file):
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    
    # Transaction setup for sending public parameters link
    tx = {
        'nonce': get_nonce(authority_address),
        'gasPrice': web3.eth.gas_price,
        'from': authority_address
    }
    # Encode and build transaction for public parameters link
    message_bytes = hash_file.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    message = contract.functions.setPublicParameters(int(process_instance_id), base64_bytes[:32],
                                                     base64_bytes[32:]).buildTransaction(tx)
    signed_transaction = web3.eth.account.sign_transaction(message, private_key)
    transaction_hash = __send_txt__(signed_transaction.rawTransaction)
    print(f'tx_hash: {web3.toHex(transaction_hash)}')
    tx_receipt = web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=600)
    if verbose:
        print(tx_receipt)

# Retrieve the public parameters link from the contract
def retrieve_parameters_link(authority_address, process_instance_id):
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    # Fetch public parameters link
    message = contract.functions.getPublicParameters(authority_address, int(process_instance_id)).call()
    message_bytes = base64.b64decode(message)
    message = message_bytes.decode('ascii')
    return message

def send_publicKey_link(authority_address, private_key, process_instance_id, hash_file):
    # Load contract ABI
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    # Initialize contract
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    
    # Prepare transaction data
    tx = {
        'nonce': get_nonce(authority_address),
        'gasPrice': web3.eth.gas_price,
        'from': authority_address
    }
    # Encode hash file as base64
    message_bytes = hash_file.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    # Build and sign transaction to set public key
    message = contract.functions.setPublicKey(int(process_instance_id), base64_bytes[:32],
                                              base64_bytes[32:]).buildTransaction(tx)
    signed_transaction = web3.eth.account.sign_transaction(message, private_key)
    # Send transaction
    transaction_hash = __send_txt__(signed_transaction.rawTransaction)
    print(f'tx_hash: {web3.toHex(transaction_hash)}')
    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=600)
    if verbose:
        print(tx_receipt)

def retrieve_publicKey_link(eth_address, process_instance_id):
    # Load contract ABI
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    # Initialize contract
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    # Retrieve public key
    message = contract.functions.getPublicKey(eth_address, int(process_instance_id)).call()
    # Decode base64 message
    message_bytes = base64.b64decode(message)
    message1 = message_bytes.decode('ascii')
    return message1

def send_MessageIPFSLink(dataOwner_address, private_key, message_id, hash_file):
    # Load contract ABI
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    # Initialize contract
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    
    # Prepare transaction data
    tx = {
        'nonce': get_nonce(dataOwner_address),
        'gasPrice': web3.eth.gas_price,
        'from': dataOwner_address
    }
    # Encode hash file as base64
    message_bytes = hash_file.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    # Build and sign transaction to set IPFS link
    message = contract.functions.setIPFSLink(int(message_id), base64_bytes[:32], base64_bytes[32:]).buildTransaction(tx)
    signed_transaction = web3.eth.account.sign_transaction(message, private_key)
    # Send transaction
    transaction_hash = __send_txt__(signed_transaction.rawTransaction)
    print(f'tx_hash: {web3.toHex(transaction_hash)}')
    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=600)
    if verbose:
        print(tx_receipt)

def retrieve_MessageIPFSLink(message_id):
    # Load contract ABI
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    # Initialize contract
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    # Retrieve IPFS link and sender
    message = contract.functions.getIPFSLink(int(message_id)).call()
    sender = message[0]
    # Decode base64 IPFS link
    message_bytes = base64.b64decode(message[1])
    ipfs_link = message_bytes.decode('ascii')
    return ipfs_link, sender

def send_users_attributes(attribute_certifier_address, private_key, process_instance_id, hash_file):
    # Load contract ABI
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    # Initialize contract
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    
    # Prepare transaction data
    tx = {
        'nonce': get_nonce(attribute_certifier_address),
        'gasPrice': web3.eth.gas_price,
        'from': attribute_certifier_address
    }
    # Encode hash file as base64
    message_bytes = hash_file.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    # Build and sign transaction to set user attributes
    message = contract.functions.setUserAttributes(int(process_instance_id), base64_bytes[:32],
                                                   base64_bytes[32:]).buildTransaction(tx)
    signed_transaction = web3.eth.account.sign_transaction(message, private_key)
    # Send transaction
    transaction_hash = __send_txt__(signed_transaction.rawTransaction)
    print(f'tx_hash: {web3.toHex(transaction_hash)}')
    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=600)
    if verbose:
        print(tx_receipt)

def retrieve_users_attributes(process_instance_id):
    # Load contract ABI
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    # Initialize contract
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    # Retrieve user attributes
    message = contract.functions.getUserAttributes(int(process_instance_id)).call()
    # Decode base64 attributes
    message_bytes = base64.b64decode(message)
    message = message_bytes.decode('ascii')
    return message

def send_publicKey_readers(reader_address, private_key, hash_file):
    # Load contract ABI
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    # Initialize contract
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    
    # Prepare transaction data
    tx = {
        'nonce': get_nonce(reader_address),
        'gasPrice': web3.eth.gas_price,
        'from': reader_address
    }
    # Encode hash file as base64
    message_bytes = hash_file.encode('ascii')
    base64_bytes = base64.b64encode(message_bytes)
    # Build and sign transaction to set public key readers
    message = contract.functions.setPublicKeyReaders(base64_bytes[:32], base64_bytes[32:]).buildTransaction(tx)
    signed_transaction = web3.eth.account.sign_transaction(message, private_key)
    # Send transaction
    transaction_hash = __send_txt__(signed_transaction.rawTransaction)
    print(f'tx_hash: {web3.toHex(transaction_hash)}')
    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=600)
    if verbose:
        print(tx_receipt)

def retrieve_publicKey_readers(reader_address):
    # Load contract ABI
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    # Initialize contract
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    # Retrieve public key readers
    message = contract.functions.getPublicKeyReaders(reader_address).call()
    # Decode base64 message
    message_bytes = base64.b64decode(message)
    message1 = message_bytes.decode('ascii')
    return message1
    
def send_key_request(actor_address, process_id, list_auth, private_key_requesting):
    # Load contract ABI
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    # Initialize contract
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    
    # Get nonce
    nonce = web3.eth.getTransactionCount(actor_address)
    # Build transaction to notify Authorities
    tx = contract.functions.notifyAuthorities(process_id, list_auth).buildTransaction({
        'chainId': 1337,  # Chain ID for Ganache
        'gas': 200000,    # Estimate or specify gas limit
        'gasPrice': web3.eth.gasPrice,
        'nonce': nonce,
    })
    # Sign transaction
    signed_tx = web3.eth.account.sign_transaction(tx, private_key_requesting)
    # Send transaction
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
    # Return block number for tracking keys from Authorities
    block = web3.eth.blockNumber + 1
    return block

def send_ipfs_link(reader_address, process_instance_id, hash_file, authority_address, authority_private_key):
    # Get nonce
    nonce = web3.eth.getTransactionCount(authority_address)
    # Prepare transaction to send IPFS link
    tx = {
        'chainId': 1337,  # Chain ID for Ganache
        'nonce': nonce,
        'to': reader_address,
        'value': 0,
        'gas': 40000,
        'gasPrice': web3.eth.gasPrice,
        'data': web3.toHex(hash_file.encode() + b',' + str(process_instance_id).encode())
    }
    # Sign transaction
    signed_tx = web3.eth.account.sign_transaction(tx, authority_private_key)
    # Send transaction
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=600)
    if verbose:
        print(tx_receipt)

