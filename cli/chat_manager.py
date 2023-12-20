import base64

from chat_ui import ChatUI
from rich.console import Console
from rich.prompt import Prompt
import sqlite3
import re
from message_utils import ChatProtocol
from encryption_utils import rsa_decrypt


class ChatManager:
    """
    Manages the chat functionality of the application.

    Args:
        config (dict): Configuration settings for the chat manager.
        username (str): The username of the current user.
        hostname (str): The hostname of the current user.
        auth (str): The authentication token for the user.
        s_pub_k (str): The server's RSA public key.
        public_key (str): The user's public key.
        private_key (str): The user's private key.

    Attributes:
        console (Console): The console object for printing messages.
        chats (list): List of ChatUI objects representing active chats.
        username (str): The username of the current user.
        hostname (str): The hostname of the current user.
        auth (str): The authentication token for the user.
        s_pub_k (str): The server's RSA public key.
        public_key (str): The user's public key.
        private_key (str): The user's private key.
        config (dict): Configuration settings for the chat manager.
        db_conn (sqlite3.Connection): Connection to the chats database.
        db_cursor (sqlite3.Cursor): Cursor for executing database queries.

    """

    def __init__(
            self,
            config,
            username,
            hostname,
            auth,
            s_pub_k,
            public_key,
            private_key):
        self.console = Console()
        self.chats = []
        self.username = username
        self.hostname = hostname
        self.auth = auth  # auth token
        self.s_pub_k = s_pub_k  # serer rsa public key
        self.public_key = public_key
        self.private_key = private_key
        self.config = config
        self.db_conn = sqlite3.connect('chats.db', check_same_thread=False)
        self.db_cursor = self.db_conn.cursor()
        self.db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY,
                username TEXT,
                interlocutor TEXT,
                aes_key TEXT,
                cid TEXT
            )
        """)
        self.load_existing_chats()

    def main_menu(self):
        """
        Displays the main menu and handles user input.
        """
        while True:
            self.console.print(
                "[1] Create new chat\n[2] Enter existing chat\n[3] Exit",
                style="bold yellow")
            choice = Prompt.ask("Choose an option")

            if choice == '1':
                self.create_new_chat()
            elif choice == '2':
                self.enter_existing_chat()
            elif choice == '3':
                break

    def create_new_chat(self):
        """
        Creates a new chat with an interlocutor.
        """
        interlocutor = Prompt.ask("Enter interlocutor's username@hostname")
        if re.match(r"^[a-zA-Z0-9]+@[a-zA-Z0-9]+$", interlocutor) is None:
            self.console.print("Invalid username@hostname", style="bold red")
            return

        chat_protocol = ChatProtocol(self.config, self.auth, self.s_pub_k)
        if not (a := chat_protocol.new_chat(interlocutor)):
            self.console.print("Error creating new chat", style="bold red")

        # aes_key - bytes
        aes_key, cid = a
        new_chat = ChatUI(self.config, f"{self.username}@{self.hostname}",
                          interlocutor, cid, self.auth, aes_key)

        aes_key_b64 = base64.b64encode(aes_key).decode("utf-8")

        # save aes_key to db
        self.db_cursor.execute("""
            INSERT INTO chats (username, interlocutor, aes_key, cid)
            VALUES (?, ?, ?, ?)
        """, (f"{self.username}@{self.hostname}", interlocutor, aes_key_b64, cid))
        self.db_conn.commit()
        self.chats.append(new_chat)
        new_chat.start()

    def load_existing_chats(self):
        """
        Loads existing chats from the database and server.
        """
        # Fetch chats from the local database
        self.db_cursor.execute("""
            SELECT username, interlocutor, cid, aes_key
            FROM chats
            WHERE username = ? OR interlocutor = ?
        """, (f"{self.username}@{self.hostname}", f"{self.username}@{self.hostname}"))
        rows = self.db_cursor.fetchall()
        for row in rows:
            aes_b64_enc = row[3]
            k_aes = base64.b64decode(aes_b64_enc)

            chat = ChatUI(self.config, f"{self.username}@{self.hostname}",
                          row[1], row[2], self.auth, k_aes)  # aes here also patched
            self.chats.append(chat)

        # Fetch chats from the server
        chat_protocol = ChatProtocol(self.config, self.auth, self.s_pub_k)
        server_chats = chat_protocol.list_chats()
        if server_chats:
            for chat in server_chats:
                if chat not in self.chats:
                    interlocutor = chat["init_login"] if chat[
                        "init_login"] != f"{self.username}@{self.hostname}" else chat["dst_login"]
                    username = f"{self.username}@{self.hostname}"
                    new_chat = ChatUI(
                        self.config,
                        username,
                        interlocutor,
                        chat["cid"],
                        self.auth,
                        rsa_decrypt(
                            chat["aes"],
                            self.private_key))
                    self.chats.append(new_chat)

    def enter_existing_chat(self):
        """
        Enters an existing chat.
        """
        if not self.chats:
            self.console.print("No existing chats.", style="bold red")
            return

        for index, chat in enumerate(self.chats):
            self.console.print(
                f"[{index}] {chat.username} - {chat.interlocutor}")
        chat_index = int(Prompt.ask("Select a chat"))
        if 0 <= chat_index < len(self.chats):
            self.chats[chat_index].start()
        else:
            self.console.print("Invalid selection", style="bold red")
