import sqlite3
from PyQt5.QtWidgets import QWidget, QApplication, QListWidgetItem, QMessageBox
from PyQt5.uic import loadUi
from PyQt5 import QtCore, QtGui
from plyer import notification 
import sys

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        loadUi("main.ui", self)
        self.calendarWidget.selectionChanged.connect(self.calendarDateChanged)
        self.calendarDateChanged()
        self.saveButton.clicked.connect(self.saveChanges)
        self.addButton.clicked.connect(self.addNewTask)

    def calendarDateChanged(self):
        print("The Calendar Date was Changed")
        dateSelected = self.calendarWidget.selectedDate().toPyDate()
        print("Date Selected: ", dateSelected)
        self.updateTaskList(dateSelected)

    def updateTaskList(self, date):
        self.listWidget.clear()

        db = sqlite3.connect("data.db")
        cursor = db.cursor()
        query = "SELECT task, completed, priority FROM tasks WHERE date = ? ORDER BY priority ASC"
        row = (date,)
        results = cursor.execute(query, row).fetchall()
        for result in results:
            item = self.createTaskItem(result)
            self.listWidget.addItem(item)

    def createTaskItem(self, result):
        task, completed, priority = result
        item = QListWidgetItem(str(task))
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(QtCore.Qt.Checked if completed == "YES" else QtCore.Qt.Unchecked)

        # Set background color based on priority using a gradient
        gradient = self.getPriorityGradient(priority)
        brush = QtGui.QBrush(gradient)
        item.setBackground(brush)

        return item

    def getPriorityGradient(self, priority):
        gradient = QtGui.QLinearGradient(0, 0, 100, 0)  # Define a linear gradient from left to right

        if priority == 1:
            gradient.setColorAt(0, QtGui.QColor(255, 0, 0))  # Red for high priority
            gradient.setColorAt(1, QtGui.QColor(255, 150, 150))  # Lighter red
        elif priority == 2:
            gradient.setColorAt(0, QtGui.QColor(255, 255, 0))  # Yellow for medium priority
            gradient.setColorAt(1, QtGui.QColor(255, 255, 150))  # Lighter yellow
        else:
            gradient.setColorAt(0, QtGui.QColor(255, 255, 255))  # Default color for low priority
            gradient.setColorAt(1, QtGui.QColor(240, 240, 240))  # Lighter gray

        return gradient

    def saveChanges(self):
        db = sqlite3.connect("data.db")
        cursor = db.cursor()
        date = self.calendarWidget.selectedDate().toPyDate()

        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            task = item.text()
            if item.checkState() == QtCore.Qt.Checked:
                query = "UPDATE tasks SET completed = 'YES' WHERE task = ? AND date = ?"
            else:
                query = "UPDATE tasks SET completed = 'NO' WHERE task = ? AND date = ?"
            row = (task, date,)
            cursor.execute(query, row)
        db.commit()

        messageBox = QMessageBox()
        messageBox.setText("Changes Saved.")
        messageBox.setStandardButtons(QMessageBox.Ok)
        messageBox.exec()
        completed_tasks = [item.text() for item in self.listWidget.findItems("", QtCore.Qt.MatchContains)]
        if completed_tasks:
            notification_title = "Completed Tasks"
            notification_text = f"{len(completed_tasks)} tasks completed!"
            notification.notify(
                title=notification_title,
                message=notification_text,
                app_icon=None,  # e.g., 'path/to/icon.png'
                timeout=10,  # seconds
            )
    
    def addNewTask(self):
        db = sqlite3.connect("data.db")
        cursor = db.cursor()

        newTask = str(self.taskLineEdit.text())
        date = self.calendarWidget.selectedDate().toPyDate()
        priority = self.prioritySpinBox.value()  # Assuming you have a QSpinBox for priority.
        reminder_time = self.timeEdit.time().toString("HH:mm:ss")

        query = "INSERT INTO tasks(task, completed, date, priority,reminder_time) VALUES (?, ?, ?, ?, ?)"
        row = (newTask, "NO", date, priority, reminder_time)

        cursor.execute(query, row)
        db.commit()
        self.updateTaskList(date)
        self.taskLineEdit.clear()

        notification_title = "New Task Added"
        notification_text = f"Task '{newTask}' added on {date}"
        notification.notify(
            title=notification_title,
            message=notification_text,
            app_icon=None,  # e.g., 'path/to/icon.png'
            timeout=10,  # seconds
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())