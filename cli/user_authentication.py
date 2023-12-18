import requests
import json
from encryption_utils import generate_key_pair

class UserAuthentication:
    def __init__(self, config):
        self.logged_in_user = None
        self.config = config

    def is_server_available(self):
        url = f"{self.config['server_url']}/status"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
            data = response.json()
            return data.get('status') == 'ok'
        except (requests.HTTPError, requests.ConnectionError, ValueError):
            return False

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
