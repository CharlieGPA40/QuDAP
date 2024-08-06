import time

from PyQt6.QtWidgets import (
    QApplication, QWidget, QMessageBox, QGroupBox, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QPushButton, QComboBox, QLineEdit)
from PyQt6.QtGui import QFont, QIntValidator, QValidator, QDoubleValidator
from PyQt6.QtCore import pyqtSignal, Qt, QObject, QThread
import sys
import pyvisa as visa
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import random
import MultiPyVu as mpv # Uncommented it on the/thesever computer
from MultiPyVu import MultiVuClient as mvc, MultiPyVuError
import sys
import traceback
# import Data_Processing_Suite.GUI.Icon as Icon

class THREAD(QThread):
    update_data = pyqtSignal(float, str, float, str, str)  # Signal to emit the temperature and field values
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.running = True

    def run(self):
        while self.running:
            try:

                T, sT = self.client.get_temperature()
                F, sF = self.client.get_field()
                C = self.client.get_chamber()
                self.update_data.emit(T, sT, F, sF, C)
                time.sleep(1)  # Update every second
            except Exception as e:
                self.running = False

    def stop(self):
        self.running = False

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=300):
        fig = Figure(figsize=(width, height), dpi=dpi)

        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class PPMS(QWidget):

    def __init__(self):
        super().__init__()
        try:
            self.init_ui()
            self.isConnect = False

            self.server_thread = None
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def init_ui(self):
        titlefont = QFont("Arial", 25)
        font = QFont("Arial", 13)
        self.setStyleSheet("background-color: white;")

        # Create main vertical layout with centered alignment
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #  ---------------------------- PART 1 --------------------------------
        self.current_intrument_label = QLabel("Physical Property Measurement System")
        self.current_intrument_label.setFont(titlefont)
        self.current_intrument_label.setStyleSheet("""
                                            QLabel{
                                                background-color: white;
                                                }
                                                """)
        #  ---------------------------- PART 2 --------------------------------

        ppms_connection = QHBoxLayout()
        connection_group_box = QGroupBox("Device Connection")
        # Set the layout for the group box
        self.host_label = QLabel("Host:")
        self.host_label.setFont(font)

        self.host_entry_box = QLineEdit("127.0.0.1")
        self.host_entry_box.setFont(font)
        self.host_entry_box.setFixedHeight(30)

        self.port_label = QLabel("Port:")
        self.port_label.setFont(font)

        self.port_entry_box = QLineEdit("5000")
        self.port_entry_box.setFixedHeight(30)
        self.port_entry_box.setFont(font)

        self.server_btn = QPushButton('Start Server')
        self.server_btn_clicked = False
        self.server_btn.clicked.connect(self.start_server)

        self.connect_btn = QPushButton('Client Connect')
        self.connect_btn.setEnabled(False)
        self.connect_btn_clicked = False
        self.connect_btn.clicked.connect(self.connect_client)

        ppms_connection.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ppms_connection.addWidget(self.host_label,1)
        ppms_connection.addWidget(self.host_entry_box, 2)
        ppms_connection.addStretch(1)
        ppms_connection.addWidget(self.port_label, 1)
        ppms_connection.addWidget(self.port_entry_box, 2)
        ppms_connection.addStretch(1)
        ppms_connection.addWidget(self.server_btn, 1)
        ppms_connection.addWidget(self.connect_btn, 1)
        connection_group_box.setLayout(ppms_connection)

        #  ---------------------------- PART 3 --------------------------------
        temperature_reading_group_box = QGroupBox("Temperature (K)")  # Container widget for the horizontal layout
        temperature_main_layout = QVBoxLayout()
        temp_reading_layout = QHBoxLayout()
        self.cur_temp_Label = QLabel("Current Temperature:")
        self.cur_temp_Label.setFont(font)
        self.cur_temp_reading_Label = QLabel("N/A K")
        self.cur_temp_reading_Label.setFont(font)
        temp_reading_layout.addWidget(self.cur_temp_Label)
        temp_reading_layout.addWidget(self.cur_temp_reading_Label)

        temp_status_layout = QHBoxLayout()
        self.cur_temp_status_Label = QLabel("Status:")
        self.cur_temp_status_Label.setFont(font)
        self.cur_temp_status_reading_Label = QLabel("Unkown")
        self.cur_temp_status_reading_Label.setFont(font)
        temp_status_layout.addWidget(self.cur_temp_status_Label)
        temp_status_layout.addWidget(self.cur_temp_status_reading_Label)
        temperature_main_layout.addLayout(temp_reading_layout)
        temperature_main_layout.addLayout(temp_status_layout)
        temperature_reading_group_box.setLayout(temperature_main_layout)

        #  ---------------------------- PART 4 --------------------------------
        Field_reading_group_box = QGroupBox("Field (Oe)")  # Container widget for the horizontal layout
        Field_main_layout = QVBoxLayout()
        Field_reading_layout = QHBoxLayout()
        self.cur_field_Label = QLabel("Current Field:")
        self.cur_field_Label.setFont(font)
        self.cur_field_reading_Label = QLabel("N/A Oe")
        self.cur_field_reading_Label.setFont(font)
        Field_reading_layout.addWidget(self.cur_field_Label)
        Field_reading_layout.addWidget(self.cur_field_reading_Label)

        Field_status_layout = QHBoxLayout()
        self.cur_field_status_Label = QLabel("Status:")
        self.cur_field_status_Label.setFont(font)
        self.cur_field_status_reading_Label = QLabel("Unkown")
        self.cur_field_status_reading_Label.setFont(font)
        Field_status_layout.addWidget(self.cur_field_status_Label)
        Field_status_layout.addWidget(self.cur_field_status_reading_Label)
        Field_main_layout.addLayout(Field_reading_layout)
        Field_main_layout.addLayout(Field_status_layout)
        Field_reading_group_box.setLayout(Field_main_layout)

        #  ---------------------------- PART 5 --------------------------------
        Rot_reading_group_box = QGroupBox("Rotator (deg)")  # Container widget for the horizontal layout
        Rot_main_layout = QVBoxLayout()
        Rot_reading_layout = QHBoxLayout()
        self.cur_Rot_Label = QLabel("Current Degree:")
        self.cur_Rot_Label.setFont(font)
        self.cur_Rot_reading_Label = QLabel("N/A deg")
        self.cur_Rot_reading_Label.setFont(font)
        Rot_reading_layout.addWidget(self.cur_Rot_Label)
        Rot_reading_layout.addWidget(self.cur_Rot_reading_Label)

        Rot_status_layout = QHBoxLayout()
        self.cur_Rot_status_Label = QLabel("Status:")
        self.cur_Rot_status_Label.setFont(font)
        self.cur_Rot_status_reading_Label = QLabel("Unkown")
        self.cur_Rot_status_reading_Label.setFont(font)
        Rot_status_layout.addWidget(self.cur_Rot_status_Label)
        Rot_status_layout.addWidget(self.cur_Rot_status_reading_Label)
        Rot_main_layout.addLayout(Rot_reading_layout)
        Rot_main_layout.addLayout(Rot_status_layout)
        Rot_reading_group_box.setLayout(Rot_main_layout)

        #  ---------------------------- PART 6 --------------------------------
        Chamb_reading_group_box = QGroupBox("Chamber Status")  # Container widget for the horizontal layout
        Chamb_main_layout = QVBoxLayout()
        self.cur_chamb_status_reading_Label = QLabel("Unknown")
        self.cur_chamb_status_reading_Label.setFont(font)
        Chamb_main_layout.addWidget(self.cur_chamb_status_reading_Label)
        Chamb_reading_group_box.setLayout(Chamb_main_layout)

        #  ---------------------------- PART 7 --------------------------------
        temperature_setting_group_box = QGroupBox("Set Temperature")  # Container widget for the horizontal layout
        temperature_set_main_layout = QVBoxLayout()
        temp_value_setting_layout = QHBoxLayout()
        self.set_temp_Label = QLabel("Target Temperature:")
        self.set_temp_Label.setFont(font)
        self.cur_temp_entry_box = QLineEdit()
        self.cur_temp_entry_box.setFont(font)
        self.cur_temp_entry_box.setFixedHeight(30)
        # Create a QDoubleValidator with range 1.8 to 400.0 and precision of 2 decimal places
        self.temp_validator = QDoubleValidator(1.8, 400.0, 2)
        self.temp_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        #
        # # Set the validator to the QLineEdit
        # Set the validator to the QLineEdit
        self.cur_temp_entry_box.setValidator(self.temp_validator)
        self.cur_temp_entry_box.setPlaceholderText("Enter an temperature between 1.8 and 400")
        self.set_temp_unit_Label = QLabel("K")
        self.set_temp_unit_Label.setFont(font)
        temp_value_setting_layout.addWidget(self.set_temp_Label)
        temp_value_setting_layout.addWidget(self.cur_temp_entry_box)
        temp_value_setting_layout.addWidget(self.set_temp_unit_Label)

        temp_rate_setting_layout = QHBoxLayout()
        self.temp_rate_Label = QLabel("Rate:")
        self.temp_rate_Label.setFont(font)
        self.temp_rate_entry_box = QLineEdit()
        self.temp_rate_entry_box.setFixedHeight(30)
        self.temp_rate_entry_box.setFont(font)
        self.temp_rate_validator = QDoubleValidator(0, 50.0, 2)
        self.temp_rate_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.temp_rate_entry_box.setValidator(self.temp_rate_validator)
        self.temp_rate_entry_box.setPlaceholderText("Enter an rate between 1 and 50")
        self.temp_rate_unit_Label = QLabel("K/s")
        self.temp_rate_unit_Label.setFont(font)
        self.temp_rate_combo = QComboBox()
        with open("GUI/QSS/QComboWidget.qss", "r") as file:
            self.QCombo_stylesheet = file.read()
        self.temp_rate_combo.setStyleSheet(self.QCombo_stylesheet)
        self.temp_rate_combo.setFont(font)
        self.temp_rate_combo.addItems([""])
        self.temp_rate_combo.addItems(["Fast Settle"])
        self.temp_rate_combo.addItems(["No Overshoot"])
        temp_rate_setting_layout.addWidget(self.temp_rate_Label,1)
        temp_rate_setting_layout.addWidget(self.temp_rate_entry_box, 2)
        temp_rate_setting_layout.addWidget(self.temp_rate_unit_Label, 1)
        temp_rate_setting_layout.addWidget(self.temp_rate_combo, 2)
        set_button_layout = QHBoxLayout()
        self.set_temp_btn = QPushButton("Send")
        self.set_temp_btn.clicked.connect(self.setTemp)
        set_button_layout.addStretch(3)
        set_button_layout.addWidget(self.set_temp_btn)
        temperature_set_main_layout.addLayout(temp_value_setting_layout)
        temperature_set_main_layout.addLayout(temp_rate_setting_layout)
        temperature_set_main_layout.addLayout(set_button_layout)
        temperature_setting_group_box.setLayout(temperature_set_main_layout)

        #  ---------------------------- PART 8 --------------------------------
        Field_setting_group_box = QGroupBox("Set Field")  # Container widget for the horizontal layout
        Field_set_main_layout = QVBoxLayout()
        field_value_setting_layout = QHBoxLayout()
        self.set_field_Label = QLabel("Target Temperature:")
        self.set_field_Label.setFont(font)
        self.cur_field_entry_box = QLineEdit()
        self.cur_field_entry_box.setFixedHeight(30)
        self.cur_field_entry_box.setFont(font)
        self.field_validator = QDoubleValidator(-90000.00, 90000.0, 2)
        self.field_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.cur_field_entry_box.setValidator(self.field_validator)
        self.cur_field_entry_box.setPlaceholderText("Enter a field between -90000 and 90000")
        self.set_field_unit_Label = QLabel("Oe")
        self.set_field_unit_Label.setFont(font)
        field_value_setting_layout.addWidget(self.set_field_Label)
        field_value_setting_layout.addWidget(self.cur_field_entry_box)
        field_value_setting_layout.addWidget(self.set_field_unit_Label)

        field_rate_setting_layout = QHBoxLayout()
        self.field_rate_Label = QLabel("Rate:")
        self.field_rate_Label.setFont(font)
        self.field_rate_entry_box = QLineEdit()
        self.field_rate_entry_box.setFixedHeight(30)
        self.field_rate_entry_box.setFont(font)
        self.field_rate_validator = QDoubleValidator(0, 220.0, 2)
        self.field_rate_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.field_rate_entry_box.setValidator(self.field_rate_validator)
        self.field_rate_entry_box.setPlaceholderText("Enter an rate between 0 and 220")
        self.field_rate_unit_Label = QLabel("Oe/s")
        self.field_rate_unit_Label.setFont(font)
        self.field_rate_combo = QComboBox()
        self.field_rate_combo.setStyleSheet(self.QCombo_stylesheet)
        self.field_rate_combo.setFont(font)
        self.field_rate_combo.addItems([""])
        self.field_rate_combo.addItems(["Linear"])
        self.field_rate_combo.addItems(["No Overshoot"])
        self.field_rate_combo.addItems(["Oscillate"])
        field_rate_setting_layout.addWidget(self.field_rate_Label,1)
        field_rate_setting_layout.addWidget(self.field_rate_entry_box,2)
        field_rate_setting_layout.addWidget(self.field_rate_unit_Label,1)
        field_rate_setting_layout.addWidget(self.field_rate_combo, 2)
        field_set_button_layout = QHBoxLayout()
        self.set_field_btn = QPushButton("Send")
        self.set_field_btn.clicked.connect(self.setField)
        field_set_button_layout.addStretch(3)
        field_set_button_layout.addWidget(self.set_field_btn)
        Field_set_main_layout.addLayout(field_value_setting_layout)
        Field_set_main_layout.addLayout(field_rate_setting_layout)
        Field_set_main_layout.addLayout(field_set_button_layout)
        Field_setting_group_box.setLayout(Field_set_main_layout)

        #  ---------------------------- PART 9 --------------------------------
        chamber_setting_group_box = QGroupBox("Set Chamber")  # Container widget for the horizontal layout
        chamber_setting_layout = QHBoxLayout()
        self.chamber_set_Label = QLabel("Set Status:")
        self.chamber_set_Label.setFont(font)
        self.chamber_set_combo = QComboBox()
        self.chamber_set_combo.setStyleSheet(self.QCombo_stylesheet)
        self.chamber_set_combo.setFont(font)
        self.chamber_set_combo.addItems([""])
        self.chamber_set_combo.addItems(["Seal"])
        self.chamber_set_combo.addItems(["Purge/Seal"])
        self.chamber_set_combo.addItems(["Vent/Seal"])
        self.chamber_set_combo.addItems(["Pump Continuous"])
        self.chamber_set_combo.addItems(["Vent Continuous"])
        self.chamber_set_combo.addItems(["High Vacuum"])
        # self.chamber_set_combo.setEnabled(False)
        chamber_setting_layout.addWidget(self.chamber_set_Label, 1)
        chamber_setting_layout.addWidget(self.chamber_set_combo, 2)
        chamber_setting_layout.setContentsMargins(0,0,450,0)
        chamber_set_button_layout = QHBoxLayout()
        self.set_chamber_btn = QPushButton("Send")
        self.set_chamber_btn.clicked.connect(self.setChamber)
        chamber_set_button_layout.addStretch(3)
        chamber_set_button_layout.addWidget(self.set_chamber_btn)
        chamber_set_main_layout = QVBoxLayout()
        chamber_set_main_layout.addLayout(chamber_setting_layout)
        chamber_set_main_layout.addLayout(chamber_set_button_layout)
        chamber_setting_group_box.setLayout(chamber_set_main_layout)

        #  ---------------------------- Main Layout --------------------------------
        # Add widgets to the main layout with centered alignment
        main_layout.addWidget(self.current_intrument_label, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(connection_group_box)
        PPMS_reading_layout = QHBoxLayout()
        PPMS_reading_layout.addWidget(temperature_reading_group_box)
        PPMS_reading_layout.addWidget(Field_reading_group_box)
        main_layout.addLayout(PPMS_reading_layout)
        PPMS_reading_layout_2 = QHBoxLayout()
        PPMS_reading_layout_2.addWidget(Rot_reading_group_box)
        PPMS_reading_layout_2.addWidget(Chamb_reading_group_box)
        main_layout.addLayout(PPMS_reading_layout_2)
        main_layout.addWidget(temperature_setting_group_box)
        main_layout.addWidget(Field_setting_group_box)
        main_layout.addWidget(chamber_setting_group_box)
        self.setLayout(main_layout)

        #  ---------------------------- Style Sheet --------------------------------
        with open("GUI/QSS/QButtonWidget.qss", "r") as file:
            self.Button_stylesheet = file.read()
        self.connect_btn.setStyleSheet(self.Button_stylesheet)
        self.server_btn.setStyleSheet(self.Button_stylesheet)
        self.set_temp_btn.setStyleSheet(self.Button_stylesheet)
        self.set_field_btn.setStyleSheet(self.Button_stylesheet)
        self.set_chamber_btn.setStyleSheet(self.Button_stylesheet)

    def remote_server(self, flags: str = ''):
        user_flags = []
        if flags == '':
            user_flags = sys.argv[1:]
        else:
            msg = 'No flags detected; using hard-coded IP address'
            msg += 'for remote access.'

            # This value comes from the server PC's self-identified IPV4
            # address and needs to be manually input
            user_flags = ['-ip=172.19.159.4']

        # Opens the server connection
        self.remoteServer = mpv.Server(user_flags, keep_server_open=True)
        self.remoteServer.open()

    def start_server(self):
        if self.server_btn_clicked == False:
            # import Data_Processing_Suite.GUI.QDesign.run_server as s
            try:
                # user_flags = ['-ip=172.19.159.4']
                # self.server = mpv.Server(user_flags, keep_server_open=True)

                try:
                    # self.start_server_thread()
                    self.server = mpv.Server()
                    self.server.open()
                    self.server_btn.setText('Stop Server')
                    self.server_btn_clicked = True
                    self.connect_btn.setEnabled(True)
                except SystemExit as e:
                    QMessageBox.critical(self, 'No Server Opened', 'No running instance of MultiVu '
                                                        'was detected. Please start MultiVu and retry without administration')
                    return
                except Exception:
                    return

            except MultiPyVuError as e:
                tb_str = traceback.format_exc()
                QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                return
        elif self.server_btn_clicked == True:
            try:
                self.stop_threads()
                self.server_btn.setText('Start Server')
                self.server_btn_clicked = False
                self.connect_btn.setEnabled(False)
            except Exception as e:
                tb_str = traceback.format_exc()
                QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                return

    def connect_client(self):
        self.host = self.host_entry_box.text()
        self.port = self.port_entry_box.text()
        print(self.host)

        if self.connect_btn_clicked == False:
            try:
                self.connect_btn.setText('Stop Client')
                self.connect_btn_clicked = True
                self.server_btn.setEnabled(False)
                # Uncommented it on the client computer
                self.client_keep_going = True
                self.client = mpv.Client(host=self.host, port=5000)
                self.client.open()
                self.thread = THREAD(self.client)
                self.thread.update_data.connect(self.ppms_reading)
                self.thread.start()
            except Exception as e:
                tb_str = traceback.format_exc()
                QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                return

        elif self.connect_btn_clicked == True:
            try:
                self.client_keep_going = False
                self.connect_btn.setText('Start Client')
                self.client.close_client()
                # if self.PPMS_client_Thread is not None:
                #     self.PPMS_client_Thread.stop_client()
                #     self.PPMS_client_Thread.wait()
                # if self.thread is not None:
                #     self.thread.stop()
                self.connect_btn_clicked = False
                self.server_btn.setEnabled(True)
                self.cur_temp_reading_Label.setText('N/A K')
                self.cur_temp_status_reading_Label.setText('Unknown')
            except Exception as e:
                tb_str = traceback.format_exc()
                QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                return

    def store_client(self, client):
        self.client = client

    def ppms_reading(self, T, sT, F, sF, C):
        # Uncomment this section to enable ppms control
        self.C = C
        self.cur_temp_reading_Label.setText(f'{T} K')
        self.cur_temp_status_reading_Label.setText(f'{sT}')
        self.cur_field_reading_Label.setText(f'{F} Oe')
        self.cur_field_status_reading_Label.setText(f'{sF}')
        self.cur_chamb_status_reading_Label.setText(f'{C}')

        # """
        # This is only for test purpose
        # """
        # T, F = random.randint(2, 400), random.randint(-10000, 10000)
        # sF, sT, C = "Testing!","Testing!","Testing!"
        # self.cur_temp_reading_Label.setText(f'{T} K')
        # self.cur_temp_status_reading_Label.setText(f'{sT}')
        # self.cur_field_reading_Label.setText(f'{F} Oe')
        # self.cur_field_status_reading_Label.setText(f'{sF}')
        # self.cur_Rot_reading_Label.setText(f'{R} degs')
        # self.cur_Rot_status_reading_Label.setText(f'{sR}')
        # self.cur_chamb_status_reading_Label.setText(f'{C}')

    def setTemp(self):
        self.thread.stop()
        self.set_temp = self.cur_temp_entry_box.displayText()
        self.set_temp_rate = self.temp_rate_entry_box.displayText()
        self.temp_rate_method = self.temp_rate_combo.currentIndex()
        temperatureValidtor =self.check_validator(self.temp_validator, self.cur_temp_entry_box)
        temperatureRateValidtor = self.check_validator(self.temp_rate_validator, self.temp_rate_entry_box)
        if not temperatureValidtor or not temperatureRateValidtor:
            return
        if self.set_temp != '' and self.set_temp_rate != '' and self.temp_rate_method != 0:

            self.set_temp_rate = float(self.set_temp_rate)
            self.set_temp = float(self.set_temp)
            self.check_validator(self.temp_validator, self.cur_temp_entry_box)
            try:
                if self.temp_rate_method == 1:
                    self.client.set_temperature(self.set_temp,
                                           self.set_temp_rate,
                                           self.client.temperature.approach_mode.fast_settle)
                elif self.temp_rate_method == 2:
                    self.client.set_temperature(self.set_temp,
                                                self.set_temp_rate,
                                                self.client.temperature.approach_mode.no_overshoot)
                self.thread = THREAD(self.client)
                self.thread.update_data.connect(self.ppms_reading)
                self.thread.start()
            except MultiPyVuError:
                QMessageBox.warning(self, "Setup Fail", "Please try again!")
        else:
            QMessageBox.warning(self, "Input Missing", "Please enter all the required information")
        self.thread.start()

    def setField(self):
        self.thread.stop()
        self.set_Field = self.cur_field_entry_box.displayText()
        self.set_field_rate = self.field_rate_entry_box.displayText()
        self.field_rate_method = self.field_rate_combo.currentIndex()
        fieldValidtor = self.check_validator(self.field_validator, self.cur_field_entry_box)
        fieldRateValidtor = self.check_validator(self.field_rate_validator, self.field_rate_entry_box)
        if not fieldValidtor or not fieldRateValidtor:
            return
        if self.set_Field != '' and self.set_field_rate != '' and self.field_rate_method != 0:

            self.set_Field = float(self.set_Field)
            self.set_field_rate = float(self.set_field_rate)
            try:
                if self.field_rate_method == 1:
                    self.client.set_field(self.set_Field,
                                                self.set_field_rate,
                                                self.client.field.approach_mode.linear)

                if self.field_rate_method == 2:
                    self.client.set_field(self.set_Field,
                                           self.set_field_rate,
                                           self.client.field.approach_mode.no_overshoot)
                elif self.field_rate_method == 3:
                    self.client.set_field(self.set_Field,
                                                self.set_field_rate,
                                                self.client.field.approach_mode.oscillate)

                self.thread = THREAD(self.client)
                self.thread.update_data.connect(self.ppms_reading)
                self.thread.start()
            except MultiPyVuError as e:
                QMessageBox.warning(self, "Setup Fail", "Please try again!")
        else:
            QMessageBox.warning(self, "Input Missing", "Please enter all the required information")
        self.thread.start()

    def setChamber(self):
        self.thread.stop()
        time.sleep(1)
        self.set_Chamber = self.chamber_set_combo.currentIndex()
        self.chamber_set_combo.setEnabled(True)
        # if self.C == 'Sealed':
        #     self.chamber_set_combo.setCurrentIndex(1)
        # elif self.C == 'Purged and Sealed':
        #     self.chamber_set_combo.setCurrentIndex(2)
        # elif self.C == 'Purged and Sealed':
        #     self.chamber_set_combo.setCurrentIndex(3)
        # elif self.C == 'Purged and Sealed':
        #     self.chamber_set_combo.setCurrentIndex(4)
        # elif self.C == 'Purged and Sealed':
        #     self.chamber_set_combo.setCurrentIndex(5)
        # elif self.C == 'Purged and Sealed':
        #     self.chamber_set_combo.setCurrentIndex(6)

        if self.set_Chamber != 0:
            try:
                if self.set_Chamber == 1:
                    self.client.set_chamber(self.client.chamber.Mode.seal)
                elif self.set_Chamber == 2:
                    self.client.set_chamber(self.client.chamber.mode.purge_seal)
                elif self.set_Chamber == 3:
                    self.client.set_chamber(self.client.chamber.mode.vent_seal)
                elif self.set_Chamber == 4:
                    self.client.set_chamber(self.client.chamber.mode.pump_continuous)
                elif self.set_Chamber == 5:
                    self.client.set_chamber(self.client.chamber.mode.vent_continuous)
                elif self.set_Chamber == 6:
                    self.client.set_chamber(self.client.chamber.mode.high_vacuum)
                self.thread = THREAD(self.client)
                self.thread.update_data.connect(self.ppms_reading)
                self.thread.start()

            # except mpv.exceptions.MultiPyVuError:
            except Exception:
                pass
                # QMessageBox.warning(self, "Setup Fail", "Please try again!")

        else:
            QMessageBox.warning(self, "Input Missing", "Please enter all the required information")


    def check_validator(self, validator_model, entry):
        try:
            if float(entry.displayText()) <= validator_model.top() and float(entry.displayText()) >= validator_model.bottom():
                return True
            else:
                QMessageBox.warning(self, "Error", "Input Out of range")
                return False
        except:
            # QMessageBox.warning(self, "Error", "Input Out of range 2")
            return False

    def start_server_thread(self):
        self.server_thread = ServerThread(self.api_handler)
        self.server_thread.start()

    def display_error(self, error_message):
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle('Server Connection Error')
        error_box.setText('An error occurred while connecting to the server.')
        error_box.setDetailedText(error_message)
        error_box.exec()

    def stop_threads(self):
        if self.server_thread:
            self.api_handler.disconnect_server()
            self.server_thread.wait()