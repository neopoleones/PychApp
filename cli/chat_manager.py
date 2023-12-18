from chat_ui import ChatUI
from rich.console import Console
from rich.prompt import Prompt
import sqlite3
import re
from message_utils import ChatProtocol

class ChatManager:
    # unique for each user
    def __init__(self, config, username, hostname, auth, s_pub_k):
        self.console = Console()
        self.chats = []
        self.username = username
        self.hostname = hostname
        self.auth = auth  # auth token
        self.s_pub_k = s_pub_k
        self.config = config
        self.public_key = None
        self.private_key = None
        self.db_conn = sqlite3.connect('chats.db', check_same_thread=False)
        self.db_cursor = self.db_conn.cursor()
        self.db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY,
                username TEXT,
                interlocutor TEXT
            )
        """)
        self.load_existing_chats()

    def main_menu(self):
        while True:
            self.console.print(
                "[1] Create new chat\n[2] Enter existing chat\n[3] Exit", style="bold yellow")
            choice = Prompt.ask("Choose an option")

            if choice == '1':
                self.create_new_chat()
            elif choice == '2':
                self.enter_existing_chat()
            elif choice == '3':
                break

    def create_new_chat(self):
        interlocutor = Prompt.ask("Enter interlocutor's username@hostname")
        if re.match(r"^[a-zA-Z0-9]+@[a-zA-Z0-9]+$", interlocutor) is None:
            self.console.print("Invalid username@hostname", style="bold red")
            return
        chat_id = len(self.chats) + 1  # generate a unique chat_id
        new_chat = ChatUI(self.username, interlocutor, chat_id)
        self.db_cursor.execute("""
            INSERT INTO chats (username, interlocutor)
            VALUES (?, ?)
        """, (self.username, interlocutor))
        self.db_conn.commit()
        chat_protocol = ChatProtocol()
        new_chat.start(chat_protocol)

    def load_existing_chats(self):
        self.db_cursor.execute("""
            SELECT username, interlocutor
            FROM chats
            WHERE username = ?
        """, (f"{self.username}@{self.hostname}",))
        rows = self.db_cursor.fetchall()
        print("rows: ", len(rows))
        for row in rows:
            chat_id = len(self.chats) + 1
            chat = ChatUI(self.username, row[1], chat_id)
            self.chats.append(chat)

    def enter_existing_chat(self):
        if not self.chats:
            self.console.print("No existing chats.", style="bold red")
            return

        for index, chat in enumerate(self.chats):
            self.console.print(
                f"[{index}] {chat.username} - {chat.interlocutor}")
        chat_index = int(Prompt.ask("Select a chat"))
        if 0 <= chat_index < len(self.chats):
            chat_protocol = ChatProtocol()
            self.chats[chat_index].start(chat_protocol)
        else:
            self.console.print("Invalid selection", style="bold red")
