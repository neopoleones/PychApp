import requests
import json
from encryption_utils import generate_aes_key, encrypt_message
import websockets
from time import now


class ChatProtocol:
    def __init__(self, config, auth, s_pub_k) -> None:
        self.config = config
        self.auth = auth
        self.s_pub_k = s_pub_k

    def new_chat(self, interlocutor, aes_key):
        url = f"http://{self.config['server_host']}:{self.config['server_port']}/api/chat/new"

        username, hostname = interlocutor.split('@')

        payload = json.dumps({
            "dest_username": username,
            "dest_hostname": hostname,
            "enc_aes": encrypt_message(generate_aes_key(), self.s_pub_k),
        })

        headers = {
            'Auth': self.auth,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        if response.status_code == 200 and data['status'] == 'ok':
            return data['cid']
        return False

    def list_chats(self):
        url = f"http://{self.config['server_host']}:{self.config['server_port']}/api/chat/list"

        headers = {
            'Auth': self.auth,
        }

        response = requests.request("GET", url, headers=headers)

        data = response.json()
        if response.status_code == 200 and data['status'] == 'ok':
            return data['chats']
        return False

    async def send_message(self, message):
        websocket_url = f"ws://{self.config['server_host']}:{self.config['ws_port']}/ws"
        async with websockets.connect(websocket_url) as websocket:
            await websocket.send(json.dumps({
                'msg': message,
                'timestamp': now(),
            }))

    async def receive_messages(self):
        websocket_url = f"ws://{self.config['server_host']}:{self.config['ws_port']}/ws"
        async with websockets.connect(websocket_url) as websocket:
            while True:
                message = await websocket.recv()
                return json.loads(message)['msg']
