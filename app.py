"""
Student Name: Kenneth Ariel Herrera Mendoza
Date Started: April 16th, 2024

-----------------------------------------------------
Task On! is a simple and easy-to-use task manager. Here a step-by-step
guide to unleash all the potential of the application:
    >  At startup, the application shows a login window with a register option.
        The application checks the fields and (if everything is correct) shows
        the main window.
    >  The main window contains three views for the calendar: Day, Week, and 
        Month. There are also buttons to add and show tasks, a mini calendar, and
        a window showing the tasks scheduled for today.
    >  Each calendar view shows the name of the task (if there is any programmed).
        When a task name is clicked a window showing the full information of the 
        task appears with buttons to edit, delete, and set the status to completed.
    >  The show tasks button shows a window containing all the tasks stored for the 
        current user, with filters, a sort by option, and a chart showing the 
        completion status of the user's task.
    >  The application creates a hidden user at the home directory that contains
        the database. 
-----------------------------------------------------
"""

from PyQt5.QtWidgets import (
    QApplication,
    QDateEdit,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QFormLayout,
    QTextEdit,
    QTimeEdit,
    QWidget,
    QLabel,
    QComboBox,
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QDialogButtonBox,
)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QFont, QPalette, QColor
import sys
import os
from pathlib import Path
from calendarWidget import CalendarWidget
from miniCalendarWidget import CalendarPreviewWidget
from calendar import Calendar as Cal
from taskWidgets import TaskListWindow, ErrorDialog
from datetime import datetime
from notifypy import Notify
import sqlite3 as sql

PATH = f"{Path.home()}/.task_on"
if not os.path.exists(f"{PATH}"):
    os.mkdir(f"{PATH}")

