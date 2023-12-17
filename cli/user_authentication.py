import requests
import json
from encryption_utils import generate_key_pair

class UserAuthentication:
    def __init__(self, config):
        self.logged_in_user = None
        self.config = config

    def register(self, username, hostname, password):
        private_key, public_key = generate_key_pair()
        url = f"{self.config['server_url']}/api/user/register"

        payload = json.dumps({
            "username": username,
            "hostname": hostname,
            "password": password,
            "u_pub_k": public_key.decode('utf-8'),
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        
        if response.status_code == 200:
            return private_key, public_key
        return False


    def login(self, username, hostname, password):
        url = f"{self.config['server_url']}/api/user/login"

        payload = json.dumps({
            "username": username,
            "hostname": hostname,
            "password": password,
        })

        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 200:
            self.logged_in_user = f"{username}@{hostname}"
            return response.headers['Auth']
        return False
