import sys
from PyQt6.QtWidgets import (
    QSizePolicy, QWidget, QMessageBox, QGroupBox, QFileDialog, QVBoxLayout, QLabel, QHBoxLayout,
    QCheckBox, QTextEdit, QPushButton, QComboBox, QLineEdit, QScrollArea, QDialog, QRadioButton, QMainWindow,
    QDialogButtonBox, QProgressBar, QButtonGroup, QApplication, QCompleter
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread
from PyQt6.QtGui import QKeyEvent
import pyvisa as visa
import matplotlib
import numpy as np
import csv

# for simulation purpose
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import random
import time
import MultiPyVu as mpv  # Uncommented it on the server computer
from MultiPyVu import MultiVuClient as mvc, MultiPyVuError
from datetime import datetime
import traceback
import os
import requests

import QuDAP.GUI.QDesign as QDesign
class Worker(QThread):
    progress_update = pyqtSignal(int)
    append_text = pyqtSignal(str, str)
    stop_measurment = pyqtSignal()
    update_ppms_temp_reading_label = pyqtSignal(str, str)
    update_ppms_field_reading_label = pyqtSignal(str, str)
    update_ppms_chamber_reading_label = pyqtSignal(str)
    update_nv_channel_1_label = pyqtSignal(str)
    update_nv_channel_2_label = pyqtSignal(str)
    update_lockin_label = pyqtSignal(str, str)
    clear_plot = pyqtSignal()
    update_plot = pyqtSignal(list, list, str, bool, bool)
    save_plot = pyqtSignal(list, list, str, bool, bool, bool, str, str)
    measurement_finished = pyqtSignal()
    error_message = pyqtSignal(str, str)

    def __init__(self, measurement_instance, keithley_6221, keithley_2182nv, DSP_7265, current, TempList, topField, botField,
                 folder_path, client, tempRate, current_mag, current_unit, file_name, run, number_of_field,
                 field_mode_fixed, nv_channel_1_enabled, nv_channel_2_enabled,nv_NPLC, ppms_field_One_zone_radio_enabled,
                 ppms_field_Two_zone_radio_enabled, ppms_field_Three_zone_radio_enabled, zone1_step_field, zone2_step_field,
                 zone3_step_field, zone1_top_field, zone2_top_field, zone3_top_field, zone1_field_rate, zone2_field_rate,
                 zone3_field_rate, Keithley_2182_Connected, Ketihley_6221_Connected, BNC845RF_Connected,
                 DSP7265_Connected):
        super().__init__()
        self.measurement_instance = measurement_instance
        self.running = True
        self.keithley_6221 = keithley_6221
        self.keithley_2182nv = keithley_2182nv
        self.DSP7265 = DSP_7265
        self.current = current
        self.TempList = TempList
        self.topField = topField
        self.botField = botField
        self.folder_path = folder_path
        self.client = client
        self.tempRate = tempRate
        self.current_mag = current_mag
        self.current_unit = current_unit
        self.file_name = file_name
        self.run = run
        self.number_of_field = number_of_field
        self.field_mode_fixed = field_mode_fixed
        self.nv_channel_1_enabled = nv_channel_1_enabled
        self.nv_channel_2_enabled = nv_channel_2_enabled
        self.nv_NPLC = nv_NPLC
        self.ppms_field_One_zone_radio_enabled = ppms_field_One_zone_radio_enabled
        self.ppms_field_Two_zone_radio_enabled = ppms_field_Two_zone_radio_enabled
        self.ppms_field_Three_zone_radio_enabled = ppms_field_Three_zone_radio_enabled
        self.zone1_step_field = zone1_step_field
        self.zone2_step_field = zone2_step_field
        self.zone3_step_field = zone3_step_field
        self.zone1_top_field = zone1_top_field
        self.zone1_top_field = zone1_top_field
        self.zone2_top_field = zone2_top_field
        self.zone3_top_field = zone3_top_field
        self.zone1_field_rate = zone1_field_rate
        self.zone2_field_rate = zone2_field_rate
        self.zone3_field_rate = zone3_field_rate
        self.Keithley_2182_Connected = Keithley_2182_Connected
        self.Ketihley_6221_Connected = Ketihley_6221_Connected
        self.BNC845RF_Connected = BNC845RF_Connected
        self.DSP7265_Connected = DSP7265_Connected

    def run(self):

        try:
            self.measurement_instance.run_ETO(self.append_text.emit, self.progress_update.emit,
                                              self.stop_measurment.emit, self.update_ppms_temp_reading_label.emit,
                                              self.update_ppms_field_reading_label.emit,
                                              self.update_ppms_chamber_reading_label.emit,
                                              self.update_nv_channel_1_label.emit,
                                              self.update_nv_channel_2_label.emit,
                                              self.update_lockin_label.emit,
                                              self.clear_plot.emit, self.update_plot.emit, self.save_plot.emit,
                                              self.measurement_finished.emit,
                                              self.error_message.emit,
                                              keithley_6221 =self.keithley_6221,
                                              keithley_2182nv=self.keithley_2182nv,
                                              DSP7265=self.DSP7265,
                                              current=self.current, TempList=self.TempList, topField=self.topField,
                                              botField=self.botField,
                                              folder_path=self.folder_path, client=self.client,
                                              tempRate=self.tempRate, current_mag=self.current_mag,
                                              current_unit=self.current_unit, file_name=self.file_name,
                                              run=self.run, number_of_field=self.number_of_field,
                                              field_mode_fixed=self.field_mode_fixed,
                                              nv_channel_1_enabled=self.nv_channel_1_enabled,
                                              nv_channel_2_enabled=self.nv_channel_2_enabled,
                                              nv_NPLC=self.nv_NPLC,
                                              ppms_field_One_zone_radio_enabled=self.ppms_field_One_zone_radio_enabled,
                                              ppms_field_Two_zone_radio_enabled=self.ppms_field_Two_zone_radio_enabled,
                                              ppms_field_Three_zone_radio_enabled=self.ppms_field_Three_zone_radio_enabled,
                                              zone1_step_field=self.zone1_step_field,
                                              zone2_step_field=self.zone2_step_field,
                                              zone3_step_field=self.zone3_step_field,
                                              zone1_top_field=self.zone1_top_field,
                                              zone2_top_field=self.zone2_top_field,
                                              zone3_top_field=self.zone3_top_field,
                                              zone1_field_rate=self.zone1_field_rate,
                                              zone2_field_rate=self.zone2_field_rate,
                                              zone3_field_rate=self.zone3_field_rate,
                                              Keithley_2182_Connected=self.Keithley_2182_Connected,
                                              Ketihley_6221_Connected=self.Ketihley_6221_Connected,
                                              BNC845RF_Connected=self.BNC845RF_Connected,
                                              DSP7265_Connected=self.DSP7265_Connected,
                                              running=lambda: self.running)
            self.running = False
            self.stop()
            return
        except SystemExit as e:
            print(e)
        except Exception as e:
            tb_str = traceback.format_exc()
            print(f'{tb_str} {str(e)}')

    def stop(self):
        self.running = False
        print("STOP")

class LogWindow(QDialog):
    def __init__(self):
        super().__init__()

        def read_bot_token(file_path):
            with open(file_path, 'r') as file:
                # Read the first line, which should be the token
                bot_token = file.readline().strip()
            return bot_token

        # Path to the text file containing the bot token
        self.token_file = 'bot.txt'
        self.setWindowTitle('Log Window')
        self.font = QFont("Arial", 13)
        self.ID = None
        self.Measurement = None
        self.run = None
        self.folder_path = None
        self.setStyleSheet('Background: white')
        with open("GUI/SHG/QButtonWidget.qss", "r") as file:
            self.Browse_Button_stylesheet = file.read()
        self.layout = QVBoxLayout()
        self.User_layout = QHBoxLayout()
        self.User_label = QLabel('User: ')
        self.User_label.setFont(self.font)
        self.User_entry_box = QLineEdit(self)
        self.User_entry_box.setFont(self.font)
        self.User_layout.addWidget(self.User_label)
        self.User_layout.addWidget(self.User_entry_box)

        user_hints = ["Chunli Tang"]
        user_completer = QCompleter(user_hints, self.User_entry_box)
        self.User_entry_box.setCompleter(user_completer)

        self.output_folder_layout = QHBoxLayout()
        self.output_folder_label = QLabel('Output Folder: ')
        self.output_folder_label.setFont(self.font)
        self.folder_entry_box = QLineEdit(self)
        self.folder_entry_box.setFont(self.font)
        self.folder_entry_box.setEnabled(False)
        self.browse_button = QPushButton('Browse')
        self.browse_button.setStyleSheet(self.Browse_Button_stylesheet)
        self.browse_button.clicked.connect(self.open_folder_dialog)
        self.output_folder_layout.addWidget(self.output_folder_label)
        self.output_folder_layout.addWidget(self.folder_entry_box)
        self.output_folder_layout.addWidget(self.browse_button)

        today = datetime.today()
        self.formatted_date = today.strftime("%m%d%Y")
        self.Date_layout = QHBoxLayout()
        self.Date_label = QLabel("Today's Date:")
        self.Date_label.setFont(self.font)
        self.Date_entry_box = QLineEdit(self)
        self.Date_entry_box.setFont(self.font)
        self.Date_entry_box.setEnabled(False)
        self.Date_entry_box.setText(str(self.formatted_date))
        self.Date_layout.addWidget(self.Date_label)
        self.Date_layout.addWidget(self.Date_entry_box)

        self.Sample_ID_layout = QHBoxLayout()
        self.Sample_ID_label = QLabel("Sample ID:")
        self.Sample_ID_label.setFont(self.font)
        self.Sample_ID_entry_box = QLineEdit(self)
        self.Sample_ID_entry_box.setFont(self.font)
        self.Sample_ID_entry_box.textChanged.connect(self.update_ID)
        self.Sample_ID_layout.addWidget(self.Sample_ID_label)
        self.Sample_ID_layout.addWidget(self.Sample_ID_entry_box)

        self.Measurement_type_layout = QHBoxLayout()
        self.Measurement_type_label = QLabel("Measurement Type:")
        self.Measurement_type_label.setFont(self.font)
        self.Measurement_type_entry_box = QLineEdit(self)
        self.Measurement_type_entry_box.setFont(self.font)
        self.Measurement_type_entry_box.textChanged.connect(self.update_measurement)
        self.Measurement_type_layout.addWidget(self.Measurement_type_label)
        self.Measurement_type_layout.addWidget(self.Measurement_type_entry_box)

        measurement_hints = ["ETO", "ETO_Rxx_in_plane", "ETO_Rxx_out_of_plane", "ETO_Rxy_in_plane","ETO_Rxy_out_of_plane", 
                             "ETO_Rxy_Rxx_in_plane", "ETO_Rxy_Rxx_out_of_plane"]
        measurement_completer = QCompleter(measurement_hints, self.Measurement_type_entry_box)
        self.Measurement_type_entry_box.setCompleter(measurement_completer)

        self.run_number_layout = QHBoxLayout()
        self.run_number_label = QLabel("Run Number:")
        self.run_number_label.setFont(self.font)
        self.run_number_entry_box = QLineEdit(self)
        self.run_number_entry_box.setFont(self.font)
        self.run_number_entry_box.textChanged.connect(self.update_run_number)
        self.run_number_layout.addWidget(self.run_number_label)
        self.run_number_layout.addWidget(self.run_number_entry_box)

        self.comment_layout = QHBoxLayout()
        self.comment_label = QLabel("Comment:")
        self.comment_label.setFont(self.font)
        self.comment_entry_box = QLineEdit(self)
        self.comment_entry_box.setFont(self.font)
        self.comment_layout.addWidget(self.comment_label)
        self.comment_layout.addWidget(self.comment_entry_box)

        self.example_file_name = QLabel()

        self.random_number = random.randint(100000, 999999)
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.ID}_{self.Measurement}_300_K_20_uA_Run_{self.run}.txt"
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

        self.button_box.setStyleSheet(self.Browse_Button_stylesheet)
        self.example_file_name.setText(self.file_name)
        self.layout.addLayout(self.User_layout)
        self.layout.addLayout(self.output_folder_layout)
        self.layout.addLayout(self.Date_layout)
        self.layout.addLayout(self.Sample_ID_layout)
        self.layout.addLayout(self.Measurement_type_layout)
        self.layout.addLayout(self.run_number_layout)
        self.layout.addLayout(self.comment_layout)
        self.layout.addWidget(self.button_box)
        self.layout.addWidget(self.example_file_name)

        self.setLayout(self.layout)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def update_ID(self, text):
        # Replace spaces with underscores in the text
        self.ID = self.Sample_ID_entry_box.text()
        self.ID = text.replace(" ", "_")
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.ID}_{self.Measurement}_300_K_20_uA_Run_{self.run}.txt"
        self.example_file_name.setText(self.file_name)

    def update_measurement(self, text):
        # Replace spaces with underscores in the text
        self.Measurement = self.Measurement_type_entry_box.text()
        self.Measurement = text.replace(" ", "_")
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.ID}_{self.Measurement}_300_K_20_uA_Run_{self.run}.txt"
        self.example_file_name.setText(self.file_name)

    def update_run_number(self, text):
        # Replace spaces with underscores in the text
        self.run = self.run_number_entry_box.text()
        self.run = text.replace(" ", "_")
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.ID}_{self.Measurement}_300_K_20_uA_Run_{self.run}.csv"
        self.example_file_name.setText(self.file_name)

    def open_folder_dialog(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if self.folder_path:
            self.folder_path = self.folder_path +'/'
            self.folder_entry_box.setText(self.folder_path)

    def accept(self):
        self.User = self.User_entry_box.text()
        self.commemt = self.comment_entry_box.text()
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.ID}_{self.Measurement}"
        # Call the inherited accept method to close the dialog
        if self.User != '' and self.folder_path != '' and self.commemt != '' and self.ID != '' and self.Measurement != '' and self.run != '':
            super().accept()
        else:
            QMessageBox.warning(self, 'Warning', 'Please enter the log completely!')

    def get_text(self):
        return self.folder_path, self.file_name, self.formatted_date, self.ID, self.Measurement, self.run, self.commemt, self.User

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=100, height=4, dpi=300):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class Measurement(QMainWindow):
    def __init__(self):
        super().__init__()

        try:
            self.preseted = False
            self.Keithley_2182_Connected = False
            self.Ketihley_6221_Connected = False
            self.BNC845RF_Connected = False
            self.DSP7265_Connected = False
            self.field_mode_fixed = None
            self.keithley_2182nv = None
            self.keithley_6221 = None
            self.DSP7265 = None
            self.worker = None  # Initialize the worker to None
            self.init_ui()
            self.ppms_field_One_zone_radio_enabled = False
            self.ppms_field_Two_zone_radio_enabled = False
            self.ppms_field_Three_zone_radio_enabled = False
            self.nv_channel_1_enabled = None
            self.nv_channel_2_enabled = None
            self.nv_NPLC = None
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
            return

    def init_ui(self):
        titlefont = QFont("Arial", 20)
        self.font = QFont("Arial", 13)
        self.setStyleSheet("background-color: white;")
        with open("GUI/QSS/QScrollbar.qss", "r") as file:
            self.scrollbar_stylesheet = file.read()
        # Create a QScrollArea
        self.scroll_area = QScrollArea()
        # self.scroll_area.setFixedSize(1200,920)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(self.scrollbar_stylesheet)
        # Create a widget to hold the main layout
        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)

        # Create main vertical layout with centered alignment
        self.main_layout = QVBoxLayout(self.content_widget)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set the content widget to expand
        self.content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        #  ---------------------------- PART 1 --------------------------------
        self.current_intrument_label = QLabel("Start Measurement")
        self.current_intrument_label.setFont(titlefont)
        self.current_intrument_label.setStyleSheet("""
                                                    QLabel{
                                                        background-color: white;
                                                        }
                                                        """)

        #  ---------------------------- PART 2 --------------------------------
        with open("GUI/QSS/QButtonWidget.qss", "r") as file:
            self.Button_stylesheet = file.read()
        self.Preset_group_box = QGroupBox("Experiment Preset")

        self.ETO_radio_buttom = QRadioButton("ETO")
        self.ETO_radio_buttom.setFont(self.font)
        self.FMR_radio_buttom = QRadioButton("FMR")
        self.FMR_radio_buttom.setFont(self.font)
        self.reset_preset_buttom = QPushButton("Reset")
        self.select_preset_buttom = QPushButton("Select")
        self.select_preset_buttom.setStyleSheet(self.Button_stylesheet)
        self.reset_preset_buttom.setStyleSheet(self.Button_stylesheet)

        self.reset_preset_buttom.clicked.connect(self.preset_reset)
        self.select_preset_buttom.clicked.connect(self.preset_select)

        self.preset_layout = QVBoxLayout()
        self.radio_btn_layout = QHBoxLayout()
        self.radio_btn_layout.addStretch(2)
        self.radio_btn_layout.addWidget(self.ETO_radio_buttom)
        self.radio_btn_layout.addStretch(1)
        self.radio_btn_layout.addWidget(self.FMR_radio_buttom)
        self.radio_btn_layout.addStretch(2)

        self.select_preset_btn_layout = QHBoxLayout()
        self.select_preset_btn_layout.addWidget(self.reset_preset_buttom)
        self.select_preset_btn_layout.addWidget(self.select_preset_buttom)

        self.preset_layout.addLayout(self.radio_btn_layout)
        self.preset_layout.addLayout(self.select_preset_btn_layout)
        self.Preset_group_box.setLayout(self.preset_layout)

        self.preset_container = QWidget()
        self.preset_container.setFixedSize(380, 180)

        self.preset_container_layout = QHBoxLayout()
        self.preset_container_layout.addWidget(self.Preset_group_box, 1)
        self.preset_container.setLayout(self.preset_container_layout)

        self.instrument_connection_layout = QHBoxLayout()
        self.instrument_connection_layout.addWidget(self.preset_container)
        self.Instruments_Content_Layout = QVBoxLayout()
        self.main_layout.addWidget(self.current_intrument_label, alignment=Qt.AlignmentFlag.AlignTop)
        self.main_layout.addLayout(self.instrument_connection_layout)
        self.main_layout.addLayout(self.Instruments_Content_Layout)

        # Set the scroll area as the central widget of the main window
        self.setCentralWidget(self.scroll_area)

    def preset_reset(self):
        try:
            self.preseted = False
            self.running = False
            self.clear_layout(self.Instruments_Content_Layout)
            try:
                self.clear_layout(self.graphing_layout)
                self.clear_layout(self.buttons_layout)
                self.instrument_connection_layout.removeWidget(self.ppms_container)
                self.ppms_container.deleteLater()
                self.instrument_connection_layout.removeWidget(self.instrument_container)
                self.instrument_container.deleteLater()
                self.main_layout.removeWidget(self.button_container)
                self.button_container.deleteLater()
                self.main_layout.removeWidget(self.log_box)
                self.log_box.deleteLater()
                self.main_layout.removeWidget(self.progress_bar)
                self.progress_bar.deleteLater()

            except Exception as e:
                pass
            try:
                self.stop_measurement()
                self.keithley_6221.close()
                self.keithley_2182nv.close()
                self.DSP7265.close()
            except Exception as e:
                pass
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
            return

    def preset_select(self):
        if self.preseted == False:
            self.preseted = True
            with open("GUI/QSS/QComboWidget.qss", "r") as file:
                self.QCombo_stylesheet = file.read()
            # --------------------------------------- Part connection ----------------------------
            self.ppms_container = QWidget()
            self.ppms_main_layout = QHBoxLayout()
            self.connection_group_box = QGroupBox("PPMS Connection")
            self.connection_box_layout = QVBoxLayout()
            # --------------------------------------- Part connection_PPMS ----------------------------
            self.ppms_connection = QVBoxLayout()
            self.ppms_host_connection_layout = QHBoxLayout()
            self.ppms_port_connection_layout = QHBoxLayout()
            self.ppms_connection_button_layout = QHBoxLayout()
            self.host_label = QLabel("PPMS Host:")
            self.host_label.setFont(self.font)
            self.host_entry_box = QLineEdit("127.0.0.1")
            self.host_entry_box.setFont(self.font)
            self.host_entry_box.setFixedHeight(30)
            self.port_label = QLabel("PPMS Port:")
            self.port_label.setFont(self.font)
            self.port_entry_box = QLineEdit("5000")
            self.port_entry_box.setFont(self.font)
            self.port_entry_box.setFixedHeight(30)
            self.server_btn = QPushButton('Start Server')
            self.server_btn_clicked = False
            self.server_btn.clicked.connect(self.start_server)
            self.connect_btn = QPushButton('Client Connect')
            self.connect_btn.setEnabled(False)
            self.connect_btn_clicked = False
            self.connect_btn.clicked.connect(self.connect_client)

            self.ppms_host_connection_layout.addWidget(self.host_label, 1)
            self.ppms_host_connection_layout.addWidget(self.host_entry_box, 2)

            self.ppms_port_connection_layout.addWidget(self.port_label, 1)
            self.ppms_port_connection_layout.addWidget(self.port_entry_box, 2)

            self.ppms_connection_button_layout.addWidget(self.server_btn)
            self.ppms_connection_button_layout.addWidget(self.connect_btn)

            self.ppms_connection.addLayout(self.ppms_host_connection_layout)
            self.ppms_connection.addLayout(self.ppms_port_connection_layout)
            self.ppms_connection.addLayout(self.ppms_connection_button_layout)

            self.connection_group_box.setLayout(self.ppms_connection)
            self.ppms_main_layout.addWidget(self.connection_group_box)
            self.ppms_container.setFixedSize(380, 180)
            self.ppms_container.setLayout(self.ppms_main_layout)

            self.instrument_connection_layout.addWidget(self.ppms_container)

            self.instrument_container = QWidget()
            self.instrument_main_layout = QHBoxLayout()
            self.instrument_connection_group_box = QGroupBox("Select Instruments")
            self.instrument_connection_box_layout = QVBoxLayout()

            self.Instru_main_layout = QVBoxLayout()
            self.instru_select_layout = QHBoxLayout()
            self.instru_connection_layout = QHBoxLayout()
            self.instru_cnt_btn_layout = QHBoxLayout()
            self.Instruments_sel_label = QLabel("Select Instruments:")
            self.Instruments_sel_label.setFont(self.font)
            self.Instruments_combo = QComboBox()
            self.Instruments_combo.setFont(self.font)
            self.Instruments_combo.setStyleSheet(self.QCombo_stylesheet)
            if self.ETO_radio_buttom.isChecked():
                self.Instruments_combo.addItems(
                    ["Select Instruments", "Keithley 2182 nv", "Keithley 6221", "DSP 7265 Lock-in"])
            elif self.FMR_radio_buttom.isChecked():
                self.Instruments_combo.addItems(["BNC 845 RF", "DSP 7265 Lock-in"])
            self.Instruments_combo.currentIndexChanged.connect(self.instru_combo_index_change)

            self.Instruments_port_label = QLabel("Channel:")
            self.Instruments_port_label.setFont(self.font)
            self.connection_combo = QComboBox()
            self.connection_combo.setStyleSheet(self.QCombo_stylesheet)
            self.connection_combo.setFont(self.font)

            self.refresh_btn = QPushButton(icon=QIcon("GUI/Icon/refresh.svg"))
            self.refresh_btn.clicked.connect(self.refresh_Connection_List)
            self.instru_connect_btn = QPushButton('Connect')
            self.instru_connect_btn.clicked.connect(self.connect_devices)
            self.instru_select_layout.addWidget(self.Instruments_sel_label, 1)
            self.instru_select_layout.addWidget(self.Instruments_combo, 2)

            self.instru_connection_layout.addWidget(self.Instruments_port_label, 1)
            self.instru_connection_layout.addWidget(self.connection_combo, 3)
            self.refresh_Connection_List()
            self.instru_cnt_btn_layout.addWidget(self.refresh_btn, 2)
            self.instru_cnt_btn_layout.addWidget(self.instru_connect_btn, 2)
            self.Instru_main_layout.addLayout(self.instru_select_layout)
            self.Instru_main_layout.addLayout(self.instru_connection_layout)
            self.Instru_main_layout.addLayout(self.instru_cnt_btn_layout)
            self.instrument_connection_group_box.setLayout(self.Instru_main_layout)
            self.instrument_main_layout.addWidget(self.instrument_connection_group_box)
            self.instrument_container.setFixedSize(380, 180)
            self.instrument_container.setLayout(self.instrument_main_layout)
            self.instrument_connection_layout.addWidget(self.instrument_container)

            self.PPMS_measurement_setup_layout = QHBoxLayout()
            self.Instruments_Content_Layout.addLayout(self.PPMS_measurement_setup_layout)

            self.Instruments_measurement_setup_layout = QHBoxLayout()
            self.Instruments_Content_Layout.addLayout(self.Instruments_measurement_setup_layout)

            self.main_layout.addLayout(self.Instruments_Content_Layout)

            self.graphing_layout = QHBoxLayout()

            figure_group_box = QGroupBox("Graph")
            figure_Layout = QVBoxLayout()
            self.canvas = MplCanvas(self, width=100, height=4, dpi=100)
            self.canvas.axes_2 = self.canvas.axes.twinx()
            toolbar = NavigationToolbar(self.canvas, self)
            toolbar.setStyleSheet("""
                                             QWidget {
                                                 border: None;
                                             }
                                         """)
            figure_Layout.addWidget(toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
            figure_Layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)
            figure_group_box.setLayout(figure_Layout)
            figure_group_box.setFixedSize(1150,400)
            self.figure_container_layout = QHBoxLayout()
            self.figure_container = QWidget(self)
            self.buttons_layout = QHBoxLayout()
            self.start_measurement_btn = QPushButton('Start')
            self.start_measurement_btn.clicked.connect(self.start_measurement)
            self.stop_btn = QPushButton('Stop')
            self.stop_btn.clicked.connect(self.stop_measurement)
            self.rst_btn = QPushButton('Reset')
            self.rst_btn.clicked.connect(self.rst)
            self.start_measurement_btn.setStyleSheet(self.Button_stylesheet)
            self.stop_btn.setStyleSheet(self.Button_stylesheet)
            self.rst_btn.setStyleSheet(self.Button_stylesheet)
            self.buttons_layout.addStretch(4)
            self.buttons_layout.addWidget(self.rst_btn)
            self.buttons_layout.addWidget(self.stop_btn)
            self.buttons_layout.addWidget(self.start_measurement_btn)

            self.button_container = QWidget()
            self.button_container.setLayout(self.buttons_layout)
            self.button_container.setFixedSize(1150,80)

            self.figure_container_layout.addWidget(figure_group_box)
            self.figure_container.setLayout(self.figure_container_layout)
            self.graphing_layout.addWidget(self.figure_container)
            self.main_layout.addLayout(self.graphing_layout)
            self.main_layout.addWidget(self.button_container)

            self.setCentralWidget(self.scroll_area)

            self.select_preset_buttom.setStyleSheet(self.Button_stylesheet)
            self.instru_connect_btn.setStyleSheet(self.Button_stylesheet)
            self.refresh_btn.setStyleSheet(self.Button_stylesheet)
            self.server_btn.setStyleSheet(self.Button_stylesheet)
            self.connect_btn.setStyleSheet(self.Button_stylesheet)

    def refresh_Connection_List(self):
        try:
            self.clear_layout(self.Instruments_measurement_setup_layout)
        except AttributeError:
            pass
        # rm = visa.ResourceManager('GUI/QDesign/visa_simulation.yaml@sim')
        rm = visa.ResourceManager()
        instruments = rm.list_resources()
        self.connection_ports = [instr for instr in instruments]
        self.Keithley_2182_Connected = False
        self.Ketihley_6221_Connected = False
        self.BNC845RF_Connected = False
        self.DSP7265_Connected = False
        self.instru_connect_btn.setText('Connect')
        self.connection_combo.clear()
        self.connection_combo.addItems(["None"])
        self.connection_combo.addItems(self.connection_ports)

    def check_validator(self, validator_model, entry):
        try:
            if float(entry.displayText()) <= validator_model.top() and float(
                    entry.displayText()) >= validator_model.bottom():
                return True
            else:
                QMessageBox.warning(self, "Error", "Input Out of range")
                return False
        except:
            return False

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                if child.layout() is not None:
                    self.clear_layout(child.layout())

    def start_server(self):
        if self.server_btn_clicked == False:
            try:
                # self.start_server_thread()
                self.server = mpv.Server()
                self.server.open()
                self.server_btn.setText('Stop Server')
                self.server_btn_clicked = True
                self.connect_btn.setEnabled(True)
            except SystemExit as e:
                QMessageBox.critical(self, 'No Server detected', 'No running instance of MultiVu '
                                                               'was detected. Please start MultiVu and retry without administration')
                self.server_btn.setText('Start Server')
                event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
                QApplication.sendEvent(self, event)
                event = QKeyEvent(QKeyEvent.Type.KeyRelease, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
                QApplication.sendEvent(self, event)
                self.server.close()
                self.server_btn_clicked = False
                self.connect_btn.setEnabled(False)
                return
        elif self.server_btn_clicked == True:
            self.server.close()
            event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
            QApplication.sendEvent(self, event)
            event = QKeyEvent(QKeyEvent.Type.KeyRelease, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
            QApplication.sendEvent(self, event)
            self.server_btn.setText('Start Server')
            self.server_btn_clicked = False
            self.connect_btn.setEnabled(False)

    def connect_client(self):
        self.host = self.host_entry_box.displayText()
        self.port = self.port_entry_box.displayText()
        if self.connect_btn_clicked == False:
            try:
                self.client = mpv.Client(host=self.host, port=int(self.port))
                self.client.open()
                self.connect_btn.setText('Stop Client')
                self.connect_btn_clicked = True
                self.server_btn.setEnabled(False)
                self.client_keep_going = True
                self.ppms_reading_group_box = QGroupBox('PPMS Status')
                self.ppms_Temp_group_box = QGroupBox('Temperature Setup')
                self.ppms_Field_group_box = QGroupBox('Field Setup')
                self.ppms_reading_layout = QVBoxLayout()
                self.ppms_temp_layout = QHBoxLayout()
                self.ppms_temp_label = QLabel('Temperature (K):')
                self.ppms_temp_label.setFont(self.font)
                self.ppms_reading_temp_label = QLabel('N/A K')
                self.ppms_reading_temp_label.setFont(self.font)
                self.ppms_temp_layout.addWidget(self.ppms_temp_label)
                self.ppms_temp_layout.addWidget(self.ppms_reading_temp_label)
                self.ppms_field_layout = QHBoxLayout()
                self.ppms_field_label = QLabel('Field (Oe):')
                self.ppms_field_label.setFont(self.font)
                self.ppms_reading_field_label = QLabel('N/A Oe')
                self.ppms_reading_field_label.setFont(self.font)
                self.ppms_field_layout.addWidget(self.ppms_field_label)
                self.ppms_field_layout.addWidget(self.ppms_reading_field_label)

                self.ppms_chamber_layout = QHBoxLayout()
                self.ppms_chamber_label = QLabel('Chamber Status:')
                self.ppms_chamber_label.setFont(self.font)
                self.ppms_reading_chamber_label = QLabel('N/A')
                self.ppms_reading_chamber_label.setFont(self.font)
                self.ppms_chamber_layout.addWidget(self.ppms_chamber_label)
                self.ppms_chamber_layout.addWidget(self.ppms_reading_chamber_label)

                self.ppms_reading_layout.addLayout(self.ppms_temp_layout)
                self.ppms_reading_layout.addLayout(self.ppms_field_layout)
                self.ppms_reading_layout.addLayout(self.ppms_chamber_layout)

                self.ppms_reading_group_box.setLayout(self.ppms_reading_layout)
                self.ppms_temp_setting_layout = QVBoxLayout()
                self.ppms_temp_radio_buttom_layout = QHBoxLayout()
                self.ppms_zone_temp_layout = QVBoxLayout()
                self.Temp_setup_Zone_1 = False
                self.Temp_setup_Zone_2 = False
                self.Temp_setup_Zone_3 = False
                self.Temp_setup_Zone_Cus = False
                self.ppms_temp_zone_number_label = QLabel('Number of Independent Step Regions:')
                self.ppms_temp_zone_number_label.setFont(self.font)
                self.ppms_temp_One_zone_radio = QRadioButton("1")
                self.ppms_temp_One_zone_radio.setFont(self.font)
                self.ppms_temp_One_zone_radio.toggled.connect(self.temp_zone_selection)
                self.ppms_temp_Two_zone_radio = QRadioButton("2")
                self.ppms_temp_Two_zone_radio.setFont(self.font)
                self.ppms_temp_Two_zone_radio.toggled.connect(self.temp_zone_selection)
                self.ppms_temp_Three_zone_radio = QRadioButton("3")
                self.ppms_temp_Three_zone_radio.setFont(self.font)
                self.ppms_temp_Three_zone_radio.toggled.connect(self.temp_zone_selection)
                self.ppms_temp_Customize_zone_radio = QRadioButton("Customize")
                self.ppms_temp_Customize_zone_radio.setFont(self.font)
                self.ppms_temp_Customize_zone_radio.toggled.connect(self.temp_zone_selection)
                self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_One_zone_radio)
                self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_Two_zone_radio)
                self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_Three_zone_radio)
                self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_Customize_zone_radio)
                self.ppms_temp_setting_layout.addWidget(self.ppms_temp_zone_number_label)
                self.ppms_temp_setting_layout.addLayout(self.ppms_temp_radio_buttom_layout)
                self.ppms_temp_setting_layout.addLayout(self.ppms_zone_temp_layout)
                self.ppms_Temp_group_box.setLayout(self.ppms_temp_setting_layout)

                self.ppms_field_setting_layout = QVBoxLayout()
                self.ppms_field_mode_buttom_layout = QHBoxLayout()
                self.ppms_field_radio_buttom_layout = QHBoxLayout()
                self.ppms_zone_field_layout = QVBoxLayout()

                self.Field_setup_Zone_1 = False
                self.Field_setup_Zone_2 = False
                self.Field_setup_Zone_3 = False

                self.ppms_field_mode_fast_radio = QRadioButton("Continuous Sweep")
                self.ppms_field_mode_fast_radio.setFont(self.font)
                self.ppms_field_mode_fast_radio.setChecked(True)
                self.ppms_field_mode_fixed_radio = QRadioButton("Fixed Field")
                self.ppms_field_mode_fixed_radio.setFont(self.font)
                self.ppms_field_mode_buttom_layout.addWidget(self.ppms_field_mode_fast_radio)
                self.ppms_field_mode_buttom_layout.addWidget(self.ppms_field_mode_fixed_radio)
                self.ppms_field_mode_buttom_group = QButtonGroup()
                self.ppms_field_mode_buttom_group.addButton(self.ppms_field_mode_fast_radio)
                self.ppms_field_mode_buttom_group.addButton(self.ppms_field_mode_fixed_radio)

                self.ppms_field_zone_number_label = QLabel('Number of Independent Step Regions:')
                self.ppms_field_zone_number_label.setFont(self.font)
                self.ppms_field_One_zone_radio = QRadioButton("1")
                self.ppms_field_One_zone_radio.setFont(self.font)
                self.ppms_field_One_zone_radio.toggled.connect(self.field_zone_selection)
                self.ppms_field_Two_zone_radio = QRadioButton("2")
                self.ppms_field_Two_zone_radio.setFont(self.font)
                self.ppms_field_Two_zone_radio.toggled.connect(self.field_zone_selection)
                self.ppms_field_Three_zone_radio = QRadioButton("3")
                self.ppms_field_Three_zone_radio.setFont(self.font)
                self.ppms_field_Three_zone_radio.toggled.connect(self.field_zone_selection)
                self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_One_zone_radio)
                self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_Two_zone_radio)
                self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_Three_zone_radio)
                self.ppms_field_setting_layout.addLayout(self.ppms_field_mode_buttom_layout)
                self.ppms_field_setting_layout.addWidget(self.ppms_field_zone_number_label)
                self.ppms_field_setting_layout.addLayout(self.ppms_field_radio_buttom_layout)
                self.ppms_field_setting_layout.addLayout(self.ppms_zone_field_layout)
                self.ppms_Field_group_box.setLayout(self.ppms_field_setting_layout)
                self.ppms_reading_group_box.setFixedWidth(340)
                self.ppms_Temp_group_box.setFixedWidth(350)
                self.ppms_Field_group_box.setFixedWidth(420)
                self.PPMS_measurement_setup_layout.addWidget(self.ppms_reading_group_box)
                self.PPMS_measurement_setup_layout.addWidget(self.ppms_Temp_group_box)
                self.PPMS_measurement_setup_layout.addWidget(self.ppms_Field_group_box)
            except SystemExit as e:
                QMessageBox.critical(self, 'Client connection failed!', 'Please try again')

        elif self.connect_btn_clicked == True:
            if self.client is not None:
                self.client.close_client()
            self.clear_layout(self.PPMS_measurement_setup_layout)
            self.client_keep_going = False
            self.connect_btn.setText('Start Client')
            self.connect_btn_clicked = False
            self.server_btn.setEnabled(True)

    def connect_devices(self):
        # self.rm = visa.ResourceManager('GUI/QDesign/visa_simulation.yaml@sim')
        self.rm = visa.ResourceManager()
        self.current_connection_index = self.Instruments_combo.currentIndex()
        self.current_connection = self.connection_combo.currentText()
        if self.ETO_radio_buttom.isChecked():
            try:
                if self.current_connection_index == 0:
                    return None
                elif self.current_connection_index == 1:
                    try:
                        self.connect_keithley_2182()
                    except Exception as e:
                        self.Keithley_2182_Connected = False
                        tb_str = traceback.format_exc()
                        QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                        self.instru_connect_btn.setText('Connect')
                elif self.current_connection_index == 2:
                    try:
                        self.connect_keithley_6221()
                    except Exception as e:
                        self.Ketihley_6221_Connected = False
                        tb_str = traceback.format_exc()
                        QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                        self.instru_connect_btn.setText('Connect')
                elif self.current_connection_index == 3:
                    try:
                        self.connect_dsp7265()
                    except Exception as e:
                        self.DSP7265_Connected = False
                        tb_str = traceback.format_exc()
                        QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                        self.instru_connect_btn.setText('Connect')
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")
        elif self.FMR_radio_buttom.isChecked():
            try:
                if self.current_connection_index == 0:
                    return None
                elif self.current_connection_index == 1:
                    try:
                        self.connect_keithley_2182()
                    except Exception as e:
                        self.Keithley_2182_Connected = False
                        tb_str = traceback.format_exc()
                        QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                        self.instru_connect_btn.setText('Connect')
                elif self.current_connection_index == 2:
                    try:
                        self.connect_keithley_6221()
                    except Exception as e:
                        self.Ketihley_6221_Connected = False
                        tb_str = traceback.format_exc()
                        QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                        self.instru_connect_btn.setText('Connect')
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")

    def connect_keithley_2182(self):
        if self.Keithley_2182_Connected == False:
            try:
                self.keithley_2182nv = self.rm.open_resource(self.current_connection, timeout=10000)
                time.sleep(2)
                Model_2182 = self.keithley_2182nv.query('*IDN?')
                QMessageBox.information(self, "Connected", F"Connected to {Model_2182}")
                #  Simulation pysim----------------------------------------------------------
                # self.keithley_2182nv = self.rm.open_resource(self.current_connection, timeout=10000,  read_termination='\n')
                # ------------------------------------------------------------------
                time.sleep(2)
                self.Keithley_2182_Connected = True
                self.instru_connect_btn.setText('Disconnect')
                self.keithley2182_Window()
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")
        else:
            self.instru_connect_btn.setText('Connect')
            self.close_keithley_2182()
            self.Keithley_2182_Connected = False

    def connect_keithley_6221(self):
        if self.Ketihley_6221_Connected == False:
            try:
                self.keithley_6221 = self.rm.open_resource(self.current_connection, timeout=10000)
                time.sleep(2)
                Model_6221 = self.keithley_6221.query('*IDN?')
                QMessageBox.information(self, "Connected", F"Connected to {Model_6221}")
                #  Simulation pysim ------------------------------------------------------
                # self.keithley_2182nv = self.rm.open_resource(self.current_connection, timeout=10000,
                #                                              read_termination='\n')
                # ---------------------------------------------------------
                time.sleep(2)
                self.Ketihley_6221_Connected = True
                self.instru_connect_btn.setText('Disconnect')
                self.keithley6221_Window()
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")
                self.Ketihley_6221_Connected = False
        else:
            self.instru_connect_btn.setText('Connect')
            self.close_keithley_6221()
            self.Ketihley_6221_Connected = False

    def connect_dsp7265(self):
        if self.DSP7265_Connected == False:
            try:
                self.DSP7265 = self.rm.open_resource(self.current_connection, timeout=10000)
                time.sleep(2)
                DSPModel = self.DSP7265.query('ID')
                self.DSP7265_Connected = True
                QMessageBox.information(self, "Connected", F"Connected to {DSPModel}")
                self.instru_connect_btn.setText('Disconnect')
                self.dsp7265_Window()
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")
        else:
            self.instru_connect_btn.setText('Connect')
            self.close_keithley_2182()
            self.DSP7265_Connected = False

    def close_keithley_2182(self):
        try:
            self.keithley_2182nv.close()
            self.Keithley_2182_Connected = False
            self.clear_layout(self.keithley_2182_contain_layout)
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def close_keithley_6221(self):
        try:
            self.keithley_6221.close()
            self.Ketihley_6221_Connected = False
            self.clear_layout(self.keithley_6221_contain_layout)
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def close_dsp7265(self):
        try:
            self.DSP7265.close()
            self.DSP7265_Connected = False
            self.clear_layout(self.DSP7265_contain_layout)
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def instru_combo_index_change(self):
        self.current_connection_index = self.Instruments_combo.currentIndex()
        if self.current_connection_index == 1:
            if self.Keithley_2182_Connected:
                self.instru_connect_btn.setText('Disconnect')
            else:
                self.instru_connect_btn.setText('Connect')

        elif self.current_connection_index == 2:
            if self.Ketihley_6221_Connected:
                self.instru_connect_btn.setText('Disconnect')
            else:
                self.instru_connect_btn.setText('Connect')

        elif self.current_connection_index == 3:
            if self.DSP7265_Connected:
                self.instru_connect_btn.setText('Disconnect')
            else:
                self.instru_connect_btn.setText('Connect')

    def dsp7265_Window(self):
        self.dsp726_Container = QWidget(self)
        self.dsp726_groupbox = QGroupBox('DSP 7265')

        self.dsp7265_main_layout = QVBoxLayout()

        self.dsp726_IMODE_layout = QHBoxLayout()
        self.dsp7265_IMODE_combo = QComboBox()
        self.dsp7265_IMODE_combo.setFont(self.font)
        self.dsp7265_IMODE_combo.setStyleSheet(self.QCombo_stylesheet)
        self.dsp7265_IMODE_combo.addItems(
            ["Select Input Mode", "Current mode off", "High bandwidth current mode", "Low noise current mode"])
        self.dsp7265_IMODE_combo.currentIndexChanged.connect(self.dsp726_IMODE_selection)
        self.dsp_imode_text = QLabel('IMODE:')
        self.dsp_imode_text.setFont(self.font)
        self.dsp726_IMODE_layout.addWidget(self.dsp_imode_text)
        self.dsp726_IMODE_layout.addWidget(self.dsp7265_IMODE_combo)
        self.dsp7265_main_layout.addLayout(self.dsp726_IMODE_layout)

        self.dsp7265_mode_contain_layout = QVBoxLayout()
        self.dsp7265_main_layout.addLayout(self.dsp7265_mode_contain_layout)

        self.dsp7265_reading_layout = QVBoxLayout()
        # self.dsp7265_x_reading_layout = QHBoxLayout()
        # self.dsp7265_x_reading_label = QLabel('X: ')
        # self.dsp7265_x_reading_label.setFont(self.font)
        # self.dsp7265_x_reading_value_label = QLabel('N/A')
        # self.dsp7265_x_reading_value_label.setFont(self.font)
        # self.dsp7265_x_reading_layout.addWidget(self.dsp7265_x_reading_label)
        # self.dsp7265_x_reading_layout.addWidget(self.dsp7265_x_reading_value_label)
        #
        # self.dsp7265_y_reading_layout = QHBoxLayout()
        # self.dsp7265_y_reading_label = QLabel('Y: ')
        # self.dsp7265_y_reading_value_label = QLabel('N/A')
        # self.dsp7265_y_reading_label.setFont(self.font)
        # self.dsp7265_y_reading_value_label.setFont(self.font)
        # self.dsp7265_y_reading_layout.addWidget(self.dsp7265_y_reading_label)
        # self.dsp7265_y_reading_layout.addWidget(self.dsp7265_y_reading_value_label)

        self.dsp7265_mag_reading_layout = QHBoxLayout()
        self.dsp7265_mag_reading_label = QLabel('Magnitude: ')
        self.dsp7265_mag_reading_value_label = QLabel('N/A')
        self.dsp7265_mag_reading_label.setFont(self.font)
        self.dsp7265_mag_reading_value_label.setFont(self.font)
        self.dsp7265_mag_reading_layout.addWidget(self.dsp7265_mag_reading_label)
        self.dsp7265_mag_reading_layout.addWidget(self.dsp7265_mag_reading_value_label)

        self.dsp7265_phase_reading_layout = QHBoxLayout()
        self.dsp7265_phase_reading_label = QLabel('Phase: ')
        self.dsp7265_phase_reading_value_label = QLabel('N/A')
        self.dsp7265_phase_reading_label.setFont(self.font)
        self.dsp7265_phase_reading_value_label.setFont(self.font)
        self.dsp7265_phase_reading_layout.addWidget(self.dsp7265_phase_reading_label)
        self.dsp7265_phase_reading_layout.addWidget(self.dsp7265_phase_reading_value_label)

        # self.dsp7265_reading_layout.addLayout(self.dsp7265_x_reading_layout)
        # self.dsp7265_reading_layout.addLayout(self.dsp7265_y_reading_layout)
        self.dsp7265_reading_layout.addLayout(self.dsp7265_mag_reading_layout)
        self.dsp7265_reading_layout.addLayout(self.dsp7265_phase_reading_layout)
        self.dsp7265_main_layout.addStretch(1)
        self.dsp7265_main_layout.addLayout(self.dsp7265_reading_layout)

        self.dsp726_groupbox.setLayout(self.dsp7265_main_layout)
        self.dsp726_groupbox.setFixedWidth(500)
        self.DSP7265_contain_layout = QHBoxLayout()
        self.DSP7265_contain_layout.addWidget(self.dsp726_groupbox)
        self.Instruments_measurement_setup_layout.addLayout(self.DSP7265_contain_layout)

    def keithley2182_Window(self):
        self.Keithley_2182_Container = QWidget(self)
        self.keithley_2182_groupbox = QGroupBox('Keithley 2182nv')
        self.NPLC_layout = QHBoxLayout()
        self.NPLC_Label = QLabel('NPLC:')
        self.NPLC_Label.setFont(self.font)
        self.NPLC_entry = QLineEdit()
        self.NPLC_entry.setFont(self.font)
        self.NPLC_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.NPLC_entry.setFont(self.font)
        self.NPLC_entry.setText('1.2')
        self.NPLC_layout.addWidget(self.NPLC_Label)
        self.NPLC_layout.addStretch(1)
        self.NPLC_layout.addWidget(self.NPLC_entry)
        self.NPLC_layout.addStretch(1)

        self.keithley_2182_channel_1_layout = QHBoxLayout()
        self.keithley_2182_channel_1_checkbox = QCheckBox('Channel 1:')
        self.keithley_2182_channel_1_checkbox.setFont(self.font)
        self.keithley_2182_channel_1_reading_label = QLabel('N/A')
        self.keithley_2182_channel_1_reading_label.setFont(self.font)
        self.keithley_2182_channel_1_layout.addWidget(self.keithley_2182_channel_1_checkbox)
        self.keithley_2182_channel_1_layout.addWidget(self.keithley_2182_channel_1_reading_label)

        self.keithley_2182_channel_2_layout = QHBoxLayout()
        self.keithley_2182_channel_2_checkbox = QCheckBox('Channel 2:')
        self.keithley_2182_channel_2_checkbox.setFont(self.font)
        self.keithley_2182_channel_2_reading_label = QLabel('N/A')
        self.keithley_2182_channel_2_reading_label.setFont(self.font)
        self.keithley_2182_channel_2_layout.addWidget(self.keithley_2182_channel_2_checkbox)
        self.keithley_2182_channel_2_layout.addWidget(self.keithley_2182_channel_2_reading_label)

        self.keithley_2182_main_layout = QVBoxLayout()
        self.keithley_2182_main_layout.addLayout(self.NPLC_layout)
        self.keithley_2182_main_layout.addLayout(self.keithley_2182_channel_1_layout)
        self.keithley_2182_main_layout.addLayout(self.keithley_2182_channel_2_layout)
        self.keithley_2182_groupbox.setLayout(self.keithley_2182_main_layout)
        self.keithley_2182_groupbox.setFixedWidth(500)
        self.keithley_2182_contain_layout = QHBoxLayout()
        self.keithley_2182_contain_layout.addWidget(self.keithley_2182_groupbox)
        self.Instruments_measurement_setup_layout.addLayout(self.keithley_2182_contain_layout)

    def keithley6221_Window(self):
        self.Keithley_6221_Container = QWidget(self)
        self.keithley_6221_groupbox = QGroupBox('Keithley 6221')

        self.Keithey_6221_main_layout = QVBoxLayout()
        self.keithley_6221_DC_radio = QRadioButton("DC")
        self.keithley_6221_DC_radio.setFont(self.font)
        self.keithley_6221_DC_radio.toggled.connect(self.Keithley_6221_DC)
        self.keithley_6221_AC_radio = QRadioButton("AC")
        self.keithley_6221_AC_radio.setFont(self.font)
        self.keithley_6221_AC_radio.toggled.connect(self.Keithley_6221_AC)
        self.keithley_6221_radio_button_layout = QHBoxLayout()
        self.keithley_6221_radio_button_layout.addWidget(self.keithley_6221_DC_radio)
        self.keithley_6221_radio_button_layout.addWidget(self.keithley_6221_AC_radio)
        self.Keithey_6221_main_layout.addLayout(self.keithley_6221_radio_button_layout)

        self.Keithey_curSour_layout = QVBoxLayout()
        self.Keithey_6221_main_layout.addLayout(self.Keithey_curSour_layout)
        self.keithley_6221_groupbox.setLayout(self.Keithey_6221_main_layout)
        self.keithley_6221_groupbox.setFixedWidth(620)
        self.keithley_6221_contain_layout = QHBoxLayout()
        self.keithley_6221_contain_layout.addWidget(self.keithley_6221_groupbox)
        self.Instruments_measurement_setup_layout.addLayout(self.keithley_6221_contain_layout)

    def Keithley_6221_DC(self):
        try:
            self.clear_layout(self.Keithey_curSour_layout)
        except Exception as e:
            pass
        self.keithley_6221_DC_range_single_layout = QVBoxLayout()
        self.keithley_6221_DC_range_layout = QHBoxLayout()
        self.keithley_6221_DC_range_checkbox = QRadioButton('Range')
        # self.keithley_6221_DC_range_checkbox.stateChanged.connect(self.on_6221_DC_toggle)
        self.keithley_6221_DC_range_checkbox.setFont(self.font)
        self.keithley_6221_DC_range_from_label = QLabel('From:')
        self.keithley_6221_DC_range_from_label.setFont(self.font)
        self.keithley_6221_DC_range_init_entry = QLineEdit()
        self.keithley_6221_DC_range_init_entry.setFont(self.font)
        self.keithley_6221_DC_range_to_label = QLabel('to')
        self.keithley_6221_DC_range_to_label.setFont(self.font)
        self.keithley_6221_DC_range_final_entry = QLineEdit()
        self.keithley_6221_DC_range_final_entry.setFont(self.font)
        self.keithley_6221_DC_range_step_label = QLabel('Step Size:')
        self.keithley_6221_DC_range_step_label.setFont(self.font)
        self.keithley_6221_DC_range_step_entry = QLineEdit()
        self.keithley_6221_DC_range_step_entry.setFont(self.font)
        self.keithley_6221_DC_range_combobox = QComboBox()
        self.keithley_6221_DC_range_combobox.setFont(self.font)
        self.keithley_6221_DC_range_combobox.setStyleSheet(self.QCombo_stylesheet)
        self.keithley_6221_DC_range_combobox.addItems(["Select Units", "mA", "µA", "nA", "pA"])
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_checkbox)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_from_label)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_init_entry)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_to_label)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_final_entry)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_step_label)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_step_entry)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_combobox)
        self.keithley_6221_DC_range_single_layout.addLayout(self.keithley_6221_DC_range_layout)
        self.keithley_6221_DC_single_layout = QHBoxLayout()
        self.keithley_6221_DC_single_checkbox = QRadioButton('List')
        # self.keithley_6221_DC_single_checkbox.stateChanged.connect(self.on_6221_DC_toggle)
        self.keithley_6221_DC_single_checkbox.setFont(self.font)

        self.keithley_6221_DC_single_entry = QLineEdit()
        self.keithley_6221_DC_single_entry.setFont(self.font)
        self.keithley_6221_DC_single_combobox = QComboBox()
        self.keithley_6221_DC_single_combobox.setFont(self.font)
        self.keithley_6221_DC_single_combobox.setStyleSheet(self.QCombo_stylesheet)
        self.keithley_6221_DC_single_combobox.addItems(["Select Units", "mA", "µA", "nA", "pA"])
        self.keithley_6221_DC_single_layout.addWidget(self.keithley_6221_DC_single_checkbox)
        self.keithley_6221_DC_single_layout.addWidget(self.keithley_6221_DC_single_entry)
        self.keithley_6221_DC_single_layout.addWidget(self.keithley_6221_DC_single_combobox)
        self.keithley_6221_DC_range_single_layout.addLayout(self.keithley_6221_DC_single_layout)
        self.Keithey_curSour_layout.addLayout(self.keithley_6221_DC_range_single_layout)

        self.keithley_6221_DC_selection_btn_group = QButtonGroup()
        self.keithley_6221_DC_selection_btn_group.addButton(self.keithley_6221_DC_range_checkbox)
        self.keithley_6221_DC_selection_btn_group.addButton(self.keithley_6221_DC_single_checkbox)

    def Keithley_6221_AC(self):
        self.keithley_6221_AC_layout = QHBoxLayout()
        self.keithley_6221_DC = QCheckBox('Channel 2:')
        try:
            self.clear_layout(self.Keithey_curSour_layout)
        except Exception as e:
            pass


    def dsp726_IMODE_selection(self):
        try:
            self.clear_layout(self.dsp7265_mode_contain_layout)
        except Exception as e:
            pass

        self.dsp_IMODE_index = self.dsp7265_IMODE_combo.currentIndex()
        if self.dsp_IMODE_index == 1:
            self.DSP7265.write('IMODE 0')

            self.dsp726_VMODE_layout = QHBoxLayout()
            self.dsp7265_VMODE_combo = QComboBox()
            self.dsp7265_VMODE_combo.setFont(self.font)
            self.dsp7265_VMODE_combo.setStyleSheet(self.QCombo_stylesheet)
            self.dsp7265_VMODE_combo.addItems(
                ["Select Input Mode", "Both grounded", "A", "-B", "A-B"])
            self.dsp7265_VMODE_combo.currentIndexChanged.connect(self.dsp726_VMODE_selection)
            self.dsp_VMODE_text = QLabel('VMODE:')
            self.dsp_VMODE_text.setFont(self.font)
            self.dsp726_IMODE_layout.addWidget(self.dsp_VMODE_text)
            self.dsp726_IMODE_layout.addWidget(self.dsp7265_VMODE_combo)
            self.dsp7265_mode_contain_layout.addLayout(self.dsp726_IMODE_layout)

            # Sensitivity
            self.dsp726_sens_layout = QHBoxLayout()
            self.dsp7265_sens_combo = QComboBox()
            self.dsp7265_sens_combo.setFont(self.font)
            self.dsp7265_sens_combo.setStyleSheet(self.QCombo_stylesheet)
            self.dsp7265_sens_combo.addItems(
                ["Select Sensitivity", "2 nV", "5 nV", "10 nV", "20 nV", "50 nV", "100 nV", "200 nV", "500 nV",
                 "1 \u00B5V", "2 \u00B5V", "5 \u00B5V", "10 \u00B5V", "20 \u00B5V", "50 \u00B5V", "100 \u00B5V",
                 "200 \u00B5V", "500 \u00B5V", "1 mV", "2 mV", "5 mV", "10 mV", "20 mV", "50 mV", "100 mV", "200 mV",
                 "500 mV",
                 "1 V", "Auto"])
            self.dsp7265_sens_combo.currentIndexChanged.connect(self.dsp726_sens_selection)
            self.dsp_sens_text = QLabel('Sensitivity:')
            self.dsp_sens_text.setFont(self.font)
            self.dsp726_sens_layout.addWidget(self.dsp_sens_text)
            self.dsp726_sens_layout.addWidget(self.dsp7265_sens_combo)
            self.dsp7265_mode_contain_layout.addLayout(self.dsp726_sens_layout)
            # TC
            self.dsp726_TC_layout = QHBoxLayout()
            self.dsp7265_TC_combo = QComboBox()
            self.dsp7265_TC_combo.setFont(self.font)
            self.dsp7265_TC_combo.setStyleSheet(self.QCombo_stylesheet)
            self.dsp7265_TC_combo.addItems(
                ["Select Input Mode", "10 \u00B5s", "20 \u00B5s", "40 \u00B5s", "80 \u00B5s", "160 \u00B5s"
                    , "320 \u00B5s", "640 \u00B5s", "5 ms", "10 ms", "20 ms", "50 ms", "100 ms", "200 ms", "500 ms"
                    , "1 s", "2 s", "5 s", "10 s", "20 s", "50 s", "100 s", "200 s", "500 s", "1 ks", "2 ks", '5 ks',
                 "10 ks", "20 ks", "50 ks", "100 ks"])
            self.dsp7265_TC_combo.currentIndexChanged.connect(self.dsp726_TC_selection)
            self.dsp_tc_text = QLabel('Time constant:')
            self.dsp_tc_text.setFont(self.font)
            self.dsp726_TC_layout.addWidget(self.dsp_tc_text)
            self.dsp726_TC_layout.addWidget(self.dsp7265_TC_combo)
            self.dsp7265_mode_contain_layout.addLayout(self.dsp726_TC_layout)

            self.dsp7265_auto_button_layout = QHBoxLayout()
            self.dsp7265_auto_sense = QPushButton('Auto Sens.')
            self.dsp7265_auto_sense.setStyleSheet(self.Button_stylesheet)
            self.dsp7265_auto_sense.clicked.connect(self.dsp725_auto_sens)

            self.dsp7265_auto_phase = QPushButton('Auto Phase')
            self.dsp7265_auto_phase.setStyleSheet(self.Button_stylesheet)
            self.dsp7265_auto_phase.clicked.connect(self.dsp725_auto_phase)

            self.dsp7265_auto_Measurement = QPushButton('Auto Meas.')
            self.dsp7265_auto_Measurement.setStyleSheet(self.Button_stylesheet)
            self.dsp7265_auto_Measurement.clicked.connect(self.dsp725_auto_meas)

            self.dsp7265_auto_button_layout.addWidget(self.dsp7265_auto_sense)
            self.dsp7265_auto_button_layout.addWidget(self.dsp7265_auto_phase)
            self.dsp7265_auto_button_layout.addWidget(self.dsp7265_auto_Measurement)
            self.dsp7265_button_container = QWidget()
            self.dsp7265_button_container.setLayout(self.dsp7265_auto_button_layout)
            self.dsp7265_button_container.setFixedHeight(50)
            self.dsp7265_mode_contain_layout.addWidget(self.dsp7265_button_container)




        elif self.dsp_IMODE_index == 2:
            self.DSP7265.write('IMODE 1')

            self.dsp726_VMODE_layout = QHBoxLayout()
            self.dsp7265_VMODE_combo = QComboBox()
            self.dsp7265_VMODE_combo.setFont(self.font)
            self.dsp7265_VMODE_combo.setStyleSheet(self.QCombo_stylesheet)
            self.dsp7265_VMODE_combo.addItems(
                ["Select Input Mode", "Both grounded", "A", "-B", "A-B"])
            self.dsp7265_VMODE_combo.currentIndexChanged.connect(self.dsp726_VMODE_selection)
            self.dsp_VMODE_text = QLabel('VMODE:')
            self.dsp_VMODE_text.setFont(self.font)
            self.dsp726_IMODE_layout.addWidget(self.dsp_VMODE_text)
            self.dsp726_IMODE_layout.addWidget(self.dsp7265_VMODE_combo)
            self.dsp7265_mode_contain_layout.addLayout(self.dsp726_IMODE_layout)

            # Sensitivity
            self.dsp726_sens_layout = QHBoxLayout()
            self.dsp7265_sens_combo = QComboBox()
            self.dsp7265_sens_combo.setFont(self.font)
            self.dsp7265_sens_combo.setStyleSheet(self.QCombo_stylesheet)
            self.dsp7265_sens_combo.addItems(
                ["Select Sensitivity", "2 fA", "5 fA", "10 fA", "20 fA", "50 fA", "100 fA", "200 fA", "500 fA",
                 "1 pA", "2 pA", "5 pA", "10 pA", "20 pA", "50 pA", "100 pA",
                 "200 pA", "500 pA", "1 nA", "2 nA", "5 nA", "10 nA", "20 nA", "50 nA", "100 nA", "200 nA",
                 "500 nA",
                 "1 \u00B5A", "Auto"])
            self.dsp7265_sens_combo.currentIndexChanged.connect(self.dsp726_sens_selection)
            self.dsp_sens_text = QLabel('Sensitivity:')
            self.dsp_sens_text.setFont(self.font)
            self.dsp726_sens_layout.addWidget(self.dsp_sens_text)
            self.dsp726_sens_layout.addWidget(self.dsp7265_sens_combo)
            self.dsp7265_mode_contain_layout.addLayout(self.dsp726_sens_layout)
            # TC
            self.dsp726_TC_layout = QHBoxLayout()
            self.dsp7265_TC_combo = QComboBox()
            self.dsp7265_TC_combo.setFont(self.font)
            self.dsp7265_TC_combo.setStyleSheet(self.QCombo_stylesheet)
            self.dsp7265_TC_combo.addItems(
                ["Select Input Mode", "10 \u00B5s", "20 \u00B5s""A", "40 \u00B5s", "80 \u00B5s", "160 \u00B5s"
                    , "320 \u00B5s", "640 \u00B5s", "5 ms", "10 ms", "20 ms", "50 ms", "100 ms", "200 ms", "500 ms"
                    , "1 s", "2 s", "5 s", "10 s", "20 s", "50 s", "100 s", "200 s", "500 s", "1 ks", "2 ks", '5 ks',
                 "10 ks", "20 ks", "50 ks", "100 ks"])
            self.dsp7265_TC_combo.currentIndexChanged.connect(self.dsp726_TC_selection)
            self.dsp_tc_text = QLabel('Time constant:')
            self.dsp_tc_text.setFont(self.font)
            self.dsp726_TC_layout.addWidget(self.dsp_tc_text)
            self.dsp726_TC_layout.addWidget(self.dsp7265_TC_combo)
            self.dsp7265_mode_contain_layout.addLayout(self.dsp726_TC_layout)

        elif self.dsp_IMODE_index == 3:
            self.DSP7265.write('IMODE 2')

    def dsp726_VMODE_selection(self):
        self.dsp_VMODE_index = self.dsp7265_VMODE_combo.currentIndex()
        if self.dsp_VMODE_index == 1:
            self.DSP7265.write('VMODE 0')
        elif self.dsp_VMODE_index == 2:
            self.DSP7265.write('VMODE 1')
        elif self.dsp_VMODE_index == 3:
            self.DSP7265.write('VMODE 2')
        elif self.dsp_VMODE_index == 4:
            self.DSP7265.write('VMODE 3')

    def dsp726_sens_selection(self):
        self.dsp_sens_index = self.dsp7265_sens_combo.currentIndex()
        if self.dsp_sens_index != 0:
            self.DSP7265.write(f'SEN {str(self.dsp_sens_index)}')
        elif self.dsp_sens_index > 27:
            self.DSP7265.write('AS')

    def dsp726_TC_selection(self):
        self.dsp_tc_index = self.dsp7265_TC_combo.currentIndex()
        if self.dsp_tc_index != 0:
            self.DSP7265.write(f'TC {str(self.dsp_tc_index-1)}')

    def dsp725_auto_sens(self):
        self.DSP7265.write('AS')
        
    def dsp725_auto_phase(self):
        self.DSP7265.write('AQN')

    def dsp725_auto_meas(self):
        self.DSP7265.write('ASM')

    def field_zone_selection(self):
        if self.ppms_field_One_zone_radio.isChecked() and self.Field_setup_Zone_1 == False:
            self.ppms_field_One_zone_radio.setChecked(False)
            self.Field_setup_Zone_1 = True
            self.Field_setup_Zone_2 = False
            self.Field_setup_Zone_3 = False
            self.field_one_zone()
            self.ppms_field_One_zone_radio.setChecked(False)
        elif self.ppms_field_Two_zone_radio.isChecked() and self.Field_setup_Zone_2 == False:
            self.ppms_field_Two_zone_radio.setChecked(False)
            self.Field_setup_Zone_1 = False
            self.Field_setup_Zone_2 = True
            self.Field_setup_Zone_3 = False
            self.field_two_zone()
            self.ppms_field_Two_zone_radio.setChecked(False)
        elif self.ppms_field_Three_zone_radio.isChecked() and self.Field_setup_Zone_3 == False:
            self.ppms_field_Three_zone_radio.setChecked(False)
            self.Field_setup_Zone_1 = False
            self.Field_setup_Zone_2 = False
            self.Field_setup_Zone_3 = True
            self.field_three_zone()
            self.ppms_field_Three_zone_radio.setChecked(False)

    def field_one_zone(self):
        self.ppms_zone1_field_layout = QVBoxLayout()
        self.ppms_zone1_field_range_layout = QHBoxLayout()
        self.ppms_zone1_from_label = QLabel('Range (Oe): Top')
        self.ppms_zone1_from_label.setFont(self.font)
        self.ppms_zone1_from_entry = QLineEdit()
        self.ppms_zone1_from_entry.setFont(self.font)
        self.ppms_zone1_from_entry.setPlaceholderText("3000 Oe")
        self.ppms_zone1_to_label = QLabel(' Bottom ')
        self.ppms_zone1_to_label.setFont(self.font)
        self.ppms_zone1_to_entry = QLineEdit()
        self.ppms_zone1_to_entry.setFont(self.font)
        self.ppms_zone1_to_entry.setPlaceholderText("-3000 Oe")
        self.ppms_zone1_field_range_layout.addWidget(self.ppms_zone1_from_label)
        self.ppms_zone1_field_range_layout.addWidget(self.ppms_zone1_from_entry)
        self.ppms_zone1_field_range_layout.addWidget(self.ppms_zone1_to_label)
        self.ppms_zone1_field_range_layout.addWidget(self.ppms_zone1_to_entry)

        self.ppms_zone1_field_step_layout = QHBoxLayout()
        self.ppms_zone1_field_step_label = QLabel('Step Size (Oe): ')
        self.ppms_zone1_field_step_label.setFont(self.font)
        self.ppms_zone1_field_step_entry = QLineEdit()
        self.ppms_zone1_field_step_entry.setFont(self.font)
        self.ppms_zone1_field_rate_label = QLabel('Rate (Oe/sec): ')
        self.ppms_zone1_field_rate_label.setFont(self.font)
        self.ppms_zone1_field_rate_entry = QLineEdit()
        self.ppms_zone1_field_rate_entry.setFont(self.font)
        self.ppms_zone1_field_rate_entry.setText('220')
        self.ppms_zone1_field_step_layout.addWidget(self.ppms_zone1_field_step_label)
        self.ppms_zone1_field_step_layout.addWidget(self.ppms_zone1_field_step_entry)
        self.ppms_zone1_field_step_layout.addWidget(self.ppms_zone1_field_rate_label)
        self.ppms_zone1_field_step_layout.addWidget(self.ppms_zone1_field_rate_entry)

        self.ppms_zone1_field_layout.addLayout(self.ppms_zone1_field_range_layout)
        self.ppms_zone1_field_layout.addLayout(self.ppms_zone1_field_step_layout)
        self.clear_layout(self.ppms_zone_field_layout)
        self.ppms_zone_field_layout.addLayout(self.ppms_zone1_field_layout)

    def field_two_zone(self):
        self.field_one_zone()
        self.ppms_zone1_from_entry.setPlaceholderText("3000 Oe")
        self.ppms_zone1_to_entry.setPlaceholderText("2000 Oe")
        self.ppms_zone2_field_layout = QVBoxLayout()
        self.ppms_zone2_field_range_layout = QHBoxLayout()
        self.ppms_zone2_from_label = QLabel('Range 2 (Oe): Top')
        self.ppms_zone2_from_label.setFont(self.font)
        self.ppms_zone2_from_entry = QLineEdit()
        self.ppms_zone2_from_entry.setFont(self.font)
        self.ppms_zone2_to_label = QLabel(' Bottom ')
        self.ppms_zone2_to_label.setFont(self.font)
        self.ppms_zone2_to_entry = QLineEdit()
        self.ppms_zone2_to_entry.setFont(self.font)
        self.ppms_zone2_from_entry.setPlaceholderText("2000 Oe")
        self.ppms_zone2_to_entry.setText("0")
        self.ppms_zone2_to_entry.setEnabled(False)
        self.ppms_zone2_field_range_layout.addWidget(self.ppms_zone2_from_label)
        self.ppms_zone2_field_range_layout.addWidget(self.ppms_zone2_from_entry)
        self.ppms_zone2_field_range_layout.addWidget(self.ppms_zone2_to_label)
        self.ppms_zone2_field_range_layout.addWidget(self.ppms_zone2_to_entry)

        self.ppms_zone2_field_step_layout = QHBoxLayout()
        self.ppms_zone2_field_step_label = QLabel('Step Size 2 (Oe): ')
        self.ppms_zone2_field_step_label.setFont(self.font)
        self.ppms_zone2_field_step_entry = QLineEdit()
        self.ppms_zone2_field_step_entry.setFont(self.font)

        self.ppms_zone2_field_rate_label = QLabel('Rate (Oe/sec): ')
        self.ppms_zone2_field_rate_label.setFont(self.font)
        self.ppms_zone2_field_rate_entry = QLineEdit()
        self.ppms_zone2_field_rate_entry.setFont(self.font)
        self.ppms_zone2_field_rate_entry.setText('220')
        self.ppms_zone2_field_step_layout.addWidget(self.ppms_zone2_field_step_label)
        self.ppms_zone2_field_step_layout.addWidget(self.ppms_zone2_field_step_entry)
        self.ppms_zone2_field_step_layout.addWidget(self.ppms_zone2_field_rate_label)
        self.ppms_zone2_field_step_layout.addWidget(self.ppms_zone2_field_rate_entry)

        self.ppms_zone2_field_layout.addLayout(self.ppms_zone2_field_range_layout)
        self.ppms_zone2_field_layout.addLayout(self.ppms_zone2_field_step_layout)
        self.ppms_zone_field_layout.addLayout(self.ppms_zone2_field_layout)

    def field_three_zone(self):
        self.field_two_zone()
        self.ppms_zone1_from_entry.setPlaceholderText("3000 Oe")
        self.ppms_zone1_to_entry.setPlaceholderText("2000 Oe")
        self.ppms_zone2_from_entry.setPlaceholderText("2000 Oe")
        self.ppms_zone2_to_entry.setPlaceholderText("1000 Oe")
        self.ppms_zone2_to_entry.clear()
        self.ppms_zone2_to_entry.setEnabled(True)
        self.ppms_zone3_field_layout = QVBoxLayout()
        self.ppms_zone3_field_range_layout = QHBoxLayout()
        self.ppms_zone3_from_label = QLabel('Range 3 (Oe): Top')
        self.ppms_zone3_from_label.setFont(self.font)
        self.ppms_zone3_from_entry = QLineEdit()
        self.ppms_zone3_from_entry.setFont(self.font)
        self.ppms_zone3_to_label = QLabel(' Bottom ')
        self.ppms_zone3_to_label.setFont(self.font)
        self.ppms_zone3_to_entry = QLineEdit()
        self.ppms_zone3_to_entry.setFont(self.font)
        self.ppms_zone3_from_entry.setPlaceholderText("1000 Oe")
        self.ppms_zone3_to_entry.setText("0")
        self.ppms_zone3_to_entry.setEnabled(False)
        self.ppms_zone3_field_range_layout.addWidget(self.ppms_zone3_from_label)
        self.ppms_zone3_field_range_layout.addWidget(self.ppms_zone3_from_entry)
        self.ppms_zone3_field_range_layout.addWidget(self.ppms_zone3_to_label)
        self.ppms_zone3_field_range_layout.addWidget(self.ppms_zone3_to_entry)

        self.ppms_zone3_field_step_layout = QHBoxLayout()
        self.ppms_zone3_field_step_label = QLabel('Step Size 3 (Oe): ')
        self.ppms_zone3_field_step_label.setFont(self.font)
        self.ppms_zone3_field_step_entry = QLineEdit()
        self.ppms_zone3_field_step_entry.setFont(self.font)

        self.ppms_zone3_field_rate_label = QLabel('Rate (Oe/sec): ')
        self.ppms_zone3_field_rate_label.setFont(self.font)
        self.ppms_zone3_field_rate_entry = QLineEdit()
        self.ppms_zone3_field_rate_entry.setFont(self.font)
        self.ppms_zone3_field_rate_entry.setText('220')

        self.ppms_zone3_field_step_layout.addWidget(self.ppms_zone3_field_step_label)
        self.ppms_zone3_field_step_layout.addWidget(self.ppms_zone3_field_step_entry)
        self.ppms_zone3_field_step_layout.addWidget(self.ppms_zone3_field_rate_label)
        self.ppms_zone3_field_step_layout.addWidget(self.ppms_zone3_field_rate_entry)

        self.ppms_zone3_field_layout.addLayout(self.ppms_zone3_field_range_layout)
        self.ppms_zone3_field_layout.addLayout(self.ppms_zone3_field_step_layout)
        self.ppms_zone_field_layout.addLayout(self.ppms_zone3_field_layout)

    def temp_zone_selection(self):
        if self.ppms_temp_One_zone_radio.isChecked() and self.Temp_setup_Zone_1 == False:
            self.ppms_temp_One_zone_radio.setChecked(False)
            self.Temp_setup_Zone_1 = True
            self.Temp_setup_Zone_2 = False
            self.Temp_setup_Zone_3 = False
            self.Temp_setup_Zone_Cus = False
            self.temp_one_zone()
            self.ppms_temp_One_zone_radio.setChecked(False)
        elif self.ppms_temp_Two_zone_radio.isChecked() and self.Temp_setup_Zone_2 == False:
            self.ppms_temp_Two_zone_radio.setChecked(False)
            self.Temp_setup_Zone_1 = False
            self.Temp_setup_Zone_2 = True
            self.Temp_setup_Zone_3 = False
            self.Temp_setup_Zone_Cus = False
            self.temp_two_zone()
            self.ppms_temp_Two_zone_radio.setChecked(False)
        elif self.ppms_temp_Three_zone_radio.isChecked() and self.Temp_setup_Zone_3 == False:
            self.ppms_temp_Three_zone_radio.setChecked(False)
            self.Temp_setup_Zone_1 = False
            self.Temp_setup_Zone_2 = False
            self.Temp_setup_Zone_3 = True
            self.Temp_setup_Zone_Cus = False
            self.temp_three_zone()
            self.ppms_temp_Three_zone_radio.setChecked(False)
        elif self.ppms_temp_Customize_zone_radio.isChecked() and self.Temp_setup_Zone_Cus == False:
            self.ppms_temp_Customize_zone_radio.setChecked(False)
            self.Temp_setup_Zone_1 = False
            self.Temp_setup_Zone_2 = False
            self.Temp_setup_Zone_3 = False
            self.Temp_setup_Zone_Cus = True
            self.temp_customize_zone()
            self.ppms_temp_Customize_zone_radio.setChecked(False)

    def temp_one_zone(self):
        self.ppms_zone1_temp_layout = QVBoxLayout()
        self.ppms_zone1_temp_range_layout = QHBoxLayout()
        self.ppms_zone1_temp_from_label = QLabel('Range (K): From')
        self.ppms_zone1_temp_from_label.setFont(self.font)
        self.ppms_zone1_temp_from_entry = QLineEdit()
        self.ppms_zone1_temp_from_entry.setFont(self.font)
        self.ppms_zone1_temp_to_label = QLabel(' to ')
        self.ppms_zone1_temp_to_label.setFont(self.font)
        self.ppms_zone1_temp_to_entry = QLineEdit()
        self.ppms_zone1_temp_to_entry.setFont(self.font)
        self.ppms_zone1_temp_range_layout.addWidget(self.ppms_zone1_temp_from_label)
        self.ppms_zone1_temp_range_layout.addWidget(self.ppms_zone1_temp_from_entry)
        self.ppms_zone1_temp_range_layout.addWidget(self.ppms_zone1_temp_to_label)
        self.ppms_zone1_temp_range_layout.addWidget(self.ppms_zone1_temp_to_entry)

        self.ppms_zone1_temp_step_layout = QHBoxLayout()
        self.ppms_zone1_temp_step_label = QLabel('Step Size (K): ')
        self.ppms_zone1_temp_step_label.setFont(self.font)
        self.ppms_zone1_temp_step_entry = QLineEdit()
        self.ppms_zone1_temp_step_entry.setFont(self.font)

        self.ppms_zone1_temp_rate_label = QLabel('Rate (K/min): ')
        self.ppms_zone1_temp_rate_label.setFont(self.font)
        self.ppms_zone1_temp_rate_entry = QLineEdit()
        self.ppms_zone1_temp_rate_entry.setFont(self.font)
        self.ppms_zone1_temp_rate_entry.setText('5')

        self.ppms_zone1_temp_step_layout.addWidget(self.ppms_zone1_temp_step_label)
        self.ppms_zone1_temp_step_layout.addWidget(self.ppms_zone1_temp_step_entry)
        self.ppms_zone1_temp_step_layout.addWidget(self.ppms_zone1_temp_rate_label)
        self.ppms_zone1_temp_step_layout.addWidget(self.ppms_zone1_temp_rate_entry)

        self.ppms_zone1_temp_layout.addLayout(self.ppms_zone1_temp_range_layout)
        self.ppms_zone1_temp_layout.addLayout(self.ppms_zone1_temp_step_layout)
        self.clear_layout(self.ppms_zone_temp_layout)
        self.ppms_zone_temp_layout.addLayout(self.ppms_zone1_temp_layout)

    def temp_two_zone(self):
        self.temp_one_zone()
        self.ppms_zone2_temp_layout = QVBoxLayout()
        self.ppms_zone2_temp_range_layout = QHBoxLayout()
        self.ppms_zone2_temp_from_label = QLabel('Range 2 (K): From')
        self.ppms_zone2_temp_from_label.setFont(self.font)
        self.ppms_zone2_temp_from_entry = QLineEdit()
        self.ppms_zone2_temp_from_entry.setFont(self.font)
        self.ppms_zone2_temp_to_label = QLabel(' to ')
        self.ppms_zone2_temp_to_label.setFont(self.font)
        self.ppms_zone2_temp_to_entry = QLineEdit()
        self.ppms_zone2_temp_to_entry.setFont(self.font)
        self.ppms_zone2_temp_range_layout.addWidget(self.ppms_zone2_temp_from_label)
        self.ppms_zone2_temp_range_layout.addWidget(self.ppms_zone2_temp_from_entry)
        self.ppms_zone2_temp_range_layout.addWidget(self.ppms_zone2_temp_to_label)
        self.ppms_zone2_temp_range_layout.addWidget(self.ppms_zone2_temp_to_entry)

        self.ppms_zone2_temp_step_layout = QHBoxLayout()
        self.ppms_zone2_temp_step_label = QLabel('Step Size 2 (K): ')
        self.ppms_zone2_temp_step_label.setFont(self.font)
        self.ppms_zone2_temp_step_entry = QLineEdit()
        self.ppms_zone2_temp_step_entry.setFont(self.font)

        # self.ppms_zone2_temp_rate_label = QLabel('Temp Rate (K/min): ')
        # self.ppms_zone2_temp_rate_label.setFont(self.font)
        # self.ppms_zone2_temp_rate_entry = QLineEdit()
        # self.ppms_zone2_temp_rate_entry.setFont(self.font)
        # self.ppms_zone2_temp_rate_entry.setText('50')

        self.ppms_zone2_temp_step_layout.addWidget(self.ppms_zone2_temp_step_label)
        self.ppms_zone2_temp_step_layout.addWidget(self.ppms_zone2_temp_step_entry)
        # self.ppms_zone2_temp_step_layout.addWidget(self.ppms_zone2_temp_rate_label)
        # self.ppms_zone2_temp_step_layout.addWidget(self.ppms_zone2_temp_rate_entry)

        self.ppms_zone2_temp_layout.addLayout(self.ppms_zone2_temp_range_layout)
        self.ppms_zone2_temp_layout.addLayout(self.ppms_zone2_temp_step_layout)
        self.ppms_zone_temp_layout.addLayout(self.ppms_zone2_temp_layout)

    def temp_three_zone(self):
        self.temp_two_zone()
        self.ppms_zone3_temp_layout = QVBoxLayout()
        self.ppms_zone3_temp_range_layout = QHBoxLayout()
        self.ppms_zone3_temp_from_label = QLabel('Range 3 (K): From')
        self.ppms_zone3_temp_from_label.setFont(self.font)
        self.ppms_zone3_temp_from_entry = QLineEdit()
        self.ppms_zone3_temp_from_entry.setFont(self.font)
        self.ppms_zone3_temp_to_label = QLabel(' to ')
        self.ppms_zone3_temp_to_label.setFont(self.font)
        self.ppms_zone3_temp_to_entry = QLineEdit()
        self.ppms_zone3_temp_to_entry.setFont(self.font)
        self.ppms_zone3_temp_range_layout.addWidget(self.ppms_zone3_temp_from_label)
        self.ppms_zone3_temp_range_layout.addWidget(self.ppms_zone3_temp_from_entry)
        self.ppms_zone3_temp_range_layout.addWidget(self.ppms_zone3_temp_to_label)
        self.ppms_zone3_temp_range_layout.addWidget(self.ppms_zone3_temp_to_entry)

        self.ppms_zone3_temp_step_layout = QHBoxLayout()
        self.ppms_zone3_temp_step_label = QLabel('Step Size 3 (K): ')
        self.ppms_zone3_temp_step_label.setFont(self.font)
        self.ppms_zone3_temp_step_entry = QLineEdit()
        self.ppms_zone3_temp_step_entry.setFont(self.font)

        # self.ppms_zone3_temp_rate_label = QLabel('Temp Rate (K/min): ')
        # self.ppms_zone3_temp_rate_label.setFont(self.font)
        # self.ppms_zone3_temp_rate_entry = QLineEdit()
        # self.ppms_zone3_temp_rate_entry.setFont(self.font)
        # self.ppms_zone3_temp_rate_entry.setText('50')

        self.ppms_zone3_temp_step_layout.addWidget(self.ppms_zone3_temp_step_label)
        self.ppms_zone3_temp_step_layout.addWidget(self.ppms_zone3_temp_step_entry)
        # self.ppms_zone3_temp_step_layout.addWidget(self.ppms_zone3_temp_rate_label)
        # self.ppms_zone3_temp_step_layout.addWidget(self.ppms_zone3_temp_rate_entry)

        self.ppms_zone3_temp_layout.addLayout(self.ppms_zone3_temp_range_layout)
        self.ppms_zone3_temp_layout.addLayout(self.ppms_zone3_temp_step_layout)
        self.ppms_zone_temp_layout.addLayout(self.ppms_zone3_temp_layout)

    def temp_customize_zone(self):
        self.ppms_zone_cus_temp_layout = QVBoxLayout()
        self.ppms_zone_cus_temp_list_layout = QHBoxLayout()
        self.ppms_zone_cus_temp_list_from_label = QLabel('Temperature List (K): [')
        self.ppms_zone_cus_temp_list_from_label.setFont(self.font)
        self.ppms_zone_cus_temp_list_entry = QLineEdit()
        self.ppms_zone_cus_temp_list_entry.setFont(self.font)
        self.ppms_zone_cus_temp_end_label = QLabel(']')
        self.ppms_zone_cus_temp_end_label.setFont(self.font)
        self.ppms_zone_cus_temp_list_layout.addWidget(self.ppms_zone_cus_temp_list_from_label)
        self.ppms_zone_cus_temp_list_layout.addWidget(self.ppms_zone_cus_temp_list_entry)
        self.ppms_zone_cus_temp_list_layout.addWidget(self.ppms_zone_cus_temp_end_label)

        self.ppms_zone_cus_temp_rate_layout = QHBoxLayout()
        self.ppms_zone_cus_temp_rate_label = QLabel('Rate (K/min): ')
        self.ppms_zone_cus_temp_rate_label.setFont(self.font)
        self.ppms_zone_cus_temp_rate_entry = QLineEdit()
        self.ppms_zone_cus_temp_rate_entry.setFont(self.font)
        self.ppms_zone_cus_temp_rate_entry.setText('5')

        self.ppms_zone_cus_temp_rate_layout.addWidget(self.ppms_zone_cus_temp_rate_label)
        self.ppms_zone_cus_temp_rate_layout.addWidget(self.ppms_zone_cus_temp_rate_entry)

        self.ppms_zone_cus_temp_layout.addLayout(self.ppms_zone_cus_temp_list_layout)
        self.ppms_zone_cus_temp_layout.addLayout(self.ppms_zone_cus_temp_rate_layout)
        self.clear_layout(self.ppms_zone_temp_layout)
        self.ppms_zone_temp_layout.addLayout(self.ppms_zone_cus_temp_layout)

    def on_6221_DC_toggle(self):
        if self.keithley_6221_DC_range_checkbox.isChecked():
            self.keithley_6221_DC_single_checkbox.setEnabled(False)
            self.keithley_6221_DC_single_entry.setEnabled(False)
            self.keithley_6221_DC_single_combobox.setEnabled(False)
        else:
            self.keithley_6221_DC_single_checkbox.setEnabled(True)
            self.keithley_6221_DC_single_entry.setEnabled(True)
            self.keithley_6221_DC_single_combobox.setEnabled(True)

        if self.keithley_6221_DC_single_checkbox.isChecked():
            self.keithley_6221_DC_range_checkbox.setEnabled(False)
            self.keithley_6221_DC_range_init_entry.setEnabled(False)
            self.keithley_6221_DC_range_final_entry.setEnabled(False)
            self.keithley_6221_DC_range_step_entry.setEnabled(False)
            self.keithley_6221_DC_range_combobox.setEnabled(False)
        else:
            self.keithley_6221_DC_range_checkbox.setEnabled(True)
            self.keithley_6221_DC_range_init_entry.setEnabled(True)
            self.keithley_6221_DC_range_final_entry.setEnabled(True)
            self.keithley_6221_DC_range_step_entry.setEnabled(True)
            self.keithley_6221_DC_range_combobox.setEnabled(True)

    def rst(self):
        try:
            self.worker = None
        except Exception:
            pass
        self.timer = QTimer()
        self.timer.stop()
        self.canvas.axes.cla()
        self.canvas.axes_2.cla()
        self.canvas.draw()
        self.ppms_field_One_zone_radio_enabled = False
        self.ppms_field_Two_zone_radio_enabled = False
        self.ppms_field_Three_zone_radio_enabled = False
        self.nv_channel_1_enabled = None
        self.nv_channel_2_enabled = None
        try:
            self.keithley_6221.write(":OUTP OFF")
            self.keithley_2182nv.write("*RST")
            self.keithley_2182nv.write("*CLS")
            # self.keithley_6221.close()
            # self.keithley_2182nv.close()
            # self.DSP7265.close()
        except Exception:
            pass


    def stop_measurement(self):
        try:
            self.keithley_6221.write(":OUTP OFF")
            self.keithley_2182nv.write("*RST")
            self.keithley_2182nv.write("*CLS")
        except Exception:
            pass

        self.running = False
        self.ppms_field_One_zone_radio_enabled = False
        self.ppms_field_Two_zone_radio_enabled = False
        self.ppms_field_Three_zone_radio_enabled = False
        self.nv_channel_1_enabled = None
        self.nv_channel_2_enabled = None
        try:
            if self.worker is not None:
                self.worker.stop()
                self.worker = None
                self.send_telegram_notification("Experiment Stop!")
        except Exception:
            QMessageBox.warning(self, 'Fail', "Fail to stop the experiment")
        # try:
        #     self.canvas.axes.cla()
        #     self.canvas.axes_2.cla()
        #     self.canvas.draw()
        # except Exception:
        #     pass

    def start_measurement(self):
        dialog = LogWindow()
        if dialog.exec():
            try:
                if self.worker is not None:
                    self.stop_measurement()
                try:
                    self.main_layout.removeWidget(self.log_box)
                    self.log_box.deleteLater()
                    self.main_layout.removeWidget(self.progress_bar)
                    self.progress_bar.deleteLater()
                except Exception:
                    pass
                self.running = True
                self.folder_path, self.file_name, self.formatted_date, self.ID, self.Measurement, self.run, self.commemt, self.User = dialog.get_text()

                self.log_box = QTextEdit(self)
                self.log_box.setReadOnly(True)  # Make the log box read-only
                self.progress_bar = QProgressBar(self)
                self.progress_bar.setMinimum(0)
                self.progress_bar.setMaximum(100)
                self.progress_bar.setFixedWidth(1140)
                self.progress_value = 0
                self.progress_bar.setValue(self.progress_value)
                self.progress_bar.setStyleSheet("""
                            QProgressBar {
                                border: 1px solid #8f8f91;
                                border-radius: 5px;
                                background-color: #e0e0e0;
                                text-align: center;
                            }

                            QProgressBar::chunk {
                                background-color:  #3498db;
                                width: 5px;
                            }
                        """)
                self.log_box.setFixedSize(1140, 150)
                self.main_layout.addWidget(self.progress_bar)
                self.main_layout.addWidget(self.log_box, alignment=Qt.AlignmentFlag.AlignCenter)
                self.log_box.clear()

                # self.send_email('Measurement Started', "start", 'czt0036@auburn.edu')
                if self.Ketihley_6221_Connected:
                    self.append_text('Check Connection of Keithley 6221....\n', 'yellow')
                    try:
                        model_6221 = self.keithley_6221.query('*IDN?')
                        self.append_text(str(model_6221), 'green')
                    except visa.errors.VisaIOError as e:
                        QMessageBox.warning(self, 'Fail to connect Keithley 6221', str(e))
                        self.stop_measurement()
                        return
                    self.append_text('Keithley 6221 connected!\n', 'green')
                if self.Keithley_2182_Connected:
                    self.append_text('Check Connection of Keithley 2182....\n', 'yellow')
                    try:
                        model_2182 = self.keithley_2182nv.query('*IDN?')
                        self.keithley_2182nv.write(':SYST:BEEP:STAT 0')
                        self.log_box.append(str(model_2182))
                        # Initialize and configure the instrument
                        self.keithley_2182nv.write("*RST")
                        self.keithley_2182nv.write("*CLS")
                        time.sleep(2)  # Wait for the reset to complete
                    except visa.errors.VisaIOError as e:
                        QMessageBox.warning(self, 'Fail to connect Keithley 2182', str(e))
                        self.stop_measurement()
                        return
                    self.append_text('Keithley 2182 connected!\n', 'green')
                if self.DSP7265_Connected:
                    self.append_text('Check Connection of DSP Lock-in 7265....\n', 'yellow')
                    try:
                        model_7265 = self.DSP7265.query('ID')
                        self.log_box.append(str(model_7265))
                        time.sleep(2)  # Wait for the reset to complete
                    except visa.errors.VisaIOError as e:
                        QMessageBox.warning(self, 'Fail to connectDSP Lock-in 7265', str(e))
                        self.stop_measurement()
                        return
                    self.append_text('DSP Lock-in 7265 connected!\n', 'green')
                def float_range(start, stop, step):
                    current = start
                    while current < stop:
                        yield current
                        current += step

                try:
                    self.append_text('Start initializing parameters...!\n', 'orange')
                    self.append_text('Start initializing Temperatures...!\n', 'blue')
                    TempList = []
                    if self.ppms_temp_One_zone_radio.isChecked():
                        zone_1_start = float(self.ppms_zone1_temp_from_entry.text())
                        zone_1_end = float(self.ppms_zone1_temp_to_entry.text()) + float(
                            self.ppms_zone1_temp_step_entry.text())
                        zone_1_step = float(self.ppms_zone1_temp_step_entry.text())
                        print(zone_1_start, zone_1_end, zone_1_step)
                        TempList = [round(float(i), 2) for i in float_range(zone_1_start, zone_1_end, zone_1_step)]
                        print(TempList)
                        tempRate = round(float(self.ppms_zone1_temp_rate_entry.text()), 2)
                    elif self.ppms_temp_Two_zone_radio.isChecked():
                        zone_1_start = float(self.ppms_zone1_temp_from_entry.text())
                        zone_1_end = float(self.ppms_zone1_temp_to_entry.text())
                        zone_1_step = float(self.ppms_zone1_temp_step_entry.text())
                        zone_2_start = float(self.ppms_zone2_temp_from_entry.text())
                        zone_2_end = float(self.ppms_zone2_temp_to_entry.text())
                        zone_2_step = float(self.ppms_zone2_temp_step_entry.text())
                        if zone_1_end == zone_2_start:
                            zone_1_end = zone_1_end
                        else:
                            zone_1_end = zone_1_end + zone_1_step
                        TempList = [round(float(i), 2) for i in float_range(zone_1_start, zone_1_end, zone_1_step)]
                        TempList += [round(float(i), 2) for i in
                                     float_range(zone_2_start, zone_2_end + zone_2_step, zone_2_step)]
                        tempRate = round(float(self.ppms_zone1_temp_rate_entry.text()), 2)
                    elif self.ppms_temp_Three_zone_radio.isChecked():
                        zone_1_start = float(self.ppms_zone1_temp_from_entry.text())
                        zone_1_end = float(self.ppms_zone1_temp_to_entry.text())
                        zone_1_step = float(self.ppms_zone1_temp_step_entry.text())

                        zone_2_start = float(self.ppms_zone2_temp_from_entry.text())
                        zone_2_end = float(self.ppms_zone2_temp_to_entry.text())
                        zone_2_step = float(self.ppms_zone2_temp_step_entry.text())

                        zone_3_start = float(self.ppms_zone3_temp_from_entry.text())
                        zone_3_end = float(self.ppms_zone3_temp_to_entry.text()) + float(
                            self.ppms_zone3_temp_step_entry.text())
                        zone_3_step = float(self.ppms_zone3_temp_step_entry.text())

                        if zone_1_end == zone_2_start:
                            zone_1_end = zone_1_end
                        else:
                            zone_1_end = zone_1_end + zone_1_step

                        if zone_2_end == zone_3_start:
                            zone_2_end = zone_2_end
                        else:
                            zone_2_end = zone_2_end + zone_2_step

                        TempList = [round(float(i), 2) for i in float_range(zone_1_start, zone_1_end, zone_1_step)]
                        TempList += [round(float(i), 2) for i in float_range(zone_2_start, zone_2_end, zone_2_step)]
                        TempList += [round(float(i), 2) for i in float_range(zone_3_start, zone_3_end, zone_3_step)]
                        tempRate = round(float(self.ppms_zone1_temp_rate_entry.text()), 2)
                    elif self.ppms_temp_Customize_zone_radio.isChecked():
                        templist = self.ppms_zone_cus_temp_list_entry.text()
                        templist = templist.replace(" ", "")
                        TempList = [round(float(item), 2) for item in templist.split(',')]
                        tempRate = round(float(self.ppms_zone_cus_temp_rate_entry.text()), 2)
                except Exception as e:
                    self.stop_measurement()
                    tb_str = traceback.format_exc()
                    QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

                self.append_text('Start initializing Field...!\n', 'blue')
                if self.ppms_field_One_zone_radio.isChecked():
                    self.zone1_top_field = float(self.ppms_zone1_from_entry.text())
                    self.zone1_bot_field = float(self.ppms_zone1_to_entry.text())
                    self.zone1_step_field = float(self.ppms_zone1_field_step_entry.text())
                    self.zone1_field_rate = float(self.ppms_zone1_field_rate_entry.text())
                    number_of_field_zone1 = 2 * (self.zone1_top_field - self.zone1_bot_field) / self.zone1_step_field
                    number_of_field = np.abs(number_of_field_zone1)
                elif self.ppms_field_Two_zone_radio.isChecked():
                    self.zone1_top_field = float(self.ppms_zone1_from_entry.text())
                    self.zone1_bot_field = float(self.ppms_zone1_to_entry.text())
                    self.zone1_step_field = float(self.ppms_zone1_field_step_entry.text())
                    self.zone1_field_rate = float(self.ppms_zone1_field_rate_entry.text())
                    self.zone2_top_field = float(self.ppms_zone2_from_entry.text())
                    self.zone2_bot_field = float(self.ppms_zone2_to_entry.text())
                    self.zone2_step_field = float(self.ppms_zone2_field_step_entry.text())
                    self.zone2_field_rate = float(self.ppms_zone2_field_rate_entry.text())
                    # Need to think about it
                    number_of_field_zone1 = 2 * (self.zone1_top_field - self.zone1_bot_field) / self.zone1_step_field
                    number_of_field_zone2 = 2 * (self.zone2_top_field - self.zone2_bot_field) / self.zone2_step_field
                    number_of_field = np.abs(number_of_field_zone1) + np.abs(number_of_field_zone2)
                elif self.ppms_field_Three_zone_radio.isChecked():
                    self.zone1_top_field = float(self.ppms_zone1_from_entry.text())
                    self.zone1_bot_field = float(self.ppms_zone1_to_entry.text())
                    self.zone1_step_field = float(self.ppms_zone1_field_step_entry.text())
                    self.zone1_field_rate = float(self.ppms_zone1_field_rate_entry.text())
                    self.zone2_top_field = float(self.ppms_zone2_from_entry.text())
                    self.zone2_bot_field = float(self.ppms_zone2_to_entry.text())
                    self.zone2_step_field = float(self.ppms_zone2_field_step_entry.text())
                    self.zone2_field_rate = float(self.ppms_zone1_field_rate_entry.text())
                    self.zone3_top_field = float(self.ppms_zone3_from_entry.text())
                    self.zone3_bot_field = float(self.ppms_zone3_to_entry.text())
                    self.zone3_step_field = float(self.ppms_zone3_field_step_entry.text())
                    self.zone3_field_rate = float(self.ppms_zone3_field_rate_entry.text())
                    # Need to think about it
                    number_of_field_zone1 = 2 * (self.zone1_top_field - self.zone1_bot_field) / self.zone1_step_field
                    number_of_field_zone2 = 2 * (self.zone2_top_field - self.zone2_bot_field) / self.zone2_step_field
                    number_of_field_zone3 = 2 * (self.zone3_top_field - self.zone3_bot_field) / self.zone3_step_field
                    number_of_field = np.abs(number_of_field_zone1) + np.abs(number_of_field_zone2) + np.abs(
                        number_of_field_zone3)

                topField = self.zone1_top_field
                botField = -1 * self.zone1_top_field

                self.append_text('Start initializing Current...!\n', 'blue')
                # =============================== Set the current ==================================== #
                if self.keithley_6221_DC_radio.isChecked():
                    if self.keithley_6221_DC_range_checkbox.isChecked():
                        init_current = float(self.keithley_6221_DC_range_init_entry.text())
                        final_current = float(self.keithley_6221_DC_range_final_entry.text())
                        step_current = float(self.keithley_6221_DC_range_step_entry.text())
                        self.DC_Range_unit = self.keithley_6221_DC_range_combobox.currentIndex()
                        if self.DC_Range_unit != 0:
                            if self.DC_Range_unit == 1:  # mA
                                DC_range_selected_unit = 'e-3'
                                self.current_unit = 'mA'
                            elif self.DC_Range_unit == 2:  # uA
                                DC_range_selected_unit = 'e-6'
                                self.current_unit = 'uA'
                            elif self.DC_Range_unit == 3:  # nA
                                DC_range_selected_unit = 'e-9'
                                self.current_unit = 'nA'
                            elif self.DC_Range_unit == 4:  # pA
                                DC_range_selected_unit = 'e-12'
                                self.current_unit = 'pA'
                        else:
                            QMessageBox.warning(self, "Missing Items",
                                                "Please select all the required parameter - missing current unit")
                            self.stop_measurement()
                            return
                        current = [f"{i}{DC_range_selected_unit}" for i in
                                   float_range(init_current, final_current + step_current, step_current)]
                        current_mag = [f"{i}" for i in
                                       float_range(init_current, final_current + step_current, step_current)]
                    elif self.keithley_6221_DC_single_checkbox.isChecked():
                        self.single_DC_current = self.keithley_6221_DC_single_entry.text()
                        self.single_DC_current = self.single_DC_current.replace(" ", "")
                        self.single_DC_current = [float(item) for item in self.single_DC_current.split(',')]
                        self.DC_Single_unit = self.keithley_6221_DC_single_combobox.currentIndex()
                        if self.DC_Single_unit != 0:
                            if self.DC_Single_unit == 1:  # mA
                                DC_single_selected_unit = 'e-3'
                                self.current_unit = 'mA'
                            elif self.DC_Single_unit == 2:  # uA
                                DC_single_selected_unit = 'e-6'
                                self.current_unit = 'uA'
                            elif self.DC_Single_unit == 3:  # nA
                                DC_single_selected_unit = 'e-9'
                                self.current_unit = 'nA'
                            elif self.DC_Single_unit == 4:  # pA
                                DC_single_selected_unit = 'e-12'
                                self.current_unit = 'pA'
                        else:
                            QMessageBox.warning(self, "Missing Items",
                                                "Please select all the required parameter - missing current unit")
                            self.stop_measurement()
                            return
                        current = [f"{self.single_DC_current[i]}{DC_single_selected_unit}" for i in
                                   range(len(self.single_DC_current))]
                        current_mag = [f"{self.single_DC_current[i]}" for i in range(len(self.single_DC_current))]
                    else:
                        QMessageBox.warning(self, 'Warning', 'Please choose one of the options')
                        self.stop_measurement()
                        return
                elif self.keithley_6221_AC_radio.isChecked():
                    QMessageBox.warning(self, "New Feature is coming", 'Abort')
                    self.stop_measurement()
                    return
                if self.Keithley_2182_Connected:
                    self.nv_NPLC = self.NPLC_entry.text()

                if self.ppms_field_One_zone_radio.isChecked():
                    self.ppms_field_One_zone_radio_enabled = True
                    self.ppms_field_Two_zone_radio_enabled = False
                    self.ppms_field_Three_zone_radio_enabled = False
                    self.zone2_step_field = self.zone1_step_field
                    self.zone3_step_field = self.zone1_step_field
                    self.zone2_field_rate = self.zone1_field_rate
                    self.zone3_field_rate = self.zone1_field_rate
                    self.zone2_top_field = self.zone1_top_field
                    self.zone3_top_field = self.zone1_top_field
                elif self.ppms_field_Two_zone_radio.isChecked():
                    self.ppms_field_Two_zone_radio_enabled = True
                    self.ppms_field_One_zone_radio_enabled = False
                    self.ppms_field_Three_zone_radio_enabled = False
                    self.zone3_step_field = self.zone2_step_field
                    self.zone3_field_rate = self.zone2_field_rate
                    self.zone3_top_field = self.zone2_top_field
                elif self.ppms_field_Three_zone_radio.isChecked():
                    self.ppms_field_Three_zone_radio_enabled = True
                    self.ppms_field_Two_zone_radio_enabled = False
                    self.ppms_field_One_zone_radio_enabled = False
                # Function to convert
                def listToString(s):
                    # initialize an empty string
                    str1 = ""
                    # return string
                    return (str1.join(s))

                temp_log = str(TempList)
                self.append_text('Create Log...!\n', 'green')
                self.folder_path = self.folder_path + f'Run_{self.run}/'
                os.makedirs(self.folder_path, exist_ok=True)
                self.random_number = random.randint(100000, 999999)
                f = open(self.folder_path + f'{self.random_number}_Experiment_Log.txt', "a")
                today = datetime.today()
                self.formatted_date_csv = today.strftime("%m-%Y-%d %H:%M:%S")
                f.write(f"User: {self.User}\n")
                f.write(f"Today's Date: {self.formatted_date_csv}\n")
                f.write(f"Sample ID: {self.ID}\n")
                f.write(f"Measurement Type: {self.Measurement}\n")
                f.write(f"Run: {self.run}\n")
                f.write(f"Comment: {self.commemt}\n")
                f.write(f"Experiment Field (Oe): {topField} to {botField}\n")
                f.write(f"Experiment Temperature (K): {temp_log}\n")
                f.write(f"Experiment Current: {listToString(current)}\n")
                if self.Keithley_2182_Connected:
                    f.write(f"Instrument: Keithley 2182\n")
                if self.Ketihley_6221_Connected:
                    f.write(f"Instrument: Keithley 6221\n")
                if self.BNC845RF_Connected:
                    f.write(f"Instrument: BNC845RF\n")
                if self.DSP7265_Connected:
                    f.write(f"Instrument: DSP 7265 Lock-in\n")
                f.close()
                self.send_telegram_notification(f"{self.User} is running {self.Measurement} on {self.ID}")
                if self.ppms_field_mode_fixed_radio.isChecked():
                    self.field_mode_fixed = True
                else:
                    self.field_mode_fixed = False
                if self.Keithley_2182_Connected:
                    if self.keithley_2182_channel_1_checkbox.isChecked():
                        self.nv_channel_1_enabled = True
                    else:
                        self.nv_channel_1_enabled = False

                    if self.keithley_2182_channel_2_checkbox.isChecked():
                        self.nv_channel_2_enabled = True
                    else:
                        self.nv_channel_2_enabled = False
                self.canvas.axes.cla()
                self.canvas.axes_2.cla()
                self.canvas.draw()
                self.worker = Worker(self, self.keithley_6221, self.keithley_2182nv, self.DSP7265, current, TempList, topField,
                                     botField, self.folder_path, self.client, tempRate, current_mag, self.current_unit,
                                     self.file_name, self.run, number_of_field, self.field_mode_fixed,
                                     self.nv_channel_1_enabled, self.nv_channel_2_enabled, self.nv_NPLC,
                                     self.ppms_field_One_zone_radio_enabled, self.ppms_field_Two_zone_radio_enabled,
                                     self.ppms_field_Three_zone_radio_enabled, self.zone1_step_field,
                                     self.zone2_step_field, self.zone3_step_field, self.zone1_top_field,
                                     self.zone2_top_field, self.zone3_top_field, self.zone1_field_rate,
                                     self.zone2_field_rate,self.zone3_field_rate, self.Keithley_2182_Connected,
                                     self.Ketihley_6221_Connected,self.BNC845RF_Connected,self.DSP7265_Connected)  # Create a worker instance
                self.worker.progress_update.connect(self.update_progress)
                self.worker.append_text.connect(self.append_text)
                self.worker.stop_measurment.connect(self.stop_measurement)
                self.worker.update_ppms_temp_reading_label.connect(self.update_ppms_temp_reading_label)
                self.worker.update_ppms_field_reading_label.connect(self.update_ppms_field_reading_label)
                self.worker.update_ppms_chamber_reading_label.connect(self.update_ppms_chamber_reading_label)
                self.worker.update_nv_channel_1_label.connect(self.update_nv_channel_1_label)
                self.worker.update_nv_channel_2_label.connect(self.update_nv_channel_2_label)
                self.worker.update_lockin_label.connect(self.update_lockin_label)
                self.worker.update_plot.connect(self.update_plot)
                self.worker.save_plot.connect(self.save_plot)
                self.worker.clear_plot.connect(self.clear_plot)
                self.worker.measurement_finished.connect(self.measurement_finished)
                self.worker.error_message.connect(self.error_popup)
                self.worker.start()  # Start the worker thread
                # self.worker.wait()
                # self.stop_measurement()
            except SystemExit as e:
                QMessageBox.critical(self, 'Possible Client Error', 'Check the client')
                self.stop_measurement()
                self.send_telegram_notification("Your measurement went wrong, possible PPMS client lost connection")
                self.client_keep_going = False
                self.connect_btn.setText('Start Client')
                self.connect_btn_clicked = False
                self.server_btn.setEnabled(True)

            except Exception as e:
                tb_str = traceback.format_exc()
                self.stop_measurement()
                QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                self.send_telegram_notification(f"Error-{tb_str} {str(e)}")

    def save_plot(self, x_data, y_data, color, channel_1_enabled, channel_2_enabled, save, temp, current):

        if channel_1_enabled:
            self.canvas.axes.plot(x_data, y_data, color, marker='s')
            self.canvas.axes.set_ylabel('Voltage (v)', color=color)

        if channel_2_enabled:
            self.canvas.axes_2.plot(x_data, y_data, color, marker='s')
            self.canvas.axes_2.set_ylabel('Voltage (v)', color=color)

        self.canvas.axes.set_xlabel('Field (Oe)')
        self.canvas.axes.legend([f'{temp}K {current}A'])
        self.canvas.figure.tight_layout()
        self.canvas.draw()

        if save:
            self.canvas.figure.savefig(self.folder_path +"{}_{}_run{}_{}K_{}A.png".format(self.ID, self.Measurement, self.run, temp, current))
            time.sleep(5)
            

            def send_image(bot_token, chat_id, image_path, caption=None):
                url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
                data = {"chat_id": chat_id}
                if caption:
                    data["caption"] = caption

                try:
                    with open(image_path, "rb") as image_file:
                        files = {"photo": image_file}
                        response = requests.post(url, data=data, files=files)

                    if response.status_code != 200:
                        raise Exception(f"Error: {response.status_code}, {response.text}")

                    return response.json()

                except FileNotFoundError:
                    return {"ok": False, "error": "File not found. Check the file path."}
                except Exception as e:
                    return {"ok": False, "error": str(e)}
            
            bot_token = self.token_file
            chat_id = "5733353343"
            image_path = r"{}{}_{}_run{}_{}K_{}A.png".format(self.folder_path, self.ID, self.Measurement, self.run, temp, current)
            print(image_path)
            if not os.path.exists(image_path):
                print("No Such File.")
            caption = f"Data preview"
            response = send_image(bot_token, chat_id, image_path, caption)
            print(response)

    def update_plot(self, x_data, y_data, color, channel_1_enabled, channel_2_enabled):

        if channel_1_enabled:
            self.canvas.axes.plot(x_data, y_data, color, marker='s')
            self.canvas.axes.set_ylabel('Voltage (v)', color=color)

        if channel_2_enabled:
            self.canvas.axes_2.plot(x_data, y_data, color, marker='s')
            self.canvas.axes_2.set_ylabel('Voltage (v)', color=color)

        self.canvas.axes.set_xlabel('Field (Oe)')
        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def error_popup(self, e, tb_str):
        self.stop_measurement()
        QMessageBox.warning(self, str(e), f'{tb_str}')

    def clear_plot(self):
        self.canvas.axes.cla()
        self.canvas.axes_2.cla()

    def update_nv_channel_1_label(self, chanel1):
        self.keithley_2182_channel_1_reading_label.setText(chanel1)

    def update_nv_channel_2_label(self, chanel2):
        self.keithley_2182_channel_2_reading_label.setText(chanel2)

    def update_progress(self, value):
        self.progress_bar.setValue(int(value))

    def show_error_message(self, tb_str, error_str):
        QMessageBox.warning(self, "Error", f'{tb_str} {str(error_str)}')

    def measurement_finished(self):
        self.stop_btn.click()
        QMessageBox.information(self, "Measurement Finished", "The measurement has completed successfully!")

    def append_text(self, text, color):
        try:
            self.log_box.append(f'<span style="color:{color}">{str(text)}</span>')
            self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

        except Exception as e:
            QMessageBox.warning(self, "Error", f'{str(e)}')

    def update_ppms_temp_reading_label(self,  temp, tempUnits):
        self.ppms_reading_temp_label.setText(f'{str(temp)} {str(tempUnits)}')

    def update_ppms_chamber_reading_label(self,  cT):
        self.ppms_reading_chamber_label.setText(f'{str(cT)}')

    def update_ppms_field_reading_label(self,  field, fieldUnits):
        self.ppms_reading_field_label.setText(f'{str(field)} {str(fieldUnits)}')

    def update_lockin_label(self, mag, phase):
        self.dsp7265_mag_reading_value_label.setText(f'{str(mag)} volts')
        self.dsp7265_phase_reading_value_label.setText(f'{str(phase)} degs')

    def run_ETO(self, append_text, progress_update, stop_measurement, update_ppms_temp_reading_label,
                update_ppms_field_reading_label, update_ppms_chamber_reading_label,
                update_nv_channel_1_label, update_nv_channel_2_label, update_lockin_label, clear_plot, update_plot,
                save_plot,
                measurement_finished, error_message,
                keithley_6221, keithley_2182nv, DSP7265, current, TempList,
                topField, botField, folder_path, client, tempRate, current_mag, current_unit,
                file_name, run, number_of_field, field_mode_fixed, nv_channel_1_enabled,
                nv_channel_2_enabled, nv_NPLC, ppms_field_One_zone_radio_enabled,
                ppms_field_Two_zone_radio_enabled, ppms_field_Three_zone_radio_enabled,zone1_step_field,
                zone2_step_field, zone3_step_field, zone1_top_field, zone2_top_field, zone3_top_field, zone1_field_rate,
                zone2_field_rate, zone3_field_rate, Keithley_2182_Connected,
                Ketihley_6221_Connected, BNC845RF_Connected, DSP7265_Connected, running):
        try:
            def send_telegram_notification(message):
                bot_token = self.token_file
                chat_id = "5733353343"
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                data = {"chat_id": chat_id, "text": message}
                response = requests.post(url, data=data)
                return response.json()

            def deltaH_chk(currentField):
                if ppms_field_One_zone_radio_enabled:
                    deltaH = zone1_step_field
                    user_field_rate = zone1_field_rate
                elif ppms_field_Two_zone_radio_enabled:
                    if (currentField <= zone1_top_field + 1 or currentField >= -1 * zone1_top_field-1):
                        deltaH = zone1_step_field
                        user_field_rate = zone1_field_rate
                    elif (currentField > -1 * zone2_top_field and currentField <= zone2_top_field):
                        deltaH = zone2_step_field
                        user_field_rate = zone2_field_rate
                elif ppms_field_Three_zone_radio_enabled:
                    if (currentField <= zone1_top_field+1 or currentField >= -1 * zone1_top_field-1):
                        deltaH = zone1_step_field
                        user_field_rate = zone1_field_rate
                    elif (currentField < zone2_top_field and currentField >= -1 * zone2_top_field):
                        deltaH = zone2_step_field
                        user_field_rate = zone2_field_rate
                    elif (currentField > -1 * zone3_top_field and currentField < zone3_top_field):
                        deltaH = zone3_step_field
                        user_field_rate = zone3_field_rate

                return deltaH, user_field_rate

            send_telegram_notification("The measurement has been started successfully.")
            number_of_current = len(current)
            number_of_temp = len(TempList)
            Fast_fieldRate = 220
            tempRate_init = 20
            zeroField = 0
            start_time = time.time()
            append_text('Measurement Start....\n', 'red')
            user_field_rate = zone1_field_rate
            time.sleep(5)
            try:
                # -------------Temp Status---------------------
                temperature, status = client.get_temperature()
                tempUnits = client.temperature.units
                append_text(f'Temperature = {temperature} {tempUnits}\n', 'purple')
                update_ppms_temp_reading_label(str(temperature), 'K')
                # ------------Field Status----------------------
                field, status = client.get_field()
                fieldUnits = client.field.units
                append_text(f'Field = {field} {fieldUnits}\n', 'purple')
                update_ppms_field_reading_label(str(field), 'Oe')
            except SystemExit as e:
                error_message(e,e)
                send_telegram_notification("Your measurement went wrong, possible PPMS client lost connection")
            # ----------------- Loop Down ----------------------#
            Curlen = len(current)
            templen = len(TempList)
            totoal_progress = Curlen*templen

            cT = client.get_chamber()
            update_ppms_chamber_reading_label(str(cT))
            if not running():
                stop_measurement()
                return
            for i in range(templen):
                append_text(f'Loop is at {str(TempList[i])} K Temperature\n', 'blue')
                Tempsetpoint = TempList[i]
                if i == 0:
                    client.set_temperature(Tempsetpoint,
                                           tempRate_init,
                                           client.temperature.approach_mode.fast_settle)  # fast_settle/no_overshoot
                else:
                    client.set_temperature(Tempsetpoint,
                                           tempRate,
                                           client.temperature.approach_mode.fast_settle)  # fast_settle/no_overshoot
                append_text(f'Waiting for {Tempsetpoint} K Temperature\n', 'red')
                time.sleep(4)

                MyTemp, sT = client.get_temperature()
                update_ppms_temp_reading_label(str(MyTemp), 'K')
                while True:
                    if not running():
                        stop_measurement()
                        return
                    time.sleep(1.5)
                    MyTemp, sT = client.get_temperature()
                    update_ppms_temp_reading_label(str(MyTemp), 'K')
                    append_text(f'Temperature Status: {sT}\n', 'blue')
                    if sT == 'Stable':
                        break
                if i == 0:
                    append_text(f'Stabilizing the Temperature....', 'orange')
                    time.sleep(60)

                else:
                    append_text(f'Stabilizing the Temperature.....', 'orange')
                    time.sleep(300)

                for j in range(Curlen):
                    send_telegram_notification(f"Starting measurement at temperature {str(TempList[i])} K, {current_mag[j]} {current_unit}")
                    clear_plot()

                    # number_of_current = number_of_current - 1
                    client.set_field(topField,
                                     Fast_fieldRate,
                                     client.field.approach_mode.linear,  # linear/oscillate
                                     client.field.driven_mode.driven)
                    append_text(f'Waiting for {topField} Oe Field... \n', 'blue')
                    time.sleep(10)
                    while True:
                        if not running():
                            stop_measurement()
                            return
                        time.sleep(15)
                        try:
                            F, sF = client.get_field()
                        except SystemExit as e:
                            error_message(e, e)
                            send_telegram_notification(
                                "Your measurement went wrong, possible PPMS client lost connection")
                        update_ppms_field_reading_label(str(F), 'Oe')
                        append_text(f'Status: {sF}\n', 'red')
                        if sF == 'Holding (driven)':
                            break
                    client.set_field(zeroField,
                                     Fast_fieldRate,
                                     client.field.approach_mode.oscillate,  # linear/oscillate
                                     client.field.driven_mode.driven)
                    append_text(f'Waiting for {zeroField} Oe Field for Demagnetization... \n', 'blue')
                    time.sleep(10)
                    while True:
                        if not running():
                            stop_measurement()
                            return
                        time.sleep(15)
                        try:
                            F, sF = client.get_field()
                        except SystemExit as e:
                            error_message(e, e)
                            send_telegram_notification(
                                "Your measurement went wrong, possible PPMS client lost connection")
                        update_ppms_field_reading_label(str(F), 'Oe')
                        append_text(f'Status: {sF}\n', 'red')
                        if sF == 'Holding (driven)':
                            break
                    if Ketihley_6221_Connected:
                        keithley_6221.write(":OUTP OFF")  # Set source function to current
                        keithley_6221.write("CURRent:RANGe:AUTO ON \n")
                        keithley_6221.write(f'CURR {current[j]} \n')
                        keithley_6221.write(":OUTP ON")  # Turn on the output
                        append_text(f'DC current is set to: {str(current_mag[j])} {str(current_unit)}', 'blue')

                    csv_filename = f"{folder_path}{file_name}_{TempList[i]}_K_{current_mag[j]}_{current_unit}_Run_{run}.csv"
                    self.pts = 0
                    currentField = topField
                    deltaH, user_field_rate = deltaH_chk(currentField)
                    number_of_field_update = number_of_field
                    self.field_array = []
                    self.channel1_array = []
                    self.channel2_array = []
                    self.lockin_x = []
                    self.lockin_y = []
                    self.lockin_mag = []
                    self.lockin_pahse = []


                    if field_mode_fixed:
                        while currentField >= botField:
                            if not running():
                                stop_measurement()
                                return
                            single_measurement_start = time.time()
                            append_text(f'Loop is at {currentField} Oe Field Up \n', 'blue')
                            Fieldsetpoint = currentField
                            append_text(f'Set the field to {Fieldsetpoint} Oe and then collect data \n', 'blue')
                            client.set_field(Fieldsetpoint,
                                             user_field_rate,
                                             client.field.approach_mode.linear,
                                             client.field.driven_mode.driven)
                            append_text(f'Waiting for {Fieldsetpoint} Oe Field \n', 'red')
                            time.sleep(4)
                            MyField, sF = client.get_field()
                            update_ppms_field_reading_label(str(MyField), 'Oe')
                            while True:
                                time.sleep(1)
                                try:
                                    MyField, sF = client.get_field()
                                except SystemExit as e:
                                    error_message(e, e)
                                    send_telegram_notification(
                                        "Your measurement went wrong, possible PPMS client lost connection")
                                update_ppms_field_reading_label(str(MyField), 'Oe')
                                append_text(f'Status: {sF}\n', 'blue')
                                if sF == 'Holding (driven)':
                                    break


                            # ----------------------------- Measure NV voltage -------------------
                            append_text(f'Saving data for {MyField} Oe \n', 'green')
                            if Keithley_2182_Connected:
                                keithley_2182nv.write("SENS:FUNC 'VOLT:DC'")
                                keithley_2182nv.write(f"VOLT:DC:NPLC {nv_NPLC}")
                            time.sleep(2)  # Wait for the configuration to complete
                            Chan_1_voltage = 0
                            Chan_2_voltage = 0
                            MyField, sF = client.get_field()
                            update_ppms_field_reading_label(str(MyField), 'Oe')
                            self.field_array.append(MyField)
                            if Keithley_2182_Connected:
                                try:
                                    if nv_channel_1_enabled:
                                        keithley_2182nv.write("SENS:CHAN 1")
                                        volt = keithley_2182nv.query("READ?")
                                        Chan_1_voltage = float(volt)
                                        update_nv_channel_1_label(str(Chan_1_voltage))
                                        append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')

                                        self.channel1_array.append(Chan_1_voltage)
                                        # # Drop off the first y element, append a new one.
                                        update_plot(self.field_array, self.channel1_array, 'black', True, False)
                                except Exception as e:
                                    QMessageBox.warning(self, 'Warning', str(e))

                                if nv_channel_2_enabled:
                                    keithley_2182nv.write("SENS:CHAN 2")
                                    volt2 = keithley_2182nv.query("READ?")
                                    Chan_2_voltage = float(volt2)
                                    update_nv_channel_2_label(str(Chan_2_voltage))
                                    append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                                    self.channel2_array.append(Chan_2_voltage)
                                    # # Drop off the first y element, append a new one.
                                    update_plot(self.field_array, self.channel2_array, 'red', False, True)

                                # Calculate the average voltage
                                resistance_chan_1 = Chan_1_voltage / float(current[j])
                                resistance_chan_2 = Chan_2_voltage / float(current[j])

                                # Append the data to the CSV file
                                with open(csv_filename, "a", newline="") as csvfile:
                                    csv_writer = csv.writer(csvfile)

                                    if csvfile.tell() == 0:  # Check if file is empty
                                        csv_writer.writerow(
                                            ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)", "Channel 2 "
                                                                                                                  "Resistance ("
                                                                                                                  "Ohm)",
                                             "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                    csv_writer.writerow([MyField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                                         Chan_2_voltage, MyTemp, current[j]])
                                    append_text(f'Data Saved for {MyField} Oe at {MyTemp} K', 'green')
                            elif DSP7265_Connected:
                                try:
                                    X = float(DSP7265.query("X."))  # Read the measurement result
                                    Y = float(DSP7265.query("Y."))  # Read the measurement result
                                    Mag = float(DSP7265.query("MAG."))  # Read the measurement result
                                    Phase = float(DSP7265.query("PHA."))  # Read the measurement result
                                    update_lockin_label(str(Mag), str(Phase))
                                    # self.lockin_x.append(X)
                                    # self.lockin_y.append(Y)
                                    self.lockin_mag.append(Mag)
                                    # self.lockin_pahse.append(Phase)

                                        # # Drop off the first y element, append a new one.
                                    update_plot(self.field_array, self.lockin_mag, 'black', True, False)
                                        # update_plot(self.field_array, self.lockin_pahse, 'red', False, True)
                                except Exception as e:
                                    QMessageBox.warning(self, "Reading Error", f'{e}')

                                resistance_chan_1 = Mag / float(current[j])
                                # Append the data to the CSV file
                                with open(csv_filename, "a", newline="") as csvfile:
                                    csv_writer = csv.writer(csvfile)

                                    if csvfile.tell() == 0:  # Check if file is empty
                                        csv_writer.writerow(
                                            ["Field (Oe)", "Resistance (Ohm)", "Voltage Mag (V)",
                                             "Voltage X (V)", "Voltage Y (V)", "Phase (deg)",
                                                                               "Temperature (K)", "Current (A)"])

                                    csv_writer.writerow(
                                        [currentField, resistance_chan_1, Mag, X, Y,
                                         Phase, MyTemp, current[j]])
                                    self.log_box.append(f'Data Saved for {currentField} Oe at {MyTemp} K\n')

                            try:
                                MyField, sF = client.get_field()
                            except SystemExit as e:
                                error_message(e, e)
                                send_telegram_notification(
                                    "Your measurement went wrong, possible PPMS client lost connection")
                            update_ppms_field_reading_label(str(MyField), 'Oe')
                            MyTemp, sT = client.get_temperature()
                            update_ppms_temp_reading_label(str(MyTemp), 'K')
                            # ----------------------------- Measure NV voltage -------------------
                            deltaH, user_field_rate = deltaH_chk(currentField)

                            append_text(f'deltaH = {deltaH}\n', 'orange')
                            # Update currentField for the next iteration
                            currentField -= deltaH
                            self.pts += 1  # Number of self.pts count
                            single_measurement_end = time.time()
                            Single_loop = single_measurement_end - single_measurement_start
                            number_of_field_update = number_of_field_update - 1
                            append_text('Estimated Single Field measurement (in secs):  {} s \n'.format(Single_loop), 'purple')
                            append_text('Estimated Single measurement (in hrs):  {} hrs \n'.format(
                                Single_loop * number_of_field / 60 / 60), 'purple')
                            total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                                        number_of_temp - i)
                            totoal_time_in_minutes = total_time_in_seconds / 60
                            total_time_in_hours = totoal_time_in_minutes / 60
                            total_time_in_days = total_time_in_hours / 24
                            append_text('Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                total_time_in_seconds), 'purple')
                            append_text(
                                'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                    totoal_time_in_minutes), 'purple')
                            append_text('Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                total_time_in_hours), 'purple')
                            append_text(
                                'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                    total_time_in_days), 'purple')

                        # ----------------- Loop Up ----------------------#
                        currentField = botField
                        deltaH, user_field_rate = deltaH_chk(currentField)
                        send_telegram_notification(f"Starting the second half of measurement - ramping field up")
                        current_progress = int((i + 1) * (j + 1) / totoal_progress * 100) / 2
                        progress_update(int(current_progress))
                        while currentField <= topField:
                            if not running():
                                stop_measurement()
                                return
                            single_measurement_start = time.time()
                            append_text(f'\n Loop is at {currentField} Oe Field Up \n', 'blue')
                            Fieldsetpoint = currentField

                            append_text(f'Set the field to {Fieldsetpoint} Oe and then collect data \n', 'greem')
                            client.set_field(Fieldsetpoint,
                                             user_field_rate,
                                             client.field.approach_mode.linear,
                                             client.field.driven_mode.driven)

                            append_text(f'Waiting for {Fieldsetpoint} Oe Field \n', 'red')
                            time.sleep(4)

                            MyField, sF = client.get_field()
                            update_ppms_field_reading_label(str(MyField), 'Oe')
                            while True:
                                time.sleep(1)
                                try:
                                    MyField, sF = client.get_field()
                                except SystemExit as e:
                                    error_message(e, e)
                                    send_telegram_notification(
                                        "Your measurement went wrong, possible PPMS client lost connection")
                                update_ppms_field_reading_label(str(MyField), 'Oe')
                                append_text(f'Status: {sF}\n', 'blue')
                                if sF == 'Holding (driven)':
                                    break

                            # ----------------------------- Measure NV voltage -------------------
                            append_text(f'Saving data for {MyField} Oe \n', 'green')
                            Chan_1_voltage = 0
                            Chan_2_voltage = 0
                            if Keithley_2182_Connected:
                                keithley_2182nv.write("SENS:FUNC 'VOLT:DC'")
                                keithley_2182nv.write(f"VOLT:DC:NPLC {nv_NPLC}")
                            time.sleep(2)  # Wait for the configuration to complete
                            MyField, sF = client.get_field()
                            update_ppms_field_reading_label(str(MyField), 'Oe')
                            self.field_array.append(MyField)
                            if Keithley_2182_Connected:
                                if nv_channel_1_enabled:
                                    keithley_2182nv.write("SENS:CHAN 1")
                                    volt = keithley_2182nv.query("READ?")
                                    Chan_1_voltage = float(volt)
                                    update_nv_channel_1_label(str(Chan_1_voltage))
                                    append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')
                                    self.channel1_array.append(Chan_1_voltage)
                                    update_plot(self.field_array, self.channel1_array, 'black', True, False)
                                if nv_channel_2_enabled:
                                    keithley_2182nv.write("SENS:CHAN 2")
                                    volt2 = keithley_2182nv.query("READ?")
                                    Chan_2_voltage = float(volt2)
                                    update_nv_channel_2_label(str(Chan_2_voltage))
                                    append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                                    self.channel2_array.append(Chan_2_voltage)
                                    # # Drop off the first y element, append a new one.
                                    update_plot(self.field_array, self.channel2_array, 'red', False, True)
                                resistance_chan_1 = Chan_1_voltage / float(current[j])
                                resistance_chan_2 = Chan_2_voltage / float(current[j])

                                # Append the data to the CSV file
                                with open(csv_filename, "a", newline="") as csvfile:
                                    csv_writer = csv.writer(csvfile)

                                    if csvfile.tell() == 0:  # Check if file is empty
                                        csv_writer.writerow(
                                            ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)", "Channel 2 "
                                                                                                                  "Resistance ("
                                                                                                                  "Ohm)",
                                             "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])
                                    try:
                                        MyField, sF = client.get_field()
                                        update_ppms_field_reading_label(str(MyField), 'Oe')
                                        MyTemp, sT = client.get_temperature()
                                        update_ppms_temp_reading_label(str(MyTemp), 'K')
                                    except SystemExit as e:
                                        error_message(e, e)
                                        send_telegram_notification(
                                            "Your measurement went wrong, possible PPMS client lost connection")
                                    csv_writer.writerow([MyField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                                         Chan_2_voltage, MyTemp, current[j]])
                                    self.log_box.append(f'Data Saved for {MyField} Oe at {MyTemp} K\n')
                            elif DSP7265_Connected:
                                try:
                                    X = float(DSP7265.query("X."))  # Read the measurement result
                                    Y = float(DSP7265.query("Y."))  # Read the measurement result
                                    Mag = float(DSP7265.query("MAG."))  # Read the measurement result
                                    Phase = float(DSP7265.query("PHA."))  # Read the measurement result
                                    update_lockin_label(str(Mag), str(Phase))
                                    # self.lockin_x.append(X)
                                    # self.lockin_y.append(Y)
                                    self.lockin_mag.append(Mag)
                                    # self.lockin_pahse.append(Phase)

                                        # # Drop off the first y element, append a new one.
                                    update_plot(self.field_array, self.lockin_mag, 'black', True, False)
                                        # update_plot(self.field_array, self.lockin_pahse, 'red', False, True)
                                except Exception as e:
                                    QMessageBox.warning(self, "Reading Error", f'{e}')

                                resistance_chan_1 = Mag / float(current[j])
                                # Append the data to the CSV file
                                with open(csv_filename, "a", newline="") as csvfile:
                                    csv_writer = csv.writer(csvfile)

                                    if csvfile.tell() == 0:  # Check if file is empty
                                        csv_writer.writerow(
                                            ["Field (Oe)", "Resistance (Ohm)", "Voltage Mag (V)",
                                             "Voltage X (V)", "Voltage Y (V)", "Phase (deg)",
                                                                               "Temperature (K)", "Current (A)"])

                                    csv_writer.writerow(
                                        [currentField, resistance_chan_1, Mag, X, Y,
                                         Phase, MyTemp, current[j]])
                                    self.log_box.append(f'Data Saved for {currentField} Oe at {MyTemp} K\n')
                            # ----------------------------- Measure NV voltage -------------------
                            deltaH, user_field_rate = deltaH_chk(currentField)

                            append_text(f'deltaH = {deltaH}\n', 'orange')
                            # Update currentField for the next iteration
                            currentField += deltaH
                            self.pts += 1  # Number of self.pts count
                            single_measurement_end = time.time()
                            Single_loop = single_measurement_end - single_measurement_start
                            number_of_field_update = number_of_field_update - 1
                            total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                                        number_of_temp - i)
                            totoal_time_in_minutes = total_time_in_seconds / 60
                            total_time_in_hours = totoal_time_in_minutes / 60
                            total_time_in_days = total_time_in_hours / 24
                            append_text('Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                total_time_in_seconds), 'purple')
                            append_text(
                                'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                    totoal_time_in_minutes), 'purple')
                            append_text(
                                'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                    total_time_in_hours), 'purple')
                            append_text(
                                'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                    total_time_in_days), 'purple')
                    else:
                        try:
                            client.set_field(topField,
                                             Fast_fieldRate,
                                             client.field.approach_mode.linear,
                                             client.field.driven_mode.driven)
                        except SystemExit as e:
                            error_message(e, e)
                            send_telegram_notification(
                                "Your measurement went wrong, possible PPMS client lost connection")
                        append_text(f'Waiting for {topField} Oe Field... \n', 'blue')
                        time.sleep(4)
                        MyField, sF = client.get_field()
                        update_ppms_field_reading_label(str(MyField), 'Oe')
                        while True:
                            try:
                                time.sleep(1.5)
                                MyField, sF = client.get_field()
                                update_ppms_field_reading_label(str(MyField), 'Oe')
                                append_text(f'Status: {sF}\n', 'red')
                                if sF == 'Holding (driven)':
                                    break
                            except SystemExit as e:
                                error_message(e, e)
                                send_telegram_notification(
                                    "Your measurement went wrong, possible PPMS client lost connection")
                        time.sleep(20)
                        deltaH, user_field_rate = deltaH_chk(MyField)
                        currentField = MyField
                        try:
                            client.set_field(botField,
                                             user_field_rate,
                                             client.field.approach_mode.linear,
                                             client.field.driven_mode.driven)
                        except SystemExit as e:
                            error_message(e, e)
                            send_telegram_notification(
                                "Your measurement went wrong, possible PPMS client lost connection")
                        append_text(f'Set the field to {str(botField)} Oe and then collect data \n', 'purple')
                        counter = 0
                        while currentField >= botField:
                            if not running():
                                stop_measurement()
                                return
                            counter += 1
                            single_measurement_start = time.time()
                            if Keithley_2182_Connected:
                                NPLC = nv_NPLC
                                keithley_2182nv.write("SENS:FUNC 'VOLT:DC'")
                                keithley_2182nv.write(f"VOLT:DC:NPLC {NPLC}")
                            time.sleep(1)
                            try:
                                currentField, sF = client.get_field()
                            except SystemExit as e:
                                error_message(e, e)
                                send_telegram_notification(
                                    "Your measurement went wrong, possible PPMS client lost connection")
                            update_ppms_field_reading_label(str(currentField), 'Oe')
                            append_text(f'Saving data for {currentField} Oe \n', 'green')

                            Chan_1_voltage = 0
                            Chan_2_voltage = 0
                            self.field_array.append(currentField)
                            if Keithley_2182_Connected:
                                if nv_channel_1_enabled:
                                    keithley_2182nv.write("SENS:CHAN 1")
                                    volt = keithley_2182nv.query("READ?")
                                    Chan_1_voltage = float(volt)
                                    update_nv_channel_1_label(str(Chan_1_voltage))
                                    append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')
                                    self.channel1_array.append(Chan_1_voltage)
                                    if counter % 20 == 0:
                                        counter = 0
                                        update_plot(self.field_array, self.channel1_array, 'black', True, False)
                                if nv_channel_2_enabled:
                                    keithley_2182nv.write("SENS:CHAN 2")
                                    volt2 = keithley_2182nv.query("READ?")
                                    Chan_2_voltage = float(volt2)
                                    update_nv_channel_2_label(str(Chan_2_voltage))
                                    append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                                    self.channel2_array.append(Chan_2_voltage)
                                    # # Drop off the first y element, append a new one.
                                    if counter % 20 == 0:
                                        counter = 0
                                        update_plot(self.field_array, self.channel2_array, 'red', False, True)

                                # Calculate the average voltage
                                resistance_chan_1 = Chan_1_voltage / float(current[j])
                                resistance_chan_2 = Chan_2_voltage / float(current[j])

                                # Append the data to the CSV file
                                with open(csv_filename, "a", newline="") as csvfile:
                                    csv_writer = csv.writer(csvfile)

                                    if csvfile.tell() == 0:  # Check if file is empty
                                        csv_writer.writerow(
                                            ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)", "Channel 2 "
                                                                                                                  "Resistance ("
                                                                                                                  "Ohm)",
                                             "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                    csv_writer.writerow([currentField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                                         Chan_2_voltage, MyTemp, current[j]])
                                    append_text(f'Data Saved for {currentField} Oe at {MyTemp} K', 'green')
                            elif DSP7265_Connected:
                                try:
                                    X = float(DSP7265.query("X."))  # Read the measurement result
                                    Y = float(DSP7265.query("Y."))  # Read the measurement result
                                    Mag = float(DSP7265.query("MAG."))  # Read the measurement result
                                    Phase = float(DSP7265.query("PHA."))  # Read the measurement result
                                    update_lockin_label(str(Mag), str(Phase))
                                    # self.lockin_x.append(X)
                                    # self.lockin_y.append(Y)
                                    self.lockin_mag.append(Mag)
                                    # self.lockin_pahse.append(Phase)
                                    if counter % 20 == 0:
                                        counter = 0
                                        # # Drop off the first y element, append a new one.
                                        update_plot(self.field_array, self.lockin_mag, 'black', True, False)
                                        # update_plot(self.field_array, self.lockin_pahse, 'red', False, True)
                                except Exception as e:
                                    QMessageBox.warning(self, "Reading Error", f'{e}')

                                resistance_chan_1 = Mag / float(current[j])
                                # Append the data to the CSV file
                                with open(csv_filename, "a", newline="") as csvfile:
                                    csv_writer = csv.writer(csvfile)

                                    if csvfile.tell() == 0:  # Check if file is empty
                                        csv_writer.writerow(
                                            ["Field (Oe)", "Resistance (Ohm)", "Voltage Mag (V)",
                                             "Voltage X (V)", "Voltage Y (V)", "Phase (deg)",
                                                                               "Temperature (K)", "Current (A)"])

                                    csv_writer.writerow(
                                        [currentField, resistance_chan_1, Mag, X, Y,
                                         Phase, MyTemp, current[j]])
                                    self.log_box.append(f'Data Saved for {currentField} Oe at {MyTemp} K\n')
                            # ----------------------------- Measure NV voltage -------------------
                            deltaH, user_field_rate = deltaH_chk(currentField)

                            append_text(f'Field Rate = {user_field_rate}\n', 'orange')
                            # Update currentField for the next iteration
                            # currentField -= deltaH
                            self.pts += 1  # Number of self.pts count
                            single_measurement_end = time.time()
                            Single_loop = single_measurement_end - single_measurement_start
                            number_of_field_update = number_of_field_update - 1
                            append_text('Estimated Single Field measurement (in secs):  {} s \n'.format(Single_loop),
                                        'purple')
                            append_text('Estimated Single measurement (in hrs):  {} hrs \n'.format(
                                Single_loop * number_of_field / 60 / 60), 'purple')
                            total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                                    number_of_temp - i)
                            totoal_time_in_minutes = total_time_in_seconds / 60
                            total_time_in_hours = totoal_time_in_minutes / 60
                            total_time_in_days = total_time_in_hours / 24
                            append_text('Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                total_time_in_seconds), 'purple')
                            append_text(
                                'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                    totoal_time_in_minutes), 'purple')
                            append_text(
                                'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                    total_time_in_hours), 'purple')
                            append_text(
                                'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                    total_time_in_days), 'purple')
                            # currentField, sF = client.get_field()
                            # update_ppms_field_reading_label(str(currentField), 'Oe')

                        # ----------------- Loop Up ----------------------#
                        send_telegram_notification(f"Starting the second half of measurement - ramping field up")
                        currentField = botField
                        client.set_field(currentField,
                                         user_field_rate,
                                         client.field.approach_mode.linear,
                                         client.field.driven_mode.driven)
                        append_text(f'Set the field to {currentField} Oe and then collect data \n', 'greem')
                        time.sleep(4)
                        currentField, sF = client.get_field()
                        update_ppms_field_reading_label(str(currentField), 'Oe')

                        while True:
                            time.sleep(1)
                            try:
                                currentField, sF = client.get_field()
                            except SystemExit as e:
                                error_message(e, e)
                                send_telegram_notification(
                                    "Your measurement went wrong, possible PPMS client lost connection")
                            update_ppms_field_reading_label(str(currentField), 'Oe')
                            append_text(f'Status: {sF}\n', 'blue')
                            if sF == 'Holding (driven)':
                                break

                        deltaH, user_field_rate = deltaH_chk(currentField)
                        time.sleep(20)
                        client.set_field(topField,
                                         user_field_rate,
                                         client.field.approach_mode.linear,
                                         client.field.driven_mode.driven)
                        append_text(f'Set the field to {str(botField)} Oe and then collect data \n', 'purple')
                        counter = 0
                        current_progress = int((i + 1) * (j + 1) / totoal_progress * 100)/2
                        progress_update(int(current_progress))
                        while currentField <= topField:
                            if not running():
                                print('Not Running')
                                stop_measurement()
                                return
                            counter += 1
                            single_measurement_start = time.time()
                            if Keithley_2182_Connected:
                                keithley_2182nv.write("SENS:FUNC 'VOLT:DC'")
                                keithley_2182nv.write(f"VOLT:DC:NPLC {nv_NPLC}")
                            time.sleep(1)
                            try:
                                currentField, sF = client.get_field()
                            except SystemExit as e:
                                error_message(e, e)
                                send_telegram_notification(
                                    "Your measurement went wrong, possible PPMS client lost connection")
                            update_ppms_field_reading_label(str(currentField), 'Oe')
                            append_text(f'Saving data for {currentField} Oe \n', 'green')

                            Chan_1_voltage = 0
                            Chan_2_voltage = 0
                            self.field_array.append(currentField)
                            if Keithley_2182_Connected:
                                if nv_channel_1_enabled:
                                    keithley_2182nv.write("SENS:CHAN 1")
                                    volt = keithley_2182nv.query("READ?")
                                    Chan_1_voltage = float(volt)
                                    update_nv_channel_1_label(str(Chan_1_voltage))
                                    append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')
                                    self.channel1_array.append(Chan_1_voltage)
                                    if counter % 20 == 0:
                                        counter = 0
                                        update_plot(self.field_array, self.channel1_array, 'black', True, False)
                                if nv_channel_2_enabled:
                                    keithley_2182nv.write("SENS:CHAN 2")
                                    volt2 = keithley_2182nv.query("READ?")
                                    Chan_2_voltage = float(volt2)
                                    update_nv_channel_2_label(str(Chan_2_voltage))
                                    append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                                    self.channel2_array.append(Chan_2_voltage)
                                    if counter % 20 == 0:
                                        counter = 0
                                    # # Drop off the first y element, append a new one.
                                        update_plot(self.field_array, self.channel2_array, 'red', False, True)

                                resistance_chan_1 = Chan_1_voltage / float(current[j])
                                resistance_chan_2 = Chan_2_voltage / float(current[j])
                                # Append the data to the CSV file
                                with open(csv_filename, "a", newline="") as csvfile:
                                    csv_writer = csv.writer(csvfile)

                                    if csvfile.tell() == 0:  # Check if file is empty
                                        csv_writer.writerow(
                                            ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)", "Channel 2 "
                                                                                                                  "Resistance ("
                                                                                                                  "Ohm)",
                                             "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                    csv_writer.writerow([currentField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                                         Chan_2_voltage, MyTemp, current[j]])
                                    self.log_box.append(f'Data Saved for {currentField} Oe at {MyTemp} K\n')
                            elif DSP7265_Connected:
                                try:
                                    X = float(DSP7265.query("X."))  # Read the measurement result
                                    Y = float(DSP7265.query("Y."))  # Read the measurement result
                                    Mag = float(DSP7265.query("MAG."))  # Read the measurement result
                                    Phase = float(DSP7265.query("PHA."))  # Read the measurement result
                                    update_lockin_label(str(Mag), str(Phase))
                                    # self.lockin_x.append(X)
                                    # self.lockin_y.append(Y)
                                    self.lockin_mag.append(Mag)
                                    # self.lockin_pahse.append(Phase)
                                    if counter % 20 == 0:
                                        counter = 0
                                    # # Drop off the first y element, append a new one.
                                        update_plot(self.field_array, self.lockin_mag, 'black', True, False)
                                        # update_plot(self.field_array, self.lockin_pahse, 'red', False, True)
                                except Exception as e:
                                    QMessageBox.warning(self, "Reading Error", f'{e}')

                                resistance_chan_1 = Mag / float(current[j])
                                # Append the data to the CSV file
                                with open(csv_filename, "a", newline="") as csvfile:
                                    csv_writer = csv.writer(csvfile)

                                    if csvfile.tell() == 0:  # Check if file is empty
                                        csv_writer.writerow(
                                            ["Field (Oe)", "Resistance (Ohm)", "Voltage Mag (V)",
                                             "Voltage X (V)","Voltage Y (V)", "Phase (deg)",
                                             "Temperature (K)", "Current (A)"])

                                    csv_writer.writerow(
                                        [currentField, resistance_chan_1, Mag, X, Y,
                                         Phase, MyTemp, current[j]])
                                    self.log_box.append(f'Data Saved for {currentField} Oe at {MyTemp} K\n')

                            # ----------------------------- Measure NV voltage -------------------
                            deltaH, user_field_rate = deltaH_chk(currentField)

                            append_text(f'Field Rate = {user_field_rate}\n', 'orange')
                            # Update currentField for the next iteration
                            # Update currentField for the next iteration
                            self.pts += 1  # Number of self.pts count
                            single_measurement_end = time.time()
                            Single_loop = single_measurement_end - single_measurement_start
                            number_of_field_update = number_of_field_update - 1
                            total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                                    number_of_temp - i)
                            totoal_time_in_minutes = total_time_in_seconds / 60
                            total_time_in_hours = totoal_time_in_minutes / 60
                            total_time_in_days = total_time_in_hours / 24
                            append_text('Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                total_time_in_seconds), 'purple')
                            append_text(
                                'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                    totoal_time_in_minutes), 'purple')
                            append_text(
                                'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                    total_time_in_hours), 'purple')
                            append_text(
                                'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                    total_time_in_days), 'purple')
                            # currentField, sF = client.get_field()
                            # update_ppms_field_reading_label(str(currentField), 'Oe')
                    if Keithley_2182_Connected:
                        if nv_channel_1_enabled:
                           save_plot(self.field_array, self.channel1_array, 'black', True, False, True, str(TempList[i]), str(current[j]))
                        if nv_channel_2_enabled:
                           save_plot(self.field_array, self.channel2_array, 'red', False, True, True, str(TempList[i]), str(current[j]))
                    elif DSP7265_Connected:
                        save_plot(self.field_array, self.lockin_mag, 'black', True, False, True, str(TempList[i]), str(current[j]))
                        # update_plot(self.field_array, self.lockin_pahse, 'red', False, True)


                    send_telegram_notification(f"{str(TempList[i])} K, {current_mag[j]} {current_unit} measurement has finished")
                    current_progress = int((i+1) * (j+1) / totoal_progress * 100)
                    progress_update(int(current_progress))
            time.sleep(2)
            client.set_field(zeroField,
                             Fast_fieldRate,
                             client.field.approach_mode.oscillate,  # linear/oscillate
                             client.field.driven_mode.driven)
            append_text('Waiting for Zero Field', 'red')
            time.sleep(2)
            temperature, status = client.get_temperature()
            append_text(f'Finished Temperature = {temperature} K', 'green')
            update_ppms_temp_reading_label(str(temperature), 'K')
            time.sleep(2)
            field, status = client.get_field()
            fieldUnits = client.field.units
            append_text(f'Finisehd Field = {field} {fieldUnits}\n', 'red')
            update_ppms_field_reading_label(str(field), 'Oe')
            if Ketihley_6221_Connected:
                keithley_6221.write(":SOR:CURR:LEV 0")  # Set current level to zero
                keithley_6221.write(":OUTP OFF")  # Turn off the output
            append_text("DC current is set to: 0.00 A\n", 'red')
            # keithley_6221_Curr_Src.close()

            # Calculate the total runtime
            end_time = time.time()
            total_runtime = (end_time - start_time) / 3600
            self.log_box.append(f"Total runtime: {total_runtime} hours\n")
            self.log_box.append(f'Total data points: {str(self.pts)} pts\n')
            send_telegram_notification("The measurement has been completed successfully.")
            progress_update(int=100)
            append_text("You measuremnt is finished!", 'green')
            stop_measurement()
            measurement_finished()
            return
        except SystemExit as e:
            send_telegram_notification("Your measurement went wrong, possible PPMS client lost connection")
            error_message(e,e)
            stop_measurement()

    def send_telegram_notification(self, message):
        bot_token = self.token_file
        chat_id = "5733353343"
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        response = requests.post(url, data=data)
        return response.json()




# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     main_window = Measurement()
#     main_window.show()
#     sys.exit(app.exec())
