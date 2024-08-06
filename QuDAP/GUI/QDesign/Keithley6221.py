from PyQt6.QtWidgets import (
    QMessageBox, QMainWindow, QWidget, QRadioButton, QGroupBox, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QPushButton, QComboBox, QLineEdit)
from PyQt6.QtGui import QIcon, QFont, QIntValidator, QValidator, QDoubleValidator
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread
import time
import sys
import pyvisa as visa


class CurrentSource6221(QWidget):

    def __init__(self):
        super().__init__()
        try:
            self.isConnect = False
            self.keithley_6221 = 'None'
            self.DCisOn = False
            self.ACisOn = False
            self.init_ui()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def init_ui(self):
        titlefont = QFont("Arial", 20)
        font = QFont("Arial", 13)
        self.setStyleSheet("background-color: white;")

        # Create main vertical layout with centered alignment
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #  ---------------------------- PART 1 --------------------------------
        self.current_intrument_label = QLabel("Keithley 6221 DC and AC Current Source")
        self.current_intrument_label.setFont(titlefont)
        self.current_intrument_label.setStyleSheet("""
                                            QLabel{
                                                background-color: white;
                                                }
                                                """)

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

        #  ---------------------------- PART 3 --------------------------------
        dc_current_group_box = QGroupBox("DC Current")  # Container widget for the horizontal layout
        dc_current_main_layout = QVBoxLayout()
        DC_setup_layout = QHBoxLayout()
        self.DCSource_label = QLabel("DC Source:")
        self.DCSource_label.setFont(font)
        self.dc_source_entry_box = QLineEdit()
        self.dc_source_entry_box.setFont(font)
        # self.cur_field_entry_box.setValidator(IntegerValidator(-10000, 10000))
        self.current_validator = QDoubleValidator(-105, 105, 3)
        self.current_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.dc_source_entry_box.setValidator(self.current_validator)
        self.dc_source_entry_box.setPlaceholderText("±0.1pA to ±105mA")
        self.dc_source_entry_box.setFixedHeight(30)
        self.DCUnitSource_combo = QComboBox()
        self.DCUnitSource_combo.setFont(font)
        self.DCUnitSource_combo.setStyleSheet(self.QCombo_stylesheet)
        self.DCUnitSource_combo.addItems(["Select Units"])  # 0
        self.DCUnitSource_combo.addItems(["mA"])  # 1
        self.DCUnitSource_combo.addItems(["µA"])  # 2
        self.DCUnitSource_combo.addItems(["nA"])  # 3
        self.DCUnitSource_combo.addItems(["pA"])  # 3

        self.DC_Range_checkbox = QCheckBox("Auto Range")
        self.DC_Range_checkbox.setFont(font)
        self.DC_Range_checkbox.setChecked(True)
        self.send_btn = QPushButton('Send')
        self.send_btn.clicked.connect(self.sendDCCurrent)

        DC_setup_layout.addWidget(self.DCSource_label, 1)
        DC_setup_layout.addWidget(self.dc_source_entry_box, 3)
        DC_setup_layout.addWidget(self.DCUnitSource_combo, 1)
        DC_setup_layout.addStretch(1)
        DC_setup_layout.addWidget(self.DC_Range_checkbox, 1)
        DC_setup_layout.addStretch(1)
        DC_setup_layout.addWidget(self.send_btn, 1)

        dc_current_main_layout.addLayout(DC_setup_layout)

        dc_current_group_box.setLayout(dc_current_main_layout)

        #  ---------------------------- PART 4 --------------------------------
        self.wave_func_label = QLabel("Wave Function:")
        self.wave_func_label.setFont(font)
        wave_group_box = QGroupBox("Wave Functions")  # Container widget for the horizontal layout
        wave_main_layout = QVBoxLayout()
        # voltage_reading_widget.setStyleSheet("QWidget { border: 2px solid black; }")
        Wave_AMP_setup_layout = QHBoxLayout()
        self.waveform_combo = QComboBox()
        self.waveform_combo.setFont(font)
        self.waveform_combo.setStyleSheet(self.QCombo_stylesheet)

        self.waveform_combo.addItems(["Select Funcs"])  # 0
        self.waveform_combo.addItems(["SINE"])  # 1
        self.waveform_combo.addItems(["SQUARE"])  # 2
        self.waveform_combo.addItems(["RAMP"])  # 3
        self.waveform_combo.addItems(["ARB(x)"])  # 3

        self.AC_Amplitude_label = QLabel("Amplitude:")
        self.AC_Amplitude_label.setFont(font)
        self.AC_Amplitude_entry_box = QLineEdit()
        self.AC_Amplitude_entry_box.setFont(font)
        # self.cur_field_entry_box.setValidator(IntegerValidator(-10000, 10000))
        self.AC_Amplitude_validator = QDoubleValidator(0, 105, 10)
        self.AC_Amplitude_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.AC_Amplitude_entry_box.setValidator(self.AC_Amplitude_validator)
        self.AC_Amplitude_entry_box.setPlaceholderText("2pA to 105mA")
        self.AC_Amplitude_entry_box.setFixedHeight(30)
        self.WaveAmpUnitSource_combo = QComboBox()
        self.WaveAmpUnitSource_combo.setFont(font)
        self.WaveAmpUnitSource_combo.setStyleSheet(self.QCombo_stylesheet)

        self.WaveAmpUnitSource_combo.addItems(["Select Units"])  # 0
        self.WaveAmpUnitSource_combo.addItems(["mA"])  # 1
        self.WaveAmpUnitSource_combo.addItems(["µA"])  # 2
        self.WaveAmpUnitSource_combo.addItems(["nA"])  # 3
        self.WaveAmpUnitSource_combo.addItems(["pA"])  # 3

        Wave_AMP_setup_layout.addWidget(self.wave_func_label, 1)
        Wave_AMP_setup_layout.addWidget(self.waveform_combo, 1)
        Wave_AMP_setup_layout.addStretch(1)
        Wave_AMP_setup_layout.addWidget(self.AC_Amplitude_label, 1)
        Wave_AMP_setup_layout.addWidget(self.AC_Amplitude_entry_box, 3)
        Wave_AMP_setup_layout.addWidget(self.WaveAmpUnitSource_combo, 1)

        Wave_Freq_Offset_setup_layout = QHBoxLayout()
        self.AC_Frequency_label = QLabel("Frequency:")
        self.AC_Frequency_label.setFont(font)
        self.AC_Frequency_entry_box = QLineEdit()
        self.AC_Frequency_entry_box.setFont(font)
        # self.cur_field_entry_box.setValidator(IntegerValidator(-10000, 10000))
        self.AC_Frequency_validator = QDoubleValidator(0.00, 100000, 5)
        self.AC_Frequency_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.AC_Frequency_entry_box.setValidator(self.AC_Frequency_validator)
        self.AC_Frequency_entry_box.setPlaceholderText("0Hz to 100KHz")
        self.AC_Frequency_entry_box.setFixedHeight(30)
        self.AC_Frequency_Unit_label = QLabel("Hz")
        self.AC_Frequency_Unit_label.setFont(font)

        self.AC_Offset_label = QLabel("Offset:")
        self.AC_Offset_label.setFont(font)
        self.AC_Offset_entry_box = QLineEdit()
        self.AC_Offset_entry_box.setFont(font)
        # self.cur_field_entry_box.setValidator(IntegerValidator(-10000, 10000))
        self.AC_Offset_validator = QDoubleValidator(-105, 105, 10)
        self.AC_Offset_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.AC_Offset_entry_box.setValidator(self.AC_Offset_validator)
        self.AC_Offset_entry_box.setPlaceholderText("0 to ±105mA")
        self.AC_Offset_entry_box.setFixedHeight(30)
        self.WaveOffsetUnitSource_combo = QComboBox()
        self.WaveOffsetUnitSource_combo.setFont(font)
        self.WaveOffsetUnitSource_combo.setStyleSheet(self.QCombo_stylesheet)

        self.WaveOffsetUnitSource_combo.addItems(["Select Units"])  # 0
        self.WaveOffsetUnitSource_combo.addItems(["mA"])  # 1
        self.WaveOffsetUnitSource_combo.addItems(["µA"])  # 2
        self.WaveOffsetUnitSource_combo.addItems(["nA"])  # 3
        self.WaveOffsetUnitSource_combo.addItems(["pA"])  # 3

        self.Wave_Range_checkbox = QCheckBox("Best Range")
        self.Wave_Range_checkbox.setFont(font)
        self.Wave_Range_checkbox.setChecked(True)
        Wave_Freq_Offset_setup_layout.addWidget(self.AC_Frequency_label)
        Wave_Freq_Offset_setup_layout.addWidget(self.AC_Frequency_entry_box)
        Wave_Freq_Offset_setup_layout.addWidget(self.AC_Frequency_Unit_label)
        Wave_Freq_Offset_setup_layout.addStretch(1)
        Wave_Freq_Offset_setup_layout.addWidget(self.AC_Offset_label)
        Wave_Freq_Offset_setup_layout.addWidget(self.AC_Offset_entry_box)
        Wave_Freq_Offset_setup_layout.addWidget(self.WaveOffsetUnitSource_combo)
        Wave_Freq_Offset_setup_layout.addStretch(1)
        Wave_Freq_Offset_setup_layout.addWidget(self.Wave_Range_checkbox)

        Wave_Arm_setup_layout = QHBoxLayout()
        self.arm_btn = QPushButton('Arm')
        self.arm_btn.clicked.connect(self.sendACCurrent)
        Wave_Arm_setup_layout.addStretch(10)
        Wave_Arm_setup_layout.addWidget(self.arm_btn, 1)

        wave_main_layout.addLayout(Wave_AMP_setup_layout)
        wave_main_layout.addLayout(Wave_Freq_Offset_setup_layout)
        wave_main_layout.addLayout(Wave_Arm_setup_layout)

        wave_group_box.setLayout(wave_main_layout)

        #  ---------------------------- Main Layout --------------------------------
        # Add widgets to the main layout with centered alignment
        main_layout.addWidget(self.current_intrument_label, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(group_box)
        main_layout.addWidget(dc_current_group_box)
        main_layout.addWidget(wave_group_box)
        self.setLayout(main_layout)

        #  ---------------------------- Style Sheet --------------------------------

        with open("GUI/QSS/QButtonWidget.qss", "r") as file:
            self.Button_stylesheet = file.read()
        self.connect_btn.setStyleSheet(self.Button_stylesheet)
        self.send_btn.setStyleSheet("""
                                   QPushButton {
                                       background-color: #CAC9Cb; /* Green background */
                                       color: black; /* White text */
                                       border-style: solid;
                                       border-color: #CAC9Cb;
                                       border-width: 2px;
                                       border-radius: 10px; /* Rounded corners */
                                       padding: 5px;
                                       min-height: 1px;
                                       min-width: 10px;
                                   }
                                   QPushButton:hover {
                                       background-color: #5F6A6A; /* Slightly darker green */
                                   }
                                   QPushButton:pressed {
                                       background-color: #979A9A; /* Even darker green */
                                   }
                               """)
        self.arm_btn.setStyleSheet("""
                                   QPushButton {
                                       background-color: #CAC9Cb; /* Green background */
                                       color: black; /* White text */
                                       border-style: solid;
                                       border-color: #CAC9Cb;
                                       border-width: 2px;
                                       border-radius: 10px; /* Rounded corners */
                                       padding: 5px;
                                       min-height: 1px;
                                       min-width: 50px;
                                   }
                                   QPushButton:hover {
                                       background-color: #5F6A6A; /* Slightly darker green */
                                   }
                                   QPushButton:pressed {
                                       background-color: #979A9A; /* Even darker green */
                                   }
                               """)
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
        self.connect_btn.setText('Connect')
        self.connect_btn_clicked = False
        self.isConnect = False
        self.isCheckedBox1 = False
        self.isCheckedBox2 = False

    def connect_current_gpib(self):
        rm = visa.ResourceManager()
        if self.connect_btn_clicked == False:
            self.connect_btn.setText('Disonnect')
            self.connect_btn_clicked = True
        elif self.connect_btn_clicked == True:
            self.connect_btn.setText('Connect')
            self.current_gpib_label.setText("Current Connection: None")
            self.connect_btn_clicked = False
            self.keithley_6221.close()
        self.current_connection = self.gpib_combo.currentText()
        if self.current_connection == 'None':
            self.isConnect = False
        else:
            if self.connect_btn_clicked == False:
                self.isConnect = False
            else:
                self.current_gpib_label.setText(f"Attempt to connect {self.current_connection}...")
                try:
                    self.keithley_6221 = rm.open_resource(self.current_connection, timeout=10000)
                    time.sleep(2)
                    Model_6221 = self.keithley_2182nv.query('*IDN?')
                    self.isConnect = True
                    self.keithley_6221.write("OUTPut OFF")
                    self.current_gpib_label.setText(f"{self.current_connection} Connection Success!")
                    time.sleep(1)
                    self.current_gpib_label.setText(f"Current Connection: {Model_6221}")
                except visa.errors.VisaIOError:
                    self.isConnect = False
                    self.current_gpib_label.setText(f"Connecting {self.current_connection} fail!")
                # Comment it in real implementation
                self.isConnect = True

    def sendDCCurrent(self):
        if self.isConnect == True:
            if self.DCisOn == False:
                self.keithley_6221.write('CLE')
                DC_validator = self.check_validator(self.current_validator, self.dc_source_entry_box)
                if DC_validator == True:
                    if self.DC_Range_checkbox.isChecked():
                        self.keithley_6221.write('CURR:RANG:AUTO ON')
                    else:
                        self.keithley_6221.write('CURR:RANG:AUTO OFF')
                    self.DC_current_entry = self.dc_source_entry_box.displayText()
                    self.DC_unit = self.DCUnitSource_combo.currentIndex()
                    if self.DC_unit != 0:
                        if self.DC_unit == 1:  # mA
                            unit = 'e-3'
                        elif self.DC_unit == 2:  # uA
                            unit = 'e-6'
                        elif self.DC_unit == 3:  # nA
                            unit = 'e-9'
                        elif self.DC_unit == 4:  # pA
                            unit = 'e-12'
                        self.keithley_6221.write("CURRent " + self.DC_current_entry + unit)
                        self.keithley_6221.write("OUTPut ON")
                        self.send_btn.setText('OFF')
                        self.DCisOn = True
                        self.arm_btn.setEnabled(False)
                        self.send_btn.setStyleSheet("""
                                                           QPushButton {
                                                               background-color: #28A630; /* Green background */
                                                               color: black; /* White text */
                                                               border-style: solid;
                                                               border-color: #28A630;
                                                               border-width: 2px;
                                                               border-radius: 10px; /* Rounded corners */
                                                               padding: 5px;
                                                               min-height: 1px;
                                                               min-width: 10px;
                                                           }
                                                           QPushButton:hover {
                                                               background-color: #F2433B; /* Slightly darker green */
                                                           }
                                                           QPushButton:pressed {
                                                               background-color: #979A9A; /* Even darker green */
                                                           }
                                                       """)
                    else:
                        QMessageBox.warning(self, "Input Missing", "Please enter all the required information")
                else:
                    QMessageBox.warning(self, "Input out of range", "Please enter again")
            else:
                self.DCisOn = False
                self.keithley_6221.write("OUTPut OFF")
                self.arm_btn.setEnabled(True)
                self.send_btn.setText('Send')
                self.send_btn.setStyleSheet("""
                                                   QPushButton {
                                                       background-color: #CAC9Cb; /* Green background */
                                                       color: black; /* White text */
                                                       border-style: solid;
                                                       border-color: #CAC9Cb;
                                                       border-width: 2px;
                                                       border-radius: 10px; /* Rounded corners */
                                                       padding: 5px;
                                                       min-height: 1px;
                                                       min-width: 10px;
                                                   }
                                                   QPushButton:hover {
                                                       background-color: #5F6A6A; /* Slightly darker green */
                                                   }
                                                   QPushButton:pressed {
                                                       background-color: #979A9A; /* Even darker green */
                                                   }
                                               """)

    def sendACCurrent(self):
        if self.isConnect:
            if self.ACisOn == False:
                self.keithley_6221.write('CLE')
                self.keithley_6221.write('CURR:RANG:AUTO ON')
                self.wave_mode = self.waveform_combo.currentIndex()
                if self.wave_mode != 0:
                    if self.wave_mode == 1:  # mA
                        self.keithley_6221.write('SOUR:WAVE:FUNC SIN')
                    elif self.wave_mode == 2:  # uA
                        self.keithley_6221.write('SOUR:WAVE:FUNC SQU')
                    elif self.wave_mode == 3:  # nA
                        self.keithley_6221.write('SOUR:WAVE:FUNC RAMP')
                    elif self.wave_mode == 4:  # pA
                        self.keithley_6221.write('SOUR:WAVE:FUNC ARB0')
                else:
                        QMessageBox.warning(self, "Input Missing", "Please enter all the required information")
                        return
                if self.AC_Amplitude_entry_box.displayText() == '':
                    self.AC_Amplitude_entry_box.setText('1')
                    self.WaveAmpUnitSource_combo.setCurrentIndex(1)  # 0

                if self.AC_Frequency_entry_box.displayText() == '':
                    self.AC_Frequency_entry_box.setText('1e3')

                if self.AC_Offset_entry_box.displayText() == '':
                    self.AC_Offset_entry_box.setText('0')
                    self.WaveOffsetUnitSource_combo.setCurrentIndex(1)  # 0
                Amplitude_Validator = self.check_validator(self.AC_Amplitude_validator, self.AC_Amplitude_entry_box)
                Freq_Validator = self.check_validator(self.AC_Frequency_validator, self.AC_Frequency_entry_box)
                Offset_Validator = self.check_validator(self.AC_Offset_validator, self.AC_Offset_entry_box)
                if Amplitude_Validator == True and Freq_Validator == True and Offset_Validator == True:

                    self.AC_amplitude = self.AC_Amplitude_entry_box.displayText()
                    
                    self.AC_amplitude_Unit = self.WaveAmpUnitSource_combo.currentIndex()
                    if self.AC_amplitude_Unit != 0:
                        if self.AC_amplitude_Unit == 1:  # mA
                            amp_unit = 'e-3'
                        elif self.AC_amplitude_Unit == 2:  # uA
                            amp_unit = 'e-6'
                        elif self.AC_amplitude_Unit == 3:  # nA
                            amp_unit = 'e-9'
                        elif self.AC_amplitude_Unit == 4:  # pA
                            amp_unit = 'e-12'
                    else:
                        QMessageBox.warning(self, "Input Missing", "Please enter all the required information")
                        return

                    self.AC_Freq = self.AC_Frequency_entry_box.displayText()
                    self.AC_Offset = self.AC_Offset_entry_box.displayText()
                    self.AC_Offset_unit = self.WaveOffsetUnitSource_combo.currentIndex()
                    if self.AC_Offset_unit != 0:
                        if self.AC_Offset_unit == 1:  # mA
                            offset_unit = 'e-3'
                        elif self.AC_Offset_unit == 2:  # uA
                            offset_unit = 'e-6'
                        elif self.AC_Offset_unit == 3:  # nA
                            offset_unit = 'e-9'
                        elif self.AC_Offset_unit == 4:  # pA
                            offset_unit = 'e-12'
                    else:
                        QMessageBox.warning(self, "Input Missing", "Please enter all the required information")
                        return
                    self.keithley_6221.write('SOUR:WAVE:AMPL ' + self.AC_amplitude + amp_unit)
                    self.keithley_6221.write('SOUR:WAVE:FREQ ' + self.AC_Freq)
                    self.keithley_6221.write('SOUR:WAVE:OFFset ' + self.AC_Offset + offset_unit)
                    self.keithley_6221.write('SOUR:WAVE:PMAR:STAT OFF')
                    if self.Wave_Range_checkbox.isChecked():
                        self.keithley_6221.write('SOUR:WAVE:RANG BEST')
                    else:
                        self.keithley_6221.write('SOUR:WAVE:RANG FIX')
                    self.keithley_6221.write('SOUR:WAVE:ARM')
                    self.keithley_6221.write('SOUR:WAVE:INIT')
                    self.ACisOn = True
                    self.send_btn.setEnabled(False)
                    self.arm_btn.setText('Abort')
                    self.arm_btn.setStyleSheet("""
                                              QPushButton {
                                                  background-color: #28A630; /* Green background */
                                                  color: black; /* White text */
                                                  border-style: solid;
                                                  border-color: #28A630;
                                                  border-width: 2px;
                                                  border-radius: 10px; /* Rounded corners */
                                                  padding: 5px;
                                                  min-height: 1px;
                                                  min-width: 10px;
                                              }
                                              QPushButton:hover {
                                                  background-color: #F2433B; /* Slightly darker green */
                                              }
                                              QPushButton:pressed {
                                                  background-color: #979A9A; /* Even darker green */
                                              }
                                          """)

                else:
                    QMessageBox.warning(self, "Input out of range", "Please enter again")
            else:
                self.ACisOn = False
                self.keithley_6221.write("SOUR:WAVE:ABOR")
                self.send_btn.setEnabled(True)
                self.arm_btn.setText('Arm')
                self.arm_btn.setStyleSheet("""
                                                                   QPushButton {
                                                                       background-color: #CAC9Cb; /* Green background */
                                                                       color: black; /* White text */
                                                                       border-style: solid;
                                                                       border-color: #CAC9Cb;
                                                                       border-width: 2px;
                                                                       border-radius: 10px; /* Rounded corners */
                                                                       padding: 5px;
                                                                       min-height: 1px;
                                                                       min-width: 10px;
                                                                   }
                                                                   QPushButton:hover {
                                                                       background-color: #5F6A6A; /* Slightly darker green */
                                                                   }
                                                                   QPushButton:pressed {
                                                                       background-color: #979A9A; /* Even darker green */
                                                                   }
                                                               """)

    def check_validator(self, validator_model, entry):

        try:
            if float(entry.displayText()) <= validator_model.top() and float(
                    entry.displayText()) >= validator_model.bottom():
                return True
            else:
                QMessageBox.warning(self, "Error", "Input Out of range")
                return False
        except:
            # QMessageBox.warning(self, "Error", "Input Out of range 2")
            return False

