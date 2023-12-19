import pytest
from srv.app.storage.provider import RSAAdapter

class TestRSAAdapter:

    def test_init_with_no_args_raises_exception(self):
        with pytest.raises(Exception):
            RSAAdapter()

    def test_init_with_secret_generates_keys(self):
        adapter = RSAAdapter(secret="super_secret")

        assert adapter.pub_pem is not None
        assert adapter.p_pem is not None

    def test_init_with_keys_does_not_generate_new_keys(self):
        pub_pem = "dummy_public_key"
        p_pem = "dummy_private_key"

        adapter = RSAAdapter(pub_pem=pub_pem, p_pem=p_pem)

        assert adapter.pub_pem == pub_pem
        assert adapter.p_pem == p_pem

    def test_encrypt_without_pub_key_raises_exception(self):
        adapter = RSAAdapter(p_pem="dummy_private_key")
        with pytest.raises(Exception):
            adapter.encrypt("message")

    def test_decrypt_without_priv_key_raises_exception(self):
        adapter = RSAAdapter(pub_pem="dummy_public_key")
        with pytest.raises(Exception):
            adapter.decrypt("message")

    def test_encrypt_decrypt(self):
        adapter = RSAAdapter(secret="mysecret")
        message = "Hello, World!"

        encrypted_message = adapter.encrypt(message)
        decrypted_message = adapter.decrypt(encrypted_message)

        assert message == decrypted_message.decode()
