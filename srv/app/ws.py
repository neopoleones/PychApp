import json
import threading
import time
from app.storage.model import User, Chat, Message
from wsocket import WSocketApp, WebSocketError, run

class ChatProtocol:
    chat: Chat
    author: User

    def __init__(self, sp, ws, storage):
        self.ws = ws
        self.sp = sp
        self.storage = storage

    @staticmethod
    def parse_message(msg):
        try:
            msg = json.loads(msg)
        except json.JSONDecodeError:
            return {"error": "failed to parse json"}
        return msg

    def get_msg(self):
        msg = self.ws.receive()
        if msg is None:
            return {"error": "empty message"}

        return self.parse_message(msg)

    def send_msg(self, msg):
        self.ws.send(json.dumps(msg))

    def auth_by_frame(self):
        msg = self.get_msg()
        if "error" in msg:
            return msg

        # Проверим наличие token (и валидность оного), а также dest_login
        try:
            tok, login = msg["token"], msg["dest_login"]
            uid = self.sp.decrypt(tok)
            src_user = self.storage.get_user_by_uid(uid.decode())
        except Exception:
            return {"error": "incorrect auth frame"}

        # А теперь проверим валидность dest_login
        ld = User.parse_login(login)
        if len(ld) != 2:
            return {"error": "invalid destination login"}
        username, hostname = ld

        dst_user = self.storage.get_users_by_filter(name=username, hostname=hostname, strict=True)
        if len(dst_user) != 1:
            return {"error": "destination not found"}
        dst_user = dst_user[0]

        # Проверим наличие переписки
        try:
            chat = self.storage.get_chat(src_user, dst_user)
        except:
            return {"error": "create chat before subscribing"}

        self.chat = chat
        self.author = src_user

        return {"status": "ok", "login": src_user.get_login()}

    def serve_new_messages(self):
        while True:
            try:
                msg = self.get_msg()
                if "error" in msg:
                    self.send_msg(msg)
                    continue

                self.storage.add_message(Message(
                    self.chat,
                    str(self.author.uid),
                    msg["msg"],
                    msg["timestamp"]
                ))

            except KeyError:
                self.send_msg({"error": "msg or timestamp not specified"})

            except WebSocketError:
                break

    def communicate(self):
        while True:
            try:
                messages = self.storage.get_messages(self.chat)
                for msg in messages:
                    if msg.author_id != str(self.author.uid):
                        self.send_msg(msg.serialize())

                        self.storage.set_message_read(msg)
                time.sleep(1)
            except WebSocketError:
                break


def run_wsapp(cfg, logger, sp, storage):
    app = WSocketApp()

    @app.route("/ws")
    def handle_websocket(environ, start_response):
        ws = environ.get("wsgi.websocket")
        if not ws:
            start_response()
            return cfg.env

        # формат {"token": tok, "dest_login": login}
        # пока ошибки - запрашиваем авторизацию
        ws_chat = ChatProtocol(sp, ws, storage)
        msg = ws_chat.auth_by_frame()
        while "error" in msg:
            ws_chat.send_msg(msg)
            msg = ws_chat.auth_by_frame()

        ws_chat.send_msg(msg)

        th = threading.Thread(target=ws_chat.serve_new_messages, args=())
        th.start()
        ws_chat.communicate()

    run(app)
