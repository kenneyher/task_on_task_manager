from PyQt5.QtWidgets import (
    QScrollArea,
    QWidget,
    QLabel,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDateEdit,
    QTimeEdit,
    QTextEdit,
    QRadioButton,
    QPushButton,
    QComboBox
)
from PyQt5.QtCore import QDate, Qt, QTime, QSize
from PyQt5.QtGui import QFont, QIcon, QPainter, QPen, QColor
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice
from notifypy import Notify
import sys
from datetime import datetime
from calendar import Calendar as Cal
import sqlite3
from pathlib import Path

PATH = f"{Path.home()}/.task_on"
conn = sqlite3.connect(f"{PATH}/task_on.db")
cursor = conn.cursor()


class TaskInfo (QWidget):
    def __init__(self, parent, task_id: int):
        super().__init__(parent=parent)
        self.setWindowFlag(Qt.WindowType.Window)
        self.setFixedWidth(400)

        self.main_layout = QVBoxLayout()
        self.main = None
        self.task_id = task_id

        self.show_task_info()

        self.setLayout(self.main_layout)

    def show_task_info(self):
        if not self.main is None:
            self.main_layout.removeWidget(self.main)
        self.main = QWidget()

        query = '''SELECT * FROM task WHERE id = ?'''
        cursor.execute(query, (f'{self.task_id}', ))

        self.task_info = cursor.fetchone()

        layout = QVBoxLayout()

        l = QLabel(f"Title: {self.task_info[1]}")
        l.setFont(QFont('Arial', 12))
        l.setWordWrap(True)
        layout.addWidget(l)
        l = QLabel(f"Content: {self.task_info[2]}")
        l.setFont(QFont('Arial', 12))
        l.setWordWrap(True)
        layout.addWidget(l)
        l = QLabel(f"Priority: {self.task_info[3]}")
        l.setFont(QFont('Arial', 12))
        l.setWordWrap(True)
        layout.addWidget(l)
        l = QLabel(f"Status: {self.task_info[4]}")
        l.setFont(QFont('Arial', 12))
        l.setWordWrap(True)
        layout.addWidget(l)
        l = QLabel(
            f"Due Date/Hour: {self.task_info[5]}  {self.task_info[6]}:{self.task_info[-2] if self.task_info[-2] > 9 else f'0{self.task_info[-2]}'}")
        l.setFont(QFont('Arial', 12))
        l.setWordWrap(True)
        layout.addWidget(l)

        btns_container = QWidget()
        btns_lay = QHBoxLayout()
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setIcon(QIcon('./edit_task.png'))
        self.edit_btn.setIconSize(QSize(25, 25))
        self.edit_btn.setFont(QFont('Arial', 14))
        self.edit_btn.clicked.connect(self.edit_task)
        btns_lay.addWidget(self.edit_btn)
        self.del_btn = QPushButton("Delete")
        self.del_btn.setStyleSheet('''
            background-color: #ff5026;
        ''')
        self.del_btn.setIcon(QIcon('./delete_task.png'))
        self.del_btn.setIconSize(QSize(25, 25))
        self.del_btn.setFont(QFont('Arial', 14, italic=True))
        self.del_btn.clicked.connect(self.delete_task)
        btns_lay.addWidget(self.del_btn)
        self.com_btn = QPushButton(icon=QIcon('./complete_task.png'))
        self.com_btn.setFixedWidth(45)
        self.com_btn.setStyleSheet('''
            background-color: #429b5b;
        ''')
        self.com_btn.setIconSize(QSize(25, 25))
        self.com_btn.clicked.connect(self.mark_as_complete)
        btns_lay.addWidget(self.com_btn)
        btns_container.setLayout(btns_lay)
        layout.addWidget(btns_container)
        self.main.setLayout(layout)

        self.main_layout.addWidget(self.main)

    def edit_task(self):
        if not self.main is None:
            self.main_layout.removeWidget(self.main)
        self.main = QWidget()
        layout = QFormLayout()
        self.main.setFont(QFont('Calibri', 11))

        self.task_name = QLineEdit()
        self.task_name.setText(self.task_info[1])
        layout.addRow("Task Name:", self.task_name)

        self.task_content = QTextEdit()
        self.task_content.setText(self.task_info[2])
        layout.addRow("Task Content:", self.task_content)

        self.deadline = QDateEdit()
        date = QDate(int(self.task_info[5][:4]), int(
            self.task_info[5][5:7]), int(self.task_info[5][8:]))
        self.deadline.setDate(date)
        print(date.toString())
        layout.addRow("Due Date:", self.deadline)

        self.deadline_hour = QTimeEdit()
        self.deadline_hour.setTime(
            QTime(int(self.task_info[6]), int(self.task_info[7]), 0))
        layout.addRow("Hour:", self.deadline_hour)

        priorities = QWidget()
        priorities_layout = QHBoxLayout()
        self.low = QRadioButton('Low')
        self.low.setChecked(self.low.text() == self.task_info[3])
        priorities_layout.addWidget(self.low)
        self.med = QRadioButton('Medium')
        self.med.setChecked(self.med.text() == self.task_info[3])
        priorities_layout.addWidget(self.med)
        self.high = QRadioButton('High')
        self.high.setChecked(self.high.text() == self.task_info[3])
        priorities_layout.addWidget(self.high)
        priorities.setLayout(priorities_layout)
        layout.addRow("Priority:", priorities)

        self.update_btn = QPushButton("Update")
        self.cancel = QPushButton("Cancel")
        self.update_btn.clicked.connect(self.update_task)
        self.cancel.clicked.connect(self.show_task_info)
        layout.addRow(self.cancel, self.update_btn)

        self.main.setLayout(layout)
        self.main_layout.addWidget(self.main)

    def update_task(self):
        day = self.deadline.date().day() if self.deadline.date().day() > 9 else f"0{
            self.deadline.date().day()}"
        month = self.deadline.date().month() if self.deadline.date(
        ).month() > 9 else f"0{self.deadline.date().month()}"
        year = self.deadline.date().year()
        if self.task_name.text() == "" or self.task_content.toPlainText() == "":
            dlg = ErrorDialog(self)
            if dlg.exec():
                pass
            else:
                self.close()
        elif self.check_rb() == "":
            dlg = ErrorDialog(self)
            if dlg.exec():
                pass
            else:
                self.close()
        else:
            try:
                cursor.execute("""
                    UPDATE task
                    SET task_name = ?,
                        content = ?,
                        priority = ?,
                        status = ?,
                        date = ?,
                        hour = ?,
                        minute = ?
                    WHERE id = ?
                """, (
                    self.task_name.text(),
                    self.task_content.toPlainText(),
                    self.check_rb(),
                    'Pending',
                    f"{year}-{month}-{day}",
                    self.deadline_hour.time().hour(),
                    self.deadline_hour.time().minute(),
                    self.task_id
                ))
                conn.commit()
            except sqlite3.Error as e:
                dlg = ErrorDialog(self)

                if dlg.exec():
                    pass
                else:
                    self.close()
            finally:
                self.close()

    def delete_task(self):
        cursor.execute(f"DELETE FROM task WHERE id = {self.task_id}")
        conn.commit()
        self.close()

    def mark_as_complete(self):
        cursor.execute(
            f"UPDATE task SET status = 'Completed' WHERE id = {self.task_id}")
        conn.commit()
        self.close()

    def check_rb(self):
        if self.low.isChecked():
            return 'Low'
        if self.med.isChecked():
            return 'Medium'
        if self.high.isChecked():
            return 'High'


