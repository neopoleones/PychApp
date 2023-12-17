from user_authentication import UserAuthentication
from chat_manager import ChatManager
from menu import Menu
import toml

def main():
    config = toml.load("config.toml")
    
    auth_system = UserAuthentication(config)
    chat_manager = ChatManager(config)
    menu = Menu(chat_manager, auth_system)
    menu.start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
