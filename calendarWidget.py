from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QScrollArea,
    QWidget,
    QLabel,
    QComboBox,
    QGroupBox,
    QBoxLayout,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QFormLayout,
    QLineEdit,
    QDateEdit,
    QTimeEdit,
    QTextEdit,
    QRadioButton,
    QPushButton
)
from builtins import filter
from PyQt5.QtCore import QDate, Qt, QTimer, QTime
from PyQt5.QtGui import QCloseEvent, QPalette, QColor, QFont
import sys
from calendar import Calendar as Cal
from datetime import datetime
import os
import sqlite3
from pathlib import Path
from taskWidgets import Task, TaskInfo

PATH = f"{Path.home()}/.task_on"

conn = sqlite3.connect(f"{PATH}/task_on.db")
cursor = conn.cursor()


class CalendarWidget(QWidget):
    __DAYS = (
        'Mon',
        'Tue',
        'Wed',
        'Thu',
        'Fri',
        'Sat',
        'Sun',
    )

    def __init__(self, user_id):
        super().__init__()
        self.main_lay = QVBoxLayout()
        self.main_lay.setSpacing(0)
        self.main_lay.setContentsMargins(5, 0, 5, 0)
        self.main_widget = None
        self.userid = user_id
        # self.setFixedSize(500, 600)
        # self.setContentsMargins(5, 0, 5, 0)

        self.render_day_calendar(
            datetime.today().month, datetime.today().day, datetime.today().year)

        self.setLayout(self.main_lay)

    def render_day_calendar(self, month: int, day: int, year: int):
        if not self.main_widget is None:
            self.main_lay.removeWidget(self.main_widget)
        self.main_widget = QWidget()
        main_lay = QVBoxLayout()
        scroll_area = QScrollArea()
        scroll_area.setFixedWidth(600)
        scroll_area.setFixedHeight(450)
        container = QWidget()
        container_lay = QVBoxLayout()
        container_lay.setSpacing(0)
        # container_lay.setContentsMargins(3, 0, 3, 0)

        cal = Cal()
        week_day = 0
        for i in cal.itermonthdays2(year, month):
            if i[0] == day:
                week_day = i[1]
                break

        day_name = QLabel(self.__DAYS[week_day].upper())
        day_name.setFixedSize(50, 50)
        day_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_lay.addWidget(day_name)

        day_date = QLabel(str(day))
        day_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        day_date.setFixedSize(50, 50)
        day_date.setObjectName("special-label")
        container_lay.addWidget(day_date)

        calendar = QWidget()
        calendar_lay = QGridLayout()

        tasks = self.get_tasks(month)

        for i in range(24):
            l = QLabel(f"{i}:00")
            calendar_lay.addWidget(l, i, 0)

            hour = QGroupBox()
            hour_lay = QVBoxLayout()
            hour_lay.setSpacing(0)
            hour_lay.setContentsMargins(5, 1, 5, 1)
            for task in tasks:
                deadline = int(task[2][8:10])
                if deadline == day:
                    deadline_hour = int(task[3])
                    if deadline_hour == i:
                        l = Task(self, task_id=task[0])
                        hour_lay.addWidget(l)
                else:
                    continue
            hour.setFixedWidth(500)
            hour.setLayout(hour_lay)
            calendar_lay.addWidget(hour, i, 1)
        calendar.setLayout(calendar_lay)
        container_lay.addWidget(calendar)

        container.setLayout(container_lay)
        scroll_area.setWidget(container)
        main_lay.addWidget(scroll_area)
        self.main_widget.setLayout(main_lay)
        self.main_lay.addWidget(self.main_widget)

    def render_month_calendar(self, month: int, day: int, year: int):
        self.main_lay.removeWidget(self.main_widget)

        self.main_widget = QWidget()
        self.main_widget.setFixedSize(600, 450)
        main_layout = QGridLayout()
        main_layout.setSpacing(1)

        w = [6, 0, 1, 2, 3, 4, 5]
        for i in range(len(w)):
            l = QLabel(self.__DAYS[w[i]].upper())
            l.setFixedWidth(80)

            main_layout.addWidget(l, 0, i)

        cal = Cal()
        cal.setfirstweekday(6)
        row = 1
        col = 0
        tasks = self.get_tasks(month)
        for i in cal.itermonthdays(year, month):
            if col == 7:
                row += 1
                col = 0
            if i == 0:
                col += 1
                continue
            day_container = QScrollArea()
            day_container.setContentsMargins(0, 0, 0, 0)
            day_container.setFixedSize(80, 80)
            container = QWidget()
            container_lay = QVBoxLayout()
            container_lay.setSpacing(0)
            container_lay.setContentsMargins(0, 0, 0, 0)

            l = QLabel(f"{'' if i == 0 else i}")
            l.setFixedSize(25, 25)
            l.setContentsMargins(5, 0, 5, 0)
            l.setStyleSheet("background-color: #00000000; font-size: 10px")
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if i == day:
                l.setStyleSheet("""
                    background-color: #ffa131;
                    color: #ffffff;
                    font-size: 12px;
                    font-weight: bold;
                    border-radius: 10%;
                """)
            container_lay.addWidget(l)
            for task in tasks:
                deadline = int(task[2][8:])
                if deadline == i:
                    l = Task(self, task_id=task[0])
                    l.setContentsMargins(3, 0, 3, 0)
                    container_lay.addWidget(l)
                else:
                    continue
            container.setLayout(container_lay)
            day_container.setWidget(container)
            main_layout.addWidget(day_container, row, col)
            col += 1

        self.main_widget.setLayout(main_layout)
        self.main_lay.addWidget(self.main_widget)

    def render_week_calendar(self, month: int, day: int, year: int):
        self.main_lay.removeWidget(self.main_widget)

        self.main_widget = QScrollArea()
        self.main_widget.setFixedSize(600, 450)
        container = QWidget()
        container_lay = QGridLayout()
        container_lay.setSpacing(4)

        week = self.get_week_of_month(year, month, day)

        tasks = self.get_tasks(month)
        query = """SELECT id, task_name, date, hour FROM task
            WHERE user_id = ? AND strftime('%m', date) = ? OR strftime('%m', date) = ?"""
        cursor.execute(query, (
            self.userid,
            f'{month-1 if month-1 > 9 else '0' + str(month-1)}',
            f'{month+1 if month+1 > 9 else '0' + str(month+1)}'
        ))
        tasks.extend(cursor.fetchall())
        for i in range(len(week)):
            weekday = week[i]

            day_info = QWidget()
            day_layout = QVBoxLayout()
            day_info.setFixedSize(70, 80)

            day_name = QLabel(self.__DAYS[weekday[1]].upper())
            day_layout.addWidget(day_name)

            day_date = QLabel(f"{weekday[0]}")
            day_date.setFixedSize(30, 30)
            day_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if weekday[0] == day:
                # day_date.setObjectName("special-label")
                day_date.setStyleSheet("""
                    background-color: #ffa131;
                    color: #ffffff;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 10%;
                """)
            day_layout.addWidget(day_date)

            day_info.setLayout(day_layout)
            container_lay.addWidget(day_info, 0, i+1)

            for j in range(24):
                hour = QLabel(f"{j}:00")
                hour.setFixedWidth(50)
                container_lay.addWidget(hour, j+1, 0)

                hour_day = QGroupBox()
                hour_day_lay = QVBoxLayout()
                hour_day_lay.setSpacing(0)
                hour_day_lay.setContentsMargins(5, 0, 5, 0)

                for task in tasks:
                    deadline = int(task[2][8:])
                    if deadline == weekday[0]:
                        deadline_hour = int(task[3])
                        if deadline_hour == j:
                            l = Task(self, task_id=task[0])
                            hour_day_lay.addWidget(l)
                    else:
                        continue

                hour_day.setLayout(hour_day_lay)
                container_lay.addWidget(hour_day, j+1, i+1)

        container.setLayout(container_lay)
        self.main_widget.setWidget(container)
        self.main_lay.addWidget(self.main_widget)

    def get_tasks(self, month: int) -> list[tuple]:
        cursor.execute("""
            SELECT id, task_name, date, hour FROM task
            WHERE strftime('%m', date) = ? AND user_id = ?
        """, (f'{month if month > 9 else '0' + str(month)}', self.userid, ))
        tasks = cursor.fetchall()
        return tasks

    def get_week_of_month(self, year, month, day):
        cal = Cal(firstweekday=6)
        week = []
        found = False
        for i in cal.monthdays2calendar(year, month):
            for j in i:
                if j[0] == day:
                    week.extend(i)
                    found = True
                    break
            if found:
                break

        if week[0][0] == 0:
            week = list(filter(lambda t: t[0] != 0, week))
            week = list(reversed(week))
            prev_month = cal.monthdays2calendar(year, month-1)[-1]
            prev_month = list(filter(lambda t: t[0] != 0, prev_month))
            needed_days = 7 - len(week)
            for i in range(-1, -needed_days-1, -1):
                new_tuple = (prev_month[i][0], prev_month[i][1])
                week.append(new_tuple)
            week = list(reversed(week))

        if week[-1][0] == 0:
            week = list(filter(lambda t: t[0] != 0, week))
            next_month = cal.monthdays2calendar(year, month+1)[0]
            next_month = list(filter(lambda t: t[0] != 0, next_month))
            needed_days = 7 - len(week)
            for i in range(needed_days):
                new_tuple = (next_month[i][0], week[needed_days-2][1] + (i+1))
                week.append(new_tuple)

        return week
