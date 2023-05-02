import json
import os
from functools import partial
from pathlib import Path
from typing import List, Union, Optional, Iterable

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

            if role == Qt.ItemDataRole:
                return QVariant(file["path"])

            if role == Qt.SizeHintRole:
                return QVariant(QSize(300, 150))

        return QVariant()

    def mimeData(self, indexes: Iterable[QModelIndex]) -> QMimeData:
        data = QMimeData()
        for index in indexes:
            if index.isValid():
                file = self.files[index.row()]
                data.setText(file["path"])
                data.setData("text/uri-list", f'file://{file["path"]}\r\n'.encode())
                # data.setImageData(QImage(self.files[index.row()]["path"]))
                _, ext = os.path.splitext(file["path"])
                if ext == ".jpg":
                    ext = ".jpeg"
                with open(self.files[index.row()]["path"], "rb") as fp:
                    data.setData(f"image/{ext[1:]}", fp.read())
            break
        return data

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        flags = super().flags(index)
        return flags | Qt.ItemIsDragEnabled

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
            meta_path = meta_filename(path)
            try:
                data = json.loads(meta_path.read_text())
            except (IOError, json.JSONDecodeError):
                data = {}

            self.data_cache[path] = data
        return self.data_cache[path]

    def set_file_meta(self, path: str, meta: dict):
        meta_path = meta_filename(path)
        meta_path.write_text(json.dumps(meta, indent=2))
        self.data_cache[path] = meta

    def delete_file(self, index: QModelIndex):
        path = Path(self.get_file(index)["path"])
        if path.exists():
            os.remove(path)

        path = meta_filename(path)
        if path.exists():
            os.remove(path)

        self.files.pop(index.row())
        self.dataChanged.emit(self.index(0), self.index(len(self.files)))

    def rate_image(self, index: QModelIndex, rating: int):
        file = self.get_file(index)
        meta = self.get_file_meta(file["path"]).copy()
        if rating != 0:
            meta["rating"] = rating
        else:
            meta.pop("rating", None)
        self.set_file_meta(file["path"], meta)


class FilterFileListModel(QSortFilterProxyModel):

    def __init__(self, parent: Optional[QObject]):
        super().__init__(parent)
        self._rate_filter = 0

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if not self._rate_filter:
            return True
        if source_row >= len(self.sourceModel().files):
            return False
        file = self.sourceModel().files[source_row]
        meta = self.sourceModel().get_file_meta(file["path"])
        return (meta.get("rating") or 0) >= self._rate_filter

    def set_rate_filter(self, rating: int):
        self._rate_filter = rating
        self.invalidateFilter()


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
        self.filter_model = FilterFileListModel(self)
        self.filter_model.setSourceModel(self.data_model)

        lv = QVBoxLayout(self)
        lh = QHBoxLayout()
        lv.addLayout(lh)

        self.path_label = QLabel(self)
        lh.addWidget(self.path_label)

        lh.addStretch(1)

        lh.addWidget(QLabel(self.tr("rating >=")))
        self.rate_filter = QSpinBox(self)
        lh.addWidget(self.rate_filter)
        self.rate_filter.setRange(0, 5)
        self.rate_filter.valueChanged.connect(self._slot_rate_filter)

        lh.addStretch(1)

        self.count_label = QLabel(f"0 files", self)
        lh.addWidget(self.count_label)

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

        self.rate_actions = []
        group = QActionGroup(self.toolbar)
        for i in range(6):
            action = QAction(str(i), self.toolbar)
            action.setShortcut(Qt.Key_0 + i)
            action.setToolTip(self.tr(f"Rate image (press {i})"))
            action.setCheckable(True)
            action.triggered.connect(partial(self._slot_rate_clicked, i))
            group.addAction(action)
            self.toolbar.addAction(action)
            self.rate_actions.append(action)

        self.toolbar.addAction(action)
        lv2.addWidget(self.toolbar)

        self.image_label = QLabel(self)
        lv2.addWidget(self.image_label)

        self.list_widget = ListView(self)
        lh.addWidget(self.list_widget)
        self.list_widget.setModel(self.filter_model)
        self.list_widget.setDragEnabled(True)
        self.list_widget.setDragDropMode(QAbstractItemView.DragDrop)
        self.list_widget.setWordWrap(True)
        #self.list_widget.setLayoutMode(QListView.Batched)
        #self.list_widget.setViewMode(QListView.IconMode)
        #self.list_widget.setBatchSize(10)
        #self.list_widget.setGridSize(QSize(150, 150))
        self.list_widget.signal_index_changed.connect(self._slot_clicked)

    def num_files(self) -> int:
        return self.filter_model.rowCount()

    def _slot_delete_action(self, down: bool):
        index = self.list_widget.currentIndex()
        if index.isValid():
            self.slot_delete_image(index)

    def _slot_rate_clicked(self, rating: int, down: bool):
        self.slot_rate_image(rating)

    def _slot_rate_filter(self, rating: int):
        self.filter_model.set_rate_filter(rating)
        self.count_label.setText(f"{self.num_files()} files")

    def slot_rate_image(self, rating: int):
        proxy_index = self.list_widget.currentIndex()
        if not proxy_index.isValid():
            return

        source_index = self.filter_model.mapToSource(proxy_index)
        self.data_model.rate_image(source_index, rating)
        self.filter_model.invalidateFilter()

    def slot_delete_image(self, proxy_index: QModelIndex()):
        if not proxy_index.isValid():
            return
        source_index = self.filter_model.mapToSource(proxy_index)

        file = self.data_model.get_file(source_index)
        button = QMessageBox.question(
            self,
            self.tr("Delete File"),
            f"Delete {file['path']}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if button == QMessageBox.Yes:
            self.data_model.delete_file(source_index)
            if self.num_files():
                new_index = self.filter_model.index(
                    max(0, min(self.num_files() - 1, proxy_index.row() - 1)),
                    0
                )
            else:
                new_index = QModelIndex()
            self.list_widget.setCurrentIndex(new_index)
            self._slot_clicked(new_index)

    def set_path(self, path: Union[str, Path]):
        previous_path = None
        index = self.list_widget.currentIndex()
        if index.isValid():
            index = self.filter_model.mapToSource(index)
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
        self.filter_model.setSourceModel(self.data_model)
        self.filter_model.invalidateFilter()
        self.count_label.setText(f"{self.num_files()} files")

        if self.num_files():
            new_index = None
            if previous_path:
                for i, file in enumerate(self.data_model.files):
                    if file["path"] == previous_path:
                        new_index = self.data_model.index(i)
                        break

            if new_index is None:
                new_index = self.data_model.index(0)

            new_index = self.filter_model.mapFromSource(new_index)
            self.list_widget.setCurrentIndex(new_index)
            self._slot_clicked(new_index)

        else:
            self._slot_clicked(QModelIndex())

    def _slot_clicked(self, proxy_index: QModelIndex):
        if proxy_index.isValid():
            source_index = self.filter_model.mapToSource(proxy_index)
            file = self.data_model.get_file(source_index)
            self.image_label.setPixmap(QPixmap(file["path"]))

            meta = self.data_model.get_file_meta(file["path"])
            rating = meta.get("rating") or 0
            if rating >= 0 and rating < len(self.rate_actions):
                self.rate_actions[rating].setChecked(True)
            else:
                self.rate_actions[0].setChecked(True)

        else:
            self.image_label.clear()
