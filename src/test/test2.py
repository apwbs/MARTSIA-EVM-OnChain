import requests


def read_process_id_from_file(process_id_path):
    with open(process_id_path, 'r') as file:
        content = file.read().strip()
        process_id = int(content)
    return process_id


process_id_value = read_process_id_from_file("process_id.txt")

# Set the URL to the Flask route
url = "http://localhost:8888/certification/attributes_certification_and_authorities/"

# Prepare the payload (data) to send in the request
payload = {
    "roles": {
        "0x7364cc4E7F136a16a7c38DE7205B7A5b18f17258": ["MANUFACTURER@AUTH1"],
        "0xa5B6B3729Cf8f377EF6F97d87C49661b36Ed02bB": ["INTERNATIONAL@AUTH2", "SUPPLIER@AUTH3", "SUPPLIER@AUTH4"],
        "0xb885E5701a3A4714799eE906f4Aa7C297f16D90a": ["CUSTOMS@AUTH1", "CUSTOMS@AUTH4"],
        "0x0882271d553738aB2b238F7a95fa7Ce0DE171EF5": ["CUSTOMS@AUTH1", "INTERNATIONAL@AUTH2"],
        "0xaA799c5cF973b4efe8386D4AcEfdAa2BF8e76Ab3": ["INTERNATIONAL@AUTH3", "CARRIER@AUTH2"]
    },
    "process_id": process_id_value
}

# Set the headers to specify that the content type is JSON
headers = {
    "Content-Type": "application/json"
}

# Send the POST request
response = requests.post(url, json=payload, headers=headers)

# Print out the status code and response
print("Status Code:", response.status_code)
print("Response Text:", response.text)
