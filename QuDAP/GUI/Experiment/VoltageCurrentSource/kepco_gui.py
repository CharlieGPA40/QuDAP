from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
                             QPushButton, QComboBox, QCheckBox, QLineEdit, QMessageBox, QScrollArea, QSizePolicy,
                             QDoubleSpinBox, QRadioButton, QButtonGroup, QTabWidget, QSpinBox)
from PyQt6.QtGui import QFont, QDoubleValidator, QIntValidator
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import sys
import pyvisa as visa
import time
import numpy as np
import pyqtgraph as pg

# Import the standalone connection class and KEPCO commands
try:
    from instrument.instrument_connection import InstrumentConnection
    from instrument.kepco import KEPCO_COMMAND
except ImportError:
    from QuDAP.instrument.instrument_connection import InstrumentConnection
    from QuDAP.instrument.kepco import KEPCO_COMMAND


class ReadingThread(QThread):
    """Thread for continuous reading updates when connected"""

    reading_signal = pyqtSignal(dict)  # {voltage, current, output_state}
    error_signal = pyqtSignal(str)

    def __init__(self, instrument, kepco_cmd, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.kepco_cmd = kepco_cmd
        self.should_stop = False

    def run(self):
        """Continuously read voltage and current"""
        try:
            while not self.should_stop:
                try:
                    # Measure voltage and current
                    voltage = float(self.kepco_cmd.measure_voltage(self.instrument).strip())
                    current = float(self.kepco_cmd.measure_current(self.instrument).strip())
                    output_state = self.kepco_cmd.get_output_state(self.instrument).strip()

                    readings = {'voltage': voltage, 'current': current, 'output_state': output_state,
                        'power': voltage * current}

                    self.reading_signal.emit(readings)
                    time.sleep(1)

                except Exception as e:
                    if not self.should_stop:
                        self.error_signal.emit(f"Reading error: {str(e)}")
                    break

        except Exception as e:
            self.error_signal.emit(f"Thread error: {str(e)}")

    def stop(self):
        """Stop reading"""
        self.should_stop = True


class EmulationThread(QThread):
    """Thread for emulation mode readings"""

    reading_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.should_stop = False
        self.voltage = 12.0
        self.current = 1.0

    def run(self):
        """Generate emulated readings"""
        while not self.should_stop:
            readings = {'voltage': self.voltage + np.random.randn() * 0.01,
                'current': self.current + np.random.randn() * 0.001, 'output_state': '1',
                'power': self.voltage * self.current}
            self.reading_signal.emit(readings)
            time.sleep(1)

    def stop(self):
        """Stop emulation"""
        self.should_stop = True


class MonitorThread(QThread):
    """Thread for monitoring and plotting"""

    data_signal = pyqtSignal(float, dict)  # (time, readings)
    error_signal = pyqtSignal(str)

    def __init__(self, instrument, kepco_cmd, is_emulation=False, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.kepco_cmd = kepco_cmd
        self.is_emulation = is_emulation
        self.should_stop = False
        self.start_time = time.time()

        # Emulation values
        self.voltage = 12.0
        self.current = 1.0

    def run(self):
        """Monitor readings for plotting"""
        try:
            while not self.should_stop:
                try:
                    elapsed_time = time.time() - self.start_time

                    if self.is_emulation:
                        # Generate simulated data
                        readings = {'voltage': self.voltage + np.random.randn() * 0.01,
                            'current': self.current + np.random.randn() * 0.001}
                    else:
                        # Read actual values
                        voltage = float(self.kepco_cmd.measure_voltage(self.instrument).strip())
                        current = float(self.kepco_cmd.measure_current(self.instrument).strip())

                        readings = {'voltage': voltage, 'current': current}

                    self.data_signal.emit(elapsed_time, readings)
                    time.sleep(0.1)  # 100ms update rate

                except Exception as e:
                    if not self.should_stop:
                        self.error_signal.emit(f"Monitor error: {str(e)}")
                    break

        except Exception as e:
            self.error_signal.emit(f"Monitor thread error: {str(e)}")

    def stop(self):
        """Stop monitoring"""
        self.should_stop = True


class KEPCO(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KEPCO KLP Series Power Supply")
        self.setGeometry(100, 100, 1600, 900)

        self.kepco = None
        self.kepco_cmd = KEPCO_COMMAND()
        self.reading_thread = None
        self.monitor_thread = None
        self.emulation_thread = None
        self.isConnect = False
        self.output_on = False

        # Data storage for plotting
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.power_data = []
        self.max_points = 10000

        self.font = QFont("Arial", 10)
        self.titlefont = QFont("Arial", 14)
        self.titlefont.setBold(True)

        # Load scrollbar stylesheet
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
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left panel with scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(self.scrollbar_stylesheet)
        self.scroll_area.setFixedWidth(800)

        left_content = QWidget()
        left_content.setMaximumWidth(780)

        self.left_layout = QVBoxLayout()
        self.left_layout.setContentsMargins(10, 10, 10, 10)
        self.left_layout.setSpacing(10)

        # Title
        title = QLabel("KEPCO KLP Series Power Supply")
        title.setFont(self.titlefont)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_layout.addWidget(title)

        # Setup sections
        self.setup_connection_section(self.left_layout)
        self.setup_readings_section(self.left_layout)
        self.setup_basic_control_section(self.left_layout)
        self.setup_protection_section(self.left_layout)
        self.setup_mode_section(self.left_layout)
        self.setup_list_programming_section(self.left_layout)
        self.setup_monitor_section(self.left_layout)

        self.left_layout.addStretch()

        left_content.setLayout(self.left_layout)
        self.scroll_area.setWidget(left_content)

        main_layout.addWidget(self.scroll_area)

        # Right panel with plots
        self.setup_plot_panel(main_layout)

        central_widget.setLayout(main_layout)

    def setup_connection_section(self, parent_layout):
        """Setup device connection section"""
        self.connection_widget = InstrumentConnection(instrument_list=["KEPCO KLP"], allow_emulation=True,
            title="Instrument Connection")
        self.connection_widget.instrument_connected.connect(self.on_instrument_connected)
        self.connection_widget.instrument_disconnected.connect(self.on_instrument_disconnected)
        parent_layout.addWidget(self.connection_widget)

    def setup_readings_section(self, parent_layout):
        """Setup current readings section"""
        readings_group = QGroupBox("Output Readings")
        readings_layout = QVBoxLayout()

        # Voltage Reading
        v_layout = QHBoxLayout()
        v_label = QLabel("Voltage:")
        v_label.setFont(self.font)
        v_label.setFixedWidth(100)
        self.voltage_reading = QLabel("N/A")
        self.voltage_reading.setFont(self.font)
        v_layout.addWidget(v_label)
        v_layout.addWidget(self.voltage_reading, 1)
        readings_layout.addLayout(v_layout)

        # Current Reading
        i_layout = QHBoxLayout()
        i_label = QLabel("Current:")
        i_label.setFont(self.font)
        i_label.setFixedWidth(100)
        self.current_reading = QLabel("N/A")
        self.current_reading.setFont(self.font)
        i_layout.addWidget(i_label)
        i_layout.addWidget(self.current_reading, 1)
        readings_layout.addLayout(i_layout)

        # Power Reading
        p_layout = QHBoxLayout()
        p_label = QLabel("Power:")
        p_label.setFont(self.font)
        p_label.setFixedWidth(100)
        self.power_reading = QLabel("N/A")
        self.power_reading.setFont(self.font)
        p_layout.addWidget(p_label)
        p_layout.addWidget(self.power_reading, 1)
        readings_layout.addLayout(p_layout)

        # Output State
        state_layout = QHBoxLayout()
        state_label = QLabel("Output State:")
        state_label.setFont(self.font)
        state_label.setFixedWidth(100)
        self.state_reading = QLabel("N/A")
        self.state_reading.setFont(self.font)
        state_layout.addWidget(state_label)
        state_layout.addWidget(self.state_reading, 1)
        readings_layout.addLayout(state_layout)

        readings_group.setLayout(readings_layout)
        parent_layout.addWidget(readings_group)

    def setup_basic_control_section(self, parent_layout):
        """Setup basic voltage/current control section"""
        control_group = QGroupBox("Basic Control")
        control_layout = QVBoxLayout()

        # Voltage setting
        v_layout = QHBoxLayout()
        v_label = QLabel("Set Voltage:")
        v_label.setFont(self.font)
        v_label.setFixedWidth(100)

        self.voltage_entry = QLineEdit()
        self.voltage_entry.setFont(self.font)
        self.voltage_entry.setPlaceholderText("Enter voltage")
        self.voltage_validator = QDoubleValidator(0, 1000, 3)
        self.voltage_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.voltage_entry.setValidator(self.voltage_validator)
        self.voltage_entry.setFixedHeight(30)

        v_unit_label = QLabel("V")
        v_unit_label.setFont(self.font)

        v_layout.addWidget(v_label)
        v_layout.addWidget(self.voltage_entry, 1)
        v_layout.addWidget(v_unit_label)
        control_layout.addLayout(v_layout)

        # Current setting
        i_layout = QHBoxLayout()
        i_label = QLabel("Set Current:")
        i_label.setFont(self.font)
        i_label.setFixedWidth(100)

        self.current_entry = QLineEdit()
        self.current_entry.setFont(self.font)
        self.current_entry.setPlaceholderText("Enter current")
        self.current_validator = QDoubleValidator(0, 100, 3)
        self.current_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.current_entry.setValidator(self.current_validator)
        self.current_entry.setFixedHeight(30)

        i_unit_label = QLabel("A")
        i_unit_label.setFont(self.font)

        i_layout.addWidget(i_label)
        i_layout.addWidget(self.current_entry, 1)
        i_layout.addWidget(i_unit_label)
        control_layout.addLayout(i_layout)

        # Set button
        set_btn_layout = QHBoxLayout()
        set_btn_layout.addStretch()
        self.set_values_btn = QPushButton("Set V/I")
        self.set_values_btn.setFont(self.font)
        self.set_values_btn.clicked.connect(self.set_voltage_current)
        self.set_values_btn.setMinimumHeight(35)
        self.set_values_btn.setMinimumWidth(150)
        self.set_values_btn.setEnabled(False)
        set_btn_layout.addWidget(self.set_values_btn)
        set_btn_layout.addStretch()
        control_layout.addLayout(set_btn_layout)

        # Output control
        output_btn_layout = QHBoxLayout()
        output_btn_layout.addStretch()
        self.output_btn = QPushButton("Output ON")
        self.output_btn.setFont(self.font)
        self.output_btn.clicked.connect(self.toggle_output)
        self.output_btn.setMinimumHeight(35)
        self.output_btn.setMinimumWidth(150)
        self.output_btn.setEnabled(False)
        output_btn_layout.addWidget(self.output_btn)
        output_btn_layout.addStretch()
        control_layout.addLayout(output_btn_layout)

        control_group.setLayout(control_layout)
        parent_layout.addWidget(control_group)

    def setup_protection_section(self, parent_layout):
        """Setup overvoltage/overcurrent protection section"""
        protection_group = QGroupBox("Protection Settings")
        protection_layout = QVBoxLayout()

        # Overvoltage Protection
        ovp_layout = QHBoxLayout()
        ovp_label = QLabel("OVP Level:")
        ovp_label.setFont(self.font)
        ovp_label.setFixedWidth(100)

        self.ovp_entry = QLineEdit()
        self.ovp_entry.setFont(self.font)
        self.ovp_entry.setPlaceholderText("Overvoltage protection")
        self.ovp_validator = QDoubleValidator(0, 1000, 3)
        self.ovp_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.ovp_entry.setValidator(self.ovp_validator)
        self.ovp_entry.setFixedHeight(30)

        ovp_unit = QLabel("V")
        ovp_unit.setFont(self.font)

        ovp_layout.addWidget(ovp_label)
        ovp_layout.addWidget(self.ovp_entry, 1)
        ovp_layout.addWidget(ovp_unit)
        protection_layout.addLayout(ovp_layout)

        # Overcurrent Protection
        ocp_layout = QHBoxLayout()
        ocp_label = QLabel("OCP Level:")
        ocp_label.setFont(self.font)
        ocp_label.setFixedWidth(100)

        self.ocp_entry = QLineEdit()
        self.ocp_entry.setFont(self.font)
        self.ocp_entry.setPlaceholderText("Overcurrent protection")
        self.ocp_validator = QDoubleValidator(0, 100, 3)
        self.ocp_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.ocp_entry.setValidator(self.ocp_validator)
        self.ocp_entry.setFixedHeight(30)

        ocp_unit = QLabel("A")
        ocp_unit.setFont(self.font)

        ocp_layout.addWidget(ocp_label)
        ocp_layout.addWidget(self.ocp_entry, 1)
        ocp_layout.addWidget(ocp_unit)
        protection_layout.addLayout(ocp_layout)

        # Set Protection button
        prot_btn_layout = QHBoxLayout()
        prot_btn_layout.addStretch()
        self.set_protection_btn = QPushButton("Set Protection")
        self.set_protection_btn.setFont(self.font)
        self.set_protection_btn.clicked.connect(self.set_protection)
        self.set_protection_btn.setMinimumHeight(35)
        self.set_protection_btn.setMinimumWidth(150)
        self.set_protection_btn.setEnabled(False)
        prot_btn_layout.addWidget(self.set_protection_btn)
        prot_btn_layout.addStretch()
        protection_layout.addLayout(prot_btn_layout)

        protection_group.setLayout(protection_layout)
        parent_layout.addWidget(protection_group)

    def setup_mode_section(self, parent_layout):
        """Setup voltage/current mode section"""
        mode_group = QGroupBox("Operation Mode")
        mode_layout = QVBoxLayout()

        # Function mode selection
        func_layout = QHBoxLayout()
        func_label = QLabel("Function:")
        func_label.setFont(self.font)
        func_label.setFixedWidth(100)

        self.function_mode_combo = QComboBox()
        self.function_mode_combo.setFont(self.font)
        self.function_mode_combo.addItems(["Voltage", "Current"])

        func_layout.addWidget(func_label)
        func_layout.addWidget(self.function_mode_combo, 1)
        mode_layout.addLayout(func_layout)

        # Voltage mode
        v_mode_layout = QHBoxLayout()
        v_mode_label = QLabel("Voltage Mode:")
        v_mode_label.setFont(self.font)
        v_mode_label.setFixedWidth(100)

        self.voltage_mode_combo = QComboBox()
        self.voltage_mode_combo.setFont(self.font)
        self.voltage_mode_combo.addItems(["FIXED", "LIST", "TRIGGERED"])

        v_mode_layout.addWidget(v_mode_label)
        v_mode_layout.addWidget(self.voltage_mode_combo, 1)
        mode_layout.addLayout(v_mode_layout)

        # Current mode
        i_mode_layout = QHBoxLayout()
        i_mode_label = QLabel("Current Mode:")
        i_mode_label.setFont(self.font)
        i_mode_label.setFixedWidth(100)

        self.current_mode_combo = QComboBox()
        self.current_mode_combo.setFont(self.font)
        self.current_mode_combo.addItems(["FIXED", "LIST", "TRIGGERED"])

        i_mode_layout.addWidget(i_mode_label)
        i_mode_layout.addWidget(self.current_mode_combo, 1)
        mode_layout.addLayout(i_mode_layout)

        # Apply Mode button
        mode_btn_layout = QHBoxLayout()
        mode_btn_layout.addStretch()
        self.apply_mode_btn = QPushButton("Apply Modes")
        self.apply_mode_btn.setFont(self.font)
        self.apply_mode_btn.clicked.connect(self.apply_modes)
        self.apply_mode_btn.setMinimumHeight(35)
        self.apply_mode_btn.setMinimumWidth(150)
        self.apply_mode_btn.setEnabled(False)
        mode_btn_layout.addWidget(self.apply_mode_btn)
        mode_btn_layout.addStretch()
        mode_layout.addLayout(mode_btn_layout)

        mode_group.setLayout(mode_layout)
        parent_layout.addWidget(mode_group)

    def setup_list_programming_section(self, parent_layout):
        """Setup list programming section"""
        list_group = QGroupBox("List Programming")
        list_layout = QVBoxLayout()

        # Voltage list
        v_list_layout = QHBoxLayout()
        v_list_label = QLabel("Voltage List:")
        v_list_label.setFont(self.font)
        v_list_label.setFixedWidth(100)

        self.voltage_list_entry = QLineEdit()
        self.voltage_list_entry.setFont(self.font)
        self.voltage_list_entry.setPlaceholderText("e.g., 5,10,15,20")
        self.voltage_list_entry.setFixedHeight(30)

        v_list_layout.addWidget(v_list_label)
        v_list_layout.addWidget(self.voltage_list_entry, 1)
        list_layout.addLayout(v_list_layout)

        # Current list
        i_list_layout = QHBoxLayout()
        i_list_label = QLabel("Current List:")
        i_list_label.setFont(self.font)
        i_list_label.setFixedWidth(100)

        self.current_list_entry = QLineEdit()
        self.current_list_entry.setFont(self.font)
        self.current_list_entry.setPlaceholderText("e.g., 0.5,1.0,1.5,2.0")
        self.current_list_entry.setFixedHeight(30)

        i_list_layout.addWidget(i_list_label)
        i_list_layout.addWidget(self.current_list_entry, 1)
        list_layout.addLayout(i_list_layout)

        # Dwell time list
        dwell_layout = QHBoxLayout()
        dwell_label = QLabel("Dwell Times:")
        dwell_label.setFont(self.font)
        dwell_label.setFixedWidth(100)

        self.dwell_list_entry = QLineEdit()
        self.dwell_list_entry.setFont(self.font)
        self.dwell_list_entry.setPlaceholderText("e.g., 1.0,1.0,1.0,1.0 (seconds)")
        self.dwell_list_entry.setFixedHeight(30)

        dwell_layout.addWidget(dwell_label)
        dwell_layout.addWidget(self.dwell_list_entry, 1)
        list_layout.addLayout(dwell_layout)

        # List count
        count_layout = QHBoxLayout()
        count_label = QLabel("List Count:")
        count_label.setFont(self.font)
        count_label.setFixedWidth(100)

        self.list_count_spin = QSpinBox()
        self.list_count_spin.setFont(self.font)
        self.list_count_spin.setRange(0, 65535)
        self.list_count_spin.setValue(1)
        self.list_count_spin.setFixedHeight(30)

        count_layout.addWidget(count_label)
        count_layout.addWidget(self.list_count_spin, 1)
        list_layout.addLayout(count_layout)

        # List direction
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Direction:")
        dir_label.setFont(self.font)
        dir_label.setFixedWidth(100)

        self.list_direction_combo = QComboBox()
        self.list_direction_combo.setFont(self.font)
        self.list_direction_combo.addItems(["UP", "DOWN"])

        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.list_direction_combo, 1)
        list_layout.addLayout(dir_layout)

        # Buttons
        list_btn_layout = QHBoxLayout()

        self.program_list_btn = QPushButton("Program List")
        self.program_list_btn.setFont(self.font)
        self.program_list_btn.clicked.connect(self.program_list)
        self.program_list_btn.setEnabled(False)

        self.clear_list_btn = QPushButton("Clear List")
        self.clear_list_btn.setFont(self.font)
        self.clear_list_btn.clicked.connect(self.clear_list)
        self.clear_list_btn.setEnabled(False)

        list_btn_layout.addWidget(self.program_list_btn)
        list_btn_layout.addWidget(self.clear_list_btn)
        list_layout.addLayout(list_btn_layout)

        list_group.setLayout(list_layout)
        parent_layout.addWidget(list_group)

    def setup_monitor_section(self, parent_layout):
        """Setup monitoring and data control section"""
        monitor_group = QGroupBox("Real-time Monitoring")
        monitor_layout = QVBoxLayout()

        # Plot parameter selection
        param_layout = QHBoxLayout()
        param_label = QLabel("Plot:")
        param_label.setFont(self.font)
        self.plot_param_combo = QComboBox()
        self.plot_param_combo.setFont(self.font)
        self.plot_param_combo.addItems(["Voltage", "Current", "Power"])
        self.plot_param_combo.currentTextChanged.connect(self.update_plot_display)
        param_layout.addWidget(param_label)
        param_layout.addWidget(self.plot_param_combo, 1)
        monitor_layout.addLayout(param_layout)

        # Start/Stop monitoring
        monitor_btn_layout = QHBoxLayout()
        self.start_monitor_btn = QPushButton("Start Monitoring")
        self.start_monitor_btn.setFont(self.font)
        self.start_monitor_btn.clicked.connect(self.toggle_monitoring)
        self.start_monitor_btn.setMinimumHeight(35)
        self.start_monitor_btn.setEnabled(False)
        monitor_btn_layout.addWidget(self.start_monitor_btn)
        monitor_layout.addLayout(monitor_btn_layout)

        # Status label
        self.monitor_status_label = QLabel("Status: Not monitoring")
        self.monitor_status_label.setFont(self.font)
        monitor_layout.addWidget(self.monitor_status_label)

        # Data control buttons
        data_btn_layout = QHBoxLayout()

        self.clear_data_btn = QPushButton("Clear Plot Data")
        self.clear_data_btn.setFont(self.font)
        self.clear_data_btn.clicked.connect(self.clear_plot_data)

        self.save_data_btn = QPushButton("Save Data")
        self.save_data_btn.setFont(self.font)
        self.save_data_btn.clicked.connect(self.save_data)
        self.save_data_btn.setEnabled(False)

        data_btn_layout.addWidget(self.clear_data_btn)
        data_btn_layout.addWidget(self.save_data_btn)
        monitor_layout.addLayout(data_btn_layout)

        monitor_group.setLayout(monitor_layout)
        parent_layout.addWidget(monitor_group)

    def setup_plot_panel(self, parent_layout):
        """Setup right panel with plot"""
        plot_widget = QWidget()
        plot_layout = QVBoxLayout()
        plot_layout.setContentsMargins(10, 10, 10, 10)

        # Plot title
        plot_title = QLabel("Output vs Time")
        plot_title.setFont(self.titlefont)
        plot_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plot_layout.addWidget(plot_title)

        # Create PyQtGraph plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Voltage (V)')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()

        # Create plot curve
        self.output_curve = self.plot_widget.plot(pen=pg.mkPen(color='b', width=2), name='Voltage')

        plot_layout.addWidget(self.plot_widget)
        plot_widget.setLayout(plot_layout)
        parent_layout.addWidget(plot_widget)

    def on_instrument_connected(self, instrument, instrument_name):
        """Handle instrument connection"""
        self.kepco = instrument
        self.isConnect = True
        print(f"Connected to {instrument_name}")

        if self.kepco and self.kepco != 'Emulation':
            # Initialize instrument
            self.kepco_cmd.clear(self.kepco)

            # Turn off output initially
            self.kepco_cmd.set_output_state(self.kepco, 'OFF')

            # Start reading thread
            self.reading_thread = ReadingThread(self.kepco, self.kepco_cmd)
            self.reading_thread.reading_signal.connect(self.update_readings)
            self.reading_thread.error_signal.connect(self.on_reading_error)
            self.reading_thread.start()
        else:
            # Emulation mode
            self.emulation_thread = EmulationThread()
            self.emulation_thread.reading_signal.connect(self.update_readings)
            self.emulation_thread.start()

        # Enable controls
        self.set_values_btn.setEnabled(True)
        self.output_btn.setEnabled(True)
        self.set_protection_btn.setEnabled(True)
        self.apply_mode_btn.setEnabled(True)
        self.program_list_btn.setEnabled(True)
        self.clear_list_btn.setEnabled(True)
        self.start_monitor_btn.setEnabled(True)

    def on_instrument_disconnected(self, instrument_name):
        """Handle instrument disconnection"""
        # Stop monitoring
        self.stop_monitoring()

        if self.reading_thread and self.reading_thread.isRunning():
            self.reading_thread.stop()
            self.reading_thread.wait()
            self.reading_thread = None

        if self.emulation_thread and self.emulation_thread.isRunning():
            self.emulation_thread.stop()
            self.emulation_thread.wait()
            self.emulation_thread = None

        # Turn off output if connected
        if self.kepco and self.kepco != 'Emulation':
            try:
                self.kepco_cmd.set_output_state(self.kepco, 'OFF')
            except:
                pass

        self.kepco = None
        self.isConnect = False
        self.output_on = False
        print(f"Disconnected from {instrument_name}")

        # Disable controls
        self.set_values_btn.setEnabled(False)
        self.output_btn.setEnabled(False)
        self.set_protection_btn.setEnabled(False)
        self.apply_mode_btn.setEnabled(False)
        self.program_list_btn.setEnabled(False)
        self.clear_list_btn.setEnabled(False)
        self.start_monitor_btn.setEnabled(False)

        # Reset readings
        self.voltage_reading.setText("N/A")
        self.current_reading.setText("N/A")
        self.power_reading.setText("N/A")
        self.state_reading.setText("N/A")

        # Reset button states
        self.output_btn.setText("Output ON")
        self.output_btn.setStyleSheet("")

    def update_readings(self, readings):
        """Update reading labels"""
        self.voltage_reading.setText(f"{readings['voltage']:.3f} V")
        self.current_reading.setText(f"{readings['current']:.3f} A")
        self.power_reading.setText(f"{readings['power']:.3f} W")

        state_text = "ON" if readings['output_state'] in ['1', 'ON'] else "OFF"
        self.state_reading.setText(state_text)

    def on_reading_error(self, error_msg):
        """Handle reading thread error"""
        print(f"Reading error: {error_msg}")

    def set_voltage_current(self):
        """Set voltage and current"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        voltage = self.voltage_entry.text()
        current = self.current_entry.text()

        if not voltage or not current:
            QMessageBox.warning(self, "Missing Input", "Please enter both voltage and current")
            return

        if self.kepco == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", f"Set:\nVoltage: {voltage} V\nCurrent: {current} A")
            if self.emulation_thread:
                self.emulation_thread.voltage = float(voltage)
                self.emulation_thread.current = float(current)
            return

        try:
            # Set voltage and current
            self.kepco_cmd.set_voltage(self.kepco, float(voltage), 'V')
            time.sleep(0.05)
            self.kepco_cmd.set_current(self.kepco, float(current), 'A')

            QMessageBox.information(self, "Success", f"Configured:\nVoltage: {voltage} V\nCurrent: {current} A")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting values:\n{str(e)}")

    def toggle_output(self):
        """Toggle output on/off"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.kepco == 'Emulation':
            if not self.output_on:
                self.output_btn.setText("Output OFF")
                self.output_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #28A630;
                        color: white;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QPushButton:hover {
                        background-color: #F2433B;
                    }
                """)
                self.output_on = True
            else:
                self.output_btn.setText("Output ON")
                self.output_btn.setStyleSheet("")
                self.output_on = False
            return

        try:
            if not self.output_on:
                # Turn ON
                self.kepco_cmd.set_output_state(self.kepco, 'ON')
                self.output_btn.setText("Output OFF")
                self.output_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #28A630;
                        color: white;
                        border-radius: 5px;
                        padding: 5px;
                    }
                    QPushButton:hover {
                        background-color: #F2433B;
                    }
                """)
                self.output_on = True
            else:
                # Turn OFF
                self.kepco_cmd.set_output_state(self.kepco, 'OFF')
                self.output_btn.setText("Output ON")
                self.output_btn.setStyleSheet("")
                self.output_on = False

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error toggling output:\n{str(e)}")

    def set_protection(self):
        """Set overvoltage and overcurrent protection"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        ovp = self.ovp_entry.text()
        ocp = self.ocp_entry.text()

        if not ovp and not ocp:
            QMessageBox.warning(self, "Missing Input", "Please enter at least one protection value")
            return

        if self.kepco == 'Emulation':
            msg = "Protection set:\n"
            if ovp:
                msg += f"OVP: {ovp} V\n"
            if ocp:
                msg += f"OCP: {ocp} A"
            QMessageBox.information(self, "Emulation Mode", msg)
            return

        try:
            if ovp:
                self.kepco_cmd.set_voltage_protection(self.kepco, float(ovp), 'V')
            if ocp:
                self.kepco_cmd.set_current_protection(self.kepco, float(ocp), 'A')

            msg = "Protection configured:\n"
            if ovp:
                msg += f"OVP: {ovp} V\n"
            if ocp:
                msg += f"OCP: {ocp} A"
            QMessageBox.information(self, "Success", msg)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting protection:\n{str(e)}")

    def apply_modes(self):
        """Apply function and operation modes"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        func_mode = self.function_mode_combo.currentText()
        v_mode = self.voltage_mode_combo.currentText()
        i_mode = self.current_mode_combo.currentText()

        if self.kepco == 'Emulation':
            QMessageBox.information(self, "Emulation Mode",
                                    f"Modes set:\nFunction: {func_mode}\nVoltage Mode: {v_mode}\nCurrent Mode: {i_mode}")
            return

        try:
            # Set function mode
            self.kepco_cmd.set_function_mode(self.kepco, func_mode)
            time.sleep(0.05)

            # Set voltage mode
            self.kepco_cmd.set_voltage_mode(self.kepco, v_mode)
            time.sleep(0.05)

            # Set current mode
            self.kepco_cmd.set_current_mode(self.kepco, i_mode)

            QMessageBox.information(self, "Success",
                                    f"Modes configured:\nFunction: {func_mode}\nVoltage Mode: {v_mode}\nCurrent Mode: {i_mode}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting modes:\n{str(e)}")

    def program_list(self):
        """Program list with voltages, currents, and dwell times"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        v_list = self.voltage_list_entry.text()
        i_list = self.current_list_entry.text()
        dwell_list = self.dwell_list_entry.text()

        if not v_list or not i_list or not dwell_list:
            QMessageBox.warning(self, "Missing Input", "Please enter voltage list, current list, and dwell times")
            return

        try:
            # Parse lists
            voltages = [float(v.strip()) for v in v_list.split(',')]
            currents = [float(i.strip()) for i in i_list.split(',')]
            dwells = [float(d.strip()) for d in dwell_list.split(',')]

            if len(voltages) != len(currents) or len(voltages) != len(dwells):
                QMessageBox.warning(self, "List Mismatch",
                                    "Voltage, current, and dwell lists must have the same length")
                return

            if len(voltages) > 250:
                QMessageBox.warning(self, "List Too Long", "Maximum 250 points allowed")
                return

        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numeric values")
            return

        if self.kepco == 'Emulation':
            QMessageBox.information(self, "Emulation Mode",
                                    f"List programmed:\n{len(voltages)} points\nCount: {self.list_count_spin.value()}\n"
                                    f"Direction: {self.list_direction_combo.currentText()}")
            return

        try:
            # Clear existing list
            self.kepco_cmd.list_clear(self.kepco)
            time.sleep(0.1)

            # Program voltage list
            self.kepco_cmd.set_list_voltage(self.kepco, *voltages)
            time.sleep(0.1)

            # Program current list
            self.kepco_cmd.set_list_current(self.kepco, *currents)
            time.sleep(0.1)

            # Program dwell times
            self.kepco_cmd.set_list_dwell(self.kepco, *dwells)
            time.sleep(0.1)

            # Set list count
            self.kepco_cmd.set_list_count(self.kepco, self.list_count_spin.value())
            time.sleep(0.05)

            # Set list direction
            self.kepco_cmd.set_list_direction(self.kepco, self.list_direction_combo.currentText())

            QMessageBox.information(self, "Success",
                                    f"List programmed:\n{len(voltages)} points\nCount: {self.list_count_spin.value()}\n"
                                    f"Direction: {self.list_direction_combo.currentText()}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error programming list:\n{str(e)}")

    def clear_list(self):
        """Clear programmed list"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.kepco == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "List cleared")
            return

        try:
            self.kepco_cmd.list_clear(self.kepco)
            QMessageBox.information(self, "Success", "List cleared")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error clearing list:\n{str(e)}")

    def toggle_monitoring(self):
        """Start or stop monitoring"""
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        """Start monitoring for plotting"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.monitor_thread and self.monitor_thread.isRunning():
            return

        is_emulation = (self.kepco == 'Emulation')

        self.monitor_thread = MonitorThread(self.kepco, self.kepco_cmd, is_emulation)
        self.monitor_thread.data_signal.connect(self.update_plot_data)
        self.monitor_thread.error_signal.connect(self.on_reading_error)
        self.monitor_thread.start()

        self.monitor_status_label.setText("Status: Monitoring active")
        self.start_monitor_btn.setText("Stop Monitoring")
        self.save_data_btn.setEnabled(True)
        print("Monitoring started")

    def stop_monitoring(self):
        """Stop monitoring"""
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()
            self.monitor_thread = None

        self.monitor_status_label.setText("Status: Not monitoring")
        self.start_monitor_btn.setText("Start Monitoring")
        print("Monitoring stopped")

    def update_plot_data(self, time_val, readings):
        """Update plot with new data point"""
        self.time_data.append(time_val)
        self.voltage_data.append(readings['voltage'])
        self.current_data.append(readings['current'])
        self.power_data.append(readings['voltage'] * readings['current'])

        # Limit data points
        if len(self.time_data) > self.max_points:
            self.time_data = self.time_data[-self.max_points:]
            self.voltage_data = self.voltage_data[-self.max_points:]
            self.current_data = self.current_data[-self.max_points:]
            self.power_data = self.power_data[-self.max_points:]

        # Update plot
        self.update_plot_display()

    def update_plot_display(self):
        """Update plot based on selected parameter"""
        if not self.time_data:
            return

        plot_mode = self.plot_param_combo.currentText()

        # Update y-axis label and data
        if plot_mode == "Voltage":
            self.plot_widget.setLabel('left', 'Voltage (V)')
            self.output_curve.setData(self.time_data, self.voltage_data)
            self.output_curve.opts['name'] = 'Voltage'
        elif plot_mode == "Current":
            self.plot_widget.setLabel('left', 'Current (A)')
            self.output_curve.setData(self.time_data, self.current_data)
            self.output_curve.opts['name'] = 'Current'
        else:  # Power
            self.plot_widget.setLabel('left', 'Power (W)')
            self.output_curve.setData(self.time_data, self.power_data)
            self.output_curve.opts['name'] = 'Power'

    def clear_plot_data(self):
        """Clear all plot data"""
        self.time_data = []
        self.voltage_data = []
        self.current_data = []
        self.power_data = []

        self.output_curve.setData([], [])

        self.save_data_btn.setEnabled(False)
        print("Plot data cleared")

    def save_data(self):
        """Save data to CSV file"""
        if not self.time_data:
            QMessageBox.warning(self, "No Data", "No data to save")
            return

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kepco_klp_data_{timestamp}.csv"

        try:
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Time (s)', 'Voltage (V)', 'Current (A)', 'Power (W)'])
                for i in range(len(self.time_data)):
                    writer.writerow([self.time_data[i], self.voltage_data[i], self.current_data[i], self.power_data[i]])

            QMessageBox.information(self, "Success", f"Data saved to {filename}")
            print(f"Data saved to {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving data:\n{str(e)}")

    def closeEvent(self, event):
        """Handle window close"""
        self.stop_monitoring()

        if self.reading_thread and self.reading_thread.isRunning():
            self.reading_thread.stop()
            self.reading_thread.wait()

        if self.emulation_thread and self.emulation_thread.isRunning():
            self.emulation_thread.stop()
            self.emulation_thread.wait()

        if self.kepco and self.kepco != 'Emulation':
            try:
                self.kepco_cmd.set_output_state(self.kepco, 'OFF')
                self.kepco.close()
            except:
                pass

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = KEPCO()
    window.show()
    sys.exit(app.exec())