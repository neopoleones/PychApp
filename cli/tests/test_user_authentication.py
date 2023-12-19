import unittest
import requests
from unittest.mock import patch
from cli.user_authentication import UserAuthentication


class TestUserAuthentication(unittest.TestCase):

    def setUp(self):
        self.config = {
            "server_host": "localhost",
            "server_port": 8080
        }
        self.auth = UserAuthentication(self.config)

    def test_is_server_available(self):
        with patch.object(requests, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"status": "ok"}
            result = self.auth.is_server_available()
            self.assertTrue(result)

    def test_register(self):
        with patch.object(requests, 'request') as mock_request:
            mock_request.return_value.status_code = 200
            private_key, public_key = self.auth.register("test_user", "test_host", "test_password")
            self.assertIsNotNone(private_key)
            self.assertIsNotNone(public_key)

            mock_request.return_value.status_code = 400
            result = self.auth.register("test_user", "test_host", "test_password")
            self.assertFalse(result)

    def test_create_users_table(self):
        self.auth.create_users_table()
        # Assert that the users table is created in the database

    def test_login(self):
        with patch.object(requests, 'request') as mock_request:
            mock_request.return_value.status_code = 200
            mock_request.return_value.json.return_value = {"status": "ok", "s_pub_k": "test_public_key"}
            auth_token, server_public_key = self.auth.login("test_user", "test_host", "test_password")
            self.assertIsNotNone(auth_token)
            self.assertIsNotNone(server_public_key)

            mock_request.return_value.status_code = 401
            result = self.auth.login("test_user", "test_host", "test_password")
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()