import json
import threading
import time
from app.storage.model import User, Chat, Message
from wsocket import WSocketApp, WebSocketError, run


class ChatProtocol:
    """
    Chat webSocket protocol for handling chat communication.

    This class defines a WebSocket protocol for handling chat communication. It includes methods for parsing messages,
    authentication, sending and receiving messages, serving new messages, and continuous communication.

    Attributes:
        sp: The security provider for encryption and decryption.
        ws: The WebSocket connection.
        storage: The storage provider for storing chat messages and data.
        chat:   The chat where users communicate.
        author: The user who connected to the chat.
    """

    chat: Chat
    author: User

    def __init__(self, sp, ws, storage):
        """
        Initialize the ChatProtocol.

        Args:
            sp: The security provider for encryption and decryption.
            ws: The WebSocket connection.
            storage: The storage provider (mongodb).
        """

        self.ws = ws
        self.sp = sp
        self.storage = storage

    @staticmethod
    def parse_message(msg):
        """
        Parse a JSON message

        Args:
            msg: The JSON message to parse.

        Returns:
            The parsed JSON message as a dictionary.
        """

        try:
            msg = json.loads(msg)
        except json.JSONDecodeError:
            return {"error": "failed to parse json"}
        return msg

    def get_msg(self):
        """
        Receive a message from the WebSocket connection.

        Returns:
            The parsed JSON message received from the WebSocket.
        """

        msg = self.ws.receive()
        if msg is None:
            return {"error": "empty message"}

        return self.parse_message(msg)

    def send_msg(self, msg):
        """
        Send a JSON message through the WebSocket connection.

        Args:
            msg: The JSON message to send.
        """

        self.ws.send(json.dumps(msg))

    def auth_by_frame(self):
        """
        Authenticate the user by processing an authentication frame.

        Returns:
            The authentication result, including the status and user login.
        """

        msg = self.get_msg()
        if "error" in msg:
            return msg

        try:
            tok, login = msg["token"], msg["dest_login"]
            uid = self.sp.decrypt(tok)
            src_user = self.storage.get_user_by_uid(uid.decode())
        except Exception:
            return {"error": "incorrect auth frame"}

        ld = User.parse_login(login)
        if len(ld) != 2:
            return {"error": "invalid destination login"}
        username, hostname = ld

        dst_user = self.storage.get_users_by_filter(
            name=username, hostname=hostname, strict=True
        )
        if len(dst_user) != 1:
            return {"error": "destination not found"}
        dst_user = dst_user[0]

        try:
            chat = self.storage.get_chat(src_user, dst_user)
        except Exception:
            return {"error": "create chat before subscribing"}

        self.chat = chat
        self.author = src_user

        return {"status": "ok", "login": src_user.get_login()}

    def serve_new_messages(self):
        """
        Serve new messages received from the WebSocket connection.

        This method continuously listens for new messages, adds them to the storage, and handles any errors.
        """

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

            except Exception as e:
                print(e)

    def communicate(self):
        """
        Continuously communicate with the WebSocket connection.

        This method continuously sends and receives messages between the users in the chat.
        """

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
            except Exception as e:
                print(e)


def run_wsapp(cfg, logger, sp, storage):
    """
    Run the WebSocket application for pychapp.

    This function runs the WebSocket application for pychapp. It handles WebSocket connections and authentication,
    and starts a thread to serve new messages.

    Args:
        cfg: The configuration object containing application settings.
        logger: The application logger.
        sp: The security provider for WebSocket communication.
        storage: The PychStorage instance for data storage.
    """

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

    run(app, host="0.0.0.0")
