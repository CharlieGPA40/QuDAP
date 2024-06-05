from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QRadioButton, QGroupBox, QFileDialog, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QPushButton, QComboBox, QLineEdit)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread
import sys
import pyvisa as visa
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import random
import time




class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=300):
        fig = Figure(figsize=(width, height), dpi=dpi)

        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class Tempdep(QWidget):

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        titlefont = QFont("Arial", 20)
        font = QFont("Arial", 13)
        self.setStyleSheet("background-color: white;")

        # Create main vertical layout with centered alignment
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #  ---------------------------- PART 1 --------------------------------
        self.SHG_General_label = QLabel("SHG Temperature Dependence Data Processing")
        self.SHG_General_label.setFont(titlefont)
        self.SHG_General_label.setStyleSheet("""
                                            QLabel{
                                                background-color: white;
                                                }
                                                """)
        #  ---------------------------- PART 2 --------------------------------
        self.file_selection_group_box = QGroupBox("Folder Selection")
        self.file_selection_section_layout = QHBoxLayout()
        self.file_selection_main_layout = QVBoxLayout()

        self.file_selection_label = QLabel('Please select a folder:')
        self.file_selection_button = QPushButton('Select')
        self.file_selection_display_label = QLabel('Folder Selected: N/A')
        self.file_selection_button.clicked.connect(self.showDialog)
        self.file_selection_section_layout.addWidget(self.file_selection_label)
        self.file_selection_section_layout.addWidget(self.file_selection_button)

        self.file_selection_main_layout.addLayout(self.file_selection_section_layout)
        self.file_selection_main_layout.addWidget(self.file_selection_display_label)
        self.file_selection_group_box.setLayout(self.file_selection_main_layout)

        #  ---------------------------- Main Layout --------------------------------
        # Add widgets to the main layout with centered alignment
        main_layout.addWidget(self.SHG_General_label, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(self.file_selection_group_box)
        # main_layout.addWidget(voltage_reading_group_box)
        # main_layout.addLayout(graphing_layout)
        self.setLayout(main_layout)

        #  ---------------------------- Style Sheet --------------------------------
        self.file_selection_button.setStyleSheet("""
                   QPushButton {
                       background-color: #3498DB; /* Green background */
                       color: white; /* White text */
                       border-style: solid;
                       border-color: #3498DB;
                       border-width: 2px;
                       border-radius: 10px; /* Rounded corners */
                       padding: 5px;
                       min-height: 2px;
                       min-width: 50px;
                   }
                   QPushButton:hover {
                       background-color: #2874A6  ; /* Slightly darker green */
                   }
                   QPushButton:pressed {
                       background-color: #85C1E9; /* Even darker green */
                   }
               """)


    def showDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.Option.DontUseNativeDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", "", options=options)
        if folder:
            print(folder)
            folder = folder + "/"
            self.folder = folder
            self.file_selection_display_label.setText("Current Folder: {}".format(self.folder))
