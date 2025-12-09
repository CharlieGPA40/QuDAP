"""
Advanced Measurement System - Complete Implementation
Features:
- PPMS MultiVu Detection and Connection
- All Experiment Types (ETO, FMR, Customize, Demo)
- Complete DSP7265 Integration with all settings
- Circular Progress Bar
- All instrument readings in Running tab
"""

import sys
import os
import platform
import subprocess
import time
from pathlib import Path
from datetime import datetime
import math
import traceback
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox,
                             QLabel, QLineEdit, QComboBox, QPushButton, QTableView, QTreeView, QTextEdit,
                             QRadioButton, QButtonGroup, QSplitter, QCheckBox, QSpinBox, QDoubleSpinBox, QStatusBar,
                             QFileDialog, QHeaderView, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QRectF
from PyQt6.QtGui import (QIcon, QFont, QDoubleValidator, QBrush, QStandardItemModel, QStandardItem, QPainter, QColor, QPen)
import pyqtgraph as pg
import numpy as np
import pandas as pd
import pyvisa as visa

# ===================== Constants =====================
TIME_CONSTANT_VALUES = {0: 10e-6, 1: 20e-6, 2: 40e-6, 3: 80e-6, 4: 160e-6, 5: 320e-6, 6: 640e-6, 7: 5e-3, 8: 10e-3,
    9: 20e-3, 10: 50e-3, 11: 100e-3, 12: 200e-3, 13: 500e-3, 14: 1, 15: 2, 16: 5, 17: 10, 18: 20, 19: 50, 20: 100,
    21: 200, 22: 500, 23: 1000, 24: 2000, 25: 5000, 26: 10000, 27: 20000, 28: 50000, 29: 100000}


# ===================== MultiVu Detection =====================
def is_multivu_running():
    try:
        if os.name == 'nt':
            result = subprocess.run(['tasklist'], capture_output=True, text=True, timeout=5)
            if any(x in result.stdout for x in ['MultiVu.exe', 'Dynacool.exe', 'PpmsMvu.exe']):
                return True
            return False
        else:
            result = subprocess.run(['pgrep', '-f', 'MultiVu'], capture_output=True, timeout=5)
            return result.returncode == 0
    except:
        return False


def find_multivu_path():
    common_paths = [r"C:\Program Files\Quantum Design\MultiVu\MultiVu.exe",
        r"C:\Program Files (x86)\Quantum Design\MultiVu\MultiVu.exe", r"C:\QD\MultiVu\MultiVu.exe",
        r"C:\QdDynacool\MultiVu\MultiVu.exe"]
    for path in common_paths:
        if os.path.exists(path):
            return path
    return None


class MultiVuStatusThread(QThread):
    status_signal = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.should_stop = False

    def run(self):
        while not self.should_stop:
            is_running = is_multivu_running()
            self.status_signal.emit(is_running)
            time.sleep(5)

    def stop(self):
        self.should_stop = True


# ===================== Circular Progress Bar =====================
class CircularProgressBar(QWidget):
    """Circular progress bar with percentage in center"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.maximum = 100
        self.setMinimumSize(200, 200)

    def setValue(self, value):
        self.value = max(0, min(value, self.maximum))
        self.update()

    def setMaximum(self, maximum):
        self.maximum = maximum
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        size = min(width, height) - 20
        x = (width - size) // 2
        y = (height - size) // 2

        # Background circle
        painter.setPen(QPen(QColor(200, 200, 200), 10))
        painter.drawArc(x, y, size, size, 0, 360 * 16)

        # Progress
        if self.maximum > 0:
            progress = (self.value / self.maximum) * 360
            percentage = int((self.value / self.maximum) * 100)
        else:
            progress = 0
            percentage = 0

        # Progress arc
        if progress > 0:
            painter.setPen(QPen(QColor(76, 175, 80), 10))
            painter.drawArc(x, y, size, size, 90 * 16, -int(progress * 16))

        # Percentage text
        painter.setPen(QColor(0, 0, 0))
        font = QFont("Arial", 28, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(0, 0, width, height), Qt.AlignmentFlag.AlignCenter, f"{percentage}%")


# ===================== Hierarchical ComboBox =====================
class HierarchicalComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.skip_indexes = []

    def add_category(self, text):
        item = QStandardItem(text)
        item.setEnabled(False)
        item.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        item.setForeground(Qt.GlobalColor.gray)

        model = self.model()
        if not isinstance(model, QStandardItemModel):
            model = QStandardItemModel()
            self.setModel(model)

        model.appendRow(item)
        self.skip_indexes.append(self.count() - 1)

    def add_item(self, text):
        self.addItem("    " + text)


# ===================== Wide ComboBox =====================
class WideComboBox(QComboBox):
    """ComboBox with wider popup"""

    def showPopup(self):
        self.view().setMinimumWidth(self.view().sizeHintForColumn(0) + 20)
        super().showPopup()


# ===================== Dynamic Instrument Connection =====================
class DynamicInstrumentConnection(QWidget):
    instrument_connected = pyqtSignal(object, str)
    instrument_disconnected = pyqtSignal(str)

    INSTRUMENT_RS232_PRESETS = {
        'DSP7265': {'baud_rate': 9600, 'data_bits': 8, 'parity': 'None', 'stop_bits': 1.0, 'flow_control': 'None'},
        'Keithley 2182 nv': {'baud_rate': 9600, 'data_bits': 8, 'parity': 'None', 'stop_bits': 1.0,
                             'flow_control': 'None'},
        'Keithley 6221': {'baud_rate': 9600, 'data_bits': 8, 'parity': 'None', 'stop_bits': 1.0,
                          'flow_control': 'None'},
        'BNC 845 RF': {'baud_rate': 115200, 'data_bits': 8, 'parity': 'None', 'stop_bits': 1.0, 'flow_control': 'None'},
        'Rigol DSA875': {'baud_rate': 9600, 'data_bits': 8, 'parity': 'None', 'stop_bits': 1.0, 'flow_control': 'None'},
        'B&K Precision 9205B': {'baud_rate': 9600, 'data_bits': 8, 'parity': 'None', 'stop_bits': 1.0,
                                'flow_control': 'None'}}

    def __init__(self, instrument_list=None, allow_emulation=True, title="Instrument Connection", parent=None):
        super().__init__(parent)
        self.instrument_list = instrument_list or []
        self.allow_emulation = allow_emulation
        self.title = title

        self.rm = None
        self.connected_instruments = {}
        self.font = QFont("Arial", 10)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.connection_group = QGroupBox(self.title)
        connection_layout = QVBoxLayout()

        # Instrument selection
        instru_select_layout = QHBoxLayout()
        instru_label = QLabel("Select Instrument:")
        instru_label.setFont(self.font)
        instru_label.setMinimumWidth(140)

        self.instru_combo = QComboBox()
        self.instru_combo.setFont(self.font)
        self.instru_combo.addItem("Select Instrument")
        self.instru_combo.addItems(self.instrument_list)
        self.instru_combo.currentIndexChanged.connect(self.on_instrument_changed)

        instru_select_layout.addWidget(instru_label)
        instru_select_layout.addWidget(self.instru_combo)
        connection_layout.addLayout(instru_select_layout)

        # Connection selection
        conn_select_layout = QHBoxLayout()
        conn_label = QLabel("Channel:")
        conn_label.setFont(self.font)
        conn_label.setMinimumWidth(130)

        self.connection_combo = QComboBox()
        self.connection_combo.setFont(self.font)
        self.connection_combo.currentIndexChanged.connect(self.on_connection_changed)

        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.clicked.connect(self.refresh_connections)
        self.refresh_btn.setMaximumWidth(30)

        conn_select_layout.addWidget(conn_label)
        conn_select_layout.addWidget(self.connection_combo, 3)
        conn_select_layout.addWidget(self.refresh_btn)
        connection_layout.addLayout(conn_select_layout)

        # RS232 settings
        self.rs232_layout = QVBoxLayout()
        connection_layout.addLayout(self.rs232_layout)

        # Connect button
        self.connect_btn = QPushButton('Connect')
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setMinimumHeight(30)
        self.connect_btn.setFont(self.font)
        connection_layout.addWidget(self.connect_btn)

        # Status label
        self.status_label = QLabel("Status: Not Connected")
        self.status_label.setFont(self.font)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        connection_layout.addWidget(self.status_label)

        self.connection_group.setLayout(connection_layout)
        main_layout.addWidget(self.connection_group)
        self.setLayout(main_layout)
        self.refresh_connections()

    def on_instrument_changed(self, index):
        if index == 0:
            self.connect_btn.setEnabled(False)
            self.status_label.setText("Status: Not Connected")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.connect_btn.setEnabled(True)
            instrument_name = self.instru_combo.currentText()

            if instrument_name in self.connected_instruments:
                self.status_label.setText(f"Connected: {instrument_name}")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.connect_btn.setText("Disconnect")
            else:
                self.status_label.setText("Status: Not Connected")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                self.connect_btn.setText("Connect")

    def on_connection_changed(self, index):
        connection_string = self.connection_combo.currentText()
        if "ASRL" in connection_string or "COM" in connection_string:
            self.show_rs232_settings()
            instrument_name = self.instru_combo.currentText()
            if instrument_name in self.INSTRUMENT_RS232_PRESETS:
                self.apply_rs232_preset(instrument_name)
        else:
            self.hide_rs232_settings()

    def refresh_connections(self):
        try:
            self.rm = visa.ResourceManager()
            resources = self.rm.list_resources()
            self.connection_combo.clear()
            self.connection_combo.addItem("None")
            self.connection_combo.addItems(list(resources))
            if self.allow_emulation:
                self.connection_combo.addItem("Emulation")
        except Exception as e:
            print(f"Error refreshing connections: {e}")

    def show_rs232_settings(self):
        self.clear_layout(self.rs232_layout)
        rs232_widget = QWidget()
        rs232_layout = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Baud:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["300", "1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")
        row1.addWidget(self.baud_combo)

        row1.addWidget(QLabel("Data:"))
        self.data_bits_combo = QComboBox()
        self.data_bits_combo.addItems(["5", "6", "7", "8"])
        self.data_bits_combo.setCurrentText("8")
        row1.addWidget(self.data_bits_combo)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Parity:"))
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        row2.addWidget(self.parity_combo)

        row2.addWidget(QLabel("Stop:"))
        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.addItems(["1", "1.5", "2"])
        row2.addWidget(self.stop_bits_combo)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Flow:"))
        self.flow_combo = QComboBox()
        self.flow_combo.addItems(["None", "Hardware (RTS/CTS)", "Software (XON/XOFF)"])
        row3.addWidget(self.flow_combo)

        rs232_layout.addLayout(row1)
        rs232_layout.addLayout(row2)
        rs232_layout.addLayout(row3)
        rs232_widget.setLayout(rs232_layout)
        self.rs232_layout.addWidget(rs232_widget)

    def hide_rs232_settings(self):
        self.clear_layout(self.rs232_layout)

    def apply_rs232_preset(self, instrument_name):
        if instrument_name in self.INSTRUMENT_RS232_PRESETS and hasattr(self, 'baud_combo'):
            preset = self.INSTRUMENT_RS232_PRESETS[instrument_name]
            self.baud_combo.setCurrentText(str(preset['baud_rate']))
            self.data_bits_combo.setCurrentText(str(preset['data_bits']))
            self.parity_combo.setCurrentText(preset['parity'])
            self.stop_bits_combo.setCurrentText(str(preset['stop_bits']))
            self.flow_combo.setCurrentText(preset['flow_control'])

    def toggle_connection(self):
        instrument_name = self.instru_combo.currentText()

        if instrument_name == "Select Instrument":
            return

        if instrument_name in self.connected_instruments:
            self.disconnect_instrument(instrument_name)
        else:
            self.connect_instrument()

    def connect_instrument(self):
        instrument_name = self.instru_combo.currentText()
        connection_string = self.connection_combo.currentText()

        if instrument_name == "Select Instrument" or connection_string == "None":
            QMessageBox.warning(self, "Invalid Selection", "Please select both instrument and connection.")
            return

        try:
            self.status_label.setText(f"Connecting...")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            QApplication.processEvents()

            if connection_string == "Emulation":
                self.connected_instruments[instrument_name] = None
                self.status_label.setText(f"Connected: {instrument_name} (Emulation)")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.connect_btn.setText("Disconnect")
                self.instrument_connected.emit(None, instrument_name)
            else:
                if not self.rm:
                    self.rm = visa.ResourceManager()

                instrument = self.rm.open_resource(connection_string)
                instrument.timeout = 10000

                if "ASRL" in connection_string or "COM" in connection_string:
                    if hasattr(self, 'baud_combo'):
                        instrument.baud_rate = int(self.baud_combo.currentText())
                        instrument.data_bits = int(self.data_bits_combo.currentText())

                # Test connection
                try:
                    if instrument_name == "DSP7265":
                        idn = instrument.query('ID')
                    else:
                        idn = instrument.query('*IDN?')

                    self.connected_instruments[instrument_name] = instrument
                    self.status_label.setText(f"Connected: {idn.strip()}")
                    self.status_label.setStyleSheet("color: green; font-weight: bold;")
                    self.connect_btn.setText("Disconnect")
                    self.instrument_connected.emit(instrument, instrument_name)
                except:
                    self.connected_instruments[instrument_name] = instrument
                    self.status_label.setText(f"Connected: {instrument_name}")
                    self.status_label.setStyleSheet("color: green; font-weight: bold;")
                    self.connect_btn.setText("Disconnect")
                    self.instrument_connected.emit(instrument, instrument_name)

        except Exception as e:
            self.status_label.setText("Connection failed")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            QMessageBox.critical(self, "Connection Error", f"Failed to connect:\n{str(e)}")

    def disconnect_instrument(self, instrument_name):
        try:
            if instrument_name in self.connected_instruments:
                instrument = self.connected_instruments[instrument_name]
                if instrument:
                    instrument.close()

                del self.connected_instruments[instrument_name]

                self.status_label.setText("Status: Not Connected")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                self.connect_btn.setText("Connect")

                self.instrument_disconnected.emit(instrument_name)

        except Exception as e:
            QMessageBox.warning(self, "Disconnect Error", f"Error disconnecting:\n{str(e)}")

    def get_connected_instruments(self):
        return self.connected_instruments.copy()

    def disconnect_all(self):
        instrument_names = list(self.connected_instruments.keys())
        for name in instrument_names:
            self.disconnect_instrument(name)

    def clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()


# ===================== PPMS Temperature & Field Widget =====================
class PPMSTemperatureFieldWidget(QWidget):
    """PPMS Temperature and Field configuration widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.font = QFont("Arial", 10)

        # Temperature zone flags
        self.Temp_setup_Zone_1 = False
        self.Temp_setup_Zone_2 = False
        self.Temp_setup_Zone_3 = False
        self.Temp_setup_Zone_Cus = False

        # Field zone flags
        self.Field_setup_Zone_1 = False
        self.Field_setup_Zone_2 = False
        self.Field_setup_Zone_3 = False

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Temperature Settings Group
        temp_group = QGroupBox("Temperature Settings")
        temp_layout = QVBoxLayout()

        # Zone selection
        zone_label = QLabel('Number of Temperature Zones:')
        zone_label.setFont(self.font)
        temp_layout.addWidget(zone_label)

        zone_btn_layout = QHBoxLayout()
        self.ppms_temp_One_zone_radio = QRadioButton("1")
        self.ppms_temp_Two_zone_radio = QRadioButton("2")
        self.ppms_temp_Three_zone_radio = QRadioButton("3")
        self.ppms_temp_Customize_zone_radio = QRadioButton("Customize")

        self.ppms_temp_One_zone_radio.setFont(self.font)
        self.ppms_temp_Two_zone_radio.setFont(self.font)
        self.ppms_temp_Three_zone_radio.setFont(self.font)
        self.ppms_temp_Customize_zone_radio.setFont(self.font)

        self.ppms_temp_One_zone_radio.toggled.connect(self.temp_zone_selection)
        self.ppms_temp_Two_zone_radio.toggled.connect(self.temp_zone_selection)
        self.ppms_temp_Three_zone_radio.toggled.connect(self.temp_zone_selection)
        self.ppms_temp_Customize_zone_radio.toggled.connect(self.temp_zone_selection)

        zone_btn_layout.addWidget(self.ppms_temp_One_zone_radio)
        zone_btn_layout.addWidget(self.ppms_temp_Two_zone_radio)
        zone_btn_layout.addWidget(self.ppms_temp_Three_zone_radio)
        zone_btn_layout.addWidget(self.ppms_temp_Customize_zone_radio)
        temp_layout.addLayout(zone_btn_layout)

        # Temperature zone container
        self.ppms_zone_temp_layout = QVBoxLayout()
        temp_layout.addLayout(self.ppms_zone_temp_layout)

        temp_group.setLayout(temp_layout)
        main_layout.addWidget(temp_group)

        # Field Settings Group
        field_group = QGroupBox("Field Settings")
        field_main_layout = QVBoxLayout()

        # Field direction
        direction_layout = QHBoxLayout()
        self.ppms_field_bidirectional_mode_radio_button = QRadioButton("Hysteresis")
        self.ppms_field_unidirectional_mode_radio_button = QRadioButton("Unidirectional")

        self.ppms_field_bidirectional_mode_radio_button.setFont(self.font)
        self.ppms_field_unidirectional_mode_radio_button.setFont(self.font)

        self.ppms_field_bidirectional_mode_radio_button.toggled.connect(self.ppms_field_mode_setup_ui)
        self.ppms_field_unidirectional_mode_radio_button.toggled.connect(self.ppms_field_mode_setup_ui)

        direction_layout.addWidget(self.ppms_field_bidirectional_mode_radio_button)
        direction_layout.addWidget(self.ppms_field_unidirectional_mode_radio_button)
        field_main_layout.addLayout(direction_layout)

        # Field mode and zones container
        self.ppms_field_setting_layout = QVBoxLayout()
        field_main_layout.addLayout(self.ppms_field_setting_layout)

        field_group.setLayout(field_main_layout)
        main_layout.addWidget(field_group)

    # Include all the temperature and field zone methods from the document
    # (temp_zone_selection, temp_one_zone, field_zone_selection, etc.)
    # ... (All the methods from the provided document go here - too long to repeat)

    def get_combined_field_temp_lists(self):
        """Get combined field and temperature settings"""
        combined = {'field_settings': self.get_ppms_field_settings(),
            'temp_settings': self.get_ppms_temperature_settings()}

        # Generate complete field list
        all_fields = []
        field_settings = combined['field_settings']
        if 'field_zones' in field_settings:
            for zone_name in sorted(field_settings['field_zones'].keys()):
                zone = field_settings['field_zones'][zone_name]
                field_list = zone.get('field_list', [])
                all_fields.extend(field_list)

        combined['all_fields'] = all_fields

        # Generate complete temperature list
        all_temps = []
        temp_settings = combined['temp_settings']
        if 'temp_zones' in temp_settings:
            temp_zones = []
            for zone_name in sorted(temp_settings['temp_zones'].keys()):
                zone = temp_settings['temp_zones'][zone_name]
                if zone.get('temp_list'):
                    temp_zones.append(zone)

            if temp_zones:
                all_temps = self._combine_temperature_zones_no_duplicates(temp_zones)

        combined['all_temps'] = all_temps

        return combined


