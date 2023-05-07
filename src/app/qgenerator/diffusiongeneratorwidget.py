from functools import partial
import unicodedata

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from src.hf import StableDiffusionSpace
from .client import Client
from .imagelistwidget import ImageListWidget
from .generatorwidgetbase import GeneratorWidgetBase, sluggify


class DiffusionGeneratorWidget(GeneratorWidgetBase):

    def set_focus(self):
        self.prompt_input.setFocus()

    def _create_control_widgets(self):
        self.prompt_input = QPlainTextEdit(self)
        self.prompt_input.setMaximumHeight(180)
        self.prompt_input.textChanged.connect(self.slot_on_prompt_change)
        self._add_control(self.tr("prompt"), self.prompt_input)

        self.negative_prompt_input = QPlainTextEdit(self)
        self.negative_prompt_input.setMaximumHeight(60)
        self._add_control(self.tr("negative prompt"), self.negative_prompt_input)

        guidance_control = QWidget(self)
        lh = QHBoxLayout(guidance_control)
        self.guidance_input = QSlider(Qt.Horizontal, self)
        self.guidance_input.setRange(0, 50)
        self.guidance_input.setValue(9)
        self.guidance_label = QLabel(str(self.guidance_input.value()), self)
        self.guidance_input.valueChanged.connect(self.slot_on_guidance_change)
        lh.addWidget(self.guidance_label)
        lh.addWidget(self.guidance_input)
        self._add_control(self.tr("guidance"), guidance_control)

    def parameters(self) -> dict:
        return {
            **super().parameters(),
            "prompt": self.prompt_input.toPlainText().strip(),
            "negative_prompt": self.negative_prompt_input.toPlainText().strip(),
            "guidance": self.guidance_input.value(),
        }

    def set_parameters(self, params: dict):
        self._ignore_slug_change = True
        self.path_input.setText(params.get("path") or "")
        self.prompt_input.setPlainText(params.get("prompt") or "")
        self.slug_input.setText(params.get("slug") or "")
        self.negative_prompt_input.setPlainText(params.get("negative_prompt") or "")
        self.guidance_input.setValue(params.get("guidance") or "")
        self.auto_update_slug_checkbox.setChecked(
            sluggify(self.prompt_input.toPlainText()) == self.slug_input.text()
        )
        self._ignore_slug_change = False

    def slot_on_prompt_change(self):
        if self.auto_update_slug_checkbox.isChecked():
            self._ignore_slug_change = True
            self.slug_input.setText(sluggify(self.prompt_input.toPlainText()))
            self._ignore_slug_change = False

    def slot_on_guidance_change(self):
        self.guidance_label.setText(str(self.guidance_input.value()))

    def create_hf_space(self) -> StableDiffusionSpace:
        params = self.parameters()
        params.pop("path")
        params.pop("slug")

        return StableDiffusionSpace(**params)
