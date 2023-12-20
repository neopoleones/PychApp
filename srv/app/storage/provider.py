import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes


class FernetAdapter:
    """
    FernetAdapter provides encryption and decryption methods using the Fernet symmetric encryption
    algorithm.

    """

    def __init__(self, secret):
        """
        Initialize a FernetAdapter with the provided secret.

        Args:
            secret: The secret key used for encryption and decryption.

        Raises:
            Exception: If an empty secret is provided.
        """

        if len(secret) == 0:
            raise Exception("Incorrect secret provided")
        self.provider = Fernet(secret)

    def encrypt(self, message):
        """
        Encrypt a message using Fernet encryption.

        Args:
            message: The message to be encrypted.

        Returns:
            The encrypted message.
        """

        return self.provider.encrypt(message)

    def decrypt(self, message):
        """
        Decrypt an encrypted message using Fernet decryption.

        Args:
            message: The encrypted message to be decrypted.

        Returns:
            The decrypted message.
        """

        return self.provider.decrypt(message)


class RSAAdapter:
    """
    RSAAdapter provides encryption and decryption methods using the RSA asymmetric encryption algorithm.

    Attributes:
        secret: The password for encrypting the private key.
    """

    def __init__(self, secret="", pub_pem=None, p_pem=None):
        """
        Initialize an RSAAdapter for encryption and decryption.

        If neither pub_pem nor p_pem is provided, a new key pair is generated using the secret.
        If pub_pem and p_pem are provided, they are used for encryption and decryption operations.

        Args:
            secret: The password for encrypting the private key (optional).
            pub_pem: The public key in PEM format (optional).
            p_pem: The private key in PEM format (optional).
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
        Encrypt a message using RSA encryption.

        Args:
            message: The message to be encrypted.

        Returns:
            The encrypted message in base64-encoded string format.
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
        Decrypt an encrypted message using RSA decryption.

        Args:
            message: The base64-encoded encrypted message.

        Returns:
            The decrypted message as a string.
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
        Generate an RSA key pair.

        This method generates an RSA key pair and returns both the public and private keys as bytes.

        Returns:
             pub_pem, p_pem: public key (as bytes) and private key (as bytes).
        """

        p_k = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        es = serialization.BestAvailableEncryption(self.secret.encode())
        p_pem = p_k.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=es
        )

        pub_key = p_k.public_key()
        pub_pem = pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return pub_pem, p_pem

    def get_pair(self):
        """
        Get the public-private key pair.

        This method returns the current public and private key pair as bytes.

        Returns:
            pub_pem, p_pem: public key (as bytes) and private key (as bytes).
        """

        return self.pub_pem, self.p_pem
