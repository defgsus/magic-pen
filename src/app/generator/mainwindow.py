from functools import partial

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .client import Client
from .generatorwidget import GeneratorWidget
from .statuswidget import StatusWidget


class MainWindow(QMainWindow):

    def __init__(self, geometry: QRect):
        super().__init__()

        self.setWindowTitle(self.tr("The Generator"))

        self.tab_menus = dict()
        self._create_main_menu()
        self._create_widgets()

        self.setGeometry(geometry)

    def _create_main_menu(self):
        menu = self.menuBar().addMenu(self.tr("&File"))

        new_menu = menu.addMenu(self.tr("New"))

        menu.addAction(self.tr("E&xit"), self.slot_exit)

        new_menu.addAction(self.tr("New &Session"), self.slot_new_session, QKeySequence("Ctrl+T"))

    def _create_widgets(self):
        parent = QWidget(self)
        self.setCentralWidget(parent)
        l = QVBoxLayout(parent)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        l.addWidget(self.tab_widget)

        self.status_widget = StatusWidget(self)
        l.addWidget(self.status_widget)

    def slot_exit(self):
        Client.singleton().stop()
        self.close()

    def slot_new_session(self):
        widget = GeneratorWidget(self)
        tab_index = self.tab_widget.addTab(widget, "new session")
        widget.signal_slug_changed.connect(self._on_slug_change)
        widget.prompt_input.setFocus()

    def _on_slug_change(self, widget: QWidget, slug: str):
        for idx in range(self.tab_widget.count()):
            w = self.tab_widget.widget(idx)
            if w == widget:
                self.tab_widget.setTabText(idx, slug)
                break

    def _on_tab_changed(self):
        widget = self.tab_widget.currentWidget()
