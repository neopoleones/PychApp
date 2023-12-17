import hashlib


class User:
    def __init__(self, name: str, hostname: str, password: str, uid=None):
        """Name and Hostname should be alphanumeric"""

        self.uid = uid
        self.name = name
        self.hostname = hostname
        self.password = password

        sp = self.password

    def validate(self):
        return self.name.isalnum() and self.hostname.isalpha() and len(self.password) >= 8

    def to_mongo(self):
        return {"name": self.name, "hostname": self.hostname, "password": self.harden(self.password)}

    def uid_as_bytes(self):
        return str(self.uid).encode()

    def get_login(self):
        return f"{self.name}@{self.hostname}"

    @staticmethod
    def harden(password):
        return hashlib.md5(password.encode()).hexdigest()
