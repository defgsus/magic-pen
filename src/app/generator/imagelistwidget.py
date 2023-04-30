import json
import os
from functools import partial
from pathlib import Path
from typing import List, Union

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .client import Client


def meta_filename(path: Union[str, Path]) -> Path:
    path, ext = os.path.splitext(str(path))
    return Path(f"{path}.json")


class FileListModel(QAbstractListModel):
    def __init__(self, files: List[dict], parent=None, *args):
        QAbstractListModel.__init__(self, parent, *args)
        self.files = files
        self.data_cache = {}

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.files)

    def data(self, index: QModelIndex, role=None):
        if index.isValid():
            file = self.get_file(index)

            if role == Qt.DecorationRole:
                # print(index.row())
                return QPixmap(file["path"]).scaled(150, 150)

            if role == Qt.DisplayRole or role == Qt.ToolTipRole:
                return QVariant(self.get_param_string(file))

        return QVariant()

    def get_file(self, index: QModelIndex) -> dict:
        return self.files[index.row()]

    def get_param_string(self, file: dict) -> str:
        lines = [file["name"]]
        for key, value in self.get_file_meta(file["path"]).items():
            if key == "negative_prompt" and not value:
                continue
            if key == "guidance" and value == 9:
                continue
            if len(lines) == 1:
                lines.append("")
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def get_file_meta(self, path: str) -> dict:
        if path not in self.data_cache:
            path = meta_filename(path)
            try:
                data = json.loads(path.read_text())
            except (IOError, json.JSONDecodeError):
                data = {}

            self.data_cache[path] = data
        return self.data_cache[path]

    def delete_file(self, index: QModelIndex):
        path = Path(self.get_file(index)["path"])
        if path.exists():
            os.remove(path)

        path = meta_filename(path)
        if path.exists():
            os.remove(path)

        self.files.pop(index.row())
        self.dataChanged.emit(self.index(0), self.index(len(self.files)))


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
        self.path = Client.singleton().result_path
        self.set_path(self.path)

    def _create_widgets(self):
        self.data_model = FileListModel([], self)

        lv = QVBoxLayout(self)
        self.path_label = QLabel(self)
        lv.addWidget(self.path_label)

        lh = QHBoxLayout()
        lv.addLayout(lh)

        lv2 = QVBoxLayout()
        lh.addLayout(lv2)

        self.toolbar = QToolBar(self)
        action = QAction("❌", self.toolbar)
        action.setShortcut(Qt.Key_D)
        action.setToolTip(self.tr("Delete image (press D)"))
        action.triggered.connect(self._slot_delete_action)

        self.toolbar.addAction(action)
        lv2.addWidget(self.toolbar)

        self.image_label = QLabel(self)
        lv2.addWidget(self.image_label)

        self.list_widget = ListView(self)
        lh.addWidget(self.list_widget)
        self.list_widget.setModel(self.data_model)
        #self.list_widget.setLayoutMode(QListView.Batched)
        #self.list_widget.setViewMode(QListView.IconMode)
        #self.list_widget.setBatchSize(10)
        self.list_widget.setGridSize(QSize(150, 150))
        self.list_widget.signal_index_changed.connect(self._slot_clicked)

    def _slot_delete_action(self, down: bool):
        index = self.list_widget.currentIndex()
        if index.isValid():
            self.slot_delete_image(index)

    def slot_delete_image(self, index: QModelIndex()):
        if not index.isValid():
            return

        file = self.data_model.get_file(index)
        button = QMessageBox.question(
            self,
            self.tr("Delete File"),
            f"Delete {file['path']}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if button == QMessageBox.Yes:
            self.data_model.delete_file(index)
            if self.data_model.files:
                new_index = self.data_model.index(
                    min(len(self.data_model.files) - 1, index.row())
                )
            else:
                new_index = QModelIndex()
            self.list_widget.setCurrentIndex(new_index)
            self._slot_clicked(new_index)

    def set_path(self, path: Union[str, Path]):
        previous_path = None
        index = self.list_widget.currentIndex()
        if index.isValid():
            previous_path = self.data_model.get_file(index)["path"]

        self.path = Path(path)
        self.path_label.setText(str(self.path))

        try:
            all_entries = sorted(
                os.scandir(self.path),
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

        if self.data_model.files:
            new_index = None
            if previous_path:
                for i, file in enumerate(self.data_model.files):
                    if file["path"] == previous_path:
                        new_index = self.data_model.index(i)
                        break

            if new_index is None:
                new_index = self.data_model.index(0)

            self.list_widget.setCurrentIndex(new_index)
            self._slot_clicked(new_index)

        else:
            self._slot_clicked(QModelIndex())

    def _slot_clicked(self, index: QModelIndex):
        if index.isValid():
            file = self.data_model.get_file(index)
            self.image_label.setPixmap(QPixmap(file["path"]))
        else:
            self.image_label.clear()
