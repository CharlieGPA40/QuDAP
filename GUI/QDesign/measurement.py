from PyQt6.QtWidgets import (
    QSizePolicy, QWidget, QMessageBox, QGroupBox, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
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
    def __init__(self, parent=None, width=100, height=4, dpi=300):
        fig = Figure(figsize=(width, height), dpi=dpi)
        # self.canvas = FigureCanvas(self.figure)
        # self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # self.canvas.updateGeometry()

        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class Measurement(QWidget):
    def __init__(self):
        super().__init__()
        try:
            self.isConnect = False
            self.init_ui()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

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
        self.current_intrument_label = QLabel("Start Measurement")
        self.current_intrument_label.setFont(titlefont)
        self.current_intrument_label.setStyleSheet("""
                                                    QLabel{
                                                        background-color: white;
                                                        }
                                                        """)

        #  ---------------------------- PART 2 --------------------------------
        with (open("GUI/QSS/QButtonWidget.qss", "r") as file):
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
        self.radio_btn_layout = QHBoxLayout(self)
        self.radio_btn_layout.addStretch(2)
        self.radio_btn_layout.addWidget(self.ETO_radio_buttom)
        self.radio_btn_layout.addStretch(1)
        self.radio_btn_layout.addWidget(self.FMR_radio_buttom)
        self.radio_btn_layout.addStretch(2)

        self.select_preset_btn_layout = QHBoxLayout(self)
        self.select_preset_btn_layout.addWidget(self.reset_preset_buttom)
        self.select_preset_btn_layout.addWidget(self.select_preset_buttom)

        self.preset_layout.addLayout(self.radio_btn_layout)
        self.preset_layout.addLayout(self.select_preset_btn_layout)
        self.Preset_group_box.setLayout(self.preset_layout)

        self.preset_container = QWidget(self)
        self.preset_container.setFixedSize(400, 200)

        self.preset_container_layout = QHBoxLayout()
        self.preset_container_layout.addWidget(self.Preset_group_box, 1)
        self.preset_container.setLayout(self.preset_container_layout)

        self.instrument_connection_layout = QHBoxLayout()
        self.instrument_connection_layout.addWidget(self.preset_container)

        self.ETO_instru_content_layout = QVBoxLayout()
        self.main_layout.addWidget(self.current_intrument_label, alignment=Qt.AlignmentFlag.AlignTop)
        self.main_layout.addLayout(self.instrument_connection_layout)
        self.main_layout.addLayout(self.ETO_instru_content_layout)

    def preset_reset(self):
        try:
                self.clear_Layout(self.ETO_instru_content_layout)
                self.main_layout.removeItem(self.ETO_instru_content_layout)
                self.clear_Layout(self.ppms_zone_field_layout)
                self.main_layout.removeItem(self.ppms_zone_field_layout)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def preset_select(self):
        try:
            if self.ETO_radio_buttom.isChecked():
                # self.FMR_radio_buttom.setChecked(False)
                self.ETO_Preset()

            if self.FMR_radio_buttom.isChecked():
                # self.ETO_radio_buttom.setChecked(False)
                return
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def ETO_Preset(self):
        with open("GUI/QSS/QComboWidget.qss", "r") as file:
            self.QCombo_stylesheet = file.read()
        #--------------------------------------- Part connection ----------------------------
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
        self.ppms_container.setFixedSize(400, 200)
        self.ppms_container.setLayout(self.ppms_main_layout)

        self.instrument_connection_layout.addWidget(self.ppms_container)

        # self.preseted_content.addLayout(ppms_connection)
        # --------------------------------------- Part connection_otherGPIB ----------------------------
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
        self.Instruments_combo.addItems(["Select Instruments"])  # 0
        self.Instruments_combo.addItems(["Keithley 2182 nv"])  # 1
        self.Instruments_combo.addItems(["Keithley 6221"])  # 2
        self.Instruments_combo.addItems(["RF"])  # 3
        self.Instruments_combo.addItems(["Locked_in"])  # 4

        self.Instruments_port_label = QLabel("Channel:")
        self.Instruments_port_label.setFont(self.font)
        self.gpib_combo = QComboBox()
        self.gpib_combo.setStyleSheet(self.QCombo_stylesheet)
        self.gpib_combo.setFont(self.font)
        self.refresh_gpib_list()
        self.refresh_btn = QPushButton(icon=QIcon("GUI/Icon/refresh.svg"))
        self.refresh_btn.clicked.connect(self.refresh_gpib_list)
        self.instru_connect_btn = QPushButton('Connect')
        self.instru_connect_btn.clicked.connect(self.connect_current_gpib)
        self.instru_select_layout.addWidget(self.Instruments_sel_label, 1)
        self.instru_select_layout.addWidget(self.Instruments_combo, 2)

        self.instru_connection_layout.addWidget(self.Instruments_port_label, 1)
        self.instru_connection_layout.addWidget(self.gpib_combo, 3)

        self.instru_cnt_btn_layout.addWidget(self.refresh_btn, 2)
        self.instru_cnt_btn_layout.addWidget(self.instru_connect_btn, 2)
        self.Instru_main_layout.addLayout(self.instru_select_layout)
        self.Instru_main_layout.addLayout(self.instru_connection_layout)
        self.Instru_main_layout.addLayout(self.instru_cnt_btn_layout)
        self.instrument_connection_group_box.setLayout(self.Instru_main_layout)
        self.instrument_main_layout.addWidget(self.instrument_connection_group_box)
        self.instrument_container.setFixedSize(400, 200)
        self.instrument_container.setLayout(self.instrument_main_layout)
        self.instrument_connection_layout.addWidget(self.instrument_container)


        # --------------------------------------- Part PPMS_layout Init ----------------------------
        self.PPMS_measurement_setup_layout = QHBoxLayout()
        self.ETO_instru_content_layout.addLayout(self.PPMS_measurement_setup_layout)

        # --------------------------------------- Part PPMS_layout Init ----------------------------
        self.Instruments_measurement_setup_layout = QHBoxLayout()
        self.ETO_instru_content_layout.addLayout(self.Instruments_measurement_setup_layout)

        self.main_layout.addLayout(self.ETO_instru_content_layout)
        # --------------------------------------- Part PPMS_layout Init ----------------------------
        # graphing_layout = QHBoxLayout()
        # selection_Layout = QHBoxLayout()
        # plotting_x_axis_group_box = QGroupBox("x Axis Selection")
        # plotting_y_axis_group_box = QGroupBox("x Axis Selection")
        # # self.checkbox1 = QCheckBox("Channel 1")
        # # self.checkbox1.setFont(self.font)
        # # self.checkbox2 = QCheckBox("Channel 2")
        # # self.checkbox2.setFont(self.font)
        #
        # plot_btn = QPushButton('Plot')
        # plot_btn.clicked.connect(self.plot_selection)
        # stop_btn = QPushButton('Stop')
        # stop_btn.clicked.connect(self.stop)
        # rst_btn = QPushButton('Reset')
        # rst_btn.clicked.connect(self.rst)
        # selection_Layout.addWidget(plot_btn)
        # selection_Layout.addWidget(stop_btn)
        # selection_Layout.addWidget(rst_btn)
        #
        # # Arrange radio buttons horizontally
        # radio_layout = QVBoxLayout()
        # radio_layout.addWidget(self.checkbox1)
        # radio_layout.addWidget(self.checkbox2)
        # radio_layout.addLayout(selection_Layout)
        # plotting_control_group_box.setLayout(radio_layout)

        # #  ---------------------------- Figure Layout --------------------------------
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
        self.figure_container_layout = QHBoxLayout()
        self.figure_container = QWidget(self)
        # self.figure_container.setFixedSize(1180, 400)
        self.figure_container_layout.addWidget(figure_group_box)
        self.figure_container.setLayout(self.figure_container_layout)
        self.main_layout.addWidget(self.figure_container)
        # graphing_layout.addWidget(plotting_control_group_box)
        # graphing_layout.addWidget(figure_group_box)
        # #  ---------------------------- Main Layout --------------------------------
        self.setLayout(self.main_layout)

        #  ---------------------------- Style Sheet --------------------------------
        self.select_preset_buttom.setStyleSheet(self.Button_stylesheet)

        self.instru_connect_btn.setStyleSheet(self.Button_stylesheet)

        self.refresh_btn.setStyleSheet(self.Button_stylesheet)
        self.server_btn.setStyleSheet(self.Button_stylesheet)
        self.connect_btn.setStyleSheet(self.Button_stylesheet)

    def refresh_gpib_list(self):
        # Access GPIB ports using PyVISA
        rm = visa.ResourceManager('@sim')
        instruments = rm.list_resources()
        self.gpib_ports = [instr for instr in instruments if 'GPIB' in instr]
        # Clear existing items and add new ones
        self.gpib_combo.clear()
        self.gpib_combo.addItems(["None"])
        self.gpib_combo.addItems(self.gpib_ports)

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
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                if child.layout() is not None:
                    self.clear_layout(child.layout())

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
            self.ppms_temp_list_label_init = QLabel('Set Temperature (K): [')
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
            self.ppms_zone_field_layout = QVBoxLayout()

            self.enter_Zone_1 = False
            self.enter_Zone_2 = False
            self.enter_Zone_3 = False
            self.ppms_field_One_zone_radio = QRadioButton("1 Zone")
            self.ppms_field_One_zone_radio.toggled.connect(self.field_zone_selection)
            self.ppms_field_Two_zone_radio = QRadioButton("2 Zones")
            self.ppms_field_Two_zone_radio.toggled.connect(self.field_zone_selection)
            self.ppms_field_Three_zone_radio = QRadioButton("3 Zones")
            self.ppms_field_Three_zone_radio.toggled.connect(self.field_zone_selection)
            self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_One_zone_radio)
            self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_Two_zone_radio)
            self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_Three_zone_radio)
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

    def field_zone_selection(self):
        # self.clear_layout(self.ppms_zone_field_layout)

        # self.clear_layout(self.ppms_zone_field_layout)

        if self.ppms_field_One_zone_radio.isChecked() and self.enter_Zone_1 == False:
            self.ppms_field_One_zone_radio.setChecked(False)
            self.enter_Zone_1 = True
            self.enter_Zone_2 = False
            self.enter_Zone_3 = False
            self.field_one_zone()
            self.ppms_field_One_zone_radio.setChecked(False)
        elif self.ppms_field_Two_zone_radio.isChecked() and self.enter_Zone_2 == False:
            self.ppms_field_Two_zone_radio.setChecked(False)
            self.enter_Zone_1 = False
            self.enter_Zone_2 = True
            self.enter_Zone_3 = False
            self.field_two_zone()
            self.ppms_field_Two_zone_radio.setChecked(False)
        elif self.ppms_field_Three_zone_radio.isChecked() and self.enter_Zone_3 == False:
            self.ppms_field_Three_zone_radio.setChecked(False)
            self.enter_Zone_1 = False
            self.enter_Zone_2 = False
            self.enter_Zone_3 = True
            self.field_three_zone()
            self.ppms_field_Three_zone_radio.setChecked(False)
    def field_one_zone(self):
        self.clear_layout(self.ppms_zone_field_layout)
        # self.clear_layout(self.ppms_zone2_field_layout)
        # self.clear_layout(self.ppms_zone3_field_layout)
        self.ppms_zone1_field_layout = QVBoxLayout()
        # self.ppms_zone2_field_layout = QVBoxLayout()
        # self.ppms_zone3_field_layout = QVBoxLayout()
        # self.clear_layout(self.ppms_zone1_field_layout)
        # self.clear_layout(self.ppms_zone2_field_layout)
        # self.clear_layout(self.ppms_zone3_field_layout)
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
        self.ppms_zone1_feild_step_label = QLabel('Step Size (Oe): ')
        self.ppms_zone1_feild_step_label.setFont(self.font)
        self.ppms_zone1_feild_step_entry = QLineEdit()
        self.ppms_zone1_feild_step_entry.setFont(self.font)
        self.ppms_zone1_field_step_layout.addWidget(self.ppms_zone1_feild_step_label)
        self.ppms_zone1_field_step_layout.addWidget(self.ppms_zone1_feild_step_entry)


        self.ppms_zone1_field_layout.addLayout(self.ppms_zone1_field_range_layout)
        self.ppms_zone1_field_layout.addLayout(self.ppms_zone1_field_step_layout)
        self.clear_layout(self.ppms_zone_field_layout)
        self.ppms_zone_field_layout.addLayout(self.ppms_zone1_field_layout)
        # self.ppms_zone_field_layout.addLayout(self.ppms_zone1_field_step_layout)



    def field_two_zone(self):
        self.clear_layout(self.ppms_zone_field_layout)
        # self.clear_layout(self.ppms_zone1_field_layout)
        # self.clear_layout(self.ppms_zone3_field_layout)
        self.field_one_zone()
        self.ppms_zone2_field_layout = QVBoxLayout()
        # self.ppms_zone3_field_layout = QVBoxLayout()
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
        self.ppms_zone2_feild_step_label = QLabel('Step Size 2 (Oe): ')
        self.ppms_zone2_feild_step_label.setFont(self.font)
        self.ppms_zone2_feild_step_entry = QLineEdit()
        self.ppms_zone2_feild_step_entry.setFont(self.font)
        self.ppms_zone2_field_step_layout.addWidget(self.ppms_zone2_feild_step_label)
        self.ppms_zone2_field_step_layout.addWidget(self.ppms_zone2_feild_step_entry)


        self.ppms_zone2_field_layout.addLayout(self.ppms_zone2_field_range_layout)
        self.ppms_zone2_field_layout.addLayout(self.ppms_zone2_field_step_layout)
        self.ppms_zone_field_layout.addLayout(self.ppms_zone2_field_layout)
        # self.ppms_zone_field_layout.addLayout(self.ppms_zone2_field_step_layout)

    def field_three_zone(self):
        self.clear_layout(self.ppms_zone_field_layout)
        # self.clear_layout(self.ppms_zone1_field_layout)
        # self.clear_layout(self.ppms_zone2_field_layout)
        # self.clear_layout(self.ppms_zone3_field_layout)
        self.field_two_zone()
        # self.ppms_zone1_field_layout = QVBoxLayout()
        # self.ppms_zone2_field_layout = QVBoxLayout()
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
        self.ppms_zone3_feild_step_label = QLabel('Step Size 3 (Oe): ')
        self.ppms_zone3_feild_step_label.setFont(self.font)
        self.ppms_zone3_feild_step_entry = QLineEdit()
        self.ppms_zone3_feild_step_entry.setFont(self.font)
        self.ppms_zone3_field_step_layout.addWidget(self.ppms_zone3_feild_step_label)
        self.ppms_zone3_field_step_layout.addWidget(self.ppms_zone3_feild_step_entry)

        self.ppms_zone3_field_layout.addLayout(self.ppms_zone3_field_range_layout)
        self.ppms_zone3_field_layout.addLayout(self.ppms_zone3_field_step_layout)

        self.ppms_zone_field_layout.addLayout(self.ppms_zone3_field_layout)


    def update_plot(self):
        # self.canvas.axes.cla()  # Clear the canvas.
        if self.isCheckedBox1 == True:
            self.isPlotting = True
            self.channel1_Volt_Array.append(self.Chan_1_voltage)
            # # Drop off the first y element, append a new one.
            self.canvas.axes.plot(self.counter_array, self.channel1_Volt_Array, 'black')
            self.canvas.draw()
        if self.isCheckedBox2 == True:
            self.isPlotting = True
            self.channel2_Volt_Array.append(self.Chan_2_voltage)
            # # Drop off the first y element, append a new one.
            self.canvas.axes.plot(self.counter_array, self.channel2_Volt_Array, 'r')
            self.canvas.draw()
        self.counter += 1
        self.counter_array.append(self.counter)

    def stop(self):
        self.timer.stop()

    def rst(self):
        # This method updates the label based on the checkbox states
        self.timer = QTimer()
        self.timer.stop()
        self.canvas.axes.cla()
        self.canvas.draw()


# if __name__ == "__main__":
#     from PyQt6.QtWidgets import QApplication
#     app = QApplication(sys.argv)
#     main_window = Measurement()
#     main_window.show()
#     sys.exit(app.exec())