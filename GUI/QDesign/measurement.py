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
        self.preset_container.setFixedSize(400, 180)

        self.preset_container_layout = QHBoxLayout()
        self.preset_container_layout.addWidget(self.Preset_group_box, 1)
        self.preset_container.setLayout(self.preset_container_layout)

        self.instrument_connection_layout = QHBoxLayout()
        self.instrument_connection_layout.addWidget(self.preset_container)
        self.Instruments_Content_Layout = QVBoxLayout()
        self.main_layout.addWidget(self.current_intrument_label, alignment=Qt.AlignmentFlag.AlignTop)
        self.main_layout.addLayout(self.instrument_connection_layout)
        self.main_layout.addLayout(self.Instruments_Content_Layout)

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
                # self.ppms_container.setParent(None)


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
            self.ppms_container.setFixedSize(400, 180)
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
            if self.ETO_radio_buttom.isChecked():
                self.Instruments_combo.addItems(["Select Instruments"])  # 0
                self.Instruments_combo.addItems(["Keithley 2182 nv"])  # 1
                self.Instruments_combo.addItems(["Keithley 6221"])  # 2
                self.Instruments_combo.addItems(["DSP 7265 Lock-in"])  # 4
            elif self.FMR_radio_buttom.isChecked():
                self.Instruments_combo.addItems(["BNC 845 RF"])  # 3
                self.Instruments_combo.addItems(["DSP 7265 Lock-in"])  # 4
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
            self.instrument_container.setFixedSize(400, 180)
            self.instrument_container.setLayout(self.instrument_main_layout)
            self.instrument_connection_layout.addWidget(self.instrument_container)


            # --------------------------------------- Part PPMS_layout Init ----------------------------
            self.PPMS_measurement_setup_layout = QHBoxLayout()
            self.Instruments_Content_Layout.addLayout(self.PPMS_measurement_setup_layout)

            # --------------------------------------- Part PPMS_layout Init ----------------------------
            self.Instruments_measurement_setup_layout = QHBoxLayout()
            self.Instruments_Content_Layout.addLayout(self.Instruments_measurement_setup_layout)

            self.main_layout.addLayout(self.Instruments_Content_Layout)
            # --------------------------------------- Part PPMS_layout Init ----------------------------
            self.graphing_layout = QHBoxLayout()
            #
            # self.plotting_x_axis_group_box = QGroupBox("x Axis Selection")
            # self.plotting_x_axis_select_layout = QVBoxLayout()
            # self.checkbox1 = QCheckBox("Channel 1")
            # self.checkbox1.setFont(self.font)
            # self.checkbox2 = QCheckBox("Channel 2")
            # self.checkbox2.setFont(self.font)
            # self.plotting_x_axis_select_layout.addWidget(self.checkbox1)
            # self.plotting_x_axis_select_layout.addWidget(self.checkbox2)
            # self.plotting_x_axis_group_box.setLayout(self.plotting_x_axis_select_layout)
            # self.graphing_layout.addWidget(self.plotting_x_axis_group_box)
            #
            # self.plotting_y_axis_group_box = QGroupBox("y Axis Selection")
            # self.plotting_y_axis_select_layout = QVBoxLayout()
            # self.checkbox1 = QCheckBox("Channel 1")
            # self.checkbox1.setFont(self.font)
            # self.checkbox2 = QCheckBox("Channel 2")
            # self.checkbox2.setFont(self.font)
            # self.plotting_y_axis_select_layout.addWidget(self.checkbox1)
            # self.plotting_y_axis_select_layout.addWidget(self.checkbox2)
            # self.plotting_y_axis_group_box.setLayout(self.plotting_y_axis_select_layout)
            # self.graphing_layout.addWidget(self.plotting_y_axis_group_box)


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
            self.buttons_layout = QHBoxLayout()
            self.start_measurement_btn = QPushButton('Start')
            # self.start_measurement_btn.clicked.connect(self.plot_selection)
            self.stop_btn = QPushButton('Stop')
            # self.stop_btn.clicked.connect(self.stop)
            self.rst_btn = QPushButton('Reset')
            # self.rst_btn.clicked.connect(self.rst)
            self.start_measurement_btn.setStyleSheet(self.Button_stylesheet)
            self.stop_btn.setStyleSheet(self.Button_stylesheet)
            self.rst_btn.setStyleSheet(self.Button_stylesheet)
            self.buttons_layout.addStretch(4)
            self.buttons_layout.addWidget(self.rst_btn)
            self.buttons_layout.addWidget(self.stop_btn)
            self.buttons_layout.addWidget(self.start_measurement_btn)

            self.figure_container_layout.addWidget(figure_group_box)
            self.figure_container.setLayout(self.figure_container_layout)
            self.graphing_layout.addWidget(self.figure_container)
            self.main_layout.addLayout(self.graphing_layout)
            self.main_layout.addLayout(self.buttons_layout)
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

    def refresh_Connection_List(self):
        # Access GPIB ports using PyVISA
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
        # Clear existing items and add new ones
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

    def clear_widget(self, widget):
        if widget is not None:
            while widget.count():
                child = widget.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                if child.layout() is not None:
                    self.clear_widget(child.layout())

    def start_server(self):
        if self.server_btn_clicked == False:
            # import Data_Processing_Suite.GUI.QDesign.run_server as s
            try:
                self.server = mpv.Server()
            except MultiPyVuError:
                QMessageBox.critical('Check MutltiVu', 'Run MultiVu without Admin or open MultiVu correctly!')
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
            self.ppms_temp_radio_buttom_layout = QHBoxLayout()
            self.ppms_zone_temp_layout = QVBoxLayout()
            self.Temp_setup_Zone_1 = False
            self.Temp_setup_Zone_2 = False
            self.Temp_setup_Zone_3 = False
            self.ppms_temp_One_zone_radio = QRadioButton("1 Zone")
            self.ppms_temp_One_zone_radio.toggled.connect(self.temp_zone_selection)
            self.ppms_temp_Two_zone_radio = QRadioButton("2 Zones")
            self.ppms_temp_Two_zone_radio.toggled.connect(self.temp_zone_selection)
            self.ppms_temp_Three_zone_radio = QRadioButton("3 Zones")
            self.ppms_temp_Three_zone_radio.toggled.connect(self.temp_zone_selection)
            self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_One_zone_radio)
            self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_Two_zone_radio)
            self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_Three_zone_radio)
            self.ppms_temp_setting_layout.addLayout(self.ppms_temp_radio_buttom_layout)
            self.ppms_temp_setting_layout.addLayout(self.ppms_zone_temp_layout)
            self.ppms_Temp_group_box.setLayout(self.ppms_temp_setting_layout)
      
            # --------------------------------------- Part PPMS Field Setup ----------------------------
            self.ppms_field_setting_layout = QVBoxLayout()
            self.ppms_field_radio_buttom_layout = QHBoxLayout()
            self.ppms_zone_field_layout = QVBoxLayout()

            self.Field_setup_Zone_1 = False
            self.Field_setup_Zone_2 = False
            self.Field_setup_Zone_3 = False
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
                # self.instru_connect_btn.clicked.connect(self.close_keithley_2182)
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
                # self.instru_connect_btn.clicked.connect(self.close_keithley_6221)
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
            # self.Instruments_measurement_setup_layout.removeItem(self.keithley_2182_contain_layout)
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
        self.keithley_2182_groupbox.setFixedSize(380,150)
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
        self.keithley_6221_groupbox.setFixedSize(600, 150)
        self.keithley_6221_contain_layout = QHBoxLayout()
        self.keithley_6221_contain_layout.addWidget(self.keithley_6221_groupbox)
        self.Instruments_measurement_setup_layout.addLayout(self.keithley_6221_contain_layout)

    def Keithley_6221_DC(self):
        try:
            self.clear_layout(self.Keithey_curSour_layout)
        except Exception as e:
            print(e)
        self.keithley_6221_DC_range_single_layout= QVBoxLayout()
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
        self.keithley_6221_DC_range_combobox.addItems(["Select Units"])  # 0
        self.keithley_6221_DC_range_combobox.addItems(["mA"])  # 1
        self.keithley_6221_DC_range_combobox.addItems(["µA"])  # 2
        self.keithley_6221_DC_range_combobox.addItems(["nA"])  # 3
        self.keithley_6221_DC_range_combobox.addItems(["pA"])  # 3
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
        self.keithley_6221_DC_single_combobox.addItems(["Select Units"])  # 0
        self.keithley_6221_DC_single_combobox.addItems(["mA"])  # 1
        self.keithley_6221_DC_single_combobox.addItems(["µA"])  # 2
        self.keithley_6221_DC_single_combobox.addItems(["nA"])  # 3
        self.keithley_6221_DC_single_combobox.addItems(["pA"])  # 4
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
            self.Field_setup_Zone_2 = True
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
        self.ppms_zone1_field_step_layout.addWidget(self.ppms_zone1_field_step_label)
        self.ppms_zone1_field_step_layout.addWidget(self.ppms_zone1_field_step_entry)


        self.ppms_zone1_field_layout.addLayout(self.ppms_zone1_field_range_layout)
        self.ppms_zone1_field_layout.addLayout(self.ppms_zone1_field_step_layout)
        self.clear_layout(self.ppms_zone_field_layout)
        self.ppms_zone_field_layout.addLayout(self.ppms_zone1_field_layout)
        # self.ppms_zone_field_layout.addLayout(self.ppms_zone1_field_step_layout)

    def field_two_zone(self):
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
        self.ppms_zone2_field_step_label = QLabel('Step Size 2 (Oe): ')
        self.ppms_zone2_field_step_label.setFont(self.font)
        self.ppms_zone2_field_step_entry = QLineEdit()
        self.ppms_zone2_field_step_entry.setFont(self.font)
        self.ppms_zone2_field_step_layout.addWidget(self.ppms_zone2_field_step_label)
        self.ppms_zone2_field_step_layout.addWidget(self.ppms_zone2_field_step_entry)


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
        self.ppms_zone3_field_step_layout.addWidget(self.ppms_zone3_field_step_label)
        self.ppms_zone3_field_step_layout.addWidget(self.ppms_zone3_field_step_entry)

        self.ppms_zone3_field_layout.addLayout(self.ppms_zone3_field_range_layout)
        self.ppms_zone3_field_layout.addLayout(self.ppms_zone3_field_step_layout)

        self.ppms_zone_field_layout.addLayout(self.ppms_zone3_field_layout)

    def temp_zone_selection(self):
        if self.ppms_temp_One_zone_radio.isChecked() and self.Temp_setup_Zone_1 == False:
            self.ppms_temp_One_zone_radio.setChecked(False)
            self.Temp_setup_Zone_1 = True
            self.Temp_setup_Zone_2 = False
            self.Temp_setup_Zone_3 = False
            self.temp_one_zone()
            self.ppms_temp_One_zone_radio.setChecked(False)
        elif self.ppms_temp_Two_zone_radio.isChecked() and self.Temp_setup_Zone_2 == False:
            self.ppms_temp_Two_zone_radio.setChecked(False)
            self.Temp_setup_Zone_1 = False
            self.Temp_setup_Zone_2 = True
            self.Temp_setup_Zone_3 = False
            self.Temp_setup_Zone_2 = True
            self.temp_two_zone()
            self.ppms_temp_Two_zone_radio.setChecked(False)
        elif self.ppms_temp_Three_zone_radio.isChecked() and self.Temp_setup_Zone_3 == False:
            self.ppms_temp_Three_zone_radio.setChecked(False)
            self.Temp_setup_Zone_1 = False
            self.Temp_setup_Zone_2 = False
            self.Temp_setup_Zone_3 = True

            self.temp_three_zone()
            self.ppms_temp_Three_zone_radio.setChecked(False)

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
        self.ppms_zone1_temp_step_layout.addWidget(self.ppms_zone1_temp_step_label)
        self.ppms_zone1_temp_step_layout.addWidget(self.ppms_zone1_temp_step_entry)

        self.ppms_zone1_temp_layout.addLayout(self.ppms_zone1_temp_range_layout)
        self.ppms_zone1_temp_layout.addLayout(self.ppms_zone1_temp_step_layout)
        self.clear_layout(self.ppms_zone_temp_layout)
        self.ppms_zone_temp_layout.addLayout(self.ppms_zone1_temp_layout)
        # self.ppms_zone_temp_layout.addLayout(self.ppms_zone1_temp_step_layout)

    def temp_two_zone(self):
        self.temp_one_zone()
        self.ppms_zone2_temp_layout = QVBoxLayout()
        # self.ppms_zone3_temp_layout = QVBoxLayout()
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
        self.ppms_zone2_temp_step_layout.addWidget(self.ppms_zone2_temp_step_label)
        self.ppms_zone2_temp_step_layout.addWidget(self.ppms_zone2_temp_step_entry)

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
        self.ppms_zone3_temp_step_layout.addWidget(self.ppms_zone3_temp_step_label)
        self.ppms_zone3_temp_step_layout.addWidget(self.ppms_zone3_temp_step_entry)

        self.ppms_zone3_temp_layout.addLayout(self.ppms_zone3_temp_range_layout)
        self.ppms_zone3_temp_layout.addLayout(self.ppms_zone3_temp_step_layout)

        self.ppms_zone_temp_layout.addLayout(self.ppms_zone3_temp_layout)
    
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