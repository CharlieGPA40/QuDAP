from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
                             QPushButton, QComboBox, QCheckBox, QLineEdit, QMessageBox, QScrollArea, QSizePolicy,
                             QRadioButton, QButtonGroup)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import sys
import pyvisa as visa
import random
import time
import pyqtgraph as pg
from datetime import datetime

# Import the standalone connection class
try:
    from instrument.instrument_connection import InstrumentConnection
except ImportError:
    from QuDAP.instrument.instrument_connection import InstrumentConnection

class MonitorThread(QThread):
    """Thread to monitor voltage parameters in real-time"""

    data_signal = pyqtSignal(float, float, float)  # (time, ch1_voltage, ch2_voltage)
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
                    # Read Channel 1
                    self.instrument.write("SENS:CHAN 1")
                    Chan_1_voltage = float(self.instrument.query("FETCH?"))

                    # Read Channel 2
                    self.instrument.write("SENS:CHAN 2")
                    Chan_2_voltage = float(self.instrument.query("FETCH?"))

                    # Calculate elapsed time
                    elapsed_time = time.time() - self.start_time

                    # Emit data
                    self.data_signal.emit(elapsed_time, Chan_1_voltage, Chan_2_voltage)

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


class EmulationThread(QThread):
    """Thread for emulation mode monitoring"""

    data_signal = pyqtSignal(float, float, float)  # (time, ch1_voltage, ch2_voltage)
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
                    # Generate random voltages
                    Chan_1_voltage = random.randint(0, 1000) / 1000
                    Chan_2_voltage = random.randint(0, 1000) / 100

                    # Calculate elapsed time
                    elapsed_time = time.time() - self.start_time

                    # Emit data
                    self.data_signal.emit(elapsed_time, Chan_1_voltage, Chan_2_voltage)

                    # Sleep for update interval
                    time.sleep(0.5)

                except Exception as e:
                    self.error_signal.emit(f"Emulation error: {str(e)}")
                    break

        except Exception as e:
            self.error_signal.emit(f"Thread error: {str(e)}")

    def stop(self):
        """Stop monitoring"""
        self.should_stop = True


