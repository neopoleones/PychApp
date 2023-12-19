import requests
import json
from encryption_utils import generate_key_pair
import os
import sqlite3


class UserAuthentication:
    def __init__(self, config):
        self.logged_in_user = None
        self.config = config
        self.create_users_table()

    def is_server_available(self):
        if os.environ.get('PYCH_DEBUG'):
            return True
    
        url = f"http://{self.config['server_host']}:{self.config['server_port']}/status"
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
            data = response.json()
            return data.get("status") == "ok"
        except (requests.HTTPError, requests.ConnectionError, ValueError):
            return False

    def register(self, username, hostname, password):
        private_key, public_key = generate_key_pair()
        url = f"http://{self.config['server_host']}:{self.config['server_port']}/api/user/register"

        payload = json.dumps({
            "username": username,
            "hostname": hostname,
            "password": password,
            "u_pub_k": public_key.decode("utf-8"),
        })
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            return private_key, public_key
        return False

    def create_users_table(self):
        db_conn = sqlite3.connect('users.db', check_same_thread=False)
        db_cursor = db_conn.cursor()
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                public_key TEXT,
                private_key TEXT
            )
        """)
        db_conn.commit()

    def save_keys_to_db(self, username, public_key, private_key):
        db_conn = sqlite3.connect('users.db', check_same_thread=False)
        db_cursor = db_conn.cursor()
        db_cursor.execute("""
            INSERT INTO users (username, public_key, private_key)
            VALUES (?, ?, ?)
        """, (username, public_key, private_key))
        db_conn.commit()

    def load_keys_from_db(self, username):
        db_conn = sqlite3.connect('users.db', check_same_thread=False)
        db_cursor = db_conn.cursor()
        db_cursor.execute("""
            SELECT public_key, private_key FROM users WHERE username = ?
        """, (username,))
        return db_cursor.fetchone()

    def login(self, username, hostname, password):
        url = f"http://{self.config['server_host']}:{self.config['server_port']}/api/user/login"

        payload = json.dumps({
            "username": username,
            "hostname": hostname,
            "password": password,
        })

        headers = {
            "Content-Type": "application/json"
        }

        if os.environ.get('PYCH_DEBUG'):
            self.logged_in_user = f"{username}@{hostname}"
            return "TEST_AUTH_TOKEN", "test_public_key="
            
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        if response.status_code == 200 and data.get("status") == "ok":
            self.logged_in_user = f"{username}@{hostname}"
            return response.headers["Auth"], data.get("s_pub_k")
        return False
