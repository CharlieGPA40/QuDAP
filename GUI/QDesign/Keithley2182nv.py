from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QRadioButton, QGroupBox, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QPushButton, QComboBox, QMessageBox)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread
import sys
import pyvisa as visa
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import random
import time


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
                Chan_2_voltage = float(self.server.query("FETCH?"))  # Read th
                error = self.server.query("SYST:ERR?")
                print(str(error))
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


class NV(QWidget):

    def __init__(self):
        super().__init__()
        try:
            self.isConnect = False
            self.isPlotting = False
            self.keithley_2182A_NV = 'None'
            self.init_ui()

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def init_ui(self):
        titlefont = QFont("Arial", 20)
        font = QFont("Arial", 13)
        self.setStyleSheet("background-color: white;")

        # Create main vertical layout with centered alignment
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #  ---------------------------- PART 1 --------------------------------
        self.current_intrument_label = QLabel("Keithley 2182 Nanovoltmeter")
        self.current_intrument_label.setFont(titlefont)
        self.current_intrument_label.setStyleSheet("""
                                            QLabel{
                                                background-color: white;
                                                }
                                                """)
        #  ---------------------------- PART 2 --------------------------------
        # GPIB ComboBox
        self.gpib_combo = QComboBox()
        with open("GUI/QSS/QComboWidget.qss", "r") as file:
            self.QCombo_stylesheet = file.read()
        self.gpib_combo.setStyleSheet(self.QCombo_stylesheet)
        self.gpib_combo.setFont(font)

        self.current_gpib_label = QLabel("Current Connection: None")
        self.current_gpib_label.setFont(font)
        # Refresh Button
        refresh_btn = QPushButton(icon=QIcon("GUI/Icon/refresh.svg"))

        refresh_btn.clicked.connect(self.refresh_gpib_list)
        # Label to display current GPIB connection

        # self.gpib_combo.currentTextChanged.connect(self.update_current_gpib)
        # Populate GPIB ports initially
        self.connect_btn = QPushButton('Connect')
        self.connect_btn_clicked = False
        self.connect_btn.clicked.connect(self.connect_current_gpib)

        # Layout for the combobox and refresh button
        combo_text_layout = QVBoxLayout()
        group_box = QGroupBox("Device Connection")

        # Set the layout for the group box

        # combo_text_widget.setStyleSheet("QWidget { border: 2px solid black; }")
        combo_layout = QHBoxLayout()
        combo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        combo_layout.addWidget(self.gpib_combo, 4)
        combo_layout.addWidget(refresh_btn, 1)
        self.refresh_gpib_list()
        combo_layout.addWidget(self.connect_btn, 2)
        combo_layout.setContentsMargins(50, 0, 50, 0)
        combo_text_layout.addLayout(combo_layout)
        combo_text_layout.addWidget(self.current_gpib_label, alignment=Qt.AlignmentFlag.AlignCenter)
        group_box.setLayout(combo_text_layout)

        #  ---------------------------- PART 3 --------------------------------
        voltage_reading_group_box = QGroupBox("Voltage Reading")  # Container widget for the horizontal layout
        voltage_reading_layout = QVBoxLayout()
        # voltage_reading_widget.setStyleSheet("QWidget { border: 2px solid black; }")
        channel1_read_layout = QHBoxLayout()
        self.channel1_Label = QLabel("Channel 1:")
        self.channel1_Label.setFont(font)
        self.channel1_Volt = QLabel("N/A Volts")
        self.channel1_Volt.setFont(font)

        channel2_read_layout = QHBoxLayout()
        self.channel2_Label = QLabel("Channel 2:")
        self.channel2_Label.setFont(font)
        self.channel2_Volt = QLabel("N/A Volts")
        self.channel2_Volt.setFont(font)
        # self.setStyleSheet("""
        #                                         QLabel{
        #                                             background-color: #F8F8F8;
        #                                             }
        #                                             """)
        # self.gpib_combo.currentTextChanged.connect(self.update_current_gpib)
        # self.voltage_timer = QTimer()
        # self.voltage_timer.setInterval(1000)
        # self.voltage_timer.timeout.connect(self.update_voltage)
        # self.voltage_timer.start()
        channel1_read_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        channel1_read_layout.addWidget(self.channel1_Label, 1)
        channel1_read_layout.addWidget(self.channel1_Volt, 5)
        channel1_read_layout.setContentsMargins(50, 0, 250, 0)
        channel2_read_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        channel2_read_layout.addWidget(self.channel2_Label, 1)
        channel2_read_layout.addWidget(self.channel2_Volt, 5)
        channel2_read_layout.setContentsMargins(50, 0, 250, 0)

        voltage_reading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        voltage_reading_layout.addLayout(channel1_read_layout, 1)
        voltage_reading_layout.addLayout(channel2_read_layout, 1)
        voltage_reading_group_box.setLayout(voltage_reading_layout)

        #  ---------------------------- PART 4 --------------------------------

        graphing_layout = QHBoxLayout()
        selection_Layout = QHBoxLayout()
        plotting_control_group_box = QGroupBox("Plotting Selection")

        self.checkbox1 = QCheckBox("Channel 1")
        self.checkbox1.setFont(font)
        self.checkbox2 = QCheckBox("Channel 2")
        self.checkbox2.setFont(font)

        plot_btn = QPushButton('Plot')
        plot_btn.clicked.connect(self.plot_selection)
        stop_btn = QPushButton('Stop')
        stop_btn.clicked.connect(self.stop)
        rst_btn = QPushButton('Reset')
        rst_btn.clicked.connect(self.rst)
        selection_Layout.addWidget(plot_btn)
        selection_Layout.addWidget(stop_btn)
        selection_Layout.addWidget(rst_btn)

        # Arrange radio buttons horizontally
        radio_layout = QVBoxLayout()
        radio_layout.addWidget(self.checkbox1)
        radio_layout.addWidget(self.checkbox2)
        radio_layout.addLayout(selection_Layout)
        plotting_control_group_box.setLayout(radio_layout)

        figure_group_box = QGroupBox("Graph")
        figure_Layout = QVBoxLayout()
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        toolbar = NavigationToolbar(self.canvas, self)
        toolbar.setStyleSheet("""
                                   QWidget {
                                       border: None; 
                                   }
                               """)
        figure_Layout.addWidget(toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
        figure_Layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)
        figure_group_box.setLayout(figure_Layout)
        graphing_layout.addWidget(plotting_control_group_box)
        graphing_layout.addWidget(figure_group_box)

        #  ---------------------------- Main Layout --------------------------------
        # Add widgets to the main layout with centered alignment
        main_layout.addWidget(self.current_intrument_label, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(group_box)
        main_layout.addWidget(voltage_reading_group_box)
        main_layout.addLayout(graphing_layout)
        self.setLayout(main_layout)

        #  ---------------------------- Style Sheet --------------------------------
        with open("GUI/QSS/QButtonWidget.qss", "r") as file:
            self.Button_stylesheet = file.read()
        plot_btn.setStyleSheet("""
                   QPushButton {
                       background-color: #3498DB; /* Green background */
                       color: white; /* White text */
                       border-style: solid;
                       border-color: #3498DB;
                       border-width: 2px;
                       border-radius: 10px; /* Rounded corners */
                       padding: 5px;
                       min-height: 2px;
                       min-width: 50px;
                   }
                   QPushButton:hover {
                       background-color: #2874A6  ; /* Slightly darker green */
                   }
                   QPushButton:pressed {
                       background-color: #85C1E9; /* Even darker green */
                   }
               """)

        rst_btn.setStyleSheet("""
                                   QPushButton {
                                       background-color: #CAC9Cb; /* Green background */
                                       color: black; /* White text */
                                       border-style: solid;
                                       border-color: #CAC9Cb;
                                       border-width: 2px;
                                       border-radius: 10px; /* Rounded corners */
                                       padding: 5px;
                                       min-height: 1px;
                                       min-width: 50px;
                                   }
                                   QPushButton:hover {
                                       background-color: #5F6A6A; /* Slightly darker green */
                                   }
                                   QPushButton:pressed {
                                       background-color: #979A9A; /* Even darker green */
                                   }
                               """)
        self.connect_btn.setStyleSheet(self.Button_stylesheet)
        refresh_btn.setStyleSheet(self.Button_stylesheet)

        stop_btn.setStyleSheet("""
                                           QPushButton {
                                               background-color: #D98880; /* Green background */
                                               color: white; /* White text */
                                               border-style: solid;
                                               border-color: #D98880;
                                               border-width: 2px;
                                               border-radius: 10px; /* Rounded corners */
                                               padding: 5px;
                                               min-height: 1px;
                                               min-width: 50px;
                                           }
                                           QPushButton:hover {
                                               background-color: #E74C3C; /* Slightly darker green */
                                           }
                                           QPushButton:pressed {
                                               background-color: #FADBD8; /* Even darker green */
                                           }
                                       """)

    def refresh_gpib_list(self):
        # Access GPIB ports using PyVISA
        rm = visa.ResourceManager()
        instruments = rm.list_resources()
        self.gpib_ports = [instr for instr in instruments]
        self.current_gpib_label.setText(f"Current Connection: None")
        # Clear existing items and add new ones
        self.gpib_combo.clear()
        self.gpib_combo.addItems(["None"])
        self.gpib_combo.addItems(self.gpib_ports)
        # self.gpib_combo.addItems(["GPIB:7"])
        # self.gpib_combo.addItems(["GPIB:8"])
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
        rm = visa.ResourceManager()
        if self.connect_btn_clicked == False:
            self.connect_btn.setText('Disonnect')
            self.connect_btn_clicked = True
        elif self.connect_btn_clicked == True:
            if self.isPlotting:
                self.rst()
            self.connect_btn.setText('Connect')
            self.current_gpib_label.setText("Current Connection: None")
            self.keithley_2182A_NV.close()
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
                    self.keithley_2182A_NV = rm.open_resource(self.current_connection, timeout=10000)
                    time.sleep(2)
                    keithley_2182A_NV = self.keithley_2182A_NV.query('*IDN?')
                    self.isConnect = True
                    self.current_gpib_label.setText(f"{self.current_connection} Connection Success!")
                    time.sleep(1)
                    self.current_gpib_label.setText(f"Current Connection: {keithley_2182A_NV}")
                    # self.keithley_2182A_NV.write("SENS:CHAN 1")
                    # Chan_1_voltage = float(self.keithley_2182A_NV.query("FETCH?"))  # Read the measurement result
                    # print(Chan_1_voltage)
                    self.keep_reading = True
                    # while self.keep_reading:
                    #     self.timer = QTimer(self)
                    #     self.timer.timeout.connect(self.update_voltage)
                    #     self.timer.start(2000)  # Update every second

                    if self.isConnect:
                        self.thread = THREAD(server=self.keithley_2182A_NV)
                        self.thread.update_data.connect(self.update_voltage)
                        self.thread.start()
                except visa.errors.VisaIOError:
                    self.isConnect = False
                    self.current_gpib_label.setText(f"Connecting {self.current_connection} fail!")
                # Comment it in real implementation
                self.isConnect = True

        # self.keithley_2182A_NV=rm.open_resource(self.current_connection, timeout=10000)

    # def enable_thread(self):
    #     if self.isConnect == True:
    #         self.keep_reading = True
    #         while self.keep_reading:

    def update_voltage(self, Chan_1_voltage, Chan_2_voltage):
        self.Chan_1_voltage = Chan_1_voltage
        self.Chan_2_voltage = Chan_2_voltage
        if self.isConnect:
            # This is for testing uncommand it to test GUI
            # self.Chan_1_voltage = random.randint(0, 1000) / 1000
            # self.Chan_2_voltage = random.randint(0, 1000) / 100

            self.channel1_Volt.setText(f"{self.Chan_1_voltage} Volts")
            self.channel2_Volt.setText(f"{self.Chan_2_voltage} Volts")

            # This is for real interfac uncommand it to test GUI
            # self.keithley_2182A_NV.write("SENS:CHAN 1")
            # Chan_1_voltage = float(self.keithley_2182A_NV.query("FETCH?"))  # Read the measurement result
            # self.channel1_Volt.setText(f"{Chan_1_voltage} Volts")
            # self.keithley_2182A_NV.write("SENS:CHAN 2")
            # # keithley_2182A_NV.write("SENS:CHAN2:RANG AUTO")
            # Chan_2_voltage = float(self.keithley_2182A_NV.query("FETCH?"))  # Read th
            # self.channel2_Volt.setText(f"{Chan_2_voltage} Volts")
        else:
            self.channel1_Volt.setText(f"N/A Volts")
            self.channel2_Volt.setText(f"N/A Volts")

    def plot_selection(self):
        # This method updates the label based on the checkbox states
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
            self.update_plot()
            self.show()

            # Setup a timer to trigger the redraw by calling update_plot.
            self.timer = QTimer()
            self.timer.setInterval(1000)
            self.timer.timeout.connect(self.update_plot)
            self.timer.start()

    def update_plot(self):
        # self.canvas.axes.cla()  # Clear the canvas.
        if self.isCheckedBox1 == True:
            self.isPlotting = True
            self.channel1_Volt_Array.append(self.Chan_1_voltage)
            # # Drop off the first y element, append a new one.
            self.canvas.axes.plot(self.counter_array, self.channel1_Volt_Array, 'black')
            self.canvas.draw()
        if self.isCheckedBox2 == True:
            self.isPlotting = True
            self.channel2_Volt_Array.append(self.Chan_2_voltage)
            # # Drop off the first y element, append a new one.
            self.canvas.axes.plot(self.counter_array, self.channel2_Volt_Array, 'r')
            self.canvas.draw()
        self.counter += 1
        self.counter_array.append(self.counter)

    def stop(self):
        self.timer.stop()

    def rst(self):
        # This method updates the label based on the checkbox states
        self.timer = QTimer()
        self.timer.stop()
        self.canvas.axes.cla()
        self.canvas.draw()
