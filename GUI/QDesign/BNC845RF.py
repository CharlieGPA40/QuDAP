from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QRadioButton, QGroupBox, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QPushButton, QComboBox, QLineEdit)
from PyQt6.QtGui import QIcon, QFont, QIntValidator, QValidator, QDoubleValidator
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
import sys
import pyvisa as visa
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import random

class IntegerValidator(QIntValidator):
    def __init__(self, minimum, maximum):
        super().__init__(minimum, maximum)
        self.minimum = minimum
        self.maximum = maximum
    def validate(self, input, pos):
        if input == "":
            return (QValidator.State.Intermediate, input, pos)
        state, value, pos = super().validate(input, pos)
        try:
            if self.minimum <= int(input) <= self.maximum:
                return (QValidator.State.Acceptable, input, pos)
            else:
                return (QValidator.State.Invalid, input, pos)
        except ValueError:
            return (QValidator.State.Invalid, input, pos)

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=300):
        fig = Figure(figsize=(width, height), dpi=dpi)

        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class BNC845RF(QWidget):

    def __init__(self):
        super().__init__()
        self.isConnect = False
        self.isPlotting = False
        self.init_ui()

    def init_ui(self):
        titlefont = QFont("Arial", 20)
        font = QFont("Arial", 13)
        self.setStyleSheet("background-color: white;")

        # Create main vertical layout with centered alignment
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #  ---------------------------- PART 1 --------------------------------
        self.current_intrument_label = QLabel("Berkeley Nucleonics Microwave and RF Signal Generator 845")
        self.current_intrument_label.setFont(titlefont)
        self.current_intrument_label.setStyleSheet("""
                                            QLabel{
                                                background-color: white;
                                                }
                                                """)

        #  ---------------------------- PART 2 --------------------------------
        # GPIB ComboBox
        self.gpib_combo = QComboBox()
        self.gpib_combo.setStyleSheet("""
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
        self.gpib_combo.setFont(font)

        self.current_gpib_label = QLabel("Current GPIB Connection: None")
        self.current_gpib_label.setFont(font)
        self.current_gpib_label.setStyleSheet("""
                                          QLabel{
                                              background-color: #F8F8F8;
                                              }
                                              """)

        # Refresh Button
        refresh_btn = QPushButton(icon=QIcon("Icon/refresh.svg"))

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
        dc_current_group_box = QGroupBox("DC Current")  # Container widget for the horizontal layout
        dc_current_main_layout = QVBoxLayout()
        # voltage_reading_widget.setStyleSheet("QWidget { border: 2px solid black; }")
        DC_setup_layout = QHBoxLayout()
        self.DCSource_label = QLabel("DC Source:")
        self.DCSource_label.setFont(font)

        self.dc_source_entry_box = QLineEdit()
        # self.cur_field_entry_box.setValidator(IntegerValidator(-10000, 10000))
        self.current_validator = QDoubleValidator(-105, 105, 3)
        self.current_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.dc_source_entry_box.setValidator(self.current_validator)
        self.dc_source_entry_box.setPlaceholderText("±0.1pA to ±105mA")
        self.dc_source_entry_box.setFixedHeight(30)
        self.DCUnitSource_combo = QComboBox()
        self.DCUnitSource_combo.setFont(font)
        self.DCUnitSource_combo.setStyleSheet("""
                            QComboBox {
                                padding: 4px;
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
                                width: 38px;   /* Width of the arrow button */
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
        self.setStyleSheet("""
                                                    QLabel{
                                                        background-color: #F8F8F8;
                                                        }
                                                        """)
        self.DCUnitSource_combo.addItems(["Select Units"])    # 0
        self.DCUnitSource_combo.addItems(["mA"])  # 1
        self.DCUnitSource_combo.addItems(["µA"])  # 2
        self.DCUnitSource_combo.addItems(["nA"])  # 3
        self.DCUnitSource_combo.addItems(["pA"])  # 3

        self.DC_Range_checkbox = QCheckBox("Auto Range")
        self.DC_Range_checkbox.setFont(font)
        self.DC_Range_checkbox.setChecked(True)
        # self.DC_Range_checkbox.clicked.connect()
        self.DC_Range_checkbox.setStyleSheet("""
                                                QCheckBox{
                                                    background-color: #F8F8F8;
                                                    }
                                                            """)

        self.send_btn = QPushButton('Send')
        # self.send_btn.clicked.connect(self.plot_selection)


        DC_setup_layout.addWidget(self.DCSource_label, 1)
        DC_setup_layout.addWidget(self.dc_source_entry_box, 3)
        DC_setup_layout.addWidget(self.DCUnitSource_combo,1)
        DC_setup_layout.addStretch(1)
        DC_setup_layout.addWidget(self.DC_Range_checkbox,1)
        DC_setup_layout.addStretch(1)
        DC_setup_layout.addWidget(self.send_btn, 1)

        dc_current_main_layout.addLayout(DC_setup_layout)

        dc_current_group_box.setLayout(dc_current_main_layout)

        #  ---------------------------- PART 4 --------------------------------
        self.wave_func_label = QLabel("Wave Function:")
        self.wave_func_label.setFont(font)
        wave_group_box = QGroupBox("Wave Functions")  # Container widget for the horizontal layout
        wave_main_layout = QVBoxLayout()
        # voltage_reading_widget.setStyleSheet("QWidget { border: 2px solid black; }")
        Wave_AMP_setup_layout = QHBoxLayout()
        self.waveform_combo = QComboBox()
        self.waveform_combo.setFont(font)
        self.waveform_combo.setStyleSheet("""
                                            QComboBox {
                                                padding: 4px;
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
                                                width: 38px;   /* Width of the arrow button */
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
        self.setStyleSheet("""
                                                                    QLabel{
                                                                        background-color: #F8F8F8;
                                                                        }
                                                                        """)
        self.waveform_combo.addItems(["Select Funcs"])  # 0
        self.waveform_combo.addItems(["SINE"])  # 1
        self.waveform_combo.addItems(["SQUARE"])  # 2
        self.waveform_combo.addItems(["RAMP"])  # 3
        self.waveform_combo.addItems(["ARB(x)"])  # 3

        self.AC_Amplitude_label = QLabel("Amplitude:")
        self.AC_Amplitude_label.setFont(font)
        self.AC_Amplitude_entry_box = QLineEdit()
        # self.cur_field_entry_box.setValidator(IntegerValidator(-10000, 10000))
        self.AC_Amplitude_validator = QDoubleValidator(0, 105, 10)
        self.AC_Amplitude_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.AC_Amplitude_entry_box.setValidator(self.AC_Amplitude_validator)
        self.AC_Amplitude_entry_box.setPlaceholderText("1pA to 105mA")
        self.AC_Amplitude_entry_box.setFixedHeight(30)
        self.WaveAmpUnitSource_combo = QComboBox()
        self.WaveAmpUnitSource_combo.setFont(font)
        self.WaveAmpUnitSource_combo.setStyleSheet("""
                                    QComboBox {
                                        padding: 4px;
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
                                        width: 38px;   /* Width of the arrow button */
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
        self.setStyleSheet("""
                                                            QLabel{
                                                                background-color: #F8F8F8;
                                                                }
                                                                """)

        self.WaveAmpUnitSource_combo.addItems(["Select Units"])  # 0
        self.WaveAmpUnitSource_combo.addItems(["mA"])  # 1
        self.WaveAmpUnitSource_combo.addItems(["µA"])  # 2
        self.WaveAmpUnitSource_combo.addItems(["nA"])  # 3
        self.WaveAmpUnitSource_combo.addItems(["pA"])  # 3

        Wave_AMP_setup_layout.addWidget(self.wave_func_label,1)
        Wave_AMP_setup_layout.addWidget(self.waveform_combo, 1)
        Wave_AMP_setup_layout.addStretch(1)
        Wave_AMP_setup_layout.addWidget(self.AC_Amplitude_label, 1)
        Wave_AMP_setup_layout.addWidget(self.AC_Amplitude_entry_box, 3)
        Wave_AMP_setup_layout.addWidget(self.WaveAmpUnitSource_combo, 1)

        Wave_Freq_Offset_setup_layout = QHBoxLayout()
        self.AC_Frequency_label = QLabel("Frequency:")
        self.AC_Frequency_label.setFont(font)
        self.AC_Frequency_entry_box = QLineEdit()
        # self.cur_field_entry_box.setValidator(IntegerValidator(-10000, 10000))
        self.AC_Frequency_validator = QDoubleValidator(0.001, 100000, 3)
        self.AC_Frequency_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.AC_Frequency_entry_box.setValidator(self.AC_Frequency_validator)
        self.AC_Frequency_entry_box.setPlaceholderText("1mHz to 100KHz")
        self.AC_Frequency_entry_box.setFixedHeight(30)
        self.AC_Frequency_Unit_label = QLabel("Hz")
        self.AC_Frequency_Unit_label.setFont(font)

        self.AC_Offset_label = QLabel("Offset:")
        self.AC_Offset_label.setFont(font)
        self.AC_Offset_entry_box = QLineEdit()
        # self.cur_field_entry_box.setValidator(IntegerValidator(-10000, 10000))
        self.AC_Offset_validator = QDoubleValidator(-105, 105, 10)
        self.AC_Offset_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.AC_Offset_entry_box.setValidator(self.AC_Offset_validator)
        self.AC_Offset_entry_box.setPlaceholderText("0 to ±105mA")
        self.AC_Offset_entry_box.setFixedHeight(30)
        self.WaveOffsetUnitSource_combo = QComboBox()
        self.WaveOffsetUnitSource_combo.setFont(font)
        self.WaveOffsetUnitSource_combo.setStyleSheet("""
                                            QComboBox {
                                                padding: 4px;
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
                                                width: 38px;   /* Width of the arrow button */
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
        self.setStyleSheet("""
                                                                    QLabel{
                                                                        background-color: #F8F8F8;
                                                                        }
                                                                        """)

        self.WaveOffsetUnitSource_combo.addItems(["Select Units"])  # 0
        self.WaveOffsetUnitSource_combo.addItems(["mA"])  # 1
        self.WaveOffsetUnitSource_combo.addItems(["µA"])  # 2
        self.WaveOffsetUnitSource_combo.addItems(["nA"])  # 3
        self.WaveOffsetUnitSource_combo.addItems(["pA"])  # 3

        self.Wave_Range_checkbox = QCheckBox("Best Range")
        self.Wave_Range_checkbox.setFont(font)
        self.Wave_Range_checkbox.setChecked(True)
        self.Wave_Range_checkbox.setStyleSheet("""
                                                        QCheckBox{
                                                            background-color: #F8F8F8;
                                                            }
                                                                    """)

        Wave_Freq_Offset_setup_layout.addWidget(self.AC_Frequency_label)
        Wave_Freq_Offset_setup_layout.addWidget(self.AC_Frequency_entry_box)
        Wave_Freq_Offset_setup_layout.addWidget(self.AC_Frequency_Unit_label)
        Wave_Freq_Offset_setup_layout.addStretch(1)
        Wave_Freq_Offset_setup_layout.addWidget(self.AC_Offset_label)
        Wave_Freq_Offset_setup_layout.addWidget(self.AC_Offset_entry_box)
        Wave_Freq_Offset_setup_layout.addWidget(self.WaveOffsetUnitSource_combo)
        Wave_Freq_Offset_setup_layout.addStretch(1)
        Wave_Freq_Offset_setup_layout.addWidget(self.Wave_Range_checkbox)

        Wave_Arm_setup_layout = QHBoxLayout()
        self.arm_btn = QPushButton('Arm')
        # send_btn.clicked.connect(self.plot_selection)
        Wave_Arm_setup_layout.addStretch(20)
        Wave_Arm_setup_layout.addWidget(self.arm_btn,1)

        wave_main_layout.addLayout(Wave_AMP_setup_layout)
        wave_main_layout.addLayout(Wave_Freq_Offset_setup_layout)
        wave_main_layout.addLayout(Wave_Arm_setup_layout)

        wave_group_box.setLayout(wave_main_layout)

        #  ---------------------------- PART 4 --------------------------------

        graphing_layout = QHBoxLayout()
        selection_Layout = QHBoxLayout()
        plotting_control_group_box = QGroupBox("Plotting Selection")

        self.checkbox1 = QCheckBox("Channel 1")
        self.checkbox1.setFont(font)
        self.checkbox2 = QCheckBox("Channel 2")
        self.checkbox1.setFont(font)
        self.checkbox1.setStyleSheet("""
                                        QCheckBox{
                                            background-color: #F8F8F8;
                                            }
                                                    """)
        self.checkbox2.setStyleSheet("""
                                                        QCheckBox{
                                                            background-color: #F8F8F8;
                                                            }
                                                            """)
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
        main_layout.addWidget(dc_current_group_box)
        main_layout.addWidget(wave_group_box)
        self.setLayout(main_layout)

        #  ---------------------------- Style Sheet --------------------------------
        # self.arm_btn.setStyleSheet("""
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

        self.connect_btn.setStyleSheet("""
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
        self.send_btn.setStyleSheet("""
                                   QPushButton {
                                       background-color: #CAC9Cb; /* Green background */
                                       color: black; /* White text */
                                       border-style: solid;
                                       border-color: #CAC9Cb;
                                       border-width: 2px;
                                       border-radius: 10px; /* Rounded corners */
                                       padding: 5px;
                                       min-height: 1px;
                                       min-width: 10px;
                                   }
                                   QPushButton:hover {
                                       background-color: #5F6A6A; /* Slightly darker green */
                                   }
                                   QPushButton:pressed {
                                       background-color: #979A9A; /* Even darker green */
                                   }
                               """)
        self.arm_btn.setStyleSheet("""
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
        refresh_btn.setStyleSheet("""
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


    def refresh_gpib_list(self):
        # Access GPIB ports using PyVISA
        rm = visa.ResourceManager()
        instruments = rm.list_resources()
        self.gpib_ports = [instr for instr in instruments if 'GPIB' in instr]
        self.current_gpib_label.setText(f"Current GPIB Connection: None")
        # Clear existing items and add new ones
        self.gpib_combo.clear()
        self.gpib_combo.addItems(["None"])
        self.gpib_combo.addItems(self.gpib_ports)
        self.gpib_combo.addItems(["GPIB:7"])
        self.gpib_combo.addItems(["GPIB:8"])
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
                    self.isConnect = True
                    self.current_gpib_label.setText(f"{self.current_connection} Connection Success!")
                except visa.errors.VisaIOError:
                    self.isConnect = False
                    self.current_gpib_label.setText(f"Connecting {self.current_connection} fail!")
                # Comment it in real implementation
                self.isConnect = True

        # self.keithley_2182A_NV=rm.open_resource(current_connection, timeout=10000)

    def update_voltage(self):
        if self.isConnect:
            self.current_gpib_label.setText(f"Current GPIB Connection: {self.current_connection}")
            # This is for testing uncommand it to test GUI
            self.Chan_1_voltage = random.randint(0, 1000) / 1000
            self.Chan_2_voltage = random.randint(0, 1000) / 100
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


