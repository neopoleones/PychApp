import falcon
from app.storage.model import User
from app.resources.middleware import *


class RegisterResource:
    """
    Resource for handling user registration.

    This class provides an endpoint to register new users. It captures user details such as username,
    hostname, password, and public key, and stores them in the system.

    Attributes:
        storage: An object to store user data.
    """

    def __init__(self, storage):
        """
        Initialize a RegisterResource instance.

        Args:
            storage: An object that provides methods to store user data.
        """

        self.storage = storage

    def on_post(self, req, resp):
        """
        Handle POST requests for user registration.

        This method extracts user data from the request, creates a new user, and stores it using the storage object.
        It then sets a successful response with the new user's details. If the request is missing required fields,
        it raises an HTTPBadRequest error.

        Args:
            req: The request object, containing user data.
            resp: The response object.
        """

        try:
            username = req.media["username"]
            hostname = req.media["hostname"]
            password = req.media["password"]
            u_pub_k = req.media["u_pub_k"]

        except Exception:
            raise falcon.HTTPBadRequest(title="not all fields specified")

        user = User(username, hostname, password, u_pub_k)
        self.storage.add_user(user)

        resp.status = falcon.HTTP_200
        resp.media = {
            "status": "ok",
            "uid": user.uid_as_bytes().decode('utf-8'),
            "s_pub_k": user.s_pub_k.decode(),
            "login": user.get_login()
        }


class SearchResource:
    """
    Resource for searching users in the chat.

    This class provides an endpoint to search for users based on username and/or hostname.

    Attributes:
        storage: An object to store and retrieve user data.
    """

    def __init__(self, storage):
        """
        Initialize a SearchResource instance.

        Args:
            storage: An object that provides methods to store and retrieve user data.
        """

        self.storage = storage

    def on_get(self, req, resp):
        """
        Handle GET requests for searching users.

        This method extracts search parameters from the request, retrieves matching users from the storage,
        and sets the response with the list of found users. If no valid search parameters are provided,
        it raises an HTTPBadRequest error.

        Args:
            req: The request object, containing search parameters.
            resp: The response object.
        """

        username = req.params['username'] if 'username' in req.params else ""
        hostname = req.params['hostname'] if 'hostname' in req.params else ""

        if len(username) == 0 and len(hostname) == 0:
            raise falcon.HTTPBadRequest(
                "username or hostname should be specified"
            )

        users = self.storage.get_users_by_filter(
            name=username, hostname=hostname
        )

        resp.status = falcon.HTTP_200
        resp.media = {
            "status": "ok",
            "users": [str(u) for u in users]
        }


class LoginResource:
    """
    Resource for handling user login.

    This class provides an endpoint for user authentication. It verifies user credentials and provides an
    authentication token upon successful login.

    Attributes:
        storage: An object to store and retrieve user data.
        sp: Security provider used for generating auth tokens.
    """

    def __init__(self, storage, sp):
        """
        Initialize a LoginResource instance.

        Args:
            storage: An object that provides methods to store and retrieve user data.
            sp: Security provider for encrypting/decrypting data.
        """

        self.storage = storage
        self.sp = sp

    def on_post(self, req, resp):
        """
        Handle POST requests for user authentication.

        This method validates the user's credentials, generates an authentication token if credentials are valid,
        and sets the response with the user's details. If the credentials are invalid or incomplete, it raises
        an appropriate HTTP error.

        Args:
            req: The request object, containing user credentials.
            resp: The response object.
        """

        try:
            username = req.media["username"]
            hostname = req.media["hostname"]
            password = req.media["password"]

        except Exception:
            raise falcon.HTTPBadRequest(title="not all fields specified")

        # Check if client specified correct auth data
        u = self.storage.get_users_by_filter(
            name=username, hostname=hostname, strict=True
        )
        if len(u) != 1:
            raise falcon.HTTPNotFound(title="user not found")
        u = u[0]

        eq_login = u.get_login() == f'{username}@{hostname}'
        if not (eq_login and User.harden(password) == u.password):
            raise falcon.HTTPUnauthorized(title="bad auth data")

        token = self.sp.encrypt(u.uid_as_bytes())
        resp.set_header("Auth", token.decode('utf-8'))
        resp.status = falcon.HTTP_200

        resp.media = {
            "status": "ok",
            "uid": u.uid_as_bytes().decode('utf-8'),
            "s_pub_k": u.s_pub_k.decode()
        }
