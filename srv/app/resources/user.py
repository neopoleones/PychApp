import time
import falcon
from .middleware import *


class RegisterResource:
    def __init__(self, storage):
        self.storage = storage

    def on_post(self, req, resp):
        print(req.media)

        resp.status = falcon.HTTP_200
