from cryptography.fernet import Fernet

key = Fernet.generate_key()  # This key should be stored and managed securely

def encrypt_message(message):
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(message.encode())

def decrypt_message(encrypted_message):
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(encrypted_message).decode()
