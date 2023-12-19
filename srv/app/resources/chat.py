import falcon
from app.storage.model import Chat
from app.storage.provider import RSAAdapter
from app.storage.mongo import EntityNotFoundException
from app.resources.middleware import UserByTokenMiddleware


class NewResource:
    def __init__(self, storage, secret):
        self.storage = storage
        self.secret = secret

    @falcon.before(UserByTokenMiddleware.check_user)
    def on_post(self, req, resp):
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
