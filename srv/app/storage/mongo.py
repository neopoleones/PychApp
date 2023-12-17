import falcon
import pymongo
from .model import User, Chat
from bson.objectid import ObjectId


class ValidationFailedException(Exception):
    @staticmethod
    def handle(ex, req, resp, params):
        # TODO: Log the error, clean up, etc. before raising
        raise falcon.HTTPBadRequest("validation failed")


class EntityNotFoundException(Exception):
    @staticmethod
    def handle(ex, req, resp, params):
        # TODO: Log the error, clean up, etc. before raising
        raise falcon.HTTPNotFound(title="user not found")


class DuplicateEntryException(Exception):
    @staticmethod
    def handle(ex, req, resp, params):
        # TODO: Log the error, clean up, etc. before raising
        raise falcon.HTTPBadRequest(title="user already registered")


class PychStorage:
    def __init__(self, cfg, rp):
        self.rp = rp
        self.con = pymongo.MongoClient(cfg.mongo['con_link'])
        self.db = self.con[cfg.mongo['db']]

        # Проверяем, что индекс уникален
        self.db["users"].create_index({"name": 1}, unique=True)

    def add_chat(self, chat):
        chats_collection = self.db["chats"]

        inserted = chats_collection.insert_one(chat.to_mongo())
        chat.cid = inserted.inserted_id

    def get_chat(self, src_user, dst_user):
        chats_collection = self.db["chats"]

        query = {
            "init_login": src_user.get_login(),
            "dst_login": dst_user.get_login(),
        }

        query_dest = {
            "init_login": dst_user.get_login(),
            "dst_login": src_user.get_login(),
        }

        doc = chats_collection.find_one({"$or": [
            query, query_dest
        ]})

        if doc is None:
            raise EntityNotFoundException()

        return Chat(
            doc.get("aes"), b"", doc.get("init_login"),
            doc.get("dst_login"), plain=True,
            cid=doc.get("_id")
        )

    def get_chats(self, src_user):
        chats_collection = self.db["chats"]
        query = {
            "init_login": src_user.get_login()
        }

        query_dest = {
            "init_login": {
                "$regex": ".*"
            },
            "dst_login": src_user.get_login()
        }

        docs = chats_collection.find({"$or": [
            query, query_dest
        ]})

        chats = []
        for doc in docs:
            chat = Chat(
                doc.get("aes"), b"", doc.get("init_login"),
                doc.get("dst_login"), plain=True,
                cid=doc.get("_id")
            )
            chats.append(chat)
        return chats

    def add_user(self, user):
        users_collection = self.db["users"]

        if not user.validate():
            raise ValidationFailedException()

        # Генерим пару pem/ов
        s_pub_pem, s_p_pem = self.rp.gen_key_pair()
        user.set_srv_certificates(s_pub_pem, s_p_pem)

        try:
            inserted = users_collection.insert_one(user.to_mongo())
            user.uid = inserted.inserted_id
        except pymongo.errors.DuplicateKeyError:
            raise DuplicateEntryException()

    def get_user_by_uid(self, uid):
        query = {"_id": ObjectId(uid)}
        users_collection = self.db["users"]

        doc = users_collection.find_one(query)
        if doc is None:
            raise EntityNotFoundException()

        user = User(
            doc.get("name"), doc.get("hostname"),
            doc.get("password"), doc.get("u_pub_pem"),
            uid=uid
        )

        user.set_srv_certificates(
            doc.get("s_pub_pem"),
            doc.get("s_p_pem")
        )

        return user

    def get_users_by_filter(self, name='', hostname='', strict=False):
        if not strict:
            query = {
                "name": {
                    "$regex": f"{name}"
                },
                "hostname": {
                    "$regex": f"{hostname}"
                },
            }
        else:
            query = {
                "name": name,
                "hostname": hostname
            }

        users_collection = self.db["users"]
        users = []
        for doc in users_collection.find(query):
            usr = User(
                doc.get("name"), doc.get("hostname"), doc.get("password"),
                doc.get("u_pub_pem"), uid=doc.get("_id")
            )

            usr.set_srv_certificates(
                doc.get("s_pub_pem"),
                doc.get("s_p_pem")
            )

            users.append(usr)
        return users
