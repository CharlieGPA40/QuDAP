from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QListWidgetItem, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QAbstractItemView)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QDateTime, QTime
import time

import sys

class Dash(QMainWindow):
    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout()
        self.headiing_layout = QVBoxLayout()
        current_time = QTime.currentTime()

        hour = current_time.hour()
        if 0 <= hour <= 12:
            self.hello_label = QLabel('Good Morning, Colleague!', self)
        elif 12 < hour <= 5:
            self.hello_label = QLabel('Good Afternoon, Colleague!', self)
        else:
            self.hello_label = QLabel('Good Evening, Colleague!', self)
        
        self.hello_label.setStyleSheet("color:   #E44E2C  ; font-weight: bold; font-size: 30px; font-style: italic")
        self.time_label = QLabel('Today is ', self)
        self.time_label.setStyleSheet("color:  #abb2b9 ; font-weight: bold; font-size: 15px;")

        # Center the label horizontally and vertically
        self.hello_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.headiing_layout.addWidget(self.hello_label)
        self.headiing_layout.addWidget(self.time_label)

        self.widget_layout = QHBoxLayout()

        self.main_layout.addLayout(self.headiing_layout)
        self.main_layout.setContentsMargins(50, 50, 50, 50)
        self.container = QWidget()
        self.container.setLayout(self.main_layout)
        self.setCentralWidget(self.container)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every 60,000 milliseconds (1 minute)
        self.update_time()


    def update_time(self):
        current_time = QDateTime.currentDateTime()
        time_display = current_time.toString("MM/dd/yyyy hh:mm:ss ")

        self.time_label.setText('Today is ' + time_display)

