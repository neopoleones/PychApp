import falcon
from app.storage.model import User
from app.resources.middleware import *


class RegisterResource:
    def __init__(self, storage):
        self.storage = storage

    def on_post(self, req, resp):
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
            "login": user.get_login()
        }


class SearchResource:
    def __init__(self, storage):
        self.storage = storage

    def on_get(self, req, resp):
        username = req.params['username'] if 'username' in req.params else ""
        hostname = req.params['hostname'] if 'hostname' in req.params else ""

        if len(username) == 0 and len(hostname) == 0:
            raise falcon.HTTPBadRequest("username or hostname should be specified")

        users = self.storage.get_users_by_filter(name=username, hostname=hostname)

        resp.status = falcon.HTTP_200
        resp.media = {
            "status": "ok",
            "users": [str(u) for u in users]
        }


class LoginResource:
    def __init__(self, storage, sp):
        self.storage = storage
        self.sp = sp

    def on_post(self, req, resp):
        try:
            username = req.media["username"]
            hostname = req.media["hostname"]
            password = req.media["password"]

        except Exception:
            raise falcon.HTTPBadRequest(title="not all fields specified")

        # Check if client specified correct auth data
        u = self.storage.get_users_by_filter(name=username, hostname=hostname)
        if len(u) != 1:
            raise falcon.HTTPNotFound(title="user not found")
        u = u[0]

        if not (u.get_login() == f'{username}@{hostname}' and User.harden(password) == u.password):
            raise falcon.HTTPUnauthorized(title="bad auth data")
        token = self.sp.encrypt(u.uid_as_bytes())

        resp.set_header("Auth", token)
        resp.status = falcon.HTTP_200

        resp.media = {
            "status": "ok",
            "message": "authorized"
        }
