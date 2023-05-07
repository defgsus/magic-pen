import json
from typing import Optional, Mapping, Any

import sqlalchemy as sq
import tornado.web

from src.imagedb import *
from .staticresources import StaticResources


class NoCacheStaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")


class BaseHandler(tornado.web.RequestHandler):

    def __init__(self, *args, **kwargs):
        self.resources: Optional[StaticResources] = None
        super().__init__(*args, **kwargs)

    def initialize(self, resources: StaticResources):
        self.resources = resources

    @property
    def db(self) -> ImageDB:
        return self.resources.db

    def write(self, *args, **kwargs) -> None:
        self.set_header("Access-Control-Allow-Origin", "*")
        super().write(*args, **kwargs)

class JsonBaseHandler(BaseHandler):

    def write(self, data: Mapping[str, Any]):
        self.set_header("Content-Type", "application/json")
        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        super().write(json.dumps(data))

    def prepare(self):
        super().prepare()
        try:
            self.json_body = json.loads(self.request.body)
        except ValueError as e:
            self.json_body = None


class StatusHandler(JsonBaseHandler):

    def get(self):
        self.write(self.db.status())



class ImageHandler(BaseHandler):

    def get(self, pk):
        entry = self.db.get_image(id=int(pk))
        if not entry:
            self.set_status(404)
            self.finish()
            return

        self.set_header("Content-Type", entry.mime_type())
        self.write(entry.filename().read_bytes())


class QueryHandler(JsonBaseHandler):

    def post(self):
        text = self.json_body.get("text")
        model = self.json_body.get("model")
        count = self.json_body.get("count") or 1
        device = self.json_body.get("device") or "auto"

        response = {"images": []}
        if text:
            index = self.db.sim_index(model=model)
            result = index.images_by_text(prompt=text, count=count, device=device)

            for image_entry, score in result:
                response["images"].append({"id": image_entry.id, "score": round(score, 3)})

        self.write(response)

