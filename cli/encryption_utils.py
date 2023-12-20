from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Hash import SHA256
import base64
import random

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes


import random


def generate_aes_key():
    """
    Generates a random AES key.

    Returns:
        str: The generated AES key.
    """
    return "".join([chr(random.randint(32, 126)) for i in range(16)])


def generate_key_pair():
    """
    Generates a pair of RSA keys.

    Returns:
        tuple: A tuple containing the private key and the public key.
    """
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key, public_key


def rsa_encrypt(message, public_key):
    """
    Encrypts a message using RSA encryption algorithm.

    Args:
        message (bytes): The message to be encrypted.
        public_key (str): The public key used for encryption.

    Returns:
        str: The encrypted message encoded in base64.

    """
    key = RSA.import_key(public_key)
    cipher = PKCS1_OAEP.new(key, hashAlgo=SHA256)
    encrypted_message = cipher.encrypt(message)
    return base64.b64encode(encrypted_message).decode("utf-8")


def rsa_decrypt(message, private_key) -> bytes:
    """
    Decrypts the given RSA encrypted message using the provided private key.

    Args:
        message (str): The RSA encrypted message to decrypt.
        private_key (str): The private key used for decryption.

    Returns:
        str: The decrypted message (bytes, plain).

    """
    key = RSA.import_key(private_key)
    cipher = PKCS1_OAEP.new(key, hashAlgo=SHA256)
    return cipher.decrypt(base64.b64decode(message))


def aes_encrypt(message: bytes, key: bytes) -> bytes:
    """
    Encrypts the given message using AES encryption algorithm.

    Args:
        message (str): The message to be encrypted.
        key (bytes): The encryption key, plain bytes.

    Returns:
        str: The encrypted ciphertext encoded in bytes (not base64).
    """

    cipher = AES.new(key, AES.MODE_ECB)

    ct_bytes = cipher.encrypt(pad(message, AES.block_size))
    return ct_bytes


def aes_decrypt(ciphertext: bytes, key: bytes) -> bytes:
    """
    Decrypts the given ciphertext using AES encryption algorithm.

    Args:
        ciphertext (bytes): The encrypted ciphertext to be decrypted, bytes (not base64!).
        key (str): The encryption key used for decryption.

    Returns:
        str: The decrypted plaintext.
    """
    cipher = AES.new(key, AES.MODE_ECB)
    pt = unpad(
        cipher.decrypt(
            ciphertext),
        AES.block_size)
    return pt


class RSAAdapter:
    """
    A class used for RSA encryption and decryption.

    Attributes:
        secret (str): The secret used for encryption and decryption.
        pub_pem (bytes): The public key in PEM format.
        p_pem (bytes): The private key in PEM format.
    """

    def __init__(self, secret="", pub_pem=None, p_pem=None):
        """
        Initializes an instance of RSAAdapter.

        Args:
            secret (str): The secret used for encryption and decryption. Default is an empty string.
            pub_pem (bytes): The public key in PEM format. Default is None.
            p_pem (bytes): The private key in PEM format. Default is None.

        Raises:
            Exception: If no public key or private key is provided.
        """
        self.secret = secret

        if pub_pem is None and p_pem is None:
            if len(secret) == 0:
                raise Exception("incorrect secret is provided")
            self.pub_pem, self.p_pem = self.gen_key_pair()
        else:
            self.pub_pem, self.p_pem = pub_pem, p_pem

    def encrypt(self, message):
        """
        Encrypts the given message using the public key.

        Args:
            message (str): The message to be encrypted.

        Returns:
            str: The encrypted message in base64-encoded format.

        Raises:
            Exception: If no public key is provided.
        """
        if self.pub_pem is None:
            raise Exception("No pub_k provided")

        pub_k = serialization.load_pem_public_key(self.pub_pem)
        encrypted = pub_k.encrypt(
            message.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode('utf-8')

    def decrypt(self, message):
        """
        Decrypts the given message using the private key.

        Args:
            message (str): The encrypted message in base64-encoded format.

        Returns:
            bytes: The decrypted message.

        Raises:
            Exception: If no private key or secret is provided.
        """
        if self.p_pem is None or self.secret is None:
            raise Exception("No pub_k provided")
        message = base64.b64decode(message)

        # Load the private key
        private_key = serialization.load_pem_private_key(
            self.p_pem,
            password=self.secret.encode()
        )

        # Decrypt the message
        d_message = private_key.decrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return d_message

    def gen_key_pair(self):
        """
        Generates a new RSA key pair.

        Returns:
            tuple: A tuple containing the public key and private key in PEM format.
        """
        p_k = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        p_pem = p_k.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(
                self.secret.encode()))

        pub_key = p_k.public_key()
        pub_pem = pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return pub_pem, p_pem

    def get_pair(self):
        """
        Returns the public key and private key pair.

        Returns:
            tuple: A tuple containing the public key and private key in PEM format.
        """
        return self.pub_pem, self.p_pem
