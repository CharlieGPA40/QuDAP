from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QListWidgetItem, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QAbstractItemView)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QDateTime, QThread
import time

import sys

class Dash(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.time_label = QLabel(self)
        # current_time = QDateTime.currentDateTime()
        # time_display = current_time.toString("hh:mm:ss AP - dd/MM/yyyy")
        # self.time_label.setText(time_display)

        font = QFont("Arial", 24)
        self.time_label.setFont(font)

        # Center the label horizontally and vertically
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self.time_label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every 60,000 milliseconds (1 minute)
        self.update_time()


    def update_time(self):
        current_time = QDateTime.currentDateTime()
        time_display = current_time.toString("hh:mm:ss AP - dd/MM/yyyy")
        self.time_label.setText(time_display)