class TaskListWindow(QWidget):
    def __init__(self, window_parent, user_id):
        super().__init__(window_parent)
        # self.window_parent = window_parent
        self.setWindowFlag(Qt.WindowType.Window)
        self.setFixedSize(900, 500)
        self.user_id = user_id

        lay = QVBoxLayout()
        lay.setSpacing(0)
        lay.setContentsMargins(5, 0, 5, 0)

        sort_box = QWidget()
        sort_box.setMaximumSize(200, 50)
        sort_lay = QHBoxLayout()

        l = QLabel('Sort by:')
        l.setMaximumWidth(100)
        sort_lay.addWidget(l)

        self.sort_by = QComboBox()
        self.sort_by.setMaximumWidth(100)
        self.sort_by.addItems(['Title', 'Date', 'Hour'])
        self.sort_by.currentTextChanged.connect(self.sort_tasks)
        sort_lay.addWidget(self.sort_by)

        sort_box.setLayout(sort_lay)
        lay.addWidget(sort_box)

        container = QWidget()
        self.main_layout = QHBoxLayout()
        self.main = QScrollArea()
        self.toolbar = QWidget()
        self.toolbar.setMaximumWidth(300)
        tb_layout = QVBoxLayout()
        tb_layout.addSpacing(0)
        tb_layout.setContentsMargins(2, 0, 2, 0)

        task_list = QWidget()
        tl_layout = QVBoxLayout()

        cursor.execute(f"SELECT * FROM task WHERE user_id = {self.user_id}")
        tasks = cursor.fetchall()

        for task in tasks:
            t = TaskItem(task[0])
            tl_layout.addWidget(t)
        task_list.setLayout(tl_layout)

        self.main.setWidget(task_list)
        self.main.setFixedWidth(300)
        self.main_layout.addWidget(self.main)

        self.word_filter = QLineEdit()
        filter_content = QPushButton('Filter by Word')
        filter_content.clicked.connect(self.show_by_word)
        self.date_filter = QDateEdit()
        self.date_filter.setDate(
            QDate(datetime.now().year, datetime.now().month, datetime.now().day))
        filter_date = QPushButton('Filter by Date')
        filter_date.clicked.connect(self.show_by_date)
        self.priority_filter = QComboBox()
        filter_priority = QPushButton('Filter by Priority')
        self.priority_filter.addItems(["Low", "Medium", "High"])
        filter_priority.clicked.connect(self.show_by_priority)
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Pending", "Completed"])
        filter_status = QPushButton('Filter by Completion State')
        filter_status.clicked.connect(self.show_by_status)
        filter_time = QPushButton('Filter by Time Frame')
        self.time_frame = QComboBox()
        self.time_frame.addItems(["Morning", "Afternoon", "Night"])
        filter_time.clicked.connect(self.show_by_time)

        tb_layout.addWidget(self.word_filter)
        tb_layout.addWidget(filter_content)
        tb_layout.addWidget(self.date_filter)
        tb_layout.addWidget(filter_date)
        tb_layout.addWidget(self.priority_filter)
        tb_layout.addWidget(filter_priority)
        tb_layout.addWidget(self.status_filter)
        tb_layout.addWidget(filter_status)
        tb_layout.addWidget(self.time_frame)
        tb_layout.addWidget(filter_time)

        self.toolbar.setFixedWidth(200)
        self.toolbar.setLayout(tb_layout)
        self.main_layout.addWidget(self.toolbar)

        self.create_chart()

        container.setLayout(self.main_layout)
        lay.addWidget(container)
        self.setLayout(lay)

    def show_by_word(self):
        query = f"""
            SELECT *
            FROM task
            WHERE
                content LIKE '%{self.word_filter.text()}%'
                OR task_name LIKE '%{self.word_filter.text()}%'
                AND user_id = {self.user_id}
            """
        cursor.execute(query)
        filtered_tasks = cursor.fetchall()

        task_list = QWidget()
        tl_layout = QVBoxLayout()

        for task in filtered_tasks:
            t = TaskItem(task[0])
            tl_layout.addWidget(t)
        task_list.setLayout(tl_layout)

        self.main.setWidget(task_list)

    def show_by_date(self):
        day = self.date_filter.date().day() if self.date_filter.date().day() > 9 else f'0{
            self.date_filter.date().day()}'
        month = self.date_filter.date().month() if self.date_filter.date(
        ).month() > 9 else f"0{self.date_filter.date().month()}"
        year = self.date_filter.date().year()
        query = f"""
            SELECT *
            FROM task
            WHERE
                date = '{year}-{month}-{day}'
                AND user_id = {self.user_id}
            """
        cursor.execute(query)
        filtered_tasks = cursor.fetchall()

        task_list = QWidget()
        tl_layout = QVBoxLayout()

        for task in filtered_tasks:
            t = TaskItem(task[0])
            tl_layout.addWidget(t)
        task_list.setLayout(tl_layout)

        self.main.setWidget(task_list)

    def show_by_priority(self):
        query = f"""
            SELECT *
            FROM task
            WHERE
                priority = '{self.priority_filter.currentText()}'
                AND user_id = {self.user_id}
            """
        cursor.execute(query)
        filtered_tasks = cursor.fetchall()

        task_list = QWidget()
        tl_layout = QVBoxLayout()

        for task in filtered_tasks:
            t = TaskItem(task[0])
            tl_layout.addWidget(t)
        task_list.setLayout(tl_layout)

        self.main.setWidget(task_list)

    def show_by_status(self):
        query = f"""
            SELECT *
            FROM task
            WHERE
                status = '{self.status_filter.currentText()}'
                AND user_id = {self.user_id}
            """
        cursor.execute(query)
        filtered_tasks = cursor.fetchall()

        task_list = QWidget()
        tl_layout = QVBoxLayout()

        for task in filtered_tasks:
            t = TaskItem(task[0])
            tl_layout.addWidget(t)
        task_list.setLayout(tl_layout)

        self.main.setWidget(task_list)

    def show_by_time(self):
        frames = {
            'Morning': [0, 11],
            'Afternoon': [12, 17],
            'Night': [18, 24]
        }
        query = f"""
            SELECT *
            FROM task
            WHERE
                hour BETWEEN
                    {frames[self.time_frame.currentText()][0]}
                    AND
                    {frames[self.time_frame.currentText()][1]}
                AND user_id = {self.user_id}
            """
        cursor.execute(query)
        filtered_tasks = cursor.fetchall()

        task_list = QWidget()
        tl_layout = QVBoxLayout()

        for task in filtered_tasks:
            t = TaskItem(task[0])
            tl_layout.addWidget(t)
        task_list.setLayout(tl_layout)

        self.main.setWidget(task_list)

    def create_chart(self):
        series = QPieSeries()
        completed = 0
        pending = 0

        query = f"""
            SELECT status
            FROM task
            WHERE
                user_id = {self.user_id}
        """
        cursor.execute(query)
        filtered_tasks = cursor.fetchall()

        for task in filtered_tasks:
            if task[0] == 'Completed':
                completed += 1
            else:
                pending += 1

        series.append("Completed", completed)
        series.append("Pending", pending)

        # adding slice
        slice = QPieSlice()
        slice = series.slices()[0]
        slice.setExploded(True)
        slice.setPen(QPen(QColor.fromRgb(66, 155, 94), 2))
        slice.setBrush(QColor.fromRgb(66, 155, 94))
        slice = QPieSlice()
        slice = series.slices()[1]
        slice.setPen(QPen(QColor.fromRgb(255, 141, 69), 2))
        slice.setBrush(QColor.fromRgb(255, 141, 69))

        chart = QChart()
        # chart.setMaximumSize(200, 200)
        chart.setFont(QFont('Arial', 10))
        chart.legend().hide()
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("Tasks Completion State:")

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)

        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.Antialiasing)

        self.main_layout.addWidget(chartview)

    def sort_tasks(self):
        if self.sort_by.currentText() == "Title":
            query = f"""
                SELECT *
                FROM task
                WHERE
                    user_id = {self.user_id}
                ORDER BY task_name ASC
            """
            cursor.execute(query)
            sorted_tasks = cursor.fetchall()

            task_list = QWidget()
            tl_layout = QVBoxLayout()

            for task in sorted_tasks:
                t = TaskItem(task[0])
                tl_layout.addWidget(t)
            task_list.setLayout(tl_layout)

            self.main.setWidget(task_list)
        if self.sort_by.currentText() == "Date":
            query = f"""
                SELECT *
                FROM task
                WHERE
                    user_id = {self.user_id}
                ORDER BY date ASC
            """
            cursor.execute(query)
            sorted_tasks = cursor.fetchall()

            task_list = QWidget()
            tl_layout = QVBoxLayout()

            for task in sorted_tasks:
                t = TaskItem(task[0])
                tl_layout.addWidget(t)
            task_list.setLayout(tl_layout)

            self.main.setWidget(task_list)
        if self.sort_by.currentText() == "Hour":
            query = f"""
                SELECT *
                FROM task
                WHERE
                    user_id = {self.user_id}
                ORDER BY hour ASC
            """
            cursor.execute(query)
            sorted_tasks = cursor.fetchall()

            task_list = QWidget()
            tl_layout = QVBoxLayout()

            for task in sorted_tasks:
                t = TaskItem(task[0])
                tl_layout.addWidget(t)
            task_list.setLayout(tl_layout)

            self.main.setWidget(task_list)


