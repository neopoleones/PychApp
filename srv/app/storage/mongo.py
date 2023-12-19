import falcon
import pymongo
from .model import User, Chat, Message
from bson.objectid import ObjectId


class ValidationFailedException(Exception):
    """
    Exception raised for validation failure.
    """

    @staticmethod
    def handle(ex, req, resp, params):
        """
        Handle the ValidationFailedException by raising a Falcon HTTPBadRequest.

        Args:
            ex: The ValidationFailedException instance.
            req: The Falcon request object.
            resp: The Falcon response object.
            params: Additional parameters (unused).
        """

        raise falcon.HTTPBadRequest("validation failed")


class EntityNotFoundException(Exception):
    """
    Exception raised for entity not found.
    """

    @staticmethod
    def handle(ex, req, resp, params):
        """
        Handle the EntityNotFoundException by raising a Falcon HTTPNotFound.

        Args:
            ex: The ValidationFailedException instance.
            req: The Falcon request object.
            resp: The Falcon response object.
            params: Additional parameters (unused).
        """
        raise falcon.HTTPNotFound(title="user not found")


class DuplicateEntryException(Exception):
    """
    Exception raised for duplicate entry.
    """

    @staticmethod
    def handle(ex, req, resp, params):
        """
        Handle the DuplicateEntryException by raising a Falcon HTTPBadRequest.

        Args:
            ex: The ValidationFailedException instance.
            req: The Falcon request object.
            resp: The Falcon response object.
            params: Additional parameters (unused).
        """
        raise falcon.HTTPBadRequest(title="user already registered")


class PychStorage:
    """
    A class representing the storage and database operations for the Pych application.

    This class handles interactions with a MongoDB database, including adding messages, managing chat sessions,
    adding users, and retrieving chat and user data.

    Attributes:
        rp: An RSAProvider for generating RSA key pairs and handling encryption.
        con: A MongoDB client connection.
        db: The MongoDB database instance.
    """

    def __init__(self, cfg, rp):
        """
        Initialize a PychStorage instance.

        Args:
            cfg: Configuration object containing MongoDB connection details.
            rp: An RSAProvider for generating RSA key pairs and handling encryption.
        """

        self.rp = rp
        self.con = pymongo.MongoClient(cfg.mongo['con_link'])
        self.db = self.con[cfg.mongo['db']]

        # Проверяем, что индекс уникален
        self.db["users"].create_index({"name": 1}, unique=True)

    def add_message(self, message):
        """
        Adds a message to the database.

        Args:
            message: The message object to be added to the database.
        """

        messages_collection = self.db["messages"]
        inserted = messages_collection.insert_one(message.to_mongo())
        message.mid = inserted.inserted_id

    def set_message_read(self, message):
        """
        Sets message as being read by user.

        Args:
            message: The message object to be changed.
        """

        messages_collection = self.db["messages"]
        message.read = True

        messages_collection.update_one({
            "_id": message.mid
        }, {
            "$set": {
                "read": True
            }
        }, upsert=False)

    def get_messages(self, chat):
        """
        Gets messages that belongs to specified chat. Returns only messages that user haven't read

        Args:
            chat: Chat object for filtering messages.
        """

        messages_collection = self.db["messages"]
        query = {
            "chat_id": str(chat.cid),
            "read": False,
        }

        messages = []
        for doc in messages_collection.find(query):
            m = Message(
                chat, doc.get("author_id"), doc.get("msg"),
                doc.get("timestamp"),
                mid=doc.get("_id"),
            )
            messages.append(m)
        return messages

    def add_chat(self, chat):
        """
        Adds a chat to the database.

        Args:
            chat: The chat object to be added to the database.
        """

        chats_collection = self.db["chats"]

        inserted = chats_collection.insert_one(chat.to_mongo())
        chat.cid = inserted.inserted_id

    def get_chat(self, src_user, dst_user):
        """
        Retrieves the chat with two specified users.

        Args:
            src_user: The user who started the chat session.
            dst_user: The user with whom the chat session was started.

        Returns:
            A chat object for specified users.
        """

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
        """
        Retrieves all chats for a given user.

        This method queries the 'chats' collection in the database to retrieve all chat sessions
        in which the specified user is involved. It returns a list of Chat objects.

        Args:
            src_user: The user for whom to retrieve chats.

        Returns:
            A list of Chat objects representing chat sessions involving the specified user.
        """

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
        """
        Adds a user to the database.

        Args:
            user (User): The user object to be added to the database.

        Raises:
            ValidationFailedException: If the user data does not pass validation.
            DuplicateEntryException: If a user with the same name already exists.
        """

        users_collection = self.db["users"]

        if not user.validate():
            raise ValidationFailedException()

        s_pub_pem, s_p_pem = self.rp.gen_key_pair()
        user.set_srv_certificates(s_pub_pem, s_p_pem)

        try:
            inserted = users_collection.insert_one(user.to_mongo())
            user.uid = inserted.inserted_id
        except pymongo.errors.DuplicateKeyError:
            raise DuplicateEntryException()

    def get_user_by_uid(self, uid):
        """
        Retrieves a user by their unique identifier.

        Args:
            uid: The unique identifier of the user.

        Returns:
            The User object representing the user with the specified UID.

        Raises:
            EntityNotFoundException: If no user with the specified UID is found.
        """

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
        """
        Retrieves users based on optional filtering criteria.

        Args:
            name: The name filter (optional).
            hostname: The hostname filter (optional).
            strict: A flag indicating strict filtering, where both name and hostname must match exactly (optional).

        Returns:
            A list of User objects representing users that match the filtering criteria.
        """

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
