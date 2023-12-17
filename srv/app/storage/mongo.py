import pymongo
import falcon
from bson.objectid import ObjectId

from .model import User


class ValidationFailedException(Exception):
    @staticmethod
    def handle(ex, req, resp, params):
        # TODO: Log the error, clean up, etc. before raising
        raise falcon.HTTPInternalServerError()


class EntityNotFoundException(Exception):
    @staticmethod
    def handle(ex, req, resp, params):
        # TODO: Log the error, clean up, etc. before raising
        raise falcon.HTTPInternalServerError()


class PychStorage:
    def __init__(self, cfg):
        self.con = pymongo.MongoClient(cfg.mongo['con_link'])
        self.db = self.con[cfg.mongo['db']]

        # Проверяем, что индекс уникален
        self.db["users"].create_index({"name": 1}, unique=True)

    def add_user(self, user):
        users_collection = self.db["users"]

        if not user.validate():
            raise ValidationFailedException()

        inserted = users_collection.insert_one(user.to_mongo())
        user.uid = inserted.inserted_id

    def get_user_by_uid(self, uid):
        query = {"_id": ObjectId(uid)}
        users_collection = self.db["users"]

        doc = users_collection.find_one(query)
        if doc is None:
            raise EntityNotFoundException()

        return User(doc.get("name"), doc.get("hostname"), doc.get("password"), uid=uid)

    def get_users_by_filter(self, name='', hostname=''):
        query = {
            "name": {
                "$regex": f"{name}.*"
            },
            "hostname": {
                "$regex": f"{hostname}.*"
            },
        }

        users_collection = self.db["users"]
        users = []
        for doc in users_collection.find(query):
            users.append(User(doc.get("name"), doc.get("hostname"), doc.get("password"), uid=doc.get("_id")))
        return users
