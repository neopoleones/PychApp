from chat_ui import ChatUI
from rich.console import Console
from rich.prompt import Prompt


class ChatManager:
    # unique for each user
    def __init__(self, config):
        self.console = Console()
        self.chats = []
        self.username = None
        self.config = config
        self.auth = None  # auth token

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
        interlocutor = Prompt.ask("Enter interlocutor's username")
        new_chat = ChatUI(self.username, interlocutor)
        self.chats.append(new_chat)
        new_chat.start()

    def enter_existing_chat(self):
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
