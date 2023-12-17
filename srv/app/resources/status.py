import time
import falcon
from .middleware import *


class StatusResource:
    def __init__(self, cfg):
        self.started = time.time()
        self.cfg = cfg

    def on_get(self, req, resp):
        status_response = {
            "app": f"pychapp_{self.cfg.env}",
            "status": "ok",
            "uptime": time.time()-self.started
        }

        if 'auth' in req.context and 'user' in req.context['auth']:
            user = req.context['auth']['user']
            if user:
                status_response['user'] = user.get_login()

        resp.media = status_response
