from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QListWidgetItem, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QAbstractItemView)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import QSize, Qt
import sys

class ETO(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Welcome to the ETO Data Processing Page")
        font = QFont("Arial", 24)
        label.setFont(font)

        # Center the label horizontally and vertically
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(label)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
