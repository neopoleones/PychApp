import structlog as slog
from app.cfg import loader
from app.service import get_service
from wsgiref.simple_server import make_server
from app.storage.provider import FernetAdapter
from app.storage.mongo import PychStorage

slog.configure(
    processors=[
        slog.processors.TimeStamper(fmt="iso"),
        slog.processors.add_log_level,
        slog.processors.JSONRenderer(),
    ]
)

if __name__ == "__main__":
    try:
        # Get all components for service
        cfg = loader.get_configuration()
        logger = slog.get_logger()
        sp,  = FernetAdapter(cfg.secret)
        storage = PychStorage(cfg)

        service = get_service(cfg, logger, sp, storage)
        with make_server(cfg.rest['host'], cfg.rest['port'], service) as httpd:
            logger.info('Starting pychapp', env=cfg.env, addr=f"{cfg.rest['host']}:{cfg.rest['port']}")
            httpd.serve_forever()

    except Exception as tle:
        print(f"Got top level exception: {type(tle)}")
