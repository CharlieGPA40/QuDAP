from PyQt6.QtWidgets import (
    QTextEdit, QButtonGroup, QWidget, QRadioButton, QGroupBox, QFileDialog, QVBoxLayout, QLabel, QHBoxLayout
, QDialog, QPushButton, QComboBox, QLineEdit)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread
import sys
import pandas as pd
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import random
import time

class UserDefineFittingWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('User Defined Fitting Window')
        self.setGeometry(150, 150, 300, 200)

        self.layout = QVBoxLayout()

        self.label = QLabel('Enter some text:', self)
        self.layout.addWidget(self.label)

        self.textbox = QLineEdit(self)
        self.layout.addWidget(self.textbox)

        self.btn_close = QPushButton('Close', self)
        self.btn_close.clicked.connect(self.close)
        self.layout.addWidget(self.btn_close)

        self.setLayout(self.layout)


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=300):
        fig = Figure(figsize=(width, height), dpi=dpi)

        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class General(QWidget):

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        titlefont = QFont("Arial", 20)
        self.font = QFont("Arial", 13)
        self.setStyleSheet("background-color: white;")

        # Create main vertical layout with centered alignment
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #  ---------------------------- PART 1 --------------------------------
        self.SHG_General_label = QLabel("SHG Data Processing")
        self.SHG_General_label.setFont(titlefont)
        self.SHG_General_label.setStyleSheet("""
                                            QLabel{
                                                background-color: white;
                                                }
                                                """)
        #  ---------------------------- PART 2 --------------------------------
        self.file_selection_group_box = QGroupBox("Directory Selection")
        self.file_selection_section_layout = QHBoxLayout()
        self.file_selection_main_layout = QVBoxLayout()

        self.file_selection_label = QLabel('Please select the data directory:')
        self.file_selection_label.setFont(self.font)
        self.file_selection_button = QPushButton('Select')
        self.file_selection_button.setStyleSheet("""
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
        self.file_selection_display_label = QLabel('Directory Selected: N/A')
        self.file_selection_display_label.setFont(QFont("Arial", 9))
        self.file_selection_button.clicked.connect(self.showDialog)
        self.file_selection_section_layout.addStretch(1)
        self.file_selection_section_layout.addWidget(self.file_selection_label, 2)
        self.file_selection_section_layout.addStretch(2)
        self.file_selection_section_layout.addWidget(self.file_selection_button, 1)
        self.file_selection_section_layout.addStretch(1)

        self.file_selection_main_layout.addLayout(self.file_selection_section_layout)
        self.file_selection_main_layout.addWidget(self.file_selection_display_label , alignment=Qt.AlignmentFlag.AlignCenter)
        self.file_selection_main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_selection_group_box.setLayout(self.file_selection_main_layout)

        self.main_layout.addWidget(self.SHG_General_label, alignment=Qt.AlignmentFlag.AlignTop)
        self.main_layout.addWidget(self.file_selection_group_box)


    def showDialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            print(folder)
            folder = folder + "/"
            self.folder = folder
            self.file_selection_display_label.setText("Current Folder: {}".format(self.folder))
            #  ---------------------------- PART 3&4 --------------------------------
            self.auto_fitting_selection_layout = QHBoxLayout()
            self.Auto_mode_group_box = QGroupBox("Auto Mode")
            self.Fitting_mode_group_box = QGroupBox("Data Fitting")
            #  ---------------------------- PART 3 --------------------------------
            self.auto_mode_layout = QVBoxLayout()
            self.auto_mode_yes_radio_buttom = QRadioButton("Auto")
            self.auto_mode_yes_radio_buttom.setFont(self.font)
            self.auto_mode_no_radio_buttom = QRadioButton("Manual")
            self.auto_mode_no_radio_buttom.setFont(self.font)

            self.auto_mode_layout.addWidget(self.auto_mode_yes_radio_buttom)
            self.auto_mode_layout.addWidget(self.auto_mode_no_radio_buttom)

            self.buttonGroup = QButtonGroup()
            self.buttonGroup.addButton(self.auto_mode_yes_radio_buttom)
            self.buttonGroup.addButton(self.auto_mode_no_radio_buttom)

            self.auto_mode_yes_radio_buttom.toggled.connect(self.updateModeSelection)
            self.auto_mode_no_radio_buttom.toggled.connect(self.updateModeSelection)

            self.Auto_mode_group_box.setLayout(self.auto_mode_layout)
            self.auto_fitting_selection_layout.addWidget(self.Auto_mode_group_box)

            #  ---------------------------- PART 4 -------------------------------
            self.fitting_mode_layout = QVBoxLayout()
            self.fitting_mode_predef_radio_buttom = QRadioButton("Pre-defined")
            self.fitting_mode_predef_radio_buttom.setFont(self.font)
            self.fitting_mode_usr_radio_buttom = QRadioButton("User-defined")
            self.fitting_mode_usr_radio_buttom.setFont(self.font)
            self.fitting_mode_no_radio_buttom = QRadioButton("No")
            self.fitting_mode_no_radio_buttom.setFont(self.font)

            self.fitting_mode_predef_layout = QHBoxLayout()
            self.fitting_mode_predef_combo = QComboBox()
            self.fitting_mode_predef_combo.setStyleSheet("""
                        QComboBox {
                            padding: 5px;
                            background-color: white;
                            border: 2px solid #c0c0c0;
                            border-radius: 4px;
                            }
                        QComboBox::item:selected {
                            background-color: #FFFFFF;  /* Background color for selected item */
                            color: #7CACEC
                        }

                        QComboBox::drop-down {
                            subcontrol-origin: padding;
                            subcontrol-position: top right;
                            width: 20px;   /* Width of the arrow button */
                            border-left-width: 1px;
                            border-left-color: darkgray;
                            border-left-style: solid; /* just a single line at the left */
                            border-top-right-radius: 3px; /* same radius as the QComboBox */
                            border-bottom-right-radius: 3px;
                        }
                        QComboBox::down-arrow {
                            image: url(Icon/chevron-down.svg); /* Set your own icon for the arrow */
                        }
                        QComboBox::down-arrow:on { /* When the combo box is open */
                            top: 1px;
                            left: 1px;
                        }
                    """)
            self.fitting_mode_predef_combo.setFont(self.font)
            self.fitting_mode_predef_combo.addItems(["Please select a model"])
            # self.fitting_mode_predef_combo.setEnabled(True)
            self.fitting_mode_predef_button = QPushButton('Select')
            self.fitting_mode_predef_button.setStyleSheet("""
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
            self.fitting_mode_predef_button.setFont(self.font)

            # self.fitting_mode_predef_button.setEnabled(True)
            self.fitting_mode_predef_layout.addWidget(self.fitting_mode_predef_radio_buttom)
            self.fitting_mode_predef_layout.addWidget(self.fitting_mode_predef_combo)
            self.fitting_mode_predef_layout.addWidget(self.fitting_mode_predef_button)

            self.fitting_mode_usrdef_layout = QHBoxLayout()
            self.fitting_mode_usrdef_button = QPushButton('Define')
            self.fitting_mode_usrdef_button.setStyleSheet("""
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
            self.fitting_mode_usrdef_button.setFont(self.font)
            # self.fitting_mode_usrdef_button.setEnabled(True)
            self.fitting_mode_usrdef_layout.addWidget(self.fitting_mode_usr_radio_buttom)
            self.fitting_mode_usrdef_layout.addWidget(self.fitting_mode_usrdef_button)

            self.fitting_mode_layout.addLayout(self.fitting_mode_predef_layout)
            self.fitting_mode_layout.addLayout(self.fitting_mode_usrdef_layout)
            self.fitting_mode_layout.addWidget(self.fitting_mode_no_radio_buttom)

            self.Fitting_mode_group_box.setLayout(self.fitting_mode_layout)
            self.auto_fitting_selection_layout.addWidget(self.Fitting_mode_group_box)

            self.fitting_buttonGroup = QButtonGroup()
            self.fitting_buttonGroup.addButton(self.fitting_mode_predef_radio_buttom)
            self.fitting_buttonGroup.addButton(self.fitting_mode_usr_radio_buttom)
            self.fitting_buttonGroup.addButton(self.fitting_mode_no_radio_buttom)

            self.fitting_mode_predef_radio_buttom.toggled.connect(self.updateFitSelection)
            self.fitting_mode_usr_radio_buttom.toggled.connect(self.updateFitSelection)
            self.fitting_mode_no_radio_buttom.toggled.connect(self.updateFitSelection)

        #  ---------------------------- Main Layout --------------------------------
        # Add widgets to the main layout with centered alignment
            self.main_layout.addLayout(self.auto_fitting_selection_layout)

            self.process_layout = QHBoxLayout()
            self.rst_button = QPushButton('Reset')
            self.rst_button.setFont(self.font)
            self.rst_button.setStyleSheet("""
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
            self.rst_button.clicked.connect(self.rstpage)
            self.Process_button = QPushButton('Process')
            self.Process_button.setStyleSheet("""
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
            self.Process_button.clicked.connect(self.process_data)
            self.Process_button.setFont(self.font)
            self.process_layout.addStretch(3)
            self.process_layout.addWidget(self.rst_button)
            self.process_layout.addWidget(self.Process_button)

            self.main_layout.addLayout(self.process_layout)

            self.setLayout(self.main_layout)

        #  ---------------------------- Style Sheet --------------------------------
    def PresetModel(self):
        self.current_model = self.fitting_mode_predef_combo.currentText()
        print(self.current_model)

    def updateModeSelection(self):
        selectedButton = self.buttonGroup.checkedButton()
        if selectedButton:
            self.autoSelection = selectedButton.text()
            print(self.autoSelection)

    def updateFitSelection(self):
        selectedButton = self.fitting_buttonGroup.checkedButton()
        if selectedButton:
            self.FitSeleciton = selectedButton.text()
            print(self.FitSeleciton)
            if self.FitSeleciton == 'Pre-defined':
                self.fitting_mode_predef_combo.setEnabled(True)
                self.fitting_mode_predef_button.setEnabled(True)
                self.fitting_mode_usrdef_button.setEnabled(False)
                self.fitting_mode_predef_button.clicked.connect(self.PresetModel)
            elif self.FitSeleciton == 'User-defined':
                self.fitting_mode_predef_combo.setEnabled(False)
                self.fitting_mode_predef_button.setEnabled(False)
                self.fitting_mode_usrdef_button.setEnabled(True)
                self.fitting_mode_usrdef_button.clicked.connect(self.showFittingPopup)
            else:
                self.FitSeleciton = self.FitSeleciton
                self.fitting_mode_predef_combo.setEnabled(False)
                self.fitting_mode_predef_button.setEnabled(False)
                self.fitting_mode_usrdef_button.setEnabled(False)



        # self.keithley_2182A_NV=rm.open_resource(self.current_connection, timeout=10000)

    # def enable_thread(self):
    #     if self.isConnect == True:
    #         self.keep_reading = True
    #         while self.keep_reading:

    def process_data(self):
        #  ---------------------------- PART 5&6 --------------------------------
        self.data_processing_layout = QHBoxLayout()
        self.log_group_box = QGroupBox("Experimental Log")
        self.Fitting_mode_group_box = QGroupBox("Graph")
        #  ---------------------------- PART 3 --------------------------------
        self.textedit_layout = QVBoxLayout()
        self.date_layout = QHBoxLayout()
        self.textedit_layout.addWidget(self.date_layout)
        self.smaple_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.smaple_layout)
        self.Measurement_Type_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.Measurement_Type_layout)
        self.incidence_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.incidence_layout)
        self.power_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.power_layout)
        self.start_angle_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.start_angle_layout)
        self.end_angle_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.end_angle_layout)
        self.step_angle_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.step_angle_layout)
        self.polarization_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.polarization_layout)
        self.exposure_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.exposure_layout)
        self.EMGain_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.EMGain_layout)
        self.Acumulation_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.Acumulation_layout)
        self.start_temperature_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.start_temperature_layout)
        self.end_temperature_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.end_temperature_layout)
        self.step_temperature_layout = QHBoxLayout()
        self.textedit_layout.addLayout(self.step_temperature_layout)

        # self.textEdit = QLineEdit(self)
        # self.textEdit.setReadOnly(True)
        # self.textedit_layout.addWidget(self.textEdit)
        self.log_group_box.setLayout(self.textedit_layout)
        self.data_processing_layout.addWidget(self.log_group_box)

        Parameter = pd.read_csv(self.folder + "Experimental_Parameters.txt", header=None, sep=':', engine='c')

        Date = Parameter.iat[0, 1]
        step_size = Parameter.iat[7, 1]
        step_size = int(step_size)
        file_name = str(Parameter.iat[1, 1]).replace(" ", "")



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
        self.Fitting_mode_group_box.setLayout(figure_Layout)
        self.data_processing_layout.addWidget(self.Fitting_mode_group_box)

        self.main_layout.addLayout(self.data_processing_layout)
        self.setLayout(self.main_layout)


    def rstpage(self):
        self.clearLayout(self.layout)
        self.init_ui()

    def showFittingPopup(self):
        self.popup = UserDefineFittingWindow()
        self.popup.exec()


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

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                elif item.layout() is not None:
                    self.clearLayout(item.layout())

