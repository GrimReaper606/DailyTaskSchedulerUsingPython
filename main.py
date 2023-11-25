import typing
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.uic import loadUi
import sys

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        loadUi("main.ui",self)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())