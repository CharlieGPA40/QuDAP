from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QListWidgetItem, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QRadioButton)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import pyqtSignal
import sys

class Settings(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        label = QLabel("Select the theme:")
        layout.addWidget(label)
        label.setFont(QFont("Arial", 14))
        # Radio buttons for theme selection
        self.radio_dark = QRadioButton("Dark Mode")
        self.radio_bright = QRadioButton("Bright Mode")
        self.radio_dark.setFont(QFont("Arial", 14))
        self.radio_bright.setFont(QFont("Arial", 14))
        # Arrange radio buttons horizontally
        layout.addWidget(label)
        layout.addWidget(self.radio_dark)
        layout.addWidget(self.radio_bright)
        # Add widgets to the layout
        self.setLayout(layout)
        self.radio_dark.toggled.connect(self.toggle_dark_mode)
        # self.radio_bright.toggled.connect(self.toggle_brighter_mode)
    def toggle_dark_mode(self, is_checked):
        if is_checked:
            print("Dark in Setting")
            self.checked = 0
        else:
            self.checked = 1
