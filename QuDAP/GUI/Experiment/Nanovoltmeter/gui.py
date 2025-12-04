try:
    from instrument.instrument_connection import InstrumentConnection
except ImportError:
    from QuDAP.instrument.instrument_connection import InstrumentConnection

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
                             QPushButton, QComboBox, QCheckBox, QMessageBox, QScrollArea, QSizePolicy)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import sys
import pyvisa as visa
import matplotlib
import random
import time

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class THREAD(QThread):
    update_data = pyqtSignal(float, float)  # Signal to emit the temperature and field values

    def __init__(self, server):
        super().__init__()
        print(str(server))
        self.server = server
        self.running = True

    def run(self):
        while self.running:
            try:
                self.server.write("SENS:CHAN 1")
                Chan_1_voltage = float(self.server.query("FETCH?"))  # Read the measurement result
                error = self.server.query("SYST:ERR?")
                print(str(error))
                self.server.write("SENS:CHAN 2")
                Chan_2_voltage = float(self.server.query("FETCH?"))  # Read the measurement result
                error = self.server.query("SYST:ERR?")
                print(str(error))
                self.update_data.emit(Chan_1_voltage, Chan_2_voltage)
                time.sleep(1)  # Update every second
            except Exception as e:
                print(f"Error: {e}")
                self.running = False

    def stop(self):
        self.running = False

