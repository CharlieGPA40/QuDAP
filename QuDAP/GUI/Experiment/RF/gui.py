try:
    from instrument.instrument_connection import InstrumentConnection
except ImportError:
    from QuDAP.instrument.instrument_connection import InstrumentConnection

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
                             QPushButton, QDoubleSpinBox, QSpinBox, QComboBox, QStackedWidget, QMessageBox, QScrollArea,
                             QSizePolicy)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
import sys
import time
import numpy as np
import pyqtgraph as pg
from datetime import datetime


class COMMAND:
    """Command class for BNC 845 RF Signal Generator"""

    def get_id(self, instrument) -> str:
        id = instrument.query('*IDN?')
        return id

    def abort(self, instrument):
        instrument.write(':ABORt')

    def initialize(self, instrument):
        instrument.write(':INIT ON')

    def set_output(self, instrument, state: str):
        if state.lower() == 'on':
            instrument.write(':OUTP ON')
        elif state.lower() == 'off':
            instrument.write(':OUTP OFF')

    def get_output(self, instrument):
        state = instrument.query(':OUTP?')
        return state

    def set_frequency(self, instrument, frequency: str):
        freq_val = int(frequency)
        if 99999 < freq_val < 26500000001:
            instrument.write(':SOUR:FREQ {}'.format(frequency))
            return True
        else:
            return False

    def get_frequency(self, instrument):
        frequency = instrument.query(':SOUR:FREQ?')
        return frequency

    def set_power(self, instrument, power: str):
        power_val = float(power)
        if -21.01 < power_val < 15.01:
            instrument.write(':SOUR:POW {}'.format(power))
            return True
        else:
            return False

    def get_power(self, instrument):
        power = instrument.query(':SOUR:POW?')
        return power

    # AM Commands
    def set_am_depth(self, instrument, am_depth: str):
        depth = int(am_depth)
        if 0 <= depth <= 100:
            instrument.write(':SOUR:AM:DEPT {}'.format(am_depth))
            return True
        return False

    def get_am_depth(self, instrument):
        depth = instrument.query(':SOUR:AM:DEPT?')
        return depth

    def set_am_frequency(self, instrument, frequency: str):
        instrument.write(':SOUR:AM:INT:FREQ {}'.format(frequency))

    def get_am_frequency(self, instrument):
        frequency = instrument.query(':SOUR:AM:INT:FREQ?')
        return frequency

    def set_am_state(self, instrument, state: str):
        if state.lower() == 'on':
            instrument.write(':SOUR:AM:STAT ON')
        elif state.lower() == 'off':
            instrument.write(':SOUR:AM:STAT OFF')

    def get_am_state(self, instrument):
        state = instrument.query(':SOUR:AM:STAT?')
        return state

    def set_am_source(self, instrument, source: str):
        if source == 'INT' or source == 'EXT':
            instrument.write(':SOUR:AM:SOUR {}'.format(source))

    def get_am_source(self, instrument):
        source = instrument.query(':SOUR:AM:SOUR?')
        return source

    # FM Commands
    def set_fm_state(self, instrument, state: str):
        if state.lower() == 'on':
            instrument.write(':SOUR:FM:STAT ON')
        elif state.lower() == 'off':
            instrument.write(':SOUR:FM:STAT OFF')

    def get_fm_state(self, instrument):
        state = instrument.query(':SOUR:FM:STAT?')
        return state

    def set_fm_frequency(self, instrument, frequency: str):
        instrument.write(':SOUR:FM:INT:FREQ {}'.format(frequency))

    def get_fm_frequency(self, instrument):
        frequency = instrument.query(':SOUR:FM:INT:FREQ?')
        return frequency

    def set_fm_deviation(self, instrument, deviation: str):
        instrument.write(':SOUR:FM:DEV {}'.format(deviation))

    def get_fm_deviation(self, instrument):
        deviation = instrument.query(':SOUR:FM:DEV?')
        return deviation

    # PM Commands
    def set_pm_state(self, instrument, state: str):
        if state.lower() == 'on':
            instrument.write(':SOUR:PM:STAT ON')
        elif state.lower() == 'off':
            instrument.write(':SOUR:PM:STAT OFF')

    def get_pm_state(self, instrument):
        state = instrument.query(':SOUR:PM:STAT?')
        return state

    def set_pm_deviation(self, instrument, deviation: str):
        instrument.write(':SOUR:PM:DEV {}'.format(deviation))

    def get_pm_deviation(self, instrument):
        deviation = instrument.query(':SOUR:PM:DEV?')
        return deviation

    # Pulse Commands
    def set_pulse_state(self, instrument, state: str):
        if state.lower() == 'on':
            instrument.write(':SOUR:PULM:STAT ON')
        elif state.lower() == 'off':
            instrument.write(':SOUR:PULM:STAT OFF')

    def get_pulse_state(self, instrument):
        state = instrument.query(':SOUR:PULM:STAT?')
        return state


