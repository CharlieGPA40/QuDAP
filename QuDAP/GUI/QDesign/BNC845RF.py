from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QRadioButton, QGroupBox, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QPushButton, QComboBox, QLineEdit)
from PyQt6.QtGui import QIcon, QFont, QIntValidator, QValidator, QDoubleValidator
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
import sys
import pyvisa as visa
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import random

class IntegerValidator(QIntValidator):
    def __init__(self, minimum, maximum):
        super().__init__(minimum, maximum)
        self.minimum = minimum
        self.maximum = maximum
    def validate(self, input, pos):
        if input == "":
            return (QValidator.State.Intermediate, input, pos)
        state, value, pos = super().validate(input, pos)
        try:
            if self.minimum <= int(input) <= self.maximum:
                return (QValidator.State.Acceptable, input, pos)
            else:
                return (QValidator.State.Invalid, input, pos)
        except ValueError:
            return (QValidator.State.Invalid, input, pos)

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=300):
        fig = Figure(figsize=(width, height), dpi=dpi)

        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class BNC845RF(QWidget):

    def __init__(self):
        super().__init__()
        self.isConnect = False
        self.isPlotting = False
        self.init_ui()

    def init_ui(self):
        titlefont = QFont("Arial", 20)
        font = QFont("Arial", 13)
        self.setStyleSheet("background-color: white;")

        # Create main vertical layout with centered alignment
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #  ---------------------------- PART 1 --------------------------------
        self.current_intrument_label = QLabel("Berkeley Nucleonics Microwave and RF Signal Generator 845 Coming Soon")
        self.current_intrument_label.setFont(titlefont)
        self.current_intrument_label.setStyleSheet("""
                                            QLabel{
                                                background-color: white;
                                                }
                                                """)
        main_layout.addWidget(self.current_intrument_label)
        #  ---------------------------- PART 2 --------------------------------
