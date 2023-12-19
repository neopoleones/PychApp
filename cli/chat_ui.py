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
    def __init__(self, config, username, interlocutor, cid, auth, aes_key):
        self.ws_url = f"ws://{config['server_host']}:{config['ws_port']}/ws"
        self.console = Console()
        self.messages = queue.Queue()
        self.running = True
        self.username = username
        self.interlocutor = interlocutor
        self.cid = cid # chat id
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
        while self.running:
            if not self.messages.empty():
                sender, message = self.messages.get()
                self.console.print("\r")
                self.console.print(f"{sender}:")

                if sender == self.username:
                    style = "bold green"
                else:
                    style = "bold blue"

                self.console.print(Panel(Text(message, style=style), expand=False))

    def send_message(self):
        while self.running:
            message = Prompt.ask(self.username)
            self.messages.put((self.username, message))
            self.db_cursor.execute("""
                INSERT INTO messages (cid, sender, message)
                VALUES (?, ?, ?)
            """, (self.cid, self.username, message))
            self.db_conn.commit()
            self.send_ws(aes_encrypt(message, self.aes_key))

    def start(self):
        self.load_chat_history()
        self.connect_ws()
        threading.Thread(target=self.display_messages, daemon=True).start()
        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.send_message()

    def load_chat_history(self):
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
        self.running = False
        if self.ws:
            self.ws.close()

    def receive_message(self, message):
        # self.console.print(f"{self.interlocutor}: ", end="")
        self.messages.put((self.interlocutor, message))
        self.db_cursor.execute("""
            INSERT INTO messages (cid, sender, message)
            VALUES (?, ?, ?)
        """, (self.cid, self.interlocutor, message))
        self.db_conn.commit()

    def receive_messages(self):
            while self.running:
                if self.ws:
                    message = aes_decrypt(json.loads(self.receive_ws())["msg"], self.aes_key)
                    print(message)
                    if message:
                        self.receive_message(message)
                time.sleep(0.1)  # Reduce CPU usage

    def connect_ws(self):
        self.ws = websocket.WebSocket()
        self.ws.connect(self.ws_url)
        self.ws.send(json.dumps({
            "token": self.auth,
            "dest_login": self.interlocutor,
        }))
        self.ws.recv()
    
    def send_ws(self, message):
        self.ws.send(json.dumps({
            "msg": message,
            "timestamp": time.time(),
        }))
    
    def receive_ws(self):
        try:
            message = self.ws.recv()
            return message
        except websocket.WebSocketConnectionClosedException:
            return None
