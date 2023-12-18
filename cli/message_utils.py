import requests
import json
from encryption_utils import generate_aes_key, encrypt_message


class ChatProtocol:
    def __init__(self, config, auth, s_pub_k) -> None:
        self.config = config
        self.auth = auth
        self.s_pub_k = s_pub_k

    def new_chat(self, interlocutor, aes_key):
        url = f"{self.config['server_url']}/api/chat/new"

        username, hostname = interlocutor.split('@')

        payload = json.dumps({
            "dest_username": username,
            "dest_hostname": hostname,
            "enc_aes": encrypt_message(generate_aes_key(), self.s_pub_k),
        })

        headers = {
            'Auth': self.auth,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        if response.status_code == 200 and data['status'] == 'ok':
            return data['cid']
        return False

    def list_chats(self):
        url = f"{self.config['server_url']}/api/chat/list"

        headers = {
            'Auth': self.auth,
        }

        response = requests.request("GET", url, headers=headers)

        data = response.json()
        if response.status_code == 200 and data['status'] == 'ok':
            return data['chats']
        return False
