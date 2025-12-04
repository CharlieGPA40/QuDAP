from PyQt6.QtWidgets import (QWidget, QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import pyqtSignal, Qt
import pyvisa as visa


class InstrumentConnection(QWidget):
    """
    Standalone instrument connection widget that can be reused across different tabs.

    Signals:
        instrument_connected: Emitted when an instrument is successfully connected
        instrument_disconnected: Emitted when an instrument is disconnected
    """

    instrument_connected = pyqtSignal(object, str)  # (instrument, instrument_name)
    instrument_disconnected = pyqtSignal(str)  # instrument_name

    # RS232 Presets for known instruments
    INSTRUMENT_RS232_PRESETS = {
        'BNC 845 RF': {'baud_rate': 115200, 'data_bits': 8, 'parity': 'None', 'stop_bits': 1.0, 'flow_control': 'None'},
        'DSP 7265 Lock-in': {'baud_rate': 9600, 'data_bits': 8, 'parity': 'None', 'stop_bits': 1.0,
            'flow_control': 'None'},
        'Keithley 2182 nv': {'baud_rate': 9600, 'data_bits': 8, 'parity': 'None', 'stop_bits': 1.0,
            'flow_control': 'None'},
        'Keithley 6221': {'baud_rate': 9600, 'data_bits': 8, 'parity': 'None', 'stop_bits': 1.0,
            'flow_control': 'None'},
        'Rigol DSA875': {'baud_rate': 9600, 'data_bits': 8, 'parity': 'None', 'stop_bits': 1.0, 'flow_control': 'None'}}

    def __init__(self, instrument_list=None, allow_emulation=True, title="Instrument Connection", parent=None):
        """
        Initialize the connection widget.

        Args:
            instrument_list: List of instrument names to show in combo box
            allow_emulation: Whether to show "Emulation" option
            title: Title for the group box
            parent: Parent widget
        """
        super().__init__(parent)

        self.instrument_list = instrument_list or ["BNC 845 RF", "DSP 7265 Lock-in"]
        self.allow_emulation = allow_emulation
        self.title = title

        self.rm = None
        self.current_instrument = None
        self.current_instrument_name = None
        self.is_connected = False

        self.font = QFont("Arial", 10)

        # Load stylesheets
        try:
            with open("GUI/QSS/QComboWidget.qss", "r") as file:
                self.combo_stylesheet = file.read()
            with open("GUI/QSS/QButtonWidget.qss", "r") as file:
                self.button_stylesheet = file.read()
        except:
            self.combo_stylesheet = ""
            self.button_stylesheet = ""

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()

        # Group box
        self.connection_group = QGroupBox(self.title)
        connection_layout = QVBoxLayout()

        # Instrument selection
        instru_select_layout = QHBoxLayout()
        instru_label = QLabel("Select Instrument:")
        instru_label.setFont(self.font)
        instru_label.setMinimumWidth(140)

        self.instru_combo = QComboBox()
        self.instru_combo.setFont(self.font)
        # self.instru_combo.setStyleSheet(self.combo_stylesheet)
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
        # self.connection_combo.setStyleSheet(self.combo_stylesheet)
        self.connection_combo.currentIndexChanged.connect(self.on_connection_changed)

        self.refresh_btn = QPushButton(icon=QIcon("GUI/Icon/refresh.svg"))
        self.refresh_btn.clicked.connect(self.refresh_connections)
        self.refresh_btn.setStyleSheet(self.button_stylesheet)
        self.refresh_btn.setMaximumWidth(30)

        conn_select_layout.addWidget(conn_label)
        conn_select_layout.addWidget(self.connection_combo, 3)
        conn_select_layout.addWidget(self.refresh_btn)
        connection_layout.addLayout(conn_select_layout)

        # RS232 settings (initially hidden)
        self.rs232_layout = QVBoxLayout()
        connection_layout.addLayout(self.rs232_layout)

        # Connect button
        button_layout = QHBoxLayout()
        self.connect_btn = QPushButton('Connect')
        self.connect_btn.clicked.connect(self.toggle_connection)
        # self.connect_btn.setStyleSheet(self.button_stylesheet)
        self.connect_btn.setMinimumHeight(30)
        self.connect_btn.setFont(self.font)
        button_layout.addWidget(self.connect_btn)
        connection_layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("Status: Not Connected")
        self.status_label.setFont(self.font)
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        connection_layout.addWidget(self.status_label)

        self.connection_group.setLayout(connection_layout)
        main_layout.addWidget(self.connection_group)
        self.setLayout(main_layout)

        # Initial refresh
        self.refresh_connections()

    def on_instrument_changed(self, index):
        """Handle instrument selection change"""
        if index == 0:  # "Select Instrument"
            self.connect_btn.setEnabled(False)
        else:
            self.connect_btn.setEnabled(True)

    def on_connection_changed(self, index):
        """Handle connection selection change"""
        connection_string = self.connection_combo.currentText()

        # Check if RS232/COM port
        if "ASRL" in connection_string or "COM" in connection_string:
            self.show_rs232_settings()

            # Apply preset if available
            instrument_name = self.instru_combo.currentText()
            if instrument_name in self.INSTRUMENT_RS232_PRESETS:
                self.apply_rs232_preset(instrument_name)
        else:
            self.hide_rs232_settings()

    def refresh_connections(self):
        """Refresh available connections"""
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
            QMessageBox.warning(self, "Error", f"Error refreshing connections:\n{str(e)}")

    def show_rs232_settings(self):
        """Show RS232 configuration options"""
        self.clear_layout(self.rs232_layout)

        rs232_widget = QWidget()
        rs232_main_layout = QVBoxLayout()

        # Row 1: Baud Rate and Data Bits
        row1_layout = QHBoxLayout()

        baud_label = QLabel("Baud:")
        baud_label.setFont(self.font)
        self.baud_combo = QComboBox()
        self.baud_combo.setFont(self.font)
        # self.baud_combo.setStyleSheet(self.combo_stylesheet)
        self.baud_combo.addItems(["300", "1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"])
        self.baud_combo.setCurrentText("9600")

        data_label = QLabel("Data:")
        data_label.setFont(self.font)
        self.data_bits_combo = QComboBox()
        self.data_bits_combo.setFont(self.font)
        # self.data_bits_combo.setStyleSheet(self.combo_stylesheet)
        self.data_bits_combo.addItems(["5", "6", "7", "8"])
        self.data_bits_combo.setCurrentText("8")

        row1_layout.addWidget(baud_label)
        row1_layout.addWidget(self.baud_combo)
        row1_layout.addWidget(data_label)
        row1_layout.addWidget(self.data_bits_combo)

        # Row 2: Parity and Stop Bits
        row2_layout = QHBoxLayout()

        parity_label = QLabel("Parity:")
        parity_label.setFont(self.font)
        self.parity_combo = QComboBox()
        # self.parity_combo.setFont(self.font)
        # self.parity_combo.setStyleSheet(self.combo_stylesheet)
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.parity_combo.setCurrentText("None")

        stop_label = QLabel("Stop:")
        stop_label.setFont(self.font)
        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.setFont(self.font)
        # self.stop_bits_combo.setStyleSheet(self.combo_stylesheet)
        self.stop_bits_combo.addItems(["1", "1.5", "2"])
        self.stop_bits_combo.setCurrentText("1")

        row2_layout.addWidget(parity_label)
        row2_layout.addWidget(self.parity_combo)
        row2_layout.addWidget(stop_label)
        row2_layout.addWidget(self.stop_bits_combo)

        # Row 3: Flow Control
        row3_layout = QHBoxLayout()

        flow_label = QLabel("Flow Control:")
        flow_label.setFont(self.font)
        self.flow_combo = QComboBox()
        self.flow_combo.setFont(self.font)
        # self.flow_combo.setStyleSheet(self.combo_stylesheet)
        self.flow_combo.addItems(["None", "Hardware (RTS/CTS)", "Software (XON/XOFF)"])
        self.flow_combo.setCurrentText("None")

        row3_layout.addWidget(flow_label)
        row3_layout.addWidget(self.flow_combo)

        rs232_main_layout.addLayout(row1_layout)
        rs232_main_layout.addLayout(row2_layout)
        rs232_main_layout.addLayout(row3_layout)

        rs232_widget.setLayout(rs232_main_layout)
        self.rs232_layout.addWidget(rs232_widget)

    def hide_rs232_settings(self):
        """Hide RS232 configuration options"""
        self.clear_layout(self.rs232_layout)

    def apply_rs232_preset(self, instrument_name):
        """Apply RS232 preset for instrument"""
        if instrument_name in self.INSTRUMENT_RS232_PRESETS and hasattr(self, 'baud_combo'):
            preset = self.INSTRUMENT_RS232_PRESETS[instrument_name]
            self.baud_combo.setCurrentText(str(preset['baud_rate']))
            self.data_bits_combo.setCurrentText(str(preset['data_bits']))
            self.parity_combo.setCurrentText(preset['parity'])
            self.stop_bits_combo.setCurrentText(str(preset['stop_bits']))
            self.flow_combo.setCurrentText(preset['flow_control'])

    def get_rs232_settings(self):
        """Get current RS232 settings"""
        if not hasattr(self, 'baud_combo'):
            return None

        return {'baud_rate': int(self.baud_combo.currentText()), 'data_bits': int(self.data_bits_combo.currentText()),
            'parity': self.parity_combo.currentText(), 'stop_bits': float(self.stop_bits_combo.currentText()),
            'flow_control': self.flow_combo.currentText()}

    def toggle_connection(self):
        """Toggle connection state"""
        if not self.is_connected:
            self.connect_instrument()
        else:
            self.disconnect_instrument()

    def connect_instrument(self):
        """Connect to selected instrument"""
        instrument_name = self.instru_combo.currentText()
        connection_string = self.connection_combo.currentText()

        if instrument_name == "Select Instrument" or connection_string == "None":
            QMessageBox.warning(self, "Invalid Selection", "Please select both instrument and connection.")
            return

        try:
            self.status_label.setText(f"Connecting to {instrument_name}...")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")

            if connection_string == "Emulation":
                # Emulation mode
                self.current_instrument = None
                self.current_instrument_name = instrument_name
                self.is_connected = True

                self.status_label.setText(f"Connected: {instrument_name} (Emulation)")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.connect_btn.setText("Disconnect")

                self.instrument_connected.emit(None, instrument_name)

            else:
                # Real instrument
                if not self.rm:
                    self.rm = visa.ResourceManager()

                instrument = self.rm.open_resource(connection_string)
                instrument.timeout = 10000

                # Configure RS232 if applicable
                if "ASRL" in connection_string or "COM" in connection_string:
                    settings = self.get_rs232_settings()
                    if settings:
                        instrument.baud_rate = settings['baud_rate']
                        instrument.data_bits = settings['data_bits']

                        # Set parity
                        parity_map = {'None': visa.constants.Parity.none, 'Even': visa.constants.Parity.even,
                            'Odd': visa.constants.Parity.odd, 'Mark': visa.constants.Parity.mark,
                            'Space': visa.constants.Parity.space}
                        instrument.parity = parity_map[settings['parity']]

                        # Set stop bits
                        stopbits_map = {1.0: visa.constants.StopBits.one, 1.5: visa.constants.StopBits.one_and_a_half,
                            2.0: visa.constants.StopBits.two}
                        instrument.stop_bits = stopbits_map[settings['stop_bits']]

                        # Set flow control
                        if settings['flow_control'] == 'Hardware (RTS/CTS)':
                            instrument.flow_control = visa.constants.ControlFlow.rts_cts
                        elif settings['flow_control'] == 'Software (XON/XOFF)':
                            instrument.flow_control = visa.constants.ControlFlow.xon_xoff
                        else:
                            instrument.flow_control = visa.constants.ControlFlow.none

                # Test connection
                try:
                    idn = instrument.query('*IDN?')
                    self.current_instrument = instrument
                    self.current_instrument_name = instrument_name
                    self.is_connected = True

                    self.status_label.setText(f"Connected: {idn.strip()}")
                    self.status_label.setStyleSheet("color: green; font-weight: bold;")
                    self.connect_btn.setText("Disconnect")

                    self.instrument_connected.emit(instrument, instrument_name)

                except:
                    # Some instruments don't support *IDN?
                    self.current_instrument = instrument
                    self.current_instrument_name = instrument_name
                    self.is_connected = True

                    self.status_label.setText(f"Connected: {instrument_name}")
                    self.status_label.setStyleSheet("color: green; font-weight: bold;")
                    self.connect_btn.setText("Disconnect")

                    self.instrument_connected.emit(instrument, instrument_name)

        except Exception as e:
            self.status_label.setText("Connection failed")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to {instrument_name}:\n{str(e)}")

    def disconnect_instrument(self):
        """Disconnect from instrument"""
        try:
            if self.current_instrument:
                self.current_instrument.close()

            instrument_name = self.current_instrument_name

            self.current_instrument = None
            self.current_instrument_name = None
            self.is_connected = False

            self.status_label.setText("Status: Not Connected")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_btn.setText("Connect")

            self.instrument_disconnected.emit(instrument_name)

        except Exception as e:
            QMessageBox.warning(self, "Disconnect Error", f"Error disconnecting:\n{str(e)}")

    def get_instrument(self):
        """Get current instrument object"""
        return self.current_instrument

    def get_instrument_name(self):
        """Get current instrument name"""
        return self.current_instrument_name

    def is_instrument_connected(self):
        """Check if instrument is connected"""
        return self.is_connected

    def clear_layout(self, layout):
        """Clear all widgets from layout"""
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()

            if widget:
                widget.setParent(None)
                widget.deleteLater()
            else:
                child_layout = item.layout()
                if child_layout:
                    self.clear_layout(child_layout)