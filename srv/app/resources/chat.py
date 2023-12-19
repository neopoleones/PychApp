import falcon
from app.storage.model import Chat
from app.storage.provider import RSAAdapter
from app.storage.mongo import EntityNotFoundException
from app.resources.middleware import UserByTokenMiddleware


class NewResource:
    """
    A resource for handling new chat creation in a Falcon web application.

    This class is responsible for handling POST requests to create a new chat
    between users.

    Attributes:
        storage: The storage backend used for retrieving and storing user and
        chat information.
        secret: A secret key used for chat-related operations.

    Methods:
        on_post(req, resp): Handles the POST request to create a new chat.
    """

    def __init__(self, storage, secret):
        self.storage = storage
        self.secret = secret

    @falcon.before(UserByTokenMiddleware.check_user)
    def on_post(self, req, resp):
        """
        Handles POST requests to create a new chat between users.

        The method extracts the destination user's username and hostname, and an encrypted AES key
        from the request. It then checks if a chat already exists between the initiator and the
        destination user. If not, it creates a new chat and adds it to the storage.

        Args:
            req: The request object, containing details about the HTTP request.
            resp: The response object, used to return data back to the client.

        Raises:
            falcon.HTTPBadRequest: If required fields are missing in the request or if the initiator
                                   tries to create a chat with themselves.
            falcon.HTTPNotFound: If the specified destination user is not found.
            falcon.HTTPUnauthorized: If there is an issue with the provided AES key.
        """

        try:
            dest_username = req.media["dest_username"]
            dest_hostname = req.media["dest_hostname"]
            enc_aes = req.media["enc_aes"]

        except Exception:
            raise falcon.HTTPBadRequest(title="not all fields specified")

        dest_user = self.storage.get_users_by_filter(
            name=dest_username, hostname=dest_hostname, strict=True
        )
        if len(dest_user) != 1:
            raise falcon.HTTPNotFound(title="user not found")

        dest_user = dest_user[0]
        init_user = req.context['auth']['user']

        if dest_user.uid == init_user.uid:
            raise falcon.HTTPBadRequest(title="you can't chat yourself")
        try:
            _ = self.storage.get_chat(init_user, dest_user)

            # Чат есть, выводим ошибку
            raise falcon.HTTPBadRequest(
                title="can't create second chat with user"
            )

        except EntityNotFoundException:

            # Чата нет, создаем новый
            try:
                new_chat = Chat(self.secret, enc_aes, init_user, dest_user)
            except ValueError:
                raise falcon.HTTPUnauthorized(title="bad aes")

            self.storage.add_chat(new_chat)

            resp.status = falcon.HTTP_200
            resp.media = {
                "status": "ok",
                "cid": str(new_chat.cid),
            }


class ListResource:
    def __init__(self, storage):
        self.storage = storage

    @falcon.before(UserByTokenMiddleware.check_user)
    def on_get(self, req, resp):
        init_user = req.context['auth']['user']
        sp = RSAAdapter(pub_pem=init_user.u_pub_k.encode())

        chats = self.storage.get_chats(init_user)

        resp.status = falcon.HTTP_200
        resp.media = {
            "status": "ok",
            "chats":  [c.safe_serialize(sp) for c in chats],
        }
