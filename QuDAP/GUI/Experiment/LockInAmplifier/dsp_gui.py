from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
                             QPushButton, QComboBox, QCheckBox, QLineEdit, QMessageBox, QScrollArea, QSizePolicy,
                             QRadioButton, QButtonGroup, QDoubleSpinBox, QSpinBox)
from PyQt6.QtGui import QIcon, QFont
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

# Time Constant Mappings
TIME_CONSTANT_VALUES = {0: 10e-6, 1: 20e-6, 2: 40e-6, 3: 80e-6, 4: 160e-6, 5: 320e-6, 6: 640e-6, 7: 5e-3, 8: 10e-3,
    9: 20e-3, 10: 50e-3, 11: 100e-3, 12: 200e-3, 13: 500e-3, 14: 1.0, 15: 2.0, 16: 5.0, 17: 10.0, 18: 20.0, 19: 50.0,
    20: 100.0, 21: 200.0, 22: 500.0, 23: 1000.0, 24: 2000.0, 25: 5000.0, 26: 10000.0, 27: 20000.0, 28: 30000.0,
    29: 50000.0}


class MonitorThread(QThread):
    """Thread to monitor lock-in parameters in real-time"""

    data_signal = pyqtSignal(float, float, float, float, float, float)  # (time, X, Y, Mag, Phase, Noise)
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
                    X = float(self.instrument.query("X."))
                    Y = float(self.instrument.query("Y."))
                    Mag = float(self.instrument.query("MAG."))
                    Phase = float(self.instrument.query("PHA."))
                    Noise = float(self.instrument.query("NHZ."))

                    elapsed_time = time.time() - self.start_time
                    self.data_signal.emit(elapsed_time, X, Y, Mag, Phase, Noise)
                    time.sleep(0.01)

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

    data_signal = pyqtSignal(float, float, float, float, float, float)  # (time, X, Y, Mag, Phase, Noise)
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
                    Mag = np.sqrt(X ** 2 + Y ** 2)
                    Phase = random.randint(0, 360)
                    Noise = random.randint(0, 100) / 1e6

                    elapsed_time = time.time() - self.start_time
                    self.data_signal.emit(elapsed_time, X, Y, Mag, Phase, Noise)
                    time.sleep(0.01)

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

    reading_signal = pyqtSignal(float, float, float, float, float)  # (X, Y, Mag, Phase, Noise)
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
                    X = float(self.instrument.query("X."))
                    Y = float(self.instrument.query("Y."))
                    Mag = float(self.instrument.query("MAG."))
                    Phase = float(self.instrument.query("PHA."))
                    Noise = float(self.instrument.query("NHZ."))

                    self.reading_signal.emit(X, Y, Mag, Phase, Noise)
                    time.sleep(1)  # Update every second

                except Exception as e:
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
    data_point_signal = pyqtSignal(float, float, float, float, float, float)  # (sweep_value, X, Y, Mag, Phase, Noise)
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
            tc_index = int(self.instrument.query('TC').strip())
            tc_value = TIME_CONSTANT_VALUES.get(tc_index, 0.1)
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
                self.error_signal.emit("DSP 7265 is not connected")
                return

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

                if self.sweep_type == 'frequency':
                    self.instrument.write(f'OF. {point}')
                    status = f"Frequency: {point:.2f} Hz ({i + 1}/{total_points})"
                else:
                    amp_uv = point * 1e6
                    self.instrument.write(f'OA. {amp_uv}')
                    status = f"Amplitude: {point:.6f} V ({i + 1}/{total_points})"

                time.sleep(rate_ms / 1000.0)

                x = float(self.instrument.query('X.').strip())
                y = float(self.instrument.query('Y.').strip())
                mag = float(self.instrument.query('MAG.').strip())
                phase = float(self.instrument.query('PHA.').strip())
                noise = float(self.instrument.query('NHZ.').strip())

                self.data_point_signal.emit(point, x, y, mag, phase, noise)
                progress = int((i + 1) / total_points * 100)
                self.progress_signal.emit(progress, status)

            self.sweep_complete_signal.emit()
            self.info_signal.emit("Sweep Complete",
                f"{sweep_type_name} sweep finished successfully\nCollected {total_points} data points")

        except Exception as e:
            import traceback
            self.error_signal.emit(f"Sweep error:\n{str(e)}\n\n{traceback.format_exc()}")

    def stop(self):
        """Stop the sweep"""
        self.should_stop = True


