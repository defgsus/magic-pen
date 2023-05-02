import json
from functools import partial
import unicodedata

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.hf import StableDiffusionSpace
from .client import Client


class StatusWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_widgets()

        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.slot_update)
        self.timer.start()

    def _create_widgets(self):
        l = QHBoxLayout()
        self.setLayout(l)

        self.status_label = QLabel(self)
        self.status_label.setWordWrap(True)
        l.addWidget(self.status_label)

    def slot_update(self):
        client = Client.singleton()
        status = client.status()

        msg = " | ".join(
            f"{key}: {status[key]}"
            for key in sorted(status)
        )
        self.status_label.setText(msg)
