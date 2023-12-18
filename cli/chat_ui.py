from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
import queue
import threading
import time
import sqlite3

class ChatUI:
    def __init__(self, username, interlocutor, chat_id):
        self.console = Console()
        self.messages = queue.Queue()
        self.running = True
        self.username = username
        self.interlocutor = interlocutor
        self.chat_id = chat_id
        self.db_conn = sqlite3.connect('chats.db', check_same_thread=False)
        self.db_cursor = self.db_conn.cursor()
        self.db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                chat_id INTEGER,
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
                INSERT INTO messages (chat_id, sender, message)
                VALUES (?, ?, ?)
            """, (self.chat_id, self.username, message))
            self.db_conn.commit()

    def start(self):
        self.load_chat_history()
        threading.Thread(target=self.display_messages, daemon=True).start()
        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.send_message()

    def load_chat_history(self):
        self.db_cursor.execute("""
            SELECT sender, message, timestamp
            FROM messages
            WHERE chat_id = ?
            ORDER BY timestamp ASC
        """, (self.chat_id,))
        rows = self.db_cursor.fetchall()
        for row in rows:
            sender, message, _ = row
            self.messages.put((sender, message))

    def stop(self):
        self.running = False

    def receive_message(self, message):
        # self.console.print(f"{self.interlocutor}: ", end="")
        self.messages.put((self.interlocutor, message))
        self.db_cursor.execute("""
            INSERT INTO messages (chat_id, sender, message)
            VALUES (?, ?, ?)
        """, (self.chat_id, self.interlocutor, message))
        self.db_conn.commit()

    def receive_messages(self):
        time.sleep(5)
        self.console.print("\r")
        self.receive_message("Hello there!")
        time.sleep(5)
        self.console.print("\r")
        self.receive_message("Test123")
