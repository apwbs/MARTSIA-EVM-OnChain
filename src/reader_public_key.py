from decouple import config
import rsa  
import ipfshttpclient
import block_int
import sqlite3
import io
import argparse

# Function to generate RSA keys for a given reader
def generate_keys(reader_name):
    # Retrieve reader's address and private key from configuration
    reader_address = config(reader_name + '_ADDRESS')
    private_key = config(reader_name + '_PRIVATEKEY')
    
    # Generate new RSA public and private keys
    (publicKey, privateKey) = rsa.newkeys(1024)
    publicKey_store = publicKey.save_pkcs1().decode('utf-8')
    privateKey_store = privateKey.save_pkcs1().decode('utf-8')
    
    # Create a string buffer to hold the address and public key
    f = io.StringIO()
    f.write('reader_address: ' + reader_address + '###' + publicKey_store)
    f.seek(0)
    
    # Connect to IPFS and add the JSON content
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    hash_file = api.add_json(f.read())
    print(f'ipfs hash: {hash_file}')
    block_int.send_publicKey_readers(reader_address, private_key, hash_file)
    
    # Connection to SQLite3 Reader database
    conn = sqlite3.connect('..//databases//reader//reader.db')
    x = conn.cursor()
    
    # Store private key in the database
    x.execute("INSERT OR IGNORE INTO rsa_private_key VALUES (?,?)", (reader_address, privateKey_store))
    conn.commit()
    
    # Store public key and its IPFS hash in the database
    x.execute("INSERT OR IGNORE INTO rsa_public_key VALUES (?,?,?)", (reader_address, hash_file, publicKey_store))
    conn.commit()

if __name__ == "__main__":
    # Set up argument parser for command-line interface
    parser = argparse.ArgumentParser(description='Reader name', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r', '--reader', type=str, help='Specify a reader name')
    
    # Parse arguments from command line
    args = parser.parse_args()
    if args.reader:
        generate_keys(args.reader)  # Generate keys if Reader name is provided
    else:
        parser.print_help()  # Print help if no Reader name is provided

