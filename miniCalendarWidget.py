from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QGridLayout,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor, QFont
from calendar import Calendar as Cal
from datetime import datetime


class CalendarPreviewWidget(QWidget):
    __DAYS = {
        0: 'M',
        1: 'T',
        2: 'W',
        3: 'T',
        4: 'F',
        5: 'S',
        6: 'S',
    }

    def __init__(self, month: int, day: int, year: int):
        super().__init__()
        self.main_widget = QWidget()
        self.main_lay = QGridLayout()

        self.render_preview(month, day, year)

    def render_preview(self, month: int, day: int, year: int):
        if not self.main_widget is None:
            self.main_lay.removeWidget(self.main_widget)
        self.main_widget = QWidget()
        self.setFixedHeight(200)
        self.main_widget.setFont(QFont('Arial', 11))

        w = [6, 0, 1, 2, 3, 4, 5]
        for i in range(len(w)):
            l = QLabel(self.__DAYS[w[i]])
            l.setFont(QFont('Arial', 12))
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if self.__DAYS[w[i]] == 'S':
                l.setStyleSheet("color: #eec683; font-weight: bold")

            self.main_lay.addWidget(l, 0, i)

        cal = Cal()
        cal.setfirstweekday(6)
        row = 1
        col = 0
        for i in cal.itermonthdays(year, month):
            if col == 7:
                row += 1
                col = 0
            if i == 0:
                col += 1
                continue

            l = QLabel(f"{'' if i == 0 else i}")
            l.setFixedSize(25, 25)
            l.setFont(QFont('Arial', 10))
            l.setStyleSheet("background-color: #00000000")
            if col == 0 or col == 6:
                l.setStyleSheet("color: #eec683;")
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if i == day:
                l.setStyleSheet("""
                    background-color: #ffa131;
                    color: #ffffff;
                    font-weight: bold;
                    border-radius: 10%;
                """)
            self.main_lay.addWidget(l, row, col)
            col += 1

        self.setLayout(self.main_lay)