class MonitorThread(QThread):
    """Thread to monitor RF source parameters in real-time"""

    data_signal = pyqtSignal(float, float, float)  # (time, frequency, power)
    error_signal = pyqtSignal(str)

    def __init__(self, instrument, command, is_emulation=False, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.command = command
        self.is_emulation = is_emulation
        self.should_stop = False
        self.start_time = time.time()

    def run(self):
        """Monitor the instrument parameters"""
        try:
            while not self.should_stop:
                try:
                    if self.is_emulation:
                        # Emulated readings
                        freq = 1e9 + np.random.randn() * 1e6
                        power = 0.0 + np.random.randn() * 0.1
                    else:
                        # Read current frequency and power
                        freq = float(self.command.get_frequency(self.instrument).strip())
                        power = float(self.command.get_power(self.instrument).strip())

                    # Calculate elapsed time
                    elapsed_time = time.time() - self.start_time

                    # Emit data
                    self.data_signal.emit(elapsed_time, freq, power)

                    # Sleep for update interval
                    time.sleep(0.5)

                except Exception as e:
                    self.error_signal.emit(f"Monitoring error: {str(e)}")
                    break

        except Exception as e:
            self.error_signal.emit(f"Thread error: {str(e)}")

    def stop(self):
        """Stop monitoring"""
        self.should_stop = True


class SweepThread(QThread):
    """Thread for executing parameter sweeps"""

    sweep_data_signal = pyqtSignal(dict)  # {step, param_value, freq, power, time}
    sweep_complete_signal = pyqtSignal()
    sweep_status_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, instrument, command, sweep_config, is_emulation=False, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.command = command
        self.sweep_config = sweep_config
        self.is_emulation = is_emulation
        self.should_stop = False
        self.start_time = time.time()

    def run(self):
        """Execute the sweep"""
        try:
            sweep_type = self.sweep_config['type']
            start_val = self.sweep_config['start']
            stop_val = self.sweep_config['stop']
            num_steps = self.sweep_config['steps']
            delay = self.sweep_config['delay']

            # Generate sweep values
            sweep_values = np.linspace(start_val, stop_val, num_steps)

            for step_idx, param_value in enumerate(sweep_values):
                if self.should_stop:
                    break

                # Set the parameter
                self.sweep_status_signal.emit(
                    f"Step {step_idx + 1}/{num_steps}: Setting {sweep_type} = {param_value:.3f}")

                try:
                    if sweep_type == 'RF Frequency':
                        if not self.is_emulation:
                            self.command.set_frequency(self.instrument, str(int(param_value)))
                    elif sweep_type == 'RF Power':
                        if not self.is_emulation:
                            self.command.set_power(self.instrument, str(param_value))
                    elif sweep_type == 'AM Frequency':
                        if not self.is_emulation:
                            self.command.set_am_frequency(self.instrument, str(param_value))
                    elif sweep_type == 'AM Depth':
                        if not self.is_emulation:
                            self.command.set_am_depth(self.instrument, str(int(param_value)))
                    elif sweep_type == 'FM Frequency':
                        if not self.is_emulation:
                            self.command.set_fm_frequency(self.instrument, str(param_value))
                    elif sweep_type == 'FM Deviation':
                        if not self.is_emulation:
                            self.command.set_fm_deviation(self.instrument, str(param_value))

                    # Wait for settling
                    time.sleep(delay)

                    # Read current state
                    if self.is_emulation:
                        freq = 1e9 + param_value * 1e6 if sweep_type != 'RF Frequency' else param_value
                        power = param_value if sweep_type == 'RF Power' else 0.0
                    else:
                        freq = float(self.command.get_frequency(self.instrument).strip())
                        power = float(self.command.get_power(self.instrument).strip())

                    elapsed_time = time.time() - self.start_time

                    # Emit data
                    sweep_data = {'step': step_idx, 'param_value': param_value, 'frequency': freq, 'power': power,
                        'time': elapsed_time}
                    self.sweep_data_signal.emit(sweep_data)

                except Exception as e:
                    self.error_signal.emit(f"Error at step {step_idx + 1}: {str(e)}")
                    break

            if not self.should_stop:
                self.sweep_complete_signal.emit()

        except Exception as e:
            self.error_signal.emit(f"Sweep thread error: {str(e)}")

    def stop(self):
        """Stop sweep"""
        self.should_stop = True


class BNC845RF(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BNC 845 RF Signal Generator")
        self.setGeometry(100, 100, 1400, 900)

        self.bnc845 = None
        self.command = COMMAND()
        self.monitor_thread = None
        self.sweep_thread = None

        # Data storage
        self.time_data = []
        self.freq_data = []
        self.power_data = []

        # Sweep data storage
        self.sweep_data_storage = []

        self.font = QFont("Arial", 10)
        self.titlefont = QFont("Arial", 12, QFont.Weight.Bold)

        # Load scrollbar stylesheet if available
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
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
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
        self.scroll_area.setFixedWidth(500)

        # Content widget for scroll area
        left_content = QWidget()
        left_content.setMaximumWidth(480)

        self.left_layout = QVBoxLayout()
        self.left_layout.setContentsMargins(10, 10, 10, 10)
        self.left_layout.setSpacing(10)

        # Title
        title = QLabel("BNC 845 RF Signal Generator")
        title.setFont(self.titlefont)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_layout.addWidget(title)

        # Connection section
        self.connection_widget = InstrumentConnection(instrument_list=["BNC 845 RF"], allow_emulation=True,
            title="Instrument Connection")
        self.connection_widget.instrument_connected.connect(self.on_instrument_connected)
        self.connection_widget.instrument_disconnected.connect(self.on_instrument_disconnected)
        self.left_layout.addWidget(self.connection_widget)

        # Reading section
        self.setup_reading_section(self.left_layout)

        # RF Control section
        self.setup_rf_control_section(self.left_layout)

        # Modulation section
        self.setup_modulation_section(self.left_layout)

        # Sweep section (NEW)
        self.setup_sweep_section(self.left_layout)

        # Monitor control section
        self.setup_monitor_section(self.left_layout)

        # Data controls
        self.setup_data_section(self.left_layout)

        # Add stretch at the end to push content to top
        self.left_layout.addStretch()

        left_content.setLayout(self.left_layout)
        self.scroll_area.setWidget(left_content)

        # Right panel - Plots
        right_panel = self.create_plot_panel()

        # Add panels to main layout
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(right_panel, 1)

        central_widget.setLayout(main_layout)

    def on_instrument_connected(self, instrument, instrument_name):
        """Handle instrument connection"""
        self.bnc845 = instrument
        print(f"Connected to {instrument_name}")

        # Update readings if real instrument
        if self.bnc845 and self.bnc845 != 'Emulation':
            self.update_readings_from_instrument()

        # Enable controls
        self.start_monitor_btn.setEnabled(True)
        self.start_sweep_btn.setEnabled(True)

        # Update sweep options based on current modulation state
        self.update_sweep_options()

    def on_instrument_disconnected(self, instrument_name):
        """Handle instrument disconnection"""
        # Stop monitoring if active
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.stop_monitoring()

        # Stop sweep if active
        if self.sweep_thread and self.sweep_thread.isRunning():
            self.abort_sweep()

        self.bnc845 = None
        print(f"Disconnected from {instrument_name}")

        # Disable controls
        self.start_monitor_btn.setEnabled(False)
        self.start_sweep_btn.setEnabled(False)

    def setup_reading_section(self, parent_layout):
        """Setup reading display section"""
        reading_group = QGroupBox("Current Readings")
        reading_layout = QVBoxLayout()

        # Frequency reading
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Frequency:")
        freq_label.setFont(self.font)
        freq_label.setFixedWidth(80)
        self.freq_reading_label = QLabel("N/A")
        self.freq_reading_label.setFont(self.font)
        self.freq_reading_label.setWordWrap(True)
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_reading_label, 1)
        reading_layout.addLayout(freq_layout)

        # Power reading
        power_layout = QHBoxLayout()
        power_label = QLabel("Power:")
        power_label.setFont(self.font)
        power_label.setFixedWidth(80)
        self.power_reading_label = QLabel("N/A")
        self.power_reading_label.setFont(self.font)
        self.power_reading_label.setWordWrap(True)
        power_layout.addWidget(power_label)
        power_layout.addWidget(self.power_reading_label, 1)
        reading_layout.addLayout(power_layout)

        # Modulation type reading
        mod_type_layout = QHBoxLayout()
        mod_type_label = QLabel("Modulation:")
        mod_type_label.setFont(self.font)
        mod_type_label.setFixedWidth(80)
        self.mod_type_reading_label = QLabel("N/A")
        self.mod_type_reading_label.setFont(self.font)
        self.mod_type_reading_label.setWordWrap(True)
        mod_type_layout.addWidget(mod_type_label)
        mod_type_layout.addWidget(self.mod_type_reading_label, 1)
        reading_layout.addLayout(mod_type_layout)

        # Modulation state reading
        mod_state_layout = QHBoxLayout()
        mod_state_label = QLabel("Mod State:")
        mod_state_label.setFont(self.font)
        mod_state_label.setFixedWidth(80)
        self.mod_state_reading_label = QLabel("N/A")
        self.mod_state_reading_label.setFont(self.font)
        self.mod_state_reading_label.setWordWrap(True)
        mod_state_layout.addWidget(mod_state_label)
        mod_state_layout.addWidget(self.mod_state_reading_label, 1)
        reading_layout.addLayout(mod_state_layout)

        # RF State reading
        rf_state_layout = QHBoxLayout()
        rf_state_label = QLabel("RF State:")
        rf_state_label.setFont(self.font)
        rf_state_label.setFixedWidth(80)
        self.rf_state_reading_label = QLabel("N/A")
        self.rf_state_reading_label.setFont(self.font)
        self.rf_state_reading_label.setWordWrap(True)
        rf_state_layout.addWidget(rf_state_label)
        rf_state_layout.addWidget(self.rf_state_reading_label, 1)
        reading_layout.addLayout(rf_state_layout)

        reading_group.setLayout(reading_layout)
        parent_layout.addWidget(reading_group)

    def setup_rf_control_section(self, parent_layout):
        """Setup RF control section"""
        rf_group = QGroupBox("RF Control")
        rf_layout = QVBoxLayout()

        # Frequency control
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Frequency:")
        freq_label.setFixedWidth(80)
        freq_label.setFont(self.font)
        self.freq_spinbox = QDoubleSpinBox()
        self.freq_spinbox.setRange(100000, 26500000000)
        self.freq_spinbox.setValue(1000000000)
        self.freq_spinbox.setDecimals(0)
        self.freq_spinbox.setSuffix(" Hz")
        self.freq_spinbox.setFont(self.font)
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_spinbox, 1)
        rf_layout.addLayout(freq_layout)

        freq_set_btn = QPushButton("Set Frequency")
        freq_set_btn.clicked.connect(self.set_frequency)
        freq_set_btn.setFont(self.font)
        freq_set_btn.setMinimumHeight(30)
        rf_layout.addWidget(freq_set_btn)

        # Power control
        power_layout = QHBoxLayout()
        power_label = QLabel("Power:")
        power_label.setFixedWidth(80)
        power_label.setFont(self.font)
        self.power_spinbox = QDoubleSpinBox()
        self.power_spinbox.setRange(-21.0, 15.0)
        self.power_spinbox.setValue(0.0)
        self.power_spinbox.setDecimals(2)
        self.power_spinbox.setSuffix(" dBm")
        self.power_spinbox.setFont(self.font)
        power_layout.addWidget(power_label)
        power_layout.addWidget(self.power_spinbox, 1)
        rf_layout.addLayout(power_layout)

        power_set_btn = QPushButton("Set Power")
        power_set_btn.clicked.connect(self.set_power)
        power_set_btn.setFont(self.font)
        power_set_btn.setMinimumHeight(30)
        rf_layout.addWidget(power_set_btn)

        # Output control
        output_layout = QHBoxLayout()
        self.output_on_btn = QPushButton("Output ON")
        self.output_on_btn.clicked.connect(lambda: self.set_output('on'))
        self.output_on_btn.setFont(self.font)
        self.output_on_btn.setMinimumHeight(30)
        self.output_off_btn = QPushButton("Output OFF")
        self.output_off_btn.clicked.connect(lambda: self.set_output('off'))
        self.output_off_btn.setFont(self.font)
        self.output_off_btn.setMinimumHeight(30)
        output_layout.addWidget(self.output_on_btn)
        output_layout.addWidget(self.output_off_btn)
        rf_layout.addLayout(output_layout)

        rf_group.setLayout(rf_layout)
        parent_layout.addWidget(rf_group)

    def setup_modulation_section(self, parent_layout):
        """Setup modulation section with dynamic vertical sizing"""
        self.mod_group = QGroupBox("Modulation")

        mod_layout = QVBoxLayout()

        # Modulation type selection
        mod_select_layout = QHBoxLayout()
        mod_label = QLabel("Type:")
        mod_label.setFont(self.font)
        mod_label.setFixedWidth(80)
        self.mod_combo = QComboBox()
        self.mod_combo.setFont(self.font)
        self.mod_combo.addItems(["No Modulation", "Pulse Mod", "Amplitude Mod", "Frequency Mod", "Phase Mod"])
        self.mod_combo.currentIndexChanged.connect(self.on_modulation_type_changed)
        mod_select_layout.addWidget(mod_label)
        mod_select_layout.addWidget(self.mod_combo, 1)
        mod_layout.addLayout(mod_select_layout)

        # Stacked widget for modulation-specific controls
        self.mod_stack = QStackedWidget()

        # Page 0: No modulation selected
        page0 = self.create_no_mod_page()
        self.mod_stack.addWidget(page0)

        # Page 1: Pulse Modulation
        page1 = self.create_pulse_mod_page()
        self.mod_stack.addWidget(page1)

        # Page 2: Amplitude Modulation
        page2 = self.create_am_mod_page()
        self.mod_stack.addWidget(page2)

        # Page 3: Frequency Modulation
        page3 = self.create_fm_mod_page()
        self.mod_stack.addWidget(page3)

        # Page 4: Phase Modulation
        page4 = self.create_pm_mod_page()
        self.mod_stack.addWidget(page4)

        mod_layout.addWidget(self.mod_stack)

        self.mod_group.setLayout(mod_layout)
        parent_layout.addWidget(self.mod_group)

    def create_no_mod_page(self):
        """Create no modulation control page"""
        page = QWidget()
        page.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout = QVBoxLayout()

        no_mod_label = QLabel("No Modulation")
        no_mod_label.setFont(self.font)
        layout.addWidget(no_mod_label)

        page.setLayout(layout)
        return page

    def create_pulse_mod_page(self):
        """Create pulse modulation control page"""
        page = QWidget()
        page.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 0)

        # State control
        state_layout = QHBoxLayout()
        self.pulse_on_btn = QPushButton("Pulse ON")
        self.pulse_on_btn.clicked.connect(lambda: self.set_pulse_state('on'))
        self.pulse_on_btn.setFont(self.font)
        self.pulse_on_btn.setMinimumHeight(30)
        self.pulse_off_btn = QPushButton("Pulse OFF")
        self.pulse_off_btn.clicked.connect(lambda: self.set_pulse_state('off'))
        self.pulse_off_btn.setFont(self.font)
        self.pulse_off_btn.setMinimumHeight(30)
        state_layout.addWidget(self.pulse_on_btn)
        state_layout.addWidget(self.pulse_off_btn)
        layout.addLayout(state_layout)

        page.setLayout(layout)
        return page

    def create_am_mod_page(self):
        """Create amplitude modulation control page"""
        page = QWidget()
        page.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 0)

        # AM Frequency
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Mod Freq:")
        freq_label.setFont(self.font)
        freq_label.setFixedWidth(80)
        self.am_freq_spinbox = QDoubleSpinBox()
        self.am_freq_spinbox.setRange(0.1, 1000000)
        self.am_freq_spinbox.setValue(1000)
        self.am_freq_spinbox.setDecimals(1)
        self.am_freq_spinbox.setSuffix(" Hz")
        self.am_freq_spinbox.setFont(self.font)
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.am_freq_spinbox, 1)
        layout.addLayout(freq_layout)

        # AM Depth
        depth_layout = QHBoxLayout()
        depth_label = QLabel("Mod Depth:")
        depth_label.setFont(self.font)
        depth_label.setFixedWidth(80)
        self.am_depth_spinbox = QSpinBox()
        self.am_depth_spinbox.setRange(0, 100)
        self.am_depth_spinbox.setValue(50)
        self.am_depth_spinbox.setSuffix(" %")
        self.am_depth_spinbox.setFont(self.font)
        depth_layout.addWidget(depth_label)
        depth_layout.addWidget(self.am_depth_spinbox, 1)
        layout.addLayout(depth_layout)

        # AM Source
        source_layout = QHBoxLayout()
        source_label = QLabel("Source:")
        source_label.setFont(self.font)
        source_label.setFixedWidth(80)
        self.am_source_combo = QComboBox()
        self.am_source_combo.setFont(self.font)
        self.am_source_combo.addItems(["INT", "EXT"])
        source_layout.addWidget(source_label)
        source_layout.addWidget(self.am_source_combo, 1)
        layout.addLayout(source_layout)

        # Apply button
        apply_btn = QPushButton("Apply AM Settings")
        apply_btn.clicked.connect(self.apply_am_settings)
        apply_btn.setFont(self.font)
        apply_btn.setMinimumHeight(30)
        layout.addWidget(apply_btn)

        # State control
        state_layout = QHBoxLayout()
        self.am_on_btn = QPushButton("AM ON")
        self.am_on_btn.clicked.connect(lambda: self.set_am_state('on'))
        self.am_on_btn.setFont(self.font)
        self.am_on_btn.setMinimumHeight(30)
        self.am_off_btn = QPushButton("AM OFF")
        self.am_off_btn.clicked.connect(lambda: self.set_am_state('off'))
        self.am_off_btn.setFont(self.font)
        self.am_off_btn.setMinimumHeight(30)
        state_layout.addWidget(self.am_on_btn)
        state_layout.addWidget(self.am_off_btn)
        layout.addLayout(state_layout)

        page.setLayout(layout)
        return page

    def create_fm_mod_page(self):
        """Create frequency modulation control page"""
        page = QWidget()
        page.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 0)

        # FM Frequency
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Mod Freq:")
        freq_label.setFont(self.font)
        freq_label.setFixedWidth(80)
        self.fm_freq_spinbox = QDoubleSpinBox()
        self.fm_freq_spinbox.setRange(0.1, 1000000)
        self.fm_freq_spinbox.setValue(1000)
        self.fm_freq_spinbox.setDecimals(1)
        self.fm_freq_spinbox.setSuffix(" Hz")
        self.fm_freq_spinbox.setFont(self.font)
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.fm_freq_spinbox, 1)
        layout.addLayout(freq_layout)

        # FM Deviation
        dev_layout = QHBoxLayout()
        dev_label = QLabel("Deviation:")
        dev_label.setFont(self.font)
        dev_label.setFixedWidth(80)
        self.fm_dev_spinbox = QDoubleSpinBox()
        self.fm_dev_spinbox.setRange(1, 10000000)
        self.fm_dev_spinbox.setValue(1000)
        self.fm_dev_spinbox.setDecimals(0)
        self.fm_dev_spinbox.setSuffix(" Hz")
        self.fm_dev_spinbox.setFont(self.font)
        dev_layout.addWidget(dev_label)
        dev_layout.addWidget(self.fm_dev_spinbox, 1)
        layout.addLayout(dev_layout)

        # Apply button
        apply_btn = QPushButton("Apply FM Settings")
        apply_btn.clicked.connect(self.apply_fm_settings)
        apply_btn.setFont(self.font)
        apply_btn.setMinimumHeight(30)
        layout.addWidget(apply_btn)

        # State control
        state_layout = QHBoxLayout()
        self.fm_on_btn = QPushButton("FM ON")
        self.fm_on_btn.clicked.connect(lambda: self.set_fm_state('on'))
        self.fm_on_btn.setFont(self.font)
        self.fm_on_btn.setMinimumHeight(30)
        self.fm_off_btn = QPushButton("FM OFF")
        self.fm_off_btn.clicked.connect(lambda: self.set_fm_state('off'))
        self.fm_off_btn.setFont(self.font)
        self.fm_off_btn.setMinimumHeight(30)
        state_layout.addWidget(self.fm_on_btn)
        state_layout.addWidget(self.fm_off_btn)
        layout.addLayout(state_layout)

        page.setLayout(layout)
        return page

    def create_pm_mod_page(self):
        """Create phase modulation control page"""
        page = QWidget()
        page.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 0)

        # PM Deviation
        dev_layout = QHBoxLayout()
        dev_label = QLabel("Deviation:")
        dev_label.setFont(self.font)
        dev_label.setFixedWidth(80)
        self.pm_dev_spinbox = QDoubleSpinBox()
        self.pm_dev_spinbox.setRange(0, 10)
        self.pm_dev_spinbox.setValue(1.0)
        self.pm_dev_spinbox.setDecimals(2)
        self.pm_dev_spinbox.setSuffix(" rad")
        self.pm_dev_spinbox.setFont(self.font)
        dev_layout.addWidget(dev_label)
        dev_layout.addWidget(self.pm_dev_spinbox, 1)
        layout.addLayout(dev_layout)

        # Apply button
        apply_btn = QPushButton("Apply PM Settings")
        apply_btn.clicked.connect(self.apply_pm_settings)
        apply_btn.setFont(self.font)
        apply_btn.setMinimumHeight(30)
        layout.addWidget(apply_btn)

        # State control
        state_layout = QHBoxLayout()
        self.pm_on_btn = QPushButton("PM ON")
        self.pm_on_btn.clicked.connect(lambda: self.set_pm_state('on'))
        self.pm_on_btn.setFont(self.font)
        self.pm_on_btn.setMinimumHeight(30)
        self.pm_off_btn = QPushButton("PM OFF")
        self.pm_off_btn.clicked.connect(lambda: self.set_pm_state('off'))
        self.pm_off_btn.setFont(self.font)
        self.pm_off_btn.setMinimumHeight(30)
        state_layout.addWidget(self.pm_on_btn)
        state_layout.addWidget(self.pm_off_btn)
        layout.addLayout(state_layout)

        page.setLayout(layout)
        return page

    def setup_sweep_section(self, parent_layout):
        """Setup parameter sweep section (NEW)"""
        self.sweep_group = QGroupBox("Parameter Sweep")
        sweep_layout = QVBoxLayout()

        # Sweep type selection
        type_layout = QHBoxLayout()
        type_label = QLabel("Sweep Type:")
        type_label.setFont(self.font)
        type_label.setFixedWidth(100)
        self.sweep_type_combo = QComboBox()
        self.sweep_type_combo.setFont(self.font)
        # Initially add only RF options
        self.sweep_type_combo.addItems(["RF Frequency", "RF Power"])
        self.sweep_type_combo.currentTextChanged.connect(self.on_sweep_type_changed)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.sweep_type_combo, 1)
        sweep_layout.addLayout(type_layout)

        # Start value
        start_layout = QHBoxLayout()
        start_label = QLabel("Start:")
        start_label.setFont(self.font)
        start_label.setFixedWidth(100)
        self.sweep_start_spin = QDoubleSpinBox()
        self.sweep_start_spin.setFont(self.font)
        self.sweep_start_spin.setRange(100000, 26500000000)
        self.sweep_start_spin.setDecimals(0)
        self.sweep_start_spin.setValue(1000000000)
        self.sweep_start_suffix = QLabel("Hz")
        self.sweep_start_suffix.setFont(self.font)
        start_layout.addWidget(start_label)
        start_layout.addWidget(self.sweep_start_spin, 1)
        start_layout.addWidget(self.sweep_start_suffix)
        sweep_layout.addLayout(start_layout)

        # Stop value
        stop_layout = QHBoxLayout()
        stop_label = QLabel("Stop:")
        stop_label.setFont(self.font)
        stop_label.setFixedWidth(100)
        self.sweep_stop_spin = QDoubleSpinBox()
        self.sweep_stop_spin.setFont(self.font)
        self.sweep_stop_spin.setRange(100000, 26500000000)
        self.sweep_stop_spin.setDecimals(0)
        self.sweep_stop_spin.setValue(2000000000)
        self.sweep_stop_suffix = QLabel("Hz")
        self.sweep_stop_suffix.setFont(self.font)
        stop_layout.addWidget(stop_label)
        stop_layout.addWidget(self.sweep_stop_spin, 1)
        stop_layout.addWidget(self.sweep_stop_suffix)
        sweep_layout.addLayout(stop_layout)

        # Number of steps
        steps_layout = QHBoxLayout()
        steps_label = QLabel("Steps:")
        steps_label.setFont(self.font)
        steps_label.setFixedWidth(100)
        self.sweep_steps_spin = QSpinBox()
        self.sweep_steps_spin.setFont(self.font)
        self.sweep_steps_spin.setRange(2, 1000)
        self.sweep_steps_spin.setValue(11)
        self.sweep_steps_suffix = QLabel("points")
        self.sweep_steps_suffix.setFont(self.font)
        steps_layout.addWidget(steps_label)
        steps_layout.addWidget(self.sweep_steps_spin, 1)
        steps_layout.addWidget(self.sweep_steps_suffix)
        sweep_layout.addLayout(steps_layout)

        # Time delay between steps
        delay_layout = QHBoxLayout()
        delay_label = QLabel("Delay:")
        delay_label.setFont(self.font)
        delay_label.setFixedWidth(100)
        self.sweep_delay_spin = QDoubleSpinBox()
        self.sweep_delay_spin.setFont(self.font)
        self.sweep_delay_spin.setRange(0.0, 60.0)
        self.sweep_delay_spin.setDecimals(2)
        self.sweep_delay_spin.setValue(0.5)
        self.sweep_delay_spin.setSuffix(" s")
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.sweep_delay_spin, 1)
        sweep_layout.addLayout(delay_layout)

        # Sweep control buttons
        sweep_btn_layout = QHBoxLayout()

        self.start_sweep_btn = QPushButton("Start Sweep")
        self.start_sweep_btn.setFont(self.font)
        self.start_sweep_btn.clicked.connect(self.start_sweep)
        self.start_sweep_btn.setMinimumHeight(35)
        self.start_sweep_btn.setEnabled(False)
        self.start_sweep_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        self.abort_sweep_btn = QPushButton("Abort Sweep")
        self.abort_sweep_btn.setFont(self.font)
        self.abort_sweep_btn.clicked.connect(self.abort_sweep)
        self.abort_sweep_btn.setMinimumHeight(35)
        self.abort_sweep_btn.setEnabled(False)
        self.abort_sweep_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")

        sweep_btn_layout.addWidget(self.start_sweep_btn)
        sweep_btn_layout.addWidget(self.abort_sweep_btn)
        sweep_layout.addLayout(sweep_btn_layout)

        # Sweep status
        self.sweep_status_label = QLabel("Status: Ready")
        self.sweep_status_label.setFont(self.font)
        self.sweep_status_label.setWordWrap(True)
        sweep_layout.addWidget(self.sweep_status_label)

        # Data save button
        save_sweep_btn = QPushButton("Save Sweep Data")
        save_sweep_btn.setFont(self.font)
        save_sweep_btn.clicked.connect(self.save_sweep_data)
        save_sweep_btn.setMinimumHeight(30)
        sweep_layout.addWidget(save_sweep_btn)

        self.sweep_group.setLayout(sweep_layout)
        parent_layout.addWidget(self.sweep_group)

    def update_sweep_options(self):
        """Update sweep type options based on current modulation state"""
        current_selection = self.sweep_type_combo.currentText()

        # Block signals while updating
        self.sweep_type_combo.blockSignals(True)
        self.sweep_type_combo.clear()

        # Always add RF options
        sweep_options = ["RF Frequency", "RF Power"]

        # Check modulation state and add appropriate options
        mod_type = self.mod_type_reading_label.text()
        mod_state = self.mod_state_reading_label.text()

        if mod_state == "ON":
            if mod_type == "AM":
                sweep_options.extend(["AM Frequency", "AM Depth"])
            elif mod_type == "FM":
                sweep_options.extend(["FM Frequency", "FM Deviation"])

        # Add all options
        self.sweep_type_combo.addItems(sweep_options)

        # Try to restore previous selection if still available
        index = self.sweep_type_combo.findText(current_selection)
        if index >= 0:
            self.sweep_type_combo.setCurrentIndex(index)
        else:
            self.sweep_type_combo.setCurrentIndex(0)

        # Unblock signals
        self.sweep_type_combo.blockSignals(False)

        # Update ranges for current selection
        self.on_sweep_type_changed(self.sweep_type_combo.currentText())

    def on_sweep_type_changed(self, sweep_type):
        """Update sweep parameter ranges based on type"""
        if sweep_type == "RF Frequency":
            self.sweep_start_spin.setRange(100000, 26500000000)
            self.sweep_stop_spin.setRange(100000, 26500000000)
            self.sweep_start_spin.setDecimals(0)
            self.sweep_stop_spin.setDecimals(0)
            self.sweep_start_spin.setValue(1000000000)
            self.sweep_stop_spin.setValue(2000000000)
            self.sweep_start_suffix.setText("Hz")
            self.sweep_stop_suffix.setText("Hz")
        elif sweep_type == "RF Power":
            self.sweep_start_spin.setRange(-21.0, 15.0)
            self.sweep_stop_spin.setRange(-21.0, 15.0)
            self.sweep_start_spin.setDecimals(2)
            self.sweep_stop_spin.setDecimals(2)
            self.sweep_start_spin.setValue(-10.0)
            self.sweep_stop_spin.setValue(10.0)
            self.sweep_start_suffix.setText("dBm")
            self.sweep_stop_suffix.setText("dBm")
        elif sweep_type == "AM Frequency":
            self.sweep_start_spin.setRange(0.1, 1000000)
            self.sweep_stop_spin.setRange(0.1, 1000000)
            self.sweep_start_spin.setDecimals(1)
            self.sweep_stop_spin.setDecimals(1)
            self.sweep_start_spin.setValue(100)
            self.sweep_stop_spin.setValue(10000)
            self.sweep_start_suffix.setText("Hz")
            self.sweep_stop_suffix.setText("Hz")
        elif sweep_type == "AM Depth":
            self.sweep_start_spin.setRange(0, 100)
            self.sweep_stop_spin.setRange(0, 100)
            self.sweep_start_spin.setDecimals(0)
            self.sweep_stop_spin.setDecimals(0)
            self.sweep_start_spin.setValue(0)
            self.sweep_stop_spin.setValue(100)
            self.sweep_start_suffix.setText("%")
            self.sweep_stop_suffix.setText("%")
        elif sweep_type == "FM Frequency":
            self.sweep_start_spin.setRange(0.1, 1000000)
            self.sweep_stop_spin.setRange(0.1, 1000000)
            self.sweep_start_spin.setDecimals(1)
            self.sweep_stop_spin.setDecimals(1)
            self.sweep_start_spin.setValue(100)
            self.sweep_stop_spin.setValue(10000)
            self.sweep_start_suffix.setText("Hz")
            self.sweep_stop_suffix.setText("Hz")
        elif sweep_type == "FM Deviation":
            self.sweep_start_spin.setRange(1, 10000000)
            self.sweep_stop_spin.setRange(1, 10000000)
            self.sweep_start_spin.setDecimals(0)
            self.sweep_stop_spin.setDecimals(0)
            self.sweep_start_spin.setValue(1000)
            self.sweep_stop_spin.setValue(100000)
            self.sweep_start_suffix.setText("Hz")
            self.sweep_stop_suffix.setText("Hz")

    def start_sweep(self):
        """Start parameter sweep"""
        if not self.bnc845:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.sweep_thread and self.sweep_thread.isRunning():
            QMessageBox.warning(self, "Sweep Active", "A sweep is already running")
            return

        # Stop monitoring if active
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.stop_monitoring()

        # Clear previous sweep data
        self.sweep_data_storage = []

        # Get sweep parameters
        sweep_config = {'type': self.sweep_type_combo.currentText(), 'start': self.sweep_start_spin.value(),
            'stop': self.sweep_stop_spin.value(), 'steps': self.sweep_steps_spin.value(),
            'delay': self.sweep_delay_spin.value()}

        # Validate parameters
        if sweep_config['start'] >= sweep_config['stop']:
            QMessageBox.warning(self, "Invalid Range", "Start value must be less than stop value")
            return

        # Create and start sweep thread
        is_emulation = (self.bnc845 == 'Emulation')
        self.sweep_thread = SweepThread(self.bnc845, self.command, sweep_config, is_emulation)
        self.sweep_thread.sweep_data_signal.connect(self.update_sweep_data)
        self.sweep_thread.sweep_complete_signal.connect(self.on_sweep_complete)
        self.sweep_thread.sweep_status_signal.connect(self.update_sweep_status)
        self.sweep_thread.error_signal.connect(self.on_sweep_error)
        self.sweep_thread.start()

        # Update UI
        self.start_sweep_btn.setEnabled(False)
        self.abort_sweep_btn.setEnabled(True)
        self.sweep_status_label.setText("Status: Sweep in progress...")
        print("Sweep started")

    def abort_sweep(self):
        """Abort current sweep"""
        if self.sweep_thread and self.sweep_thread.isRunning():
            self.sweep_thread.stop()
            self.sweep_thread.wait()
            self.sweep_status_label.setText("Status: Sweep aborted")
            self.start_sweep_btn.setEnabled(True)
            self.abort_sweep_btn.setEnabled(False)
            print("Sweep aborted")

    def update_sweep_data(self, sweep_data):
        """Update plot with sweep data"""
        # Store data
        self.sweep_data_storage.append(sweep_data)

        # Update plots (append to existing data)
        self.time_data.append(sweep_data['time'])
        self.freq_data.append(sweep_data['frequency'])
        self.power_data.append(sweep_data['power'])

        self.freq_curve.setData(self.time_data, self.freq_data)
        self.power_curve.setData(self.time_data, self.power_data)

    def on_sweep_complete(self):
        """Handle sweep completion"""
        self.sweep_status_label.setText(f"Status: Sweep complete ({len(self.sweep_data_storage)} points)")
        self.start_sweep_btn.setEnabled(True)
        self.abort_sweep_btn.setEnabled(False)
        print("Sweep completed")
        QMessageBox.information(self, "Sweep Complete",
                                f"Sweep completed successfully!\n\nTotal points: {len(self.sweep_data_storage)}")

    def update_sweep_status(self, status_msg):
        """Update sweep status label"""
        self.sweep_status_label.setText(f"Status: {status_msg}")

    def on_sweep_error(self, error_msg):
        """Handle sweep error"""
        self.sweep_status_label.setText(f"Error: {error_msg}")
        self.start_sweep_btn.setEnabled(True)
        self.abort_sweep_btn.setEnabled(False)
        QMessageBox.critical(self, "Sweep Error", error_msg)

    def save_sweep_data(self):
        """Save sweep data to file"""
        if not self.sweep_data_storage:
            QMessageBox.warning(self, "No Data", "No sweep data to save")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sweep_type = self.sweep_type_combo.currentText().replace(" ", "_")
            filename = f"bnc845_sweep_{sweep_type}_{timestamp}.csv"

            with open(filename, 'w') as f:
                # Write header
                f.write(f"# BNC 845 RF Sweep Data\n")
                f.write(f"# Sweep Type: {self.sweep_type_combo.currentText()}\n")
                f.write(f"# Start: {self.sweep_start_spin.value()} {self.sweep_start_suffix.text()}\n")
                f.write(f"# Stop: {self.sweep_stop_spin.value()} {self.sweep_stop_suffix.text()}\n")
                f.write(f"# Steps: {self.sweep_steps_spin.value()} {self.sweep_steps_suffix.text()}\n")
                f.write(f"# Delay: {self.sweep_delay_spin.value()} s\n")
                f.write(f"# Timestamp: {timestamp}\n")
                f.write("#\n")
                f.write("Step,Parameter Value,Time (s),Frequency (Hz),Power (dBm)\n")

                # Write data
                for data in self.sweep_data_storage:
                    f.write(f"{data['step']},{data['param_value']},{data['time']:.3f},"
                            f"{data['frequency']},{data['power']}\n")

            QMessageBox.information(self, "Data Saved",
                                    f"Sweep data saved to:\n{filename}\n\nTotal points: {len(self.sweep_data_storage)}")

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving data:\n{str(e)}")

    def setup_monitor_section(self, parent_layout):
        """Setup monitor control section"""
        monitor_group = QGroupBox("Real-time Monitoring")
        monitor_layout = QVBoxLayout()

        button_layout = QHBoxLayout()
        self.start_monitor_btn = QPushButton("Start Monitor")
        self.start_monitor_btn.clicked.connect(self.start_monitoring)
        self.start_monitor_btn.setEnabled(False)
        self.start_monitor_btn.setMinimumHeight(30)
        self.start_monitor_btn.setFont(self.font)

        self.stop_monitor_btn = QPushButton("Stop Monitor")
        self.stop_monitor_btn.clicked.connect(self.stop_monitoring)
        self.stop_monitor_btn.setEnabled(False)
        self.stop_monitor_btn.setMinimumHeight(30)
        self.stop_monitor_btn.setFont(self.font)

        button_layout.addWidget(self.start_monitor_btn)
        button_layout.addWidget(self.stop_monitor_btn)
        monitor_layout.addLayout(button_layout)

        self.monitor_status = QLabel("Status: Not monitoring")
        self.monitor_status.setWordWrap(True)
        self.monitor_status.setFont(self.font)
        monitor_layout.addWidget(self.monitor_status)

        # Update readings button
        update_btn = QPushButton("Update Readings")
        update_btn.clicked.connect(self.update_readings_from_instrument)
        update_btn.setFont(self.font)
        update_btn.setMinimumHeight(30)
        monitor_layout.addWidget(update_btn)

        monitor_group.setLayout(monitor_layout)
        parent_layout.addWidget(monitor_group)

    def setup_data_section(self, parent_layout):
        """Setup data control section"""
        data_group = QGroupBox("Data Control")
        data_layout = QVBoxLayout()

        self.clear_data_button = QPushButton("Clear Plot Data")
        self.clear_data_button.clicked.connect(self.clear_plot_data)
        self.clear_data_button.setFont(self.font)
        self.clear_data_button.setMinimumHeight(30)

        self.save_data_button = QPushButton("Save Monitor Data")
        self.save_data_button.clicked.connect(self.save_data)
        self.save_data_button.setFont(self.font)
        self.save_data_button.setMinimumHeight(30)

        data_layout.addWidget(self.clear_data_button)
        data_layout.addWidget(self.save_data_button)

        data_group.setLayout(data_layout)
        parent_layout.addWidget(data_group)

    def create_plot_panel(self):
        """Create the plotting panel"""
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        plot_title = QLabel("Real-time RF Monitoring")
        plot_title.setFont(self.titlefont)
        plot_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(plot_title)

        # Create frequency plot
        self.freq_plot_widget = pg.PlotWidget()
        self.freq_plot_widget.setBackground('w')
        self.freq_plot_widget.setLabel('left', 'Frequency', units='Hz')
        self.freq_plot_widget.setLabel('bottom', 'Time', units='s')
        self.freq_plot_widget.setTitle('Frequency vs Time')
        self.freq_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.freq_plot_widget.addLegend()

        self.freq_curve = self.freq_plot_widget.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), symbol='o', symbolSize=4,
            symbolBrush=(0, 0, 255), name='Frequency')

        # Create power plot
        self.power_plot_widget = pg.PlotWidget()
        self.power_plot_widget.setBackground('w')
        self.power_plot_widget.setLabel('left', 'Power', units='dBm')
        self.power_plot_widget.setLabel('bottom', 'Time', units='s')
        self.power_plot_widget.setTitle('Power vs Time')
        self.power_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.power_plot_widget.addLegend()

        self.power_curve = self.power_plot_widget.plot(pen=pg.mkPen(color=(255, 0, 0), width=2), symbol='o',
            symbolSize=4, symbolBrush=(255, 0, 0), name='Power')

        right_layout.addWidget(self.freq_plot_widget)
        right_layout.addWidget(self.power_plot_widget)

        right_panel.setLayout(right_layout)
        return right_panel

    def on_modulation_type_changed(self, index):
        """Handle modulation type selection change"""
        self.mod_stack.setCurrentIndex(index)
        QTimer.singleShot(0, self.update_modulation_size)

    def update_modulation_size(self):
        """Update the modulation groupbox size to fit content"""
        current_widget = self.mod_stack.currentWidget()
        current_widget.updateGeometry()
        self.mod_stack.updateGeometry()
        self.mod_group.updateGeometry()
        self.left_layout.update()
        self.left_layout.activate()

    def set_frequency(self):
        """Set RF frequency"""
        if not self.bnc845:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        try:
            freq = str(int(self.freq_spinbox.value()))

            if self.bnc845 == 'Emulation':
                print(f"[Emulation] Set frequency to {freq} Hz")
                self.freq_reading_label.setText(f"{float(freq) / 1e9:.4f} GHz")
                return

            success = self.command.set_frequency(self.bnc845, freq)
            if success:
                self.update_readings_from_instrument()
                print(f"Set frequency to {freq} Hz")
            else:
                QMessageBox.warning(self, "Invalid Value", "Frequency out of range")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting frequency:\n{str(e)}")

    def set_power(self):
        """Set RF power"""
        if not self.bnc845:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        try:
            power = str(self.power_spinbox.value())

            if self.bnc845 == 'Emulation':
                print(f"[Emulation] Set power to {power} dBm")
                self.power_reading_label.setText(f"{float(power):.2f} dBm")
                return

            success = self.command.set_power(self.bnc845, power)
            if success:
                self.update_readings_from_instrument()
                print(f"Set power to {power} dBm")
            else:
                QMessageBox.warning(self, "Invalid Value", "Power out of range")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting power:\n{str(e)}")

    def set_output(self, state):
        """Set RF output state"""
        if not self.bnc845:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        try:
            if self.bnc845 == 'Emulation':
                print(f"[Emulation] Set output {state}")
                self.rf_state_reading_label.setText("ON" if state == 'on' else "OFF")
                return

            self.command.set_output(self.bnc845, state)
            self.update_readings_from_instrument()
            print(f"Set output {state}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting output:\n{str(e)}")

    def apply_am_settings(self):
        """Apply AM modulation settings"""
        if not self.bnc845:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        try:
            freq = str(self.am_freq_spinbox.value())
            depth = str(self.am_depth_spinbox.value())
            source = self.am_source_combo.currentText()

            if self.bnc845 == 'Emulation':
                print(f"[Emulation] Applied AM settings: {freq} Hz, {depth}%, {source}")
                QMessageBox.information(self, "Success", "AM settings applied successfully (Emulation)")
                return

            self.command.set_am_frequency(self.bnc845, freq)
            self.command.set_am_depth(self.bnc845, depth)
            self.command.set_am_source(self.bnc845, source)

            print(f"Applied AM settings: {freq} Hz, {depth}%, {source}")
            QMessageBox.information(self, "Success", "AM settings applied successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error applying AM settings:\n{str(e)}")

    def set_am_state(self, state):
        """Set AM state"""
        if not self.bnc845:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        try:
            if self.bnc845 == 'Emulation':
                print(f"[Emulation] Set AM {state}")
                if state == 'on':
                    self.mod_type_reading_label.setText('AM')
                    self.mod_state_reading_label.setText('ON')
                else:
                    self.mod_type_reading_label.setText('OFF')
                    self.mod_state_reading_label.setText('OFF')
                # Update sweep options when modulation state changes
                self.update_sweep_options()
                return

            self.command.set_am_state(self.bnc845, state)
            self.update_readings_from_instrument()
            # Update sweep options when modulation state changes
            self.update_sweep_options()
            print(f"Set AM {state}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting AM state:\n{str(e)}")

    def apply_fm_settings(self):
        """Apply FM modulation settings"""
        if not self.bnc845:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        try:
            freq = str(self.fm_freq_spinbox.value())
            dev = str(self.fm_dev_spinbox.value())

            if self.bnc845 == 'Emulation':
                print(f"[Emulation] Applied FM settings: {freq} Hz, {dev} Hz deviation")
                QMessageBox.information(self, "Success", "FM settings applied successfully (Emulation)")
                return

            self.command.set_fm_frequency(self.bnc845, freq)
            self.command.set_fm_deviation(self.bnc845, dev)

            print(f"Applied FM settings: {freq} Hz, {dev} Hz deviation")
            QMessageBox.information(self, "Success", "FM settings applied successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error applying FM settings:\n{str(e)}")

    def set_fm_state(self, state):
        """Set FM state"""
        if not self.bnc845:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        try:
            if self.bnc845 == 'Emulation':
                print(f"[Emulation] Set FM {state}")
                if state == 'on':
                    self.mod_type_reading_label.setText('FM')
                    self.mod_state_reading_label.setText('ON')
                else:
                    self.mod_type_reading_label.setText('OFF')
                    self.mod_state_reading_label.setText('OFF')
                # Update sweep options when modulation state changes
                self.update_sweep_options()
                return

            self.command.set_fm_state(self.bnc845, state)
            self.update_readings_from_instrument()
            # Update sweep options when modulation state changes
            self.update_sweep_options()
            print(f"Set FM {state}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting FM state:\n{str(e)}")

    def apply_pm_settings(self):
        """Apply PM modulation settings"""
        if not self.bnc845:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        try:
            dev = str(self.pm_dev_spinbox.value())

            if self.bnc845 == 'Emulation':
                print(f"[Emulation] Applied PM settings: {dev} rad deviation")
                QMessageBox.information(self, "Success", "PM settings applied successfully (Emulation)")
                return

            self.command.set_pm_deviation(self.bnc845, dev)
            print(f"Applied PM settings: {dev} rad deviation")
            QMessageBox.information(self, "Success", "PM settings applied successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error applying PM settings:\n{str(e)}")

    def set_pm_state(self, state):
        """Set PM state"""
        if not self.bnc845:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        try:
            if self.bnc845 == 'Emulation':
                print(f"[Emulation] Set PM {state}")
                if state == 'on':
                    self.mod_type_reading_label.setText('PM')
                    self.mod_state_reading_label.setText('ON')
                else:
                    self.mod_type_reading_label.setText('OFF')
                    self.mod_state_reading_label.setText('OFF')
                # Update sweep options when modulation state changes
                self.update_sweep_options()
                return

            self.command.set_pm_state(self.bnc845, state)
            self.update_readings_from_instrument()
            # Update sweep options when modulation state changes
            self.update_sweep_options()
            print(f"Set PM {state}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting PM state:\n{str(e)}")

    def set_pulse_state(self, state):
        """Set Pulse state"""
        if not self.bnc845:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        try:
            if self.bnc845 == 'Emulation':
                print(f"[Emulation] Set Pulse {state}")
                if state == 'on':
                    self.mod_type_reading_label.setText('PULSE')
                    self.mod_state_reading_label.setText('ON')
                else:
                    self.mod_type_reading_label.setText('OFF')
                    self.mod_state_reading_label.setText('OFF')
                # Update sweep options when modulation state changes
                self.update_sweep_options()
                return

            self.command.set_pulse_state(self.bnc845, state)
            self.update_readings_from_instrument()
            # Update sweep options when modulation state changes
            self.update_sweep_options()
            print(f"Set Pulse {state}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting Pulse state:\n{str(e)}")

    def update_readings_from_instrument(self):
        """Update all reading labels from instrument"""
        if not self.bnc845 or self.bnc845 == 'Emulation':
            return

        try:
            # Update frequency
            freq = self.command.get_frequency(self.bnc845).strip()
            self.freq_reading_label.setText(f"{float(freq) / 1e9:.4f} GHz")

            # Update power
            power = self.command.get_power(self.bnc845).strip()
            self.power_reading_label.setText(f"{float(power):.2f} dBm")

            # Update RF state
            state = self.command.get_output(self.bnc845).strip()
            self.rf_state_reading_label.setText("ON" if state == '1' else "OFF")

            # Check modulation types
            am_state = self.command.get_am_state(self.bnc845).strip()
            fm_state = self.command.get_fm_state(self.bnc845).strip()
            pm_state = self.command.get_pm_state(self.bnc845).strip()
            pulse_state = self.command.get_pulse_state(self.bnc845).strip()

            # Determine active modulation
            if am_state == '1' or am_state.upper() == 'ON':
                self.mod_type_reading_label.setText('AM')
                self.mod_state_reading_label.setText('ON')
            elif fm_state == '1' or fm_state.upper() == 'ON':
                self.mod_type_reading_label.setText('FM')
                self.mod_state_reading_label.setText('ON')
            elif pm_state == '1' or pm_state.upper() == 'ON':
                self.mod_type_reading_label.setText('PM')
                self.mod_state_reading_label.setText('ON')
            elif pulse_state == '1' or pulse_state.upper() == 'ON':
                self.mod_type_reading_label.setText('PULSE')
                self.mod_state_reading_label.setText('ON')
            else:
                self.mod_type_reading_label.setText('OFF')
                self.mod_state_reading_label.setText('OFF')

            # Update sweep options based on new modulation state
            self.update_sweep_options()

        except Exception as e:
            print(f"Error updating readings: {e}")

    def start_monitoring(self):
        """Start real-time monitoring"""
        if not self.bnc845:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        # Clear previous data
        self.time_data = []
        self.freq_data = []
        self.power_data = []
        self.freq_curve.setData([], [])
        self.power_curve.setData([], [])

        # Start monitor thread
        is_emulation = (self.bnc845 == 'Emulation')
        self.monitor_thread = MonitorThread(self.bnc845, self.command, is_emulation)
        self.monitor_thread.data_signal.connect(self.update_plots)
        self.monitor_thread.error_signal.connect(self.on_monitor_error)
        self.monitor_thread.finished.connect(self.on_monitor_finished)

        self.monitor_thread.start()

        self.start_monitor_btn.setEnabled(False)
        self.stop_monitor_btn.setEnabled(True)
        self.monitor_status.setText("Status: Monitoring active")

    def stop_monitoring(self):
        """Stop real-time monitoring"""
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()

        self.start_monitor_btn.setEnabled(True)
        self.stop_monitor_btn.setEnabled(False)
        self.monitor_status.setText("Status: Not monitoring")

    def update_plots(self, time_val, freq, power):
        """Update plots with new data"""
        self.time_data.append(time_val)
        self.freq_data.append(freq)
        self.power_data.append(power)

        # Update plots
        self.freq_curve.setData(self.time_data, self.freq_data)
        self.power_curve.setData(self.time_data, self.power_data)

    def on_monitor_error(self, error_msg):
        """Handle monitoring error"""
        print(f"Monitor error: {error_msg}")
        self.monitor_status.setText(f"Error: {error_msg}")
        QMessageBox.warning(self, "Monitor Error", error_msg)

    def on_monitor_finished(self):
        """Handle monitor thread finished"""
        self.start_monitor_btn.setEnabled(True)
        self.stop_monitor_btn.setEnabled(False)

    def clear_plot_data(self):
        """Clear plot data"""
        self.time_data = []
        self.freq_data = []
        self.power_data = []
        self.freq_curve.setData([], [])
        self.power_curve.setData([], [])

        QMessageBox.information(self, "Data Cleared", "Plot data has been cleared")

    def save_data(self):
        """Save monitoring data to file"""
        if not self.time_data:
            QMessageBox.warning(self, "No Data", "No data to save")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bnc845_monitor_{timestamp}.csv"

            with open(filename, 'w') as f:
                f.write("Time (s),Frequency (Hz),Power (dBm)\n")
                for i in range(len(self.time_data)):
                    f.write(f"{self.time_data[i]},{self.freq_data[i]},{self.power_data[i]}\n")

            QMessageBox.information(self, "Data Saved",
                                    f"Data saved to:\n{filename}\n\nTotal points: {len(self.time_data)}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving data:\n{str(e)}")

    def closeEvent(self, event):
        """Handle window close"""
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()

        if self.sweep_thread and self.sweep_thread.isRunning():
            self.sweep_thread.stop()
            self.sweep_thread.wait()

        if self.bnc845 and self.bnc845 != 'Emulation':
            try:
                self.bnc845.close()
            except:
                pass

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BNC845RF()
    window.show()
    sys.exit(app.exec())