class EMULATION(QThread):
    update_data = pyqtSignal(float, float)  # Signal to emit the temperature and field values

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            try:
                Chan_1_voltage = random.randint(0, 1000) / 1000
                Chan_2_voltage = random.randint(0, 1000) / 100
                self.update_data.emit(Chan_1_voltage, Chan_2_voltage)
                time.sleep(1)  # Update every second
            except Exception as e:
                print(f"Error: {e}")
                self.running = False

    def stop(self):
        self.running = False

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=300):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class NV(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keithley 2182 Nanovoltmeter")
        self.setGeometry(100, 100, 1400, 900)

        self.isConnect = False
        self.isPlotting = False
        self.keithley_2182A_NV = 'None'
        self.connect_btn_clicked = False
        self.isCheckedBox1 = False
        self.isCheckedBox2 = False
        self.counter = 0
        self.counter_array = []
        self.channel1_Volt_Array = []
        self.channel2_Volt_Array = []
        self.Chan_1_voltage = 0
        self.Chan_2_voltage = 0

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

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)

        # Title
        title = QLabel("Keithley 2182 Nanovoltmeter")
        title.setFont(self.titlefont)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title)

        # Connection section
        self.setup_connection_section(left_layout)

        # Voltage reading section
        self.setup_voltage_reading_section(left_layout)

        # Plotting control section
        self.setup_plotting_control_section(left_layout)

        # Add stretch at the end
        left_layout.addStretch()

        left_content.setLayout(left_layout)
        self.scroll_area.setWidget(left_content)

        # Right panel - Graph (no scroll)
        right_panel = self.create_graph_panel()

        # Add panels to main layout
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(right_panel, 1)

        central_widget.setLayout(main_layout)

    def setup_connection_section(self, parent_layout):
        """Setup device connection section"""
        connection_group = QGroupBox("Device Connection")
        connection_layout = QVBoxLayout()

        # GPIB ComboBox and Refresh button
        combo_layout = QHBoxLayout()

        self.gpib_combo = QComboBox()
        try:
            with open("GUI/QSS/QComboWidget.qss", "r") as file:
                self.QCombo_stylesheet = file.read()
            self.gpib_combo.setStyleSheet(self.QCombo_stylesheet)
        except:
            pass
        self.gpib_combo.setFont(self.font)

        refresh_btn = QPushButton(icon=QIcon("GUI/Icon/refresh.svg"))
        refresh_btn.clicked.connect(self.refresh_gpib_list)
        refresh_btn.setFixedWidth(40)

        try:
            with open("GUI/QSS/QButtonWidget.qss", "r") as file:
                self.Button_stylesheet = file.read()
            refresh_btn.setStyleSheet(self.Button_stylesheet)
        except:
            pass

        combo_layout.addWidget(self.gpib_combo, 3)
        combo_layout.addWidget(refresh_btn)
        connection_layout.addLayout(combo_layout)

        # Connect button
        self.connect_btn = QPushButton('Connect')
        self.connect_btn.clicked.connect(self.connect_current_gpib)
        self.connect_btn.setFont(self.font)
        self.connect_btn.setMinimumHeight(30)
        try:
            self.connect_btn.setStyleSheet(self.Button_stylesheet)
        except:
            pass
        connection_layout.addWidget(self.connect_btn)

        # Current connection label
        self.current_gpib_label = QLabel("Current Connection: None")
        self.current_gpib_label.setFont(self.font)
        self.current_gpib_label.setWordWrap(True)
        self.current_gpib_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        connection_layout.addWidget(self.current_gpib_label)

        connection_group.setLayout(connection_layout)
        parent_layout.addWidget(connection_group)

        # Initialize GPIB list
        self.refresh_gpib_list()

    def setup_voltage_reading_section(self, parent_layout):
        """Setup voltage reading section"""
        voltage_group = QGroupBox("Voltage Reading")
        voltage_layout = QVBoxLayout()

        # Channel 1
        channel1_layout = QHBoxLayout()
        channel1_label = QLabel("Channel 1:")
        channel1_label.setFont(self.font)
        channel1_label.setFixedWidth(80)
        self.channel1_Volt = QLabel("N/A Volts")
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
        self.channel2_Volt = QLabel("N/A Volts")
        self.channel2_Volt.setFont(self.font)
        self.channel2_Volt.setWordWrap(True)
        channel2_layout.addWidget(channel2_label)
        channel2_layout.addWidget(self.channel2_Volt, 1)
        voltage_layout.addLayout(channel2_layout)

        voltage_group.setLayout(voltage_layout)
        parent_layout.addWidget(voltage_group)

    def setup_plotting_control_section(self, parent_layout):
        """Setup plotting control section"""
        plotting_group = QGroupBox("Plotting Selection")
        plotting_layout = QVBoxLayout()

        # Checkboxes
        self.checkbox1 = QCheckBox("Channel 1")
        self.checkbox1.setFont(self.font)
        plotting_layout.addWidget(self.checkbox1)

        self.checkbox2 = QCheckBox("Channel 2")
        self.checkbox2.setFont(self.font)
        plotting_layout.addWidget(self.checkbox2)

        # Control buttons
        button_layout = QHBoxLayout()

        plot_btn = QPushButton('Plot')
        plot_btn.clicked.connect(self.plot_selection)
        plot_btn.setFont(self.font)
        plot_btn.setMinimumHeight(30)
        plot_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border-style: solid;
                border-color: #3498DB;
                border-width: 2px;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #2874A6;
            }
            QPushButton:pressed {
                background-color: #85C1E9;
            }
        """)

        stop_btn = QPushButton('Stop')
        stop_btn.clicked.connect(self.stop)
        stop_btn.setFont(self.font)
        stop_btn.setMinimumHeight(30)
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #D98880;
                color: white;
                border-style: solid;
                border-color: #D98880;
                border-width: 2px;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #E74C3C;
            }
            QPushButton:pressed {
                background-color: #FADBD8;
            }
        """)

        rst_btn = QPushButton('Reset')
        rst_btn.clicked.connect(self.rst)
        rst_btn.setFont(self.font)
        rst_btn.setMinimumHeight(30)
        rst_btn.setStyleSheet("""
            QPushButton {
                background-color: #CAC9Cb;
                color: black;
                border-style: solid;
                border-color: #CAC9Cb;
                border-width: 2px;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #5F6A6A;
            }
            QPushButton:pressed {
                background-color: #979A9A;
            }
        """)

        button_layout.addWidget(plot_btn)
        button_layout.addWidget(stop_btn)

        plotting_layout.addLayout(button_layout)
        plotting_layout.addWidget(rst_btn)

        plotting_group.setLayout(plotting_layout)
        parent_layout.addWidget(plotting_group)

    def create_graph_panel(self):
        """Create the graph panel"""
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        graph_title = QLabel("Real-time Voltage Monitoring")
        graph_title_font = QFont()
        graph_title_font.setPointSize(12)
        graph_title_font.setBold(True)
        graph_title.setFont(graph_title_font)
        graph_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(graph_title)

        # Create matplotlib canvas
        self.canvas = MplCanvas(self, width=8, height=6, dpi=100)

        # Create toolbar
        toolbar = NavigationToolbar(self.canvas, self)
        toolbar.setStyleSheet("""
            QWidget {
                border: None;
            }
        """)

        right_layout.addWidget(toolbar)
        right_layout.addWidget(self.canvas)

        right_panel.setLayout(right_layout)
        return right_panel

    def refresh_gpib_list(self):
        """Refresh the list of available GPIB devices"""
        try:
            rm = visa.ResourceManager()
            instruments = rm.list_resources()
            self.gpib_ports = [instr for instr in instruments]
        except:
            self.gpib_ports = []

        self.current_gpib_label.setText("Current Connection: None")

        # Clear existing items and add new ones
        self.gpib_combo.clear()
        self.gpib_combo.addItems(["None"])
        self.gpib_combo.addItems(self.gpib_ports)
        self.gpib_combo.addItems(["Emulation"])

        self.connect_btn.setText('Connect')
        self.connect_btn_clicked = False
        self.isConnect = False
        self.isCheckedBox1 = False
        self.isCheckedBox2 = False
        self.counter = 0
        self.counter_array = []

        if self.isPlotting:
            self.rst()

    def connect_current_gpib(self):
        """Connect/disconnect to the selected GPIB device"""
        rm = visa.ResourceManager()

        if self.connect_btn_clicked == False:
            self.connect_btn.setText('Disconnect')
            self.connect_btn_clicked = True
        elif self.connect_btn_clicked == True:
            if self.isPlotting:
                self.rst()
            self.connect_btn.setText('Connect')
            self.current_gpib_label.setText("Current Connection: None")
            if self.gpib_combo.currentText() != 'Emulation':
                try:
                    self.keithley_2182A_NV.close()
                except:
                    pass
            self.connect_btn_clicked = False

        self.current_connection = self.gpib_combo.currentText()

        if self.current_connection == 'None':
            self.isConnect = False
        else:
            if self.connect_btn_clicked == False:
                self.isConnect = False
            else:
                self.current_gpib_label.setText(f"Attempt to connect {self.current_connection}...")
                try:
                    if self.current_connection == 'Emulation':
                        self.isConnect = True
                        self.current_gpib_label.setText(f"Current Connection: Emulation")
                        if self.isConnect:
                            self.emulation = EMULATION()
                            self.emulation.update_data.connect(self.update_voltage)
                            self.emulation.start()
                    else:
                        self.keithley_2182A_NV = rm.open_resource(self.current_connection, timeout=10000)
                        time.sleep(2)
                        keithley_2182A_NV = self.keithley_2182A_NV.query('*IDN?')
                        self.isConnect = True
                        self.current_gpib_label.setText(f"{self.current_connection} Connection Success!")
                        time.sleep(1)
                        self.current_gpib_label.setText(f"Current Connection: {keithley_2182A_NV}")

                        if self.isConnect:
                            self.thread = THREAD(server=self.keithley_2182A_NV)
                            self.thread.update_data.connect(self.update_voltage)
                            self.thread.start()
                except visa.errors.VisaIOError as e:
                    self.isConnect = False
                    self.current_gpib_label.setText(f"Connecting {self.current_connection} fail!")
                    QMessageBox.warning(self, "Connection Error", str(e))

    def update_voltage(self, Chan_1_voltage, Chan_2_voltage):
        """Update voltage readings"""
        self.Chan_1_voltage = Chan_1_voltage
        self.Chan_2_voltage = Chan_2_voltage

        if self.isConnect:
            self.channel1_Volt.setText(f"{self.Chan_1_voltage:.4f} Volts")
            self.channel2_Volt.setText(f"{self.Chan_2_voltage:.4f} Volts")
        else:
            self.channel1_Volt.setText("N/A Volts")
            self.channel2_Volt.setText("N/A Volts")

    def plot_selection(self):
        """Start plotting based on checkbox selection"""
        status = []

        if self.checkbox1.isChecked():
            status.append(self.checkbox1.text())
            self.isCheckedBox1 = True
        else:
            self.isCheckedBox1 = False

        if self.checkbox2.isChecked():
            status.append(self.checkbox2.text())
            self.isCheckedBox2 = True
        else:
            self.isCheckedBox2 = False

        if len(status) > 0 and self.isConnect == True:
            self.canvas.axes.cla()
            self.channel1_Volt_Array = []
            self.channel2_Volt_Array = []
            self.counter = 0
            self.counter_array = []
            self.counter_array.append(self.counter)

            self.canvas.axes.set_xlabel('Time (s)')
            self.canvas.axes.set_ylabel('Voltage (V)')
            self.canvas.axes.set_title('Voltage vs Time')
            self.canvas.axes.grid(True, alpha=0.3)

            self.update_plot()

            # Setup a timer to trigger the redraw
            self.timer = QTimer()
            self.timer.setInterval(1000)
            self.timer.timeout.connect(self.update_plot)
            self.timer.start()
        elif not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")

    def update_plot(self):
        """Update the plot with new data"""
        self.canvas.axes.cla()

        if self.isCheckedBox1 == True:
            self.isPlotting = True
            self.channel1_Volt_Array.append(self.Chan_1_voltage)
            self.canvas.axes.plot(self.counter_array, self.channel1_Volt_Array, 'b-', label='Channel 1')

        if self.isCheckedBox2 == True:
            self.isPlotting = True
            self.channel2_Volt_Array.append(self.Chan_2_voltage)
            self.canvas.axes.plot(self.counter_array, self.channel2_Volt_Array, 'r-', label='Channel 2')

        self.canvas.axes.set_xlabel('Time (s)')
        self.canvas.axes.set_ylabel('Voltage (V)')
        self.canvas.axes.set_title('Voltage vs Time')
        self.canvas.axes.grid(True, alpha=0.3)
        self.canvas.axes.legend()

        self.canvas.draw()

        self.counter += 1
        self.counter_array.append(self.counter)

    def stop(self):
        """Stop plotting"""
        if hasattr(self, 'timer'):
            self.timer.stop()

    def rst(self):
        """Reset the plot"""
        if hasattr(self, 'timer'):
            self.timer.stop()

        self.canvas.axes.cla()
        self.canvas.axes.set_xlabel('Time (s)')
        self.canvas.axes.set_ylabel('Voltage (V)')
        self.canvas.axes.set_title('Voltage vs Time')
        self.canvas.axes.grid(True, alpha=0.3)
        self.canvas.draw()

        self.isPlotting = False
        self.counter = 0
        self.counter_array = []
        self.channel1_Volt_Array = []
        self.channel2_Volt_Array = []

    def closeEvent(self, event):
        """Handle window close"""
        if self.isPlotting:
            self.rst()

        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.stop()
            self.thread.wait()

        if hasattr(self, 'emulation') and self.emulation.isRunning():
            self.emulation.stop()
            self.emulation.wait()

        if self.keithley_2182A_NV != 'None':
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