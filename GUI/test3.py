from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QMessageBox, QGroupBox, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QPushButton, QComboBox, QLineEdit, QScrollArea, QFrame, QRadioButton)
from PyQt6.QtGui import QIcon, QFont, QDoubleValidator
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
import MultiPyVu as mpv # Uncommented it on the/thesever computer
from MultiPyVu import MultiVuClient as mvc, MultiPyVuError


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=300):
        fig = Figure(figsize=(width, height), dpi=dpi)

        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class Measurement(QWidget):
    def __init__(self):
        super().__init__()
        self.isConnect = False
        self.init_ui()

    def init_ui(self):
        titlefont = QFont("Arial", 20)
        self.font = QFont("Arial", 13)
        self.setStyleSheet("background-color: white;")

        # Create main vertical layout with centered alignment
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.scroll_area = QScrollArea()
        # self.scroll_area.setWidgetResizable(True)
        # self.scroll_area.setLayout(self.main_layout)

        #  ---------------------------- PART 1 --------------------------------
        self.current_intrument_label = QLabel("Select Measurement")
        self.current_intrument_label.setFont(titlefont)
        self.current_intrument_label.setStyleSheet("""
                                                    QLabel{
                                                        background-color: white;
                                                        }
                                                        """)

        #  ---------------------------- PART 2 --------------------------------
        self.Preset_group_box = QGroupBox("Preseted Measure")
        self.ETO_radio_buttom = QRadioButton("ETO")
        self.FMR_radio_buttom = QRadioButton("FMR")

        self.reset_preset_buttom = QPushButton("Reset")
        self.select_preset_buttom = QPushButton("Select")
        self.select_preset_buttom.setStyleSheet("""
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

        self.reset_preset_buttom.setStyleSheet("""
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

        self.reset_preset_buttom.clicked.connect(self.preset_reset)
        self.select_preset_buttom.clicked.connect(self.preset_select)

        self.radio_btn_layout = QHBoxLayout(self)
        self.radio_btn_layout.addWidget(self.ETO_radio_buttom)
        self.radio_btn_layout.addWidget(self.FMR_radio_buttom)
        self.radio_btn_layout.addWidget(self.reset_preset_buttom)
        self.radio_btn_layout.addWidget(self.select_preset_buttom)

        self.Preset_group_box.setLayout(self.radio_btn_layout)

        self.preseted_content = QVBoxLayout(self)
        self.main_layout.addWidget(self.current_intrument_label, alignment=Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.Preset_group_box)

    def preset_reset(self):
        self.clear_layout(self, self.preseted_content)

    def preset_select(self):
        if self.ETO_radio_buttom.isChecked():
            self.FMR_radio_buttom.setChecked(False)
            print('checked')
            self.ETO_Preset()

        if self.FMR_radio_buttom.isChecked():
            self.ETO_radio_buttom.setChecked(False)

    def ETO_Preset(self):
        #--------------------------------------- Part connection ----------------------------
        self.connection_group_box = QGroupBox("Select Instruments")
        # --------------------------------------- Part connection_PPMS ----------------------------
        ppms_connection = QHBoxLayout()
        self.host_label = QLabel("Host:")
        self.host_label.setFont(self.font)
        self.host_entry_box = QLineEdit("127.0.0.1")
        self.host_entry_box.setFixedHeight(30)
        self.port_label = QLabel("Port:")
        self.port_label.setFont(self.font)
        self.port_entry_box = QLineEdit("5000")
        self.port_entry_box.setFixedHeight(30)
        self.server_btn = QPushButton('Start Server')
        self.server_btn_clicked = False
        self.server_btn.clicked.connect(self.start_server)
        self.connect_btn = QPushButton('Client Connect')
        self.connect_btn.setEnabled(False)
        self.connect_btn_clicked = False
        self.connect_btn.clicked.connect(self.connect_client)
        ppms_connection.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ppms_connection.addWidget(self.host_label, 1)
        ppms_connection.addWidget(self.host_entry_box, 2)
        ppms_connection.addStretch(1)
        ppms_connection.addWidget(self.port_label, 1)
        ppms_connection.addWidget(self.port_entry_box, 2)
        ppms_connection.addStretch(1)
        ppms_connection.addWidget(self.server_btn, 1)
        ppms_connection.addWidget(self.connect_btn, 1)
        self.preseted_content.addLayout(ppms_connection)
        # --------------------------------------- Part connection_otherGPIB ----------------------------
        Instru_main_layout = QHBoxLayout()
        self.Instruments_sel_label = QLabel("Select Instruments:")
        self.Instruments_sel_label.setFont(self.font)
        self.refresh_gpib_list()
        self.Instruments_combo = QComboBox()
        self.Instruments_combo.setFont(self.font)
        self.Instruments_combo.setStyleSheet("""
                                                            QComboBox {
                                                                padding: 4px;
                                                                background-color: white;
                                                                border: 2px solid #c0c0c0;
                                                                border-radius: 4px;
                                                                }
                                                            QComboBox::item:selected {
                                                                background-color: #FFFFFF;  /* Background color for selected item */
                                                                color: #7CACEC
                                                            }

                                                            QComboBox::drop-down {
                                                                subcontrol-origin: padding;
                                                                subcontrol-position: top right;
                                                                width: 38px;   /* Width of the arrow button */
                                                                border-left-width: 1px;
                                                                border-left-color: darkgray;
                                                                border-left-style: solid; /* just a single line at the left */
                                                                border-top-right-radius: 3px; /* same radius as the QComboBox */
                                                                border-bottom-right-radius: 3px;
                                                            }
                                                            QComboBox::down-arrow {
                                                                image: url(GUI/Icon/chevron-down.svg); /* Set your own icon for the arrow */
                                                            }
                                                            QComboBox::down-arrow:on { /* When the combo box is open */
                                                                top: 1px;
                                                                left: 1px;
                                                            }
                                                        """)
        self.Instruments_combo.addItems(["Select Instruments"])  # 0
        self.Instruments_combo.addItems(["Keithley 2182 nv"])  # 1
        self.Instruments_combo.addItems(["Keithley 6221"])  # 2
        self.Instruments_combo.addItems(["RF"])  # 3
        self.Instruments_combo.addItems(["Locked_in"])  # 4

        self.gpib_combo = QComboBox()
        self.gpib_combo.setStyleSheet("""
                            QComboBox {
                                padding: 5px;
                                background-color: white;
                                border: 2px solid #c0c0c0;
                                border-radius: 4px;
                                }
                            QComboBox::item:selected {
                                background-color: #FFFFFF;  /* Background color for selected item */
                                color: #7CACEC
                            }

                            QComboBox::drop-down {
                                subcontrol-origin: padding;
                                subcontrol-position: top right;
                                width: 20px;   /* Width of the arrow button */
                                border-left-width: 1px;
                                border-left-color: darkgray;
                                border-left-style: solid; /* just a single line at the left */
                                border-top-right-radius: 3px; /* same radius as the QComboBox */
                                border-bottom-right-radius: 3px;
                            }
                            QComboBox::down-arrow {
                                image: url(GUI/Icon/chevron-down.svg); /* Set your own icon for the arrow */
                            }
                            QComboBox::down-arrow:on { /* When the combo box is open */
                                top: 1px;
                                left: 1px;
                            }
                        """)
        self.gpib_combo.setFont(self.font)

        self.refresh_btn = QPushButton(icon=QIcon("GUI/Icon/refresh.svg"))
        self.refresh_btn.clicked.connect(self.refresh_gpib_list)

        self.instru_connect_btn = QPushButton('Connect')
        self.instru_connect_btn = False
        self.instru_connect_btn.clicked.connect(self.connect_current_gpib)

        Instru_main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        Instru_main_layout.addWidget(self.Instruments_sel_label)
        Instru_main_layout.addWidget(self.Instruments_combo)
        Instru_main_layout.addWidget(self.refresh_btn)
        Instru_main_layout.addWidget(self.instru_connect_btn)
        self.preseted_content.addLayout(Instru_main_layout)

        # --------------------------------------- Part PPMS_layout Init ----------------------------
        self.PPMS_measurement_setup_layout = QHBoxLayout()
        self.preseted_content.addLayout(self.PPMS_measurement_setup_layout)
        # --------------------------------------- Part PPMS_layout Init ----------------------------
        self.Instruments_measurement_setup_layout = QHBoxLayout()
        self.preseted_content.addLayout(self.PPMS_measurement_setup_layout)

        # --------------------------------------- Part PPMS_layout Init ----------------------------
        #  ---------------------------- Main Layout --------------------------------
        figure_group_box = QGroupBox("Graph")
        figure_Layout = QVBoxLayout()
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        toolbar = NavigationToolbar(self.canvas, self)
        toolbar.setStyleSheet("""
                                         QWidget {
                                             border: None; 
                                         }
                                     """)
        figure_Layout.addWidget(toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
        figure_Layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)
        figure_group_box.setLayout(figure_Layout)
        # graphing_layout.addWidget(plotting_control_group_box)
        # graphing_layout.addWidget(figure_group_box)
        #  ---------------------------- Main Layout --------------------------------

        self.setLayout(self.main_layout)

        #  ---------------------------- Style Sheet --------------------------------
        self.select_preset_buttom.setStyleSheet("""
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

        self.connect_btn.setStyleSheet("""
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
        self.refresh_btn.setStyleSheet("""
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

    def refresh_gpib_list(self):
        # Access GPIB ports using PyVISA
        rm = visa.ResourceManager()
        instruments = rm.list_resources()
        self.gpib_ports = [instr for instr in instruments if 'GPIB' in instr]
        # Clear existing items and add new ones
        self.gpib_combo.clear()
        self.gpib_combo.addItems(["None"])
        self.gpib_combo.addItems(self.gpib_ports)

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
                        self.send_btn.setText('Abort')
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

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def start_server(self):
        if self.server_btn_clicked == False:
            # import Data_Processing_Suite.GUI.QDesign.run_server as s
            self.server = mpv.Server()
            # user_flags = ['-ip=172.19.159.4']
            # self.server = mpv.Server(user_flags, keep_server_open=True)
            self.server_btn.setText('Stop Server')
            self.server_btn_clicked = True
            self.connect_btn.setEnabled(True)
            self.server.open()
        elif self.server_btn_clicked == True:
            self.server.close()  # Uncommented it on the sever computer
            self.server_btn.setText('Start Server')
            self.server_btn_clicked = False
            self.connect_btn.setEnabled(False)

    def connect_client(self):
        self.host = self.host_entry_box.displayText()
        self.port = self.port_entry_box.displayText()
        if self.connect_btn_clicked == False:
            self.connect_btn.setText('Stop Client')
            self.connect_btn_clicked = True
            self.server_btn.setEnabled(False)
            self.client_keep_going = True
            self.client = mpv.Client(host=self.host, port=5000)
            self.client.open()

            self.ppms_reading_group_box = QGroupBox('PPMS Reading')
            self.ppms_Temp_group_box = QGroupBox('Setup Experiment Temperature')
            self.ppms_Field_group_box = QGroupBox('Setup Experiment Field')
            # --------------------------------------- Part PPMS_Reading ----------------------------
            self.ppms_reading_layout = QVBoxLayout()
            self.ppms_temp_layout = QHBoxLayout()
            self.ppms_temp_label = QLabel('Temperature (K):')
            self.ppms_reading_temp_label = QLabel('N/A K')
            self.ppms_temp_layout.addWidget(self.ppms_temp_label)
            self.ppms_temp_layout.addWidget(self.ppms_reading_temp_label)

            self.ppms_field_layout = QHBoxLayout()
            self.ppms_field_label = QLabel('Field (Oe):')
            self.ppms_reading_field_label = QLabel('N/A Oe')
            self.ppms_field_layout.addWidget(self.ppms_field_label)
            self.ppms_field_layout.addWidget(self.ppms_reading_field_label)

            self.ppms_chamber_layout = QHBoxLayout()
            self.ppms_chamber_label = QLabel('Chamber Status:')
            self.ppms_reading_chamber_label = QLabel('N/A')
            self.ppms_chamber_layout.addWidget(self.ppms_chamber_label)
            self.ppms_chamber_layout.addWidget(self.ppms_reading_chamber_label)

            self.ppms_reading_layout.addLayout(self.ppms_temp_layout)
            self.ppms_reading_layout.addLayout(self.ppms_field_layout)
            self.ppms_reading_layout.addLayout(self.ppms_chamber_layout)

            self.ppms_reading_group_box.setLayout(self.ppms_reading_layout)
            # --------------------------------------- Part PPMS Temp Setup ----------------------------
            self.ppms_temp_setting_layout = QVBoxLayout()
            self.ppms_temp_list_layout = QHBoxLayout()
            self.ppms_temp_list_label_init = QLabel('Experiment Temperature (K): [')
            self.ppms_temp_list_label_init.setFont(self.font)
            self.ppms_temp_list_entry = QLineEdit()
            self.ppms_temp_list_entry.setFont(self.font)
            self.ppms_temp_list_label_end = QLabel(']')
            self.ppms_temp_list_label_end.setFont(self.font)

            self.ppms_temp_list_layout.addWidget(self.ppms_temp_list_label_init)
            self.ppms_temp_list_layout.addWidget(self.ppms_temp_list_entry)
            self.ppms_temp_list_layout.addWidget(self.ppms_temp_list_label_end)

            self.ppms_temp_setting_layout.addLayout(self.ppms_temp_list_layout)

            self.ppms_Temp_group_box.setLayout(self.ppms_temp_setting_layout)

            # --------------------------------------- Part PPMS Field Setup ----------------------------
            self.ppms_field_setting_layout = QVBoxLayout()
            self.ppms_field_radio_buttom_layout = QHBoxLayout()
            self.ppms_field_One_zone_radio = QRadioButton("1 Zone")
            self.ppms_field_One_zone_radio.toggled.connect(self.field_one_zone)
            self.ppms_field_Two_zone_radio = QRadioButton("2 Zones")
            self.ppms_field_One_zone_radio.toggled.connect(self.field_two_zone)
            self.ppms_field_Three_zone_radio = QRadioButton("3 Zones")
            self.ppms_field_Three_zone_radio.toggled.connect(self.field_three_zone)
            self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_One_zone_radio)
            self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_Two_zone_radio)
            self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_Three_zone_radio)
            self.ppms_field_setting_layout.addLayout(self.ppms_field_radio_buttom_layout)
            self.ppms_Field_group_box.setLayout(self.ppms_field_setting_layout)


            self.PPMS_measurement_setup_layout.addWidget(self.ppms_reading_group_box)
            self.PPMS_measurement_setup_layout.addWidget(self.ppms_Temp_group_box)



        elif self.connect_btn_clicked == True:
            self.client.close_client()
            self.clear_layout(self.PPMS_measurement_setup_layout)
            self.client_keep_going = False
            self.connect_btn.setText('Start Client')
            self.connect_btn_clicked = False
            self.server_btn.setEnabled(True)


    def connect_current_gpib(self):
        rm = visa.ResourceManager()
        self.current_connection_index = self.Instruments_combo.currentIndex()
        self.current_connection = self.gpib_combo.currentText()
        try:
            if self.current_connection == 'None':
                return None
            elif self.current_connection_index == 1:
                self.keithley_2182nv = rm.open_resource(self.current_connection, timeout=10000)



            elif self.current_connection_index == 2:
                self.keithley_6221 = rm.open_resource(self.current_connection, timeout=10000)
            elif self.current_connection_index == 3:
                self.keithley_6221 = rm.open_resource(self.current_connection, timeout=10000)
            elif self.current_connection_index == 4:
                self.keithley_6221 = rm.open_resource(self.current_connection, timeout=10000)
        except visa.errors.VisaIOError:
            QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")



    def field_one_zone(self):

        self.ppms_temp_list_label_init = QLabel('Experiment Temperature (K): [')
        self.ppms_temp_list_label_init.setFont(self.font)
        self.ppms_temp_list_entry = QLineEdit()
        self.ppms_temp_list_entry.setFont(self.font)
        self.ppms_temp_list_label_end = QLabel(']')
        self.ppms_temp_list_label_end.setFont(self.font)

        self.ppms_temp_list_layout.addWidget(self.ppms_temp_list_label_init)
        self.ppms_temp_list_layout.addWidget(self.ppms_temp_list_entry)
        self.ppms_temp_list_layout.addWidget(self.ppms_temp_list_label_end)

        self.ppms_temp_setting_layout.addLayout(self.ppms_temp_list_layout)

        self.ppms_Temp_group_box.setLayout(self.ppms_temp_setting_layout)

        self.PPMS_measurement_setup_layout.addWidget(self.ppms_Field_group_box)