class NV(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keithley Nanovoltmeter")
        self.setGeometry(100, 100, 1400, 900)

        self.keithley_2182A_NV = None
        self.monitor_thread = None
        self.isConnect = False

        # Data storage
        self.time_data = []
        self.channel1_data = []
        self.channel2_data = []

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
        self.scroll_area.setFixedWidth(400)

        # Content widget for scroll area
        left_content = QWidget()
        left_content.setMaximumWidth(380)

        self.left_layout = QVBoxLayout()
        self.left_layout.setContentsMargins(10, 10, 10, 10)
        self.left_layout.setSpacing(10)

        # Title
        title = QLabel("Keithley Nanovoltmeter")
        title.setFont(self.titlefont)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_layout.addWidget(title)

        # Connection section using standalone class
        self.setup_connection_section(self.left_layout)

        # Configuration section
        self.setup_configuration_section(self.left_layout)

        # Voltage reading section
        self.setup_voltage_reading_section(self.left_layout)

        # Real-time monitoring section
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
        self.connection_widget = InstrumentConnection(instrument_list=["Keithley 2182A"], allow_emulation=True,
            title="Instrument Connection")
        self.connection_widget.instrument_connected.connect(self.on_instrument_connected)
        self.connection_widget.instrument_disconnected.connect(self.on_instrument_disconnected)
        parent_layout.addWidget(self.connection_widget)

    def setup_configuration_section(self, parent_layout):
        """Setup configuration section (NPLC, filters, etc.)"""
        config_group = QGroupBox("Configuration")
        config_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        config_layout = QVBoxLayout()

        # NPLC (Number of Power Line Cycles)
        nplc_layout = QHBoxLayout()
        nplc_label = QLabel("NPLC:")
        nplc_label.setFont(self.font)
        nplc_label.setFixedWidth(80)
        nplc_label.setToolTip("Number of power line cycle (Integration time - N/60 or N/50);\n"
                              "1). 0.1 for fast speed high noise;\n"
                              "2). 1 for medium integration time\n"
                              "3). 5 for slow integration time.")

        self.NPLC_entry = QLineEdit()
        self.NPLC_entry.setFont(self.font)
        self.NPLC_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.NPLC_entry.setText('5')

        nplc_layout.addWidget(nplc_label)
        nplc_layout.addWidget(self.NPLC_entry, 1)
        config_layout.addLayout(nplc_layout)

        # Line Synchronization radio buttons
        lsync_label = QLabel("Line Synchronization:")
        lsync_label.setFont(self.font)
        lsync_label.setToolTip("This is the filter to synchronize the power line frequency.")
        config_layout.addWidget(lsync_label)

        lsync_layout = QHBoxLayout()
        self.keithley_2182_lsync_on_radio = QRadioButton("ON")
        self.keithley_2182_lsync_on_radio.setFont(self.font)
        self.keithley_2182_lsync_on_radio.setChecked(True)
        self.keithley_2182_lsync_off_radio = QRadioButton("OFF")
        self.keithley_2182_lsync_off_radio.setFont(self.font)

        lsync_layout.addWidget(self.keithley_2182_lsync_on_radio)
        lsync_layout.addWidget(self.keithley_2182_lsync_off_radio)

        self.keithley_2182_lsync_button_group = QButtonGroup()
        self.keithley_2182_lsync_button_group.addButton(self.keithley_2182_lsync_on_radio, 0)
        self.keithley_2182_lsync_button_group.addButton(self.keithley_2182_lsync_off_radio, 1)

        config_layout.addLayout(lsync_layout)

        # Filter selection radio buttons
        filter_label = QLabel("Filter Selection:")
        filter_label.setFont(self.font)
        config_layout.addWidget(filter_label)

        filter_layout = QVBoxLayout()
        self.keithley_2182_digital_filter_radio = QRadioButton("Digital Filter")
        self.keithley_2182_digital_filter_radio.setFont(self.font)
        self.keithley_2182_analog_filter_radio = QRadioButton("Analog Filter")
        self.keithley_2182_analog_filter_radio.setFont(self.font)
        self.keithley_2182_no_filter_radio = QRadioButton("OFF")
        self.keithley_2182_no_filter_radio.setFont(self.font)
        self.keithley_2182_no_filter_radio.setChecked(True)

        filter_layout.addWidget(self.keithley_2182_digital_filter_radio)
        filter_layout.addWidget(self.keithley_2182_analog_filter_radio)
        filter_layout.addWidget(self.keithley_2182_no_filter_radio)

        self.keithley_2182_filter_button_group = QButtonGroup()
        self.keithley_2182_filter_button_group.addButton(self.keithley_2182_digital_filter_radio, 0)
        self.keithley_2182_filter_button_group.addButton(self.keithley_2182_analog_filter_radio, 1)
        self.keithley_2182_filter_button_group.addButton(self.keithley_2182_no_filter_radio, 2)

        config_layout.addLayout(filter_layout)

        # Apply configuration button
        apply_config_btn = QPushButton("Apply Configuration")
        apply_config_btn.clicked.connect(self.apply_configuration)
        apply_config_btn.setFont(self.font)
        apply_config_btn.setMinimumHeight(30)
        config_layout.addWidget(apply_config_btn)

        config_group.setLayout(config_layout)
        parent_layout.addWidget(config_group)

    def setup_voltage_reading_section(self, parent_layout):
        """Setup voltage reading section"""
        voltage_group = QGroupBox("Current Readings")
        voltage_layout = QVBoxLayout()

        # Channel 1
        channel1_layout = QHBoxLayout()
        channel1_label = QLabel("Channel 1:")
        channel1_label.setFont(self.font)
        channel1_label.setFixedWidth(80)
        self.channel1_Volt = QLabel("N/A")
        self.channel1_Volt.setFont(self.font)
        self.channel1_Volt.setWordWrap(True)
        channel1_layout.addWidget(channel1_label)
        channel1_layout.addWidget(self.channel1_Volt, 1)
        voltage_layout.addLayout(channel1_layout)

        # Channel 2
        channel2_layout = QHBoxLayout()
        channel2_label = QLabel("Channel 2:")
        channel2_label.setFont(self.font)
        channel2_label.setFixedWidth(80)
        self.channel2_Volt = QLabel("N/A")
        self.channel2_Volt.setFont(self.font)
        self.channel2_Volt.setWordWrap(True)
        channel2_layout.addWidget(channel2_label)
        channel2_layout.addWidget(self.channel2_Volt, 1)
        voltage_layout.addLayout(channel2_layout)

        # Update readings button
        update_btn = QPushButton("Update Readings")
        update_btn.clicked.connect(self.update_readings_from_instrument)
        update_btn.setFont(self.font)
        update_btn.setMinimumHeight(30)
        voltage_layout.addWidget(update_btn)

        voltage_group.setLayout(voltage_layout)
        parent_layout.addWidget(voltage_group)

    def setup_monitor_section(self, parent_layout):
        """Setup real-time monitoring section"""
        monitor_group = QGroupBox("Real-time Monitoring")
        monitor_layout = QVBoxLayout()

        # Channel selection checkboxes
        self.ch1_monitor_checkbox = QCheckBox("Monitor Channel 1")
        self.ch1_monitor_checkbox.setFont(self.font)
        self.ch1_monitor_checkbox.setChecked(True)
        monitor_layout.addWidget(self.ch1_monitor_checkbox)

        self.ch2_monitor_checkbox = QCheckBox("Monitor Channel 2")
        self.ch2_monitor_checkbox.setFont(self.font)
        self.ch2_monitor_checkbox.setChecked(True)
        monitor_layout.addWidget(self.ch2_monitor_checkbox)

        # Monitor control buttons
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

        # Monitor status
        self.monitor_status = QLabel("Status: Not monitoring")
        self.monitor_status.setWordWrap(True)
        self.monitor_status.setFont(self.font)
        monitor_layout.addWidget(self.monitor_status)

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
        """Create the plot panel with PyQtGraph"""
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        plot_title = QLabel("Real-time Voltage Monitoring")
        plot_title_font = QFont()
        plot_title_font.setPointSize(12)
        plot_title_font.setBold(True)
        plot_title.setFont(plot_title_font)
        plot_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(plot_title)

        # Create Channel 1 plot
        self.ch1_plot_widget = pg.PlotWidget()
        self.ch1_plot_widget.setBackground('w')
        self.ch1_plot_widget.setLabel('left', 'Channel 1 Voltage', units='V')
        self.ch1_plot_widget.setLabel('bottom', 'Time', units='s')
        self.ch1_plot_widget.setTitle('Channel 1 Voltage vs Time')
        self.ch1_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.ch1_plot_widget.addLegend()

        self.ch1_curve = self.ch1_plot_widget.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), symbol='o', symbolSize=4,
            symbolBrush=(0, 0, 255), name='Channel 1')

        # Create Channel 2 plot
        self.ch2_plot_widget = pg.PlotWidget()
        self.ch2_plot_widget.setBackground('w')
        self.ch2_plot_widget.setLabel('left', 'Channel 2 Voltage', units='V')
        self.ch2_plot_widget.setLabel('bottom', 'Time', units='s')
        self.ch2_plot_widget.setTitle('Channel 2 Voltage vs Time')
        self.ch2_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.ch2_plot_widget.addLegend()

        self.ch2_curve = self.ch2_plot_widget.plot(pen=pg.mkPen(color=(255, 0, 0), width=2), symbol='o', symbolSize=4,
            symbolBrush=(255, 0, 0), name='Channel 2')

        right_layout.addWidget(self.ch1_plot_widget)
        right_layout.addWidget(self.ch2_plot_widget)

        right_panel.setLayout(right_layout)
        return right_panel

    def on_instrument_connected(self, instrument, instrument_name):
        """Handle instrument connection"""
        self.keithley_2182A_NV = instrument
        self.isConnect = True
        print(f"Connected to {instrument_name}")

        # Update readings if real instrument
        if self.keithley_2182A_NV:
            self.update_readings_from_instrument()

        # Enable monitor button
        self.start_monitor_btn.setEnabled(True)

    def on_instrument_disconnected(self, instrument_name):
        """Handle instrument disconnection"""
        # Stop monitoring if active
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.stop_monitoring()

        self.keithley_2182A_NV = None
        self.isConnect = False
        print(f"Disconnected from {instrument_name}")

        # Disable monitor button
        self.start_monitor_btn.setEnabled(False)
        self.channel1_Volt.setText("N/A")
        self.channel2_Volt.setText("N/A")

    def apply_configuration(self):
        """Apply NPLC and filter configuration to instrument"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.keithley_2182A_NV == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Configuration is not applied in emulation mode")
            return

        try:
            nplc_value = self.NPLC_entry.text()
            # Apply NPLC setting
            self.keithley_2182A_NV.write(f"SENS:VOLT:NPLC {nplc_value}")

            # Apply line sync setting
            selected_lsync = self.keithley_2182_lsync_button_group.checkedId()
            if selected_lsync == 0:  # ON
                self.keithley_2182A_NV.write("SYST:LSYN ON")
            else:  # OFF
                self.keithley_2182A_NV.write("SYST:LSYN OFF")

            # Apply filter setting
            selected_filter = self.keithley_2182_filter_button_group.checkedId()
            if selected_filter == 0:  # Digital filter
                self.keithley_2182A_NV.write("SENS:VOLT:DFIL ON")
                self.keithley_2182A_NV.write("SENS:VOLT:LPAS OFF")
            elif selected_filter == 1:  # Analog filter
                self.keithley_2182A_NV.write("SENS:VOLT:LPAS ON")
                self.keithley_2182A_NV.write("SENS:VOLT:DFIL OFF")
            else:  # No filter
                self.keithley_2182A_NV.write("SENS:VOLT:DFIL OFF")
                self.keithley_2182A_NV.write("SENS:VOLT:LPAS OFF")

            QMessageBox.information(self, "Success", "Configuration applied successfully")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error applying configuration:\n{str(e)}")

    def update_readings_from_instrument(self):
        """Update voltage readings from instrument"""
        if not self.isConnect or not self.keithley_2182A_NV:
            return

        if self.keithley_2182A_NV == 'Emulation':
            self.channel1_Volt.setText(f"{random.random():.6f} V")
            self.channel2_Volt.setText(f"{random.random() * 10:.6f} V")
            return

        try:
            # Read Channel 1
            self.keithley_2182A_NV.write("SENS:CHAN 1")
            ch1_voltage = float(self.keithley_2182A_NV.query("FETCH?"))
            self.channel1_Volt.setText(f"{ch1_voltage:.6f} V")

            # Read Channel 2
            self.keithley_2182A_NV.write("SENS:CHAN 2")
            ch2_voltage = float(self.keithley_2182A_NV.query("FETCH?"))
            self.channel2_Volt.setText(f"{ch2_voltage:.6f} V")
        except Exception as e:
            print(f"Error updating readings: {e}")

    def start_monitoring(self):
        """Start real-time monitoring"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if not self.ch1_monitor_checkbox.isChecked() and not self.ch2_monitor_checkbox.isChecked():
            QMessageBox.warning(self, "No Selection", "Please select at least one channel to monitor")
            return

        # Clear previous data
        self.time_data = []
        self.channel1_data = []
        self.channel2_data = []
        self.ch1_curve.setData([], [])
        self.ch2_curve.setData([], [])

        # Start monitor thread
        if self.keithley_2182A_NV == 'Emulation':
            self.monitor_thread = EmulationThread()
        else:
            self.monitor_thread = MonitorThread(self.keithley_2182A_NV)

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

    def update_plots(self, time_val, ch1_voltage, ch2_voltage):
        """Update plots with new data"""
        self.time_data.append(time_val)
        self.channel1_data.append(ch1_voltage)
        self.channel2_data.append(ch2_voltage)

        # Update Channel 1 plot if selected
        if self.ch1_monitor_checkbox.isChecked():
            self.ch1_curve.setData(self.time_data, self.channel1_data)

        # Update Channel 2 plot if selected
        if self.ch2_monitor_checkbox.isChecked():
            self.ch2_curve.setData(self.time_data, self.channel2_data)

        # Update reading labels
        self.channel1_Volt.setText(f"{ch1_voltage:.6f} V")
        self.channel2_Volt.setText(f"{ch2_voltage:.6f} V")

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
        self.channel1_data = []
        self.channel2_data = []
        self.ch1_curve.setData([], [])
        self.ch2_curve.setData([], [])

        QMessageBox.information(self, "Data Cleared", "Plot data has been cleared")

    def save_data(self):
        """Save monitoring data to file"""
        if not self.time_data:
            QMessageBox.warning(self, "No Data", "No data to save")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"keithley2182_data_{timestamp}.csv"

            with open(filename, 'w') as f:
                f.write("Time (s),Channel 1 (V),Channel 2 (V)\n")
                for i in range(len(self.time_data)):
                    f.write(f"{self.time_data[i]},{self.channel1_data[i]},{self.channel2_data[i]}\n")

            QMessageBox.information(self, "Data Saved",
                f"Data saved to:\n{filename}\n\nTotal points: {len(self.time_data)}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving data:\n{str(e)}")

    def closeEvent(self, event):
        """Handle window close"""
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.monitor_thread.stop()
            self.monitor_thread.wait()

        if self.keithley_2182A_NV and self.keithley_2182A_NV != 'Emulation':
            try:
                self.keithley_2182A_NV.close()
            except:
                pass

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NV()
    window.show()
    sys.exit(app.exec())