from PyQt6.QtWidgets import (
    QMessageBox, QButtonGroup, QWidget, QRadioButton, QGroupBox, QFileDialog, QVBoxLayout, QLabel, QHBoxLayout
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
import matplotlib.patches as patches
import numpy as np
import time
from pptx import Presentation
from pptx.util import Inches, Pt

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

        self.ax = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class General(QWidget):

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.plot_index = 0

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
            self.auto_fitting()

    def auto_fitting(self):
        #  ---------------------------- PART 3&4 --------------------------------
        self.auto_fitting_selection_layout = QHBoxLayout()
        self.Auto_mode_group_box = QGroupBox("Auto Mode *")
        self.Fitting_mode_group_box = QGroupBox("Data Fitting *")
        #  ---------------------------- PART 3 --------------------------------
        self.auto_mode_layout = QVBoxLayout()
        self.auto_mode_yes_radio_buttom = QRadioButton("Auto")
        self.auto_mode_yes_radio_buttom.setFont(self.font)
        self.auto_mode_yes_radio_buttom.setChecked(True)
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
        self.fitting_mode_no_radio_buttom.setChecked(True)

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
                        image: url(GUI/Icon/chevron-down.svg); /* Set your own icon for the arrow */
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
        selectedModeButton = self.buttonGroup.checkedButton()
        if selectedModeButton:
            self.modeSelected = True
            self.auto = str(selectedModeButton.text())
        else:
            self.modeSelected = False
            self.auto = 'None'

    def updateFitSelection(self):
        selectedButton = self.fitting_buttonGroup.checkedButton()
        if selectedButton:
            self.fitSelected = True
            self.FitSeleciton = selectedButton.text()
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
                self.fitting_mode_predef_combo.setEnabled(False)
                self.fitting_mode_predef_button.setEnabled(False)
                self.fitting_mode_usrdef_button.setEnabled(False)
        else:
            self.fitSelected = False

    def process_data(self):
        self.updateModeSelection()
        self.updateFitSelection()
        if self.modeSelected and self.fitSelected:
            #  ---------------------------- PART 5&6 --------------------------------
            self.data_processing_layout = QHBoxLayout()
            self.log_group_box = QGroupBox("Experimental Log")
            self.Fitting_mode_group_box = QGroupBox("Graph")
            #  ---------------------------- PART 3 --------------------------------
            Parameter = pd.read_csv(self.folder + "Experimental_Parameters.txt", header=None, sep=':', engine='c')
            Date = Parameter.iat[0, 1]
            self.date_label = QLabel('Date: ' + str(Date))
            self.date_label.setFont(self.font)
            file_name = Parameter.iat[1, 1]
            self.sample_label = QLabel('Sample: ' + str(file_name))
            self.sample_label.setFont(self.font)
            Measure_Type = Parameter.iat[2, 1]
            self.measure_type_label = QLabel('Measurement Type: ' + str(Measure_Type))
            self.measure_type_label.setFont(self.font)
            Light_angle = Parameter.iat[3, 1]
            self.light_angle_label = QLabel('Incident Angle: ' + str(Light_angle))
            self.light_angle_label.setFont(self.font)
            power = Parameter.iat[4, 1]
            self.power_label = QLabel('Power (mW): ' + str(power))
            self.power_label.setFont(self.font)
            start_angle = Parameter.iat[5, 1]
            self.start_angle_label = QLabel('Start Angle (degree): ' + str(start_angle))
            self.start_angle_label.setFont(self.font)
            end_angle = Parameter.iat[6, 1]
            self.end_angle_label = QLabel('Termination Angle (degree): ' + str(end_angle))
            self.end_angle_label.setFont(self.font)
            step_size = Parameter.iat[7, 1]
            self.step_angle_label = QLabel('Angle Step Size (degree): ' + str(step_size))
            self.step_angle_label.setFont(self.font)
            step_size = int(step_size)
            polarization = Parameter.iat[8, 1]
            self.polarization_label = QLabel('Polarization Configuration: ' + str(polarization))
            self.polarization_label.setFont(self.font)
            exp_time = Parameter.iat[9, 1]
            self.exp_time_label = QLabel('Exposure Time (s): ' + str(exp_time))
            self.exp_time_label.setFont(self.font)
            EMGain = Parameter.iat[10, 1]
            self.EMGain_label = QLabel('EMGain: ' + str(EMGain))
            self.EMGain_label.setFont(self.font)
            Accumulation = Parameter.iat[11, 1]
            self.acc_label = QLabel('Accumulation: ' + str(Accumulation))
            self.acc_label.setFont(self.font)
            Start_temp = Parameter.iat[12, 1]
            self.start_temp_label = QLabel('Initial Temperature (K): ' + str(Start_temp))
            self.start_temp_label.setFont(self.font)
            End_temp = Parameter.iat[13, 1]
            self.end_temp_label = QLabel('Termination Temperature (K): ' + str(End_temp))
            self.end_temp_label.setFont(self.font)
            Step_temp = Parameter.iat[14, 1]
            self.step_temp_label = QLabel('Step Temperature (K): ' + str(Step_temp))
            self.step_temp_label.setFont(self.font)

            # If need to remove the space
            file_name = str(Parameter.iat[1, 1]).replace(" ", "")

            self.log_layout = QVBoxLayout()
            self.log_layout.addWidget(self.date_label)
            self.log_layout.addWidget(self.sample_label)
            self.log_layout.addWidget(self.measure_type_label)
            self.log_layout.addWidget(self.light_angle_label)
            self.log_layout.addWidget(self.power_label)
            self.log_layout.addWidget(self.start_angle_label)
            self.log_layout.addWidget(self.end_angle_label)
            self.log_layout.addWidget(self.step_angle_label)
            self.log_layout.addWidget(self.polarization_label)
            self.log_layout.addWidget(self.exp_time_label)
            self.log_layout.addWidget(self.EMGain_label)
            self.log_layout.addWidget(self.acc_label)
            self.log_layout.addWidget(self.start_temp_label)
            self.log_layout.addWidget(self.end_temp_label)
            self.log_layout.addWidget(self.step_temp_label)

            self.log_group_box.setLayout(self.log_layout)
            self.data_processing_layout.addWidget(self.log_group_box)
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
            degree = 130
            SHG_Raw = np.loadtxt(self.folder + file_name + "_{}deg".format(degree) + ".txt", dtype=int, delimiter=',')

            if self.auto == 'Auto':
                max_sum = -np.inf
                max_region = None
                max_sum_candidate = np.inf
                min_sum = 0
                best_size = None
                min_region_size = 10
                max_region_size = 30
                array = []

                for region_size in range(min_region_size, max_region_size + 1, 10):
                    for i in range(SHG_Raw.shape[0] - region_size + 1):
                        for j in range(SHG_Raw.shape[1] - region_size + 1):
                            region = SHG_Raw[i:i + region_size, j:j + region_size]
                            background_pixel = np.sum(SHG_Raw[450:512, 450:512]) / (512-450) ** 2
                            pixel_region_sum = np.sum(region)
                            pixel_region_sum = pixel_region_sum - background_pixel * (region_size**2)
                            if pixel_region_sum < 0:
                                pixel_region_sum = 0

                            if pixel_region_sum > 0.8 * max_sum:
                                max_sum_candidate = pixel_region_sum
                                if region_size == min_region_size:
                                    max_sum = max_sum_candidate

                                if max_sum_candidate > max_sum:
                                    print(
                                        f'Current row pixel at {i}; current colum pixel at {j}; current size {region_size}')
                                    print(pixel_region_sum)
                                    array.append(pixel_region_sum)
                                    max_sum = pixel_region_sum
                                    best_size = region_size
                                    max_region = (i, j, best_size, min_sum)

                # csv_file_path = 'standardized_intensity_matrix.csv'
                # pd.DataFrame(array).to_csv(csv_file_path, index=False, header=False)

                start_i, start_j, region_size, region_sum = max_region
                center_i = start_i + region_size // 2
                center_j = start_j + region_size // 2

                # self.canvas.figure.clf()
                self.canvas.ax.imshow(SHG_Raw, aspect='auto', vmin=0, vmax=5000)

                # # Plot the heatmap with the square region of maximum intensity highlighted
                # self.canvas.figure.colorbar(label='{} Polarization'.format(polarization))
                self.canvas.ax.scatter(center_i, center_j, s=30, color='tomato',
                               marker='x')
                exposure_time = str(float(Parameter.iat[9, 1]))
                title = str(Parameter.iat[1, 1]) + '' + str(Parameter.iat[2, 1]) + '' + str(Parameter.iat[3, 1]) \
                        + '\n' + str(Parameter.iat[4, 1]) + 'mW Exposure Time ' + exposure_time + 's Averaging ' \
                        + str(int(Parameter.iat[11, 1]))
                self.canvas.ax.set_title(title + ' at {} Degree'.format(degree), pad=10, wrap=True)
                self.canvas.figure.gca().add_patch(patches.Rectangle((start_i, start_j), region_size, region_size,
                                                        edgecolor='white', facecolor='none', linewidth=1))
                self.canvas.figure.savefig(self.folder + "Preview_Figure_at_130_Deg.png")
                self.canvas.draw()
            # #
            # # else:
            # #     return
            # #     fig, ax = matplotlib.pyplot.subplots()
            # #     im = matplotlib.pyplot.imshow(SHG_Raw, vmin=0, vmax=5000)
            # #     polarization = Parameter.iat[8, 1]
            # #     matplotlib.pyplot.colorbar(label='{} Polarization'.format(polarization))
            # #     exposure_time = str(float(Parameter.iat[9, 1]))
            # #     title = str(Parameter.iat[1, 1]) + '' + str(Parameter.iat[2, 1]) + '' + str(Parameter.iat[3, 1]) \
            # #             + '\n' + str(Parameter.iat[4, 1]) + 'mW Exposure Time ' + exposure_time + 's Averaging ' \
            # #             + str(int(Parameter.iat[11, 1]))
            # #     matplotlib.pyplot.title(title + ' at {} Degree'.format(degree), pad=10, wrap=True)
            # #
            # #     def onclick(event):
            # #         if event.dblclick:
            # #             global cur_x, cur_y, click
            # #             cur_x = event.xdata
            # #             cur_y = event.ydata
            # #             click = event.button
            # #             if click == 1:
            # #                 print('Closing')
            # #                 matplotlib.pyplot.close()
            # #
            # #     connection_id = fig.canvas.mpl_connect('button_press_event', onclick)
            # #     matplotlib.pyplot.savefig(self.folder + "Preview_Figure_at_130_Deg.png")
            # #     matplotlib.pyplot.show()
            # #
            deg_file = []
            sig_file = []
            if not self.autoSelection:
                center_x = int(cur_x)
                center_y = int(cur_y)
                region_size = int(input('Enter the box size: '))
                half_region_size = (np.ceil(region_size / 2)).astype(int)
                SHG_Raw = np.loadtxt(self.folder + file_name + "_{}deg".format(degree) + ".txt", dtype=int,
                                     delimiter=',')
                fig, ax = pyplot.subplots()
                region = SHG_Raw[center_x - half_region_size: center_x + half_region_size,
                         center_y - half_region_size: center_y + half_region_size]
                im = ax.imshow(SHG_Raw, vmin=1000, vmax=5000)
                fig.colorbar(im, ax=ax, label='Interactive colorbar')
                ax.scatter(center_x, center_y, s=30, color='tomato', marker='x')
                rect = patches.Rectangle((center_x - half_region_size, center_y - half_region_size),
                                         region_size, region_size, linewidth=1, edgecolor='r', facecolor='none')
                # Add the patch to the Axes
                ax.add_patch(rect)
                pyplot.show()
                angle = 365
            for degree in range(0, 365, step_size):
                deg_file = np.append(deg_file, degree)
                SHG_Raw = np.loadtxt(self.folder + file_name + "_{}deg".format(degree) + ".txt", dtype=int,
                                     delimiter=',')
                if not self.autoSelection:
                    region = SHG_Raw[center_x - half_region_size: center_x + half_region_size,
                             center_y - half_region_size: center_y + half_region_size]
                else:
                    region = SHG_Raw[top_left_col: top_left_col + region_size, top_left_row: top_left_row + region_size]

                small_sum = sum(map(sum, region))
                large_sum = sum(map(sum, SHG_Raw))
                bkg_pixel = (large_sum - small_sum) / (512 ** 2 - region_size ** 2)
                sig = small_sum - bkg_pixel * region_size ** 2
                sig_file = np.append(sig_file, sig)

            sig_file = sig_file.astype(np.float64)
            # sig_file = sig_file.tolist()
            max_lim = max(sig_file)
            min_lim = min(sig_file)
            deg_file = deg_file * np.pi / 180
            deg_file = deg_file.astype(np.float64)
            # deg_file = deg_file.tolist()
            fig, ax = pyplot.subplots(subplot_kw={'projection': 'polar'})
            ax.plot(deg_file, sig_file, color='red')
            ax.set_ylim(bottom=min_lim, top=max_lim)
            # pyplot.autoscale()
            pyplot.show()
            pyplot.plot(deg_file, sig_file, linewidth=5, color='blue')
            pyplot.close()
            csv_file_name = 'Processed_First_Data.csv'
            comb = pd.DataFrame(list(zip(deg_file, sig_file)))
            rec_data = pd.DataFrame()
            rec_data = pd.concat([rec_data, comb], ignore_index=True, axis=1)
            rec_data.to_csv(folder_selected + csv_file_name, mode='a', index=False, encoding='utf-8-sig', header=None)

            slope = (sig_file[-1] - sig_file[0]) / (deg_file[-1] - deg_file[0])
            const = sig_file[-1] - slope * deg_file[-1]
            # const = sig_file[-1] + slope * deg_file[-1]
            sig_file = sig_file - (slope * deg_file + const)
            sig_file = (sig_file / 30) / 380000
            csv_file_name = 'Processed_Data.csv'
            comb = pd.DataFrame(list(zip(deg_file, sig_file)))
            rec_data = pd.DataFrame()
            rec_data = pd.concat([rec_data, comb], ignore_index=True, axis=1)
            rec_data.to_csv(folder_selected + csv_file_name, mode='a', index=False, encoding='utf-8-sig', header=None)

            min_sig = min(sig_file)
            sig_file = sig_file - min_sig
            csv_file_name = 'Processed_Data_Min_Shift.csv'
            comb = pd.DataFrame(list(zip(deg_file, sig_file)))
            rec_data = pd.DataFrame()
            rec_data = pd.concat([rec_data, comb], ignore_index=True, axis=1)
            rec_data.to_csv(folder_selected + csv_file_name, mode='w', index=False, encoding='utf-8-sig', header=None)

            pyplot.plot(deg_file, sig_file, linewidth=5, color='blue')
            pyplot.show()

            max_lim = max(sig_file)
            min_lim = min(sig_file)

            fig, ax = pyplot.subplots(subplot_kw={'projection': 'polar'})
            ax.plot(deg_file, sig_file, color='tomato')
            ax.scatter(deg_file, sig_file, color='tomato')
            ax.set_ylim(bottom=min_lim, top=max_lim)
            pyplot.title(title + '{} Polarization'.format(polarization), pad=10, wrap=True)
            pyplot.tight_layout()
            pyplot.savefig(folder_selected + "Figure_2.png")
            pyplot.show()

            fit = True
            if fit == True:
                def shg_sin(params, x, data=None):
                    A = params['A']
                    a2 = params['a2']
                    B = params['B']
                    x0 = params['x0']
                    model = (A * np.sin(a2 - 3 * (x - x0)) + B * np.sin(a2 + (x - x0))) ** 2
                    if data is None:
                        return model
                    return model - data

                def shg_cos(params, x, data=None):

                    A = params['A']
                    a2 = params['a2']
                    B = params['B']
                    model = A * np.cos(a2 - 3 * x) + B * np.cos(a2 + 3 * x) * 2
                    if data is None:
                        return model
                    return model - data

                # Create a Parameters object
                params = lmfit.Parameters()
                params.add('A', value=-0.1)
                params.add('a2', value=-0.1)
                params.add('B', value=11)
                params.add('x0', value=0.1)
                result_sin = lmfit.minimize(shg_sin, params, args=(deg_file,), kws={'data': sig_file})
                sin_A = result_sin.params['A'].value
                sin_a2 = result_sin.params['a2'].value
                sin_B = result_sin.params['B'].value
                sin_x0 = result_sin.params['x0'].value

                sin_A_err = result_sin.params['A'].stderr
                sin_a2_err = result_sin.params['a2'].stderr
                sin_B_err = result_sin.params['B'].stderr
                sin_x0_err = result_sin.params['x0'].stderr

                fig, ax = pyplot.subplots(subplot_kw={'projection': 'polar'})

                ax.plot(deg_file, result_sin.residual + sig_file, color='#E74C3C', linewidth=2)
                ax.scatter(deg_file, sig_file, color='black', s=4)
                ax.set_ylim(bottom=min_lim * 1.1, top=max_lim * 1.1)
                pyplot.title(title + '{} Polarization'.format(polarization), pad=10, wrap=True)
                pyplot.tight_layout()
                pyplot.savefig(folder_selected + "Fitted_Data.png")
                pyplot.show()

                df = pd.DataFrame()
                df_comb = pd.DataFrame(
                    list(zip([sin_A], [sin_A_err], [sin_a2], [sin_a2_err], [sin_B], [sin_B_err], [sin_x0], [sin_x0_err])))
                df = pd.concat([df, df_comb], ignore_index=True, axis=1)
                df.to_csv(folder_selected + 'Fitted_Data.csv', index=False)

                # df = pd.DataFrame()
                # df_comb = pd.DataFrame(list(zip([sin_A_err], [sin_a2_err], [sin_B_err], [sin_x0_err])))
                # df = pd.concat([df, df_comb], ignore_index=True, axis=1)
                # df.to_csv(folder_selected + 'Fitted_Data.csv', index=False)

            if os.path.exists(folder_selected + 'Results.pptx'):
                prs = Presentation(folder_selected + 'Results.pptx')
                prs.slide_width = Inches(13.33)
                prs.slide_height = Inches(7.5)
            else:
                prs = Presentation()
                prs.slide_width = Inches(13.33)
                prs.slide_height = Inches(7.5)
                prs.save(folder_selected + 'Results.pptx')
                prs = Presentation(folder_selected + 'Results.pptx')
                prs.slide_width = Inches(13.33)
                prs.slide_height = Inches(7.5)

            SHG_Image = folder_selected + 'Figure_1.png'
            SHG_Signal = folder_selected + 'Figure_2.png'
            blank_slide_layout = prs.slide_layouts[6]
            slide = prs.slides.add_slide(blank_slide_layout)
            SHG_Image_img = slide.shapes.add_picture(SHG_Image, Inches(0.32), Inches(1.42), Inches(6.39))
            SHG_Signal_img = slide.shapes.add_picture(SHG_Signal, Inches(6.49), Inches(1.42), Inches(6.39))
            text_frame = slide.shapes.add_textbox(Inches(0.18), Inches(0.2), Inches(6.67), Inches(0.4))
            Data_frame = slide.shapes.add_textbox(Inches(11.19), Inches(0.2), Inches(2.04), Inches(0.4))
            text_frame = text_frame.text_frame
            Data_frame = Data_frame.text_frame
            p = text_frame.paragraphs[0]
            d = Data_frame.paragraphs[0]
            run = p.add_run()
            run.text = str(folder_name_pptx)
            font = run.font
            font.name = 'Calibri'
            font.size = Pt(18)

            run_d = d.add_run()
            run_d.text = str(Date)
            font_d = run_d.font
            font_d.name = 'Calibri'
            font_d.size = Pt(18)
            prs.save(folder_selected + 'Results.pptx')





        else:
            QMessageBox.warning(self, "Please try again!", "Select all the required option")

    def rstpage(self):
        self.clearLayout(self.layout)
        self.init_ui()

    def showFittingPopup(self):
        self.popup = UserDefineFittingWindow()
        self.popup.exec()




    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                elif item.layout() is not None:
                    self.clearLayout(item.layout())

