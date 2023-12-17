import falcon
from app.resources.status import StatusResource
from app.resources.user import RegisterResource

from app.resources.middleware import *


def register_handlers(app, cfg, storage):
    app.add_route("/status", StatusResource(cfg))
    app.add_route("/api/register", RegisterResource(storage))


def get_service(cfg, logger, security_provider, storage) -> falcon.App:
    app = falcon.App(
        middleware=[
            TokenMiddleware(security_provider),
            UserByTokenMiddleware(storage),
            RequireJSON(),
        ]
    )

    logger.info('Registering the resources')
    register_handlers(app, cfg, storage)

    return app
