from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64
import os


def generate_aes_key():
    # generate a random 32-byte key
    return os.urandom(32)

# generate pair of keys
def generate_key_pair():
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key, public_key

def encrypt_message(message, public_key: str | bytes) -> str:
    # return encrypted message in base64
    key = RSA.import_key(public_key)
    cipher = PKCS1_OAEP.new(key)
    encrypted_message = cipher.encrypt(message)
    return base64.b64encode(encrypted_message).decode("utf-8")