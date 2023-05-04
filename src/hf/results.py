import dataclasses
from io import BytesIO
from pathlib import Path
from typing import Union

import PIL.Image

_MIME_EXT_MAPPING = {
    "jpeg": "jpg",
    "x-wav": "wav",
}


@dataclasses.dataclass
class Result:
    data: bytes
    mime_type: str

    @property
    def extension(self) -> str:
        ext = self.mime_type.split("/")[-1].lower()
        ext = _MIME_EXT_MAPPING.get(ext, ext)
        return ext

    def save(self, filename: Union[str, Path]):
        with open(filename, "wb") as fp:
            fp.write(self.data)


class ImageResult(Result):

    def to_pil(self) -> PIL.Image.Image:
        fp = BytesIO(self.data)
        return PIL.Image.open(fp)

    def _ipython_display_(self):
        from IPython.display import display
        display(self.to_pil())


class AudioResult(Result):

    def _ipython_display_(self):
        from IPython.display import Audio, display
        display(Audio(self.data))
