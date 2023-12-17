import hashlib
from app.storage.provider import RSAAdapter


class User:
    s_p_k: str
    s_pub_k: str

    def __init__(self, name: str, hostname: str, password: str, u_pub_k: str, uid=None):
        """Name and Hostname should be alphanumeric"""

        self.uid = uid
        self.name = name
        self.hostname = hostname
        self.password = password
        self.u_pub_k = u_pub_k

    def __str__(self):
        return self.get_login()

    def validate(self):
        return self.name.isalnum() and self.hostname.isalnum() and len(self.password) >= 8

    def to_mongo(self):
        return {
            "name": self.name,
            "hostname": self.hostname,
            "password": self.harden(self.password),
            "u_pub_pem": self.u_pub_k,
            "s_p_pem": self.s_p_k,
            "s_pub_pem": self.s_pub_k,
        }

    def uid_as_bytes(self):
        return str(self.uid).encode()

    def get_login(self):
        return f"{self.name}@{self.hostname}"

    def set_srv_certificates(self, pub_pem, p_pem):
        self.s_p_k = p_pem
        self.s_pub_k = pub_pem

    @staticmethod
    def harden(password):
        return hashlib.md5(password.encode()).hexdigest()


class Chat:
    def __init__(self, secret: str, aes_srv_encoded: bytes, u_init: User, u_dest: User):
        print(secret)

        self.ra = RSAAdapter(
            secret=secret,
            pub_pem=u_init.s_pub_k,
            p_pem=u_init.s_p_k
        )

        self.aes = self.ra.decrypt(aes_srv_encoded)
        self.init_user = u_init
        self.dst_user = u_dest

    def to_mongo(self):
        return {
            "aes": self.aes.decode('utf-8'),
            "init_uid": self.init_user,
            "dst_user": self.dst_user,
        }
