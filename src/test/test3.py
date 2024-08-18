import requests
import base64
import json


def read_process_id_from_file(process_id_path):
    with open(process_id_path, 'r') as file:
        content = file.read().strip()
        process_id = int(content)
    return process_id
    

def file_to_base64(file_path):
    try:
        with open(file_path, 'rb') as file:
            encoded = base64.b64encode(file.read()).decode('utf-8')
        return encoded
    except Exception as e:
        print(f"Error encoding file to Base64: {e}")
        return None


process_id = read_process_id_from_file("process_id.txt")

# Set the URL to the Flask route
url = "http://localhost:8888//encrypt/"

# Prepare the payload (data) to send in the request
payload = {
    "policy": {
        "export_document_slice1.pdf": "(MANUFACTURER@AUTH1 or (SUPPLIER@AUTH4 and INTERNATIONAL@AUTH2))"
    },
    "process_id": process_id,
    # Here the actor is the INTERNATIONAL SUPPLIER, for testing purposes he pushes the message to
    # be encrypted on the blockchain directly through his private key
    "actor": "0xa5B6B3729Cf8f377EF6F97d87C49661b36Ed02bB",
    "message": file_to_base64("../../input_files/export_document_slice1.pdf")
}

# Set the headers to specify that the content type is JSON
headers = {
    "Content-Type": "application/json"
}

# Send the POST request
response = requests.post(url, json=payload, headers=headers)

# Print out the status code and response
print("Status Code:", response.status_code)
print("Response Text:", response.text, end="")

response_dict = json.loads(response.text)
message_id = response_dict.get('message_id')

# I save automatically the message_id to a file so I do not need to edit test4.py for every test
with open("message_id.txt", 'w') as file:
        file.write(str(message_id))
