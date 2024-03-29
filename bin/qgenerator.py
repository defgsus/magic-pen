import sys
import time

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import qdarkstyle

from src.app.qgenerator.mainwindow import MainWindow
from src.app.qgenerator.client import Client


def main():
    app = QApplication(sys.argv)

    app.setStyleSheet(qdarkstyle.load_stylesheet())
    screen = app.primaryScreen()

    win = MainWindow()
    app.aboutToQuit.connect(win.slot_save_sessions)

    win.showMaximized()
    time.sleep(.1)
    win.setGeometry(screen.availableGeometry())

    result = app.exec_()

    Client.singleton().stop()
    sys.exit(result)


if __name__ == "__main__":
    main()