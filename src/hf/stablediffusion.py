import urllib.request
from io import BytesIO
from typing import List

import PIL.Image

from .space import HuggingfaceSpace
from .results import ImageResult


class StableDiffusionSpace(HuggingfaceSpace):

    def __init__(
            self,
            prompt: str,
            negative_prompt: str = None,
            guidance: int = 9,
    ):
        super().__init__(
            websocket_url="wss://stabilityai-stable-diffusion.hf.space/queue/join",
            parameters=[prompt, negative_prompt, guidance],
        )

    def parameters(self) -> dict:
        return {
            "prompt": self._parameters[0],
            "negative_prompt": self._parameters[1],
            "guidance": self._parameters[2],
        }

    def result(self) -> List[ImageResult]:
        if not self._result:
            return []

        images = []
        for results in self._result["output"]["data"]:
            for uri in results:
                mime_type = uri.split(";", 1)[0].split(":")[-1]

                response = urllib.request.urlopen(uri)
                data = response.fp.read()

                images.append(
                    ImageResult(mime_type=mime_type, data=data)
                )

        return images
