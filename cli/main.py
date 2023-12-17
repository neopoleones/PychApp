from user_authentication import UserAuthentication
from menu import Menu
import toml

def main(): 
    config = toml.load("config.toml")
    auth_system = UserAuthentication(config)
    menu = Menu(config, auth_system)
    menu.start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
