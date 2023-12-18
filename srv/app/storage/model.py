import hashlib
import time

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

    @staticmethod
    def parse_login(login):
        return login.split("@")


class Chat:
    def __init__(self, secret: str, aes_srv_encoded: bytes, u_init: User, u_dest: User, cid=None, plain=False):
        if not plain:
            self.ra = RSAAdapter(
                secret=secret,
                pub_pem=u_init.s_pub_k,
                p_pem=u_init.s_p_k
            )

            self.aes = self.ra.decrypt(aes_srv_encoded)
            self.init_user_login = u_init.get_login()
            self.dst_user_login = u_dest.get_login()
        else:
            self.aes = secret
            self.init_user_login = u_init
            self.dst_user_login = u_dest

        self.cid = cid

    def to_mongo(self):
        return {
            "aes": self.aes,
            "init_login": self.init_user_login,
            "dst_login": self.dst_user_login,
        }

    def safe_serialize(self, sp):
        model = self.to_mongo()
        if isinstance(model["aes"], (bytes, bytearray)):
            model["aes"] = model["aes"].decode('utf-8')

        model["aes"] = sp.encrypt(model["aes"])
        return model


class Message:
    def __init__(self, chat: Chat, author_id: str, msg: str, timestamp: float, mid=None):
        self.mid = mid
        self.msg = msg
        self.chat = chat
        self.author_id = author_id
        self.timestamp = timestamp
        self.read = False

    def to_mongo(self):
        return {
            "msg": self.msg,
            "chat_id": str(self.chat.cid),
            "author_id": self.author_id,
            "read": self.read,
            "timestamp": self.timestamp,
        }

    def serialize(self):
        return {
            "msg": self.msg,
            "author_id": self.author_id,
            "timestamp": self.timestamp,
        }