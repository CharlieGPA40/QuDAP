from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
                             QPushButton, QComboBox, QCheckBox, QLineEdit, QMessageBox, QScrollArea, QSizePolicy,
                             QDoubleSpinBox, QSpinBox)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import sys
import pyvisa as visa
import random
import time
import pyqtgraph as pg
from datetime import datetime
import numpy as np

# Import the standalone connection class
try:
    from instrument.instrument_connection import InstrumentConnection
except ImportError:
    from QuDAP.instrument.instrument_connection import InstrumentConnection


class MonitorThread(QThread):
    """Thread to monitor lock-in parameters in real-time"""

    data_signal = pyqtSignal(float, float, float, float, float)  # (time, X, Y, R, Theta)
    error_signal = pyqtSignal(str)

    def __init__(self, instrument, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.should_stop = False
        self.start_time = time.time()

    def run(self):
        """Monitor the instrument parameters"""
        try:
            while not self.should_stop:
                try:
                    # Use SNAP command for efficient reading
                    values = self.instrument.query("SNAP? 1,2,3,4")
                    X, Y, R, Theta = values.split(',')
                    X = float(X)
                    Y = float(Y)
                    R = float(R)
                    Theta = float(Theta)

                    elapsed_time = time.time() - self.start_time
                    self.data_signal.emit(elapsed_time, X, Y, R, Theta)
                    time.sleep(0.1)

                except Exception as e:
                    self.error_signal.emit(f"Monitoring error: {str(e)}")
                    break

        except Exception as e:
            self.error_signal.emit(f"Thread error: {str(e)}")

    def stop(self):
        """Stop monitoring"""
        self.should_stop = True


class EmulationThread(QThread):
    """Thread for emulation mode monitoring"""

    data_signal = pyqtSignal(float, float, float, float, float)  # (time, X, Y, R, Theta)
    error_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.should_stop = False
        self.start_time = time.time()

    def run(self):
        """Monitor in emulation mode"""
        try:
            while not self.should_stop:
                try:
                    X = random.randint(0, 1000) / 1000
                    Y = random.randint(0, 1000) / 1000
                    R = np.sqrt(X ** 2 + Y ** 2)
                    Theta = random.randint(0, 360)

                    elapsed_time = time.time() - self.start_time
                    self.data_signal.emit(elapsed_time, X, Y, R, Theta)
                    time.sleep(0.1)

                except Exception as e:
                    self.error_signal.emit(f"Emulation error: {str(e)}")
                    break

        except Exception as e:
            self.error_signal.emit(f"Thread error: {str(e)}")

    def stop(self):
        """Stop monitoring"""
        self.should_stop = True


class ContinuousReadingThread(QThread):
    """Thread for continuous reading updates when connected"""

    reading_signal = pyqtSignal(float, float, float, float)  # (X, Y, R, Theta)
    error_signal = pyqtSignal(str)

    def __init__(self, instrument, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.should_stop = False

    def run(self):
        """Continuously read instrument parameters"""
        try:
            while not self.should_stop:
                try:
                    values = self.instrument.query("SNAP? 1,2,3,4")
                    X, Y, R, Theta = values.split(',')
                    X = float(X)
                    Y = float(Y)
                    R = float(R)
                    Theta = float(Theta)

                    self.reading_signal.emit(X, Y, R, Theta)
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


class SweepThread(QThread):
    """Thread to perform frequency or amplitude sweep"""

    progress_signal = pyqtSignal(int, str)
    data_point_signal = pyqtSignal(float, float, float, float, float)  # (sweep_value, X, Y, R, Theta)
    error_signal = pyqtSignal(str)
    info_signal = pyqtSignal(str, str)
    sweep_complete_signal = pyqtSignal()

    def __init__(self, instrument, sweep_type, start_value, stop_value, step_value, use_auto_rate=True,
                 manual_rate=None, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.sweep_type = sweep_type
        self.start_value = start_value
        self.stop_value = stop_value
        self.step_value = step_value
        self.use_auto_rate = use_auto_rate
        self.manual_rate = manual_rate
        self.should_stop = False

    def get_time_constant(self):
        """Get current time constant from instrument"""
        try:
            # SR830 OFLT? returns time constant index (0-19)
            tc_index = int(self.instrument.query('OFLT?').strip())
            # SR830 time constants: 10µs to 30ks
            tc_values = [10e-6, 30e-6, 100e-6, 300e-6, 1e-3, 3e-3, 10e-3, 30e-3, 100e-3, 300e-3, 1, 3, 10, 30, 100, 300,
                         1e3, 3e3, 10e3, 30e3]
            tc_value = tc_values[tc_index] if tc_index < len(tc_values) else 0.1
            return tc_value
        except Exception as e:
            print(f"Error reading time constant: {e}")
            return 0.1

    def calculate_sweep_rate(self, tc_value):
        """Calculate sweep rate as 2x time constant"""
        rate_seconds = 2 * tc_value
        rate_ms = rate_seconds * 1000
        return max(50, min(1000000, rate_ms))

    def run(self):
        """Execute the sweep"""
        try:
            if not self.instrument:
                self.error_signal.emit("SR830 is not connected")
                return

            if self.instrument == 'Emulation':
                if self.use_auto_rate:
                    rate_ms = 100
                    self.info_signal.emit("Auto Rate Configured (Emulation)",
                                          f"Using default sweep rate: {rate_ms:.2f} ms")
                else:
                    rate_ms = self.manual_rate if self.manual_rate else 100
            else:
                if self.use_auto_rate:
                    tc_value = self.get_time_constant()
                    rate_ms = self.calculate_sweep_rate(tc_value)
                    self.info_signal.emit("Auto Rate Configured",
                                          f"Time Constant: {tc_value * 1000:.2f} ms\nSweep Rate: {rate_ms:.2f} ms (2×TC)")
                else:
                    rate_ms = self.manual_rate if self.manual_rate else 100

            if self.start_value <= self.stop_value:
                sweep_points = np.arange(self.start_value, self.stop_value + self.step_value / 2, self.step_value)
            else:
                sweep_points = np.arange(self.start_value, self.stop_value - self.step_value / 2, -self.step_value)

            total_points = len(sweep_points)
            if total_points == 0:
                self.error_signal.emit("No sweep points generated")
                return

            sweep_type_name = "Frequency" if self.sweep_type == 'frequency' else "Amplitude"
            unit = "Hz" if self.sweep_type == 'frequency' else "V"

            self.info_signal.emit(f"{sweep_type_name} Sweep Started",
                                  f"Sweeping from {self.start_value} {unit} to {self.stop_value} {unit}\n"
                                  f"Total points: {total_points}\nRate: {rate_ms:.2f} ms/point")

            for i, point in enumerate(sweep_points):
                if self.should_stop:
                    return

                if self.instrument == 'Emulation':
                    x = random.randint(0, 1000) / 1000
                    y = random.randint(0, 1000) / 1000
                    r = np.sqrt(x ** 2 + y ** 2)
                    theta = random.randint(0, 360)
                    status = f"{sweep_type_name}: {point:.2f} {unit} ({i + 1}/{total_points})"
                else:
                    if self.sweep_type == 'frequency':
                        self.instrument.write(f'FREQ {point}')
                        status = f"Frequency: {point:.2f} Hz ({i + 1}/{total_points})"
                    else:
                        self.instrument.write(f'SLVL {point}')
                        status = f"Amplitude: {point:.6f} V ({i + 1}/{total_points})"

                    time.sleep(rate_ms / 1000.0)

                    values = self.instrument.query("SNAP? 1,2,3,4")
                    x, y, r, theta = values.split(',')
                    x = float(x)
                    y = float(y)
                    r = float(r)
                    theta = float(theta)

                self.data_point_signal.emit(point, x, y, r, theta)
                progress = int((i + 1) / total_points * 100)
                self.progress_signal.emit(progress, status)

                if self.instrument == 'Emulation':
                    time.sleep(rate_ms / 1000.0)

            self.sweep_complete_signal.emit()
            self.info_signal.emit("Sweep Complete",
                                  f"{sweep_type_name} sweep finished successfully\nCollected {total_points} data points")

        except Exception as e:
            import traceback
            self.error_signal.emit(f"Sweep error:\n{str(e)}\n\n{traceback.format_exc()}")

    def stop(self):
        """Stop the sweep"""
        self.should_stop = True


class SR830(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SR830 Lock-in Amplifier")
        self.setGeometry(100, 100, 1600, 900)

        self.SR830_instrument = None
        self.monitor_thread = None
        self.sweep_thread = None
        self.reading_thread = None
        self.isConnect = False
        self.is_plotting = False

        # Data storage
        self.time_data = []
        self.sweep_param_data = []
        self.x_data = []
        self.y_data = []
        self.r_data = []
        self.theta_data = []

        self.is_sweep_mode = False

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
        self.scroll_area.setFixedWidth(500)

        left_content = QWidget()
        left_content.setMaximumWidth(480)

        self.left_layout = QVBoxLayout()
        self.left_layout.setContentsMargins(10, 10, 10, 10)
        self.left_layout.setSpacing(10)

        # Title
        title = QLabel("SR830 Lock-in Amplifier")
        title.setFont(self.titlefont)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_layout.addWidget(title)

        # Setup sections
        self.setup_connection_section(self.left_layout)
        self.setup_readings_section(self.left_layout)
        self.setup_configuration_section(self.left_layout)
        self.setup_auto_functions_section(self.left_layout)
        self.setup_monitor_section(self.left_layout)
        self.setup_data_control_section(self.left_layout)

        self.left_layout.addStretch()

        left_content.setLayout(self.left_layout)
        self.scroll_area.setWidget(left_content)

        # Right panel - Plots
        right_panel = self.create_plot_panel()

        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(right_panel, 1)

        central_widget.setLayout(main_layout)

    def setup_connection_section(self, parent_layout):
        """Setup device connection section"""
        self.connection_widget = InstrumentConnection(instrument_list=["SR830 Lock-in"], allow_emulation=True,
            title="Instrument Connection")
        self.connection_widget.instrument_connected.connect(self.on_instrument_connected)
        self.connection_widget.instrument_disconnected.connect(self.on_instrument_disconnected)
        parent_layout.addWidget(self.connection_widget)

    def setup_readings_section(self, parent_layout):
        """Setup current readings section"""
        readings_group = QGroupBox("Current Readings")
        readings_layout = QVBoxLayout()

        # X Reading
        x_layout = QHBoxLayout()
        x_label = QLabel("X:")
        x_label.setFont(self.font)
        x_label.setFixedWidth(100)
        self.x_reading_label = QLabel("N/A V")
        self.x_reading_label.setFont(self.font)
        x_layout.addWidget(x_label)
        x_layout.addWidget(self.x_reading_label, 1)
        readings_layout.addLayout(x_layout)

        # Y Reading
        y_layout = QHBoxLayout()
        y_label = QLabel("Y:")
        y_label.setFont(self.font)
        y_label.setFixedWidth(100)
        self.y_reading_label = QLabel("N/A V")
        self.y_reading_label.setFont(self.font)
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.y_reading_label, 1)
        readings_layout.addLayout(y_layout)

        # R (Magnitude)
        r_layout = QHBoxLayout()
        r_label = QLabel("R:")
        r_label.setFont(self.font)
        r_label.setFixedWidth(100)
        self.r_reading_label = QLabel("N/A V")
        self.r_reading_label.setFont(self.font)
        r_layout.addWidget(r_label)
        r_layout.addWidget(self.r_reading_label, 1)
        readings_layout.addLayout(r_layout)

        # Theta (Phase)
        theta_layout = QHBoxLayout()
        theta_label = QLabel("θ (Theta):")
        theta_label.setFont(self.font)
        theta_label.setFixedWidth(100)
        self.theta_reading_label = QLabel("N/A deg")
        self.theta_reading_label.setFont(self.font)
        theta_layout.addWidget(theta_label)
        theta_layout.addWidget(self.theta_reading_label, 1)
        readings_layout.addLayout(theta_layout)

        # Frequency
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Frequency:")
        freq_label.setFont(self.font)
        freq_label.setFixedWidth(100)
        self.freq_reading_label = QLabel("N/A Hz")
        self.freq_reading_label.setFont(self.font)
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_reading_label, 1)
        readings_layout.addLayout(freq_layout)

        # Amplitude
        amp_layout = QHBoxLayout()
        amp_label = QLabel("Amplitude:")
        amp_label.setFont(self.font)
        amp_label.setFixedWidth(100)
        self.amp_reading_label = QLabel("N/A Vrms")
        self.amp_reading_label.setFont(self.font)
        amp_layout.addWidget(amp_label)
        amp_layout.addWidget(self.amp_reading_label, 1)
        readings_layout.addLayout(amp_layout)

        # Sensitivity
        sens_layout = QHBoxLayout()
        sens_label = QLabel("Sensitivity:")
        sens_label.setFont(self.font)
        sens_label.setFixedWidth(100)
        self.sens_reading_label = QLabel("N/A")
        self.sens_reading_label.setFont(self.font)
        sens_layout.addWidget(sens_label)
        sens_layout.addWidget(self.sens_reading_label, 1)
        readings_layout.addLayout(sens_layout)

        # Time Constant
        tc_layout = QHBoxLayout()
        tc_label = QLabel("Time Constant:")
        tc_label.setFont(self.font)
        tc_label.setFixedWidth(100)
        self.tc_reading_label = QLabel("N/A")
        self.tc_reading_label.setFont(self.font)
        tc_layout.addWidget(tc_label)
        tc_layout.addWidget(self.tc_reading_label, 1)
        readings_layout.addLayout(tc_layout)

        # Update button
        update_btn = QPushButton("Update Readings")
        update_btn.clicked.connect(self.update_readings_from_instrument)
        update_btn.setFont(self.font)
        update_btn.setMinimumHeight(30)
        readings_layout.addWidget(update_btn)

        readings_group.setLayout(readings_layout)
        parent_layout.addWidget(readings_group)

    def setup_configuration_section(self, parent_layout):
        """Setup configuration section"""
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()

        # Reference Source
        ref_layout = QHBoxLayout()
        ref_label = QLabel("Reference:")
        ref_label.setFont(self.font)
        ref_label.setFixedWidth(100)
        self.ref_combo = QComboBox()
        self.ref_combo.setFont(self.font)
        self.ref_combo.addItems(["External", "Internal"])
        self.ref_combo.currentIndexChanged.connect(self.apply_reference)
        ref_layout.addWidget(ref_label)
        ref_layout.addWidget(self.ref_combo, 1)
        config_layout.addLayout(ref_layout)

        # Frequency
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Frequency:")
        freq_label.setFont(self.font)
        freq_label.setFixedWidth(100)
        self.freq_entry = QLineEdit()
        self.freq_entry.setFont(self.font)
        self.freq_entry.setPlaceholderText("Hz")
        freq_hz_label = QLabel("Hz")
        freq_hz_label.setFont(self.font)
        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_entry, 1)
        freq_layout.addWidget(freq_hz_label)
        config_layout.addLayout(freq_layout)

        freq_set_btn = QPushButton("Set Frequency")
        freq_set_btn.clicked.connect(self.apply_frequency)
        freq_set_btn.setFont(self.font)
        freq_set_btn.setMinimumHeight(30)
        config_layout.addWidget(freq_set_btn)

        # Sine Output Amplitude
        amp_layout = QHBoxLayout()
        amp_label = QLabel("Sine Amplitude:")
        amp_label.setFont(self.font)
        amp_label.setFixedWidth(100)
        self.amp_entry = QLineEdit()
        self.amp_entry.setFont(self.font)
        self.amp_entry.setPlaceholderText("Vrms")
        amp_vrms_label = QLabel("Vrms")
        amp_vrms_label.setFont(self.font)
        amp_layout.addWidget(amp_label)
        amp_layout.addWidget(self.amp_entry, 1)
        amp_layout.addWidget(amp_vrms_label)
        config_layout.addLayout(amp_layout)

        amp_set_btn = QPushButton("Set Amplitude")
        amp_set_btn.clicked.connect(self.apply_amplitude)
        amp_set_btn.setFont(self.font)
        amp_set_btn.setMinimumHeight(30)
        config_layout.addWidget(amp_set_btn)

        # Sensitivity
        sens_layout = QHBoxLayout()
        sens_label = QLabel("Sensitivity:")
        sens_label.setFont(self.font)
        sens_label.setFixedWidth(100)
        self.sens_combo = QComboBox()
        self.sens_combo.setFont(self.font)
        self.sens_combo.addItems(
            ["Select", "2 nV", "5 nV", "10 nV", "20 nV", "50 nV", "100 nV", "200 nV", "500 nV", "1 µV", "2 µV", "5 µV",
                "10 µV", "20 µV", "50 µV", "100 µV", "200 µV", "500 µV", "1 mV", "2 mV", "5 mV", "10 mV", "20 mV",
                "50 mV", "100 mV", "200 mV", "500 mV", "1 V"])
        self.sens_combo.currentIndexChanged.connect(self.apply_sensitivity)
        sens_layout.addWidget(sens_label)
        sens_layout.addWidget(self.sens_combo, 1)
        config_layout.addLayout(sens_layout)

        # Time Constant
        tc_layout = QHBoxLayout()
        tc_label = QLabel("Time Constant:")
        tc_label.setFont(self.font)
        tc_label.setFixedWidth(100)
        self.tc_combo = QComboBox()
        self.tc_combo.setFont(self.font)
        self.tc_combo.addItems(
            ["Select", "10 µs", "30 µs", "100 µs", "300 µs", "1 ms", "3 ms", "10 ms", "30 ms", "100 ms", "300 ms",
                "1 s", "3 s", "10 s", "30 s", "100 s", "300 s", "1 ks", "3 ks", "10 ks", "30 ks"])
        self.tc_combo.currentIndexChanged.connect(self.apply_time_constant)
        tc_layout.addWidget(tc_label)
        tc_layout.addWidget(self.tc_combo, 1)
        config_layout.addLayout(tc_layout)

        # Filter Slope
        slope_layout = QHBoxLayout()
        slope_label = QLabel("Filter Slope:")
        slope_label.setFont(self.font)
        slope_label.setFixedWidth(100)
        self.slope_combo = QComboBox()
        self.slope_combo.setFont(self.font)
        self.slope_combo.addItems(["Select", "6 dB/oct", "12 dB/oct", "18 dB/oct", "24 dB/oct"])
        self.slope_combo.currentIndexChanged.connect(self.apply_slope)
        slope_layout.addWidget(slope_label)
        slope_layout.addWidget(self.slope_combo, 1)
        config_layout.addLayout(slope_layout)

        config_group.setLayout(config_layout)
        parent_layout.addWidget(config_group)

    def setup_auto_functions_section(self, parent_layout):
        """Setup auto functions section"""
        auto_group = QGroupBox("Auto Functions")
        auto_layout = QHBoxLayout()

        auto_gain_btn = QPushButton("Auto Gain")
        auto_gain_btn.clicked.connect(self.auto_gain)
        auto_gain_btn.setFont(self.font)
        auto_gain_btn.setMinimumHeight(30)

        auto_reserve_btn = QPushButton("Auto Reserve")
        auto_reserve_btn.clicked.connect(self.auto_reserve)
        auto_reserve_btn.setFont(self.font)
        auto_reserve_btn.setMinimumHeight(30)

        auto_phase_btn = QPushButton("Auto Phase")
        auto_phase_btn.clicked.connect(self.auto_phase)
        auto_phase_btn.setFont(self.font)
        auto_phase_btn.setMinimumHeight(30)

        auto_layout.addWidget(auto_gain_btn)
        auto_layout.addWidget(auto_reserve_btn)
        auto_layout.addWidget(auto_phase_btn)

        auto_group.setLayout(auto_layout)
        parent_layout.addWidget(auto_group)

    def setup_monitor_section(self, parent_layout):
        """Setup merged real-time monitoring and sweep section"""
        monitor_group = QGroupBox("Real-time Monitoring & Sweep")
        monitor_layout = QVBoxLayout()

        # Mode selection
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode:")
        mode_label.setFont(self.font)
        mode_label.setFixedWidth(100)
        self.mode_combo = QComboBox()
        self.mode_combo.setFont(self.font)
        self.mode_combo.addItems(["Real-time Monitor", "Frequency Sweep", "Amplitude Sweep"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo, 1)
        monitor_layout.addLayout(mode_layout)

        # Parameter selection
        param_label = QLabel("Select Parameters to Plot:")
        param_label.setFont(self.font)
        monitor_layout.addWidget(param_label)

        self.x_monitor_checkbox = QCheckBox("X")
        self.x_monitor_checkbox.setFont(self.font)
        self.x_monitor_checkbox.setChecked(True)
        self.x_monitor_checkbox.stateChanged.connect(self.on_checkbox_changed)
        monitor_layout.addWidget(self.x_monitor_checkbox)

        self.y_monitor_checkbox = QCheckBox("Y")
        self.y_monitor_checkbox.setFont(self.font)
        self.y_monitor_checkbox.setChecked(True)
        self.y_monitor_checkbox.stateChanged.connect(self.on_checkbox_changed)
        monitor_layout.addWidget(self.y_monitor_checkbox)

        self.r_monitor_checkbox = QCheckBox("R (Magnitude)")
        self.r_monitor_checkbox.setFont(self.font)
        self.r_monitor_checkbox.setChecked(True)
        self.r_monitor_checkbox.stateChanged.connect(self.on_checkbox_changed)
        monitor_layout.addWidget(self.r_monitor_checkbox)

        self.theta_monitor_checkbox = QCheckBox("θ (Phase)")
        self.theta_monitor_checkbox.setFont(self.font)
        self.theta_monitor_checkbox.setChecked(True)
        self.theta_monitor_checkbox.stateChanged.connect(self.on_checkbox_changed)
        monitor_layout.addWidget(self.theta_monitor_checkbox)

        # Sweep parameters
        self.sweep_params_widget = QWidget()
        sweep_params_layout = QVBoxLayout()
        sweep_params_layout.setContentsMargins(0, 0, 0, 0)

        # Start value
        start_layout = QHBoxLayout()
        self.sweep_start_label = QLabel("Start (Hz):")
        self.sweep_start_label.setFont(self.font)
        self.sweep_start_label.setFixedWidth(100)
        self.sweep_start_entry = QDoubleSpinBox()
        self.sweep_start_entry.setFont(self.font)
        self.sweep_start_entry.setRange(0, 102000)
        self.sweep_start_entry.setDecimals(3)
        self.sweep_start_entry.setValue(1000)
        start_layout.addWidget(self.sweep_start_label)
        start_layout.addWidget(self.sweep_start_entry, 1)
        sweep_params_layout.addLayout(start_layout)

        # Stop value
        stop_layout = QHBoxLayout()
        self.sweep_stop_label = QLabel("Stop (Hz):")
        self.sweep_stop_label.setFont(self.font)
        self.sweep_stop_label.setFixedWidth(100)
        self.sweep_stop_entry = QDoubleSpinBox()
        self.sweep_stop_entry.setFont(self.font)
        self.sweep_stop_entry.setRange(0, 102000)
        self.sweep_stop_entry.setDecimals(3)
        self.sweep_stop_entry.setValue(10000)
        stop_layout.addWidget(self.sweep_stop_label)
        stop_layout.addWidget(self.sweep_stop_entry, 1)
        sweep_params_layout.addLayout(stop_layout)

        # Step value
        step_layout = QHBoxLayout()
        self.sweep_step_label = QLabel("Step (Hz):")
        self.sweep_step_label.setFont(self.font)
        self.sweep_step_label.setFixedWidth(100)
        self.sweep_step_entry = QDoubleSpinBox()
        self.sweep_step_entry.setFont(self.font)
        self.sweep_step_entry.setRange(0.001, 10000)
        self.sweep_step_entry.setDecimals(3)
        self.sweep_step_entry.setValue(100)
        step_layout.addWidget(self.sweep_step_label)
        step_layout.addWidget(self.sweep_step_entry, 1)
        sweep_params_layout.addLayout(step_layout)

        # Auto rate checkbox
        self.sweep_auto_rate_checkbox = QCheckBox("Auto Rate (2× Time Constant)")
        self.sweep_auto_rate_checkbox.setFont(self.font)
        self.sweep_auto_rate_checkbox.setChecked(True)
        sweep_params_layout.addWidget(self.sweep_auto_rate_checkbox)

        self.sweep_params_widget.setLayout(sweep_params_layout)
        self.sweep_params_widget.setVisible(False)
        monitor_layout.addWidget(self.sweep_params_widget)

        # Control buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_operation)
        self.start_btn.setEnabled(False)
        self.start_btn.setMinimumHeight(30)
        self.start_btn.setFont(self.font)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_operation)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(30)
        self.stop_btn.setFont(self.font)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        monitor_layout.addLayout(button_layout)

        # Status
        self.operation_status = QLabel("Status: Ready")
        self.operation_status.setWordWrap(True)
        self.operation_status.setFont(self.font)
        monitor_layout.addWidget(self.operation_status)

        monitor_group.setLayout(monitor_layout)
        parent_layout.addWidget(monitor_group)

    def setup_data_control_section(self, parent_layout):
        """Setup data control section"""
        data_group = QGroupBox("Data Control")
        data_layout = QVBoxLayout()

        self.clear_data_button = QPushButton("Clear Plot Data")
        self.clear_data_button.clicked.connect(self.clear_plot_data)
        self.clear_data_button.setFont(self.font)
        self.clear_data_button.setMinimumHeight(30)

        self.save_data_button = QPushButton("Save Data")
        self.save_data_button.clicked.connect(self.save_data)
        self.save_data_button.setFont(self.font)
        self.save_data_button.setMinimumHeight(30)

        data_layout.addWidget(self.clear_data_button)
        data_layout.addWidget(self.save_data_button)

        data_group.setLayout(data_layout)
        parent_layout.addWidget(data_group)

    def create_plot_panel(self):
        """Create the plot panel with PyQtGraph plots"""
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        plot_title = QLabel("Real-time Lock-in Monitoring")
        plot_title_font = QFont()
        plot_title_font.setPointSize(12)
        plot_title_font.setBold(True)
        plot_title.setFont(plot_title_font)
        plot_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(plot_title)

        # X/Y/R plot
        self.xyr_plot_widget = pg.PlotWidget()
        self.xyr_plot_widget.setBackground('w')
        self.xyr_plot_widget.setLabel('left', 'Voltage', units='V')
        self.xyr_plot_widget.setLabel('bottom', 'Time', units='s')
        self.xyr_plot_widget.setTitle('X, Y, and R')
        self.xyr_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.xyr_plot_widget.addLegend()

        self.x_curve = self.xyr_plot_widget.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), symbol='o', symbolSize=4,
            symbolBrush=(0, 0, 255), name='X')

        self.y_curve = self.xyr_plot_widget.plot(pen=pg.mkPen(color=(255, 0, 0), width=2), symbol='o', symbolSize=4,
            symbolBrush=(255, 0, 0), name='Y')

        self.r_curve = self.xyr_plot_widget.plot(pen=pg.mkPen(color=(0, 128, 0), width=2), symbol='o', symbolSize=4,
            symbolBrush=(0, 128, 0), name='R')

        # Theta (Phase) plot
        self.theta_plot_widget = pg.PlotWidget()
        self.theta_plot_widget.setBackground('w')
        self.theta_plot_widget.setLabel('left', 'Phase', units='deg')
        self.theta_plot_widget.setLabel('bottom', 'Time', units='s')
        self.theta_plot_widget.setTitle('θ (Phase)')
        self.theta_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.theta_plot_widget.addLegend()

        self.theta_curve = self.theta_plot_widget.plot(pen=pg.mkPen(color=(128, 0, 128), width=2), symbol='o',
            symbolSize=4, symbolBrush=(128, 0, 128), name='θ')

        right_layout.addWidget(self.xyr_plot_widget)
        right_layout.addWidget(self.theta_plot_widget)

        right_panel.setLayout(right_layout)
        return right_panel

    def on_mode_changed(self, mode):
        """Handle mode change"""
        if mode == "Real-time Monitor":
            self.sweep_params_widget.setVisible(False)
            self.is_sweep_mode = False
            self.xyr_plot_widget.setLabel('bottom', 'Time', units='s')
            self.theta_plot_widget.setLabel('bottom', 'Time', units='s')
        elif mode == "Frequency Sweep":
            self.sweep_params_widget.setVisible(True)
            self.is_sweep_mode = True
            self.sweep_start_label.setText("Start (Hz):")
            self.sweep_stop_label.setText("Stop (Hz):")
            self.sweep_step_label.setText("Step (Hz):")
            self.sweep_start_entry.setRange(0, 102000)
            self.sweep_stop_entry.setRange(0, 102000)
            self.sweep_step_entry.setRange(0.001, 10000)
            self.sweep_start_entry.setDecimals(3)
            self.sweep_start_entry.setValue(1000)
            self.sweep_stop_entry.setValue(10000)
            self.sweep_step_entry.setValue(100)
            self.xyr_plot_widget.setLabel('bottom', 'Frequency', units='Hz')
            self.theta_plot_widget.setLabel('bottom', 'Frequency', units='Hz')
        else:
            self.sweep_params_widget.setVisible(True)
            self.is_sweep_mode = True
            self.sweep_start_label.setText("Start (V):")
            self.sweep_stop_label.setText("Stop (V):")
            self.sweep_step_label.setText("Step (V):")
            self.sweep_start_entry.setRange(0, 5.0)
            self.sweep_stop_entry.setRange(0, 5.0)
            self.sweep_step_entry.setRange(0.000001, 1.0)
            self.sweep_start_entry.setDecimals(6)
            self.sweep_start_entry.setValue(0.004)
            self.sweep_stop_entry.setValue(5.0)
            self.sweep_step_entry.setValue(0.1)
            self.xyr_plot_widget.setLabel('bottom', 'Amplitude', units='Vrms')
            self.theta_plot_widget.setLabel('bottom', 'Amplitude', units='Vrms')

    def on_checkbox_changed(self):
        """Handle checkbox state change"""
        if self.is_plotting:
            self.update_plot_visibility()

    def update_plot_visibility(self):
        """Update plot visibility and auto-zoom"""
        x_data = self.sweep_param_data if self.is_sweep_mode else self.time_data

        if self.x_monitor_checkbox.isChecked():
            self.x_curve.setData(x_data, self.x_data)
        else:
            self.x_curve.setData([], [])

        if self.y_monitor_checkbox.isChecked():
            self.y_curve.setData(x_data, self.y_data)
        else:
            self.y_curve.setData([], [])

        if self.r_monitor_checkbox.isChecked():
            self.r_curve.setData(x_data, self.r_data)
        else:
            self.r_curve.setData([], [])

        self.xyr_plot_widget.autoRange()

        if self.theta_monitor_checkbox.isChecked():
            self.theta_curve.setData(x_data, self.theta_data)
        else:
            self.theta_curve.setData([], [])

        self.theta_plot_widget.autoRange()

    def on_instrument_connected(self, instrument, instrument_name):
        """Handle instrument connection"""
        self.SR830_instrument = instrument
        self.isConnect = True
        print(f"Connected to {instrument_name}")

        if self.SR830_instrument:
            self.update_readings_from_instrument()

            if self.SR830_instrument != 'Emulation':
                self.reading_thread = ContinuousReadingThread(self.SR830_instrument)
                self.reading_thread.reading_signal.connect(self.update_current_readings)
                self.reading_thread.error_signal.connect(self.on_reading_error)
                self.reading_thread.start()
            else:
                self.reading_timer = QTimer()
                self.reading_timer.timeout.connect(self.update_emulation_readings)
                self.reading_timer.start(1000)

        self.start_btn.setEnabled(True)

    def on_instrument_disconnected(self, instrument_name):
        """Handle instrument disconnection"""
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.stop_operation()

        if self.sweep_thread and self.sweep_thread.isRunning():
            self.stop_operation()

        if self.reading_thread and self.reading_thread.isRunning():
            self.reading_thread.stop()
            self.reading_thread.wait()
            self.reading_thread = None

        if hasattr(self, 'reading_timer'):
            self.reading_timer.stop()

        self.SR830_instrument = None
        self.isConnect = False
        print(f"Disconnected from {instrument_name}")

        self.start_btn.setEnabled(False)
        self.x_reading_label.setText("N/A V")
        self.y_reading_label.setText("N/A V")
        self.r_reading_label.setText("N/A V")
        self.theta_reading_label.setText("N/A deg")
        self.freq_reading_label.setText("N/A Hz")
        self.amp_reading_label.setText("N/A Vrms")
        self.sens_reading_label.setText("N/A")
        self.tc_reading_label.setText("N/A")

    def update_current_readings(self, X, Y, R, Theta):
        """Update current reading labels"""
        if not self.is_plotting:
            self.x_reading_label.setText(f"{X:.6f} V")
            self.y_reading_label.setText(f"{Y:.6f} V")
            self.r_reading_label.setText(f"{R:.6f} V")
            self.theta_reading_label.setText(f"{Theta:.2f} deg")

    def update_emulation_readings(self):
        """Update readings for emulation mode"""
        if not self.is_plotting:
            X = random.random()
            Y = random.random()
            R = np.sqrt(X ** 2 + Y ** 2)
            Theta = random.randint(0, 360)

            self.x_reading_label.setText(f"{X:.6f} V")
            self.y_reading_label.setText(f"{Y:.6f} V")
            self.r_reading_label.setText(f"{R:.6f} V")
            self.theta_reading_label.setText(f"{Theta} deg")

    def on_reading_error(self, error_msg):
        """Handle reading thread error"""
        print(f"Reading error: {error_msg}")

    def update_readings_from_instrument(self):
        """Manual update of readings from instrument"""
        if not self.isConnect or not self.SR830_instrument:
            return

        if self.SR830_instrument == 'Emulation':
            self.x_reading_label.setText(f"{random.random():.6f} V")
            self.y_reading_label.setText(f"{random.random():.6f} V")
            self.r_reading_label.setText(f"{random.random():.6f} V")
            self.theta_reading_label.setText(f"{random.randint(0, 360)} deg")
            self.freq_reading_label.setText("1000 Hz")
            self.amp_reading_label.setText("1.0 Vrms")
            self.sens_reading_label.setText("100 mV")
            self.tc_reading_label.setText("1 s")
            return

        try:
            # Read X, Y, R, Theta
            values = self.SR830_instrument.query("SNAP? 1,2,3,4")
            X, Y, R, Theta = values.split(',')
            self.x_reading_label.setText(f"{float(X):.6f} V")
            self.y_reading_label.setText(f"{float(Y):.6f} V")
            self.r_reading_label.setText(f"{float(R):.6f} V")
            self.theta_reading_label.setText(f"{float(Theta):.2f} deg")

            # Frequency
            freq = float(self.SR830_instrument.query('FREQ?'))
            self.freq_reading_label.setText(f"{freq:.2f} Hz")

            # Amplitude
            amp = float(self.SR830_instrument.query('SLVL?'))
            self.amp_reading_label.setText(f"{amp:.6f} Vrms")

            # Sensitivity
            sens_idx = int(self.SR830_instrument.query("SENS?"))
            sens_values = ["2 nV", "5 nV", "10 nV", "20 nV", "50 nV", "100 nV", "200 nV", "500 nV", "1 µV", "2 µV",
                           "5 µV", "10 µV", "20 µV", "50 µV", "100 µV", "200 µV", "500 µV", "1 mV", "2 mV", "5 mV",
                           "10 mV", "20 mV", "50 mV", "100 mV", "200 mV", "500 mV", "1 V"]
            sensitivity = sens_values[sens_idx] if sens_idx < len(sens_values) else "Unknown"
            self.sens_reading_label.setText(sensitivity)

            # Time constant
            tc_idx = int(self.SR830_instrument.query("OFLT?"))
            tc_values = ["10 µs", "30 µs", "100 µs", "300 µs", "1 ms", "3 ms", "10 ms", "30 ms", "100 ms", "300 ms",
                         "1 s", "3 s", "10 s", "30 s", "100 s", "300 s", "1 ks", "3 ks", "10 ks", "30 ks"]
            time_constant = tc_values[tc_idx] if tc_idx < len(tc_values) else "Unknown"
            self.tc_reading_label.setText(time_constant)

        except Exception as e:
            print(f"Error updating readings: {e}")

    def apply_reference(self):
        """Apply reference source setting"""
        if not self.isConnect:
            return

        if self.SR830_instrument == 'Emulation':
            return

        idx = self.ref_combo.currentIndex()
        try:
            self.SR830_instrument.write(f'FMOD {idx}')
            time.sleep(0.1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting reference:\n{str(e)}")

    def apply_frequency(self):
        """Apply frequency setting"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.SR830_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Configuration not applied in emulation mode")
            return

        freq = self.freq_entry.text()
        if not freq:
            QMessageBox.warning(self, "Warning", "Please enter frequency")
            return

        try:
            self.SR830_instrument.write(f'FREQ {freq}')
            time.sleep(0.1)
            QMessageBox.information(self, "Success", "Frequency set successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting frequency:\n{str(e)}")

    def apply_amplitude(self):
        """Apply sine output amplitude setting"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.SR830_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Configuration not applied in emulation mode")
            return

        amp = self.amp_entry.text()
        if not amp:
            QMessageBox.warning(self, "Warning", "Please enter amplitude")
            return

        try:
            self.SR830_instrument.write(f'SLVL {amp}')
            time.sleep(0.1)
            QMessageBox.information(self, "Success", "Amplitude set successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting amplitude:\n{str(e)}")

    def apply_sensitivity(self):
        """Apply sensitivity setting"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.SR830_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Configuration not applied in emulation mode")
            return

        idx = self.sens_combo.currentIndex()
        if idx == 0:
            return

        try:
            self.SR830_instrument.write(f'SENS {idx - 1}')
            time.sleep(0.1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting sensitivity:\n{str(e)}")

    def apply_time_constant(self):
        """Apply time constant setting"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.SR830_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Configuration not applied in emulation mode")
            return

        idx = self.tc_combo.currentIndex()
        if idx == 0:
            return

        try:
            self.SR830_instrument.write(f'OFLT {idx - 1}')
            time.sleep(0.1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting time constant:\n{str(e)}")

    def apply_slope(self):
        """Apply filter slope setting"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.SR830_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Configuration not applied in emulation mode")
            return

        idx = self.slope_combo.currentIndex()
        if idx == 0:
            return

        try:
            self.SR830_instrument.write(f'OFSL {idx - 1}')
            time.sleep(0.1)
            QMessageBox.information(self, "Success", "Filter slope set successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting slope:\n{str(e)}")

    def auto_gain(self):
        """Auto gain"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.SR830_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Auto functions not available in emulation mode")
            return

        try:
            self.SR830_instrument.write('AGAN')
            time.sleep(2)
            self.update_readings_from_instrument()
            QMessageBox.information(self, "Success", "Auto gain completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in auto gain:\n{str(e)}")

    def auto_reserve(self):
        """Auto reserve"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.SR830_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Auto functions not available in emulation mode")
            return

        try:
            self.SR830_instrument.write('ARSV')
            time.sleep(2)
            self.update_readings_from_instrument()
            QMessageBox.information(self, "Success", "Auto reserve completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in auto reserve:\n{str(e)}")

    def auto_phase(self):
        """Auto phase"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.SR830_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Auto functions not available in emulation mode")
            return

        try:
            self.SR830_instrument.write('APHS')
            time.sleep(2)
            self.update_readings_from_instrument()
            QMessageBox.information(self, "Success", "Auto phase completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in auto phase:\n{str(e)}")

    def start_operation(self):
        """Start monitoring or sweep based on mode"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if not (
                self.x_monitor_checkbox.isChecked() or self.y_monitor_checkbox.isChecked() or self.r_monitor_checkbox.isChecked() or self.theta_monitor_checkbox.isChecked()):
            QMessageBox.warning(self, "No Selection", "Please select at least one parameter to plot")
            return

        # Clear previous data
        self.time_data = []
        self.sweep_param_data = []
        self.x_data = []
        self.y_data = []
        self.r_data = []
        self.theta_data = []
        self.x_curve.setData([], [])
        self.y_curve.setData([], [])
        self.r_curve.setData([], [])
        self.theta_curve.setData([], [])

        self.is_plotting = True
        mode = self.mode_combo.currentText()

        if mode == "Real-time Monitor":
            self.is_sweep_mode = False
            if self.SR830_instrument == 'Emulation':
                self.monitor_thread = EmulationThread()
            else:
                self.monitor_thread = MonitorThread(self.SR830_instrument)

            self.monitor_thread.data_signal.connect(self.update_plots)
            self.monitor_thread.error_signal.connect(self.on_error)
            self.monitor_thread.finished.connect(self.on_finished)
            self.monitor_thread.start()

            self.operation_status.setText("Status: Monitoring active")

        else:
            self.is_sweep_mode = True
            sweep_type = 'frequency' if mode == "Frequency Sweep" else 'amplitude'
            start_val = self.sweep_start_entry.value()
            stop_val = self.sweep_stop_entry.value()
            step_val = self.sweep_step_entry.value()
            use_auto = self.sweep_auto_rate_checkbox.isChecked()

            if self.SR830_instrument == 'Emulation':
                self.sweep_thread = SweepThread('Emulation', sweep_type, start_val, stop_val, step_val, use_auto)
            else:
                self.sweep_thread = SweepThread(self.SR830_instrument, sweep_type, start_val, stop_val, step_val,
                                                use_auto)

            self.sweep_thread.progress_signal.connect(self.update_progress)
            self.sweep_thread.data_point_signal.connect(self.update_sweep_plots)
            self.sweep_thread.error_signal.connect(self.on_error)
            self.sweep_thread.info_signal.connect(self.on_info)
            self.sweep_thread.sweep_complete_signal.connect(self.on_complete)
            self.sweep_thread.finished.connect(self.on_finished)

            if self.reading_thread and self.reading_thread.isRunning():
                self.reading_thread.stop()
                self.reading_thread.wait()

            self.sweep_thread.start()

            self.operation_status.setText("Status: Sweep in progress")

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def stop_operation(self):
        """Stop monitoring or sweep"""
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()

        if self.sweep_thread and self.sweep_thread.isRunning():
            self.sweep_thread.stop()
            self.sweep_thread.wait()

        self.is_plotting = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.operation_status.setText("Status: Stopped")

        # Restart reading thread
        if self.SR830_instrument and self.SR830_instrument != 'Emulation':
            if not self.reading_thread or not self.reading_thread.isRunning():
                self.reading_thread = ContinuousReadingThread(self.SR830_instrument)
                self.reading_thread.reading_signal.connect(self.update_current_readings)
                self.reading_thread.error_signal.connect(self.on_reading_error)
                self.reading_thread.start()

    def update_plots(self, time_val, X, Y, R, Theta):
        """Update plots for real-time monitoring"""
        self.time_data.append(time_val)
        self.x_data.append(X)
        self.y_data.append(Y)
        self.r_data.append(R)
        self.theta_data.append(Theta)

        self.update_plot_visibility()

        self.x_reading_label.setText(f"{X:.6f} V")
        self.y_reading_label.setText(f"{Y:.6f} V")
        self.r_reading_label.setText(f"{R:.6f} V")
        self.theta_reading_label.setText(f"{Theta:.2f} deg")

    def update_sweep_plots(self, sweep_val, X, Y, R, Theta):
        """Update plots for sweep"""
        self.sweep_param_data.append(sweep_val)
        self.x_data.append(X)
        self.y_data.append(Y)
        self.r_data.append(R)
        self.theta_data.append(Theta)

        self.update_plot_visibility()

        self.x_reading_label.setText(f"{X:.6f} V")
        self.y_reading_label.setText(f"{Y:.6f} V")
        self.r_reading_label.setText(f"{R:.6f} V")
        self.theta_reading_label.setText(f"{Theta:.2f} deg")

    def update_progress(self, percentage, status):
        """Update progress for sweep"""
        self.operation_status.setText(f"{status} - {percentage}%")

    def on_info(self, title, message):
        """Show info message"""
        QMessageBox.information(self, title, message)

    def on_complete(self):
        """Handle operation completion"""
        self.operation_status.setText("Status: Complete")

    def on_error(self, error_msg):
        """Handle error"""
        print(f"Error: {error_msg}")
        QMessageBox.critical(self, "Error", error_msg)
        self.operation_status.setText(f"Status: Error")

    def on_finished(self):
        """Handle thread finished"""
        self.is_plotting = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def clear_plot_data(self):
        """Clear plot data"""
        self.time_data = []
        self.sweep_param_data = []
        self.x_data = []
        self.y_data = []
        self.r_data = []
        self.theta_data = []
        self.x_curve.setData([], [])
        self.y_curve.setData([], [])
        self.r_curve.setData([], [])
        self.theta_curve.setData([], [])

        QMessageBox.information(self, "Data Cleared", "Plot data has been cleared")

    def save_data(self):
        """Save all monitored/swept data to file"""
        if not self.x_data and not self.y_data:
            QMessageBox.warning(self, "No Data", "No data to save")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if self.is_sweep_mode:
                mode = self.mode_combo.currentText()
                sweep_type = "frequency" if "Frequency" in mode else "amplitude"
                filename = f"sr830_sweep_{sweep_type}_{timestamp}.csv"

                with open(filename, 'w') as f:
                    header_param = "Frequency (Hz)" if sweep_type == "frequency" else "Amplitude (Vrms)"
                    f.write(f"{header_param},X (V),Y (V),R (V),θ (deg)\n")
                    for i in range(len(self.sweep_param_data)):
                        f.write(
                            f"{self.sweep_param_data[i]},{self.x_data[i]},{self.y_data[i]},{self.r_data[i]},{self.theta_data[i]}\n")

                QMessageBox.information(self, "Data Saved",
                                        f"Sweep data saved to:\n{filename}\n\nTotal points: {len(self.sweep_param_data)}")
            else:
                filename = f"sr830_monitor_{timestamp}.csv"

                with open(filename, 'w') as f:
                    f.write("Time (s),X (V),Y (V),R (V),θ (deg)\n")
                    for i in range(len(self.time_data)):
                        f.write(
                            f"{self.time_data[i]},{self.x_data[i]},{self.y_data[i]},{self.r_data[i]},{self.theta_data[i]}\n")

                QMessageBox.information(self, "Data Saved",
                                        f"Monitoring data saved to:\n{filename}\n\nTotal points: {len(self.time_data)}")

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

        if self.reading_thread and self.reading_thread.isRunning():
            self.reading_thread.stop()
            self.reading_thread.wait()

        if hasattr(self, 'reading_timer'):
            self.reading_timer.stop()

        if self.SR830_instrument and self.SR830_instrument != 'Emulation':
            try:
                self.SR830_instrument.close()
            except:
                pass

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SR830()
    window.show()
    sys.exit(app.exec())