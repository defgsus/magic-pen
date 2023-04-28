from functools import partial
import unicodedata

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
#import PyQt5.QtWidgets
#PyQt5.QtWidgets.QPlainTextEdit

from src.hf import StableDiffusionSpace
from .client import Client
from .imagelistwidget import ImageListWidget


class GeneratorWidget(QWidget):

    signal_slug_changed = pyqtSignal(QWidget, str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._auto_update_slug = True
        self._ignore_slug_change = False
        self._create_widgets()

    def _create_widgets(self):
        l0 = QHBoxLayout(self)

        l = QVBoxLayout()
        l0.addLayout(l)

        l.addWidget(QLabel(self.tr("sub-directory"), self))
        self.path_input = QPlainTextEdit(self)
        self.path_input.setFixedHeight(30)
        self.path_input.textChanged.connect(self.slot_on_path_change)
        l.addWidget(self.path_input)

        l.addWidget(QLabel(self.tr("session slug"), self))
        self.slug_input = QPlainTextEdit(self)
        self.slug_input.setFixedHeight(30)
        self.slug_input.textChanged.connect(self.slot_on_slug_change)
        l.addWidget(self.slug_input)

        l.addWidget(QLabel(self.tr("prompt"), self))
        self.prompt_input = QPlainTextEdit(self)
        self.prompt_input.setMaximumHeight(100)
        self.prompt_input.textChanged.connect(self.slot_on_prompt_change)
        l.addWidget(self.prompt_input)

        l.addWidget(QLabel(self.tr("negative prompt"), self))
        self.negative_prompt_input = QPlainTextEdit(self)
        self.negative_prompt_input.setMaximumHeight(100)
        l.addWidget(self.negative_prompt_input)

        l.addWidget(QLabel(self.tr("guidance"), self))
        lh = QHBoxLayout()
        l.addLayout(lh)
        self.guidance_input = QSlider(Qt.Horizontal, self)
        self.guidance_input.setRange(0, 50)
        self.guidance_input.setValue(9)
        self.guidance_label = QLabel(str(self.guidance_input.value()), self)
        self.guidance_input.valueChanged.connect(self.slot_on_guidance_change)
        lh.addWidget(self.guidance_label)
        lh.addWidget(self.guidance_input)

        button = QPushButton(self.tr("&start"), self)
        l.addWidget(button)
        button.clicked.connect(self.slot_run)

        self.image_list = ImageListWidget(self)
        l0.addWidget(self.image_list, 2)

    def parameters(self) -> dict:
        return {
            "path": self.path_input.toPlainText().strip(),
            "slug": self.slug_input.toPlainText().strip(),
            "prompt": self.prompt_input.toPlainText().strip(),
            "negative_prompt": self.negative_prompt_input.toPlainText().strip(),
            "guidance": self.guidance_input.value(),
        }

    def slot_on_slug_change(self):
        slug = self.slug_input.toPlainText()

        if not self._ignore_slug_change:
            self._auto_update_slug = True if not slug else False

        self.signal_slug_changed.emit(self, slug)

    def slot_on_path_change(self):
        self.image_list.set_path(Client.singleton().result_path / self.path_input.toPlainText())

    def slot_on_prompt_change(self):
        if self._auto_update_slug:
            self._ignore_slug_change = True
            self.slug_input.setPlainText(sluggify(self.prompt_input.toPlainText()))
            self._ignore_slug_change = False

    def slot_on_guidance_change(self):
        self.guidance_label.setText(str(self.guidance_input.value()))

    def slot_run(self):
        params = self.parameters()

        path = params.pop("path") or ""
        slug = params.pop("slug") or "undefined"

        space = StableDiffusionSpace(**params)
        Client.singleton().run_space(space, path, slug)


def sluggify(s : str) -> str:
    s = unicodedata.normalize('NFKD', s.lower()).encode("ascii", "ignore").decode("ascii")
    result = ""
    for c in s:
        if c.isalnum():
            result += c
        else:
            if not result.endswith("-"):
                result += "-"
    return result
