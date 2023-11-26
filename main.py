from PyQt5.QtWidgets import QWidget, QApplication, QListWidgetItem
from PyQt5.uic import loadUi
from PyQt5  import QtCore
import sys

tasks = ["Emails", "Future work", "pog"]

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        loadUi("main.ui",self)
        self.calendarWidget.selectionChanged.connect(self.calendarDateChanged)
        self.updateTaskList()

    def calendarDateChanged(self):
        print("The Calendar Date was Changed")
        dateSelected = self.calendarWidget.selectedDate().toPyDate().strftime("%d-%m")
        print("Date Selected: ",dateSelected)
    def updateTaskList(self):
        for task in tasks:
            item = QListWidgetItem(task)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.listWidget.addItem(item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())