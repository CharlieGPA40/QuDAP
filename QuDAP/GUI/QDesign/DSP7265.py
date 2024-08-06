from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QScrollArea, QGroupBox, QSizePolicy, QVBoxLayout, QLabel, QHBoxLayout
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
    update_data = pyqtSignal(float, float, float, float)  # Signal to emit the temperature and field values

    def __init__(self, server):
        super().__init__()
        print(str(server))
        self.server = server
        self.running = True

    def run(self):
        while self.running:
            try:
                X = float(self.server.query("X."))  # Read the measurement result
                Y = float(self.server.query("Y."))  # Read the measurement result
                Mag = float(self.server.query("MAG."))  # Read the measurement result
                Phase = float(self.server.query("PHA."))  # Read the measurement result
                self.update_data.emit(X,Y,Mag, Phase)
                time.sleep(0.01)  # Update every second
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


class Lockin(QMainWindow):

    def __init__(self):
        super().__init__()
        try:
            self.isConnect = False
            self.isPlotting = False
            self.DSP7265 = 'None'
            self.init_ui()

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def init_ui(self):
        titlefont = QFont("Arial", 20)
        font = QFont("Arial", 13)
        self.setStyleSheet("background-color: white;")

        self.setStyleSheet("background-color: white;")
        with open("GUI/QSS/QScrollbar.qss", "r") as file:
            self.scrollbar_stylesheet = file.read()

        self.scroll_area = QScrollArea()
        # self.scroll_area.setFixedSize(1200,920)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(self.scrollbar_stylesheet)
        # Create a widget to hold the main layout
        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)

        # Create main vertical layout with centered alignment
        self.main_layout = QVBoxLayout(self.content_widget)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set the content widget to expand
        self.content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


        #  ---------------------------- PART 1 --------------------------------
        self.current_intrument_label = QLabel("Signal Recovery 7265 DSP Lock-in Amplifier")
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
        self.lockin_reading_plotting_layout = QHBoxLayout()

        self.Lockin_reading_group_box = QGroupBox("Lock-in Reading")
        self.lockin_reading_layout = QVBoxLayout()

        self.lockin_x_reading_layout = QHBoxLayout()
        self.lockiin_x_reading_text_label = QLabel('X: ')
        self.lockiin_x_reading_text_label.setFont(font)
        self.lockiin_x_reading_label = QLabel('N/A Volts')
        self.lockiin_x_reading_label.setFont(font)
        self.lockin_x_reading_layout.addWidget(self.lockiin_x_reading_text_label)
        self.lockin_x_reading_layout.addWidget(self.lockiin_x_reading_label)

        self.lockin_y_reading_layout = QHBoxLayout()
        self.lockiin_y_reading_text_label = QLabel('Y: ')
        self.lockiin_y_reading_text_label.setFont(font)
        self.lockiin_y_reading_label = QLabel('N/A Volts')
        self.lockiin_y_reading_label.setFont(font)
        self.lockin_y_reading_layout.addWidget(self.lockiin_y_reading_text_label)
        self.lockin_y_reading_layout.addWidget(self.lockiin_y_reading_label)

        self.lockin_mag_reading_layout = QHBoxLayout()
        self.lockiin_mag_reading_text_label = QLabel('Magnitude: ')
        self.lockiin_mag_reading_text_label.setFont(font)
        self.lockiin_mag_reading_label = QLabel('N/A Volts')
        self.lockiin_mag_reading_label.setFont(font)
        self.lockin_mag_reading_layout.addWidget(self.lockiin_mag_reading_text_label)
        self.lockin_mag_reading_layout.addWidget(self.lockiin_mag_reading_label)

        self.lockin_phase_reading_layout = QHBoxLayout()
        self.lockiin_phase_reading_text_label = QLabel('Phase: ')
        self.lockiin_phase_reading_text_label.setFont(font)
        self.lockiin_phase_reading_label = QLabel('N/A deg')
        self.lockiin_phase_reading_label.setFont(font)
        self.lockin_phase_reading_layout.addWidget(self.lockiin_phase_reading_text_label)
        self.lockin_phase_reading_layout.addWidget(self.lockiin_phase_reading_label)

        self.lockin_reading_layout.addLayout(self.lockin_x_reading_layout)
        self.lockin_reading_layout.addLayout(self.lockin_y_reading_layout)
        self.lockin_reading_layout.addLayout(self.lockin_mag_reading_layout)
        self.lockin_reading_layout.addLayout(self.lockin_phase_reading_layout)

        self.Lockin_reading_group_box.setLayout(self.lockin_reading_layout)

        # #  ---------------------------- PART 3 Right --------------------------------
        #
        # graphing_layout = QHBoxLayout()
        # figure_group_box = QGroupBox("Graph")
        # figure_Layout = QVBoxLayout()
        # self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        # toolbar = NavigationToolbar(self.canvas, self)
        # toolbar.setStyleSheet("""
        #                            QWidget {
        #                                border: None;
        #                            }
        #                        """)
        # figure_Layout.addWidget(toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
        # figure_Layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)
        # figure_group_box.setLayout(figure_Layout)
        # graphing_layout.addWidget(plotting_control_group_box)
        # graphing_layout.addWidget(figure_group_box)

        #  ---------------------------- Main Layout --------------------------------
        # Add widgets to the main layout with centered alignment
        self.main_layout.addWidget(self.current_intrument_label, alignment=Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(group_box)
        self.main_layout.addWidget(self.Lockin_reading_group_box)
        # main_layout.addWidget(voltage_reading_group_box)
        # main_layout.addLayout(graphing_layout)
        self.setLayout(self.main_layout)
        self.setCentralWidget(self.scroll_area)
        #  ---------------------------- Style Sheet --------------------------------
        with open("GUI/QSS/QButtonWidget.qss", "r") as file:
            self.Button_stylesheet = file.read()
        self.connect_btn.setStyleSheet(self.Button_stylesheet)
        refresh_btn.setStyleSheet(self.Button_stylesheet)
        # plot_btn.setStyleSheet("""
        #            QPushButton {
        #                background-color: #3498DB; /* Green background */
        #                color: white; /* White text */
        #                border-style: solid;
        #                border-color: #3498DB;
        #                border-width: 2px;
        #                border-radius: 10px; /* Rounded corners */
        #                padding: 5px;
        #                min-height: 2px;
        #                min-width: 50px;
        #            }
        #            QPushButton:hover {
        #                background-color: #2874A6  ; /* Slightly darker green */
        #            }
        #            QPushButton:pressed {
        #                background-color: #85C1E9; /* Even darker green */
        #            }
        #        """)
        #
        # rst_btn.setStyleSheet("""
        #                            QPushButton {
        #                                background-color: #CAC9Cb; /* Green background */
        #                                color: black; /* White text */
        #                                border-style: solid;
        #                                border-color: #CAC9Cb;
        #                                border-width: 2px;
        #                                border-radius: 10px; /* Rounded corners */
        #                                padding: 5px;
        #                                min-height: 1px;
        #                                min-width: 50px;
        #                            }
        #                            QPushButton:hover {
        #                                background-color: #5F6A6A; /* Slightly darker green */
        #                            }
        #                            QPushButton:pressed {
        #                                background-color: #979A9A; /* Even darker green */
        #                            }
        #                        """)
        # self.connect_btn.setStyleSheet(self.Button_stylesheet)
        # refresh_btn.setStyleSheet(self.Button_stylesheet)
        #
        # stop_btn.setStyleSheet("""
        #                                    QPushButton {
        #                                        background-color: #D98880; /* Green background */
        #                                        color: white; /* White text */
        #                                        border-style: solid;
        #                                        border-color: #D98880;
        #                                        border-width: 2px;
        #                                        border-radius: 10px; /* Rounded corners */
        #                                        padding: 5px;
        #                                        min-height: 1px;
        #                                        min-width: 50px;
        #                                    }
        #                                    QPushButton:hover {
        #                                        background-color: #E74C3C; /* Slightly darker green */
        #                                    }
        #                                    QPushButton:pressed {
        #                                        background-color: #FADBD8; /* Even darker green */
        #                                    }
        #                                """)

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
                    self.DSP7265 = rm.open_resource(self.current_connection, timeout=10000)
                    time.sleep(2)
                    DSP7265_device = self.DSP7265.query('ID')
                    self.isConnect = True
                    self.current_gpib_label.setText(f"{self.current_connection} Connection Success!")
                    time.sleep(1)
                    self.current_gpib_label.setText(f"Current Connection: {DSP7265_device}")
                    if self.isConnect:
                        self.thread = THREAD(server=self.DSP7265)
                        self.thread.update_data.connect(self.update_lockin)
                        self.thread.start()
                except visa.errors.VisaIOError:
                    self.isConnect = False
                    self.current_gpib_label.setText(f"Connecting {self.current_connection} fail!")
                # Comment it in real implementation
                self.isConnect = True

    def update_lockin(self, X, Y, Mag, Phase):
        self.X = X
        self.Y = Y
        self.Mag = Mag
        self.Phase = Phase
        if self.isConnect:
            self.lockiin_x_reading_label.setText(f"{self.X} Volts")
            self.lockiin_y_reading_label.setText(f"{self.Y} Volts")
            self.lockiin_mag_reading_label.setText(f"{self.Mag} Volts")
            self.lockiin_phase_reading_label.setText(f"{self.Phase} deg")

        else:
            self.lockiin_x_reading_label.setText(f"N/A Volts")
            self.lockiin_y_reading_label.setText(f"N/A Volts")
            self.lockiin_mag_reading_label.setText(f"N/A Volts")
            self.lockiin_phase_reading_label.setText(f"N/A deg")

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
