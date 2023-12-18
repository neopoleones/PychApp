from rich.console import Console
from rich.prompt import Prompt
from chat_manager import ChatManager


class Menu:
    def __init__(self, config, auth_system):
        self.config = config
        self.auth_system = auth_system
        self.chat_manager = None
        self.console = Console()
        self.public_key = None
        self.private_key = None

        if not self.auth_system.is_server_available():
            self.console.print("Server is not available", style="bold red")
            self.console.print("Exiting...", style="bold red")
            exit(1)

    def start(self):
        while True:
            if self.auth_system.logged_in_user:
                self.chat_manager.username = self.auth_system.logged_in_user
                self.chat_manager.main_menu()
            else:
                self.show_login_menu()

    def show_login_menu(self):
        self.console.print(
            "[1] Register\n[2] Login\n[3] Exit", style="bold yellow")
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
            self.public_key = keys[0]
            self.private_key = keys[1]

        else:
            self.console.print("Registration failed", style="bold red")

    def login_user(self):
        username = Prompt.ask("Enter your username")
        hostname = Prompt.ask("Enter a hostname")
        password = Prompt.ask("Enter your password", password=True)
        if login := self.auth_system.login(username, hostname, password):
            self.console.print("Login successful", style="bold green")
            self.chat_manager = ChatManager(self.config, username, hostname, auth=login[0], s_pub_k=login[1], private_key=self.private_key,
                                            public_key=self.public_key)
        else:
            self.console.print(
                "Invalid username or password", style="bold red")
