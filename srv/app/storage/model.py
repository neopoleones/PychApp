import hashlib
from app.storage.provider import RSAAdapter


class User:
    """
    Represents a user in the pychapp.

    This class encapsulates the data and operations associated with a user, including their credentials,
    public key, and server certificates.

    Attributes:
        s_p_k: The private key of the server, in PEM format.
        s_pub_k: The public key of the server, in PEM format.
        u_pub_k: The public key of the user, in PEM format.
        uid: The unique identifier of the user.
        name: The name of the user, should be alphanumeric.
        hostname: The hostname associated with the user, should be alphanumeric.
        password: The password of the user, at least 8 characters.
    """

    def __init__(self, name, hostname, password, u_pub_k, uid=None):
        """
        Initialize a User instance.

        Args:
            name: The name of the user. Must be alphanumeric.
            hostname: The hostname associated with the user. Must be alphanumeric.
            password: The password of the user.
            u_pub_k: The public key of the user, in PEM format.
            uid: The unique identifier of the user. Defaults to None.
        """

        self.uid = uid
        self.name = name
        self.hostname = hostname
        self.password = password
        self.u_pub_k = u_pub_k

        self.s_p_k = None
        self.s_pub_k = None

    def __str__(self):
        """
        Return a string representation of the user.

        Returns:
            The user's login identifier.
        """

        return self.get_login()

    def validate(self):
        """
        Validate the user fields.

        Returns:
            True if the user's name and hostname are alphanumeric and the password is at least 8 characters long.
        """

        uc = self.name.isalnum() and self.hostname.isalnum()
        return uc and len(self.password) >= 8

    def to_mongo(self):
        """
        Prepare the user's data for storage in MongoDB.

        Returns:
            A dictionary of the user's data, suitable for MongoDB.
        """

        return {
            "name": self.name,
            "hostname": self.hostname,
            "password": self.harden(self.password),
            "u_pub_pem": self.u_pub_k,
            "s_p_pem": self.s_p_k,
            "s_pub_pem": self.s_pub_k,
        }

    def uid_as_bytes(self):
        """
        Convert the user's UID to bytes.

        Returns:
            The user's UID in bytes.
        """

        return str(self.uid).encode()

    def get_login(self):
        """
        Get the user's login identifier.

        Returns:
            The login identifier of the user, typically in the format 'name@hostname'.
        """

        return f"{self.name}@{self.hostname}"

    def set_srv_certificates(self, pub_pem, p_pem):
        """
        Set the server's certificates for the user.

        Args:
            pub_pem: The public key of the server, in PEM format.
            p_pem: The private key of the server, in PEM format.
        """

        self.s_p_k = p_pem
        self.s_pub_k = pub_pem

    @staticmethod
    def harden(password):
        """
        Generates a hashed version of a given password.

        This static method applies MD5 hashing to a password. It's a basic form of security measure
        to ensure that plain-text passwords are not stored or transmitted.

        Args:
            password: The password to be hashed.

        Returns:
            A hexadecimal MD5 hash of the password.
        """

        return hashlib.md5(password.encode()).hexdigest()

    @staticmethod
    def parse_login(login):
        """
        Parses a login string into its constituent parts.

        This static method splits a login string into the username and hostname parts. The login
        string is expected to be in the format 'username@hostname'.

        Args:
            login: The login string to be parsed.
        """

        return login.split("@")


class Chat:
    """
    A class representing a chat session between users.

    This class handles the initialization of a chat session, managing encryption and user details.
    It can operate in two modes: encrypted and plain. In encrypted mode, it uses RSA encryption
    for securing the chat. In plain mode, it simply stores the given secret as is for use in api endpoints.

    Attributes:
        ra: An instance of RSAAdapter for handling RSA encryption and decryption.
        aes: The AES key used for chat encryption, decrypted or plain based on the mode.
        init_user_login: The login of the initiating user.
        dst_user_login: The login of the destination user.
        cid: Chat identifier, optional.
    """

    def __init__(self, secret, aes, u_init, u_dest, cid=None, plain=False):
        """
        Initialize a Chat instance.

        In encrypted mode, 'u_init' and 'u_dest' should be User objects with RSA keys. In plain mode,
        they should be strings representing user logins. The AES key is decrypted in encrypted mode.

        Args:
            secret: The secret key for RSA encryption/decryption.
            aes: The AES key, either encrypted or plain.
            u_init: The initiating user's object or login, depending on the mode.
            u_dest: The destination user's object or login, depending on the mode.
            cid: An identifier for the chat session. Defaults to None.
            plain: A flag to indicate if the chat is in plain mode (not encrypted). Defaults to False.
        """

        if not plain:
            self.ra = RSAAdapter(
                secret=secret,
                pub_pem=u_init.s_pub_k,
                p_pem=u_init.s_p_k
            )

            self.aes = self.ra.decrypt(aes)
            self.init_user_login = u_init.get_login()
            self.dst_user_login = u_dest.get_login()
        else:
            self.aes = secret
            self.init_user_login = u_init
            self.dst_user_login = u_dest

        self.cid = cid

    def to_mongo(self):
        """
        Prepares the chat data for storage in MongoDB.

        Returns:
            A dictionary representing the chat data suitable for MongoDB storage.
        """

        return {
            "aes": self.aes,
            "init_login": self.init_user_login,
            "dst_login": self.dst_user_login,
        }

    def safe_serialize(self, sp):
        """
        Safely serializes the chat object for secure storage and transmission.

        This method prepares the chat data for secure storage or transmission by encrypting the AES key.
        It also ensures all data is in the correct format, such as converting bytes to strings.

        Args:
            sp: An instance of a service provider used for encryption.

        Returns:
            A dictionary representing the chat data, with the AES key encrypted and all data properly formatted.
        """

        model = self.to_mongo()
        if isinstance(model["aes"], (bytes, bytearray)):
            model["aes"] = model["aes"].decode('utf-8')

        model["aes"] = sp.encrypt(model["aes"])
        model["cid"] = str(self.cid)
        return model


class Message:
    """
    A class representing a message within a chat.

    This class encapsulates the details of a message, including its content, author, timestamp, and read status.
    It provides methods to prepare the message for storage and to serialize it for transmission.

    Attributes:
        mid: Message identifier, optional.
        msg: The content of the message.
        chat: The chat object to which the message belongs.
        author_id: The identifier of the message author.
        timestamp: The timestamp of the message.
        read: A flag indicating whether the message has been read.
    """

    def __init__(self, chat, author_id, msg, timestamp, mid=None):
        """
        Initialize a Message instance.

        Args:
            chat: The chat object to which the message belongs.
            author_id: The identifier of the message author.
            msg: The content of the message.
            timestamp: The timestamp of the message.
            mid: An identifier for the message. Defaults to None.
        """

        self.mid = mid
        self.msg = msg
        self.chat = chat
        self.author_id = author_id
        self.timestamp = timestamp
        self.read = False

    def to_mongo(self):
        """
        Prepares the message data for storage in MongoDB.

        Returns:
            A dictionary representing the message data suitable for MongoDB storage.
        """

        return {
            "msg": self.msg,
            "chat_id": str(self.chat.cid),
            "author_id": self.author_id,
            "read": self.read,
            "timestamp": self.timestamp,
        }

    def serialize(self):
        """
        Serializes the message for transmission.

        Returns:
            A dictionary representing the message data suitable for transmission.
        """

        return {
            "msg": self.msg,
            "author_id": self.author_id,
            "timestamp": self.timestamp,
        }