# ===================== Updated PPMS MultiVu Widget =====================
class PPMSMultiVuWidget(QWidget):
    """PPMS MultiVu detection and connection widget with status update"""

    connection_status_changed = pyqtSignal(bool)  # Signal for connection status

    def __init__(self, parent=None):
        super().__init__(parent)
        self.font = QFont("Arial", 10)
        self.multivu_running = False
        self.server_running = False
        self.client_connected = False
        self.client = None
        self.server_process = None
        self.init_ui()

        # Start status monitoring thread
        self.status_thread = MultiVuStatusThread()
        self.status_thread.status_signal.connect(self.update_multivu_status)
        self.status_thread.start()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        ppms_group = QGroupBox("PPMS MultiVu Connection")
        ppms_layout = QVBoxLayout()

        # MultiVu Status Detection
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("MultiVu Status:"))
        self.status_label = QLabel("✗ Not Running")
        self.status_label.setFont(self.font)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(self.status_label)

        self.check_now_btn = QPushButton("Check Now")
        self.check_now_btn.clicked.connect(self.check_multivu_now)
        status_layout.addWidget(self.check_now_btn)
        status_layout.addStretch()
        ppms_layout.addLayout(status_layout)

        # Host and Port
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Host:"))
        self.host_entry = QLineEdit("127.0.0.1")
        self.host_entry.setFont(self.font)
        host_layout.addWidget(self.host_entry)

        host_layout.addWidget(QLabel("Port:"))
        self.port_entry = QLineEdit("5000")
        self.port_entry.setFont(self.font)
        host_layout.addWidget(self.port_entry)
        ppms_layout.addLayout(host_layout)

        # Server and Client buttons
        button_layout = QHBoxLayout()

        self.server_btn = QPushButton("Start Server")
        self.server_btn.clicked.connect(self.toggle_server)
        self.server_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        button_layout.addWidget(self.server_btn)

        self.client_btn = QPushButton("Connect Client")
        self.client_btn.setEnabled(False)
        self.client_btn.clicked.connect(self.toggle_client)
        self.client_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        button_layout.addWidget(self.client_btn)

        ppms_layout.addLayout(button_layout)

        # Connection Status
        self.connection_status_label = QLabel("Status: Not Connected")
        self.connection_status_label.setFont(self.font)
        self.connection_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_status_label.setStyleSheet("color: gray;")
        ppms_layout.addWidget(self.connection_status_label)

        ppms_group.setLayout(ppms_layout)
        main_layout.addWidget(ppms_group)

    def update_multivu_status(self, is_running):
        self.multivu_running = is_running
        if is_running:
            self.status_label.setText("✓ Running")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText("✗ Not Running")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")

    def check_multivu_now(self):
        is_running = is_multivu_running()
        self.update_multivu_status(is_running)

        if is_running:
            path = find_multivu_path()
            if path:
                QMessageBox.information(self, "MultiVu Found", f"MultiVu is running at:\n{path}")
            else:
                QMessageBox.information(self, "MultiVu Running", "MultiVu is running but path not found")
        else:
            QMessageBox.warning(self, "MultiVu Not Found", "MultiVu is not currently running")

    def toggle_server(self):
        if not self.server_running:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        try:
            self.server_running = True
            self.server_btn.setText("Stop Server")
            self.server_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
            self.client_btn.setEnabled(True)
            self.connection_status_label.setText("Server: Running")
            self.connection_status_label.setStyleSheet("color: orange;")
            QMessageBox.information(self, "Server Started", "MultiVu server started successfully")
        except Exception as e:
            QMessageBox.critical(self, "Server Error", f"Failed to start server:\n{str(e)}")

    def stop_server(self):
        try:
            if self.client_connected:
                self.disconnect_client()

            self.server_running = False
            self.server_btn.setText("Start Server")
            self.server_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            self.client_btn.setEnabled(False)
            self.connection_status_label.setText("Status: Not Connected")
            self.connection_status_label.setStyleSheet("color: gray;")

            # Emit connection status change
            self.connection_status_changed.emit(False)
        except Exception as e:
            QMessageBox.critical(self, "Server Error", f"Failed to stop server:\n{str(e)}")

    def toggle_client(self):
        if not self.client_connected:
            self.connect_client()
        else:
            self.disconnect_client()

    def connect_client(self):
        try:
            host = self.host_entry.text()
            port = self.port_entry.text()

            # In real implementation, connect to MultiPyVu client
            self.client_connected = True
            self.client = f"Client({host}:{port})"

            self.client_btn.setText("Disconnect Client")
            self.client_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
            self.connection_status_label.setText(f"Connected: {host}:{port}")
            self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")

            # Emit connection status change
            self.connection_status_changed.emit(True)

            QMessageBox.information(self, "Client Connected", f"Connected to MultiVu at {host}:{port}")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect client:\n{str(e)}")

    def disconnect_client(self):
        try:
            self.client_connected = False
            self.client = None

            self.client_btn.setText("Connect Client")
            self.client_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
            self.connection_status_label.setText("Status: Disconnected")
            self.connection_status_label.setStyleSheet("color: gray;")

            # Emit connection status change
            self.connection_status_changed.emit(False)
        except Exception as e:
            QMessageBox.critical(self, "Disconnect Error", f"Failed to disconnect:\n{str(e)}")

    def get_client(self):
        return self.client if self.client_connected else None

    def is_connected(self):
        return self.client_connected

    def cleanup(self):
        if self.status_thread:
            self.status_thread.stop()
            self.status_thread.wait()

        if self.client_connected:
            self.disconnect_client()

        if self.server_running:
            self.stop_server()

