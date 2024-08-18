import rsa  
import ipfshttpclient
import block_int
import sqlite3
import io

# It generates the RSA keys of an actor!
def generate_keys(reader_address):
    (publicKey, privateKey) = rsa.newkeys(1024)
    publicKey_store = publicKey.save_pkcs1().decode('utf-8')
    privateKey_store = privateKey.save_pkcs1().decode('utf-8')
    
    f = io.StringIO()
    f.write('reader_address: ' + reader_address + '###' + publicKey_store)
    f.seek(0)
    
    api = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    hash_file = api.add_json(f.read())
    
    print(f'ipfs hash: {hash_file}')
    
    conn = sqlite3.connect('..//databases//reader//reader.db')
    x = conn.cursor()

    x.execute("INSERT OR IGNORE INTO rsa_private_key VALUES (?,?)", (reader_address, privateKey_store))
    conn.commit()
    x.execute("INSERT OR IGNORE INTO rsa_public_key VALUES (?,?,?)", (reader_address, hash_file, publicKey_store))
    conn.commit()
    
    # This function ("block_int.send_publicKey_readers") needs to be edited. It should be performed through MetaMask!
    # Now to test it I simulate the transaction of the MANUFACTURER ("0x7364cc4E7F136a16a7c38DE7205B7A5b18f17258") with his private key!
    return block_int.send_publicKey_readers(hash_file, reader_address)
