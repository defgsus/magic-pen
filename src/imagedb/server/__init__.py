import tornado.web
import tornado.ioloop

# from src.imagedb import ImageDB
from src import log
from .handlers import *
from .staticresources import StaticResources


def run_server(
        db: ImageDB,
        host: str = "127.0.0.1",
        port: int = 8000,
        verbose: bool = False,
        debug: bool = True,
):
    # tornado.ioloop.IOLoop.current().start()

    handler_kwargs = {"resources": StaticResources(db=db)}

    app = tornado.web.Application(
        handlers=[
            (r"/status/", StatusHandler, handler_kwargs),
            (r"/image/([0-9]+)/", ImageHandler, handler_kwargs),
            (r"/query/", QueryHandler, handler_kwargs),
        ],
        default_host=host,
        #static_path=str(config.STATIC_PATH),
        #template_path=str(config.TEMPLATE_PATH),
        debug=debug,
        static_handler_class=handlers.NoCacheStaticFileHandler,
        #default_handler_class=IndexFallbackHandler,
    )
    app.listen(port)

    if verbose:
        log.log(f"Server: running at http://{host}:{port}")

    tornado.ioloop.IOLoop.current().start()