class DSP7265(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DSP 7265 Lock-in Amplifier")
        self.setGeometry(100, 100, 1600, 900)

        self.DSP7265_instrument = None
        self.monitor_thread = None
        self.sweep_thread = None
        self.reading_thread = None
        self.isConnect = False
        self.is_plotting = False

        # Data storage - unified for both monitoring and sweep
        self.time_data = []
        self.sweep_param_data = []  # Stores frequency or amplitude for sweep
        self.x_data = []
        self.y_data = []
        self.mag_data = []
        self.phase_data = []
        self.noise_data = []

        self.is_sweep_mode = False  # Track if currently in sweep mode

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
        title = QLabel("DSP 7265 Lock-in Amplifier")
        title.setFont(self.titlefont)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_layout.addWidget(title)

        # Connection section
        self.setup_connection_section(self.left_layout)

        # Current Readings section
        self.setup_readings_section(self.left_layout)

        # Configuration section
        self.setup_configuration_section(self.left_layout)

        # Auto Functions section
        self.setup_auto_functions_section(self.left_layout)

        # Real-time monitoring/sweep section (merged)
        self.setup_monitor_section(self.left_layout)

        # Data control section
        self.setup_data_control_section(self.left_layout)

        # Add stretch at the end
        self.left_layout.addStretch()

        left_content.setLayout(self.left_layout)
        self.scroll_area.setWidget(left_content)

        # Right panel - Plots (no scroll)
        right_panel = self.create_plot_panel()

        # Add panels to main layout
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(right_panel, 1)

        central_widget.setLayout(main_layout)

    def setup_connection_section(self, parent_layout):
        """Setup device connection section using standalone class"""
        self.connection_widget = InstrumentConnection(instrument_list=["DSP 7265 Lock-in"], allow_emulation=True,
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
        self.x_reading_label.setWordWrap(True)
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
        self.y_reading_label.setWordWrap(True)
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.y_reading_label, 1)
        readings_layout.addLayout(y_layout)

        # Magnitude Reading
        mag_layout = QHBoxLayout()
        mag_label = QLabel("Magnitude:")
        mag_label.setFont(self.font)
        mag_label.setFixedWidth(100)
        self.mag_reading_label = QLabel("N/A V")
        self.mag_reading_label.setFont(self.font)
        self.mag_reading_label.setWordWrap(True)
        mag_layout.addWidget(mag_label)
        mag_layout.addWidget(self.mag_reading_label, 1)
        readings_layout.addLayout(mag_layout)

        # Phase Reading
        phase_layout = QHBoxLayout()
        phase_label = QLabel("Phase:")
        phase_label.setFont(self.font)
        phase_label.setFixedWidth(100)
        self.phase_reading_label = QLabel("N/A deg")
        self.phase_reading_label.setFont(self.font)
        self.phase_reading_label.setWordWrap(True)
        phase_layout.addWidget(phase_label)
        phase_layout.addWidget(self.phase_reading_label, 1)
        readings_layout.addLayout(phase_layout)

        # Noise Reading
        noise_layout = QHBoxLayout()
        noise_label = QLabel("Noise:")
        noise_label.setFont(self.font)
        noise_label.setFixedWidth(100)
        self.noise_reading_label = QLabel("N/A V/√Hz")
        self.noise_reading_label.setFont(self.font)
        self.noise_reading_label.setWordWrap(True)
        noise_layout.addWidget(noise_label)
        noise_layout.addWidget(self.noise_reading_label, 1)
        readings_layout.addLayout(noise_layout)

        # Amplitude Reading
        amp_layout = QHBoxLayout()
        amp_label = QLabel("Amplitude:")
        amp_label.setFont(self.font)
        amp_label.setFixedWidth(100)
        self.amp_reading_label = QLabel("N/A Vrms")
        self.amp_reading_label.setFont(self.font)
        self.amp_reading_label.setWordWrap(True)
        amp_layout.addWidget(amp_label)
        amp_layout.addWidget(self.amp_reading_label, 1)
        readings_layout.addLayout(amp_layout)

        # Sensitivity Reading
        sens_layout = QHBoxLayout()
        sens_label = QLabel("Sensitivity:")
        sens_label.setFont(self.font)
        sens_label.setFixedWidth(100)
        self.sens_reading_label = QLabel("N/A")
        self.sens_reading_label.setFont(self.font)
        self.sens_reading_label.setWordWrap(True)
        sens_layout.addWidget(sens_label)
        sens_layout.addWidget(self.sens_reading_label, 1)
        readings_layout.addLayout(sens_layout)

        # Time Constant Reading
        tc_layout = QHBoxLayout()
        tc_label = QLabel("Time Constant:")
        tc_label.setFont(self.font)
        tc_label.setFixedWidth(100)
        self.tc_reading_label = QLabel("N/A")
        self.tc_reading_label.setFont(self.font)
        self.tc_reading_label.setWordWrap(True)
        tc_layout.addWidget(tc_label)
        tc_layout.addWidget(self.tc_reading_label, 1)
        readings_layout.addLayout(tc_layout)

        # Slope Reading
        slope_layout = QHBoxLayout()
        slope_label = QLabel("Slope:")
        slope_label.setFont(self.font)
        slope_label.setFixedWidth(100)
        self.slope_reading_label = QLabel("N/A")
        self.slope_reading_label.setFont(self.font)
        self.slope_reading_label.setWordWrap(True)
        slope_layout.addWidget(slope_label)
        slope_layout.addWidget(self.slope_reading_label, 1)
        readings_layout.addLayout(slope_layout)

        # Reference Reading
        ref_layout = QHBoxLayout()
        ref_label = QLabel("Reference:")
        ref_label.setFont(self.font)
        ref_label.setFixedWidth(100)
        self.ref_reading_label = QLabel("N/A")
        self.ref_reading_label.setFont(self.font)
        self.ref_reading_label.setWordWrap(True)
        ref_layout.addWidget(ref_label)
        ref_layout.addWidget(self.ref_reading_label, 1)
        readings_layout.addLayout(ref_layout)

        # Update readings button (manual update)
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
        config_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        config_layout = QVBoxLayout()

        # Reference (standalone - changes immediately)
        ref_layout = QHBoxLayout()
        ref_label = QLabel("Reference:")
        ref_label.setFont(self.font)
        ref_label.setFixedWidth(100)
        self.ref_combo = QComboBox()
        self.ref_combo.setFont(self.font)
        self.ref_combo.addItems(["INT", "EXT REAR", "EXT FRONT"])
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

        # Oscillator Amplitude
        osc_layout = QHBoxLayout()
        osc_label = QLabel("Osc. Amplitude:")
        osc_label.setFont(self.font)
        osc_label.setFixedWidth(100)
        self.osc_entry = QLineEdit()
        self.osc_entry.setFont(self.font)
        self.osc_entry.setPlaceholderText("Vrms")
        osc_vrms_label = QLabel("Vrms")
        osc_vrms_label.setFont(self.font)
        osc_layout.addWidget(osc_label)
        osc_layout.addWidget(self.osc_entry, 1)
        osc_layout.addWidget(osc_vrms_label)
        config_layout.addLayout(osc_layout)

        osc_set_btn = QPushButton("Set Amplitude")
        osc_set_btn.clicked.connect(self.apply_oscillator_amplitude)
        osc_set_btn.setFont(self.font)
        osc_set_btn.setMinimumHeight(30)
        config_layout.addWidget(osc_set_btn)

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
        tc_label.setToolTip("Select the time constant that is 5 to 10 times larger than 1/f")
        self.tc_combo = QComboBox()
        self.tc_combo.setFont(self.font)
        self.tc_combo.addItems(
            ["Select", "10 µs", "20 µs", "40 µs", "80 µs", "160 µs", "320 µs", "640 µs", "5 ms", "10 ms", "20 ms",
                "50 ms", "100 ms", "200 ms", "500 ms", "1 s", "2 s", "5 s", "10 s", "20 s", "50 s", "100 s", "200 s",
                "500 s", "1 ks", "2 ks", "5 ks", "10 ks", "20 ks", "50 ks", "100 ks"])
        self.tc_combo.currentIndexChanged.connect(self.apply_time_constant)
        tc_layout.addWidget(tc_label)
        tc_layout.addWidget(self.tc_combo, 1)
        config_layout.addLayout(tc_layout)

        # Slope
        slope_layout = QHBoxLayout()
        slope_label = QLabel("Slope:")
        slope_label.setFont(self.font)
        slope_label.setFixedWidth(100)
        self.slope_combo = QComboBox()
        self.slope_combo.setFont(self.font)
        self.slope_combo.addItems(["Select", "6 dB/octave", "12 dB/octave", "18 dB/octave", "24 dB/octave"])
        self.slope_combo.currentIndexChanged.connect(self.apply_slope)
        slope_layout.addWidget(slope_label)
        slope_layout.addWidget(self.slope_combo, 1)
        config_layout.addLayout(slope_layout)

        # Clear and Reset buttons
        clr_rst_layout = QHBoxLayout()
        self.clr_btn = QPushButton("Clear")
        self.clr_btn.clicked.connect(self.clear_instrument)
        self.clr_btn.setFont(self.font)
        self.clr_btn.setMinimumHeight(30)

        self.rst_btn = QPushButton("Reset")
        self.rst_btn.clicked.connect(self.reset_instrument)
        self.rst_btn.setFont(self.font)
        self.rst_btn.setMinimumHeight(30)

        clr_rst_layout.addWidget(self.clr_btn)
        clr_rst_layout.addWidget(self.rst_btn)
        config_layout.addLayout(clr_rst_layout)

        config_group.setLayout(config_layout)
        parent_layout.addWidget(config_group)

    def setup_auto_functions_section(self, parent_layout):
        """Setup auto functions section"""
        auto_group = QGroupBox("Auto Functions")
        auto_layout = QHBoxLayout()

        auto_sens_btn = QPushButton("Auto Sens.")
        auto_sens_btn.clicked.connect(self.auto_sensitivity)
        auto_sens_btn.setFont(self.font)
        auto_sens_btn.setMinimumHeight(30)

        auto_phase_btn = QPushButton("Auto Phase")
        auto_phase_btn.clicked.connect(self.auto_phase)
        auto_phase_btn.setFont(self.font)
        auto_phase_btn.setMinimumHeight(30)

        auto_meas_btn = QPushButton("Auto Meas.")
        auto_meas_btn.clicked.connect(self.auto_measurement)
        auto_meas_btn.setFont(self.font)
        auto_meas_btn.setMinimumHeight(30)

        auto_layout.addWidget(auto_sens_btn)
        auto_layout.addWidget(auto_phase_btn)
        auto_layout.addWidget(auto_meas_btn)

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

        # Parameter selection (what to plot)
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

        self.mag_monitor_checkbox = QCheckBox("Magnitude")
        self.mag_monitor_checkbox.setFont(self.font)
        self.mag_monitor_checkbox.setChecked(True)
        self.mag_monitor_checkbox.stateChanged.connect(self.on_checkbox_changed)
        monitor_layout.addWidget(self.mag_monitor_checkbox)

        self.phase_monitor_checkbox = QCheckBox("Phase")
        self.phase_monitor_checkbox.setFont(self.font)
        self.phase_monitor_checkbox.setChecked(True)
        self.phase_monitor_checkbox.stateChanged.connect(self.on_checkbox_changed)
        monitor_layout.addWidget(self.phase_monitor_checkbox)

        self.noise_monitor_checkbox = QCheckBox("Noise")
        self.noise_monitor_checkbox.setFont(self.font)
        self.noise_monitor_checkbox.setChecked(True)
        self.noise_monitor_checkbox.stateChanged.connect(self.on_checkbox_changed)
        monitor_layout.addWidget(self.noise_monitor_checkbox)

        # Sweep parameters (hidden by default)
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
        self.sweep_start_entry.setRange(0, 250000)
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
        self.sweep_stop_entry.setRange(0, 250000)
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
        """Create the plot panel with three PyQtGraph plots"""
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        plot_title = QLabel("Real-time Lock-in Monitoring")
        plot_title_font = QFont()
        plot_title_font.setPointSize(12)
        plot_title_font.setBold(True)
        plot_title.setFont(plot_title_font)
        plot_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(plot_title)

        # Create X/Y/Magnitude plot
        self.xy_plot_widget = pg.PlotWidget()
        self.xy_plot_widget.setBackground('w')
        self.xy_plot_widget.setLabel('left', 'Voltage', units='V')
        self.xy_plot_widget.setLabel('bottom', 'Time', units='s')
        self.xy_plot_widget.setTitle('X, Y, and Magnitude')
        self.xy_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.xy_plot_widget.addLegend()

        self.x_curve = self.xy_plot_widget.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), symbol='o', symbolSize=4,
            symbolBrush=(0, 0, 255), name='X')

        self.y_curve = self.xy_plot_widget.plot(pen=pg.mkPen(color=(255, 0, 0), width=2), symbol='o', symbolSize=4,
            symbolBrush=(255, 0, 0), name='Y')

        self.mag_curve = self.xy_plot_widget.plot(pen=pg.mkPen(color=(0, 128, 0), width=2), symbol='o', symbolSize=4,
            symbolBrush=(0, 128, 0), name='Magnitude')

        # Create Phase plot
        self.phase_plot_widget = pg.PlotWidget()
        self.phase_plot_widget.setBackground('w')
        self.phase_plot_widget.setLabel('left', 'Phase', units='deg')
        self.phase_plot_widget.setLabel('bottom', 'Time', units='s')
        self.phase_plot_widget.setTitle('Phase')
        self.phase_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.phase_plot_widget.addLegend()

        self.phase_curve = self.phase_plot_widget.plot(pen=pg.mkPen(color=(128, 0, 128), width=2), symbol='o',
            symbolSize=4, symbolBrush=(128, 0, 128), name='Phase')

        # Create Noise plot
        self.noise_plot_widget = pg.PlotWidget()
        self.noise_plot_widget.setBackground('w')
        self.noise_plot_widget.setLabel('left', 'Noise', units='V/√Hz')
        self.noise_plot_widget.setLabel('bottom', 'Time', units='s')
        self.noise_plot_widget.setTitle('Noise')
        self.noise_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.noise_plot_widget.addLegend()

        self.noise_curve = self.noise_plot_widget.plot(pen=pg.mkPen(color=(255, 128, 0), width=2), symbol='o',
            symbolSize=4, symbolBrush=(255, 128, 0), name='Noise')

        right_layout.addWidget(self.xy_plot_widget)
        right_layout.addWidget(self.phase_plot_widget)
        right_layout.addWidget(self.noise_plot_widget)

        right_panel.setLayout(right_layout)
        return right_panel

    def on_mode_changed(self, mode):
        """Handle mode change"""
        if mode == "Real-time Monitor":
            self.sweep_params_widget.setVisible(False)
            self.is_sweep_mode = False
            # Reset x-axis labels to time
            self.xy_plot_widget.setLabel('bottom', 'Time', units='s')
            self.phase_plot_widget.setLabel('bottom', 'Time', units='s')
            self.noise_plot_widget.setLabel('bottom', 'Time', units='s')
        elif mode == "Frequency Sweep":
            self.sweep_params_widget.setVisible(True)
            self.is_sweep_mode = True
            self.sweep_start_label.setText("Start (Hz):")
            self.sweep_stop_label.setText("Stop (Hz):")
            self.sweep_step_label.setText("Step (Hz):")
            self.sweep_start_entry.setRange(0, 250000)
            self.sweep_stop_entry.setRange(0, 250000)
            self.sweep_step_entry.setRange(0.001, 10000)
            self.sweep_start_entry.setDecimals(3)
            self.sweep_start_entry.setValue(1000)
            self.sweep_stop_entry.setValue(10000)
            self.sweep_step_entry.setValue(100)
            # Set x-axis labels to frequency
            self.xy_plot_widget.setLabel('bottom', 'Frequency', units='Hz')
            self.phase_plot_widget.setLabel('bottom', 'Frequency', units='Hz')
            self.noise_plot_widget.setLabel('bottom', 'Frequency', units='Hz')
        else:  # Amplitude Sweep
            self.sweep_params_widget.setVisible(True)
            self.is_sweep_mode = True
            self.sweep_start_label.setText("Start (V):")
            self.sweep_stop_label.setText("Stop (V):")
            self.sweep_step_label.setText("Step (V):")
            self.sweep_start_entry.setRange(0, 5.0)
            self.sweep_stop_entry.setRange(0, 5.0)
            self.sweep_step_entry.setRange(0.000001, 1.0)
            self.sweep_start_entry.setDecimals(6)
            self.sweep_start_entry.setValue(0.1)
            self.sweep_stop_entry.setValue(1.0)
            self.sweep_step_entry.setValue(0.1)
            # Set x-axis labels to amplitude
            self.xy_plot_widget.setLabel('bottom', 'Amplitude', units='V')
            self.phase_plot_widget.setLabel('bottom', 'Amplitude', units='V')
            self.noise_plot_widget.setLabel('bottom', 'Amplitude', units='V')

    def on_checkbox_changed(self):
        """Handle checkbox state change - update plots and auto-zoom"""
        if self.is_plotting:
            self.update_plot_visibility()

    def update_plot_visibility(self):
        """Update plot visibility and auto-zoom based on checkbox states"""
        # Get x-axis data (time or sweep parameter)
        if self.is_sweep_mode:
            x_data = self.sweep_param_data
        else:
            x_data = self.time_data

        # Update X/Y/Magnitude plot
        if self.x_monitor_checkbox.isChecked():
            self.x_curve.setData(x_data, self.x_data)
        else:
            self.x_curve.setData([], [])

        if self.y_monitor_checkbox.isChecked():
            self.y_curve.setData(x_data, self.y_data)
        else:
            self.y_curve.setData([], [])

        if self.mag_monitor_checkbox.isChecked():
            self.mag_curve.setData(x_data, self.mag_data)
        else:
            self.mag_curve.setData([], [])

        # Auto-zoom for X/Y/Magnitude plot
        self.xy_plot_widget.autoRange()

        # Update Phase plot
        if self.phase_monitor_checkbox.isChecked():
            self.phase_curve.setData(x_data, self.phase_data)
        else:
            self.phase_curve.setData([], [])

        # Auto-zoom for Phase plot
        self.phase_plot_widget.autoRange()

        # Update Noise plot
        if self.noise_monitor_checkbox.isChecked():
            self.noise_curve.setData(x_data, self.noise_data)
        else:
            self.noise_curve.setData([], [])

        # Auto-zoom for Noise plot
        self.noise_plot_widget.autoRange()

    def on_instrument_connected(self, instrument, instrument_name):
        """Handle instrument connection"""
        self.DSP7265_instrument = instrument
        self.isConnect = True
        print(f"Connected to {instrument_name}")

        if self.DSP7265_instrument:
            self.update_readings_from_instrument()

            # Start continuous reading thread
            if self.DSP7265_instrument != 'Emulation':
                self.reading_thread = ContinuousReadingThread(self.DSP7265_instrument)
                self.reading_thread.reading_signal.connect(self.update_current_readings)
                self.reading_thread.error_signal.connect(self.on_reading_error)
                self.reading_thread.start()
            else:
                # For emulation, use a timer
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

        if hasattr(self, 'reading_timer'):
            self.reading_timer.stop()

        self.DSP7265_instrument = None
        self.isConnect = False
        print(f"Disconnected from {instrument_name}")

        self.start_btn.setEnabled(False)
        self.x_reading_label.setText("N/A V")
        self.y_reading_label.setText("N/A V")
        self.mag_reading_label.setText("N/A V")
        self.phase_reading_label.setText("N/A deg")
        self.noise_reading_label.setText("N/A V/√Hz")
        self.amp_reading_label.setText("N/A Vrms")
        self.sens_reading_label.setText("N/A")
        self.tc_reading_label.setText("N/A")
        self.slope_reading_label.setText("N/A")
        self.ref_reading_label.setText("N/A")

    def update_current_readings(self, X, Y, Mag, Phase, Noise):
        """Update current reading labels (called by continuous reading thread)"""
        if not self.is_plotting:  # Only update if not plotting
            self.x_reading_label.setText(f"{X:.6f} V")
            self.y_reading_label.setText(f"{Y:.6f} V")
            self.mag_reading_label.setText(f"{Mag:.6f} V")
            self.phase_reading_label.setText(f"{Phase:.2f} deg")
            self.noise_reading_label.setText(f"{Noise:.9f} V/√Hz")

    def update_emulation_readings(self):
        """Update readings for emulation mode"""
        if not self.is_plotting:
            X = random.random()
            Y = random.random()
            Mag = np.sqrt(X ** 2 + Y ** 2)
            Phase = random.randint(0, 360)
            Noise = random.random() * 1e-6

            self.x_reading_label.setText(f"{X:.6f} V")
            self.y_reading_label.setText(f"{Y:.6f} V")
            self.mag_reading_label.setText(f"{Mag:.6f} V")
            self.phase_reading_label.setText(f"{Phase} deg")
            self.noise_reading_label.setText(f"{Noise:.9f} V/√Hz")

    def on_reading_error(self, error_msg):
        """Handle reading thread error"""
        print(f"Reading error: {error_msg}")

    def update_readings_from_instrument(self):
        """Manual update of readings from instrument"""
        if not self.isConnect or not self.DSP7265_instrument:
            return

        if self.DSP7265_instrument == 'Emulation':
            self.x_reading_label.setText(f"{random.random():.6f} V")
            self.y_reading_label.setText(f"{random.random():.6f} V")
            self.mag_reading_label.setText(f"{random.random():.6f} V")
            self.phase_reading_label.setText(f"{random.randint(0, 360)} deg")
            self.noise_reading_label.setText(f"{random.random() * 1e-6:.9f} V/√Hz")
            self.amp_reading_label.setText("1.0 Vrms")
            self.sens_reading_label.setText("100 mV")
            self.tc_reading_label.setText("1 s")
            self.slope_reading_label.setText("6 dB/octave")
            self.ref_reading_label.setText("Internal")
            return

        try:
            X = float(self.DSP7265_instrument.query("X."))
            self.x_reading_label.setText(f"{X:.6f} V")

            Y = float(self.DSP7265_instrument.query("Y."))
            self.y_reading_label.setText(f"{Y:.6f} V")

            Mag = float(self.DSP7265_instrument.query("MAG."))
            self.mag_reading_label.setText(f"{Mag:.6f} V")

            Phase = float(self.DSP7265_instrument.query("PHA."))
            self.phase_reading_label.setText(f"{Phase:.2f} deg")

            Noise = float(self.DSP7265_instrument.query("NHZ."))
            self.noise_reading_label.setText(f"{Noise:.9f} V/√Hz")

            amplitude = float(self.DSP7265_instrument.query('OA[.]')) / 1e6
            self.amp_reading_label.setText(f"{amplitude:.6f} Vrms")

            # Sensitivity
            sen_idx = int(self.DSP7265_instrument.query("SEN"))
            mode = int(self.DSP7265_instrument.query("IMODE"))

            if mode > 0:
                sen_values = ["2fA", "5fA", "10fA", "20fA", "50fA", "100fA", "200fA", "500fA", "1pA", "2pA", "5pA",
                              "10pA", "20pA", "50pA", "100pA", "200pA", "500pA", "1nA", "2nA", "5nA", "10nA", "20nA",
                              "50nA", "100nA", "200nA", "500nA", "1µA"]
            else:
                sen_values = ["", "2 nV", "5 nV", "10 nV", "20 nV", "50 nV", "100 nV", "200 nV", "500 nV", "1 µV",
                              "2 µV", "5 µV", "10 µV", "20 µV", "50 µV", "100 µV", "200 µV", "500 µV", "1 mV", "2 mV",
                              "5 mV", "10 mV", "20 mV", "50 mV", "100 mV", "200 mV", "500 mV", "1 V"]

            sensitivity = sen_values[sen_idx] if sen_idx < len(sen_values) else "Unknown"
            self.sens_reading_label.setText(sensitivity)

            # Time constant
            tc_idx = int(self.DSP7265_instrument.query("TC"))
            tc_values = ["10 µs", "20 µs", "40 µs", "80 µs", "160 µs", "320 µs", "640 µs", "5 ms", "10 ms", "20 ms",
                         "50 ms", "100 ms", "200 ms", "500 ms", "1 s", "2 s", "5 s", "10 s", "20 s", "50 s", "100 s",
                         "200 s", "500 s", "1 ks", "2 ks", "5 ks", "10 ks", "20 ks", "50 ks", "100 ks"]
            time_constant = tc_values[tc_idx] if tc_idx < len(tc_values) else "Unknown"
            self.tc_reading_label.setText(time_constant)

            # Slope
            slope_idx = int(self.DSP7265_instrument.query("SLOPE"))
            slope_values = ['6 dB/octave', '12 dB/octave', '18 dB/octave', '24 dB/octave']
            slope = slope_values[slope_idx] if slope_idx < len(slope_values) else "Unknown"
            self.slope_reading_label.setText(slope)

            # Reference source
            ref = int(self.DSP7265_instrument.query("IE"))
            ref_sources = {0: "Internal", 1: "External TTL", 2: "External Analog"}
            ref_source = ref_sources.get(ref, "Unknown")
            self.ref_reading_label.setText(ref_source)

        except Exception as e:
            print(f"Error updating readings: {e}")

    def apply_reference(self):
        """Apply reference setting (changes immediately)"""
        if not self.isConnect:
            return

        if self.DSP7265_instrument == 'Emulation':
            return

        idx = self.ref_combo.currentIndex()
        try:
            self.DSP7265_instrument.write(f'IE {idx}')
            time.sleep(0.1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting reference:\n{str(e)}")

    def apply_frequency(self):
        """Apply frequency setting"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.DSP7265_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Configuration is not applied in emulation mode")
            return

        freq = self.freq_entry.text()
        if not freq:
            QMessageBox.warning(self, "Warning", "Please enter frequency")
            return

        try:
            self.DSP7265_instrument.write(f'OF. {freq}')
            time.sleep(0.1)
            QMessageBox.information(self, "Success", "Frequency set successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting frequency:\n{str(e)}")

    def apply_oscillator_amplitude(self):
        """Apply oscillator amplitude setting"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.DSP7265_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Configuration is not applied in emulation mode")
            return

        amp = self.osc_entry.text()
        if not amp:
            QMessageBox.warning(self, "Warning", "Please enter amplitude")
            return

        try:
            self.DSP7265_instrument.write(f'OA. {amp}')
            time.sleep(1)
            QMessageBox.information(self, "Success", "Oscillator amplitude set successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting amplitude:\n{str(e)}")

    def apply_sensitivity(self):
        """Apply sensitivity setting"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.DSP7265_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Configuration is not applied in emulation mode")
            return

        idx = self.sens_combo.currentIndex()
        if idx == 0:
            return

        try:
            self.DSP7265_instrument.write(f'SEN {idx}')
            time.sleep(0.1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting sensitivity:\n{str(e)}")

    def apply_time_constant(self):
        """Apply time constant setting"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.DSP7265_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Configuration is not applied in emulation mode")
            return

        idx = self.tc_combo.currentIndex()
        if idx == 0:
            return

        try:
            self.DSP7265_instrument.write(f'TC {idx - 1}')
            time.sleep(0.1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting time constant:\n{str(e)}")

    def apply_slope(self):
        """Apply slope setting"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.DSP7265_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Configuration is not applied in emulation mode")
            return

        idx = self.slope_combo.currentIndex()
        if idx == 0:
            return

        try:
            self.DSP7265_instrument.write(f'SLOPE {idx - 1}')
            time.sleep(0.1)
            QMessageBox.information(self, "Success", "Slope set successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting slope:\n{str(e)}")

    def clear_instrument(self):
        """Clear instrument status"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.DSP7265_instrument == 'Emulation':
            return

        try:
            self.DSP7265_instrument.write('*CLS')
            QMessageBox.information(self, "Success", "Instrument status cleared")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error clearing instrument:\n{str(e)}")

    def reset_instrument(self):
        """Reset instrument to default settings"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.DSP7265_instrument == 'Emulation':
            return

        reply = QMessageBox.question(self, "Confirm Reset",
                                     "Are you sure you want to reset the instrument to default settings?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.DSP7265_instrument.write('*RST')
                time.sleep(1)
                QMessageBox.information(self, "Success", "Instrument reset successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error resetting instrument:\n{str(e)}")

    def auto_sensitivity(self):
        """Auto sensitivity"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.DSP7265_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Auto functions not available in emulation mode")
            return

        try:
            self.DSP7265_instrument.write('AS')
            time.sleep(1)
            QMessageBox.information(self, "Success", "Auto sensitivity completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in auto sensitivity:\n{str(e)}")

    def auto_phase(self):
        """Auto phase"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.DSP7265_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Auto functions not available in emulation mode")
            return

        try:
            self.DSP7265_instrument.write('AQN')
            time.sleep(1)
            QMessageBox.information(self, "Success", "Auto phase completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in auto phase:\n{str(e)}")

    def auto_measurement(self):
        """Auto measurement"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.DSP7265_instrument == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Auto functions not available in emulation mode")
            return

        try:
            self.DSP7265_instrument.write('ASM')
            time.sleep(2)
            QMessageBox.information(self, "Success", "Auto measurement completed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in auto measurement:\n{str(e)}")

    def start_operation(self):
        """Start monitoring or sweep based on mode"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if not (
                self.x_monitor_checkbox.isChecked() or self.y_monitor_checkbox.isChecked() or self.mag_monitor_checkbox.isChecked() or self.phase_monitor_checkbox.isChecked() or self.noise_monitor_checkbox.isChecked()):
            QMessageBox.warning(self, "No Selection", "Please select at least one parameter to plot")
            return

        # Clear previous data
        self.time_data = []
        self.sweep_param_data = []
        self.x_data = []
        self.y_data = []
        self.mag_data = []
        self.phase_data = []
        self.noise_data = []
        self.x_curve.setData([], [])
        self.y_curve.setData([], [])
        self.mag_curve.setData([], [])
        self.phase_curve.setData([], [])
        self.noise_curve.setData([], [])

        self.is_plotting = True
        mode = self.mode_combo.currentText()

        if mode == "Real-time Monitor":
            self.is_sweep_mode = False
            # Start monitoring thread
            if self.DSP7265_instrument == 'Emulation':
                self.monitor_thread = EmulationThread()
            else:
                self.monitor_thread = MonitorThread(self.DSP7265_instrument)

            self.monitor_thread.data_signal.connect(self.update_plots)
            self.monitor_thread.error_signal.connect(self.on_error)
            self.monitor_thread.finished.connect(self.on_finished)
            self.monitor_thread.start()

            self.operation_status.setText("Status: Monitoring active")

        else:
            # Start sweep
            self.is_sweep_mode = True
            sweep_type = 'frequency' if mode == "Frequency Sweep" else 'amplitude'
            start_val = self.sweep_start_entry.value()
            stop_val = self.sweep_stop_entry.value()
            step_val = self.sweep_step_entry.value()
            use_auto = self.sweep_auto_rate_checkbox.isChecked()

            if self.DSP7265_instrument == 'Emulation':
                self.sweep_thread = SweepThread('Emulation', sweep_type, start_val, stop_val, step_val, use_auto)
            else:
                self.sweep_thread = SweepThread(self.DSP7265_instrument, sweep_type, start_val, stop_val, step_val,
                                                use_auto)

            self.sweep_thread.progress_signal.connect(self.update_progress)
            self.sweep_thread.data_point_signal.connect(self.update_sweep_plots)
            self.sweep_thread.error_signal.connect(self.on_error)
            self.sweep_thread.info_signal.connect(self.on_info)
            self.sweep_thread.sweep_complete_signal.connect(self.on_complete)
            self.sweep_thread.finished.connect(self.on_finished)
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

    def update_plots(self, time_val, X, Y, Mag, Phase, Noise):
        """Update plots for real-time monitoring"""
        self.time_data.append(time_val)
        self.x_data.append(X)
        self.y_data.append(Y)
        self.mag_data.append(Mag)
        self.phase_data.append(Phase)
        self.noise_data.append(Noise)

        # Update plots based on checkbox state
        self.update_plot_visibility()

        # Update reading labels with current plot values
        self.x_reading_label.setText(f"{X:.6f} V")
        self.y_reading_label.setText(f"{Y:.6f} V")
        self.mag_reading_label.setText(f"{Mag:.6f} V")
        self.phase_reading_label.setText(f"{Phase:.2f} deg")
        self.noise_reading_label.setText(f"{Noise:.9f} V/√Hz")

    def update_sweep_plots(self, sweep_val, X, Y, Mag, Phase, Noise):
        """Update plots for sweep"""
        self.sweep_param_data.append(sweep_val)
        self.x_data.append(X)
        self.y_data.append(Y)
        self.mag_data.append(Mag)
        self.phase_data.append(Phase)
        self.noise_data.append(Noise)

        # Update plots based on checkbox state
        self.update_plot_visibility()

        # Update reading labels with current plot values
        self.x_reading_label.setText(f"{X:.6f} V")
        self.y_reading_label.setText(f"{Y:.6f} V")
        self.mag_reading_label.setText(f"{Mag:.6f} V")
        self.phase_reading_label.setText(f"{Phase:.2f} deg")
        self.noise_reading_label.setText(f"{Noise:.9f} V/√Hz")

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
        self.mag_data = []
        self.phase_data = []
        self.noise_data = []
        self.x_curve.setData([], [])
        self.y_curve.setData([], [])
        self.mag_curve.setData([], [])
        self.phase_curve.setData([], [])
        self.noise_curve.setData([], [])

        QMessageBox.information(self, "Data Cleared", "Plot data has been cleared")

    def save_data(self):
        """Save all monitored/swept data to file"""
        if not self.x_data and not self.y_data:
            QMessageBox.warning(self, "No Data", "No data to save")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if self.is_sweep_mode:
                # Save sweep data
                mode = self.mode_combo.currentText()
                sweep_type = "frequency" if "Frequency" in mode else "amplitude"
                filename = f"dsp7265_sweep_{sweep_type}_{timestamp}.csv"

                with open(filename, 'w') as f:
                    header_param = "Frequency (Hz)" if sweep_type == "frequency" else "Amplitude (V)"
                    f.write(f"{header_param},X (V),Y (V),Magnitude (V),Phase (deg),Noise (V/√Hz)\n")
                    for i in range(len(self.sweep_param_data)):
                        f.write(
                            f"{self.sweep_param_data[i]},{self.x_data[i]},{self.y_data[i]},{self.mag_data[i]},{self.phase_data[i]},{self.noise_data[i]}\n")

                QMessageBox.information(self, "Data Saved",
                                        f"Sweep data saved to:\n{filename}\n\nTotal points: {len(self.sweep_param_data)}")
            else:
                # Save monitoring data
                filename = f"dsp7265_monitor_{timestamp}.csv"

                with open(filename, 'w') as f:
                    f.write("Time (s),X (V),Y (V),Magnitude (V),Phase (deg),Noise (V/√Hz)\n")
                    for i in range(len(self.time_data)):
                        f.write(
                            f"{self.time_data[i]},{self.x_data[i]},{self.y_data[i]},{self.mag_data[i]},{self.phase_data[i]},{self.noise_data[i]}\n")

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

        if self.DSP7265_instrument and self.DSP7265_instrument != 'Emulation':
            try:
                self.DSP7265_instrument.close()
            except:
                pass

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DSP7265()
    window.show()
    sys.exit(app.exec())