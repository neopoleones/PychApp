import time
import falcon
from .middleware import *


class StatusResource:
    """
    A resource for retrieving the status of the application.

    This class provides an endpoint to get the current state of the application, including its uptime and
    the environment it's running in. Optionally, if a user is authenticated, their login information is included.

    Attributes:
        started: The timestamp when the instance was created, used to calculate uptime.
        cfg: A configuration object containing environment and other settings.

    """

    def __init__(self, cfg):
        """
        Initialize a StatusResource instance.

        The constructor initializes the `started` attribute to the current time and stores the configuration object.

        Args:
            cfg: A configuration object containing environment and other settings.
        """

        self.started = time.time()
        self.cfg = cfg

    def on_get(self, req, resp):
        """
        Handle a GET request to the status endpoint.

        This method constructs a status response that includes the application name, status ("ok"), and uptime.
        If a user is authenticated and available in the request context,
        their login information is included in the response.
        It sets the constructed status information in the response media and sets the HTTP status to 200 OK.

        Args:
            req: The request object.
            resp: The response object.
        """
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
        resp.status = falcon.HTTP_200
