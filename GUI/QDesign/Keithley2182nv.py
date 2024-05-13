from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QListWidgetItem, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QPushButton, QComboBox)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import pyqtSignal, Qt
import sys
import pyvisa as visa
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


import GUI.Icon as Icon

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)

        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class NV(QWidget):

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        font = QFont("Arial", 15)
        self.setStyleSheet("background-color: white;")

        # Create main vertical layout with centered alignment
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # GPIB ComboBox
        self.gpib_combo = QComboBox()
        self.gpib_combo.setFont(font)
        # self.refresh_gpib_list()  # Populate GPIB ports initially

        # Refresh Button
        refresh_btn = QPushButton(icon=QIcon("Icon/refresh.svg"))
        refresh_btn.clicked.connect(self.refresh_gpib_list)

        # Label to display current GPIB connection
        self.current_gpib_label = QLabel("Current GPIB Connection: None")
        self.current_gpib_label.setFont(font)
        # self.gpib_combo.currentTextChanged.connect(self.update_current_gpib)

        # Layout for the combobox and refresh button
        combo_layout = QHBoxLayout()
        combo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        combo_layout.addWidget(self.gpib_combo, 4)
        combo_layout.addWidget(refresh_btn, 1)
        combo_layout.setContentsMargins(50,0,50,0)

        # Add widgets to the main layout with centered alignment
        main_layout.addLayout(combo_layout)
        main_layout.addWidget(self.current_gpib_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)

    def refresh_gpib_list(self):
        # Access GPIB ports using PyVISA
        rm = visa.ResourceManager()
        instruments = rm.list_resources()
        gpib_ports = [instr for instr in instruments if 'GPIB' in instr]

        # Clear existing items and add new ones
        self.gpib_combo.clear()
        self.gpib_combo.addItems(gpib_ports)
        if gpib_ports:
            self.current_gpib_label.setText(f"Current GPIB Connection: {gpib_ports[0]}")
        else:
            self.current_gpib_label.setText("Current GPIB Connection: None")
