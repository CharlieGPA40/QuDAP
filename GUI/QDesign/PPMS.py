from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QMessageBox, QGroupBox, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QPushButton, QComboBox, QLineEdit)
from PyQt6.QtGui import QIcon, QFont, QIntValidator, QValidator
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
import sys
import pyvisa as visa
import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import random
# import MultiPyVu as mpv # Uncommented it on the sever computer
import sys
import Data_Processing_Suite.GUI.Icon as Icon

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


class PPMS(QWidget):

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.isConnect = False

    def init_ui(self):
        titlefont = QFont("Arial", 25)
        font = QFont("Arial", 15)
        self.setStyleSheet("background-color: white;")

        # Create main vertical layout with centered alignment
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #  ---------------------------- PART 1 --------------------------------
        self.current_intrument_label = QLabel("Physical Property Measurement System")
        self.current_intrument_label.setFont(titlefont)
        self.current_intrument_label.setStyleSheet("""
                                            QLabel{
                                                background-color: white;
                                                }
                                                """)
        #  ---------------------------- PART 2 --------------------------------
        # This command needs to be uncommented on the server PC
        # self.server()  # Uncommented it on the sever computer
        ppms_connection = QHBoxLayout()
        connection_group_box = QGroupBox("Device Connection")
        # Set the layout for the group box
        self.host_label = QLabel("Host:")
        self.host_label.setFont(font)
        self.host_label.setStyleSheet("""
                                            QLabel{
                                                background-color: #F8F8F8;
                                                }
                                                """)
        self.host_entry_box = QLineEdit("127.0.0.1")

        self.port_label = QLabel("Port:")
        self.port_label.setFont(font)
        self.port_label.setStyleSheet("""
                                                    QLabel{
                                                        background-color: #F8F8F8;
                                                        }
                                                        """)

        self.port_entry_box = QLineEdit("5000")

        self.server_btn = QPushButton('Start Server')
        self.server_btn_clicked = False
        self.server_btn.clicked.connect(self.start_server)

        self.connect_btn = QPushButton('Client Connect')
        self.connect_btn.setEnabled(False)
        self.connect_btn_clicked = False
        self.connect_btn.clicked.connect(self.connect_client)

        ppms_connection.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ppms_connection.addWidget(self.host_label,1)
        ppms_connection.addWidget(self.host_entry_box, 2)
        ppms_connection.addStretch(1)
        # self.refresh_gpib_list()
        ppms_connection.addWidget(self.port_label, 1)
        ppms_connection.addWidget(self.port_entry_box, 2)
        ppms_connection.addStretch(1)
        ppms_connection.addWidget(self.server_btn, 1)
        ppms_connection.addWidget(self.connect_btn, 1)
        # combo_layout.setContentsMargins(50, 0, 50, 0)
        connection_group_box.setLayout(ppms_connection)

        #  ---------------------------- PART 3 --------------------------------
        temperature_reading_group_box = QGroupBox("Temperature (K)")  # Container widget for the horizontal layout
        temperature_main_layout = QVBoxLayout()
        # voltage_reading_widget.setStyleSheet("QWidget { border: 2px solid black; }")
        temp_reading_layout = QHBoxLayout()
        self.cur_temp_Label = QLabel("Current Temperature:")
        self.cur_temp_Label.setFont(font)
        self.cur_temp_reading_Label = QLabel("N/A K")
        self.cur_temp_reading_Label.setFont(font)
        temp_reading_layout.addWidget(self.cur_temp_Label)
        temp_reading_layout.addWidget(self.cur_temp_reading_Label)

        temp_status_layout = QHBoxLayout()
        self.cur_temp_status_Label = QLabel("Status:")
        self.cur_temp_status_Label.setFont(font)
        self.cur_temp_status_reading_Label = QLabel("Unkown")
        self.cur_temp_status_reading_Label.setFont(font)
        temp_status_layout.addWidget(self.cur_temp_status_Label)
        temp_status_layout.addWidget(self.cur_temp_status_reading_Label)
        temperature_main_layout.addLayout(temp_reading_layout)
        temperature_main_layout.addLayout(temp_status_layout)
        temperature_reading_group_box.setLayout(temperature_main_layout)

        #  ---------------------------- PART 4 --------------------------------
        Field_reading_group_box = QGroupBox("Field (Oe)")  # Container widget for the horizontal layout
        Field_main_layout = QVBoxLayout()
        # voltage_reading_widget.setStyleSheet("QWidget { border: 2px solid black; }")
        Field_reading_layout = QHBoxLayout()
        self.cur_field_Label = QLabel("Current Field:")
        self.cur_field_Label.setFont(font)
        self.cur_field_reading_Label = QLabel("N/A Oe")
        self.cur_field_reading_Label.setFont(font)
        Field_reading_layout.addWidget(self.cur_field_Label)
        Field_reading_layout.addWidget(self.cur_field_reading_Label)

        Field_status_layout = QHBoxLayout()
        self.cur_field_status_Label = QLabel("Status:")
        self.cur_field_status_Label.setFont(font)
        self.cur_field_status_reading_Label = QLabel("Unkown")
        self.cur_field_status_reading_Label.setFont(font)
        Field_status_layout.addWidget(self.cur_field_status_Label)
        Field_status_layout.addWidget(self.cur_field_status_reading_Label)
        Field_main_layout.addLayout(Field_reading_layout)
        Field_main_layout.addLayout(Field_status_layout)
        Field_reading_group_box.setLayout(Field_main_layout)

        #  ---------------------------- PART 5 --------------------------------
        Rot_reading_group_box = QGroupBox("Rotator (deg)")  # Container widget for the horizontal layout
        Rot_main_layout = QVBoxLayout()
        # voltage_reading_widget.setStyleSheet("QWidget { border: 2px solid black; }")
        Rot_reading_layout = QHBoxLayout()
        self.cur_Rot_Label = QLabel("Current Degree:")
        self.cur_Rot_Label.setFont(font)
        self.cur_Rot_reading_Label = QLabel("N/A deg")
        self.cur_Rot_reading_Label.setFont(font)
        Rot_reading_layout.addWidget(self.cur_Rot_Label)
        Rot_reading_layout.addWidget(self.cur_Rot_reading_Label)

        Rot_status_layout = QHBoxLayout()
        self.cur_Rot_status_Label = QLabel("Status:")
        self.cur_Rot_status_Label.setFont(font)
        self.cur_Rot_status_reading_Label = QLabel("Unkown")
        self.cur_Rot_status_reading_Label.setFont(font)
        Rot_status_layout.addWidget(self.cur_Rot_status_Label)
        Rot_status_layout.addWidget(self.cur_Rot_status_reading_Label)
        Rot_main_layout.addLayout(Rot_reading_layout)
        Rot_main_layout.addLayout(Rot_status_layout)
        Rot_reading_group_box.setLayout(Rot_main_layout)

        #  ---------------------------- PART 6 --------------------------------
        Chamb_reading_group_box = QGroupBox("Chamber Status")  # Container widget for the horizontal layout
        Chamb_main_layout = QVBoxLayout()
        # voltage_reading_widget.setStyleSheet("QWidget { border: 2px solid black; }")
        self.cur_chamb_status_reading_Label = QLabel("Unknown")
        self.cur_chamb_status_reading_Label.setFont(font)
        Chamb_main_layout.addWidget(self.cur_chamb_status_reading_Label)
        Chamb_reading_group_box.setLayout(Chamb_main_layout)

        #  ---------------------------- PART 7 --------------------------------
        temperature_setting_group_box = QGroupBox("Set Temperature")  # Container widget for the horizontal layout
        temperature_set_main_layout = QVBoxLayout()
        # voltage_reading_widget.setStyleSheet("QWidget { border: 2px solid black; }")
        temp_value_setting_layout = QHBoxLayout()
        self.set_temp_Label = QLabel("Target Temperature:")
        self.set_temp_Label.setFont(font)
        self.cur_temp_entry_box = QLineEdit()
        self.cur_temp_entry_box.setValidator(IntegerValidator(0, 400))
        self.cur_temp_entry_box.setPlaceholderText("Enter an temperature between 0 and 400")
        self.set_temp_unit_Label = QLabel("K")
        self.set_temp_unit_Label.setFont(font)
        temp_value_setting_layout.addWidget(self.set_temp_Label)
        temp_value_setting_layout.addWidget(self.cur_temp_entry_box)
        temp_value_setting_layout.addWidget(self.set_temp_unit_Label)

        temp_rate_setting_layout = QHBoxLayout()
        self.temp_rate_Label = QLabel("Rate:")
        self.temp_rate_Label.setFont(font)
        self.temp_rate_entry_box = QLineEdit()
        self.temp_rate_entry_box.setValidator(IntegerValidator(0, 50))
        self.temp_rate_entry_box.setPlaceholderText("Enter an rate between 1 and 50")
        self.temp_rate_unit_Label = QLabel("K/s")
        self.temp_rate_unit_Label.setFont(font)
        self.temp_rate_combo = QComboBox()
        self.temp_rate_combo.setStyleSheet("""
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
        self.temp_rate_combo.setFont(font)
        self.temp_rate_combo.addItems([""])
        self.temp_rate_combo.addItems(["Fast Settle"])
        self.temp_rate_combo.addItems(["No Overshoot"])
        temp_rate_setting_layout.addWidget(self.temp_rate_Label,1)
        temp_rate_setting_layout.addWidget(self.temp_rate_entry_box, 2)
        temp_rate_setting_layout.addWidget(self.temp_rate_unit_Label, 1)
        temp_rate_setting_layout.addWidget(self.temp_rate_combo, 2)
        set_button_layout = QHBoxLayout()
        self.set_temp_btn = QPushButton("Send")
        self.set_temp_btn.clicked.connect(self.setTemp)
        set_button_layout.addStretch(3)
        set_button_layout.addWidget(self.set_temp_btn)
        temperature_set_main_layout.addLayout(temp_value_setting_layout)
        temperature_set_main_layout.addLayout(temp_rate_setting_layout)
        temperature_set_main_layout.addLayout(set_button_layout)
        temperature_setting_group_box.setLayout(temperature_set_main_layout)

        #  ---------------------------- PART 8 --------------------------------
        Field_setting_group_box = QGroupBox("Set Field")  # Container widget for the horizontal layout
        Field_set_main_layout = QVBoxLayout()
        # voltage_reading_widget.setStyleSheet("QWidget { border: 2px solid black; }")
        field_value_setting_layout = QHBoxLayout()
        self.set_field_Label = QLabel("Target Temperature:")
        self.set_field_Label.setFont(font)
        self.cur_field_entry_box = QLineEdit()
        self.cur_field_entry_box.setValidator(IntegerValidator(-10000, 10000))
        self.cur_field_entry_box.setPlaceholderText("Enter a field between -10000 and 10000")
        self.set_field_unit_Label = QLabel("Oe")
        self.set_field_unit_Label.setFont(font)
        field_value_setting_layout.addWidget(self.set_field_Label)
        field_value_setting_layout.addWidget(self.cur_field_entry_box)
        field_value_setting_layout.addWidget(self.set_field_unit_Label)

        field_rate_setting_layout = QHBoxLayout()
        self.field_rate_Label = QLabel("Rate:")
        self.field_rate_Label.setFont(font)
        self.field_rate_entry_box = QLineEdit()
        self.field_rate_entry_box.setValidator(IntegerValidator(0, 220))
        self.field_rate_entry_box.setPlaceholderText("Enter an rate between 0 and 220")
        self.field_rate_unit_Label = QLabel("Oe/s")
        self.field_rate_unit_Label.setFont(font)
        self.field_rate_combo = QComboBox()
        self.field_rate_combo.setStyleSheet("""
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
        self.field_rate_combo.setFont(font)
        self.field_rate_combo.addItems([""])
        self.field_rate_combo.addItems(["Linear"])
        self.field_rate_combo.addItems(["No Overshoot"])
        self.field_rate_combo.addItems(["Oscillate"])
        field_rate_setting_layout.addWidget(self.field_rate_Label,1)
        field_rate_setting_layout.addWidget(self.field_rate_entry_box,2)
        field_rate_setting_layout.addWidget(self.field_rate_unit_Label,1)
        field_rate_setting_layout.addWidget(self.field_rate_combo, 2)
        field_set_button_layout = QHBoxLayout()
        self.set_field_btn = QPushButton("Send")
        self.set_field_btn.clicked.connect(self.setField)
        field_set_button_layout.addStretch(3)
        field_set_button_layout.addWidget(self.set_field_btn)
        Field_set_main_layout.addLayout(field_value_setting_layout)
        Field_set_main_layout.addLayout(field_rate_setting_layout)
        Field_set_main_layout.addLayout(field_set_button_layout)
        Field_setting_group_box.setLayout(Field_set_main_layout)

        #  ---------------------------- PART 9 --------------------------------
        chamber_setting_group_box = QGroupBox("Set Chamber")  # Container widget for the horizontal layout
        chamber_setting_layout = QHBoxLayout()
        self.chamber_set_Label = QLabel("Set Status:")
        self.chamber_set_Label.setFont(font)
        self.chamber_set_combo = QComboBox()
        self.chamber_set_combo.setStyleSheet("""
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
                                        width: 35px;   /* Width of the arrow button */
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
        self.chamber_set_combo.setFont(font)
        self.chamber_set_combo.addItems([""])
        self.chamber_set_combo.addItems(["Seal"])
        self.chamber_set_combo.addItems(["Purge/Seal"])
        self.chamber_set_combo.addItems(["Vent/Seal"])
        self.chamber_set_combo.addItems(["Pump Continuous"])
        self.chamber_set_combo.addItems(["Vent Continuous"])
        self.chamber_set_combo.addItems(["High Vacuum"])
        chamber_setting_layout.addWidget(self.chamber_set_Label, 1)
        chamber_setting_layout.addWidget(self.chamber_set_combo, 2)
        chamber_setting_layout.setContentsMargins(0,0,450,0)
        chamber_set_button_layout = QHBoxLayout()
        self.set_chamber_btn = QPushButton("Send")
        self.set_chamber_btn.clicked.connect(self.setChamber)
        chamber_set_button_layout.addStretch(3)
        chamber_set_button_layout.addWidget(self.set_chamber_btn)
        chamber_set_main_layout = QVBoxLayout()
        chamber_set_main_layout.addLayout(chamber_setting_layout)
        chamber_set_main_layout.addLayout(chamber_set_button_layout)
        chamber_setting_group_box.setLayout(chamber_set_main_layout)

        #  ---------------------------- Main Layout --------------------------------
        # Add widgets to the main layout with centered alignment
        main_layout.addWidget(self.current_intrument_label, alignment=Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(connection_group_box)
        PPMS_reading_layout = QHBoxLayout()
        PPMS_reading_layout.addWidget(temperature_reading_group_box)
        PPMS_reading_layout.addWidget(Field_reading_group_box)
        main_layout.addLayout(PPMS_reading_layout)
        PPMS_reading_layout_2 = QHBoxLayout()
        PPMS_reading_layout_2.addWidget(Rot_reading_group_box)
        PPMS_reading_layout_2.addWidget(Chamb_reading_group_box)
        main_layout.addLayout(PPMS_reading_layout_2)
        main_layout.addWidget(temperature_setting_group_box)
        main_layout.addWidget(Field_setting_group_box)
        main_layout.addWidget(chamber_setting_group_box)
        self.setLayout(main_layout)

        #  ---------------------------- Style Sheet --------------------------------
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
                                       min-width: 90px;
                                   }
                                   QPushButton:hover {
                                       background-color: #5F6A6A; /* Slightly darker green */
                                   }
                                   QPushButton:pressed {
                                       background-color: #979A9A; /* Even darker green */
                                   }
                               """)
        self.server_btn.setStyleSheet("""
                                   QPushButton {
                                       background-color: #CAC9Cb; /* Green background */
                                       color: black; /* White text */
                                       border-style: solid;
                                       border-color: #CAC9Cb;
                                       border-width: 2px;
                                       border-radius: 10px; /* Rounded corners */
                                       padding: 5px;
                                       min-height: 1px;
                                       min-width: 80px;
                                   }
                                   QPushButton:hover {
                                       background-color: #5F6A6A; /* Slightly darker green */
                                   }
                                   QPushButton:pressed {
                                       background-color: #979A9A; /* Even darker green */
                                   }
                               """)

        self.set_temp_btn.setStyleSheet("""
                                           QPushButton {
                                               background-color: #CAC9Cb; /* Green background */
                                               color: black; /* White text */
                                               border-style: solid;
                                               border-color: #CAC9Cb;
                                               border-width: 2px;
                                               border-radius: 10px; /* Rounded corners */
                                               padding: 5px;
                                               min-height: 1px;
                                               min-width: 80px;
                                           }
                                           QPushButton:hover {
                                               background-color: #5F6A6A; /* Slightly darker green */
                                           }
                                           QPushButton:pressed {
                                               background-color: #979A9A; /* Even darker green */
                                           }
                                       """)

        self.set_field_btn.setStyleSheet("""
                                                   QPushButton {
                                                       background-color: #CAC9Cb; /* Green background */
                                                       color: black; /* White text */
                                                       border-style: solid;
                                                       border-color: #CAC9Cb;
                                                       border-width: 2px;
                                                       border-radius: 10px; /* Rounded corners */
                                                       padding: 5px;
                                                       min-height: 1px;
                                                       min-width: 80px;
                                                   }
                                                   QPushButton:hover {
                                                       background-color: #5F6A6A; /* Slightly darker green */
                                                   }
                                                   QPushButton:pressed {
                                                       background-color: #979A9A; /* Even darker green */
                                                   }
                                               """)

        self.set_chamber_btn.setStyleSheet("""
                                                           QPushButton {
                                                               background-color: #CAC9Cb; /* Green background */
                                                               color: black; /* White text */
                                                               border-style: solid;
                                                               border-color: #CAC9Cb;
                                                               border-width: 2px;
                                                               border-radius: 10px; /* Rounded corners */
                                                               padding: 5px;
                                                               min-height: 1px;
                                                               min-width: 80px;
                                                           }
                                                           QPushButton:hover {
                                                               background-color: #5F6A6A; /* Slightly darker green */
                                                           }
                                                           QPushButton:pressed {
                                                               background-color: #979A9A; /* Even darker green */
                                                           }
                                                       """)

    def start_server(self):
        # self.server()
        if self.server_btn_clicked == False:
            # self.s.open()  # Uncommented it on the sever computer
            self.server_btn.setText('Stop Server')
            self.server_btn_clicked = True
            self.connect_btn.setEnabled(True)
        elif self.server_btn_clicked == True:
            # self.s.close()  # Uncommented it on the sever computer
            self.server_btn.setText('Start Server')
            self.server_btn_clicked = False
            self.connect_btn.setEnabled(False)

    # Uncommented it on the sever computer
    # def server(self, flags: str = ''):
    #     user_flags = []
    #     if flags == '':
    #         user_flags = sys.argv[1:]
    #     else:
    #         msg = 'No flags detected; using hard-coded IP address'
    #         msg += 'for remote access.'
    #         print(msg)
    #
    #         # This value comes from the server PC's self-identified IPV4
    #         # address and needs to be manually input
    #         self.host = self.host_entry_box.displayText()
    #         user_flags = [f'-ip={self.host}']
    #
    #     # Opens the server connection
    #     self.s = mpv.Server(user_flags, keep_server_open=True)

    def connect_client(self):
        self.reading_timer = QTimer()
        if self.connect_btn_clicked == False:
            self.connect_btn.setText('Stop Client')
            self.connect_btn_clicked = True
            self.server_btn.setEnabled(False)
            # Uncommented it on the client computer
            # with mpv.Client(self.host, self.port) as self.client:
            #     self.reading_timer = QTimer()
            #     self.reading_timer.setInterval(1000)
            #     self.reading_timer.timeout.connect(self.ppms_reading)
            #     self.reading_timer.start()

            """
            THis is only for test purpose
            """

            self.reading_timer.setInterval(1000)
            self.reading_timer.timeout.connect(self.ppms_reading)
            self.reading_timer.start()


        elif self.connect_btn_clicked == True:
            self.connect_btn.setText('Start Client')
            self.connect_btn_clicked = False
            self.server_btn.setEnabled(True)
            self.reading_timer.stop()
            self.cur_temp_reading_Label.setText('N/A K')
            self.cur_temp_status_reading_Label.setText('Unknown')
        self.host = self.host_entry_box.displayText()
        self.port = self.port_entry_box.displayText()


    def ppms_reading(self):
        # Uncomment this section to enable ppms control
        # T, sT = self.client.get_temperature()
        # F, sF = self.client.get_field()
        R, sR = "N/A", "Unknown"
        # C = self.client.get_chamber()
        # self.cur_temp_reading_Label.setText(f'{T} K')
        # self.cur_temp_status_reading_Label.setText(f'{sT}')
        # self.cur_field_reading_Label.setText(f'{F} Oe')
        # self.cur_field_status_reading_Label.setText(f'{sF}')
        # self.cur_chamb_status_reading_Label.setText(f'{C}')

        """
        This is only for test purpose
        """
        T, F = random.randint(2, 400), random.randint(-10000, 10000)
        sF, sT, C = "Testing!","Testing!","Testing!"
        self.cur_temp_reading_Label.setText(f'{T} K')
        self.cur_temp_status_reading_Label.setText(f'{sT}')
        self.cur_field_reading_Label.setText(f'{F} Oe')
        self.cur_field_status_reading_Label.setText(f'{sF}')
        self.cur_Rot_reading_Label.setText(f'{R} degs')
        self.cur_Rot_status_reading_Label.setText(f'{sR}')
        self.cur_chamb_status_reading_Label.setText(f'{C}')

    def setTemp(self):
        self.set_temp = self.cur_temp_entry_box.displayText()
        self.set_temp_rate = self.temp_rate_entry_box.displayText()
        self.temp_rate_method = self.temp_rate_combo.currentIndex()

        if self.set_temp != '' and self.set_temp_rate != '' and self.temp_rate_method != 0:
            self.set_temp_rate = float(self.set_temp_rate)
            self.set_temp = float(self.set_temp)
            print(self.set_temp, self.set_temp_rate, self.temp_rate_method)
            if self.temp_rate_method == 1:
                self.client.set_temperature(self.set_temp,
                                       self.set_temp_rate,
                                       self.client.temperature.approach_mode.fast_settle)
            elif self.temp_rate_method == 2:
                self.client.set_temperature(self.set_temp,
                                            self.set_temp_rate,
                                            self.client.temperature.approach_mode.no_overshoot)

        else:
            QMessageBox.warning(self, "Input Missing", "Please enter all the required information")


    def setField(self):
        self.set_Field = self.cur_field_entry_box.displayText()
        self.set_field_rate = self.field_rate_entry_box.displayText()
        self.field_rate_method = self.field_rate_combo.currentIndex()
        if self.set_Field != '' and self.set_field_rate != '' and self.field_rate_method != 0:
            self.set_Field = int(self.set_Field)
            self.set_field_rate = int(self.set_field_rate)
            print(self.set_Field, self.set_field_rate, self.field_rate_method)
            if self.temp_rate_method == 1:
                self.client.set_field(self.set_Field,
                                            self.set_field_rate,
                                            self.client.field.approach_mode.linear)
            if self.temp_rate_method == 2:
                self.client.set_field(self.set_Field,
                                       self.set_field_rate,
                                       self.client.field.approach_mode.fast_settle)
            elif self.temp_rate_method == 3:
                self.client.set_field(self.set_Field,
                                            self.set_temp_rate,
                                            self.client.tempfielderature.approach_mode.no_overshoot)
        else:
            QMessageBox.warning(self, "Input Missing", "Please enter all the required information")

    def setChamber(self):
        self.set_Chamber = self.chamber_set_combo.currentIndex()
        if self.set_Chamber != 0:
            print(self.set_Chamber)
            if self.set_Chamber == 1:
                self.client.set_chamber(self.client.chamber.mode.seal)
            elif self.set_Chamber == 2:
                self.client.set_chamber(self.client.chamber.mode.seal)
            elif self.set_Chamber == 2:
                self.client.set_chamber(self.client.chamber.mode.seal)
            elif self.set_Chamber == 2:
                self.client.set_chamber(self.client.chamber.mode.seal)
            elif self.set_Chamber == 2:
                self.client.set_chamber(self.client.chamber.mode.seal)
            elif self.set_Chamber == 2:
                self.client.set_chamber(self.client.chamber.mode.seal)

        else:
            QMessageBox.warning(self, "Input Missing", "Please enter all the required information")

