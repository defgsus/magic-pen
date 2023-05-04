import urllib.request
from io import BytesIO
from typing import List

import requests

from .space import HuggingfaceSpace
from .results import AudioResult


class BarkSpace(HuggingfaceSpace):

    def __init__(
            self,
            prompt: str,
            voice: str = "Unconditional",
    ):
        super().__init__(
            websocket_url="wss://suno-bark--r8scr.hf.space/queue/join",
            parameters=[prompt, voice],
        )

    def parameters(self) -> dict:
        return {
            "prompt": self._parameters[0],
            "voice": self._parameters[1],
        }

    def result(self) -> List[AudioResult]:
        if not (self._result and self._result.get("output") and self._result["output"].get("data")):
            return []

        results = []
        for result in self._result["output"]["data"]:
            name = result["name"]
            url = f"https://suno-bark--r8scr.hf.space/file={name}"
            response = requests.get(url)

            results.append(
                AudioResult(mime_type="audio/wav", data=response.content)
            )

        return results
