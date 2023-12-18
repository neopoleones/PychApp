import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes


class FernetAdapter:
    def __init__(self, secret):
        if len(secret) == 0:
            raise Exception("Incorrect secret provided")
        self.provider = Fernet(secret)

    def encrypt(self, message):
        return self.provider.encrypt(message)

    def decrypt(self, message):
        return self.provider.decrypt(message)


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


if __name__ == "__main__":
    k  = b"-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1Zw9CElIHiID5mV1gcHu\n5ddh8AItgp3iSGHbjsjhd0W1lI/tZXCtyDFxDwK94KAPC7NHg4uYnEtFlLRYva6U\nfYynLhHNMXPaphiZr4gGspDxwCsQrEqlMByhMa2LXtqYifkK37tey/aA5MJdMBJC\n7YYTpbqSHKMAplzuiSaCcmRodD90eKdd4Dcbe6VubpRCadQ0vZyoIpEZuGv2ZYnz\n+nuN0ONctnnosaL2rXMb/mAAb76WXT+EEf5tXwjMag7XzaCmNUCbX+SWLakImyhB\n66m/JJG2xZ/hRQf8/3g8TKwU5oS7TpiUXe1gmUQcBaEoHF9/FMSXK0mX1tpfqybT\nzwIDAQAB\n-----END PUBLIC KEY-----\n"
    ra = RSAAdapter(pub_pem=k)
    res = ra.encrypt("abaca")
    print(res)
#	key = input('secret: ')
#	ra = RSAAdapter(secret=key)
#	pub, priv = ra.gen_key_pair()
#	print(pub)
#	print(priv)
