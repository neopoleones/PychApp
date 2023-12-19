import falcon

from app.storage.mongo import *
from app.resources.middleware import *
from app.resources.status import StatusResource
from app.resources.chat import NewResource, ListResource
from app.resources.user import RegisterResource, SearchResource, LoginResource


def register_handlers(app, cfg, storage, sp):
    """
    Register API routes and resources with the Falcon application.

    Args:
        app: The Falcon application instance.
        cfg: The configuration object containing application settings.
        storage: The PychStorage instance for data storage.
        sp: The security provider for token validation and encryption.
    """

    app.add_route("/status", StatusResource(cfg))
    app.add_route("/api/user/register", RegisterResource(storage))
    app.add_route("/api/user/search", SearchResource(storage))
    app.add_route("/api/user/login", LoginResource(storage, sp))
    app.add_route("/api/chat/new", NewResource(storage, cfg.secret))
    app.add_route("/api/chat/list", ListResource(storage))


def get_service(cfg, logger, security_provider, storage) -> falcon.App:
    """
    Create and configure the Falcon application.

    This function creates and configures the Falcon application for the PychChat service, including adding middleware,
    error handlers, and registering API routes and resources.

    Args:
        cfg: The configuration object containing application settings.
        logger: The application logger.
        security_provider: The security provider for middleware.
        storage: The PychStorage instance for data storage.

    Returns:
        The configured Falcon application instance.
    """

    app = falcon.App(
        middleware=[
            TokenMiddleware(security_provider),
            UserByTokenMiddleware(storage),
            RequireJSON(),
        ]
    )

    app.add_error_handler(
        ValidationFailedException, ValidationFailedException.handle)
    app.add_error_handler(
        EntityNotFoundException, EntityNotFoundException.handle)
    app.add_error_handler(
        DuplicateEntryException, DuplicateEntryException.handle)

    logger.info('Registering the resources')
    register_handlers(app, cfg, storage, security_provider)

    return app
