from decouple import config
import rsa  
import ipfshttpclient
import block_int
import sqlite3
import io
import argparse

api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

# Connection to SQLite3 reader database
conn = sqlite3.connect('..//databases//reader//reader.db')
x = conn.cursor()
    
def generate_keys(reader_name):
    
    reader_address = config(reader_name + '_ADDRESS')
    private_key = config(reader_name + '_PRIVATEKEY')
    
    (publicKey, privateKey) = rsa.newkeys(1024)
    publicKey_store = publicKey.save_pkcs1().decode('utf-8')
    privateKey_store = privateKey.save_pkcs1().decode('utf-8')
    f = io.StringIO()
    f.write('reader_address: ' + reader_address + '###' + publicKey_store)
    f.seek(0)
    hash_file = api.add_json(f.read())
    print(f'ipfs hash: {hash_file}')
    block_int.send_publicKey_readers(reader_address, private_key, hash_file)
    # reader address not necessary because each user has one key. Since we use only one 'reader/client' for all the
    # readers, we need a distinction.
    x.execute("INSERT OR IGNORE INTO rsa_private_key VALUES (?,?)", (reader_address, privateKey_store))
    conn.commit()
    x.execute("INSERT OR IGNORE INTO rsa_public_key VALUES (?,?,?)", (reader_address, hash_file, publicKey_store))
    conn.commit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Reader name', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r', '--reader', type=str, help='Specify a reader name')
    args = parser.parse_args()
    if args.reader:
        generate_keys(args.reader)
    else:
        parser.print_help()