conn = sql.connect(f"{PATH}/task_on.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
""")

cursor.execute('''
    CREATE TABLE IF NOT EXISTS task (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_name TEXT NOT NULL,
        content TEXT,
        priority TEXT CHECK (priority IN ('Low', 'Medium', 'High')),
        status TEXT CHECK (status IN ('Pending', 'Completed')),
        date DATE,
        hour INT,
        minute INT,
        user_id INT,
        FOREIGN KEY (user_id)
            REFERENCES user (user_id)
    )
''')


class TaskWindow(QWidget):
    def __init__(self, prt, userid):
        super().__init__(parent=prt)
        self.user_id = userid
        self.setWindowFlag(Qt.WindowType.Window)

        main_layout = QFormLayout()

        self.task_name = QLineEdit()
        main_layout.addRow("Task Name:", self.task_name)

        self.task_content = QTextEdit()
        main_layout.addRow("Task Content:", self.task_content)

        self.deadline = QDateEdit()
        self.deadline.setDate(
            QDate(datetime.now().year, datetime.now().month, datetime.now().day))
        main_layout.addRow("Due Date:", self.deadline)

        self.deadline_hour = QTimeEdit()
        main_layout.addRow("Hour:", self.deadline_hour)

        priorities = QWidget()
        priorities_layout = QHBoxLayout()
        self.low = QRadioButton('Low')
        priorities_layout.addWidget(self.low)
        self.med = QRadioButton('Medium')
        priorities_layout.addWidget(self.med)
        self.high = QRadioButton('High')
        priorities_layout.addWidget(self.high)
        priorities.setLayout(priorities_layout)
        main_layout.addRow("Priority:", priorities)

        self.submit = QPushButton("Submit")
        self.submit.clicked.connect(self.submit_task)
        main_layout.addRow(self.submit)

        self.setLayout(main_layout)

    def submit_task(self):
        day = self.deadline.date().day() if self.deadline.date().day() > 9 else f'0{
            self.deadline.date().day()}'
        month = self.deadline.date().month() if self.deadline.date(
        ).month() > 9 else f"0{self.deadline.date().month()}"
        year = self.deadline.date().year()

        try:
            cursor.execute(f"""
                INSERT INTO task (task_name, content, priority, status, date, hour, minute, user_id)
                VALUES (
                    '{self.task_name.text()}',
                    '{self.task_content.toPlainText()}',
                    '{self.check_rb()}',
                    'Pending',
                    '{year}-{month}-{day}',
                    {self.deadline_hour.time().hour()},
                    {self.deadline_hour.time().minute()},
                    {self.user_id}
                )
            """)
            conn.commit()
            self.close()
        except sql.Error as e:
            dlg = ErrorDialog(self)
            if dlg.exec():
                pass
            else:
                self.close()

    def check_rb(self) -> str:
        if self.low.isChecked():
            return 'Low'
        if self.med.isChecked():
            return 'Medium'
        if self.high.isChecked():
            return 'High'


class Window (QWidget):
    __MONTHS = (
        'January',
        'February',
        'March',
        'April',
        'May',
        'June',
        'July',
        'August',
        'September',
        'October',
        'November',
        'December'
    )
    __DAYS = (
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday'
    )
    __TODAY = datetime.today()

    def __init__(self, user_id):
        super().__init__()
        self.setWindowTitle("Calendar")
        self.task_win = None
        self.add_win = None
        self.user_id = user_id
        self.today_tasks = None
        self.setWindowFlag(Qt.Window)
        # self.setFixedSize(1000, 650)

        # body = QWidget()
        bod_layout = QHBoxLayout()

        main = QWidget()
        main_layout = QVBoxLayout()

        hdr = QWidget()
        # hdr.setMaximumHeight(50)
        hdr_layout = QHBoxLayout()

        l = QLabel('Calendar View:')
        l.setMaximumWidth(100)
        hdr_layout.addWidget(l)

        self.view = QComboBox()
        self.view.addItems(['Day', 'Week', 'Month'])
        self.view.setFixedWidth(100)
        self.view.currentTextChanged.connect(self.change_view)
        hdr_layout.addWidget(self.view)

        self.curMonth = QLabel(
            f"{self.__MONTHS[self.__TODAY.month-1]} {self.__TODAY.year}".upper())
        self.curMonth.setStyleSheet("""
            font-size: 24px;
            font-weight: 900;
            color: #ff920f;
        """)
        hdr_layout.addWidget(self.curMonth)

        self.show_btn = QPushButton("Show Tasks")
        self.show_btn.setFixedWidth(100)
        self.show_btn.clicked.connect(self.show_tasks)
        hdr_layout.addWidget(self.show_btn)

        self.task_btn = QPushButton("Add Task")
        self.task_btn.setFixedWidth(100)
        self.task_btn.clicked.connect(self.new_task)
        hdr_layout.addWidget(self.task_btn)

        hdr.setLayout(hdr_layout)
        main_layout.addWidget(hdr)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_wid)
        self.timer.start()

        # Calendar here ->
        self.calendar = CalendarWidget(self.user_id)

        main_layout.addWidget(self.calendar)
        main.setLayout(main_layout)
        bod_layout.addWidget(main)

        side_pane = QWidget()
        side_pane.setFixedWidth(300)
        pane_layout = QVBoxLayout()

        date = QLabel(f"{self.__DAYS[self.__TODAY.weekday()]} {
                      self.__TODAY.day} {self.__MONTHS[self.__TODAY.month-1][:3]} {self.__TODAY.year}")
        date.setMaximumHeight(50)
        date.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #429b5b;
            border-style: none;
            border-bottom-style: solid;
            border-bottom-width: 1px;
            border-bottom-color: #429b5b;
        """)
        pane_layout.addWidget(date)
        l = QLabel("Scheduled Today:")
        l.setMaximumHeight(30)
        l.setStyleSheet("""
            font-size: 12px;
            font-weight: 700;
        """)
        pane_layout.addWidget(l)

        self.scheduled_tasks = QScrollArea()
        self.container = QWidget()
        self.show_today_tasks()
        self.scheduled_tasks.setWidget(self.container)

        pane_layout.addWidget(self.scheduled_tasks)

        self.mini_calendar = CalendarPreviewWidget(
            self.__TODAY.month, self.__TODAY.day, self.__TODAY.year)
        pane_layout.addWidget(self.mini_calendar)

        side_pane.setLayout(pane_layout)
        bod_layout.addWidget(side_pane)

        self.setLayout(bod_layout)

    def update_wid(self):
        last_updated = os.path.getmtime(f"{PATH}/task_on.db")
        modified_time = datetime.fromtimestamp(last_updated)
        hour = datetime.today().hour
        day = datetime.today().day
        min = datetime.today().minute
        sec = datetime.today().second
        if hour != self.__TODAY.hour:
            self.__TODAY = datetime.today()
            self.change_view()
            self.mini_calendar.render_preview(
                self.__TODAY.month, self.__TODAY.day)
            self.show_today_tasks()
        if day != self.__TODAY.day:
            self.__TODAY = datetime.today()
            self.change_view()
            self.mini_calendar.render_preview(
                self.__TODAY.month, self.__TODAY.day)
            self.show_today_tasks()
        if modified_time.second + 1 == sec and modified_time.minute == min:
            self.change_view()
            self.show_today_tasks()
        self.check_notifications()

    def change_view(self):
        if self.view.currentText().upper() == 'DAY':
            self.calendar.render_day_calendar(
                self.__TODAY.month, self.__TODAY.day, self.__TODAY.year)
        if self.view.currentText().upper() == 'MONTH':
            self.calendar.render_month_calendar(
                self.__TODAY.month, self.__TODAY.day, self.__TODAY.year)
        if self.view.currentText().upper() == 'WEEK':
            self.calendar.render_week_calendar(
                self.__TODAY.month, self.__TODAY.day, self.__TODAY.year)

    def new_task(self):
        if self.add_win is None:
            self.add_win = TaskWindow(self, self.user_id)
            self.add_win.show()
        else:
            self.add_win.close()
            self.add_win = None

    def show_today_tasks(self):
        self.container = QWidget()
        lay = QVBoxLayout()
        lay.setSpacing(4)
        lay.setContentsMargins(10, 5, 0, 5)

        cursor.execute("""
            SELECT task_name, content, date, priority FROM task
            WHERE strftime('%d', date) = ? AND user_id = ?
        """, (f'{self.__TODAY.day if self.__TODAY.day > 9 else f'0{self.__TODAY.day}'}', self.user_id, ))
        tasks = cursor.fetchall()

        for t in tasks:
            t_container = QWidget()
            t_container.setFixedWidth(250)
            t_container.setStyleSheet('''
                background-color: #429b5b;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            ''')
            t_layout = QVBoxLayout()

            for i in range(len(t)):
                l = QLabel(f"{f'Due Date: {t[i]}' if i == 2 else t[i]}")
                l.setWordWrap(True)
                t_layout.addWidget(l)
            t_container.setLayout(t_layout)
            lay.addWidget(t_container)

        self.container.setLayout(lay)
        self.scheduled_tasks.setWidget(self.container)

    def show_tasks(self):
        if self.task_win is None:
            self.task_win = TaskListWindow(self, self.user_id)
            self.task_win.show()
        else:
            self.task_win.close()
            self.task_win = None

    def check_notifications(self):
        cursor.execute("""
            SELECT task_name, content, hour, minute FROM task
            WHERE strftime('%d', date) = ? AND user_id = ? AND (hour = ? AND minute = ?)
        """, (
            f'{self.__TODAY.day if self.__TODAY.day >
                9 else f'0{self.__TODAY.day}'}',
            self.user_id,
            datetime.today().hour,
            datetime.today().minute,
        ))
        tasks = cursor.fetchall()

        for task in tasks:
            if task[2] == datetime.today().hour and task[3] == datetime.today().minute and datetime.today().second == 0:
                self.send_notification(task[0], task[1])

    def send_notification(self, title: str, comment: str) -> None:
        noti = Notify()

        noti.application_name = "Task 🍊n!"
        noti.icon = "./task_on_logo.png"

        noti.title = "You have a task scheduled right now!"
        noti.message = f"The task {title} has come to its due date!\n{comment}"

        noti.timeout = 5000
        noti.send()


