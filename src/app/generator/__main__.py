import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import qdarkstyle

from src.app.generator.mainwindow import MainWindow
from src.app.generator.client import Client


def main():
    app = QApplication(sys.argv)

    app.setStyleSheet(qdarkstyle.load_stylesheet())
    screen = app.primaryScreen()

    win = MainWindow(screen.availableGeometry())
    win.show()

    result = app.exec_()

    Client.singleton().stop()
    sys.exit(result)


if __name__ == "__main__":
    main()