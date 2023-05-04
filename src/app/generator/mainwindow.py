import json
from functools import partial
from typing import List
from pathlib import Path

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .client import Client
from .generatorwidgetbase import GeneratorWidgetBase
from .diffusiongeneratorwidget import DiffusionGeneratorWidget
from .barkgeneratorwidget import BarkGeneratorWidget
from .statuswidget import StatusWidget


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(self.tr("The Generator"))
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint, True)

        self.sessions: List[GeneratorWidgetBase] = []
        self.tab_menus = dict()
        self._create_main_menu()
        self._create_widgets()

        self.slot_load_sessions()

    def _create_main_menu(self):
        menu = self.menuBar().addMenu(self.tr("&File"))

        new_menu = menu.addMenu(self.tr("New"))

        menu.addAction(self.tr("E&xit"), self.slot_exit)

        new_menu.addAction(self.tr("New &Diffusion Session"), self.slot_new_diffusion_session, QKeySequence("Ctrl+T"))
        new_menu.addAction(self.tr("New &Bark Session"), self.slot_new_bark_session, QKeySequence("Ctrl+B"))

    def _create_widgets(self):
        parent = QWidget(self)
        self.setCentralWidget(parent)
        l = QVBoxLayout(parent)

        self.tab_widget = QTabWidget(parent)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        l.addWidget(self.tab_widget)

        self.status_widget = StatusWidget(parent)
        l.addWidget(self.status_widget)

    def close(self) -> bool:
        if not super().close():
            return False

        # self.slot_save_sessions()
        # Client.singleton().stop()
        return True

    def slot_exit(self):
        self.close()

    def config_filename(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent.parent / ".generator-config.json"

    def slot_save_sessions(self):
        sessions = []
        for gen in self.sessions:
            params = gen.parameters()
            params["_class"] = type(gen).__name__
            sessions.append(params)

        data = {
            "sessions": sessions,
        }
        self.config_filename().write_text(json.dumps(data, indent=2))

    def slot_load_sessions(self):
        try:
            data = json.loads(self.config_filename().read_text())
        except (IOError, json.JSONDecodeError):
            return

        self.tab_widget.clear()
        self.sessions.clear()

        for session in data["sessions"]:
            _class = session.pop("_class", None)
            if not _class or _class == "DiffusionGeneratorWidget":
                widget = DiffusionGeneratorWidget(self)
            elif _class == "BarkGeneratorWidget":
                widget = BarkGeneratorWidget(self)
            else:
                print("UNKNOWN GENERATOR CLASS:", _class)
                continue

            self._add_generator_widget(widget)
            widget.set_parameters(session)

    def slot_new_diffusion_session(self):
        widget = DiffusionGeneratorWidget(self)
        tab_index = self._add_generator_widget(widget)
        self.tab_widget.setCurrentIndex(tab_index)

    def slot_new_bark_session(self):
        widget = BarkGeneratorWidget(self)
        tab_index = self._add_generator_widget(widget)
        self.tab_widget.setCurrentIndex(tab_index)

    def _add_generator_widget(self, widget: GeneratorWidgetBase) -> int:
        tab_index = self.tab_widget.addTab(widget, "new session")
        widget.signal_slug_changed.connect(self._on_slug_change)
        widget.set_focus()
        self.sessions.append(widget)
        self._on_slug_change(widget, widget.slug_input.text())
        return tab_index

    def _on_slug_change(self, widget: QWidget, slug: str):
        for idx in range(self.tab_widget.count()):
            w = self.tab_widget.widget(idx)
            if w == widget:
                self.tab_widget.setTabText(idx, slug)
                break

    def _on_tab_changed(self):
        widget = self.tab_widget.currentWidget()