class LoginWindow (QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.Window)
        container_lay = QVBoxLayout()
        self.main = QWidget()
        self.container = QWidget()

        self.main_lay = QVBoxLayout()
        self.main.setLayout(self.main_lay)

        container_lay.addWidget(self.main)
        self.login_win()

        self.setLayout(container_lay)

    def login_win(self):
        if self.container is not None:
            self.main_lay.removeWidget(self.container)
        self.container = QWidget()
        container_lay = QVBoxLayout()

        container_lay.addWidget(QLabel("Welcome to Task–🍊n!"))
        qtn = QPushButton('New User? Click here to Register!')
        qtn.setFont(QFont('Arial', 12, QFont.Bold))
        qtn.setStyleSheet("""
            background-color: #00000000;
            color: #429b5b;
        """)
        qtn.clicked.connect(self.register_win)
        container_lay.addWidget(qtn)

        form_widget = QGroupBox()
        form_layout = QFormLayout()

        self.username = QLineEdit()
        form_layout.addRow("Username:", self.username)
        self.passwd = QLineEdit()
        self.passwd.setEchoMode(QLineEdit.Password)
        self.passwd.returnPressed.connect(self.login)
        form_layout.addRow("Password:", self.passwd)

        form_widget.setLayout(form_layout)
        container_lay.addWidget(form_widget)

        login = QPushButton('Login!')
        login.clicked.connect(self.login)
        container_lay.addWidget(login)

        self.container.setLayout(container_lay)
        self.main_lay.addWidget(self.container)

    def register_win(self):
        if self.container is not None:
            self.main_lay.removeWidget(self.container)
        self.container = QWidget()
        container_lay = QVBoxLayout()

        container_lay.addWidget(QLabel("Fill the following to create a user:"))

        form_widget = QGroupBox()
        form_layout = QFormLayout()

        self.username = QLineEdit()
        form_layout.addRow("Username:", self.username)
        self.passwd = QLineEdit()
        self.passwd.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.passwd)
        self.passwd.returnPressed.connect(self.create_user)

        form_widget.setLayout(form_layout)
        container_lay.addWidget(form_widget)

        btns_lay = QHBoxLayout()
        btns_container = QWidget()

        create = QPushButton('Create!')
        create.setFixedWidth(100)
        btns_lay.addWidget(create)
        cancel = QPushButton('Cancel!')
        cancel.setFixedWidth(100)
        btns_lay.addWidget(cancel)

        cancel.clicked.connect(self.login_win)
        create.clicked.connect(self.create_user)

        btns_container.setLayout(btns_lay)
        container_lay.addWidget(btns_container)

        self.container.setLayout(container_lay)
        self.main_lay.addWidget(self.container)

    def create_user(self):
        command = f"""
            INSERT INTO user (username, password)
            VALUES ('{self.username.text()}', '{self.passwd.text()}')
        """

        if self.username.text() == "" or self.passwd.text() == "":
            dlg = QDialog(parent=self)

            dlg.setWindowTitle("Task 🍊n! says: Oops!")

            dlg_lay = QVBoxLayout()

            dlg_lay.addWidget(
                QLabel('Something went wrong :c\nPlease provide all the requirements needed'))
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
            btn_box.accepted.connect(dlg.close)
            dlg_lay.addWidget(btn_box)

            dlg.setLayout(dlg_lay)

            if dlg.exec():
                pass
        else:
            try:
                cursor.execute(command)
                conn.commit()
                self.login()
            except sql.Error as e:
                dlg = QDialog(parent=self)

                dlg.setWindowTitle("Task 🍊n! says: Oops!")

                dlg_lay = QVBoxLayout()

                dlg_lay.addWidget(
                    QLabel('Something went wrong :c\nPlease check that you username is unique!'))
                btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
                btn_box.accepted.connect(dlg.close)
                dlg_lay.addWidget(btn_box)

                dlg.setLayout(dlg_lay)

                if dlg.exec():
                    pass

    def login(self):
        query = f"""
            SELECT * FROM user WHERE username = '{self.username.text()}'
        """
        cursor.execute(query)
        user = cursor.fetchone()

        if user and user[2] == self.passwd.text():
            self.main_win = Window(user[0])
            self.main_win.show()
            self.close()
        else:
            dlg = QDialog(parent=self)

            dlg.setWindowTitle("Task 🍊n! says: Wait!")

            dlg_lay = QVBoxLayout()

            dlg_lay.addWidget(
                QLabel('Something went wrong :c\nPlease check your username and/or your password\nIf you do not have a username, click register!'))
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
            btn_box.accepted.connect(dlg.close)
            dlg_lay.addWidget(btn_box)

            dlg.setLayout(dlg_lay)

            if dlg.exec():
                pass


# takatakatka calendario takatakataka color takatakataka numeritos
app = QApplication(sys.argv)
palette = QPalette()
palette.setColor(QPalette.Window, QColor(253, 254, 255))
palette.setColor(QPalette.WindowText, QColor(155, 156, 157))
palette.setColor(QPalette.Text, QColor(155, 156, 157))
app.setPalette(palette)

app.setStyleSheet("""
    QLabel#special-label {
        background-color: #ffa131;
        color: #ffffff;
        font-size: 18px;
        font-weight: bold;
        border-radius: 25%;
    }
    QPushButton {
        background-color: #ffa131;
        border-style: none;
        border-radius: 10px;
        padding: 10px;
        color: white;
        font-weight: 900;
    }
    QLineEdit, QTextEdit, QDateEdit, QTimeEdit {
        background-color: #ffffff;
        color: black;
        border-style: inset;
        border-width: 1px;
        border-color: black;
    }
""")

win = LoginWindow()
win.show()

app.exec()

conn.commit()
conn.close()
