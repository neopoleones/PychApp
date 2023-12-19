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


def generate_aes_key():
    return "".join([chr(random.randint(32, 126)) for i in range(16)])

def generate_key_pair():
    # generate pair of keys
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key, public_key

def rsa_encrypt(message, public_key: str | bytes) -> str:
    # return encrypted message in base64
    key = RSA.import_key(public_key)
    cipher = PKCS1_OAEP.new(key, hashAlgo=SHA256)
    encrypted_message = cipher.encrypt(message)
    return base64.b64encode(encrypted_message).decode("utf-8")

def rsa_decrypt(message, private_key) -> str:
    # return decrypted message
    key = RSA.import_key(private_key)
    cipher = PKCS1_OAEP.new(key, hashAlgo=SHA256)
    decrypted_message = cipher.decrypt(base64.b64decode(message))
    return decrypted_message.decode()

def aes_encrypt(message, key):
    cipher = AES.new(base64.b64decode(key), AES.MODE_ECB)
    ct_bytes = cipher.encrypt(pad(message.encode(), AES.block_size))
    ciphertext = ct_bytes
    return base64.b64encode(ciphertext).decode('utf-8')

def aes_decrypt(ciphertext, key):
    cipher = AES.new(key.encode(), AES.MODE_ECB)
    pt = unpad(cipher.decrypt(base64.b64decode(ciphertext.encode())), AES.block_size)
    return pt.decode('utf-8')

class RSAAdapter:
    def __init__(self, secret="", pub_pem=None, p_pem=None):
        self.secret = secret

        if pub_pem is None and p_pem is None:
            if len(secret) == 0:
                raise Exception("incorrect secret is provided")
            self.pub_pem, self.p_pem = self.gen_key_pair()
        else:
            self.pub_pem, self.p_pem = pub_pem, p_pem

    def encrypt(self, message):
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
        p_k = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        p_pem = p_k.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(self.secret.encode())
        )

        pub_key = p_k.public_key()
        pub_pem = pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return pub_pem, p_pem

    def get_pair(self):
        return self.pub_pem, self.p_pem
