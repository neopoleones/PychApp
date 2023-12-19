import unittest
from unittest.mock import patch
from cli.message_utils import ChatProtocol
import base64

class TestChatProtocol(unittest.TestCase):

    def setUp(self):
        self.config = {
            'server_host': 'localhost',
            'server_port': 8080
        }
        self.auth = 'my_auth_token'
        self.s_pub_k = 'my_public_key'

        self.protocol = ChatProtocol(self.config, self.auth, self.s_pub_k)

    def test_new_chat_success(self):
        interlocutor = 'user@example.com'
        aes_key = 'my_aes_key'
        chat_id = '12345'

        expected_payload = {
            "dest_username": 'user',
            "dest_hostname": 'example.com',
            "enc_aes": 'encrypted_aes_key',
        }

        expected_response = {
            'status': 'ok',
            'cid': chat_id
        }

        with patch('cli.message_utils.generate_aes_key', return_value=aes_key):
            with patch('cli.message_utils.RSAAdapter') as mock_rsa_adapter:
                mock_rsa_adapter.return_value.encrypt.return_value = 'encrypted_aes_key'

                with patch('requests.request') as mock_request:
                    mock_request.return_value.status_code = 200
                    mock_request.return_value.json.return_value = expected_response

                    result = self.protocol.new_chat(interlocutor)

                    mock_request.assert_called_once_with("POST", f"http://{self.config['server_host']}:{self.config['server_port']}/api/chat/new", headers={'Auth': self.auth, 'Content-Type': 'application/json'}, data='{"dest_username": "user", "dest_hostname": "example.com", "enc_aes": "encrypted_aes_key"}')

                    self.assertEqual(result, (base64.b64encode(aes_key.encode()).decode(), chat_id))

    def test_list_chats_success(self):
        expected_response = {
            'status': 'ok',
            'chats': ['chat1', 'chat2']
        }

        with patch('requests.request') as mock_request:
            mock_request.return_value.status_code = 200
            mock_request.return_value.json.return_value = expected_response

            result = self.protocol.list_chats()

            mock_request.assert_called_once_with("GET", f"http://{self.config['server_host']}:{self.config['server_port']}/api/chat/list", headers={'Auth': self.auth})

            self.assertEqual(result, expected_response['chats'])

    def test_list_chats_failure(self):
        expected_response = {
            'status': 'error',
            'message': 'Failed to retrieve chats'
        }

        with patch('requests.request') as mock_request:
            mock_request.return_value.status_code = 400
            mock_request.return_value.json.return_value = expected_response

            result = self.protocol.list_chats()

            mock_request.assert_called_once_with("GET", f"http://{self.config['server_host']}:{self.config['server_port']}/api/chat/list", headers={'Auth': self.auth})

            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()