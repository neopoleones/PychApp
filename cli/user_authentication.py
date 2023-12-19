import requests
import json
from cli.encryption_utils import generate_key_pair
import os
import sqlite3


class UserAuthentication:
    """
    Class for user authentication.

    Args:
        config (dict): Configuration settings.

    Attributes:
        logged_in_user (str): Currently logged in user.
        config (dict): Configuration settings.

    Methods:
        is_server_available: Check if the server is available.
        register: Register a new user.
        create_users_table: Create the users table in the database.
        save_keys_to_db: Save user keys to the database.
        load_keys_from_db: Load user keys from the database.
        login: Log in a user.

    """

    def __init__(self, config):
        self.logged_in_user = None
        self.config = config
        self.create_users_table()

    def is_server_available(self):
        """
        Check if the server is available.

        Returns:
            bool: True if the server is available, False otherwise.

        """
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
        """
        Register a new user.

        Args:
            username (str): User's username.
            hostname (str): User's hostname.
            password (str): User's password.

        Returns:
            tuple: A tuple containing the private key and public key if registration is successful, False otherwise.

        """
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
        """
        Create the users table in the database.

        """
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
        """
        Save user keys to the database.

        Args:
            username (str): User's username.
            public_key (str): User's public key.
            private_key (str): User's private key.

        """
        db_conn = sqlite3.connect('users.db', check_same_thread=False)
        db_cursor = db_conn.cursor()
        db_cursor.execute("""
            INSERT INTO users (username, public_key, private_key)
            VALUES (?, ?, ?)
        """, (username, public_key, private_key))
        db_conn.commit()

    def load_keys_from_db(self, username):
        """
        Load user keys from the database.

        Args:
            username (str): User's username.

        Returns:
            tuple: A tuple containing the public key and private key of the user.

        """
        db_conn = sqlite3.connect('users.db', check_same_thread=False)
        db_cursor = db_conn.cursor()
        db_cursor.execute("""
            SELECT public_key, private_key FROM users WHERE username = ?
        """, (username,))
        return db_cursor.fetchone()

    def login(self, username, hostname, password):
        """
        Log in a user.

        Args:
            username (str): User's username.
            hostname (str): User's hostname.
            password (str): User's password.

        Returns:
            tuple: A tuple containing the authentication token and server public key if login is successful, False otherwise.

        """
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
