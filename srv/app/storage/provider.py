from cryptography.fernet import Fernet
from Crypto.Cipher import AES
import base64, os


class FernetAdapter:
    def __init__(self, secret):
        if len(secret) == 0:
            raise Exception("Incorrect secret provided")
        self.provider = Fernet(secret)

    def encrypt(self, message):
        return self.provider.encrypt(message)

    def decrypt(self, message):
        return self.provider.decrypt(message)


# Naive wrapper for https://gist.github.com/syedrakib/d71c463fc61852b8d366
class AesAdapter:
    def __init__(self, enc_secret=None, pad='{'):
        if not enc_secret:
            enc_secret = self.generate_secret(kl=16)

        self.enc_secret_key = enc_secret
        self.pad = pad

    def encrypt(self, message):
        secret_key = base64.b64decode(self.enc_secret_key)
        cipher = AES.new(secret_key)

        padded_private_msg = message + (self.pad * ((16-len(message)) % 16))
        encrypted_msg = cipher.encrypt(padded_private_msg)

        return base64.b64encode(encrypted_msg)

    def decrypt(self, message):
        secret_key = base64.b64decode(self.enc_secret_key)
        encrypted_msg = base64.b64decode(message)
        cipher = AES.new(secret_key)

        decrypted_msg = cipher.decrypt(encrypted_msg)
        return decrypted_msg.rstrip(self.pad)

    def get_enc_secret(self):
        return self.enc_secret_key

    @staticmethod
    def generate_secret(kl=24):
        secret_key = os.urandom(kl)
        return base64.b64encode(secret_key)


from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os

# Предполагаемый пароль
password = b"example password"

# Генерация соли
salt = os.urandom(16)

# Создание ключа из пароля
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=100000,
    backend=default_backend()
)
key = kdf.derive(password)

# Генерация асимметричной пары ключей
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)
public_key = private_key.public_key()

# Сериализация ключей
private_key_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

public_key_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)
