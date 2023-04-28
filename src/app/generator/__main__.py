import sys
from PyQt5.QtWidgets import *


from src.app.generator.mainwindow import MainWindow
from src.app.generator.client import Client

app = QApplication(sys.argv)

win = MainWindow()
win.show()

result = app.exec_()

Client.singleton().stop()
sys.exit(result)
