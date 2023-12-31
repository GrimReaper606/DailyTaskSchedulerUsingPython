import sqlite3
from PyQt5.QtWidgets import QWidget, QApplication, QListWidgetItem, QMessageBox
from PyQt5.uic import loadUi
from PyQt5 import QtCore, QtGui 
from datetime import datetime, timedelta
from win10toast import ToastNotifier
import sys

class NotificationThread(QtCore.QThread):
    notification_signal = QtCore.pyqtSignal(str, int, str)

    def __init__(self, task, priority, reminder_time):
        super(NotificationThread, self).__init__()
        self.task = task
        self.priority = priority
        self.reminder_time = reminder_time
        self._is_running = True

    def run(self):
        self.schedule_notification()

    def stop(self):
        self._is_running = False

    def schedule_notification(self):
        reminder_datetime = datetime.combine(datetime.today(), datetime.strptime(self.reminder_time, "%H:%M:%S").time())
        current_datetime = datetime.now()

        if self.priority == 1:
            time_difference = reminder_datetime - current_datetime - timedelta(seconds=20)
        elif self.priority == 2:
            time_difference = reminder_datetime - current_datetime - timedelta(seconds=10)
        else:
            time_difference = reminder_datetime - current_datetime - timedelta(seconds=5)

        seconds_until_notification = max(0, int(time_difference.total_seconds()))

        while self._is_running and seconds_until_notification > 0:
            self.sleep(1)
            seconds_until_notification -= 1

        if self._is_running:
            # Schedule the notification using win10toast
            toaster = ToastNotifier()
            toaster.show_toast(
                f"Reminder for Task: {self.task}",
                f"Priority: {self.priority}\nTime: {self.reminder_time}",
                duration=5,
            )

    def __del__(self):
        self.wait()

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        loadUi("main.ui", self)
        self.setWindowTitle("Daily Task Scheduler")  # Set your desired app name
        self.setWindowIcon(QtGui.QIcon('icon.svg'))  # Set the path to your icon file
        self.calendarWidget.selectionChanged.connect(self.calendarDateChanged)
        self.calendarDateChanged()
        self.saveButton.clicked.connect(self.saveChanges)
        self.addButton.clicked.connect(self.addNewTask)
        self.notification_threads = []

    def calendarDateChanged(self):
        dateSelected = self.calendarWidget.selectedDate().toPyDate()
        self.updateTaskList(dateSelected)

    def updateTaskList(self, date):
        self.listWidget.clear()

        db = sqlite3.connect("data.db")
        cursor = db.cursor()
        query = "SELECT task, completed, priority, reminder_time FROM tasks WHERE date = ? ORDER BY priority ASC"
        row = (date,)
        results = cursor.execute(query, row).fetchall()
        for result in results:
            item = self.createTaskItem(result)
            self.listWidget.addItem(item)

            # Schedule reminders for tasks with specific priorities
            self.schedule_notification(result)

    def createTaskItem(self, result):
        task, completed, priority, reminder_time = result
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

    def addNewTask(self):
        db = sqlite3.connect("data.db")
        cursor = db.cursor()

        newTask = str(self.taskLineEdit.text())
        date = self.calendarWidget.selectedDate().toPyDate()
        priority = self.prioritySpinBox.value()
        reminder_time = self.timeEdit.time().toString("HH:mm:ss")

        query = "INSERT INTO tasks(task, completed, date, priority, reminder_time) VALUES (?, ?, ?, ?, ?)"
        row = (newTask, "NO", date, priority, reminder_time)

        cursor.execute(query, row)
        db.commit()
        self.updateTaskList(date)
        self.taskLineEdit.clear()

        # After adding a new task, show a scheduled notification using a separate thread
        notification_thread = NotificationThread(newTask, priority, reminder_time)
        self.notification_threads.append(notification_thread)
        notification_thread.start()

        # Remove completed threads
        self.notification_threads = [thread for thread in self.notification_threads if thread.isRunning()]

    def schedule_notification(self, result):
        task, completed, priority, reminder_time = result
        current_time = datetime.now().strftime("%H:%M:%S")
        
        if not completed and current_time < reminder_time:
            # Check if the reminder time is in the future
            notification_thread = NotificationThread(task, priority, reminder_time)
            self.notification_threads.append(notification_thread)
            notification_thread.start()

            # Remove completed threads
            self.notification_threads = [thread for thread in self.notification_threads if thread.isRunning()]

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
