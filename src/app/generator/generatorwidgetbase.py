from functools import partial
import unicodedata
from typing import Union

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.hf import HuggingfaceSpace
from .client import Client
from .imagelistwidget import ImageListWidget


class GeneratorWidgetBase(QWidget):

    signal_path_changed = pyqtSignal(QWidget, str)
    signal_slug_changed = pyqtSignal(QWidget, str)
    signal_run_finished = pyqtSignal()

    list_item_height: int = 150

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ignore_slug_change = False
        self._create_widgets()
        self.signal_run_finished.connect(self.slot_update_files)

    def set_focus(self):
        pass

    def _create_control_widgets(self):
        raise NotImplementedError

    def parameters(self) -> dict:
        return {
            "path": self.path_input.text().strip(),
            "slug": self.slug_input.text().strip(),
        }

    def set_parameters(self, params: dict):
        raise NotImplementedError

    def _add_control(self, label: str, widget: Union[QWidget, QLayout]):
        container = QWidget(self)
        layout = QVBoxLayout(container)
        label = QLabel(label, container)
        font = QFont(label.font())
        font.setBold(True)
        label.setFont(font)
        layout.addWidget(label, 0)
        if isinstance(widget, QWidget):
            layout.addWidget(widget, 2)
        else:
            layout.addLayout(widget)
        self.v_layout.addWidget(container)

    def _create_widgets(self):
        l0 = QHBoxLayout(self)

        self.v_layout = l = QVBoxLayout()
        l0.addLayout(l)

        self.path_input = QLineEdit(self)
        self.path_input.textChanged.connect(self.slot_on_path_change)
        self._add_control(self.tr("sub directory"), self.path_input)

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
        self._add_control(self.tr("filename slug"), slug_control)

        self._create_control_widgets()

        button = QPushButton(self.tr("&start"), self)
        l.addWidget(button)
        button.clicked.connect(self.slot_run)

        self.image_list = ImageListWidget(self.list_item_height, self)
        l0.addWidget(self.image_list, 2)

    def slot_on_slug_change(self):
        slug = self.slug_input.text()

        if not self._ignore_slug_change:
            self.auto_update_slug_checkbox.setChecked(True if not slug else False)

        self.signal_slug_changed.emit(self, slug)

    def slot_on_path_change(self):
        params = self.parameters()
        self.image_list.set_path(Client.singleton().result_path / params["path"])
        self.signal_path_changed.emit(self, params["path"])

    def create_hf_space(self) -> HuggingfaceSpace:
        raise NotImplementedError

    def slot_run(self):
        params = self.parameters()
        path = params.get("path") or ""
        slug = params.get("slug") or "undefined"

        space = self.create_hf_space()
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
