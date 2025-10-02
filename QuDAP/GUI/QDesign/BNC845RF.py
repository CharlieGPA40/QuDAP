from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QRadioButton, QGroupBox, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QPushButton, QComboBox, QLineEdit)
from PyQt6.QtGui import QIcon, QFont, QIntValidator, QValidator, QDoubleValidator
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
import sys
import pyvisa as visa
import matplotlib
import time
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import random

class Command:
    def get_id(self, instrument) -> str:
        id = instrument.query('*IDN?')
        return id

    def abort(self, instrument):
        instrument.write(':ABORt')

    def initialize(self, instrument):
        instrument.write(':INIT ON')

    def output_on(self, instrument, state: str):
        if state.lower == 'on':
            instrument.write(':OUTP ON')
        elif state.lower == 'off':
            instrument.write(':OUTP OFF')

    def set_frequency(self, instrument, frequency: str):
        if 99999 < int(frequency) < 26500000001:
            instrument.write(':SOUR:FREQ {}'.format(frequency))
        else:
            return None

    def set_power(self, instrument, power: str):
        if -21 < int(power) < 16:
            instrument.write(':SOUR:POW {}'.format(power))
        else:
            return None

    def set_am_depth(self, instrument, am_depth: str):
        if 0 <= int(am_depth) <= 1:
            instrument.write(':SOUR:AM:DEPT {}'.format(am_depth))

    def set_am_state(self, instrument, state: str):
        if state.lower == 'on':
            instrument.write(':SOUR:AM:STAT ON')
        elif state.lower == 'off':
            instrument.write(':SOUR:AM:STAT off')

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
        # GPIB ComboBox
        self.gpib_combo = QComboBox()
        with open("GUI/QSS/QComboWidget.qss", "r") as file:
            self.QCombo_stylesheet = file.read()
        self.gpib_combo.setStyleSheet(self.QCombo_stylesheet)
        self.gpib_combo.setFont(font)

        self.current_gpib_label = QLabel("Current Connection: None")
        self.current_gpib_label.setFont(font)
        # Refresh Button
        refresh_btn = QPushButton(icon=QIcon("GUI/Icon/refresh.svg"))

        refresh_btn.clicked.connect(self.refresh_gpib_list)
        # Label to display current GPIB connection

        # self.gpib_combo.currentTextChanged.connect(self.update_current_gpib)
        # Populate GPIB ports initially
        self.connect_btn = QPushButton('Connect')
        self.connect_btn_clicked = False
        self.connect_btn.clicked.connect(self.connect_current_gpib)

        # Layout for the combobox and refresh button
        combo_text_layout = QVBoxLayout()
        group_box = QGroupBox("Device Connection")

        # Set the layout for the group box

        # combo_text_widget.setStyleSheet("QWidget { border: 2px solid black; }")
        combo_layout = QHBoxLayout()
        combo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        combo_layout.addWidget(self.gpib_combo, 4)
        combo_layout.addWidget(refresh_btn, 1)
        self.refresh_gpib_list()
        combo_layout.addWidget(self.connect_btn, 2)
        combo_layout.setContentsMargins(50, 0, 50, 0)
        combo_text_layout.addLayout(combo_layout)
        combo_text_layout.addWidget(self.current_gpib_label, alignment=Qt.AlignmentFlag.AlignCenter)
        group_box.setLayout(combo_text_layout)
        main_layout.addWidget(group_box)



        with open("GUI/QSS/QButtonWidget.qss", "r") as file:
            self.Button_stylesheet = file.read()
        self.connect_btn.setStyleSheet(self.Button_stylesheet)
        refresh_btn.setStyleSheet(self.Button_stylesheet)

    def refresh_gpib_list(self):
        # Access GPIB ports using PyVISA
        rm = visa.ResourceManager()
        instruments = rm.list_resources()
        self.gpib_ports = [instr for instr in instruments]
        self.current_gpib_label.setText(f"Current Connection: None")
        # Clear existing items and add new ones
        self.gpib_combo.clear()
        self.gpib_combo.addItems(["None"])
        self.gpib_combo.addItems(self.gpib_ports)
        self.gpib_combo.addItems(['Emulation'])
        self.connect_btn.setText('Connect')
        self.connect_btn_clicked = False
        self.isConnect = False
        self.isCheckedBox1 = False
        self.isCheckedBox2 = False
        self.counter = 0
        self.counter_array = []

    def connect_current_gpib(self):
        rm = visa.ResourceManager()
        if self.connect_btn_clicked == False:
            self.connect_btn.setText('Disconnect')
            self.connect_btn_clicked = True
        elif self.connect_btn_clicked == True:

            self.connect_btn.setText('Connect')
            self.current_gpib_label.setText("Current Connection: None")

            self.connect_btn_clicked = False
        self.current_connection = self.gpib_combo.currentText()
        if self.current_connection == 'None':
            self.isConnect = False
        else:
            if self.connect_btn_clicked == False:
                self.isConnect = False
            else:
                self.current_gpib_label.setText(f"Attempt to connect {self.current_connection}...")
                try:
                    if self.current_connection == 'Emulation':
                        self.isConnect = True
                        self.current_gpib_label.setText(f"{self.current_connection} Connection Success!")
                        time.sleep(1)
                        self.current_gpib_label.setText(f"Current Connection: Emulation")

                    else:
                        self.bnc845 = rm.open_resource(self.current_connection, timeout=10000)
                        time.sleep(2)
                        bnc846 = self.bnc845.query('ID')
                        self.isConnect = True
                        self.current_gpib_label.setText(f"{self.current_connection} Connection Success!")
                        time.sleep(1)
                        self.current_gpib_label.setText(f"Current Connection: {bnc846}")

                except visa.errors.VisaIOError:
                    self.isConnect = False
                    self.current_gpib_label.setText(f"Connecting {self.current_connection} fail!")
                # Comment it in real implementation
                self.isConnect = True

    def bnc845rf_window_reading_ui(self):
        None