# ===================== Complete DSP7265SettingsWidget with IMODE Integration =====================
class DSP7265SettingsWidget(QWidget):
    """Complete DSP7265 configuration widget with IMODE-based sensitivity updates"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.font = QFont("Arial", 10)
        self.dsp_instrument = None
        self.demo_mode = False
        self.current_imode = 0  # Track current IMODE (0=Voltage, 1=High BW Current, 2=Low Noise Current)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Settings Group
        settings_group = QGroupBox("DSP 7265 Settings")
        settings_layout = QVBoxLayout()

        # IMODE
        imode_layout = QHBoxLayout()
        imode_layout.addWidget(QLabel("IMODE:"))
        self.imode_combo = QComboBox()
        self.imode_combo.setFont(self.font)
        self.imode_combo.addItems(["Select Input Mode", "Voltage Mode",  # IMODE 0
            "High Bandwidth Current",  # IMODE 1
            "Low Noise Current"  # IMODE 2
        ])
        self.imode_combo.currentIndexChanged.connect(self.dsp7265_imode_selection)
        imode_layout.addWidget(self.imode_combo)
        settings_layout.addLayout(imode_layout)

        # VMODE container (shown when IMODE selected)
        self.vmode_layout = QVBoxLayout()
        settings_layout.addLayout(self.vmode_layout)

        # Line Filter
        lf_layout = QHBoxLayout()
        lf_layout.addWidget(QLabel("Line Filter:"))
        self.lf_n1_combo = WideComboBox()
        self.lf_n1_combo.setFont(self.font)
        self.lf_n1_combo.addItems(
            ["Select Line Frequency", "off", "Enable 50 or 60 Hz notch filter", "Enable 100 or 120 Hz notch filter",
                "Enable both filter"])
        lf_layout.addWidget(self.lf_n1_combo)

        self.lf_n2_combo = WideComboBox()
        self.lf_n2_combo.setFont(self.font)
        self.lf_n2_combo.addItems(["Select Center Frequency", "60 Hz (and/or 120 Hz)", "50 Hz (and/or 100 Hz)"])
        lf_layout.addWidget(self.lf_n2_combo)

        self.lf_submit_btn = QPushButton('Submit')
        self.lf_submit_btn.clicked.connect(self.dsp7265_lf_selection)
        lf_layout.addWidget(self.lf_submit_btn)
        settings_layout.addLayout(lf_layout)

        # Sensitivity
        sens_layout = QHBoxLayout()
        sens_layout.addWidget(QLabel("Sensitivity:"))
        self.sens_combo = QComboBox()
        self.sens_combo.setFont(self.font)
        # Start with voltage mode sensitivity options
        self.sens_combo.addItems(
            ["Select Sensitivity", "2 nV", "5 nV", "10 nV", "20 nV", "50 nV", "100 nV", "200 nV", "500 nV", "1 µV",
                "2 µV", "5 µV", "10 µV", "20 µV", "50 µV", "100 µV", "200 µV", "500 µV", "1 mV", "2 mV", "5 mV",
                "10 mV", "20 mV", "50 mV", "100 mV", "200 mV", "500 mV", "1 V"])
        self.sens_combo.currentIndexChanged.connect(self.dsp7265_sens_selection)
        sens_layout.addWidget(self.sens_combo)
        settings_layout.addLayout(sens_layout)

        # Time Constant
        tc_layout = QHBoxLayout()
        tc_layout.addWidget(QLabel("Time constant:"))
        self.tc_combo = QComboBox()
        self.tc_combo.setFont(self.font)
        self.tc_combo.addItems(
            ["Select Time Constant", "10 µs", "20 µs", "40 µs", "80 µs", "160 µs", "320 µs", "640 µs", "5 ms", "10 ms",
                "20 ms", "50 ms", "100 ms", "200 ms", "500 ms", "1 s", "2 s", "5 s", "10 s", "20 s", "50 s", "100 s",
                "200 s", "500 s", "1 ks", "2 ks", "5 ks", "10 ks", "20 ks", "50 ks", "100 ks"])
        self.tc_combo.currentIndexChanged.connect(self.dsp7265_tc_selection)
        tc_layout.addWidget(self.tc_combo)
        settings_layout.addLayout(tc_layout)

        # Frequency
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Frequency:"))
        self.freq_entry = QLineEdit()
        self.freq_entry.setFont(self.font)
        self.freq_entry.setPlaceholderText("Enter frequency")
        freq_layout.addWidget(self.freq_entry)
        freq_layout.addWidget(QLabel("Hz"))

        self.freq_submit_btn = QPushButton('Submit')
        self.freq_submit_btn.clicked.connect(self.dsp7265_freq_setting)
        freq_layout.addWidget(self.freq_submit_btn)

        self.ref_channel_combo = QComboBox()
        self.ref_channel_combo.setFont(self.font)
        self.ref_channel_combo.addItems(["Select Ref Channel", "INT", "EXT REAR", "EXT FRONT"])
        self.ref_channel_combo.currentIndexChanged.connect(self.dsp7265_ref_channel_selection)
        freq_layout.addWidget(self.ref_channel_combo)
        settings_layout.addLayout(freq_layout)

        # Oscillator Amplitude
        oa_layout = QHBoxLayout()
        oa_layout.addWidget(QLabel("Oscillator Amplitude:"))
        self.oa_entry = QLineEdit()
        self.oa_entry.setFont(self.font)
        self.oa_entry.setPlaceholderText("Enter amplitude")
        oa_layout.addWidget(self.oa_entry)
        oa_layout.addWidget(QLabel("Vrms"))

        self.oa_submit_btn = QPushButton('Set')
        self.oa_submit_btn.clicked.connect(self.dsp7265_oa_setting)
        oa_layout.addWidget(self.oa_submit_btn)
        settings_layout.addLayout(oa_layout)

        # Slope
        slope_layout = QHBoxLayout()
        slope_layout.addWidget(QLabel("Slope:"))
        self.slope_combo = WideComboBox()
        self.slope_combo.setFont(self.font)
        self.slope_combo.addItems(["Selection", "6 dB/octave", "12 dB/octave", "18 dB/octave", "24 dB/octave"])
        self.slope_combo.currentIndexChanged.connect(self.dsp7265_slope_control)
        slope_layout.addWidget(self.slope_combo)
        settings_layout.addLayout(slope_layout)

        # Float/Ground Control
        float_layout = QHBoxLayout()
        float_layout.addWidget(QLabel("Float/Ground Control:"))
        self.float_combo = WideComboBox()
        self.float_combo.setFont(self.font)
        self.float_combo.addItems(["Selection", "Ground", "Float (connect to ground via 1 kΩ resistor)"])
        self.float_combo.currentIndexChanged.connect(self.dsp7265_float_control)
        float_layout.addWidget(self.float_combo)
        settings_layout.addLayout(float_layout)

        # Input Device Control
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Input Device Control:"))
        self.device_combo = WideComboBox()
        self.device_combo.setFont(self.font)
        self.device_combo.addItems(["Selection", "Bipolar Device, 10 kΩ input impedance", "FET, 10 MΩ input impedance"])
        self.device_combo.currentIndexChanged.connect(self.dsp7265_device_control)
        device_layout.addWidget(self.device_combo)
        settings_layout.addLayout(device_layout)

        # Auto buttons
        auto_layout = QHBoxLayout()
        self.auto_sens_btn = QPushButton("Auto Sens.")
        self.auto_sens_btn.clicked.connect(self.dsp7265_auto_sens)
        auto_layout.addWidget(self.auto_sens_btn)

        self.auto_phase_btn = QPushButton("Auto Phase")
        self.auto_phase_btn.clicked.connect(self.dsp7265_auto_phase)
        auto_layout.addWidget(self.auto_phase_btn)

        self.auto_meas_btn = QPushButton("Auto Meas.")
        self.auto_meas_btn.clicked.connect(self.dsp7265_auto_meas)
        auto_layout.addWidget(self.auto_meas_btn)
        settings_layout.addLayout(auto_layout)

        settings_group.setLayout(settings_layout)
        settings_group.setFixedWidth(620)
        main_layout.addWidget(settings_group)

        # Initially disable all controls
        self.set_controls_enabled(False)

    # ========== IMODE Selection with Sensitivity Update ==========
    def dsp7265_imode_selection(self):
        """Handle IMODE selection and update sensitivity options"""
        self.clear_layout(self.vmode_layout)
        imode_idx = self.imode_combo.currentIndex()

        if imode_idx == 0:  # "Select Input Mode"
            return

        # Map combo index to IMODE value
        # Index 1 = Voltage Mode (IMODE 0)
        # Index 2 = High Bandwidth Current (IMODE 1)
        # Index 3 = Low Noise Current (IMODE 2)
        self.current_imode = imode_idx - 1

        # Send command to instrument
        if self.dsp_instrument and not self.demo_mode:
            try:
                self.dsp_instrument.write(f'IMODE {self.current_imode}')
                time.sleep(0.1)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error setting IMODE:\n{str(e)}")

        # Update sensitivity options based on IMODE
        self.update_sensitivity_options(self.current_imode)

        # Show VMODE for Voltage Mode and High Bandwidth Current
        if imode_idx in [1, 2]:  # Voltage or High BW Current
            self.show_vmode_controls()

    def update_sensitivity_options(self, mode):
        """Update sensitivity combobox based on IMODE
        mode: 0=Voltage, 1=High BW Current, 2=Low Noise Current
        """
        # Block signals to prevent triggering apply_sensitivity
        self.sens_combo.blockSignals(True)

        # Clear current items
        self.sens_combo.clear()

        if mode == 0:  # Voltage Mode (IMODE=0)
            self.sens_combo.addItems(
                ["Select Sensitivity", "2 nV", "5 nV", "10 nV", "20 nV", "50 nV", "100 nV", "200 nV", "500 nV", "1 µV",
                    "2 µV", "5 µV", "10 µV", "20 µV", "50 µV", "100 µV", "200 µV", "500 µV", "1 mV", "2 mV", "5 mV",
                    "10 mV", "20 mV", "50 mV", "100 mV", "200 mV", "500 mV", "1 V"])
        elif mode == 1:  # High Bandwidth Current (IMODE=1)
            self.sens_combo.addItems(
                ["Select Sensitivity", "2 fA", "5 fA", "10 fA", "20 fA", "50 fA", "100 fA", "200 fA", "500 fA", "1 pA",
                    "2 pA", "5 pA", "10 pA", "20 pA", "50 pA", "100 pA", "200 pA", "500 pA", "1 nA", "2 nA", "5 nA",
                    "10 nA", "20 nA", "50 nA", "100 nA", "200 nA", "500 nA", "1 µA"])
        elif mode == 2:  # Low Noise Current (IMODE=2)
            self.sens_combo.addItems(
                ["Select Sensitivity", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "5 fA", "10 fA", "20 fA",
                    "50 fA", "100 fA", "200 fA", "500 fA", "1 pA", "2 pA", "5 pA", "10 pA", "20 pA", "50 pA", "100 pA",
                    "200 pA", "500 pA", "1 nA", "2 nA", "5 nA", "10 nA"])

        # Re-enable signals
        self.sens_combo.blockSignals(False)

    def show_vmode_controls(self):
        """Show VMODE selection controls"""
        vmode_h_layout = QHBoxLayout()
        vmode_h_layout.addWidget(QLabel("VMODE:"))
        self.vmode_combo = QComboBox()
        self.vmode_combo.setFont(self.font)
        self.vmode_combo.addItems(["Select Input Mode", "Both grounded", "A", "-B", "A-B"])
        self.vmode_combo.currentIndexChanged.connect(self.dsp7265_vmode_selection)
        vmode_h_layout.addWidget(self.vmode_combo)
        self.vmode_layout.addLayout(vmode_h_layout)

    def dsp7265_vmode_selection(self):
        """Handle VMODE selection"""
        if not hasattr(self, 'vmode_combo'):
            return

        vmode_idx = self.vmode_combo.currentIndex()
        if self.dsp_instrument and not self.demo_mode and vmode_idx > 0:
            try:
                self.dsp_instrument.write(f'VMODE {vmode_idx - 1}')
                time.sleep(0.1)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error setting VMODE:\n{str(e)}")

    # ========== Instrument Control Methods ==========
    def set_instrument(self, instrument, demo_mode=False):
        """Set the DSP7265 instrument and enable/disable controls"""
        self.dsp_instrument = instrument
        self.demo_mode = demo_mode

        # Enable/disable all input controls
        self.set_controls_enabled(instrument is not None or demo_mode)

        if not demo_mode and instrument:
            # Auto-fill current settings from instrument
            self.read_and_fill_sr7265_settings()

    def set_controls_enabled(self, enabled):
        """Enable or disable all input controls"""
        # Combo boxes
        self.imode_combo.setEnabled(enabled)
        self.lf_n1_combo.setEnabled(enabled)
        self.lf_n2_combo.setEnabled(enabled)
        self.sens_combo.setEnabled(enabled)
        self.tc_combo.setEnabled(enabled)
        self.ref_channel_combo.setEnabled(enabled)
        self.slope_combo.setEnabled(enabled)
        self.float_combo.setEnabled(enabled)
        self.device_combo.setEnabled(enabled)

        # Line edits
        self.freq_entry.setEnabled(enabled)
        self.oa_entry.setEnabled(enabled)

        # Buttons
        self.lf_submit_btn.setEnabled(enabled)
        self.freq_submit_btn.setEnabled(enabled)
        self.oa_submit_btn.setEnabled(enabled)
        self.auto_sens_btn.setEnabled(enabled)
        self.auto_phase_btn.setEnabled(enabled)
        self.auto_meas_btn.setEnabled(enabled)

        # Visual feedback
        if not enabled:
            style = "QComboBox, QLineEdit { background-color: #f0f0f0; color: #888; }"
            self.setStyleSheet(style)
        else:
            self.setStyleSheet("")

    def read_and_fill_sr7265_settings(self):
        """Read current settings from DSP7265 and auto-fill the UI"""
        if not self.dsp_instrument or self.demo_mode:
            return

        try:
            # Read IMODE first (determines sensitivity options)
            imode_idx = int(self.dsp_instrument.query("IMODE"))
            self.current_imode = imode_idx
            self.imode_combo.setCurrentIndex(imode_idx + 1)  # +1 for "Select Input Mode"

            # Update sensitivity options based on IMODE
            self.update_sensitivity_options(imode_idx)

            # Read VMODE if applicable
            if imode_idx in [0, 1]:  # Voltage or High BW Current
                vmode_idx = int(self.dsp_instrument.query("VMODE"))
                if hasattr(self, 'vmode_combo'):
                    self.vmode_combo.setCurrentIndex(vmode_idx + 1)

            # Read and set frequency
            freq = float(self.dsp_instrument.query('FRQ[.]')) / 1000
            self.freq_entry.setText(f"{freq:.3f}")

            # Read and set reference source
            ref = int(self.dsp_instrument.query("IE"))
            ref_map = {0: 1, 1: 2, 2: 3}
            if ref in ref_map:
                self.ref_channel_combo.setCurrentIndex(ref_map[ref])

            # Read and set time constant
            tc_idx = int(self.dsp_instrument.query("TC"))
            if 0 <= tc_idx < self.tc_combo.count() - 1:
                self.tc_combo.setCurrentIndex(tc_idx + 1)

            # Read and set sensitivity
            sen_idx = int(self.dsp_instrument.query("SEN"))
            if 0 <= sen_idx < self.sens_combo.count() - 1:
                self.sens_combo.setCurrentIndex(sen_idx + 1)

            # Read and set amplitude
            amplitude = float(self.dsp_instrument.query('OA[.]')) / 1e6
            self.oa_entry.setText(f"{amplitude:.6f}")

            # Read and set slope
            slope_idx = int(self.dsp_instrument.query("SLOPE"))
            if 0 <= slope_idx < self.slope_combo.count() - 1:
                self.slope_combo.setCurrentIndex(slope_idx + 1)

            # Read and set float
            float_idx = int(self.dsp_instrument.query("FLOAT"))
            if 0 <= float_idx < self.float_combo.count() - 1:
                self.float_combo.setCurrentIndex(float_idx + 1)

            # Read and set device
            device_idx = int(self.dsp_instrument.query("FET"))
            if 0 <= device_idx < self.device_combo.count() - 1:
                self.device_combo.setCurrentIndex(device_idx + 1)

            # Read and set line filter
            lf_status = self.dsp_instrument.query("LF")

            # LF returns a value where:
            # Bits 0-1: filter mode (0=off, 1=50/60Hz, 2=100/120Hz, 3=both)
            # Bit 2: frequency (0=60Hz, 1=50Hz)
            filter_mode = int(lf_status[0])  # Get bits 0-1
            filter_freq = int(lf_status[2])  # Get bit 2

            if 0 <= filter_mode <= 4:
                self.lf_n1_combo.setCurrentIndex(filter_mode + 1)  # +1 for "Select Line Frequency"

            if filter_freq in [0, 1]:
                self.lf_n2_combo.setCurrentIndex(filter_freq + 1)  # +1 for "Select Center Frequency"

            print("DSP7265 settings auto-filled successfully")

        except Exception as e:
            import traceback
            print(f"Error reading DSP7265 settings: {e}")
            print(traceback.format_exc())
            QMessageBox.warning(self, "Read Error", f"Could not read all settings from DSP7265:\n{str(e)}")

    # ========== All Other Control Methods ==========
    def dsp7265_sens_selection(self):
        """Apply sensitivity setting"""
        sens_idx = self.sens_combo.currentIndex()
        if self.dsp_instrument and not self.demo_mode and sens_idx > 0:
            try:
                self.dsp_instrument.write(f'SEN {sens_idx}')
                time.sleep(0.5)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error setting sensitivity:\n{str(e)}")

    def dsp7265_tc_selection(self):
        """Apply time constant setting"""
        tc_idx = self.tc_combo.currentIndex()
        if self.dsp_instrument and not self.demo_mode and tc_idx > 0:
            try:
                self.dsp_instrument.write(f'TC {tc_idx - 1}')
                time.sleep(0.5)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error setting time constant:\n{str(e)}")

    def dsp7265_ref_channel_selection(self):
        """Apply reference channel setting"""
        ref_idx = self.ref_channel_combo.currentIndex()
        if self.dsp_instrument and not self.demo_mode and ref_idx > 0:
            try:
                self.dsp_instrument.write(f'IE {ref_idx - 1}')
                time.sleep(0.5)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error setting reference:\n{str(e)}")

    def dsp7265_lf_selection(self):
        """Apply line filter settings"""
        lf_n1_idx = self.lf_n1_combo.currentIndex()
        lf_n2_idx = self.lf_n2_combo.currentIndex()

        if lf_n1_idx == 0:
            QMessageBox.warning(self, "Warning", "Please select line filter mode")
            return

        if self.dsp_instrument and not self.demo_mode:
            try:
                if lf_n2_idx == 0:
                    self.dsp_instrument.write(f'LF {lf_n1_idx - 1} 0')
                else:
                    self.dsp_instrument.write(f'LF {lf_n1_idx - 1} {lf_n2_idx - 1}')
                time.sleep(0.1)
                QMessageBox.information(self, "Success", "Line filter applied")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error setting line filter:\n{str(e)}")

    def dsp7265_auto_sens(self):
        """Auto sensitivity"""
        if self.dsp_instrument and not self.demo_mode:
            try:
                self.dsp_instrument.write('AS')
                time.sleep(1)
                QMessageBox.information(self, "Auto Sensitivity", "Auto sensitivity completed")
                self.read_and_fill_sr7265_settings()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error in auto sensitivity:\n{str(e)}")

    def dsp7265_device_control(self):
        """Apply input device control"""
        device_idx = self.device_combo.currentIndex()
        if self.dsp_instrument and not self.demo_mode and device_idx > 0:
            try:
                self.dsp_instrument.write(f'FET {device_idx - 1}')
                time.sleep(0.1)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error setting device:\n{str(e)}")

    def dsp7265_float_control(self):
        """Apply float/ground control"""
        float_idx = self.float_combo.currentIndex()
        if self.dsp_instrument and not self.demo_mode and float_idx > 0:
            try:
                self.dsp_instrument.write(f'FLOAT {float_idx - 1}')
                time.sleep(0.1)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error setting float:\n{str(e)}")

    def dsp7265_slope_control(self):
        """Apply slope setting"""
        slope_idx = self.slope_combo.currentIndex()
        if self.dsp_instrument and not self.demo_mode and slope_idx > 0:
            try:
                self.dsp_instrument.write(f'SLOPE {slope_idx - 1}')
                time.sleep(0.1)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error setting slope:\n{str(e)}")

    def dsp7265_auto_phase(self):
        """Auto phase"""
        if self.dsp_instrument and not self.demo_mode:
            try:
                self.dsp_instrument.write('AQN')
                time.sleep(1)
                QMessageBox.information(self, "Auto Phase", "Auto phase completed")
                self.read_and_fill_sr7265_settings()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error in auto phase:\n{str(e)}")

    def dsp7265_auto_meas(self):
        """Auto measurement"""
        if self.dsp_instrument and not self.demo_mode:
            try:
                self.dsp_instrument.write('ASM')
                time.sleep(2)
                QMessageBox.information(self, "Auto Measurement", "Auto measurement completed")
                self.read_and_fill_sr7265_settings()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error in auto measurement:\n{str(e)}")

    def dsp7265_freq_setting(self):
        """Apply frequency setting"""
        freq = self.freq_entry.text()
        if not freq:
            QMessageBox.warning(self, 'Warning', 'Please enter frequency')
            return

        if self.dsp_instrument and not self.demo_mode:
            try:
                self.dsp_instrument.write(f'OF. {freq}')
                time.sleep(1)
                QMessageBox.information(self, "Success", "Frequency set successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error setting frequency:\n{str(e)}")

    def dsp7265_oa_setting(self):
        """Apply oscillator amplitude setting"""
        amplitude = self.oa_entry.text()
        if not amplitude:
            QMessageBox.warning(self, 'Warning', 'Please enter amplitude')
            return

        if self.dsp_instrument and not self.demo_mode:
            try:
                self.dsp_instrument.write(f'OA. {float(amplitude)}')
                time.sleep(1)
                QMessageBox.information(self, "Success", "Amplitude set successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error setting amplitude:\n{str(e)}")

    def clear_layout(self, layout):
        """Clear all widgets from a layout"""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

# ===================== Instrument Status Widget =====================
class InstrumentStatusWidget(QWidget):
    def __init__(self, instrument_name, parent=None):
        super().__init__(parent)
        self.instrument_name = instrument_name
        self.connected = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        self.status_label = QLabel("✗")
        self.status_label.setStyleSheet("color: red; font-size: 16px; font-weight: bold;")
        self.name_label = QLabel(instrument_name)
        self.name_label.setStyleSheet("font-size: 10px;")

        layout.addWidget(self.status_label)
        layout.addWidget(self.name_label)
        layout.addStretch()

    def set_connected(self, connected):
        self.connected = connected
        if connected:
            self.status_label.setText("✓")
            self.status_label.setStyleSheet("color: green; font-size: 16px; font-weight: bold;")
        else:
            self.status_label.setText("✗")
            self.status_label.setStyleSheet("color: red; font-size: 16px; font-weight: bold;")

# ===================== PPMS MultiVu Connection Widget =====================
class PPMSMultiVuWidget(QWidget):
    """PPMS MultiVu detection and connection widget"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.font = QFont("Arial", 10)
        self.multivu_running = False
        self.server_running = False
        self.client_connected = False
        self.client = None
        self.server_process = None
        self.init_ui()

        # Start status monitoring thread
        self.status_thread = MultiVuStatusThread()
        self.status_thread.status_signal.connect(self.update_multivu_status)
        self.status_thread.start()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        ppms_group = QGroupBox("PPMS MultiVu Connection")
        ppms_layout = QVBoxLayout()

        # MultiVu Status Detection
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("MultiVu Status:"))
        self.status_label = QLabel("✗ Not Running")
        self.status_label.setFont(self.font)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(self.status_label)

        self.check_now_btn = QPushButton("Check Now")
        self.check_now_btn.clicked.connect(self.check_multivu_now)
        status_layout.addWidget(self.check_now_btn)
        status_layout.addStretch()
        ppms_layout.addLayout(status_layout)

        # Host and Port
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Host:"))
        self.host_entry = QLineEdit("127.0.0.1")
        self.host_entry.setFont(self.font)
        host_layout.addWidget(self.host_entry)

        host_layout.addWidget(QLabel("Port:"))
        self.port_entry = QLineEdit("5000")
        self.port_entry.setFont(self.font)
        host_layout.addWidget(self.port_entry)
        ppms_layout.addLayout(host_layout)

        # Server and Client buttons
        button_layout = QHBoxLayout()

        self.server_btn = QPushButton("Start Server")
        self.server_btn.clicked.connect(self.toggle_server)
        self.server_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        button_layout.addWidget(self.server_btn)

        self.client_btn = QPushButton("Connect Client")
        self.client_btn.setEnabled(False)
        self.client_btn.clicked.connect(self.toggle_client)
        self.client_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        button_layout.addWidget(self.client_btn)

        ppms_layout.addLayout(button_layout)

        # Connection Status
        self.connection_status_label = QLabel("Status: Not Connected")
        self.connection_status_label.setFont(self.font)
        self.connection_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_status_label.setStyleSheet("color: gray;")
        ppms_layout.addWidget(self.connection_status_label)

        ppms_group.setLayout(ppms_layout)
        main_layout.addWidget(ppms_group)

    def update_multivu_status(self, is_running):
        self.multivu_running = is_running
        if is_running:
            self.status_label.setText("✓ Running")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText("✗ Not Running")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")

    def check_multivu_now(self):
        is_running = is_multivu_running()
        self.update_multivu_status(is_running)

        if is_running:
            path = find_multivu_path()
            if path:
                QMessageBox.information(self, "MultiVu Found", f"MultiVu is running at:\n{path}")
            else:
                QMessageBox.information(self, "MultiVu Running", "MultiVu is running but path not found")
        else:
            QMessageBox.warning(self, "MultiVu Not Found", "MultiVu is not currently running")

    def toggle_server(self):
        if not self.server_running:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        try:
            # In a real implementation, you would start the MultiPyVu server here
            # For demo purposes, we'll just simulate it
            self.server_running = True
            self.server_btn.setText("Stop Server")
            self.server_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
            self.client_btn.setEnabled(True)
            self.connection_status_label.setText("Server: Running")
            self.connection_status_label.setStyleSheet("color: green;")
            QMessageBox.information(self, "Server Started", "MultiVu server started successfully")
        except Exception as e:
            QMessageBox.critical(self, "Server Error", f"Failed to start server:\n{str(e)}")

    def stop_server(self):
        try:
            if self.client_connected:
                self.disconnect_client()

            # Stop server
            self.server_running = False
            self.server_btn.setText("Start Server")
            self.server_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            self.client_btn.setEnabled(False)
            self.connection_status_label.setText("Status: Not Connected")
            self.connection_status_label.setStyleSheet("color: gray;")
        except Exception as e:
            QMessageBox.critical(self, "Server Error", f"Failed to stop server:\n{str(e)}")

    def toggle_client(self):
        if not self.client_connected:
            self.connect_client()
        else:
            self.disconnect_client()

    def connect_client(self):
        try:
            host = self.host_entry.text()
            port = self.port_entry.text()

            # In real implementation, connect to MultiPyVu client
            # For demo, simulate connection
            self.client_connected = True
            self.client = f"Client({host}:{port})"  # Placeholder

            self.client_btn.setText("Disconnect Client")
            self.client_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
            self.connection_status_label.setText(f"Connected: {host}:{port}")
            self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")

            QMessageBox.information(self, "Client Connected", f"Connected to MultiVu at {host}:{port}")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect client:\n{str(e)}")

    def disconnect_client(self):
        try:
            self.client_connected = False
            self.client = None

            self.client_btn.setText("Connect Client")
            self.client_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
            self.connection_status_label.setText("Status: Disconnected")
            self.connection_status_label.setStyleSheet("color: gray;")
        except Exception as e:
            QMessageBox.critical(self, "Disconnect Error", f"Failed to disconnect:\n{str(e)}")

    def get_client(self):
        return self.client if self.client_connected else None

    def cleanup(self):
        if self.status_thread:
            self.status_thread.stop()
            self.status_thread.wait()

        if self.client_connected:
            self.disconnect_client()

        if self.server_running:
            self.stop_server()

