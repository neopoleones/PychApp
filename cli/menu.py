from rich.console import Console
from rich.prompt import Prompt


class Menu:
    def __init__(self, chat_manager, auth_system):
        self.console = Console()
        self.chat_manager = chat_manager
        self.auth_system = auth_system

    def start(self):
        while True:
            if self.auth_system.logged_in_user:
                self.chat_manager.username = self.auth_system.logged_in_user
                self.chat_manager.main_menu()
            else:
                self.show_login_menu()

    def show_login_menu(self):
        self.console.print("[1] Register\n[2] Login\n[3] Exit", style="bold yellow")
        choice = Prompt.ask("Choose an option")

        if choice == '1':
            self.register_user()
        elif choice == '2':
            self.login_user()
        elif choice == '3':
            exit(0)

    def register_user(self):
        username = Prompt.ask("Enter a username")
        hostname = Prompt.ask("Enter a hostname")
        password = Prompt.ask("Enter a password", password=True)
        
        if keys := self.auth_system.register(username, hostname, password):
            self.console.print("Registration successful", style="bold green")
            self.chat_manager.public_key = keys[0]
            self.chat_manager.private_key = keys[1]

        else:
            self.console.print("Registration failed", style="bold red")

    def login_user(self):
        username = Prompt.ask("Enter your username")
        hostname = Prompt.ask("Enter a hostname")
        password = Prompt.ask("Enter your password", password=True)
        if auth := self.auth_system.login(username, hostname, password):
            self.chat_manager.auth = auth
            self.console.print("Login successful", style="bold green")
        else:
            self.console.print("Invalid username or password", style="bold red")
