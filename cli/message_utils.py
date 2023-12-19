import requests
import json
from encryption_utils import generate_aes_key, rsa_encrypt, RSAAdapter
from time import time
import base64


class ChatProtocol:
    """
    Represents a chat protocol for interacting with a chat server.

    Args:
        config (dict): The configuration settings for the chat protocol.
        auth (str): The authentication token for accessing the chat server.
        s_pub_k (str): The public key used for encryption.

    Attributes:
        config (dict): The configuration settings for the chat protocol.
        auth (str): The authentication token for accessing the chat server.
        s_pub_k (str): The public key used for encryption.
    """

    def __init__(self, config, auth, s_pub_k) -> None:
        self.config = config
        self.auth = auth
        self.s_pub_k = s_pub_k

    def new_chat(self, interlocutor):
        """
        Creates a new chat with the specified interlocutor.

        Args:
            interlocutor (str): The username and hostname of the interlocutor in the format "username@hostname".

        Returns:
            tuple: A tuple containing the encoded AES key and the chat ID if the chat creation is successful, False otherwise.
        """
        url = f"http://{self.config['server_host']}:{self.config['server_port']}/api/chat/new"

        username, hostname = interlocutor.split('@')

        aes_key = generate_aes_key()

        rsa = RSAAdapter(pub_pem=self.s_pub_k.encode())

        payload = json.dumps({
            "dest_username": username,
            "dest_hostname": hostname,
            "enc_aes": rsa.encrypt(aes_key),
        })

        headers = {
            'Auth': self.auth,
            'Content-Type': 'application/json'
        }
    
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        if response.status_code == 200 and data['status'] == 'ok':
            return (base64.b64encode(aes_key.encode()).decode('utf-8'), data['cid'])
        return False

    def list_chats(self):
        """
        Retrieves a list of chats.

        Returns:
            list: A list of chats if the retrieval is successful, False otherwise.
        """
        url = f"http://{self.config['server_host']}:{self.config['server_port']}/api/chat/list"

        headers = {
            'Auth': self.auth,
        }

        response = requests.request("GET", url, headers=headers)

        data = response.json()
        if response.status_code == 200 and data['status'] == 'ok':
            return data['chats']
        return False
