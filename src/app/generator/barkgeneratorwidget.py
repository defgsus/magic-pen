from functools import partial
import unicodedata

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.hf import BarkSpace
from .client import Client
from .imagelistwidget import ImageListWidget
from .generatorwidgetbase import GeneratorWidgetBase, sluggify


class BarkGeneratorWidget(GeneratorWidgetBase):

    list_item_height: int = 100

    def set_focus(self):
        self.prompt_input.setFocus()

    def _create_control_widgets(self):
        lv = QVBoxLayout()

        self.prompt_input = QPlainTextEdit(self)
        lv.addWidget(self.prompt_input)
        self.prompt_input.setMaximumHeight(180)
        self.prompt_input.textChanged.connect(self.slot_on_prompt_change)
        self._add_control(self.tr("prompt"), lv)

        lh = QHBoxLayout()
        lv.addLayout(lh)
        for text in ("♪", "—", "[laughs]"):
            butt = QToolButton(self)
            butt.setText(text)
            butt.clicked.connect(partial(self.add_to_prompt, text))
            lh.addWidget(butt)
        lh.addStretch(2)

        self.voice_select = QComboBox(self)
        self.voice_select.addItem("Unconditional")
        self.voice_select.addItem("Announcer")
        for lang in ("en", "de", "es", "fr", "hi", "it", "ja", "ko", "pl", "pt", "ru", "tr", "th"):
            for i in range(10):
                self.voice_select.addItem(f"Speaker {i} ({lang})")
        self._add_control(self.tr("voice"), self.voice_select)

    def parameters(self) -> dict:
        return {
            **super().parameters(),
            "prompt": self.prompt_input.toPlainText().strip(),
            "voice": self.voice_select.currentText().strip(),
        }

    def set_parameters(self, params: dict):
        self._ignore_slug_change = True
        self.path_input.setText(params.get("path") or "")
        self.prompt_input.setPlainText(params.get("prompt") or "")
        self.slug_input.setText(params.get("slug") or "")
        self.voice_select.setCurrentText(params.get("voice") or "Unconditional")
        self.auto_update_slug_checkbox.setChecked(
            sluggify(self.prompt_input.toPlainText()) == self.slug_input.text()
        )
        self._ignore_slug_change = False

    def add_to_prompt(self, text: str):
        self.prompt_input.textCursor().insertText(text)

    def slot_on_prompt_change(self):
        if self.auto_update_slug_checkbox.isChecked():
            self._ignore_slug_change = True
            self.slug_input.setText(sluggify(self.prompt_input.toPlainText()))
            self._ignore_slug_change = False

    def create_hf_space(self) -> BarkSpace:
        params = self.parameters()
        params.pop("path")
        params.pop("slug")

        return BarkSpace(**params)