class TaskItem(QWidget):
    def __init__(self, task_id=0) -> None:
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(2, 10, 2, 10)
        self.setFixedWidth(280)

        query = '''SELECT * FROM task WHERE id = ?'''
        cursor.execute(query, (f'{task_id}', ))
        info = cursor.fetchone()

        title = QLabel(info[1].upper())
        title.setFont(QFont('Helvetica', 16, weight=QFont.Bold))
        # title.font().setBold(True)
        title.setWordWrap(True)
        title.setStyleSheet("""
            color: #429b5b;
        """)
        self.main_layout.addWidget(title)
        comment = QLabel(info[2])
        comment.setFont(QFont('Arial', 14))
        comment.setWordWrap(True)
        self.main_layout.addWidget(comment)

        other_info = QLabel(f"Priority: {info[3]}\nStatus: {
                            info[4]}\nDate/Hour: {info[5]}  {info[6]}:{info[7] if info[7] > 9 else f'0{info[7]}'}")
        other_info.setFont(QFont('Arial', 12))
        other_info.setStyleSheet("border-style: none")
        self.main_layout.addWidget(other_info)

        self.setLayout(self.main_layout)


class Task (QWidget):
    def __init__(self, window_parent, task_id=0):
        super().__init__()
        self.window_parent = window_parent
        self.task_id = task_id
        self.task_info = None
        self.setMaximumWidth(70)
        self.setContentsMargins(0,  0, 0, 0)
        self.setStyleSheet("font-size: 10px;")
        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(2)
        self.main_layout.setContentsMargins(5, 2, 5, 2)

        query = '''SELECT id, task_name, status FROM task WHERE id = ?'''
        cursor.execute(query, (f'{self.task_id}', ))

        self.info = cursor.fetchone()

        bar = QLabel('')
        bar.setFixedWidth(5)
        bar.setContentsMargins(0, 0, 10, 0)
        bar.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(bar)

        self.label = QLabel(self.info[1])
        if self.info[2] == 'Completed':
            bar.setStyleSheet("""
                padding: 2px;
                border-radius: 2px;
                background-color: #429b5b;
            """)
            self.label.setStyleSheet("color: #a2a2a2")
        else:
            bar.setStyleSheet("""
                padding: 2px;
                border-radius: 2px;
                background-color: #ffa131;
            """)
            self.label.setStyleSheet("color: black")
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(50)
        self.label.setMinimumHeight(20)
        self.main_layout.addWidget(self.label)

        self.setLayout(self.main_layout)

    def mousePressEvent(self, a0) -> None:
        if self.task_info is None:
            self.task_info = TaskInfo(self, self.task_id)
            self.task_info.show()
        else:
            self.task_info.close()
            self.task_info = None


class ErrorDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedWidth(300)

        self.setWindowTitle("Task 🍊n! says: Oops!")

        btn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.button_box = QDialogButtonBox(btn)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.close)

        self.main_layout = QVBoxLayout()
        message = QLabel(
            "The data passed to each field looks wrong. Can double check it?")
        message.setWordWrap(True)
        self.main_layout.addWidget(message)
        message = QLabel(
            "Please avoid the use of symbols like '?' and '!'. All fields must be filled.")
        message.setWordWrap(True)
        self.main_layout.addWidget(message)
        self.main_layout.addWidget(self.button_box)
        self.setLayout(self.main_layout)
