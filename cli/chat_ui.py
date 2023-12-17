from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
import queue
import threading
import time


class ChatUI:
    def __init__(self, username, interlocutor):
        self.console = Console()
        self.messages = queue.Queue()
        self.running = True
        self.username = username
        self.interlocutor = interlocutor

    def display_messages(self):
        while self.running:
            if not self.messages.empty():
                message = self.messages.get()
                self.console.print("\r")
                self.console.print(Panel(message, expand=False))

    def send_message(self):
        while self.running:
            message = Prompt.ask(self.username)
            self.messages.put(Text(message, style="bold green"))

    def start(self):
        threading.Thread(target=self.display_messages, daemon=True).start()
        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.send_message()

    def stop(self):
        self.running = False

    def receive_message(self, message):
        self.console.print(f"{self.interlocutor}: ", end="")
        self.messages.put(Text(message, style="bold blue"))

    def receive_messages(self):
        time.sleep(5)
        self.receive_message("Hello there!")
        time.sleep(5)
        self.receive_message("Test123")
