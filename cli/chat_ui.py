from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
import queue
import threading
import time
import sqlite3
import websocket
import json
from encryption_utils import aes_decrypt, aes_encrypt
import base64


class ChatUI:
    """
    Represents a chat user interface.

    Args:
        config (dict): The configuration settings.
        username (str): The username of the user.
        interlocutor (str): The username of the interlocutor.
        cid (int): The chat ID.
        auth (str): The authentication token.
        aes_key (str): The AES encryption key.

    Attributes:
        ws_url (str): The WebSocket URL.
        console (Console): The console object for printing messages.
        messages (Queue): The queue to store incoming messages.
        running (bool): Flag indicating if the chat UI is running.
        username (str): The username of the user.
        interlocutor (str): The username of the interlocutor.
        cid (int): The chat ID.
        auth (str): The authentication token.
        aes_key (bytes): The AES encryption key.
        db_conn (sqlite3.Connection): The SQLite database connection.
        db_cursor (sqlite3.Cursor): The database cursor.
        ws (WebSocket): The WebSocket connection.

    """

    def __init__(
            self,
            config,
            username,
            interlocutor,
            cid,
            auth,
            aes_key: bytes):
        self.ws_url = f"ws://{config['server_host']}:{config['ws_port']}/ws"
        self.console = Console()
        self.messages = queue.Queue()
        self.running = True
        self.username = username
        self.interlocutor = interlocutor
        self.cid = cid  # chat id
        self.auth = auth
        self.aes_key = aes_key
        self.db_conn = sqlite3.connect('chats.db', check_same_thread=False)
        self.db_cursor = self.db_conn.cursor()
        self.ws = None
        self.db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                cid INTEGER,
                sender TEXT,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def display_messages(self):
        """
        Displays the incoming messages in the console.
        """
        while self.running:
            if not self.messages.empty():
                sender, message = self.messages.get()
                self.console.print("\r")
                self.console.print(f"{sender}:")

                if sender == self.username:
                    style = "bold green"
                else:
                    style = "bold blue"

                self.console.print(
                    Panel(
                        Text(
                            message,
                            style=style),
                        expand=False))

    def send_message(self):
        """
        Sends a message to the interlocutor.
        """
        while self.running:
            message = Prompt.ask(self.username)
            self.messages.put((self.username, message))
            self.db_cursor.execute("""
                INSERT INTO messages (cid, sender, message)
                VALUES (?, ?, ?)
            """, (self.cid, self.username, message))
            self.db_conn.commit()

            # допустим, что ключ - bytes
            enc_message = aes_encrypt(message.encode(), self.aes_key)
            b64_message = base64.b64encode(enc_message).decode()
            self.send_ws(b64_message)

    def start(self):
        """
        Starts the chat UI.
        """
        self.load_chat_history()
        self.connect_ws()
        threading.Thread(target=self.display_messages, daemon=True).start()
        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.send_message()

    def load_chat_history(self):
        """
        Loads the chat history from the database.
        """
        self.db_cursor.execute("""
            SELECT sender, message, timestamp
            FROM messages
            WHERE cid = ?
            ORDER BY timestamp ASC
        """, (self.cid,))
        rows = self.db_cursor.fetchall()
        for row in rows:
            sender, message, _ = row
            self.messages.put((sender, message))

    def stop(self):
        """
        Stops the chat UI.
        """
        self.running = False
        if self.ws:
            self.ws.close()

    def receive_message(self, message: str):
        """
        Receives a message from the interlocutor.

        Args:
            message (str): The received message.
        """

        self.messages.put((self.interlocutor, message))
        self.db_cursor.execute("""
            INSERT INTO messages (cid, sender, message)
            VALUES (?, ?, ?)
        """, (self.cid, self.interlocutor, message))
        self.db_conn.commit()

    def receive_messages(self):
        """
        Receives incoming messages from the WebSocket connection.
        """
        while self.running:
            if self.ws:
                raw_msg = self.receive_ws()
                b64_message = json.loads(raw_msg)["msg"]
                b64_decoded = base64.b64decode(b64_message)

                message = aes_decrypt(
                    b64_decoded,
                    self.aes_key
                )
                if message:
                    self.receive_message(message.decode())
            time.sleep(0.1)  # Reduce CPU usage

    def connect_ws(self):
        """
        Connects to the WebSocket server.
        """
        self.ws = websocket.WebSocket()
        self.ws.connect(self.ws_url)
        self.ws.send(json.dumps({
            "token": self.auth,
            "dest_login": self.interlocutor,
        }))
        self.ws.recv()

    def send_ws(self, message):
        """
        Sends a message through the WebSocket connection.

        Args:
            message (str): The message to be sent.
        """
        self.ws.send(json.dumps({
            "msg": message,
            "timestamp": time.time(),
        }))

    def receive_ws(self):
        """
        Receives a message from the WebSocket connection.

        Returns:
            str: The received message.
        """
        try:
            message = self.ws.recv()
            return message
        except websocket.WebSocketConnectionClosedException:
            return None
