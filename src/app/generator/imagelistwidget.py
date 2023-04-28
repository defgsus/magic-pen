import json
import os
from functools import partial
from pathlib import Path
from typing import List, Union

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .client import Client


class FileListModel(QAbstractListModel):
    def __init__(self, files: List[dict], parent=None, *args):
        QAbstractListModel.__init__(self, parent, *args)
        self.files = files
        self.data_cache = {}

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.files)

    def data(self, index: QModelIndex, role=None):
        if index.isValid():
            file = self.files[index.row()]

            if role == Qt.DecorationRole:
                # print(index.row())
                return QPixmap(file["path"]).scaled(150, 150)

            if role == Qt.DisplayRole:
                lines = [file["name"]]
                for key, value in self.get_file_data(file["path"]).items():
                    if key == "negative_prompt" and not value:
                        continue
                    if key == "guidance" and value == 9:
                        continue
                    if len(lines) == 1:
                        lines.append("")
                    lines.append(f"{key}: {value}")

                return QVariant("\n".join(lines))

        return QVariant()

    def get_file_data(self, path: str) -> dict:
        if path not in self.data_cache:
            path, ext = os.path.splitext(path)
            path = Path(f"{path}.json")
            try:
                data = json.loads(path.read_text())
            except (IOError, json.JSONDecodeError):
                data = {}

            self.data_cache[path] = data
        return self.data_cache[path]


class ListView(QListView):

    signal_index_changed = pyqtSignal(QModelIndex)

    def selectionChanged(self, selected: QItemSelection, deselected):
        indexes = selected.indexes()
        if indexes:
            index = indexes[0]
        else:
            index = QModelIndex()
        self.signal_index_changed.emit(index)
        return super().selectionChanged(selected, deselected)


class ImageListWidget(QWidget):

    signal_image_clicked = pyqtSignal(dict)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_widgets()
        self.set_path(Client.singleton().result_path)

    def _create_widgets(self):
        self.data_model = FileListModel([], self)

        lv = QVBoxLayout(self)
        self.path_label = QLabel(self)
        lv.addWidget(self.path_label)

        lh = QHBoxLayout()
        lv.addLayout(lh)

        self.image_label = QLabel(self)
        lh.addWidget(self.image_label)

        self.list_widget = ListView(self)
        lh.addWidget(self.list_widget)
        self.list_widget.setModel(self.data_model)
        #self.list_widget.setLayoutMode(QListView.Batched)
        #self.list_widget.setViewMode(QListView.IconMode)
        #self.list_widget.setBatchSize(10)
        self.list_widget.setGridSize(QSize(150, 150))
        self.list_widget.signal_index_changed.connect(self._slot_clicked)

    def set_path(self, path: Union[str, Path]):
        path = Path(path)
        self.path_label.setText(str(path))

        try:
            all_entries = sorted(
                os.scandir(path),
                key=lambda e: e.stat().st_mtime,
                reverse=True,
            )
        except FileNotFoundError:
            all_entries = []

        files_data = []
        for entry in all_entries:
            if not entry.name.startswith('.') and entry.is_file():
                if not entry.name.endswith(".json"):
                    files_data.append({
                        "path": entry.path,
                        "name": entry.name,
                    })

        self.data_model = FileListModel(files_data, self)
        self.list_widget.setModel(self.data_model)

        if files_data:
            self.image_label.setPixmap(QPixmap(files_data[0]["path"]))
        else:
            self.image_label.clear()

    def _slot_clicked(self, index: QModelIndex):
        # from .imagewindow import ImageWindow
        if index.isValid():
            file = self.data_model.files[index.row()]
            self.image_label.setPixmap(QPixmap(file["path"]))
        else:
            self.image_label.clear()
        #window = ImageWindow(file["path"])
        #window.show()

