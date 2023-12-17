import falcon

from app.resources.middleware import *
from app.resources.status import StatusResource
from app.resources.chat import NewResource, ListResource
from app.resources.user import RegisterResource, SearchResource, LoginResource
from app.storage.mongo import ValidationFailedException, EntityNotFoundException, DuplicateEntryException


def register_handlers(app, cfg, storage, sp):
    app.add_route("/status", StatusResource(cfg))
    app.add_route("/api/user/register", RegisterResource(storage))
    app.add_route("/api/user/search", SearchResource(storage))
    app.add_route("/api/user/login", LoginResource(storage, sp))
    app.add_route("/api/chat/new", NewResource(storage, cfg.secret))
    app.add_route("/api/chat/list", ListResource(storage))


def get_service(cfg, logger, security_provider, storage) -> falcon.App:
    app = falcon.App(
        middleware=[
            TokenMiddleware(security_provider),
            UserByTokenMiddleware(storage),
            RequireJSON(),
        ]
    )

    app.add_error_handler(ValidationFailedException, ValidationFailedException.handle)
    app.add_error_handler(EntityNotFoundException, EntityNotFoundException.handle)
    app.add_error_handler(DuplicateEntryException, DuplicateEntryException.handle)

    logger.info('Registering the resources')
    register_handlers(app, cfg, storage, security_provider)

    return app
