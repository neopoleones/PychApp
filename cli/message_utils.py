import requests
import json
from encryption_utils import generate_aes_key, encrypt_message, RSAAdapter
from time import time
import base64


class ChatProtocol:
    def __init__(self, config, auth, s_pub_k) -> None:
        self.config = config
        self.auth = auth
        self.s_pub_k = s_pub_k

    def new_chat(self, interlocutor):
        url = f"http://{self.config['server_host']}:{self.config['server_port']}/api/chat/new"

        username, hostname = interlocutor.split('@')

        aes_key = generate_aes_key()

        rsa = RSAAdapter(pub_pem=self.s_pub_k.encode())

        payload = json.dumps({
            "dest_username": username,
            "dest_hostname": hostname,
            "enc_aes": rsa.encrypt(("A"*16)),
        })

        headers = {
            'Auth': self.auth,
            'Content-Type': 'application/json'
        }
    
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        if response.status_code == 200 and data['status'] == 'ok':
            return (base64.b64encode(aes_key).decode('utf-8'), data['cid'])
        return False

    def list_chats(self):
        url = f"http://{self.config['server_host']}:{self.config['server_port']}/api/chat/list"

        headers = {
            'Auth': self.auth,
        }

        response = requests.request("GET", url, headers=headers)

        data = response.json()
        if response.status_code == 200 and data['status'] == 'ok':
            return data['chats']
        return False