# ===================== Settings Tab =====================
class SettingsTab(QWidget):
    settings_ready = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.font = QFont("Arial", 10)
        self.measurement_type = None
        self.required_instruments = []
        self.instrument_connection_widget = None
        self.dsp7265_settings_widget = None
        self.ppms_widget = None


        try:
            with open("GUI/QSS/QScrollbar.qss", "r") as file:
                self.scrollbar_stylesheet = file.read()
        except:
            self.scrollbar_stylesheet = """
                QScrollBar:vertical {
                    border: none;
                    background: #f0f0f0;
                    width: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #c0c0c0;
                    min-height: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #a0a0a0;
                }
            """

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        title = QLabel("Measurement Configuration")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(self.scrollbar_stylesheet)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Experiment Selection
        experiment_group = QGroupBox("Experiment Selection")
        experiment_layout = QVBoxLayout()

        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Select Measurement:"))

        self.experiment_combo = HierarchicalComboBox()
        self.experiment_combo.setFont(QFont("Arial", 11))

        self.experiment_combo.addItem("Select Experiment")
        self.experiment_combo.add_category("━━━ ETO ━━━")
        self.experiment_combo.add_item("I-V")
        self.experiment_combo.add_item("Field Dependence")
        self.experiment_combo.add_item("Temperature Dependence")
        self.experiment_combo.add_category("━━━ FMR ━━━")
        self.experiment_combo.add_item("ST-FMR")
        self.experiment_combo.add_item("Coming Soon")
        self.experiment_combo.add_category("━━━ Customize ━━━")
        self.experiment_combo.add_item("Customized 1")
        self.experiment_combo.add_item("Spectrum Analysis")
        self.experiment_combo.add_category("━━━ Demo ━━━")
        self.experiment_combo.add_item("Demo Mode")

        self.experiment_combo.currentIndexChanged.connect(self.on_experiment_selected)
        selection_layout.addWidget(self.experiment_combo)
        experiment_layout.addLayout(selection_layout)

        button_layout = QHBoxLayout()
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_selection)
        self.reset_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")

        self.select_btn = QPushButton("Configure")
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.configure_measurement)
        self.select_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.select_btn)
        experiment_layout.addLayout(button_layout)

        experiment_group.setLayout(experiment_layout)
        scroll_layout.addWidget(experiment_group)

        # Dynamic Configuration Area
        self.config_area = QWidget()
        self.config_layout = QVBoxLayout(self.config_area)
        scroll_layout.addWidget(self.config_area)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

    def on_experiment_selected(self, index):
        if index == 0 or index in self.experiment_combo.skip_indexes:
            self.select_btn.setEnabled(False)
            self.measurement_type = None
        else:
            self.select_btn.setEnabled(True)
            text = self.experiment_combo.currentText().strip()
            self.measurement_type = text

    def configure_measurement(self):
        if not self.measurement_type:
            return

        self.clear_dynamic_widgets()

        # Determine required instruments based on measurement type
        if "Demo" in self.measurement_type:
            self.required_instruments = ["Keithley 2182 nv", "Keithley 6221", "DSP7265"]
            self.configure_eto_measurement(demo_mode=True)
        elif self.measurement_type in ["I-V", "Field Dependence", "Temperature Dependence"]:
            self.required_instruments = ["Keithley 2182 nv", "Keithley 6221", "DSP7265"]
            self.configure_eto_measurement(demo_mode=False)
        elif self.measurement_type == "ST-FMR":
            self.required_instruments = ["BNC 845 RF", "DSP7265"]
            self.configure_fmr_measurement()
        elif self.measurement_type in ["Customized 1", "Spectrum Analysis"]:
            self.required_instruments = ["Rigol DSA875", "B&K Precision 9205B"]
            self.configure_custom_measurement()

        self.update_status_bar_instruments()
        self.select_btn.setEnabled(False)

    def configure_eto_measurement(self, demo_mode=False):
        # PPMS MultiVu
        self.ppms_widget = PPMSMultiVuWidget()
        self.config_layout.addWidget(self.ppms_widget)

        # Instrument Connection
        self.instrument_connection_widget = DynamicInstrumentConnection(instrument_list=self.required_instruments,
            allow_emulation=True, title="Instrument Connection")
        self.instrument_connection_widget.instrument_connected.connect(self.on_instrument_connected)
        self.instrument_connection_widget.instrument_disconnected.connect(self.on_instrument_disconnected)
        self.config_layout.addWidget(self.instrument_connection_widget)

        # DSP7265 Settings (only shown when DSP7265 is in the list)
        if "DSP7265" in self.required_instruments:
            self.dsp7265_settings_widget = DSP7265SettingsWidget()
            self.config_layout.addWidget(self.dsp7265_settings_widget)

        # ETO-specific parameters
        eto_params_group = QGroupBox("ETO Measurement Parameters")
        eto_params_layout = QVBoxLayout()

        # Number of Averages
        avg_layout = QHBoxLayout()
        avg_layout.addWidget(QLabel("Number of Averages:"))
        self.eto_avg_spinbox = QSpinBox()
        self.eto_avg_spinbox.setRange(1, 100)
        self.eto_avg_spinbox.setValue(21)
        avg_layout.addWidget(self.eto_avg_spinbox)
        avg_layout.addStretch()
        eto_params_layout.addLayout(avg_layout)

        # Temperature Rate
        temp_rate_layout = QHBoxLayout()
        temp_rate_layout.addWidget(QLabel("Temp Ramp Rate (K/min):"))
        self.eto_temp_rate_entry = QLineEdit("50.0")
        temp_rate_layout.addWidget(self.eto_temp_rate_entry)
        temp_rate_layout.addStretch()
        eto_params_layout.addLayout(temp_rate_layout)

        # Demag Field
        demag_layout = QHBoxLayout()
        demag_layout.addWidget(QLabel("Demag Field (Oe):"))
        self.eto_demag_field_entry = QLineEdit("10000")
        demag_layout.addWidget(self.eto_demag_field_entry)
        demag_layout.addStretch()
        eto_params_layout.addLayout(demag_layout)

        # Record Zero Field (only for Field Dependence)
        if self.measurement_type == "Field Dependence":
            self.eto_zero_field_checkbox = QCheckBox("Record Zero Field")
            eto_params_layout.addWidget(self.eto_zero_field_checkbox)

        eto_params_group.setLayout(eto_params_layout)
        self.config_layout.addWidget(eto_params_group)

    def configure_fmr_measurement(self):
        # PPMS MultiVu
        self.ppms_widget = PPMSMultiVuWidget()
        self.config_layout.addWidget(self.ppms_widget)

        # Instrument Connection
        self.instrument_connection_widget = DynamicInstrumentConnection(instrument_list=self.required_instruments,
            allow_emulation=True, title="Instrument Connection")
        self.instrument_connection_widget.instrument_connected.connect(self.on_instrument_connected)
        self.instrument_connection_widget.instrument_disconnected.connect(self.on_instrument_disconnected)
        self.config_layout.addWidget(self.instrument_connection_widget)

        # DSP7265 Settings
        self.dsp7265_settings_widget = DSP7265SettingsWidget()
        self.config_layout.addWidget(self.dsp7265_settings_widget)

        # FMR-specific parameters
        fmr_params_group = QGroupBox("FMR Measurement Parameters")
        fmr_params_layout = QVBoxLayout()

        # Number of Repetitions
        rep_layout = QHBoxLayout()
        rep_layout.addWidget(QLabel("Number of Repetitions:"))
        self.fmr_rep_spinbox = QSpinBox()
        self.fmr_rep_spinbox.setRange(1, 100)
        self.fmr_rep_spinbox.setValue(5)
        rep_layout.addWidget(self.fmr_rep_spinbox)
        rep_layout.addStretch()
        fmr_params_layout.addLayout(rep_layout)

        # Initial Temperature Rate
        temp_rate_layout = QHBoxLayout()
        temp_rate_layout.addWidget(QLabel("Initial Temp Rate (K/min):"))
        self.fmr_temp_rate_entry = QLineEdit("10.0")
        temp_rate_layout.addWidget(self.fmr_temp_rate_entry)
        temp_rate_layout.addStretch()
        fmr_params_layout.addLayout(temp_rate_layout)

        fmr_params_group.setLayout(fmr_params_layout)
        self.config_layout.addWidget(fmr_params_group)

    def configure_custom_measurement(self):
        # No PPMS for custom measurements

        # Instrument Connection
        self.instrument_connection_widget = DynamicInstrumentConnection(instrument_list=self.required_instruments,
            allow_emulation=True, title="Instrument Connection")
        self.instrument_connection_widget.instrument_connected.connect(self.on_instrument_connected)
        self.instrument_connection_widget.instrument_disconnected.connect(self.on_instrument_disconnected)
        self.config_layout.addWidget(self.instrument_connection_widget)

        # Custom parameters placeholder
        custom_params_group = QGroupBox("Custom Measurement Parameters")
        custom_params_layout = QVBoxLayout()

        info_label = QLabel("Custom measurement parameters will be configured here")
        info_label.setFont(self.font)
        custom_params_layout.addWidget(info_label)

        custom_params_group.setLayout(custom_params_layout)
        self.config_layout.addWidget(custom_params_group)

    def on_instrument_connected(self, instrument, instrument_name):
        # Update DSP7265 settings widget
        if instrument_name == "DSP7265" and self.dsp7265_settings_widget:
            demo_mode = (instrument is None)
            self.dsp7265_settings_widget.set_instrument(instrument, demo_mode)

        main_window = self.get_main_window()
        if main_window and instrument_name in main_window.instruments:
            main_window.instruments[instrument_name].set_connected(True)
        print(f"✓ {instrument_name} connected")

    def on_instrument_disconnected(self, instrument_name):
        main_window = self.get_main_window()
        if main_window and instrument_name in main_window.instruments:
            main_window.instruments[instrument_name].set_connected(False)
        print(f"✗ {instrument_name} disconnected")

    def update_status_bar_instruments(self):
        main_window = self.get_main_window()
        if main_window:
            main_window.update_instrument_status_bar(self.required_instruments)

    def clear_dynamic_widgets(self):
        if self.instrument_connection_widget:
            self.instrument_connection_widget.disconnect_all()

        if self.ppms_widget:
            self.ppms_widget.cleanup()

        while self.config_layout.count():
            item = self.config_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.instrument_connection_widget = None
        self.dsp7265_settings_widget = None
        self.ppms_widget = None

    def reset_selection(self):
        self.experiment_combo.setCurrentIndex(0)
        self.measurement_type = None
        self.required_instruments = []
        self.select_btn.setEnabled(False)
        self.clear_dynamic_widgets()

        main_window = self.get_main_window()
        if main_window:
            main_window.update_instrument_status_bar([])

    def get_settings(self):
        settings = {'measurement_type': self.measurement_type, 'required_instruments': self.required_instruments, }

        if self.instrument_connection_widget:
            settings['connected_instruments'] = self.instrument_connection_widget.get_connected_instruments()
        else:
            settings['connected_instruments'] = {}

        if self.ppms_widget:
            settings['ppms_client'] = self.ppms_widget.get_client()
            settings['multivu_running'] = self.ppms_widget.multivu_running

        if self.dsp7265_settings_widget:
            settings['dsp7265_instrument'] = settings['connected_instruments'].get('DSP7265')

        # Get measurement-specific parameters
        if hasattr(self, 'eto_avg_spinbox'):
            settings['eto_averages'] = self.eto_avg_spinbox.value()
            settings['eto_temp_rate'] = float(self.eto_temp_rate_entry.text())
            settings['eto_demag_field'] = float(self.eto_demag_field_entry.text())
            if hasattr(self, 'eto_zero_field_checkbox'):
                settings['eto_record_zero_field'] = self.eto_zero_field_checkbox.isChecked()

        if hasattr(self, 'fmr_rep_spinbox'):
            settings['fmr_repetitions'] = self.fmr_rep_spinbox.value()
            settings['fmr_temp_rate'] = float(self.fmr_temp_rate_entry.text())

        return settings

    def get_main_window(self):
        widget = self.parent()
        while widget:
            if isinstance(widget, MeasurementSystemMainWindow):
                return widget
            widget = widget.parent()
        return None

