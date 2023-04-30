from functools import partial
import unicodedata

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.hf import StableDiffusionSpace
from .client import Client
from .imagelistwidget import ImageListWidget


class GeneratorWidget(QWidget):

    signal_slug_changed = pyqtSignal(QWidget, str)
    signal_run_finished = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ignore_slug_change = False
        self._create_widgets()
        self.signal_run_finished.connect(self.slot_update_files)

    def _create_widgets(self):
        l0 = QHBoxLayout(self)

        l = QVBoxLayout()
        l0.addLayout(l)

        def _add_control(label: str, widget: QWidget):
            container = QWidget(self)
            layout = QVBoxLayout(container)
            label = QLabel(label, container)
            font = QFont(label.font())
            font.setBold(True)
            label.setFont(font)
            layout.addWidget(label, 0)
            layout.addWidget(widget, 2)
            l.addWidget(container)

        self.path_input = QLineEdit(self)
        self.path_input.textChanged.connect(self.slot_on_path_change)
        _add_control(self.tr("sub directory"), self.path_input)

        slug_control = QWidget(self)
        l2 = QVBoxLayout(slug_control)
        l3 = QHBoxLayout()
        self.auto_update_slug_checkbox = QCheckBox(self)
        self.auto_update_slug_checkbox.setChecked(True)
        self.auto_update_slug_checkbox.setToolTip(self.tr("auto update from prompt"))
        l3.addWidget(self.auto_update_slug_checkbox, 0)
        l3.addWidget(QLabel(self.tr("auto update")), 2)
        l2.addLayout(l3)

        self.slug_input = QLineEdit(self)
        self.slug_input.textChanged.connect(self.slot_on_slug_change)
        l2.addWidget(self.slug_input)
        _add_control(self.tr("filename slug"), slug_control)

        self.prompt_input = QPlainTextEdit(self)
        self.prompt_input.setMaximumHeight(180)
        self.prompt_input.textChanged.connect(self.slot_on_prompt_change)
        _add_control(self.tr("prompt"), self.prompt_input)

        self.negative_prompt_input = QPlainTextEdit(self)
        self.negative_prompt_input.setMaximumHeight(60)
        _add_control(self.tr("negative prompt"), self.negative_prompt_input)

        guidance_control = QWidget(self)
        lh = QHBoxLayout(guidance_control)
        self.guidance_input = QSlider(Qt.Horizontal, self)
        self.guidance_input.setRange(0, 50)
        self.guidance_input.setValue(9)
        self.guidance_label = QLabel(str(self.guidance_input.value()), self)
        self.guidance_input.valueChanged.connect(self.slot_on_guidance_change)
        lh.addWidget(self.guidance_label)
        lh.addWidget(self.guidance_input)
        _add_control(self.tr("guidance"), guidance_control)

        button = QPushButton(self.tr("&start"), self)
        l.addWidget(button)
        button.clicked.connect(self.slot_run)

        self.image_list = ImageListWidget(self)
        l0.addWidget(self.image_list, 2)

    def parameters(self) -> dict:
        return {
            "path": self.path_input.text().strip(),
            "slug": self.slug_input.text().strip(),
            "prompt": self.prompt_input.toPlainText().strip(),
            "negative_prompt": self.negative_prompt_input.toPlainText().strip(),
            "guidance": self.guidance_input.value(),
        }

    def set_parameters(self, params: dict):
        self._ignore_slug_change = True
        self.path_input.setText(params.get("path") or "")
        self.slug_input.setText(params.get("slug") or "")
        self.prompt_input.setPlainText(params.get("prompt") or "")
        self.negative_prompt_input.setPlainText(params.get("negative_prompt") or "")
        self.guidance_input.setValue(params.get("guidance") or "")
        self.auto_update_slug_checkbox.setChecked(
            sluggify(self.prompt_input.toPlainText()) == self.slug_input.text()
        )
        self._ignore_slug_change = False

    def slot_on_slug_change(self):
        slug = self.slug_input.text()

        if not self._ignore_slug_change:
            self.auto_update_slug_checkbox.setChecked(True if not slug else False)

        self.signal_slug_changed.emit(self, slug)

    def slot_on_path_change(self):
        params = self.parameters()
        self.image_list.set_path(Client.singleton().result_path / params["path"])

    def slot_on_prompt_change(self):
        if self.auto_update_slug_checkbox.isChecked():
            self._ignore_slug_change = True
            self.slug_input.setText(sluggify(self.prompt_input.toPlainText()))
            self._ignore_slug_change = False

    def slot_on_guidance_change(self):
        self.guidance_label.setText(str(self.guidance_input.value()))

    def slot_run(self):
        params = self.parameters()

        path = params.pop("path") or ""
        slug = params.pop("slug") or "undefined"

        space = StableDiffusionSpace(**params)
        Client.singleton().run_space(space, path, slug, callback=self._finish_callback)

    def slot_update_files(self):
        self.image_list.set_path(self.image_list.path)

    def _finish_callback(self):
        self.signal_run_finished.emit()


def sluggify(s : str, max_length: int = 45) -> str:
    s = unicodedata.normalize('NFKD', s.lower()).encode("ascii", "ignore").decode("ascii")
    result = ""
    for c in s:
        if c.isalnum():
            result += c
        else:
            if not result.endswith("-"):
                result += "-"

        if len(result) >= max_length:
            break

    return result.strip("-")
