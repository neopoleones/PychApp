class UserAuthentication:
    def __init__(self, config):
        self.logged_in_user = None
        self.config = config

    def register(self, username, password):
        # Placeholder for server communication
        pass

    def login(self, username, password):
        # Placeholder for server communication
        # If login is successful, set self.logged_in_user
        self.logged_in_user = username  # Assuming login is successful
        return True  # Return True if login is successful, False otherwise
