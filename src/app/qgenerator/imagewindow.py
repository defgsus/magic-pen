import json
import os
from functools import partial
from pathlib import Path
from typing import List, Union

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class ImageWindow(QWidget):

    def __init__(self, path: Union[str, Path], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = Path(path)
        self.resize(400, 300)

        self._create_widgets()

    def _create_widgets(self):
        from .imagelistwidget import ImageListWidget
        #parent = QWidget(self)
        #self.setCentralWidget(parent)
        l = QHBoxLayout(self)

        self.image_widget = QLabel(self)
        l.addWidget(self.image_widget)
        self.image_widget.setPixmap(QPixmap(str(self.path)))

        self.image_list = ImageListWidget(150, self)
        l.addWidget(self.image_list)
        self.image_list.set_path(self.path.parent)