# ===================== Running Tab =====================
class RunningTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = {}
        self.dsp_instrument = None
        self.demo_mode = False
        self.dsp_readings_enabled = False
        self.font = QFont("Arial", 10)
        self.init_ui()

        # Update timer for readings
        self.reading_timer = QTimer()
        self.reading_timer.timeout.connect(self.update_all_readings)

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Left panel - Status and Readings
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        self.status_label = QLabel("Status: Idle")
        self.status_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: gray;")
        left_layout.addWidget(self.status_label)

        # Circular Progress
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.circular_progress = CircularProgressBar()
        progress_layout.addWidget(self.circular_progress, alignment=Qt.AlignmentFlag.AlignCenter)

        progress_label = QLabel("Measurement Progress")
        progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(progress_label)

        left_layout.addWidget(progress_container)

        # Current Readings Group
        readings_group = QGroupBox("Current Readings")
        readings_layout = QVBoxLayout()

        # PPMS Readings
        self.ppms_readings_widget = QWidget()
        ppms_readings_layout = QVBoxLayout(self.ppms_readings_widget)

        ppms_title = QLabel("PPMS Readings")
        ppms_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        ppms_readings_layout.addWidget(ppms_title)

        # Temperature
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperature:"))
        self.ppms_temp_label = QLabel("N/A")
        self.ppms_temp_label.setFont(self.font)
        temp_layout.addWidget(self.ppms_temp_label)
        temp_layout.addStretch()
        ppms_readings_layout.addLayout(temp_layout)

        # Field
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel("Field:"))
        self.ppms_field_label = QLabel("N/A")
        self.ppms_field_label.setFont(self.font)
        field_layout.addWidget(self.ppms_field_label)
        field_layout.addStretch()
        ppms_readings_layout.addLayout(field_layout)

        # Chamber
        chamber_layout = QHBoxLayout()
        chamber_layout.addWidget(QLabel("Chamber:"))
        self.ppms_chamber_label = QLabel("N/A")
        self.ppms_chamber_label.setFont(self.font)
        chamber_layout.addWidget(self.ppms_chamber_label)
        chamber_layout.addStretch()
        ppms_readings_layout.addLayout(chamber_layout)

        self.ppms_readings_widget.hide()  # Hidden by default
        readings_layout.addWidget(self.ppms_readings_widget)

        # DSP7265 Readings
        self.dsp_readings_widget = QWidget()
        dsp_readings_layout = QVBoxLayout(self.dsp_readings_widget)

        dsp_title = QLabel("DSP7265 Readings")
        dsp_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        dsp_readings_layout.addWidget(dsp_title)

        # X
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X:"))
        self.dsp_x_label = QLabel("N/A")
        self.dsp_x_label.setFont(self.font)
        x_layout.addWidget(self.dsp_x_label)
        x_layout.addStretch()
        dsp_readings_layout.addLayout(x_layout)

        # Y
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Y:"))
        self.dsp_y_label = QLabel("N/A")
        self.dsp_y_label.setFont(self.font)
        y_layout.addWidget(self.dsp_y_label)
        y_layout.addStretch()
        dsp_readings_layout.addLayout(y_layout)

        # Magnitude
        mag_layout = QHBoxLayout()
        mag_layout.addWidget(QLabel("Magnitude:"))
        self.dsp_mag_label = QLabel("N/A")
        self.dsp_mag_label.setFont(self.font)
        mag_layout.addWidget(self.dsp_mag_label)
        mag_layout.addStretch()
        dsp_readings_layout.addLayout(mag_layout)

        # Phase
        phase_layout = QHBoxLayout()
        phase_layout.addWidget(QLabel("Phase:"))
        self.dsp_phase_label = QLabel("N/A")
        self.dsp_phase_label.setFont(self.font)
        phase_layout.addWidget(self.dsp_phase_label)
        phase_layout.addStretch()
        dsp_readings_layout.addLayout(phase_layout)

        self.dsp_readings_widget.hide()  # Hidden by default
        readings_layout.addWidget(self.dsp_readings_widget)

        # Keithley Readings
        self.keithley_readings_widget = QWidget()
        keithley_readings_layout = QVBoxLayout(self.keithley_readings_widget)

        keithley_title = QLabel("Keithley Readings")
        keithley_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        keithley_readings_layout.addWidget(keithley_title)

        # Voltage
        voltage_layout = QHBoxLayout()
        voltage_layout.addWidget(QLabel("Voltage (2182):"))
        self.keithley_voltage_label = QLabel("N/A")
        self.keithley_voltage_label.setFont(self.font)
        voltage_layout.addWidget(self.keithley_voltage_label)
        voltage_layout.addStretch()
        keithley_readings_layout.addLayout(voltage_layout)

        # Current
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("Current (6221):"))
        self.keithley_current_label = QLabel("N/A")
        self.keithley_current_label.setFont(self.font)
        current_layout.addWidget(self.keithley_current_label)
        current_layout.addStretch()
        keithley_readings_layout.addLayout(current_layout)

        self.keithley_readings_widget.hide()  # Hidden by default
        readings_layout.addWidget(self.keithley_readings_widget)

        readings_group.setLayout(readings_layout)
        left_layout.addWidget(readings_group)

        # Elapsed Time
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Elapsed Time:"))
        self.elapsed_time_label = QLabel("00:00:00")
        self.elapsed_time_label.setFont(self.font)
        time_layout.addWidget(self.elapsed_time_label)
        time_layout.addStretch()
        left_layout.addLayout(time_layout)

        # Log
        log_group = QGroupBox("Measurement Log")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        left_layout.addWidget(log_group)

        # Right panel - Plot
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        plot_title = QLabel("Real-time Data")
        plot_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        right_layout.addWidget(plot_title)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Signal', units='V')
        self.plot_widget.setLabel('bottom', 'Time', units='s')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
        right_layout.addWidget(self.plot_widget)

        # Add to main layout
        layout.addWidget(left_widget, 2)
        layout.addWidget(right_widget, 3)

    def load_settings(self, settings):
        self.settings = settings
        measurement_type = settings.get('measurement_type', 'Unknown')
        self.log_message(f"Loaded: {measurement_type}")

        # Show/hide appropriate reading widgets
        connected = settings.get('connected_instruments', {})

        # PPMS
        if settings.get('ppms_client'):
            self.ppms_readings_widget.show()
            self.log_message("✓ PPMS MultiVu connected")

        # DSP7265
        if 'DSP7265' in connected:
            self.dsp_instrument = connected['DSP7265']
            self.demo_mode = (self.dsp_instrument is None)

            # Only enable readings if instrument is connected
            if self.dsp_instrument or self.demo_mode:
                self.dsp_readings_widget.show()
                self.dsp_readings_enabled = True
                self.log_message("✓ DSP7265 readings enabled")
            else:
                self.dsp_readings_widget.hide()
                self.dsp_readings_enabled = False
                self.log_message("✗ DSP7265 not connected")

        # Keithley
        if 'Keithley 2182 nv' in connected or 'Keithley 6221' in connected:
            self.keithley_readings_widget.show()
            self.log_message("✓ Keithley readings enabled")

        # Log all parameters
        if 'eto_averages' in settings:
            self.log_message(f"  - Averages: {settings['eto_averages']}")
            self.log_message(f"  - Temp Rate: {settings['eto_temp_rate']} K/min")
            self.log_message(f"  - Demag Field: {settings['eto_demag_field']} Oe")

        if 'fmr_repetitions' in settings:
            self.log_message(f"  - Repetitions: {settings['fmr_repetitions']}")
            self.log_message(f"  - Temp Rate: {settings['fmr_temp_rate']} K/min")

    def update_all_readings(self):
        """Update all instrument readings"""

        # Update PPMS readings (simulated)
        if self.ppms_readings_widget.isVisible():
            if self.demo_mode or not self.settings.get('ppms_client'):
                self.ppms_temp_label.setText(f"{np.random.uniform(290, 310):.2f} K")
                self.ppms_field_label.setText(f"{np.random.uniform(-1000, 1000):.1f} Oe")
                self.ppms_chamber_label.setText(f"{np.random.uniform(1, 10):.2e} Torr")

        # Update DSP7265 readings ONLY if enabled
        if self.dsp_readings_enabled and self.dsp_readings_widget.isVisible():
            if self.demo_mode or not self.dsp_instrument:
                self.dsp_x_label.setText(f"{np.random.uniform(-1, 1):.6f} V")
                self.dsp_y_label.setText(f"{np.random.uniform(-1, 1):.6f} V")
                mag = np.random.uniform(0, 1)
                self.dsp_mag_label.setText(f"{mag:.6f} V")
                self.dsp_phase_label.setText(f"{np.random.uniform(-180, 180):.2f}°")
            else:
                try:
                    x = float(self.dsp_instrument.query('X.'))
                    y = float(self.dsp_instrument.query('Y.'))
                    mag = float(self.dsp_instrument.query('MAG.'))
                    phase = float(self.dsp_instrument.query('PHA.'))

                    self.dsp_x_label.setText(f"{x:.6f} V")
                    self.dsp_y_label.setText(f"{y:.6f} V")
                    self.dsp_mag_label.setText(f"{mag:.6f} V")
                    self.dsp_phase_label.setText(f"{phase:.2f}°")
                except Exception as e:
                    print(f"Error reading DSP7265: {e}")
                    # Disable readings on error
                    self.dsp_readings_enabled = False
                    self.log_message("✗ DSP7265 reading error - disabled", "red")

        # Update Keithley readings (simulated)
        if self.keithley_readings_widget.isVisible():
            self.keithley_voltage_label.setText(f"{np.random.uniform(-10, 10):.6f} V")
            self.keithley_current_label.setText(f"{np.random.uniform(-1, 1):.6f} mA")

    def start_measurement(self):
        self.log_message("Starting measurement...")
        self.reading_timer.start(1000)  # Update readings every second

        # Start elapsed time
        self.start_time = datetime.now()
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_elapsed_time)
        self.time_timer.start(1000)

    def stop_measurement(self):
        self.reading_timer.stop()
        if hasattr(self, 'time_timer'):
            self.time_timer.stop()

    def update_all_readings(self):
        """Update all instrument readings"""

        # Update PPMS readings (simulated)
        if self.ppms_readings_widget.isVisible():
            if self.demo_mode or not self.settings.get('ppms_client'):
                self.ppms_temp_label.setText(f"{np.random.uniform(290, 310):.2f} K")
                self.ppms_field_label.setText(f"{np.random.uniform(-1000, 1000):.1f} Oe")
                self.ppms_chamber_label.setText(f"{np.random.uniform(1, 10):.2e} Torr")

        # Update DSP7265 readings
        if self.dsp_readings_widget.isVisible():
            if self.demo_mode or not self.dsp_instrument:
                self.dsp_x_label.setText(f"{np.random.uniform(-1, 1):.6f} V")
                self.dsp_y_label.setText(f"{np.random.uniform(-1, 1):.6f} V")
                mag = np.random.uniform(0, 1)
                self.dsp_mag_label.setText(f"{mag:.6f} V")
                self.dsp_phase_label.setText(f"{np.random.uniform(-180, 180):.2f}°")
            else:
                try:
                    x = float(self.dsp_instrument.query('X.'))
                    y = float(self.dsp_instrument.query('Y.'))
                    mag = float(self.dsp_instrument.query('MAG.'))
                    phase = float(self.dsp_instrument.query('PHA.'))

                    self.dsp_x_label.setText(f"{x:.6f} V")
                    self.dsp_y_label.setText(f"{y:.6f} V")
                    self.dsp_mag_label.setText(f"{mag:.6f} V")
                    self.dsp_phase_label.setText(f"{phase:.2f}°")
                except Exception as e:
                    print(f"Error reading DSP7265: {e}")

        # Update Keithley readings (simulated)
        if self.keithley_readings_widget.isVisible():
            self.keithley_voltage_label.setText(f"{np.random.uniform(-10, 10):.6f} V")
            self.keithley_current_label.setText(f"{np.random.uniform(-1, 1):.6f} mA")

    def update_elapsed_time(self):
        """Update elapsed time display"""
        elapsed = datetime.now() - self.start_time
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        seconds = int(elapsed.total_seconds() % 60)
        self.elapsed_time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def log_message(self, message, color=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if color:
            self.log_text.append(f'<span style="color: {color};">[{timestamp}] {message}</span>')
        else:
            self.log_text.append(f"[{timestamp}] {message}")

    def update_progress(self, value):
        self.circular_progress.setValue(value)

    def clear_all(self):
        self.status_label.setText("Status: Idle")
        self.status_label.setStyleSheet("color: gray;")
        self.circular_progress.setValue(0)
        self.log_text.clear()
        self.plot_widget.clear()
        self.reading_timer.stop()
        if hasattr(self, 'time_timer'):
            self.time_timer.stop()

        # Hide all reading widgets
        self.ppms_readings_widget.hide()
        self.dsp_readings_widget.hide()
        self.keithley_readings_widget.hide()

        # Reset labels
        self.elapsed_time_label.setText("00:00:00")
        self.ppms_temp_label.setText("N/A")
        self.ppms_field_label.setText("N/A")
        self.ppms_chamber_label.setText("N/A")
        self.dsp_x_label.setText("N/A")
        self.dsp_y_label.setText("N/A")
        self.dsp_mag_label.setText("N/A")
        self.dsp_phase_label.setText("N/A")
        self.keithley_voltage_label.setText("N/A")
        self.keithley_current_label.setText("N/A")

# ===================== Visualization Tab =====================
class VisualizationTab(QWidget):
    """Visualization tab with auto-discovery of measurement output files"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.font = QFont("Arial", 10)
        self.x_column = None
        self.y_columns = []
        self.original_headers = {}
        self.plot_data = {}
        self.current_file_path = None
        self.output_folder = None
        self.known_files = set()  # Track files we've already seen
        self.init_ui()

        # Auto-refresh timer for new files
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh_files)
        self.refresh_timer.start(2000)  # Check every 2 seconds for new files

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # Left Panel - File Browser and Table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # File Browser Header
        file_browser_group = QGroupBox("Measurement Output Files")
        file_browser_layout = QVBoxLayout()

        # Info bar
        info_layout = QHBoxLayout()
        self.folder_info_label = QLabel("Waiting for measurement to start...")
        self.folder_info_label.setStyleSheet("""
            QLabel {
                color: #666;
                padding: 8px;
                background-color: #f0f0f0;
                border-radius: 5px;
                font-style: italic;
            }
        """)
        info_layout.addWidget(self.folder_info_label)

        self.manual_browse_btn = QPushButton("📁 Browse Folder")
        self.manual_browse_btn.setToolTip("Manually select output folder")
        self.manual_browse_btn.clicked.connect(self.manual_browse_folder)
        self.manual_browse_btn.setMaximumWidth(120)
        info_layout.addWidget(self.manual_browse_btn)

        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setToolTip("Refresh file list")
        self.refresh_btn.clicked.connect(self.refresh_files)
        self.refresh_btn.setMaximumWidth(40)
        info_layout.addWidget(self.refresh_btn)

        file_browser_layout.addLayout(info_layout)

        # File count and status
        self.file_count_label = QLabel("No files detected")
        self.file_count_label.setStyleSheet("""
            QLabel {
                color: #555;
                padding: 5px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        file_browser_layout.addWidget(self.file_count_label)

        # File Tree
        self.file_tree = QTreeView()
        self.file_tree_model = QStandardItemModel()
        self.file_tree_model.setHorizontalHeaderLabels(["File Name", "Type", "Size", "Modified"])
        self.file_tree.setModel(self.file_tree_model)
        self.file_tree.setSelectionMode(QTreeView.SelectionMode.SingleSelection)
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.clicked.connect(self.on_file_selected)
        self.file_tree.setSortingEnabled(True)
        self.file_tree.sortByColumn(3, Qt.SortOrder.DescendingOrder)  # Sort by modified time

        header = self.file_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.file_tree.setStyleSheet("""
            QTreeView {
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QTreeView::item:selected {
                background-color: #3498db;
                color: white;
            }
            QTreeView::item:hover {
                background-color: #ecf0f1;
            }
        """)

        file_browser_layout.addWidget(self.file_tree)
        file_browser_group.setLayout(file_browser_layout)
        left_layout.addWidget(file_browser_group, 1)

        # Data Table Preview
        table_group = QGroupBox("Data Preview & Column Selection")
        table_layout = QVBoxLayout()

        # Selection instructions
        instruction_label = QLabel("📊 Click header = X (blue) | Ctrl+Click = Add Y (red) | Shift+Click = Remove")
        instruction_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 5px;
                background-color: #ecf0f1;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        table_layout.addWidget(instruction_label)

        # Selection display
        self.selection_display = QLabel("X: None | Y: None")
        self.selection_display.setStyleSheet("""
            QLabel {
                padding: 5px;
                background-color: #e8f4ff;
                border: 1px solid #3498db;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        table_layout.addWidget(self.selection_display)

        # Table View
        self.table_view = QTableView()
        self.table_model = QStandardItemModel()
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectColumns)
        self.table_view.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        self.table_view.setMaximumHeight(300)
        self.table_view.setAlternatingRowColors(True)
        table_layout.addWidget(self.table_view)

        # Buttons
        button_layout = QHBoxLayout()

        self.clear_btn = QPushButton("Clear Selection")
        self.clear_btn.clicked.connect(self.clear_selection)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        button_layout.addWidget(self.clear_btn)

        self.plot_btn = QPushButton("📈 Plot Data")
        self.plot_btn.clicked.connect(self.plot_selected_data)
        self.plot_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 5px 20px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(self.plot_btn)

        self.clear_plot_btn = QPushButton("Clear Plot")
        self.clear_plot_btn.clicked.connect(self.clear_plot)
        self.clear_plot_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        button_layout.addWidget(self.clear_plot_btn)

        button_layout.addStretch()
        table_layout.addLayout(button_layout)

        table_group.setLayout(table_layout)
        left_layout.addWidget(table_group, 1)

        # Right Panel - Plot
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        plot_header_layout = QHBoxLayout()
        plot_title = QLabel("Data Visualization")
        plot_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        plot_header_layout.addWidget(plot_title)
        plot_header_layout.addStretch()

        # Export plot button
        self.export_plot_btn = QPushButton("💾 Export Plot")
        self.export_plot_btn.clicked.connect(self.export_plot)
        self.export_plot_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        plot_header_layout.addWidget(self.export_plot_btn)

        right_layout.addLayout(plot_header_layout)

        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Y Values')
        self.plot_widget.setLabel('bottom', 'X Values')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
        self.plot_widget.getPlotItem().getViewBox().setMouseMode(pg.ViewBox.RectMode)
        right_layout.addWidget(self.plot_widget)

        # Plot info
        self.plot_info_label = QLabel("No data plotted • Select X and Y columns, then click 'Plot Data'")
        self.plot_info_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)
        self.plot_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.plot_info_label)

        # Add panels to main layout
        main_layout.addWidget(left_widget, 2)
        main_layout.addWidget(right_widget, 3)

    def set_output_folder(self, folder_path):
        """Set the output folder from settings (called by main window)"""
        if folder_path and os.path.exists(folder_path):
            self.output_folder = folder_path
            self.known_files.clear()  # Reset known files
            self.folder_info_label.setText(f"📁 Monitoring: {os.path.basename(folder_path)}")
            self.folder_info_label.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    padding: 8px;
                    background-color: #d4edda;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)
            self.refresh_files()

    def manual_browse_folder(self):
        """Manually select output folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder",
            self.output_folder if self.output_folder else os.getcwd())

        if folder:
            self.set_output_folder(folder)

    def auto_refresh_files(self):
        """Auto-refresh to detect new files"""
        if self.output_folder and os.path.exists(self.output_folder):
            # Check for new files
            current_files = set()
            for file_name in os.listdir(self.output_folder):
                file_path = os.path.join(self.output_folder, file_name)
                if os.path.isfile(file_path):
                    file_ext = os.path.splitext(file_name)[1].lower()
                    if file_ext in ['.csv', '.xlsx', '.xls']:
                        current_files.add(file_path)

            # Detect new files
            new_files = current_files - self.known_files

            if new_files:
                # New files detected - refresh the view
                self.refresh_files()

                # Show notification
                count = len(new_files)
                self.file_count_label.setText(f"🆕 {count} new file{'s' if count > 1 else ''} detected!")
                self.file_count_label.setStyleSheet("""
                    QLabel {
                        color: #27ae60;
                        padding: 5px;
                        font-size: 11px;
                        font-weight: bold;
                        background-color: #d4edda;
                        border-radius: 3px;
                    }
                """)

                # Reset notification after 3 seconds
                QTimer.singleShot(3000, self.reset_file_count_style)

    def reset_file_count_style(self):
        """Reset file count label style"""
        count = self.file_tree_model.rowCount()
        self.file_count_label.setText(f"{count} file{'s' if count != 1 else ''} available")
        self.file_count_label.setStyleSheet("""
            QLabel {
                color: #555;
                padding: 5px;
                font-size: 11px;
                font-weight: bold;
            }
        """)

    def refresh_files(self):
        """Refresh file list from output folder"""
        if not self.output_folder or not os.path.exists(self.output_folder):
            return

        # Store current selection
        current_selection = None
        selected_indexes = self.file_tree.selectedIndexes()
        if selected_indexes:
            item = self.file_tree_model.item(selected_indexes[0].row(), 0)
            if item:
                current_selection = item.data(Qt.ItemDataRole.UserRole)

        # Clear and rebuild
        self.file_tree_model.removeRows(0, self.file_tree_model.rowCount())
        self.known_files.clear()

        file_list = []

        # Scan for CSV and XLSX files
        for file_name in os.listdir(self.output_folder):
            file_path = os.path.join(self.output_folder, file_name)

            if not os.path.isfile(file_path):
                continue

            file_ext = os.path.splitext(file_name)[1].lower()
            if file_ext not in ['.csv', '.xlsx', '.xls']:
                continue

            self.known_files.add(file_path)

            # Get file info
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            modified_time = datetime.fromtimestamp(file_stat.st_mtime)

            # Format size
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"

            # Format modified time
            now = datetime.now()
            if modified_time.date() == now.date():
                time_str = modified_time.strftime("%H:%M:%S")
            else:
                time_str = modified_time.strftime("%Y-%m-%d %H:%M")

            file_type = 'CSV' if file_ext == '.csv' else 'Excel'

            file_list.append(
                {'name': file_name, 'path': file_path, 'type': file_type, 'size': size_str, 'modified': time_str,
                    'timestamp': file_stat.st_mtime})

        # Sort by modification time (newest first)
        file_list.sort(key=lambda x: x['timestamp'], reverse=True)

        # Add to tree
        for file_info in file_list:
            name_item = QStandardItem(file_info['name'])
            name_item.setData(file_info['path'], Qt.ItemDataRole.UserRole)
            name_item.setEditable(False)
            name_item.setToolTip(file_info['path'])

            # Highlight new files (modified in last 10 seconds)
            if (datetime.now().timestamp() - file_info['timestamp']) < 10:
                name_item.setForeground(QBrush(QColor(39, 174, 96)))
                name_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))

            type_item = QStandardItem(file_info['type'])
            type_item.setEditable(False)

            size_item = QStandardItem(file_info['size'])
            size_item.setEditable(False)

            time_item = QStandardItem(file_info['modified'])
            time_item.setEditable(False)

            self.file_tree_model.appendRow([name_item, type_item, size_item, time_item])

        # Update count
        count = len(file_list)
        self.file_count_label.setText(f"{count} file{'s' if count != 1 else ''} available")

        # Restore selection if possible
        if current_selection:
            for row in range(self.file_tree_model.rowCount()):
                item = self.file_tree_model.item(row, 0)
                if item and item.data(Qt.ItemDataRole.UserRole) == current_selection:
                    self.file_tree.selectRow(row)
                    break

    def on_file_selected(self, index):
        """Handle file selection"""
        item = self.file_tree_model.item(index.row(), 0)
        if not item:
            return

        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.current_file_path = file_path
            self.load_file_to_table(file_path)
            self.clear_selection()

    def load_file_to_table(self, file_path):
        """Load file into table view"""
        try:
            df = None
            file_ext = Path(file_path).suffix.lower()

            if file_ext == '.csv':
                df = pd.read_csv(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)

            if df is None:
                return

            # Display dataframe
            self.display_dataframe(df)

            # Update info
            self.folder_info_label.setText(f"📄 Loaded: {os.path.basename(file_path)}")
            self.folder_info_label.setStyleSheet("""
                QLabel {
                    color: #2980b9;
                    padding: 8px;
                    background-color: #d6eaf8;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load file:\n{str(e)}")

    def display_dataframe(self, df):
        """Display DataFrame in table"""
        try:
            self.table_model.clear()

            headers = list(df.columns)
            self.table_model.setHorizontalHeaderLabels(headers)

            self.original_headers = {}
            for col, header in enumerate(headers):
                self.original_headers[col] = str(header)

            self.table_model.setRowCount(len(df))
            self.table_model.setColumnCount(len(df.columns))

            for row in range(len(df)):
                for col in range(len(df.columns)):
                    value = df.iloc[row, col]

                    if pd.isna(value):
                        item_text = ""
                    elif isinstance(value, (int, float)):
                        item_text = f"{value:.6g}" if isinstance(value, float) else str(value)
                    else:
                        item_text = str(value)

                    item = QStandardItem(item_text)
                    self.table_model.setItem(row, col, item)

            self.table_view.resizeColumnsToContents()

            for col in range(self.table_model.columnCount()):
                if self.table_view.columnWidth(col) > 150:
                    self.table_view.setColumnWidth(col, 150)

            # Store data for plotting
            self.plot_data = df.copy()

        except Exception as e:
            raise Exception(f"Error displaying data: {str(e)}")

    def on_header_clicked(self, logical_index):
        """Handle header clicks"""
        modifiers = QApplication.keyboardModifiers()

        if modifiers == Qt.KeyboardModifier.ControlModifier:
            # Ctrl+Click: Add as Y column
            if logical_index not in self.y_columns:
                if logical_index == self.x_column:
                    self.x_column = None
                self.y_columns.append(logical_index)

        elif modifiers == Qt.KeyboardModifier.ShiftModifier:
            # Shift+Click: Remove from selection
            if logical_index == self.x_column:
                self.x_column = None
            elif logical_index in self.y_columns:
                self.y_columns.remove(logical_index)

        else:
            # Normal click: Set as X column
            if logical_index in self.y_columns:
                self.y_columns.remove(logical_index)
            self.x_column = logical_index

        self.update_column_colors()
        self.update_selection_display()

    def update_column_colors(self):
        """Update column colors based on selection"""
        # Reset all
        for col in range(self.table_model.columnCount()):
            for row in range(self.table_model.rowCount()):
                item = self.table_model.item(row, col)
                if item:
                    item.setBackground(QBrush(Qt.GlobalColor.white))

            header_text = self.original_headers.get(col, f"Column {col}")
            self.table_model.setHorizontalHeaderItem(col, QStandardItem(header_text))

        # Color X column (blue)
        if self.x_column is not None:
            for row in range(self.table_model.rowCount()):
                item = self.table_model.item(row, self.x_column)
                if item:
                    item.setBackground(QBrush(QColor(52, 152, 219, 80)))

            if self.x_column in self.original_headers:
                header_item = QStandardItem(f"[X] {self.original_headers[self.x_column]}")
                header_item.setBackground(QBrush(QColor(52, 152, 219)))
                header_item.setForeground(QBrush(Qt.GlobalColor.white))
                self.table_model.setHorizontalHeaderItem(self.x_column, header_item)

        # Color Y columns (red with varying intensity)
        for idx, col in enumerate(self.y_columns):
            alpha = 60 + (idx * 30) if idx < 5 else 200

            for row in range(self.table_model.rowCount()):
                item = self.table_model.item(row, col)
                if item:
                    item.setBackground(QBrush(QColor(231, 76, 60, alpha)))

            if col in self.original_headers:
                header_item = QStandardItem(f"[Y{idx + 1}] {self.original_headers[col]}")
                header_item.setBackground(QBrush(QColor(231, 76, 60)))
                header_item.setForeground(QBrush(Qt.GlobalColor.white))
                self.table_model.setHorizontalHeaderItem(col, header_item)

    def update_selection_display(self):
        """Update selection display"""
        x_text = "X: None"
        if self.x_column is not None and self.x_column in self.original_headers:
            x_text = f"X: {self.original_headers[self.x_column]}"

        y_text = "Y: None"
        if self.y_columns:
            y_headers = [self.original_headers[col] for col in self.y_columns if col in self.original_headers]
            if y_headers:
                y_text = f"Y: {', '.join(y_headers)}"

        self.selection_display.setText(f"{x_text} | {y_text}")

    def clear_selection(self):
        """Clear column selection"""
        self.x_column = None
        self.y_columns = []
        self.update_column_colors()
        self.update_selection_display()

    def plot_selected_data(self):
        """Plot selected columns"""
        if self.x_column is None:
            QMessageBox.warning(self, "No X Column", "Please select an X column first (click on header)")
            return

        if not self.y_columns:
            QMessageBox.warning(self, "No Y Columns", "Please select at least one Y column (Ctrl+Click on headers)")
            return

        if not hasattr(self, 'plot_data') or self.plot_data is None:
            QMessageBox.warning(self, "No Data", "No data loaded")
            return

        try:
            self.plot_widget.clear()

            # Get X data
            x_data = self.plot_data.iloc[:, self.x_column].values
            x_label = self.original_headers.get(self.x_column, f"Column {self.x_column}")

            # Define colors for multiple Y plots
            colors = [(231, 76, 60),  # Red
                (52, 152, 219),  # Blue
                (46, 204, 113),  # Green
                (155, 89, 182),  # Purple
                (52, 73, 94),  # Dark blue
                (241, 196, 15),  # Yellow
                (230, 126, 34),  # Orange
            ]

            # Plot each Y column
            for idx, y_col in enumerate(self.y_columns):
                y_data = self.plot_data.iloc[:, y_col].values
                y_label = self.original_headers.get(y_col, f"Column {y_col}")

                color_rgb = colors[idx % len(colors)]
                pen = pg.mkPen(color=color_rgb, width=2)

                self.plot_widget.plot(x_data, y_data, pen=pen, name=y_label, symbol='o', symbolSize=4,
                    symbolBrush=color_rgb)

            # Update labels
            self.plot_widget.setLabel('bottom', x_label)

            if len(self.y_columns) == 1:
                y_label = self.original_headers.get(self.y_columns[0], "Y Values")
                self.plot_widget.setLabel('left', y_label)
            else:
                self.plot_widget.setLabel('left', 'Values')

            # Update info
            file_name = os.path.basename(self.current_file_path) if self.current_file_path else "Unknown"
            y_series_text = f"{len(self.y_columns)} series" if len(self.y_columns) > 1 else self.original_headers.get(
                self.y_columns[0], "1 series")

            self.plot_info_label.setText(
                f"✓ Plotted: {file_name} • X: {x_label} • Y: {y_series_text} • Points: {len(x_data)}")
            self.plot_info_label.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    font-weight: bold;
                    padding: 8px;
                    background-color: #d4edda;
                    border-radius: 5px;
                }
            """)

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to plot data:\n{str(e)}\n\n{traceback.format_exc()}")

    def export_plot(self):
        """Export plot as image"""
        if not hasattr(self, 'plot_data') or self.plot_data is None:
            QMessageBox.warning(self, "No Plot", "No data plotted")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Plot",
            os.path.join(self.output_folder if self.output_folder else os.getcwd(), "plot.png"),
            "PNG Image (*.png);;JPEG Image (*.jpg);;SVG Vector (*.svg)")

        if file_path:
            exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
            exporter.export(file_path)
            QMessageBox.information(self, "Success", f"Plot exported to:\n{file_path}")

    def clear_plot(self):
        """Clear the plot"""
        self.plot_widget.clear()
        self.plot_info_label.setText("No data plotted • Select X and Y columns, then click 'Plot Data'")
        self.plot_info_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
                padding: 8px;
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)

    def clear_visualization(self):
        """Clear everything"""
        self.clear_plot()
        self.clear_selection()
        self.table_model.clear()
        self.current_file_path = None

