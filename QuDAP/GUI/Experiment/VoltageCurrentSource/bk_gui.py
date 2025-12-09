from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
                             QPushButton, QComboBox, QCheckBox, QLineEdit, QMessageBox, QScrollArea, QSizePolicy,
                             QDoubleSpinBox, QRadioButton, QButtonGroup, QTabWidget)
from PyQt6.QtGui import QFont, QDoubleValidator
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import sys
import pyvisa as visa
import time
import numpy as np
import pyqtgraph as pg

# Import the standalone connection class and BK commands
try:
    from instrument.instrument_connection import InstrumentConnection
    from instrument.BK_precision_9129B import BK_9129_COMMAND
except ImportError:
    from QuDAP.instrument.instrument_connection import InstrumentConnection
    from QuDAP.instrument.BK_precision_9129B import BK_9129_COMMAND


class ReadingThread(QThread):
    """Thread for continuous reading updates when connected"""

    reading_signal = pyqtSignal(dict)  # {ch1_v, ch1_i, ch2_v, ch2_i, ch3_v, ch3_i, ch1_p, ch2_p, ch3_p}
    error_signal = pyqtSignal(str)

    def __init__(self, instrument, bk_cmd, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.bk_cmd = bk_cmd
        self.should_stop = False

    def run(self):
        """Continuously read all channels"""
        try:
            while not self.should_stop:
                try:
                    # Measure all voltages, currents, and powers
                    voltages = self.bk_cmd.measure_all_voltages(self.instrument).strip().split(',')
                    currents = self.bk_cmd.measure_all_currents(self.instrument).strip().split(',')

                    # Measure power for each channel
                    power1 = self.bk_cmd.measure_power(self.instrument, 'CH1').strip()
                    power2 = self.bk_cmd.measure_power(self.instrument, 'CH2').strip()
                    power3 = self.bk_cmd.measure_power(self.instrument, 'CH3').strip()

                    readings = {'ch1_v': float(voltages[0]), 'ch2_v': float(voltages[1]), 'ch3_v': float(voltages[2]),
                        'ch1_i': float(currents[0]), 'ch2_i': float(currents[1]), 'ch3_i': float(currents[2]),
                        'ch1_p': float(power1), 'ch2_p': float(power2), 'ch3_p': float(power3)}

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
        self.ch1_v = 5.0
        self.ch2_v = 12.0
        self.ch3_v = 3.3
        self.ch1_i = 0.5
        self.ch2_i = 1.0
        self.ch3_i = 0.3

    def run(self):
        """Generate emulated readings"""
        while not self.should_stop:
            readings = {'ch1_v': self.ch1_v + np.random.randn() * 0.01, 'ch2_v': self.ch2_v + np.random.randn() * 0.01,
                'ch3_v': self.ch3_v + np.random.randn() * 0.01, 'ch1_i': self.ch1_i + np.random.randn() * 0.001,
                'ch2_i': self.ch2_i + np.random.randn() * 0.001, 'ch3_i': self.ch3_i + np.random.randn() * 0.001,
                'ch1_p': self.ch1_v * self.ch1_i, 'ch2_p': self.ch2_v * self.ch2_i, 'ch3_p': self.ch3_v * self.ch3_i}
            self.reading_signal.emit(readings)
            time.sleep(1)

    def stop(self):
        """Stop emulation"""
        self.should_stop = True


class MonitorThread(QThread):
    """Thread for monitoring and plotting"""

    data_signal = pyqtSignal(float, dict)  # (time, readings)
    error_signal = pyqtSignal(str)

    def __init__(self, instrument, bk_cmd, is_emulation=False, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.bk_cmd = bk_cmd
        self.is_emulation = is_emulation
        self.should_stop = False
        self.start_time = time.time()

        # Emulation values
        self.ch1_v = 5.0
        self.ch2_v = 12.0
        self.ch3_v = 3.3
        self.ch1_i = 0.5
        self.ch2_i = 1.0
        self.ch3_i = 0.3

    def run(self):
        """Monitor readings for plotting"""
        try:
            while not self.should_stop:
                try:
                    elapsed_time = time.time() - self.start_time

                    if self.is_emulation:
                        # Generate simulated data
                        readings = {'ch1_v': self.ch1_v + np.random.randn() * 0.01,
                            'ch2_v': self.ch2_v + np.random.randn() * 0.01,
                            'ch3_v': self.ch3_v + np.random.randn() * 0.01,
                            'ch1_i': self.ch1_i + np.random.randn() * 0.001,
                            'ch2_i': self.ch2_i + np.random.randn() * 0.001,
                            'ch3_i': self.ch3_i + np.random.randn() * 0.001, }
                    else:
                        # Read actual values
                        voltages = self.bk_cmd.measure_all_voltages(self.instrument).strip().split(',')
                        currents = self.bk_cmd.measure_all_currents(self.instrument).strip().split(',')

                        readings = {'ch1_v': float(voltages[0]), 'ch2_v': float(voltages[1]),
                            'ch3_v': float(voltages[2]), 'ch1_i': float(currents[0]), 'ch2_i': float(currents[1]),
                            'ch3_i': float(currents[2])}

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


class BK9129(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BK Precision 9129 Triple Output DC Power Supply")
        self.setGeometry(100, 100, 1600, 900)

        self.bk_9129 = None
        self.bk_cmd = BK_9129_COMMAND()
        self.reading_thread = None
        self.monitor_thread = None
        self.emulation_thread = None
        self.isConnect = False

        # Output states
        self.ch1_output_on = False
        self.ch2_output_on = False
        self.ch3_output_on = False
        self.series_mode = False
        self.parallel_mode = False

        # Data storage for plotting
        self.time_data = []
        self.ch1_v_data = []
        self.ch1_i_data = []
        self.ch2_v_data = []
        self.ch2_i_data = []
        self.ch3_v_data = []
        self.ch3_i_data = []
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
        title = QLabel("BK Precision 9129 Triple Output DC Power Supply")
        title.setFont(self.titlefont)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_layout.addWidget(title)

        # Setup sections
        self.setup_connection_section(self.left_layout)
        self.setup_readings_section(self.left_layout)
        self.setup_combine_mode_section(self.left_layout)
        self.setup_channel_control_section(self.left_layout)
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
        self.connection_widget = InstrumentConnection(instrument_list=["BK Precision 9129"], allow_emulation=True,
            title="Instrument Connection")
        self.connection_widget.instrument_connected.connect(self.on_instrument_connected)
        self.connection_widget.instrument_disconnected.connect(self.on_instrument_disconnected)
        parent_layout.addWidget(self.connection_widget)

    def setup_readings_section(self, parent_layout):
        """Setup current readings section"""
        readings_group = QGroupBox("Channel Readings")
        readings_layout = QVBoxLayout()

        # Channel 1
        ch1_group = QGroupBox("Channel 1")
        ch1_layout = QHBoxLayout()

        ch1_v_label = QLabel("Voltage:")
        ch1_v_label.setFont(self.font)
        ch1_v_label.setFixedWidth(60)
        self.ch1_v_reading = QLabel("N/A")
        self.ch1_v_reading.setFont(self.font)

        ch1_i_label = QLabel("Current:")
        ch1_i_label.setFont(self.font)
        ch1_i_label.setFixedWidth(60)
        self.ch1_i_reading = QLabel("N/A")
        self.ch1_i_reading.setFont(self.font)

        ch1_p_label = QLabel("Power:")
        ch1_p_label.setFont(self.font)
        ch1_p_label.setFixedWidth(60)
        self.ch1_p_reading = QLabel("N/A")
        self.ch1_p_reading.setFont(self.font)

        ch1_layout.addWidget(ch1_v_label)
        ch1_layout.addWidget(self.ch1_v_reading, 1)
        ch1_layout.addWidget(ch1_i_label)
        ch1_layout.addWidget(self.ch1_i_reading, 1)
        ch1_layout.addWidget(ch1_p_label)
        ch1_layout.addWidget(self.ch1_p_reading, 1)
        ch1_group.setLayout(ch1_layout)
        readings_layout.addWidget(ch1_group)

        # Channel 2
        ch2_group = QGroupBox("Channel 2")
        ch2_layout = QHBoxLayout()

        ch2_v_label = QLabel("Voltage:")
        ch2_v_label.setFont(self.font)
        ch2_v_label.setFixedWidth(60)
        self.ch2_v_reading = QLabel("N/A")
        self.ch2_v_reading.setFont(self.font)

        ch2_i_label = QLabel("Current:")
        ch2_i_label.setFont(self.font)
        ch2_i_label.setFixedWidth(60)
        self.ch2_i_reading = QLabel("N/A")
        self.ch2_i_reading.setFont(self.font)

        ch2_p_label = QLabel("Power:")
        ch2_p_label.setFont(self.font)
        ch2_p_label.setFixedWidth(60)
        self.ch2_p_reading = QLabel("N/A")
        self.ch2_p_reading.setFont(self.font)

        ch2_layout.addWidget(ch2_v_label)
        ch2_layout.addWidget(self.ch2_v_reading, 1)
        ch2_layout.addWidget(ch2_i_label)
        ch2_layout.addWidget(self.ch2_i_reading, 1)
        ch2_layout.addWidget(ch2_p_label)
        ch2_layout.addWidget(self.ch2_p_reading, 1)
        ch2_group.setLayout(ch2_layout)
        readings_layout.addWidget(ch2_group)

        # Channel 3
        ch3_group = QGroupBox("Channel 3")
        ch3_layout = QHBoxLayout()

        ch3_v_label = QLabel("Voltage:")
        ch3_v_label.setFont(self.font)
        ch3_v_label.setFixedWidth(60)
        self.ch3_v_reading = QLabel("N/A")
        self.ch3_v_reading.setFont(self.font)

        ch3_i_label = QLabel("Current:")
        ch3_i_label.setFont(self.font)
        ch3_i_label.setFixedWidth(60)
        self.ch3_i_reading = QLabel("N/A")
        self.ch3_i_reading.setFont(self.font)

        ch3_p_label = QLabel("Power:")
        ch3_p_label.setFont(self.font)
        ch3_p_label.setFixedWidth(60)
        self.ch3_p_reading = QLabel("N/A")
        self.ch3_p_reading.setFont(self.font)

        ch3_layout.addWidget(ch3_v_label)
        ch3_layout.addWidget(self.ch3_v_reading, 1)
        ch3_layout.addWidget(ch3_i_label)
        ch3_layout.addWidget(self.ch3_i_reading, 1)
        ch3_layout.addWidget(ch3_p_label)
        ch3_layout.addWidget(self.ch3_p_reading, 1)
        ch3_group.setLayout(ch3_layout)
        readings_layout.addWidget(ch3_group)

        readings_group.setLayout(readings_layout)
        parent_layout.addWidget(readings_group)

    def setup_combine_mode_section(self, parent_layout):
        """Setup series/parallel mode section"""
        combine_group = QGroupBox("Combine Mode (CH1 + CH2)")
        combine_layout = QVBoxLayout()

        # Radio buttons for mode selection
        mode_layout = QHBoxLayout()

        self.independent_radio = QRadioButton("Independent")
        self.independent_radio.setFont(self.font)
        self.independent_radio.setChecked(True)
        self.independent_radio.toggled.connect(self.on_combine_mode_changed)

        self.series_radio = QRadioButton("Series")
        self.series_radio.setFont(self.font)
        self.series_radio.toggled.connect(self.on_combine_mode_changed)

        self.parallel_radio = QRadioButton("Parallel")
        self.parallel_radio.setFont(self.font)
        self.parallel_radio.toggled.connect(self.on_combine_mode_changed)

        self.combine_mode_group = QButtonGroup()
        self.combine_mode_group.addButton(self.independent_radio)
        self.combine_mode_group.addButton(self.series_radio)
        self.combine_mode_group.addButton(self.parallel_radio)

        mode_layout.addWidget(self.independent_radio)
        mode_layout.addWidget(self.series_radio)
        mode_layout.addWidget(self.parallel_radio)
        combine_layout.addLayout(mode_layout)

        # Apply button
        apply_layout = QHBoxLayout()
        apply_layout.addStretch()
        self.apply_combine_btn = QPushButton("Apply Mode")
        self.apply_combine_btn.setFont(self.font)
        self.apply_combine_btn.clicked.connect(self.apply_combine_mode)
        self.apply_combine_btn.setMinimumHeight(35)
        self.apply_combine_btn.setMinimumWidth(150)
        self.apply_combine_btn.setEnabled(False)
        apply_layout.addWidget(self.apply_combine_btn)
        apply_layout.addStretch()
        combine_layout.addLayout(apply_layout)

        combine_group.setLayout(combine_layout)
        parent_layout.addWidget(combine_group)

    def setup_channel_control_section(self, parent_layout):
        """Setup individual channel control section"""
        channel_tabs = QTabWidget()
        channel_tabs.setFont(self.font)

        # Channel 1 Tab
        ch1_widget = self.create_channel_widget(1)
        channel_tabs.addTab(ch1_widget, "Channel 1")

        # Channel 2 Tab
        ch2_widget = self.create_channel_widget(2)
        channel_tabs.addTab(ch2_widget, "Channel 2")

        # Channel 3 Tab
        ch3_widget = self.create_channel_widget(3)
        channel_tabs.addTab(ch3_widget, "Channel 3")

        parent_layout.addWidget(channel_tabs)

    def create_channel_widget(self, channel_num):
        """Create control widget for a channel"""
        widget = QWidget()
        layout = QVBoxLayout()

        # Voltage setting
        v_layout = QHBoxLayout()
        v_label = QLabel("Set Voltage:")
        v_label.setFont(self.font)
        v_label.setFixedWidth(100)

        v_entry = QLineEdit()
        v_entry.setFont(self.font)
        v_entry.setPlaceholderText("0-30V (CH1/CH2) or 0-5V (CH3)")
        v_validator = QDoubleValidator(0, 30 if channel_num <= 2 else 5, 3)
        v_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        v_entry.setValidator(v_validator)
        v_entry.setFixedHeight(30)

        v_unit = QLabel("V")
        v_unit.setFont(self.font)

        v_layout.addWidget(v_label)
        v_layout.addWidget(v_entry, 1)
        v_layout.addWidget(v_unit)
        layout.addLayout(v_layout)

        # Current setting
        i_layout = QHBoxLayout()
        i_label = QLabel("Set Current:")
        i_label.setFont(self.font)
        i_label.setFixedWidth(100)

        i_entry = QLineEdit()
        i_entry.setFont(self.font)
        i_entry.setPlaceholderText("0-3A (CH1/CH2) or 0-3A (CH3)")
        i_validator = QDoubleValidator(0, 3, 3)
        i_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        i_entry.setValidator(i_validator)
        i_entry.setFixedHeight(30)

        i_unit = QLabel("A")
        i_unit.setFont(self.font)

        i_layout.addWidget(i_label)
        i_layout.addWidget(i_entry, 1)
        i_layout.addWidget(i_unit)
        layout.addLayout(i_layout)

        # Set button
        set_layout = QHBoxLayout()
        set_layout.addStretch()
        set_btn = QPushButton(f"Set CH{channel_num}")
        set_btn.setFont(self.font)
        set_btn.clicked.connect(lambda: self.set_channel_values(channel_num))
        set_btn.setMinimumHeight(35)
        set_btn.setMinimumWidth(150)
        set_btn.setEnabled(False)
        set_layout.addWidget(set_btn)
        set_layout.addStretch()
        layout.addLayout(set_layout)

        # Output control
        output_layout = QHBoxLayout()
        output_layout.addStretch()
        output_btn = QPushButton(f"Output CH{channel_num} ON")
        output_btn.setFont(self.font)
        output_btn.clicked.connect(lambda: self.toggle_channel_output(channel_num))
        output_btn.setMinimumHeight(35)
        output_btn.setMinimumWidth(150)
        output_btn.setEnabled(False)
        output_layout.addWidget(output_btn)
        output_layout.addStretch()
        layout.addLayout(output_layout)

        layout.addStretch()
        widget.setLayout(layout)

        # Store references
        if channel_num == 1:
            self.ch1_v_entry = v_entry
            self.ch1_i_entry = i_entry
            self.ch1_set_btn = set_btn
            self.ch1_output_btn = output_btn
        elif channel_num == 2:
            self.ch2_v_entry = v_entry
            self.ch2_i_entry = i_entry
            self.ch2_set_btn = set_btn
            self.ch2_output_btn = output_btn
        else:
            self.ch3_v_entry = v_entry
            self.ch3_i_entry = i_entry
            self.ch3_set_btn = set_btn
            self.ch3_output_btn = output_btn

        return widget

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
        self.plot_param_combo.addItems(["Voltage", "Current"])
        self.plot_param_combo.currentTextChanged.connect(self.update_plot_display)
        param_layout.addWidget(param_label)
        param_layout.addWidget(self.plot_param_combo, 1)
        monitor_layout.addLayout(param_layout)

        # Channel visibility checkboxes
        checkbox_layout = QHBoxLayout()
        self.ch1_checkbox = QCheckBox("CH1")
        self.ch1_checkbox.setFont(self.font)
        self.ch1_checkbox.setChecked(True)
        self.ch1_checkbox.stateChanged.connect(self.update_plot_display)

        self.ch2_checkbox = QCheckBox("CH2")
        self.ch2_checkbox.setFont(self.font)
        self.ch2_checkbox.setChecked(True)
        self.ch2_checkbox.stateChanged.connect(self.update_plot_display)

        self.ch3_checkbox = QCheckBox("CH3")
        self.ch3_checkbox.setFont(self.font)
        self.ch3_checkbox.setChecked(True)
        self.ch3_checkbox.stateChanged.connect(self.update_plot_display)

        checkbox_layout.addWidget(self.ch1_checkbox)
        checkbox_layout.addWidget(self.ch2_checkbox)
        checkbox_layout.addWidget(self.ch3_checkbox)
        checkbox_layout.addStretch()
        monitor_layout.addLayout(checkbox_layout)

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
        """Setup right panel with plots"""
        plot_widget = QWidget()
        plot_layout = QVBoxLayout()
        plot_layout.setContentsMargins(10, 10, 10, 10)

        # Plot title
        plot_title = QLabel("Channel Outputs vs Time")
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

        # Create plot curves for each channel
        self.ch1_curve = self.plot_widget.plot(pen=pg.mkPen(color='b', width=2), name='CH1')
        self.ch2_curve = self.plot_widget.plot(pen=pg.mkPen(color='r', width=2), name='CH2')
        self.ch3_curve = self.plot_widget.plot(pen=pg.mkPen(color='g', width=2), name='CH3')

        plot_layout.addWidget(self.plot_widget)
        plot_widget.setLayout(plot_layout)
        parent_layout.addWidget(plot_widget)

    def on_instrument_connected(self, instrument, instrument_name):
        """Handle instrument connection"""
        self.bk_9129 = instrument
        self.isConnect = True
        print(f"Connected to {instrument_name}")

        if self.bk_9129 and self.bk_9129 != 'Emulation':
            # Initialize instrument
            self.bk_cmd.clear(self.bk_9129)

            # Turn off all outputs initially
            self.bk_cmd.set_all_outputs(self.bk_9129, '0', '0', '0')

            # Start reading thread
            self.reading_thread = ReadingThread(self.bk_9129, self.bk_cmd)
            self.reading_thread.reading_signal.connect(self.update_readings)
            self.reading_thread.error_signal.connect(self.on_reading_error)
            self.reading_thread.start()
        else:
            # Emulation mode
            self.emulation_thread = EmulationThread()
            self.emulation_thread.reading_signal.connect(self.update_readings)
            self.emulation_thread.start()

        # Enable controls
        self.apply_combine_btn.setEnabled(True)
        self.ch1_set_btn.setEnabled(True)
        self.ch2_set_btn.setEnabled(True)
        self.ch3_set_btn.setEnabled(True)
        self.ch1_output_btn.setEnabled(True)
        self.ch2_output_btn.setEnabled(True)
        self.ch3_output_btn.setEnabled(True)
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

        # Turn off outputs if connected
        if self.bk_9129 and self.bk_9129 != 'Emulation':
            try:
                self.bk_cmd.set_all_outputs(self.bk_9129, '0', '0', '0')
            except:
                pass

        self.bk_9129 = None
        self.isConnect = False
        print(f"Disconnected from {instrument_name}")

        # Disable controls
        self.apply_combine_btn.setEnabled(False)
        self.ch1_set_btn.setEnabled(False)
        self.ch2_set_btn.setEnabled(False)
        self.ch3_set_btn.setEnabled(False)
        self.ch1_output_btn.setEnabled(False)
        self.ch2_output_btn.setEnabled(False)
        self.ch3_output_btn.setEnabled(False)
        self.start_monitor_btn.setEnabled(False)

        # Reset readings
        self.ch1_v_reading.setText("N/A")
        self.ch1_i_reading.setText("N/A")
        self.ch1_p_reading.setText("N/A")
        self.ch2_v_reading.setText("N/A")
        self.ch2_i_reading.setText("N/A")
        self.ch2_p_reading.setText("N/A")
        self.ch3_v_reading.setText("N/A")
        self.ch3_i_reading.setText("N/A")
        self.ch3_p_reading.setText("N/A")

        # Reset button states
        self.ch1_output_btn.setText("Output CH1 ON")
        self.ch1_output_btn.setStyleSheet("")
        self.ch2_output_btn.setText("Output CH2 ON")
        self.ch2_output_btn.setStyleSheet("")
        self.ch3_output_btn.setText("Output CH3 ON")
        self.ch3_output_btn.setStyleSheet("")

    def update_readings(self, readings):
        """Update reading labels"""
        self.ch1_v_reading.setText(f"{readings['ch1_v']:.3f} V")
        self.ch1_i_reading.setText(f"{readings['ch1_i']:.3f} A")
        self.ch1_p_reading.setText(f"{readings['ch1_p']:.3f} W")

        self.ch2_v_reading.setText(f"{readings['ch2_v']:.3f} V")
        self.ch2_i_reading.setText(f"{readings['ch2_i']:.3f} A")
        self.ch2_p_reading.setText(f"{readings['ch2_p']:.3f} W")

        self.ch3_v_reading.setText(f"{readings['ch3_v']:.3f} V")
        self.ch3_i_reading.setText(f"{readings['ch3_i']:.3f} A")
        self.ch3_p_reading.setText(f"{readings['ch3_p']:.3f} W")

    def on_reading_error(self, error_msg):
        """Handle reading thread error"""
        print(f"Reading error: {error_msg}")

    def on_combine_mode_changed(self):
        """Handle combine mode radio button change"""
        pass  # Just for UI feedback

    def apply_combine_mode(self):
        """Apply the selected combine mode"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.bk_9129 == 'Emulation':
            if self.series_radio.isChecked():
                QMessageBox.information(self, "Emulation Mode", "Series mode enabled (CH1+CH2)")
                self.series_mode = True
                self.parallel_mode = False
            elif self.parallel_radio.isChecked():
                QMessageBox.information(self, "Emulation Mode", "Parallel mode enabled (CH1+CH2)")
                self.parallel_mode = True
                self.series_mode = False
            else:
                QMessageBox.information(self, "Emulation Mode", "Independent mode enabled")
                self.series_mode = False
                self.parallel_mode = False
            return

        try:
            if self.series_radio.isChecked():
                self.bk_cmd.set_series_mode(self.bk_9129)
                self.series_mode = True
                self.parallel_mode = False
                QMessageBox.information(self, "Success", "Series mode enabled (CH1+CH2)")
            elif self.parallel_radio.isChecked():
                self.bk_cmd.set_parallel_mode(self.bk_9129)
                self.parallel_mode = True
                self.series_mode = False
                QMessageBox.information(self, "Success", "Parallel mode enabled (CH1+CH2)")
            else:
                self.bk_cmd.disable_combine_mode(self.bk_9129)
                self.series_mode = False
                self.parallel_mode = False
                QMessageBox.information(self, "Success", "Independent mode enabled")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting combine mode:\n{str(e)}")

    def set_channel_values(self, channel_num):
        """Set voltage and current for a channel"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        # Get entry widgets
        if channel_num == 1:
            v_entry = self.ch1_v_entry
            i_entry = self.ch1_i_entry
        elif channel_num == 2:
            v_entry = self.ch2_v_entry
            i_entry = self.ch2_i_entry
        else:
            v_entry = self.ch3_v_entry
            i_entry = self.ch3_i_entry

        voltage = v_entry.text()
        current = i_entry.text()

        if not voltage or not current:
            QMessageBox.warning(self, "Missing Input", "Please enter both voltage and current")
            return

        if self.bk_9129 == 'Emulation':
            QMessageBox.information(self, "Emulation Mode",
                                    f"CH{channel_num} set to:\nVoltage: {voltage} V\nCurrent: {current} A")
            return

        try:
            # Select channel
            channel_name = f"CH{channel_num}"
            self.bk_cmd.select_channel(self.bk_9129, channel_name)
            time.sleep(0.05)

            # Set voltage and current
            self.bk_cmd.set_voltage(self.bk_9129, float(voltage), 'V')
            time.sleep(0.05)
            self.bk_cmd.set_current(self.bk_9129, float(current), 'A')

            QMessageBox.information(self, "Success",
                                    f"CH{channel_num} configured:\nVoltage: {voltage} V\nCurrent: {current} A")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting channel values:\n{str(e)}")

    def toggle_channel_output(self, channel_num):
        """Toggle output for a channel"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        # Get button and current state
        if channel_num == 1:
            btn = self.ch1_output_btn
            is_on = self.ch1_output_on
        elif channel_num == 2:
            btn = self.ch2_output_btn
            is_on = self.ch2_output_on
        else:
            btn = self.ch3_output_btn
            is_on = self.ch3_output_on

        if self.bk_9129 == 'Emulation':
            if not is_on:
                btn.setText(f"Output CH{channel_num} OFF")
                btn.setStyleSheet("""
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
                if channel_num == 1:
                    self.ch1_output_on = True
                elif channel_num == 2:
                    self.ch2_output_on = True
                else:
                    self.ch3_output_on = True
            else:
                btn.setText(f"Output CH{channel_num} ON")
                btn.setStyleSheet("")
                if channel_num == 1:
                    self.ch1_output_on = False
                elif channel_num == 2:
                    self.ch2_output_on = False
                else:
                    self.ch3_output_on = False
            return

        try:
            # Select channel
            channel_name = f"CH{channel_num}"
            self.bk_cmd.select_channel(self.bk_9129, channel_name)
            time.sleep(0.05)

            if not is_on:
                # Turn ON
                self.bk_cmd.set_channel_output_state(self.bk_9129, 'ON')
                btn.setText(f"Output CH{channel_num} OFF")
                btn.setStyleSheet("""
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
                if channel_num == 1:
                    self.ch1_output_on = True
                elif channel_num == 2:
                    self.ch2_output_on = True
                else:
                    self.ch3_output_on = True
            else:
                # Turn OFF
                self.bk_cmd.set_channel_output_state(self.bk_9129, 'OFF')
                btn.setText(f"Output CH{channel_num} ON")
                btn.setStyleSheet("")
                if channel_num == 1:
                    self.ch1_output_on = False
                elif channel_num == 2:
                    self.ch2_output_on = False
                else:
                    self.ch3_output_on = False

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error toggling output:\n{str(e)}")

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

        is_emulation = (self.bk_9129 == 'Emulation')

        self.monitor_thread = MonitorThread(self.bk_9129, self.bk_cmd, is_emulation)
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
        self.ch1_v_data.append(readings['ch1_v'])
        self.ch1_i_data.append(readings['ch1_i'])
        self.ch2_v_data.append(readings['ch2_v'])
        self.ch2_i_data.append(readings['ch2_i'])
        self.ch3_v_data.append(readings['ch3_v'])
        self.ch3_i_data.append(readings['ch3_i'])

        # Limit data points
        if len(self.time_data) > self.max_points:
            self.time_data = self.time_data[-self.max_points:]
            self.ch1_v_data = self.ch1_v_data[-self.max_points:]
            self.ch1_i_data = self.ch1_i_data[-self.max_points:]
            self.ch2_v_data = self.ch2_v_data[-self.max_points:]
            self.ch2_i_data = self.ch2_i_data[-self.max_points:]
            self.ch3_v_data = self.ch3_v_data[-self.max_points:]
            self.ch3_i_data = self.ch3_i_data[-self.max_points:]

        # Update plot
        self.update_plot_display()

    def update_plot_display(self):
        """Update plot based on selected parameter and checkboxes"""
        if not self.time_data:
            return

        plot_mode = self.plot_param_combo.currentText()

        # Update y-axis label
        if plot_mode == "Voltage":
            self.plot_widget.setLabel('left', 'Voltage (V)')
            ch1_data = self.ch1_v_data
            ch2_data = self.ch2_v_data
            ch3_data = self.ch3_v_data
        else:  # Current
            self.plot_widget.setLabel('left', 'Current (A)')
            ch1_data = self.ch1_i_data
            ch2_data = self.ch2_i_data
            ch3_data = self.ch3_i_data

        # Update curves based on checkboxes
        if self.ch1_checkbox.isChecked():
            self.ch1_curve.setData(self.time_data, ch1_data)
        else:
            self.ch1_curve.setData([], [])

        if self.ch2_checkbox.isChecked():
            self.ch2_curve.setData(self.time_data, ch2_data)
        else:
            self.ch2_curve.setData([], [])

        if self.ch3_checkbox.isChecked():
            self.ch3_curve.setData(self.time_data, ch3_data)
        else:
            self.ch3_curve.setData([], [])

    def clear_plot_data(self):
        """Clear all plot data"""
        self.time_data = []
        self.ch1_v_data = []
        self.ch1_i_data = []
        self.ch2_v_data = []
        self.ch2_i_data = []
        self.ch3_v_data = []
        self.ch3_i_data = []

        self.ch1_curve.setData([], [])
        self.ch2_curve.setData([], [])
        self.ch3_curve.setData([], [])

        self.save_data_btn.setEnabled(False)
        print("Plot data cleared")

    def save_data(self):
        """Save data to CSV file"""
        if not self.time_data:
            QMessageBox.warning(self, "No Data", "No data to save")
            return

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bk9129_data_{timestamp}.csv"

        try:
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Time (s)', 'CH1 Voltage (V)', 'CH1 Current (A)', 'CH2 Voltage (V)', 'CH2 Current (A)',
                                 'CH3 Voltage (V)', 'CH3 Current (A)'])
                for i in range(len(self.time_data)):
                    writer.writerow([self.time_data[i], self.ch1_v_data[i], self.ch1_i_data[i], self.ch2_v_data[i],
                        self.ch2_i_data[i], self.ch3_v_data[i], self.ch3_i_data[i]])

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

        if self.bk_9129 and self.bk_9129 != 'Emulation':
            try:
                self.bk_cmd.set_all_outputs(self.bk_9129, '0', '0', '0')
                self.bk_9129.close()
            except:
                pass

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BK9129()
    window.show()
    sys.exit(app.exec())