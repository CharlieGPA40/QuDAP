import sys
from PyQt6.QtWidgets import (
    QSizePolicy, QWidget, QMessageBox, QGroupBox, QFileDialog, QVBoxLayout, QLabel, QHBoxLayout,
    QCheckBox, QTextEdit, QPushButton, QComboBox, QLineEdit, QScrollArea, QDialog, QRadioButton, QMainWindow,
    QDialogButtonBox, QProgressBar, QButtonGroup
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread
import pyvisa as visa
import matplotlib
import numpy as np

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import random
import time
import MultiPyVu as mpv  # Uncommented it on the server computer
from MultiPyVu import MultiVuClient as mvc, MultiPyVuError
from datetime import datetime

class LogWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.font = QFont("Arial", 13)
        self.ID = None
        self.Measurement = None
        self.run = None
        self.folder_path = None
        self.setStyleSheet('Background: white')
        with open("GUI/SHG/QButtonWidget.qss", "r") as file:
            self.Browse_Button_stylesheet = file.read()
        self.layout = QVBoxLayout()
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
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.ID}_{self.Measurement}_300_K_20_uA_Run_{self.run}.txt"
        self.example_file_name.setText(self.file_name)

    def open_folder_dialog(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if self.folder_path:
            self.folder_path = self.folder_path +'/'
            self.folder_entry_box.setText(self.folder_path)

    def accept(self):
        self.commemt = self.comment_entry_box.text()
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.ID}_{self.Measurement}"
        # Call the inherited accept method to close the dialog
        super().accept()

    def get_text(self):
        return self.folder_path, self.file_name, self.formatted_date, self.ID, self.Measurement, self.run, self.commemt

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
            self.init_ui()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
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
        self.Preset_group_box = QGroupBox("Preseted Measure")

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
                print(e)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
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
            self.host_entry_box.setFixedHeight(30)
            self.port_label = QLabel("PPMS Port:")
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
            toolbar = NavigationToolbar(self.canvas, self)
            toolbar.setStyleSheet("""
                                             QWidget {
                                                 border: None;
                                             }
                                         """)
            figure_Layout.addWidget(toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
            figure_Layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)
            figure_group_box.setLayout(figure_Layout)
            figure_group_box.setFixedSize(1140,400)
            self.figure_container_layout = QHBoxLayout()
            self.figure_container = QWidget(self)
            self.buttons_layout = QHBoxLayout()
            self.start_measurement_btn = QPushButton('Start')
            self.start_measurement_btn.clicked.connect(self.start_measurement)
            self.stop_btn = QPushButton('Stop')
            self.rst_btn = QPushButton('Reset')
            self.rst_btn.clicked.connect(self.preset_reset)
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
        except Exception as e:
            print(e)
        rm = visa.ResourceManager('@sim')
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
                self.server = mpv.Server()
            except MultiPyVuError:
                QMessageBox.critical('Check MutltiVu', 'Run MultiVu without Admin or open MultiVu correctly!')
            self.server_btn.setText('Stop Server')
            self.server_btn_clicked = True
            self.connect_btn.setEnabled(True)
            self.server.open()
        elif self.server_btn_clicked == True:
            self.server.close()
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
            self.ppms_temp_One_zone_radio = QRadioButton("1 Zone")
            self.ppms_temp_One_zone_radio.setFont(self.font)
            self.ppms_temp_One_zone_radio.toggled.connect(self.temp_zone_selection)
            self.ppms_temp_Two_zone_radio = QRadioButton("2 Zones")
            self.ppms_temp_Two_zone_radio.setFont(self.font)
            self.ppms_temp_Two_zone_radio.toggled.connect(self.temp_zone_selection)
            self.ppms_temp_Three_zone_radio = QRadioButton("3 Zones")
            self.ppms_temp_Three_zone_radio.setFont(self.font)
            self.ppms_temp_Three_zone_radio.toggled.connect(self.temp_zone_selection)
            self.ppms_temp_Customize_zone_radio = QRadioButton("Customize")
            self.ppms_temp_Customize_zone_radio.setFont(self.font)
            self.ppms_temp_Customize_zone_radio.toggled.connect(self.temp_zone_selection)
            self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_One_zone_radio)
            self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_Two_zone_radio)
            self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_Three_zone_radio)
            self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_Customize_zone_radio)
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

            self.ppms_field_mode_fast_radio = QRadioButton("Fast Sweep")
            self.ppms_field_mode_fast_radio.setFont(self.font)
            self.ppms_field_mode_fast_radio.setChecked(True)
            self.ppms_field_mode_fixed_radio = QRadioButton("Fixed Field")
            self.ppms_field_mode_fixed_radio.setFont(self.font)
            self.ppms_field_mode_buttom_layout.addWidget(self.ppms_field_mode_fast_radio)
            self.ppms_field_mode_buttom_layout.addWidget(self.ppms_field_mode_fixed_radio)
            self.ppms_field_mode_buttom_group = QButtonGroup()
            self.ppms_field_mode_buttom_group.addButton(self.ppms_field_mode_fast_radio)
            self.ppms_field_mode_buttom_group.addButton(self.ppms_field_mode_fixed_radio)

            self.ppms_field_One_zone_radio = QRadioButton("1 Zone")
            self.ppms_field_One_zone_radio.setFont(self.font)
            self.ppms_field_One_zone_radio.toggled.connect(self.field_zone_selection)
            self.ppms_field_Two_zone_radio = QRadioButton("2 Zones")
            self.ppms_field_Two_zone_radio.setFont(self.font)
            self.ppms_field_Two_zone_radio.toggled.connect(self.field_zone_selection)
            self.ppms_field_Three_zone_radio = QRadioButton("3 Zones")
            self.ppms_field_Three_zone_radio.setFont(self.font)
            self.ppms_field_Three_zone_radio.toggled.connect(self.field_zone_selection)
            self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_One_zone_radio)
            self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_Two_zone_radio)
            self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_Three_zone_radio)
            self.ppms_field_setting_layout.addLayout(self.ppms_field_mode_buttom_layout)
            self.ppms_field_setting_layout.addLayout(self.ppms_field_radio_buttom_layout)
            self.ppms_field_setting_layout.addLayout(self.ppms_zone_field_layout)
            self.ppms_Field_group_box.setLayout(self.ppms_field_setting_layout)
            self.PPMS_measurement_setup_layout.addWidget(self.ppms_reading_group_box, 1)
            self.PPMS_measurement_setup_layout.addWidget(self.ppms_Temp_group_box, 2)
            self.PPMS_measurement_setup_layout.addWidget(self.ppms_Field_group_box, 2)

        elif self.connect_btn_clicked == True:
            self.client.close_client()
            self.clear_layout(self.PPMS_measurement_setup_layout)
            self.client_keep_going = False
            self.connect_btn.setText('Start Client')
            self.connect_btn_clicked = False
            self.server_btn.setEnabled(True)

    def connect_devices(self):
        self.rm = visa.ResourceManager('@sim')
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
                        QMessageBox.warning(self, 'Error', str(e))
                        self.instru_connect_btn.setText('Connect')
                elif self.current_connection_index == 2:
                    try:
                        self.connect_keithley_6221()
                    except Exception as e:
                        self.Ketihley_6221_Connected = False
                        QMessageBox.warning(self, 'Error', str(e))
                        self.instru_connect_btn.setText('Connect')
                elif self.current_connection_index == 3:
                    try:
                        self.connect_dsp7265()
                    except Exception as e:
                        self.DSP7265_Connected = False
                        QMessageBox.warning(self, 'Error', str(e))
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
                        QMessageBox.warning(self, 'Error', str(e))
                        self.instru_connect_btn.setText('Connect')
                elif self.current_connection_index == 2:
                    try:
                        self.connect_keithley_6221()
                    except Exception as e:
                        self.Ketihley_6221_Connected = False
                        QMessageBox.warning(self, 'Error', str(e))
                        self.instru_connect_btn.setText('Connect')
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")

    def connect_keithley_2182(self):
        if self.Keithley_2182_Connected == False:
            try:
                self.keithley_2182nv = self.rm.open_resource(self.current_connection, timeout=10000)
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
                self.DSP7265_Connected = True
                self.instru_connect_btn.setText('Disconnect')
                self.keithley2182_Window()
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
            QMessageBox.warning(self, "Error", str(e))

    def close_keithley_6221(self):
        try:
            self.keithley_6221.close()
            self.Ketihley_6221_Connected = False
            self.clear_layout(self.keithley_6221_contain_layout)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

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

    def keithley2182_Window(self):
        self.Keithley_2182_Container = QWidget(self)
        self.keithley_2182_groupbox = QGroupBox('Keithley 2182nv')
        self.NPLC_layout = QHBoxLayout()
        self.NPLC_Label = QLabel('NPLC:')
        self.NPLC_Label.setFont(self.font)
        self.NPLC_entry = QLineEdit()
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
        self.keithley_2182_groupbox.setFixedSize(365, 150)
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
        self.keithley_6221_groupbox.setFixedSize(740, 150)
        self.keithley_6221_contain_layout = QHBoxLayout()
        self.keithley_6221_contain_layout.addWidget(self.keithley_6221_groupbox)
        self.Instruments_measurement_setup_layout.addLayout(self.keithley_6221_contain_layout)

    def Keithley_6221_DC(self):
        try:
            self.clear_layout(self.Keithey_curSour_layout)
        except Exception as e:
            print(e)
        self.keithley_6221_DC_range_single_layout = QVBoxLayout()
        self.keithley_6221_DC_range_layout = QHBoxLayout()
        self.keithley_6221_DC_range_checkbox = QCheckBox('Range')
        self.keithley_6221_DC_range_checkbox.stateChanged.connect(self.on_6221_DC_toggle)
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
        self.keithley_6221_DC_single_checkbox = QCheckBox('Single')
        self.keithley_6221_DC_single_checkbox.stateChanged.connect(self.on_6221_DC_toggle)
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

    def Keithley_6221_AC(self):
        self.keithley_6221_AC_layout = QHBoxLayout()
        self.keithley_6221_DC = QCheckBox('Channel 2:')
        try:
            self.clear_layout(self.Keithey_curSour_layout)
        except Exception as e:
            print(e)

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
        self.ppms_zone1_from_label = QLabel('Field Range (Oe): From')
        self.ppms_zone1_from_label.setFont(self.font)
        self.ppms_zone1_from_entry = QLineEdit()
        self.ppms_zone1_from_entry.setFont(self.font)
        self.ppms_zone1_to_label = QLabel(' to ')
        self.ppms_zone1_to_label.setFont(self.font)
        self.ppms_zone1_to_entry = QLineEdit()
        self.ppms_zone1_to_entry.setFont(self.font)
        self.ppms_zone1_field_range_layout.addWidget(self.ppms_zone1_from_label)
        self.ppms_zone1_field_range_layout.addWidget(self.ppms_zone1_from_entry)
        self.ppms_zone1_field_range_layout.addWidget(self.ppms_zone1_to_label)
        self.ppms_zone1_field_range_layout.addWidget(self.ppms_zone1_to_entry)

        self.ppms_zone1_field_step_layout = QHBoxLayout()
        self.ppms_zone1_field_step_label = QLabel('Step Size (Oe): ')
        self.ppms_zone1_field_step_label.setFont(self.font)
        self.ppms_zone1_field_step_entry = QLineEdit()
        self.ppms_zone1_field_step_entry.setFont(self.font)
        self.ppms_zone1_field_rate_label = QLabel('Field Rate (Oe/sec): ')
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
        self.ppms_zone2_field_layout = QVBoxLayout()
        self.ppms_zone2_field_range_layout = QHBoxLayout()
        self.ppms_zone2_from_label = QLabel('Field Range 2 (Oe): From')
        self.ppms_zone2_from_label.setFont(self.font)
        self.ppms_zone2_from_entry = QLineEdit()
        self.ppms_zone2_from_entry.setFont(self.font)
        self.ppms_zone2_to_label = QLabel(' to ')
        self.ppms_zone2_to_label.setFont(self.font)
        self.ppms_zone2_to_entry = QLineEdit()
        self.ppms_zone2_to_entry.setFont(self.font)
        self.ppms_zone2_field_range_layout.addWidget(self.ppms_zone2_from_label)
        self.ppms_zone2_field_range_layout.addWidget(self.ppms_zone2_from_entry)
        self.ppms_zone2_field_range_layout.addWidget(self.ppms_zone2_to_label)
        self.ppms_zone2_field_range_layout.addWidget(self.ppms_zone2_to_entry)

        self.ppms_zone2_field_step_layout = QHBoxLayout()
        self.ppms_zone2_field_step_label = QLabel('Step Size 2 (Oe): ')
        self.ppms_zone2_field_step_label.setFont(self.font)
        self.ppms_zone2_field_step_entry = QLineEdit()
        self.ppms_zone2_field_step_entry.setFont(self.font)

        self.ppms_zone2_field_rate_label = QLabel('Field Rate (Oe/sec): ')
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
        self.ppms_zone3_field_layout = QVBoxLayout()
        self.ppms_zone3_field_range_layout = QHBoxLayout()
        self.ppms_zone3_from_label = QLabel('Field Range 3 (Oe): From')
        self.ppms_zone3_from_label.setFont(self.font)
        self.ppms_zone3_from_entry = QLineEdit()
        self.ppms_zone3_from_entry.setFont(self.font)
        self.ppms_zone3_to_label = QLabel(' to ')
        self.ppms_zone3_to_label.setFont(self.font)
        self.ppms_zone3_to_entry = QLineEdit()
        self.ppms_zone3_to_entry.setFont(self.font)
        self.ppms_zone3_field_range_layout.addWidget(self.ppms_zone3_from_label)
        self.ppms_zone3_field_range_layout.addWidget(self.ppms_zone3_from_entry)
        self.ppms_zone3_field_range_layout.addWidget(self.ppms_zone3_to_label)
        self.ppms_zone3_field_range_layout.addWidget(self.ppms_zone3_to_entry)

        self.ppms_zone3_field_step_layout = QHBoxLayout()
        self.ppms_zone3_field_step_label = QLabel('Step Size 3 (Oe): ')
        self.ppms_zone3_field_step_label.setFont(self.font)
        self.ppms_zone3_field_step_entry = QLineEdit()
        self.ppms_zone3_field_step_entry.setFont(self.font)

        self.ppms_zone3_field_rate_label = QLabel('Field Rate (Oe/sec): ')
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
        self.ppms_zone1_temp_from_label = QLabel('Temperature Range (K): From')
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

        self.ppms_zone1_temp_rate_label = QLabel('Temp Rate (K/min): ')
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
        self.ppms_zone2_temp_from_label = QLabel('Temperature Range 2 (K): From')
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
        self.ppms_zone3_temp_from_label = QLabel('Temperature Range 3 (K): From')
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
        self.ppms_zone_cus_temp_rate_label = QLabel('Temp Rate (K/min): ')
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

    def update_plot(self):
        if self.isCheckedBox1 == True:
            self.isPlotting = True
            self.channel1_Volt_Array.append(self.Chan_1_voltage)
            self.canvas.axes.plot(self.counter_array, self.channel1_Volt_Array, 'black')
            self.canvas.draw()
        if self.isCheckedBox2 == True:
            self.isPlotting = True
            self.channel2_Volt_Array.append(self.Chan_2_voltage)
            self.canvas.axes.plot(self.counter_array, self.channel2_Volt_Array, 'r')
            self.canvas.draw()
        self.counter += 1
        self.counter_array.append(self.counter)

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

    def stop(self):
        self.timer.stop()

    def rst(self):
        self.timer = QTimer()
        self.timer.stop()
        self.canvas.axes.cla()
        self.canvas.draw()

    def start_measurement(self):
        dialog = LogWindow()
        if dialog.exec():
            try:
                self.folder_path, self.file_name, self.formatted_date, self.ID, self.Measurement, self.run, self.commemt = dialog.get_text()
                self.log_box = QTextEdit(self)
                self.log_box.setReadOnly(True)  # Make the log box read-only
                self.progress_bar = QProgressBar(self)
                self.progress_bar.setMinimum(0)
                self.progress_bar.setMaximum(100)
                self.progress_value = 50
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
                self.main_layout.addWidget(self.log_box)
                self.main_layout.addWidget(self.progress_bar)

            except Exception as e:
                QMessageBox.warning(self, 'Warning', str(e))

            try:
                self.run_ETO()
            except Exception as e:
                QMessageBox.warning(self, 'Warning', str(e))

    def run_ETO(self):
        self.log_box.clear()
        self.log_box.append('Check Connection of Keithley 6221....')
        # try:
        #     self.keithley_6221.query('*IDN?')
        # except visa.errors.VisaIOError as e:
        #     QMessageBox.warning(self, 'Fail to connect Keithley 6221', str(e))
        #     return
        self.log_box.append('Keithley 6221 connected!')
        self.log_box.append('Check Connection of Keithley 2182....')
        # try:
        #     self.keithley_2182nv.query('*IDN?')
        # except visa.errors.VisaIOError as e:
        #     QMessageBox.warning(self, 'Fail to connect Keithley 2182', str(e))
        #     return
        self.log_box.append('Keithley 2182 connected!')
        def float_range(start, stop, step):
            current = start
            while current < stop:
                yield current
                current += step
        try:
            TempList = []
            if self.ppms_temp_One_zone_radio.isChecked():
                # if len(self.ppms_zone1_temp_from_entry.text()) == 0 or len(self.ppms_zone1_temp_to_entry.text()) == 0 or len(self.ppms_zone1_temp_step_entry.text()) == 0:
                #     QMessageBox.warning(self, 'Warning', 'Please enter all required box')
                zone_1_start = float(self.ppms_zone1_temp_from_entry.text())
                zone_1_end = float(self.ppms_zone1_temp_to_entry.text()) + float(self.ppms_zone1_temp_step_entry.text())
                zone_1_step = float(self.ppms_zone1_temp_step_entry.text())
                TempList = [round(float(i), 2) for i in float_range(zone_1_start, zone_1_end, zone_1_step)]
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
                TempList += [round(float(i), 2) for i in float_range(zone_2_start, zone_2_end + zone_2_step, zone_2_step)]
                tempRate = round(float(self.ppms_zone1_temp_rate_entry.text()), 2)
            elif self.ppms_temp_Three_zone_radio.isChecked():
                zone_1_start = float(self.ppms_zone1_temp_from_entry.text())
                zone_1_end = float(self.ppms_zone1_temp_to_entry.text())
                zone_1_step = float(self.ppms_zone1_temp_step_entry.text())

                zone_2_start = float(self.ppms_zone2_temp_from_entry.text())
                zone_2_end = float(self.ppms_zone2_temp_to_entry.text())
                zone_2_step = float(self.ppms_zone2_temp_step_entry.text())

                zone_3_start = float(self.ppms_zone3_temp_from_entry.text())
                zone_3_end = float(self.ppms_zone3_temp_to_entry.text()) + float(self.ppms_zone3_temp_step_entry.text())
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
                tempRate = round(float(self.ppms_zone_cus_temp_rate_entry.text()),2)
        except Exception as e:
            QMessageBox.warning(self, 'Error', str(e))
        self.log_box.append('Measurement Temperature '+ TempList)
        # =============================== Set the Field ==================================== #
        if self.ppms_field_One_zone_radio.isChecked():
            self.zone1_bot_field = float(self.ppms_zone1_from_entry.text())
            self.zone1_top_field = float(self.ppms_zone1_to_entry.text())
            self.zone1_step_field = float(self.ppms_zone1_field_step_entry.text())
            self.zone1_field_rate = float(self.ppms_zone1_field_rate_entry.text())
            number_of_field_zone1 = 2 * (self.zone1_top_field - self.zone1_bot_field) / self.zone1_step_field
            number_of_field = np.abs(number_of_field_zone1)
        elif self.ppms_field_Two_zone_radio.isChecked():
            self.zone1_bot_field = float(self.ppms_zone1_from_entry.text())
            self.zone1_top_field = float(self.ppms_zone1_to_entry.text())
            self.zone1_step_field = float(self.ppms_zone1_field_step_entry.text())
            self.zone1_field_rate = float(self.ppms_zone1_field_rate_entry.text())
            self.zone2_bot_field = float(self.ppms_zone2_from_entry.text())
            self.zone2_top_field = float(self.ppms_zone2_to_entry.text())
            self.zone2_step_field = float(self.ppms_zone2_field_step_entry.text())
            self.zone2_field_rate = float(self.ppms_zone2_field_rate_entry.text())
            # Need to think about it
            number_of_field_zone1 = 2 * (self.zone1_top_field - self.zone1_bot_field) / self.zone1_step_field
            number_of_field_zone2 = 2 * (self.zone2_top_field - self.zone2_bot_field) / self.zone2_step_field
            number_of_field = np.abs(number_of_field_zone1) + np.abs(number_of_field_zone2)
        elif self.ppms_field_Three_zone_radio.isChecked():
            self.zone1_bot_field = float(self.ppms_zone1_from_entry.text())
            self.zone1_top_field = float(self.ppms_zone1_to_entry.text())
            self.zone1_step_field = float(self.ppms_zone1_field_step_entry.text())
            self.zone1_field_rate = float(self.ppms_zone1_field_rate_entry.text())
            self.zone2_bot_field = float(self.ppms_zone2_from_entry.text())
            self.zone2_top_field = float(self.ppms_zone2_to_entry.text())
            self.zone2_step_field = float(self.ppms_zone2_field_step_entry.text())
            self.zone1_field_rate = float(self.ppms_zone1_field_rate_entry.text())
            self.zone3_bot_field = float(self.ppms_zone3_from_entry.text())
            self.zone3_top_field = float(self.ppms_zone3_to_entry.text())
            self.zone3_step_field = float(self.ppms_zone3_field_step_entry.text())
            self.zone3_field_rate = float(self.ppms_zone3_field_rate_entry.text())
            # Need to think about it
            number_of_field_zone1 = 2 * (self.zone1_top_field - self.zone1_bot_field) / self.zone1_step_field
            number_of_field_zone2 = 2 * (self.zone2_top_field - self.zone2_bot_field) / self.zone2_step_field
            number_of_field_zone3 = 2 * (self.zone3_top_field - self.zone3_bot_field) / self.zone3_step_field
            number_of_field = np.abs(number_of_field_zone1) + np.abs(number_of_field_zone2) + np.abs(number_of_field_zone3)
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
                    elif self.DC_Range_unit == 2:  # uA
                        DC_range_selected_unit = 'e-6'
                    elif self.DC_Range_unit == 3:  # nA
                        DC_range_selected_unit = 'e-9'
                    elif self.DC_Range_unit == 4:  # pA
                        DC_range_selected_unit = 'e-12'
                current = [f"{i}{DC_range_selected_unit}" for i in range(init_current, final_current+step_current, step_current)]
            elif self.keithley_6221_DC_single_checkbox.isChecked():
                self.single_DC_current = self.keithley_6221_DC_single_entry.text()
                self.DC_Single_unit = self.keithley_6221_DC_single_combobox.currentIndex()
                if self.DC_Single_unit != 0:
                    if self.DC_Range_unit == 1:  # mA
                        DC_single_selected_unit = 'e-3'
                    elif self.DC_Range_unit == 2:  # uA
                        DC_single_selected_unit = 'e-6'
                    elif self.DC_Range_unit == 3:  # nA
                        DC_single_selected_unit = 'e-9'
                    elif self.DC_Range_unit == 4:  # pA
                        DC_single_selected_unit = 'e-12'
                current = [f"{i}{DC_single_selected_unit}"]
            else:
                QMessageBox.warning(self, 'Warning', 'Please choose one of the options')
                return
        elif self.keithley_6221_DC_radio.isChecked():
            QMessageBox.warning(self, "New Feature is coming", 'Abort')
            return


        number_of_current = len(current)
        number_of_temp = len(TempList)
        tempRate_init = 50
        zeroField = 0
        start_time = time.time()

        # fieldRate = 220
        # fieldRateSweeping = 10

        def deltaH_chk(deltaH_small, deltaH_med, deltaH_large, currentField):
            if (currentField <= LowerB2 or currentField >= UpperB2):
                deltaH = deltaH_large

            elif (currentField > LowerB2 and currentField <= LowerB1):
                deltaH = deltaH_med

            elif (currentField < UpperB2 and currentField >= UpperB1):
                deltaH = deltaH_med

            elif (currentField > LowerB1 and currentField < UpperB1):
                deltaH = deltaH_small

            return deltaH

        def save_temp_field_chamber():
            T, sT = self.client.get_temperature()
            F, sF = self.client.get_field()
            C = self.client.get_chamber()
            print(f'{T:{7}.{3}f} {sT:{10}} {F:{7}} {sF:{20}} {C:{15}}')


        time.sleep(5)

        # -------------Temp Status---------------------
        temperature, status = self.client.get_temperature()
        tempUnits = self.client.temperature.units
        print(f'\nTemperature = {temperature} {tempUnits}')

        # ------------Field Status----------------------
        field, status = client.get_field()
        fieldUnits = client.field.units
        print(f'Field = {field} {fieldUnits}')

        # ------------Purge/Seal------------------------
        if temperature == 300 and field == 0:
            # Purge/Seal the chamber; wait to continue
            print('Change the chamber state to Purge/Seal')
            client.set_chamber(client.chamber.mode.purge_seal)
            # client.wait_for(10, 0, client.subsystem.chamber)

        # ---------------print a header----------------
        print('')
        hdr = '______ T ______     __________ H __________\t______ Chamber Status ______'
        print(hdr)
        save_temp_field_chamber()

        # # ----------------------- Set Temperature-------------------------------------
        # CurrentTemp, sT = client.get_temperature()
        # #points = 10
        #
        # setpoint = 1.775 #1.7 K Setpoint
        # tempRate = 50
        #
        # wait = abs(CurrentTemp-setpoint)/tempRate*60
        # message = f'Set the temperature {setpoint} K at {tempRate} K rate '
        # message += f'wait {wait} seconds'
        # print('')
        # print(message)
        # print('')
        # client.set_temperature(setpoint,
        #                        tempRate,
        #                        client.temperature.approach_mode.fast_settle) #fast_settle/no_overshoot
        # #for t in range(points):
        # save_temp_field_chamber()
        # #time.sleep(wait)
        # client.wait_for(wait, 0, client.temperature.waitfor)
        # save_temp_field_chamber()

        # ----------------------------------------------------------------------------------#
        # -------------------------------- Main Field Loop ---------------------------------#
        # currentField = 0
        # MaxField = 2000 #Oe
        # i = 0

        rm = visa.ResourceManager()
        keithley_2182A_NV = rm.open_resource("GPIB1::7::INSTR", timeout=10000)
        print(f'\n Waiting for {zeroField} Oe Field \n')
        time.sleep(10)
        # client.wait_for(30,
        #                 timeout_sec=100,
        #                 bitmask=client.field.waitfor)
        # save_temp_field_chamber()

        # ----------------- Loop Down ----------------------#
        Curlen = len(current)
        templen = len(TempList)

        for i in range(templen):
            # number_of_temp = number_of_temp - 1
            print(f'\n Loop is at {TempList[i]} K Temperature\n')
            Tempsetpoint = TempList[i]
            self.client.set_temperature(Tempsetpoint,
                                   tempRate,
                                   client.temperature.approach_mode.fast_settle)  # fast_settle/no_overshoot
            print(f'Waiting for {Tempsetpoint} K Temperature')
            time.sleep(4)

            MyTemp, sT = client.get_temperature()
            while True:
                time.sleep(1)
                MyTemp, sT = client.get_temperature()
                print(f'Status: {sT}')
                if sT == 'Stable':
                    break

            for j in range(Curlen):
                # number_of_current = number_of_current - 1

                client.set_field(topField,
                                 fieldRate,
                                 client.field.approach_mode.linear,  # linear/oscillate
                                 client.field.driven_mode.driven)
                print(f'\n Waiting for {zeroField} Oe Field \n')
                time.sleep(10)
                while True:
                    time.sleep(15)
                    F, sF = client.get_field()
                    print(f'Status: {sF}')
                    if sF == 'Holding (driven)':
                        break

                client.set_field(zeroField,
                                 fieldRate,
                                 client.field.approach_mode.oscillate,  # linear/oscillate
                                 client.field.driven_mode.driven)
                print(f'\n Waiting for {zeroField} Oe Field \n')
                time.sleep(10)
                while True:
                    time.sleep(15)
                    F, sF = client.get_field()
                    print(f'Status: {sF}')
                    if sF == 'Holding (driven)':
                        break

                current_in_uA = round(float(current[j]) / 1e-6, 1)
                current_in_mA = round(float(current[j]) / 1e-3, 1)
                keithley_6221_Curr_Src.write(":OUTP OFF")  # Set source function to current
                keithley_6221_Curr_Src.write("CURRent:RANGe:AUTO ON \n")
                keithley_6221_Curr_Src.write(f'CURR {current[j]} \n')
                # keithley_6221_Curr_Src.write(":SOUR:CURR:LEV {current}")  # Set current level to 20 µA
                # keithley_6221_Curr_Src.write(f':SOUR:CURR:LEV {current}')  # Set current level to 20 µA
                keithley_6221_Curr_Src.write(":OUTP ON")  # Turn on the output
                print(f'DC current is set to: {current_in_uA} mA')
                csv_filename = f"061524_THE_Fe_WSe2_0607-02_03_ETO_Rxy_Rxx_{current_in_uA}_uA_{TempList[i]}_K_Room_temp_Temp_Dep_Run_5.csv"
                # csv_filename = f"053024_TTU_MOS2_ThinFilm_5nm_ETO_Rxy_{current_in_uA}_uA_{CurTemp}_K_Run_Test.csv"
                pts = 0
                currentField = topField
                number_of_field_update = number_of_field
                while currentField >= botField:
                    single_measurement_start = time.time()
                    print(f'\n Loop is at {currentField} Oe Field Up \n')
                    Fieldsetpoint = currentField
                    print(f'\n Set the field to {Fieldsetpoint} Oe and then collect data \n')
                    client.set_field(Fieldsetpoint,
                                     fieldRate,
                                     client.field.approach_mode.linear,
                                     client.field.driven_mode.driven)
                    print(f'\n Waiting for {Fieldsetpoint} Oe Field \n')
                    time.sleep(4)
                    MyField, sF = client.get_field()
                    while True:
                        time.sleep(1)
                        MyField, sF = client.get_field()
                        print(f'Status: {sF}')
                        if sF == 'Holding (driven)':
                            break

                    MyField, sF = client.get_field()
                    # ----------------------------- Measure NV voltage -------------------
                    print(f'\n Saving data for {MyField} Oe \n')
                    import NV_Read_Function

                    NV_Read_Function.NV_Read(keithley_2182A_NV, MyField, CurTemp, csv_filename,
                                             float(current[j]))

                    # ----------------------------- Measure NV voltage -------------------
                    deltaH = deltaH_chk(deltaH_small, deltaH_med, deltaH_large, currentField)

                    print(f'deltaH = {deltaH}')
                    # Update currentField for the next iteration
                    currentField -= deltaH
                    pts += 1  # Number of pts count
                    single_measurement_end = time.time()
                    Single_loop = single_measurement_end - single_measurement_start
                    number_of_field_update = number_of_field_update - 1
                    print('Estimated Single Field measurement (in secs):  {} s \n'.format(Single_loop))
                    print('Estimated Single measurement (in hrs):  {} s \n'.format(
                        Single_loop * number_of_field / 60 / 60))
                    total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                                number_of_temp - i)
                    totoal_time_in_minutes = total_time_in_seconds / 60
                    total_time_in_hours = totoal_time_in_minutes / 60
                    total_time_in_days = total_time_in_hours / 24
                    print('Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                        total_time_in_seconds))
                    print(
                        'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                            totoal_time_in_minutes))
                    print('Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                        total_time_in_hours))
                    print(
                        'Estimated Remaining Time for this round of measurement (in mins):  {} days \n'.format(
                            total_time_in_days))

                # ----------------- Loop Up ----------------------#
                currentField = botField
                while currentField <= topField:
                    single_measurement_start = time.time()
                    print(f'\n Loop is at {currentField} Oe Field Up \n')
                    Fieldsetpoint = currentField

                    print(f'\n Set the field to {Fieldsetpoint} Oe and then collect data \n')
                    client.set_field(Fieldsetpoint,
                                     fieldRate,
                                     client.field.approach_mode.linear,
                                     client.field.driven_mode.driven)

                    print(f'\n Waiting for {Fieldsetpoint} Oe Field \n')
                    time.sleep(4)

                    MyField, sF = client.get_field()
                    while True:
                        time.sleep(1)
                        MyField, sF = client.get_field()
                        print(f'Status: {sF}')
                        if sF == 'Holding (driven)':
                            break

                    MyField, sF = client.get_field()

                    # ----------------------------- Measure NV voltage -------------------
                    print(f'Saving data for  {MyField} Oe')
                    import NV_Read_Function

                    NV_Read_Function.NV_Read(keithley_2182A_NV, MyField, CurTemp, csv_filename,
                                             float(current[j]))

                    # ----------------------------- Measure NV voltage -------------------
                    deltaH = deltaH_chk(deltaH_small, deltaH_med, deltaH_large, currentField)

                    print(f'deltaH = {deltaH}')
                    # Update currentField for the next iteration
                    currentField += deltaH
                    pts += 1  # Number of pts count
                    single_measurement_end = time.time()
                    Single_loop = single_measurement_end - single_measurement_start
                    number_of_field_update = number_of_field_update - 1
                    total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                                number_of_temp - i)
                    totoal_time_in_minutes = total_time_in_seconds / 60
                    total_time_in_hours = totoal_time_in_minutes / 60
                    total_time_in_days = total_time_in_hours / 24
                    print('Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                        total_time_in_seconds))
                    print(
                        'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                            totoal_time_in_minutes))
                    print('Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                        total_time_in_hours))
                    print(
                        'Estimated Remaining Time for this round of measurement (in mins):  {} days \n'.format(
                            total_time_in_days))

        client.set_field(zeroField,
                         fieldRate,
                         client.field.approach_mode.oscillate,  # linear/oscillate
                         client.field.driven_mode.driven)
        print('Waiting for Zero Field')

        client.set_temperature(CurTemp,
                               tempRate,
                               client.temperature.approach_mode.fast_settle)  # fast_settle/no_overshoot
        print(f'Waiting for {CurTemp} K Temperature')
        time.sleep(4)
        # client.wait_for(10,
        #                 100,
        #                 client.field.waitfor)

        temperature, status = client.get_temperature()
        print(f'Temperature = {temperature} {tempUnits}')

        field, status = client.get_field()
        fieldUnits = client.field.units
        print(f'Field = {field} {fieldUnits}')

        keithley_6221_Curr_Src.write(":SOR:CURR:LEV 0")  # Set current level to zero
        keithley_6221_Curr_Src.write(":OUTP OFF")  # Turn off the output
        print("DC current is set to: 0.00 A")
        keithley_6221_Curr_Src.close()

        # Calculate the total runtime
        end_time = time.time()
        total_runtime = (end_time - start_time) / 3600
        print(f"Total runtime: {total_runtime} hours")
        print(f'Total data points: {pts} pts')

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     main_window = Measurement()
#     main_window.show()
#     sys.exit(app.exec())
