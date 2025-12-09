from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
                             QPushButton, QComboBox, QCheckBox, QLineEdit, QMessageBox, QScrollArea, QSizePolicy,
                             QDoubleSpinBox, QRadioButton, QButtonGroup)
from PyQt6.QtGui import QFont, QDoubleValidator
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import sys
import pyvisa as visa
import time
import numpy as np
import pyqtgraph as pg

# Import the standalone connection class
try:
    from instrument.instrument_connection import InstrumentConnection
except ImportError:
    from QuDAP.instrument.instrument_connection import InstrumentConnection


class ReadingThread(QThread):
    """Thread for continuous reading updates when connected"""

    reading_signal = pyqtSignal(float, str)  # (current, state)
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
                    # Query current and output state
                    current = float(self.instrument.query("SOUR:CURR?"))
                    output_state = self.instrument.query("OUTP?").strip()
                    state = "ON" if output_state == "1" else "OFF"

                    self.reading_signal.emit(current, state)
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


class MonitorThread(QThread):
    """Thread for monitoring current output for plotting"""

    data_signal = pyqtSignal(float, float)  # (time, current)
    error_signal = pyqtSignal(str)

    def __init__(self, instrument, is_emulation=False, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.is_emulation = is_emulation
        self.should_stop = False
        self.start_time = time.time()

    def run(self):
        """Monitor current output"""
        try:
            while not self.should_stop:
                try:
                    elapsed_time = time.time() - self.start_time

                    if self.is_emulation:
                        # Generate simulated current data
                        current = np.random.randn() * 1e-6
                    else:
                        # Read actual current
                        current = float(self.instrument.query("SOUR:CURR?"))

                    self.data_signal.emit(elapsed_time, current)
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


class EmulationThread(QThread):
    """Thread for emulation mode monitoring"""

    data_signal = pyqtSignal(float, float)  # (time, current)

    def __init__(self, waveform_type, amplitude, frequency, offset, parent=None):
        super().__init__(parent)
        self.waveform_type = waveform_type
        self.amplitude = amplitude
        self.frequency = frequency
        self.offset = offset
        self.should_stop = False
        self.start_time = time.time()

    def run(self):
        """Generate emulated waveform data"""
        while not self.should_stop:
            elapsed_time = time.time() - self.start_time
            t = elapsed_time

            # Generate waveform based on type
            if self.waveform_type == 'SIN':
                current = self.amplitude * np.sin(2 * np.pi * self.frequency * t) + self.offset
            elif self.waveform_type == 'SQU':
                current = self.amplitude * np.sign(np.sin(2 * np.pi * self.frequency * t)) + self.offset
            elif self.waveform_type == 'RAMP':
                phase = (self.frequency * t) % 1.0
                current = self.amplitude * (2 * phase - 1) + self.offset
            else:  # ARB0
                current = self.amplitude * np.sin(2 * np.pi * self.frequency * t) + self.offset

            self.data_signal.emit(elapsed_time, current)
            time.sleep(0.01)  # 10ms for smooth waveform

    def stop(self):
        """Stop emulation"""
        self.should_stop = True


class Keithley6221(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keithley 6221 DC and AC Current Source")
        self.setGeometry(100, 100, 1400, 900)

        self.keithley_6221 = None
        self.reading_thread = None
        self.monitor_thread = None
        self.emulation_thread = None
        self.isConnect = False
        self.DCisOn = False
        self.ACisOn = False

        # Data storage
        self.time_data = []
        self.current_data = []
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
        self.scroll_area.setFixedWidth(700)

        left_content = QWidget()
        left_content.setMaximumWidth(680)

        self.left_layout = QVBoxLayout()
        self.left_layout.setContentsMargins(10, 10, 10, 10)
        self.left_layout.setSpacing(10)

        # Title
        title = QLabel("Keithley 6221 DC and AC Current Source")
        title.setFont(self.titlefont)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_layout.addWidget(title)

        # Setup sections
        self.setup_connection_section(self.left_layout)
        self.setup_readings_section(self.left_layout)
        self.setup_mode_selection(self.left_layout)
        self.setup_dc_section(self.left_layout)
        self.setup_ac_section(self.left_layout)
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
        self.connection_widget = InstrumentConnection(instrument_list=["Keithley 6221"], allow_emulation=True,
            title="Instrument Connection")
        self.connection_widget.instrument_connected.connect(self.on_instrument_connected)
        self.connection_widget.instrument_disconnected.connect(self.on_instrument_disconnected)
        parent_layout.addWidget(self.connection_widget)

    def setup_readings_section(self, parent_layout):
        """Setup current readings section"""
        readings_group = QGroupBox("Current Readings")
        readings_layout = QVBoxLayout()

        # Current Reading
        current_layout = QHBoxLayout()
        current_label = QLabel("Current:")
        current_label.setFont(self.font)
        current_label.setFixedWidth(100)
        self.current_reading_label = QLabel("N/A")
        self.current_reading_label.setFont(self.font)
        current_layout.addWidget(current_label)
        current_layout.addWidget(self.current_reading_label, 1)
        readings_layout.addLayout(current_layout)

        # State Reading
        state_layout = QHBoxLayout()
        state_label = QLabel("State:")
        state_label.setFont(self.font)
        state_label.setFixedWidth(100)
        self.state_reading_label = QLabel("N/A")
        self.state_reading_label.setFont(self.font)
        state_layout.addWidget(state_label)
        state_layout.addWidget(self.state_reading_label, 1)
        readings_layout.addLayout(state_layout)

        readings_group.setLayout(readings_layout)
        parent_layout.addWidget(readings_group)

    def setup_mode_selection(self, parent_layout):
        """Setup DC/AC mode selection"""
        mode_group = QGroupBox("Source Mode")
        mode_layout = QHBoxLayout()

        self.dc_radio = QRadioButton("DC Current")
        self.dc_radio.setFont(self.font)
        self.dc_radio.setChecked(True)
        self.dc_radio.toggled.connect(self.on_mode_changed)

        self.ac_radio = QRadioButton("AC Current (Waveform)")
        self.ac_radio.setFont(self.font)
        self.ac_radio.toggled.connect(self.on_mode_changed)

        self.mode_button_group = QButtonGroup()
        self.mode_button_group.addButton(self.dc_radio)
        self.mode_button_group.addButton(self.ac_radio)

        mode_layout.addWidget(self.dc_radio)
        mode_layout.addWidget(self.ac_radio)
        mode_group.setLayout(mode_layout)
        parent_layout.addWidget(mode_group)

    def setup_dc_section(self, parent_layout):
        """Setup DC current section"""
        self.dc_group = QGroupBox("DC Current Configuration")
        dc_layout = QVBoxLayout()

        # DC Current value
        dc_value_layout = QHBoxLayout()
        dc_label = QLabel("DC Current:")
        dc_label.setFont(self.font)
        dc_label.setFixedWidth(100)
        self.dc_current_entry = QLineEdit()
        self.dc_current_entry.setFont(self.font)
        self.dc_current_entry.setPlaceholderText("±0.1pA to ±105mA")
        self.dc_validator = QDoubleValidator(-105, 105, 10)
        self.dc_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.dc_current_entry.setValidator(self.dc_validator)
        self.dc_current_entry.setFixedHeight(30)

        self.dc_unit_combo = QComboBox()
        self.dc_unit_combo.setFont(self.font)
        self.dc_unit_combo.addItems(["Select Units", "mA", "µA", "nA", "pA"])
        self.dc_unit_combo.setFixedWidth(120)

        dc_value_layout.addWidget(dc_label)
        dc_value_layout.addWidget(self.dc_current_entry, 1)
        dc_value_layout.addWidget(self.dc_unit_combo)
        dc_layout.addLayout(dc_value_layout)

        # Auto Range checkbox
        self.dc_auto_range_checkbox = QCheckBox("Auto Range")
        self.dc_auto_range_checkbox.setFont(self.font)
        self.dc_auto_range_checkbox.setChecked(True)
        dc_layout.addWidget(self.dc_auto_range_checkbox)

        # Send button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.dc_send_btn = QPushButton("Send DC Current")
        self.dc_send_btn.clicked.connect(self.send_dc_current)
        self.dc_send_btn.setFont(self.font)
        self.dc_send_btn.setMinimumHeight(35)
        self.dc_send_btn.setMinimumWidth(150)
        self.dc_send_btn.setEnabled(False)
        button_layout.addWidget(self.dc_send_btn)
        button_layout.addStretch()
        dc_layout.addLayout(button_layout)

        self.dc_group.setLayout(dc_layout)
        parent_layout.addWidget(self.dc_group)

    def setup_ac_section(self, parent_layout):
        """Setup AC waveform section"""
        self.ac_group = QGroupBox("AC Waveform Configuration")
        ac_layout = QVBoxLayout()

        # Waveform selection
        waveform_layout = QHBoxLayout()
        waveform_label = QLabel("Waveform:")
        waveform_label.setFont(self.font)
        waveform_label.setFixedWidth(100)
        self.waveform_combo = QComboBox()
        self.waveform_combo.setFont(self.font)
        self.waveform_combo.addItems(["Select Function", "SINE", "SQUARE", "RAMP", "ARB(x)"])
        waveform_layout.addWidget(waveform_label)
        waveform_layout.addWidget(self.waveform_combo, 1)
        ac_layout.addLayout(waveform_layout)

        # Amplitude
        amp_layout = QHBoxLayout()
        amp_label = QLabel("Amplitude:")
        amp_label.setFont(self.font)
        amp_label.setFixedWidth(100)
        self.amp_entry = QLineEdit()
        self.amp_entry.setFont(self.font)
        self.amp_entry.setPlaceholderText("2pA to 105mA")
        self.amp_validator = QDoubleValidator(0, 105, 10)
        self.amp_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.amp_entry.setValidator(self.amp_validator)
        self.amp_entry.setFixedHeight(30)

        self.amp_unit_combo = QComboBox()
        self.amp_unit_combo.setFont(self.font)
        self.amp_unit_combo.addItems(["Select Units", "mA", "µA", "nA", "pA"])
        self.amp_unit_combo.setFixedWidth(120)

        amp_layout.addWidget(amp_label)
        amp_layout.addWidget(self.amp_entry, 1)
        amp_layout.addWidget(self.amp_unit_combo)
        ac_layout.addLayout(amp_layout)

        # Frequency
        freq_layout = QHBoxLayout()
        freq_label = QLabel("Frequency:")
        freq_label.setFont(self.font)
        freq_label.setFixedWidth(100)
        self.freq_entry = QLineEdit()
        self.freq_entry.setFont(self.font)
        self.freq_entry.setPlaceholderText("0Hz to 100KHz")
        self.freq_validator = QDoubleValidator(0.00, 100000, 5)
        self.freq_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.freq_entry.setValidator(self.freq_validator)
        self.freq_entry.setFixedHeight(30)

        freq_hz_label = QLabel("Hz")
        freq_hz_label.setFont(self.font)

        freq_layout.addWidget(freq_label)
        freq_layout.addWidget(self.freq_entry, 1)
        freq_layout.addWidget(freq_hz_label)
        ac_layout.addLayout(freq_layout)

        # Offset
        offset_layout = QHBoxLayout()
        offset_label = QLabel("Offset:")
        offset_label.setFont(self.font)
        offset_label.setFixedWidth(100)
        self.offset_entry = QLineEdit()
        self.offset_entry.setFont(self.font)
        self.offset_entry.setPlaceholderText("0 to ±105mA")
        self.offset_entry.setText("0")
        self.offset_validator = QDoubleValidator(-105, 105, 10)
        self.offset_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.offset_entry.setValidator(self.offset_validator)
        self.offset_entry.setFixedHeight(30)

        self.offset_unit_combo = QComboBox()
        self.offset_unit_combo.setFont(self.font)
        self.offset_unit_combo.addItems(["Select Units", "mA", "µA", "nA", "pA"])
        self.offset_unit_combo.setFixedWidth(120)

        offset_layout.addWidget(offset_label)
        offset_layout.addWidget(self.offset_entry, 1)
        offset_layout.addWidget(self.offset_unit_combo)
        ac_layout.addLayout(offset_layout)

        # Phase Marker
        phase_layout = QHBoxLayout()
        phase_label = QLabel("Phase Marker:")
        phase_label.setFont(self.font)
        phase_label.setFixedWidth(100)

        self.phase_marker_on = QRadioButton("ON")
        self.phase_marker_on.setFont(self.font)
        self.phase_marker_off = QRadioButton("OFF")
        self.phase_marker_off.setFont(self.font)
        self.phase_marker_off.setChecked(True)

        self.phase_marker_group = QButtonGroup()
        self.phase_marker_group.addButton(self.phase_marker_on)
        self.phase_marker_group.addButton(self.phase_marker_off)

        phase_layout.addWidget(phase_label)
        phase_layout.addWidget(self.phase_marker_on)
        phase_layout.addWidget(self.phase_marker_off)
        phase_layout.addStretch()
        ac_layout.addLayout(phase_layout)

        # Phase Marker Trigger Line
        trigger_layout = QHBoxLayout()
        trigger_label = QLabel("PM Trigger Line:")
        trigger_label.setFont(self.font)
        trigger_label.setFixedWidth(100)
        self.trigger_line_combo = QComboBox()
        self.trigger_line_combo.setFont(self.font)
        self.trigger_line_combo.addItems([" ", "1", "2", "3", "4", "5", "6"])
        trigger_layout.addWidget(trigger_label)
        trigger_layout.addWidget(self.trigger_line_combo, 1)
        ac_layout.addLayout(trigger_layout)

        # Best Range checkbox
        self.ac_best_range_checkbox = QCheckBox("Best Range")
        self.ac_best_range_checkbox.setFont(self.font)
        self.ac_best_range_checkbox.setChecked(True)
        ac_layout.addWidget(self.ac_best_range_checkbox)

        # Arm button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.ac_arm_btn = QPushButton("Arm Waveform")
        self.ac_arm_btn.clicked.connect(self.arm_waveform)
        self.ac_arm_btn.setFont(self.font)
        self.ac_arm_btn.setMinimumHeight(35)
        self.ac_arm_btn.setMinimumWidth(150)
        self.ac_arm_btn.setEnabled(False)
        button_layout.addWidget(self.ac_arm_btn)
        button_layout.addStretch()
        ac_layout.addLayout(button_layout)

        self.ac_group.setLayout(ac_layout)
        self.ac_group.setVisible(False)
        parent_layout.addWidget(self.ac_group)

    def setup_monitor_section(self, parent_layout):
        """Setup monitoring and data control section"""
        monitor_group = QGroupBox("Real-time Monitoring")
        monitor_layout = QVBoxLayout()

        # Status label
        self.monitor_status_label = QLabel("Status: Not monitoring")
        self.monitor_status_label.setFont(self.font)
        monitor_layout.addWidget(self.monitor_status_label)

        # Button layout
        button_layout = QHBoxLayout()

        self.clear_data_btn = QPushButton("Clear Plot Data")
        self.clear_data_btn.setFont(self.font)
        self.clear_data_btn.clicked.connect(self.clear_plot_data)

        self.save_data_btn = QPushButton("Save Data")
        self.save_data_btn.setFont(self.font)
        self.save_data_btn.clicked.connect(self.save_data)
        self.save_data_btn.setEnabled(False)

        button_layout.addWidget(self.clear_data_btn)
        button_layout.addWidget(self.save_data_btn)

        monitor_layout.addLayout(button_layout)
        monitor_group.setLayout(monitor_layout)
        parent_layout.addWidget(monitor_group)

    def setup_plot_panel(self, parent_layout):
        """Setup right panel with plot"""
        plot_widget = QWidget()
        plot_layout = QVBoxLayout()
        plot_layout.setContentsMargins(10, 10, 10, 10)

        # Plot title
        plot_title = QLabel("Current Output vs Time")
        plot_title.setFont(self.titlefont)
        plot_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plot_layout.addWidget(plot_title)

        # Create PyQtGraph plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Current (A)')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()

        # Create plot curve
        self.current_curve = self.plot_widget.plot(pen=pg.mkPen(color='b', width=2), name='Current')

        plot_layout.addWidget(self.plot_widget)
        plot_widget.setLayout(plot_layout)
        parent_layout.addWidget(plot_widget)

    def on_mode_changed(self):
        """Handle mode selection change"""
        if self.dc_radio.isChecked():
            self.dc_group.setVisible(True)
            self.ac_group.setVisible(False)
        else:
            self.dc_group.setVisible(False)
            self.ac_group.setVisible(True)

    def on_instrument_connected(self, instrument, instrument_name):
        """Handle instrument connection"""
        self.keithley_6221 = instrument
        self.isConnect = True
        print(f"Connected to {instrument_name}")

        if self.keithley_6221 and self.keithley_6221 != 'Emulation':
            # Turn off output initially
            self.keithley_6221.write("OUTP OFF")

            # Start reading thread
            self.reading_thread = ReadingThread(self.keithley_6221)
            self.reading_thread.reading_signal.connect(self.update_readings)
            self.reading_thread.error_signal.connect(self.on_reading_error)
            self.reading_thread.start()

        self.dc_send_btn.setEnabled(True)
        self.ac_arm_btn.setEnabled(True)

    def on_instrument_disconnected(self, instrument_name):
        """Handle instrument disconnection"""
        # Stop monitoring
        self.stop_monitoring()

        if self.reading_thread and self.reading_thread.isRunning():
            self.reading_thread.stop()
            self.reading_thread.wait()
            self.reading_thread = None

        # Turn off outputs if connected
        if self.keithley_6221 and self.keithley_6221 != 'Emulation':
            try:
                self.keithley_6221.write("OUTP OFF")
                self.keithley_6221.write("SOUR:WAVE:ABOR")
            except:
                pass

        self.keithley_6221 = None
        self.isConnect = False
        self.DCisOn = False
        self.ACisOn = False
        print(f"Disconnected from {instrument_name}")

        self.dc_send_btn.setEnabled(False)
        self.ac_arm_btn.setEnabled(False)
        self.current_reading_label.setText("N/A")
        self.state_reading_label.setText("N/A")

        # Reset button states
        self.dc_send_btn.setText("Send DC Current")
        self.dc_send_btn.setStyleSheet("")
        self.ac_arm_btn.setText("Arm Waveform")
        self.ac_arm_btn.setStyleSheet("")

    def update_readings(self, current, state):
        """Update reading labels"""
        self.current_reading_label.setText(f"{current:.9e} A")
        self.state_reading_label.setText(state)

    def on_reading_error(self, error_msg):
        """Handle reading thread error"""
        print(f"Reading error: {error_msg}")

    def update_plot_data(self, time_val, current):
        """Update plot with new data point"""
        self.time_data.append(time_val)
        self.current_data.append(current)

        # Limit data points
        if len(self.time_data) > self.max_points:
            self.time_data = self.time_data[-self.max_points:]
            self.current_data = self.current_data[-self.max_points:]

        # Update plot
        self.current_curve.setData(self.time_data, self.current_data)

    def clear_plot_data(self):
        """Clear all plot data"""
        self.time_data = []
        self.current_data = []
        self.current_curve.setData([], [])
        self.save_data_btn.setEnabled(False)
        print("Plot data cleared")

    def save_data(self):
        """Save data to CSV file"""
        if not self.time_data:
            QMessageBox.warning(self, "No Data", "No data to save")
            return

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"keithley6221_data_{timestamp}.csv"

        try:
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Time (s)', 'Current (A)'])
                for t, i in zip(self.time_data, self.current_data):
                    writer.writerow([t, i])

            QMessageBox.information(self, "Success", f"Data saved to {filename}")
            print(f"Data saved to {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving data:\n{str(e)}")

    def start_monitoring(self):
        """Start monitoring current output"""
        if self.monitor_thread and self.monitor_thread.isRunning():
            return

        is_emulation = (self.keithley_6221 == 'Emulation')

        if is_emulation:
            # Use emulation thread
            self.stop_monitoring()
        else:
            # Use monitor thread for real instrument
            self.monitor_thread = MonitorThread(self.keithley_6221, is_emulation)
            self.monitor_thread.data_signal.connect(self.update_plot_data)
            self.monitor_thread.error_signal.connect(self.on_reading_error)
            self.monitor_thread.start()

        self.save_data_btn.setEnabled(True)
        print("Monitoring started")

    def start_ac_monitoring(self, waveform_type, amplitude, frequency, offset):
        """Start AC waveform monitoring with emulation"""
        self.stop_monitoring()

        if self.keithley_6221 == 'Emulation':
            # Start emulation thread for waveform
            self.emulation_thread = EmulationThread(waveform_type, amplitude, frequency, offset)
            self.emulation_thread.data_signal.connect(self.update_plot_data)
            self.emulation_thread.start()
        else:
            # Start monitor thread for real instrument
            self.monitor_thread = MonitorThread(self.keithley_6221, False)
            self.monitor_thread.data_signal.connect(self.update_plot_data)
            self.monitor_thread.error_signal.connect(self.on_reading_error)
            self.monitor_thread.start()

        self.monitor_status_label.setText("Status: Monitoring AC waveform")
        self.save_data_btn.setEnabled(True)

    def stop_monitoring(self):
        """Stop all monitoring threads"""
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()
            self.monitor_thread = None

        if self.emulation_thread and self.emulation_thread.isRunning():
            self.emulation_thread.stop()
            self.emulation_thread.wait()
            self.emulation_thread = None

        self.monitor_status_label.setText("Status: Not monitoring")
        print("Monitoring stopped")

    def send_dc_current(self):
        """Send or turn off DC current"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if not self.DCisOn:
            # Validate inputs
            dc_current = self.dc_current_entry.text()
            if not dc_current:
                QMessageBox.warning(self, "Missing Input", "Please enter DC current value")
                return

            unit_idx = self.dc_unit_combo.currentIndex()
            if unit_idx == 0:
                QMessageBox.warning(self, "Missing Input", "Please select current unit")
                return

            # Convert to scientific notation
            unit_map = {1: 'e-3', 2: 'e-6', 3: 'e-9', 4: 'e-12'}
            unit_suffix = unit_map[unit_idx]
            unit_multiplier = {1: 1e-3, 2: 1e-6, 3: 1e-9, 4: 1e-12}
            current_value = float(dc_current) * unit_multiplier[unit_idx]

            if self.keithley_6221 == 'Emulation':
                QMessageBox.information(self, "Emulation Mode",
                                        f"DC Current set to: {dc_current} {self.dc_unit_combo.currentText()}")
                self.DCisOn = True
                self.dc_send_btn.setText("Turn OFF")
                self.dc_send_btn.setStyleSheet("""
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
                self.ac_arm_btn.setEnabled(False)

                # Start monitoring
                self.clear_plot_data()
                self.start_monitoring()
                self.monitor_status_label.setText("Status: Monitoring DC current")
                return

            try:
                # Clear any errors
                self.keithley_6221.write('*CLS')

                # Configure auto range
                if self.dc_auto_range_checkbox.isChecked():
                    self.keithley_6221.write('CURR:RANG:AUTO ON')
                else:
                    self.keithley_6221.write('CURR:RANG:AUTO OFF')

                # Set current and turn on
                self.keithley_6221.write(f"CURR {dc_current}{unit_suffix}")
                time.sleep(0.1)
                self.keithley_6221.write("OUTP ON")

                self.DCisOn = True
                self.dc_send_btn.setText("Turn OFF")
                self.dc_send_btn.setStyleSheet("""
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
                self.ac_arm_btn.setEnabled(False)

                # Start monitoring
                self.clear_plot_data()
                self.start_monitoring()
                self.monitor_status_label.setText("Status: Monitoring DC current")

                QMessageBox.information(self, "Success", "DC current output enabled")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error setting DC current:\n{str(e)}")

        else:
            # Turn off DC current
            self.stop_monitoring()

            if self.keithley_6221 != 'Emulation':
                try:
                    self.keithley_6221.write("OUTP OFF")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error turning off output:\n{str(e)}")

            self.DCisOn = False
            self.dc_send_btn.setText("Send DC Current")
            self.dc_send_btn.setStyleSheet("")
            self.ac_arm_btn.setEnabled(True)
            self.monitor_status_label.setText("Status: Not monitoring")

    def arm_waveform(self):
        """Arm or abort AC waveform"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if not self.ACisOn:
            # Validate inputs
            waveform_idx = self.waveform_combo.currentIndex()
            if waveform_idx == 0:
                QMessageBox.warning(self, "Missing Input", "Please select waveform function")
                return

            amp = self.amp_entry.text()
            freq = self.freq_entry.text()
            offset = self.offset_entry.text()

            if not amp:
                QMessageBox.warning(self, "Missing Input", "Please enter amplitude")
                return
            if not freq:
                QMessageBox.warning(self, "Missing Input", "Please enter frequency")
                return
            if not offset:
                offset = "0"
                self.offset_entry.setText("0")
                self.offset_unit_combo.setCurrentIndex(1)

            amp_unit_idx = self.amp_unit_combo.currentIndex()
            offset_unit_idx = self.offset_unit_combo.currentIndex()

            if amp_unit_idx == 0:
                QMessageBox.warning(self, "Missing Input", "Please select amplitude unit")
                return
            if offset_unit_idx == 0:
                QMessageBox.warning(self, "Missing Input", "Please select offset unit")
                return

            # Convert units
            unit_map = {1: 'e-3', 2: 'e-6', 3: 'e-9', 4: 'e-12'}
            unit_multiplier = {1: 1e-3, 2: 1e-6, 3: 1e-9, 4: 1e-12}
            amp_suffix = unit_map[amp_unit_idx]
            offset_suffix = unit_map[offset_unit_idx]

            amp_value = float(amp) * unit_multiplier[amp_unit_idx]
            freq_value = float(freq)
            offset_value = float(offset) * unit_multiplier[offset_unit_idx]

            # Map waveform
            waveform_map = {1: 'SIN', 2: 'SQU', 3: 'RAMP', 4: 'ARB0'}
            waveform = waveform_map[waveform_idx]

            if self.keithley_6221 == 'Emulation':
                QMessageBox.information(self, "Emulation Mode", f"Waveform armed:\n"
                                                                f"Function: {self.waveform_combo.currentText()}\n"
                                                                f"Amplitude: {amp} {self.amp_unit_combo.currentText()}\n"
                                                                f"Frequency: {freq} Hz\n"
                                                                f"Offset: {offset} {self.offset_unit_combo.currentText()}")
                self.ACisOn = True
                self.ac_arm_btn.setText("Abort Waveform")
                self.ac_arm_btn.setStyleSheet("""
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
                self.dc_send_btn.setEnabled(False)

                # Start AC monitoring with emulation
                self.clear_plot_data()
                self.start_ac_monitoring(waveform, amp_value, freq_value, offset_value)
                return

            try:
                # Clear any previous waveform
                self.keithley_6221.write("SOUR:WAVE:ABOR")
                time.sleep(0.1)
                self.keithley_6221.write("*CLS")

                # Configure auto range
                self.keithley_6221.write("CURR:RANG:AUTO ON")

                # Set waveform parameters
                self.keithley_6221.write(f"SOUR:WAVE:FUNC {waveform}")
                self.keithley_6221.write(f"SOUR:WAVE:AMPL {amp}{amp_suffix}")
                self.keithley_6221.write(f"SOUR:WAVE:FREQ {freq}")
                self.keithley_6221.write(f"SOUR:WAVE:OFFS {offset}{offset_suffix}")

                # Phase marker
                if self.phase_marker_on.isChecked():
                    self.keithley_6221.write("SOUR:WAVE:PMAR:STAT ON")
                    trigger_idx = self.trigger_line_combo.currentIndex()
                    if trigger_idx > 0:
                        self.keithley_6221.write(f"SOUR:WAVE:PMAR:OLIN {trigger_idx}")
                else:
                    self.keithley_6221.write("SOUR:WAVE:PMAR:STAT OFF")

                # Range mode
                if self.ac_best_range_checkbox.isChecked():
                    self.keithley_6221.write("SOUR:WAVE:RANG BEST")
                else:
                    self.keithley_6221.write("SOUR:WAVE:RANG FIX")

                # Arm and initiate
                self.keithley_6221.write("SOUR:WAVE:ARM")
                time.sleep(0.1)
                self.keithley_6221.write("SOUR:WAVE:INIT")

                self.ACisOn = True
                self.ac_arm_btn.setText("Abort Waveform")
                self.ac_arm_btn.setStyleSheet("""
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
                self.dc_send_btn.setEnabled(False)

                # Start monitoring
                self.clear_plot_data()
                self.start_ac_monitoring(waveform, amp_value, freq_value, offset_value)

                QMessageBox.information(self, "Success", "Waveform armed and initiated")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error arming waveform:\n{str(e)}")

        else:
            # Abort waveform
            self.stop_monitoring()

            if self.keithley_6221 != 'Emulation':
                try:
                    self.keithley_6221.write("SOUR:WAVE:ABOR")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Error aborting waveform:\n{str(e)}")

            self.ACisOn = False
            self.ac_arm_btn.setText("Arm Waveform")
            self.ac_arm_btn.setStyleSheet("")
            self.dc_send_btn.setEnabled(True)
            self.monitor_status_label.setText("Status: Not monitoring")

    def closeEvent(self, event):
        """Handle window close"""
        self.stop_monitoring()

        if self.reading_thread and self.reading_thread.isRunning():
            self.reading_thread.stop()
            self.reading_thread.wait()

        if self.keithley_6221 and self.keithley_6221 != 'Emulation':
            try:
                self.keithley_6221.write("OUTP OFF")
                self.keithley_6221.write("SOUR:WAVE:ABOR")
                self.keithley_6221.close()
            except:
                pass

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Keithley6221()
    window.show()
    sys.exit(app.exec())