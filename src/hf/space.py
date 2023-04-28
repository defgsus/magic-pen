import json
import secrets
from typing import Iterable, Any, Optional, Callable

import websocket


class HuggingfaceSpace:

    def __init__(
            self,
            websocket_url: str,
            parameters: Iterable[Any] = tuple(),
    ):
        self.websocket_url = websocket_url
        self.parameters = list(parameters)
        self._result = None
        self.state = "pending"
        self.status = None
        self._ws: Optional[websocket.WebSocketApp] = None
        self._session_hash: Optional[str] = None
        self.finished: Optional[Callable] = None

    def result(self):
        return self._result

    def run(self):
        self._ws = websocket.WebSocketApp(
            url=self.websocket_url,
            header={
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:106.0) Gecko/20100101 Firefox/106.0",
            },
            on_open=self._on_open,
            on_close=self._on_close,
            on_message=self._on_message,
            on_error=self._on_error,
        )
        self._ws.run_forever()
        if self.finished is not None:
            self.finished()

    def _on_message(self, ws, message):
        print("MSG:", message)
        message = json.loads(message)
        if message.get("msg") == "send_hash":
            self.state = "connecting"
            self._session_hash = secrets.token_urlsafe(8)
            self._ws.send(json.dumps({
                "fn_index": 3,
                "session_hash": self._session_hash,
            }))

        elif message.get("msg") == "estimation":
            # {"msg": "estimation",
            #  "rank": 29,
            #  "queue_size": 30,
            #  "avg_event_process_time": 26.253087945852066,
            #  "avg_event_concurrent_process_time": 0.3281635993231508,
            #  "rank_eta": 36.097995925546584,
            #  "queue_eta": 9}
            self.state = "wait_queue"
            self.status = {
                "rank": message["rank"],
                "queue_size": message["queue_size"],
                "estimated": message["rank_eta"],
            }

        elif message.get("msg") == "send_data":
            self._ws.send(json.dumps({
                "fn_index": 3,
                "session_hash": self._session_hash,
                "data": self.parameters,
            }))

        elif message.get("msg") == "process_starts":
            self.state = "processing"

        elif message.get("msg") == "process_completed":
            self.state = "complete"
            self._result = message
            print(json.dumps(message, indent=2))

    def _on_error(self, ws, error):
        self.state = "error"
        print("error:", error)

    def _on_close(self, ws, close_status_code, close_msg):
        self.state = "closed"
        print("### closed ###")

    def _on_open(self, ws):
        self.state = "open"
        print("Opened connection")
