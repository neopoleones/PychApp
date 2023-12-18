import requests
import json
from encryption_utils import generate_aes_key, encrypt_message, RSAAdapter
import websockets
from time import time
import base64


class ChatProtocol:
    def __init__(self, config, auth, s_pub_k) -> None:
        self.config = config
        self.auth = auth
        self.s_pub_k = s_pub_k

    def new_chat(self, interlocutor):
        url = f"http://{self.config['server_host']}:{self.config['server_port']}/api/chat/new"

        username, hostname = interlocutor.split('@')

        aes_key = generate_aes_key()

        rsa = RSAAdapter(pub_pem=self.s_pub_k.encode())

        print(f"{self.s_pub_k=}")

        payload = json.dumps({
            "dest_username": username,
            "dest_hostname": hostname,
            "enc_aes": rsa.encrypt(("A"*16)),
        })

        headers = {
            'Auth': self.auth,
            'Content-Type': 'application/json'
        }
    
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        print(data)
        if response.status_code == 200 and data['status'] == 'ok':
            return base64.b64encode(aes_key).decode('utf-8')
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

    async def init_chat(self, dest_login):
        websocket_url = f"ws://{self.config['server_host']}:{self.config['ws_port']}/ws"
        async with websockets.connect(websocket_url) as websocket:
            print(f"init_chat")
            await websocket.send(json.dumps({
                'token': self.auth,
                'dest_login': dest_login,
            }))

    async def send_message(self, message):
        websocket_url = f"ws://{self.config['server_host']}:{self.config['ws_port']}/ws"
        async with websockets.connect(websocket_url) as websocket:
            print(f"send_message")
            await websocket.send(json.dumps({
                'msg': message,
                'timestamp': time(),
            }))

    async def receive_messages(self):
        websocket_url = f"ws://{self.config['server_host']}:{self.config['ws_port']}/ws"
        async with websockets.connect(websocket_url) as websocket:
            print(f"receive_messages")
            while True:
                message = await websocket.recv()
                return json.loads(message)['msg']
