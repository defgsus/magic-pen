import dataclasses
from io import BytesIO
from pathlib import Path
from typing import Union

import PIL.Image


@dataclasses.dataclass
class ImageResult:
    data: bytes
    mime_type: str

    @property
    def extension(self) -> str:
        ext = self.mime_type.split("/")[-1].lower()
        if ext == "jpeg":
            ext = "jpg"
        return ext

    def save(self, filename: Union[str, Path]):
        with open(filename, "wb") as fp:
            fp.write(self.data)

    def to_pil(self) -> PIL.Image.Image:
        fp = BytesIO(self.data)
        return PIL.Image.open(fp)

