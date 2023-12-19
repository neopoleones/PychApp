import unittest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64

from cli.encryption_utils import RSAAdapter
from cli.encryption_utils import aes_decrypt, aes_encrypt


class TestRSAAdapter(unittest.TestCase):

    def setUp(self):
        self.adapter = RSAAdapter(secret="mysecret")

    def test_encrypt_decrypt(self):
        message = "Hello, World!"
        encrypted = self.adapter.encrypt(message)
        decrypted = self.adapter.decrypt(encrypted)
        self.assertEqual(decrypted.decode(), message)

    def test_gen_key_pair(self):
        pub_pem, p_pem = self.adapter.get_pair()
        pub_key = serialization.load_pem_public_key(pub_pem)
        private_key = serialization.load_pem_private_key(
            p_pem, password=b"mysecret")
        self.assertIsInstance(pub_key, rsa.RSAPublicKey)
        self.assertIsInstance(private_key, rsa.RSAPrivateKey)


class TestAES(unittest.TestCase):
    def test_aes(self):
        message = "Hello, World!"
        key = "A" * 16
        encrypted = aes_encrypt(message, base64.b64encode(key.encode()))
        decrypted = aes_decrypt(encrypted, key)
        self.assertEqual(decrypted, message)


if __name__ == '__main__':
    unittest.main()