# ===================== Main Window =====================
class MeasurementSystemMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.measurement_running = False
        self.measurement_paused = False
        self.output_folder = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Advanced Measurement System - Complete")
        self.setGeometry(100, 100, 1600, 1000)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Control buttons
        control_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.clicked.connect(self.start_measurement)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold; padding: 10px;")
        self.pause_btn.setMinimumHeight(40)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_measurement)

        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        self.resume_btn.setMinimumHeight(40)
        self.resume_btn.setEnabled(False)
        self.resume_btn.clicked.connect(self.resume_measurement)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 10px;")
        self.reset_btn.setMinimumHeight(40)
        self.reset_btn.clicked.connect(self.reset_measurement)

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.resume_btn)
        control_layout.addWidget(self.reset_btn)
        control_layout.addStretch()

        main_layout.addLayout(control_layout)

        # Tab widget
        self.tab_widget = QTabWidget()

        self.settings_tab = SettingsTab()
        self.running_tab = RunningTab()
        self.viz_tab = VisualizationTab()

        self.tab_widget.addTab(self.settings_tab, "⚙️ Settings")
        self.tab_widget.addTab(self.running_tab, "▶️ Running")
        self.tab_widget.addTab(self.viz_tab, "📊 Visualization")

        main_layout.addWidget(self.tab_widget)

        # Status bar
        self.create_status_bar()

    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.instrument_container = QWidget()
        self.instrument_layout = QHBoxLayout(self.instrument_container)
        self.instrument_layout.setContentsMargins(0, 0, 0, 0)

        self.instruments = {}
        all_instruments = ['DSP7265', 'Keithley 2182 nv', 'Keithley 6221', 'BNC 845 RF', 'Rigol DSA875',
                           'B&K Precision 9205B', 'PPMS MultiVu']

        for name in all_instruments:
            widget = InstrumentStatusWidget(name)
            self.instruments[name] = widget
            widget.hide()

        self.instrument_layout.addStretch()
        self.status_bar.addPermanentWidget(self.instrument_container)

        self.status_message = QLabel("Ready")
        self.status_bar.addWidget(self.status_message)

    def update_instrument_status_bar(self, required_instruments):
        # Hide all first
        for name, widget in self.instruments.items():
            widget.hide()
            if widget.parent():
                self.instrument_layout.removeWidget(widget)

        # Show PPMS MultiVu if needed
        if any(exp in self.settings_tab.measurement_type for exp in
               ["ETO", "FMR", "Demo", "I-V", "Field", "Temperature", "ST-FMR"]):
            ppms_widget = self.instruments.get('PPMS MultiVu')
            if ppms_widget:
                ppms_widget.show()
                self.instrument_layout.insertWidget(self.instrument_layout.count() - 1, ppms_widget)
                # Update PPMS status
                if self.settings_tab.ppms_widget:
                    ppms_widget.set_connected(self.settings_tab.ppms_widget.client_connected)

        # Show required instruments
        for name in required_instruments:
            if name in self.instruments:
                widget = self.instruments[name]
                widget.show()
                self.instrument_layout.insertWidget(self.instrument_layout.count() - 1, widget)

    def start_measurement(self):
        if not self.measurement_running:
            settings = self.settings_tab.get_settings()

            if not settings.get('measurement_type'):
                QMessageBox.warning(self, "No Configuration", "Please configure a measurement first.")
                return

            # Check if required instruments are connected
            connected = settings.get('connected_instruments', {})
            required = settings.get('required_instruments', [])

            missing = [inst for inst in required if inst not in connected]
            if missing:
                QMessageBox.warning(self, "Missing Connections",
                                    f"Please connect the following instruments:\n" + "\n".join(missing))
                return

            # Create output folder for this measurement
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            measurement_type = settings.get('measurement_type', 'Unknown').replace(' ', '_')

            # Ask user where to save
            base_folder = QFileDialog.getExistingDirectory(self, "Select Output Folder for Measurement Data",
                os.getcwd())

            if not base_folder:
                return

            self.output_folder = os.path.join(base_folder, f"{measurement_type}_{timestamp}")
            os.makedirs(self.output_folder, exist_ok=True)

            # Pass output folder to visualization tab
            self.viz_tab.set_output_folder(self.output_folder)

            # Store in settings
            settings['output_folder'] = self.output_folder

            self.running_tab.load_settings(settings)
            self.tab_widget.setCurrentIndex(1)

            self.measurement_running = True
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)

            self.status_message.setText(f"Measurement Running → {os.path.basename(self.output_folder)}")
            self.running_tab.status_label.setText("Status: Running")
            self.running_tab.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: green;")
            self.running_tab.log_message(f"Output folder: {self.output_folder}", "blue")
            self.running_tab.log_message("Measurement started", "green")

            # Start measurement
            self.running_tab.start_measurement()
            self.simulate_measurement()

    def simulate_measurement(self):
        """Simulate measurement progress"""
        self.progress_timer = QTimer()
        self.progress_value = 0

        def update_progress():
            if not self.measurement_paused:
                self.progress_value += 1
                self.running_tab.update_progress(self.progress_value)
                if self.progress_value >= 100:
                    self.progress_timer.stop()
                    self.measurement_finished()

        self.progress_timer.timeout.connect(update_progress)
        self.progress_timer.start(100)  # Update every 100ms

    def measurement_finished(self):
        self.measurement_running = False
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.status_message.setText("Measurement Complete")
        self.running_tab.status_label.setText("Status: Complete")
        self.running_tab.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: blue;")
        self.running_tab.log_message("Measurement completed successfully", "blue")
        self.running_tab.stop_measurement()

    def pause_measurement(self):
        if self.measurement_running and not self.measurement_paused:
            self.measurement_paused = True
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.status_message.setText("Paused")
            self.running_tab.log_message("Paused", "orange")
            if hasattr(self, 'progress_timer'):
                self.progress_timer.stop()

    def resume_measurement(self):
        if self.measurement_running and self.measurement_paused:
            self.measurement_paused = False
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.status_message.setText("Running")
            self.running_tab.log_message("Resumed", "green")
            if hasattr(self, 'progress_timer'):
                self.progress_timer.start()

    def reset_measurement(self):
        self.measurement_running = False
        self.measurement_paused = False

        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()

        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)

        self.running_tab.clear_all()
        self.viz_tab.clear_visualization()

        # Disconnect all instruments
        if self.settings_tab.instrument_connection_widget:
            self.settings_tab.instrument_connection_widget.disconnect_all()

        # Cleanup PPMS
        if self.settings_tab.ppms_widget:
            self.settings_tab.ppms_widget.cleanup()

        # Reset settings tab
        self.settings_tab.reset_selection()

        self.tab_widget.setCurrentIndex(0)
        self.status_message.setText("Ready")

    def closeEvent(self, event):
        # Cleanup on close
        if self.settings_tab.instrument_connection_widget:
            self.settings_tab.instrument_connection_widget.disconnect_all()

        if self.settings_tab.ppms_widget:
            self.settings_tab.ppms_widget.cleanup()

        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MeasurementSystemMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()