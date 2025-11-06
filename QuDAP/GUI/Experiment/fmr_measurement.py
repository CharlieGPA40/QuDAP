from PyQt6.QtWidgets import (
    QSizePolicy, QWidget, QMessageBox, QGroupBox, QFileDialog, QVBoxLayout, QLabel, QHBoxLayout,
    QCheckBox, QTextEdit, QPushButton, QComboBox, QLineEdit, QScrollArea, QDialog, QRadioButton, QMainWindow,
    QDialogButtonBox, QProgressBar, QButtonGroup, QApplication, QCompleter, QToolButton
)
from PyQt6.QtGui import QIcon, QFont, QDoubleValidator, QIcon
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread, QSettings, QSize
from PyQt6.QtGui import QKeyEvent
import traceback
import random
import matplotlib
import datetime
import time
import numpy as np
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

try:
    # from GUI.Experiment.BNC845RF import COMMAND
    from QuDAP.instrument.BNC845 import BNC_845M_COMMAND
    from QuDAP.instrument.rigol_spectrum_analyzer import RIGOL_COMMAND

except ImportError:
    # from QuDAP.GUI.Experiment.BNC845RF import COMMAND
    from instrument.BNC845 import BNC_845M_COMMAND
    from instrument.BK_precision_9129B import BK_9129_COMMAND
    # from GUI.Experiment.rigol_experiment import RIGOL_Measurement

class FMR_Measurement(QWidget):
    def __init__(self, ppms_client = None, bnc845 = None, dsp7265 = None):
        super().__init__()
        try:
            with open("GUI/QSS/QButtonWidget.qss", "r") as file:
                self.Button_stylesheet = file.read()
            with open("GUI/QSS/QComboWidget.qss", "r") as file:
                self.QCombo_stylesheet = file.read()
            self.font = QFont("Arial", 13)
            self.CLIENT = ppms_client
            self.BNC = bnc845
            self.DSP7265 = dsp7265
            self.worker = None
            self.init_ui()
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
            return

    def init_ui(self):
        self.bnc845rf_main_layout = QHBoxLayout()

        self.bnc845rf_reading_groupbox = QGroupBox("BNC 845RF Reading")
        self.bnc845rf_reading_groupbox.setLayout(self.bnc845rf_window_reading_ui())
        self.bnc845rf_reading_groupbox.setFixedWidth(560)

        self.bnc845rf_setting_groupbox = QGroupBox("BNC 845RF Setting")
        self.bnc845rf_setting_groupbox.setLayout(self.bnc845rf_window_setting_ui())
        self.bnc845rf_setting_groupbox.setFixedWidth(560)

        self.bnc845rf_main_layout.addWidget(self.bnc845rf_reading_groupbox)
        self.bnc845rf_main_layout.addWidget(self.bnc845rf_setting_groupbox)
        return self.bnc845rf_main_layout
        # self.Instruments_measurement_setup_layout.addLayout(self.bnc845rf_main_layout)

    def bnc845rf_window_reading_ui(self):
        self.bnc845rf_window_reading_layout = QVBoxLayout()

        self.bnc845rf_current_frequency_layout = QHBoxLayout()
        bnc845rf_current_frequency_label = QLabel('Current Frequency:')
        bnc845rf_current_frequency_label.setFont(self.font)
        self.bnc845rf_current_frequency_reading_label = QLabel('N/A')
        self.bnc845rf_current_frequency_reading_label.setFont(self.font)
        self.bnc845rf_current_frequency_layout.addWidget(bnc845rf_current_frequency_label)
        self.bnc845rf_current_frequency_layout.addWidget(self.bnc845rf_current_frequency_reading_label)

        self.bnc845rf_current_power_layout = QHBoxLayout()
        bnc845rf_current_power_label = QLabel('Current Power:')
        bnc845rf_current_power_label.setFont(self.font)
        self.bnc845rf_current_power_reading_label = QLabel('N/A:')
        self.bnc845rf_current_power_reading_label.setFont(self.font)
        self.bnc845rf_current_power_layout.addWidget(bnc845rf_current_power_label)
        self.bnc845rf_current_power_layout.addWidget(self.bnc845rf_current_power_reading_label)

        self.bnc845rf_modulation_layout = QHBoxLayout()
        bnc845rf_modulation_label = QLabel('Modulation Type:')
        bnc845rf_modulation_label.setFont(self.font)
        self.bnc845rf_modulation_reading_label = QLabel('N/A')
        self.bnc845rf_modulation_reading_label.setFont(self.font)
        self.bnc845rf_modulation_layout.addWidget(bnc845rf_modulation_label)
        self.bnc845rf_modulation_layout.addWidget(self.bnc845rf_modulation_reading_label)

        self.bnc845rf_modulation_depth_reading_layout = QHBoxLayout()
        bnc845rf_modulation_depth_label = QLabel('Modulation Depth:')
        bnc845rf_modulation_depth_label.setFont(self.font)
        self.bnc845rf_modulation_depth_reading_label = QLabel('N/A')
        self.bnc845rf_modulation_depth_reading_label.setFont(self.font)
        self.bnc845rf_modulation_depth_reading_layout.addWidget(bnc845rf_modulation_depth_label)
        self.bnc845rf_modulation_depth_reading_layout.addWidget(self.bnc845rf_modulation_depth_reading_label)

        self.bnc845rf_modulation_frequency_reading_layout = QHBoxLayout()
        bnc845rf_modulation_frequency_label = QLabel('Modulation Frequency:')
        bnc845rf_modulation_frequency_label.setFont(self.font)
        self.bnc845rf_modulation_frequency_reading_label = QLabel('N/A')
        self.bnc845rf_modulation_frequency_reading_label.setFont(self.font)
        self.bnc845rf_modulation_frequency_reading_layout.addWidget(bnc845rf_modulation_frequency_label)
        self.bnc845rf_modulation_frequency_reading_layout.addWidget(self.bnc845rf_modulation_frequency_reading_label)

        self.bnc845rf_modulation_state_layout = QHBoxLayout()
        bnc845rf_modulation_state_label = QLabel('Modulation State:')
        bnc845rf_modulation_state_label.setFont(self.font)
        self.bnc845rf_modulation_state_reading_label = QLabel('N/A')
        self.bnc845rf_modulation_state_reading_label.setFont(self.font)
        self.bnc845rf_modulation_state_layout.addWidget(bnc845rf_modulation_state_label)
        self.bnc845rf_modulation_state_layout.addWidget(self.bnc845rf_modulation_state_reading_label)

        self.bnc845rf_state_layout = QHBoxLayout()
        bnc845rf_state_label = QLabel('RF State:')
        bnc845rf_state_label.setFont(self.font)
        self.bnc845rf_state_reading_label = QLabel('N/A')
        self.bnc845rf_state_reading_label.setFont(self.font)
        self.bnc845rf_state_layout.addWidget(bnc845rf_state_label)
        self.bnc845rf_state_layout.addWidget(self.bnc845rf_state_reading_label)

        self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_current_frequency_layout)
        self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_current_power_layout)
        self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_modulation_layout)
        # self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_modulation_depth_reading_layout)
        # self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_modulation_frequency_reading_layout)
        self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_modulation_state_layout)
        self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_state_layout)

        return self.bnc845rf_window_reading_layout

    def bnc845rf_window_setting_ui(self):
        self.bnc845rf_setting_layout = QVBoxLayout()

        self.bnc845rf_loop_setting_content_layout = QVBoxLayout()
        self.bnc845rf_loop_setting_layout = QHBoxLayout()
        bnc845rf_loop_setting_label = QLabel('Select the Experiment Loop:')
        bnc845rf_loop_setting_label.setFont(self.font)
        self.bnc845rf_loop_setting_combo = QComboBox()
        self.bnc845rf_loop_setting_combo.setFont(self.font)
        self.bnc845rf_loop_setting_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_loop_setting_combo.addItems(
            ["Select Loop", "Frequency Dependent", "Power Dependent", "Frequency and Power Dependent"])
        self.bnc845rf_loop_setting_combo.currentIndexChanged.connect(self.bnc845rf_loop_selection_ui)
        self.bnc845rf_loop_setting_layout.addWidget(bnc845rf_loop_setting_label)
        self.bnc845rf_loop_setting_layout.addWidget(self.bnc845rf_loop_setting_combo)

        self.bnc845rf_setting_layout.addLayout(self.bnc845rf_loop_setting_layout)
        self.bnc845rf_setting_layout.addLayout(self.bnc845rf_loop_setting_content_layout)
        self.bnc845rf_setting_layout.addLayout(self.bnc845rf_modulation_ui())

        return self.bnc845rf_setting_layout

    def bnc845rf_modulation_ui(self):
        self.bnc845rf_modulation_layout =QVBoxLayout()

        self.bnc845rf_modulation_select_layout = QHBoxLayout()
        self.bnc845rf_modulation_label = QLabel('Modulation: ')
        self.bnc845rf_modulation_label.setFont(self.font)
        self.bnc845rf_modulation_combo = QComboBox()
        self.bnc845rf_modulation_combo.setFont(self.font)
        self.bnc845rf_modulation_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_modulation_combo.addItems(
            ["Select Modulation", "Pulse Mod", "Amplitude Mod", "Frequency Mod", "Phase Mod"])
        self.bnc845rf_modulation_combo.currentIndexChanged.connect(self.bnc845rf_modulation_selection_ui)

        self.bnc845rf_modulation_select_layout.addWidget(self.bnc845rf_modulation_label)
        self.bnc845rf_modulation_select_layout.addWidget(self.bnc845rf_modulation_combo)

        self.bnc845rf_modulation_selected_layout = QVBoxLayout()

        self.bnc845rf_modulation_layout.addLayout(self.bnc845rf_modulation_select_layout)
        self.bnc845rf_modulation_layout.addLayout(self.bnc845rf_modulation_selected_layout)
        return self.bnc845rf_modulation_layout

    def bnc845rf_loop_selection_ui(self):
        self.clear_layout(self.bnc845rf_loop_setting_content_layout)
        if self.bnc845rf_loop_setting_combo.currentIndex() == 1:
            self.bnc845rf_frequency_radio_buttom_layout = QHBoxLayout()
            self.bnc845rf_frequency_zone_layout = QVBoxLayout()

            self.bnc845rf_frequency_zone_1 = False
            self.bnc845rf_frequency_zone_2 = False
            self.bnc845rf_frequency_zone_3 = False
            self.bnc845rf_frequency_zone_customized = False

            self.bnc845rf_frequency_zone_number_label = QLabel('Number of Independent Frequency Regions:')
            self.bnc845rf_frequency_zone_number_label.setFont(self.font)
            self.bnc845rf_frequency_zone_one_radio_button = QRadioButton("1")
            self.bnc845rf_frequency_zone_one_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_one_radio_button.toggled.connect(self.select_frequency_zone)
            self.bnc845rf_frequency_zone_two_radio_button = QRadioButton("2")
            self.bnc845rf_frequency_zone_two_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_two_radio_button.toggled.connect(self.select_frequency_zone)
            self.bnc845rf_frequency_zone_three_radio_button = QRadioButton("3")
            self.bnc845rf_frequency_zone_three_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_three_radio_button.toggled.connect(self.select_frequency_zone)
            self.bnc845rf_frequency_zone_customized_radio_button = QRadioButton("Customize")
            self.bnc845rf_frequency_zone_customized_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_customized_radio_button.toggled.connect(self.select_frequency_zone)

            self.bnc845rf_frequency_zone_radio_button_group = QButtonGroup()
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_one_radio_button)
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_two_radio_button)
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_three_radio_button)
            self.bnc845rf_frequency_zone_radio_button_group.addButton(
                self.bnc845rf_frequency_zone_customized_radio_button)

            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_one_radio_button)
            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_two_radio_button)
            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_three_radio_button)
            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_customized_radio_button)
            self.bnc845rf_power_setting_layout = QHBoxLayout()
            bnc845rf_power_setting_label = QLabel('Power:')
            bnc845rf_power_setting_label.setFont(self.font)
            self.bnc845rf_power_setting_entry = QLineEdit()
            self.bnc845rf_power_setting_entry.setFont(self.font)
            bnc845rf_power_setting_unit_label = QLabel('dbm')
            bnc845rf_power_setting_unit_label.setFont(self.font)
            self.bnc845rf_power_setting_layout.addWidget(bnc845rf_power_setting_label)
            self.bnc845rf_power_setting_layout.addWidget(self.bnc845rf_power_setting_entry)
            self.bnc845rf_power_setting_layout.addWidget(bnc845rf_power_setting_unit_label)

            self.bnc845rf_loop_setting_content_layout.addWidget(self.bnc845rf_frequency_zone_number_label)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_frequency_radio_buttom_layout)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_frequency_zone_layout)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_power_setting_layout)
        elif self.bnc845rf_loop_setting_combo.currentIndex() == 2:
            self.bnc845rf_power_radio_buttom_layout = QHBoxLayout()
            self.bnc845rf_power_zone_layout = QVBoxLayout()

            self.bnc845rf_power_zone_1 = False
            self.bnc845rf_power_zone_customized = False

            self.bnc845rf_power_zone_number_label = QLabel('Number of Independent Power Regions:')
            self.bnc845rf_power_zone_number_label.setFont(self.font)
            self.bnc845rf_power_zone_one_radio_button = QRadioButton("1")
            self.bnc845rf_power_zone_one_radio_button.setFont(self.font)
            self.bnc845rf_power_zone_one_radio_button.toggled.connect(self.select_power_zone)
            self.bnc845rf_power_zone_customized_radio_button = QRadioButton("Customize")
            self.bnc845rf_power_zone_customized_radio_button.setFont(self.font)
            self.bnc845rf_power_zone_customized_radio_button.toggled.connect(self.select_power_zone)

            self.bnc845rf_power_radio_buttom_layout.addWidget(self.bnc845rf_power_zone_one_radio_button)
            self.bnc845rf_power_radio_buttom_layout.addWidget(self.bnc845rf_power_zone_customized_radio_button)

            self.bnc845rf_power_zone_radio_button_group = QButtonGroup()
            self.bnc845rf_power_zone_radio_button_group.addButton(self.bnc845rf_power_zone_one_radio_button)
            self.bnc845rf_power_zone_radio_button_group.addButton(self.bnc845rf_power_zone_customized_radio_button)


            self.bnc845rf_frequency_setting_layout = QHBoxLayout()
            bnc845rf_frequency_setting_label = QLabel('Frequency:')
            bnc845rf_frequency_setting_label.setFont(self.font)
            self.bnc845rf_frequency_setting_entry = QLineEdit()
            self.bnc845rf_frequency_setting_entry.setFont(self.font)
            bnc845rf_frequency_setting_unit_combo = QComboBox()
            bnc845rf_frequency_setting_unit_combo.setFont(self.font)
            bnc845rf_frequency_setting_unit_combo.setStyleSheet(self.QCombo_stylesheet)
            bnc845rf_frequency_setting_unit_combo.addItems(
                ["Select Unit", "Hz", "kHz", "MHz", "GHz"])
            self.bnc845rf_frequency_setting_layout.addWidget(bnc845rf_frequency_setting_label)
            self.bnc845rf_frequency_setting_layout.addWidget(self.bnc845rf_frequency_setting_entry)
            self.bnc845rf_frequency_setting_layout.addWidget(bnc845rf_frequency_setting_unit_combo)

            self.bnc845rf_loop_setting_content_layout.addWidget(self.bnc845rf_frequency_zone_number_label)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_power_radio_buttom_layout)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_power_zone_layout)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_frequency_setting_layout)
        elif self.bnc845rf_loop_setting_combo.currentIndex() == 3:
            self.bnc845rf_frequency_radio_buttom_layout = QHBoxLayout()
            self.bnc845rf_frequency_zone_layout = QVBoxLayout()

            self.bnc845rf_frequency_zone_1 = False
            self.bnc845rf_frequency_zone_2 = False
            self.bnc845rf_frequency_zone_3 = False
            self.bnc845rf_frequency_zone_customized = False

            self.bnc845rf_frequency_zone_number_label = QLabel('Number of Independent Frequency Regions:')
            self.bnc845rf_frequency_zone_number_label.setFont(self.font)
            self.bnc845rf_frequency_zone_one_radio_button = QRadioButton("1")
            self.bnc845rf_frequency_zone_one_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_one_radio_button.toggled.connect(self.select_frequency_zone)
            self.bnc845rf_frequency_zone_two_radio_button = QRadioButton("2")
            self.bnc845rf_frequency_zone_two_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_two_radio_button.toggled.connect(self.select_frequency_zone)
            self.bnc845rf_frequency_zone_three_radio_button = QRadioButton("3")
            self.bnc845rf_frequency_zone_three_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_three_radio_button.toggled.connect(self.select_frequency_zone)
            self.bnc845rf_frequency_zone_customized_radio_button = QRadioButton("Customize")
            self.bnc845rf_frequency_zone_customized_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_customized_radio_button.toggled.connect(self.select_frequency_zone)

            self.bnc845rf_frequency_zone_radio_button_group = QButtonGroup()
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_one_radio_button)
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_two_radio_button)
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_three_radio_button)
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_customized_radio_button)

            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_one_radio_button)
            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_two_radio_button)
            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_three_radio_button)
            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_customized_radio_button)

            self.bnc845rf_power_radio_buttom_layout = QHBoxLayout()
            self.bnc845rf_power_zone_layout = QVBoxLayout()

            self.bnc845rf_power_zone_1 = False
            self.bnc845rf_power_zone_customized = False

            self.bnc845rf_power_zone_number_label = QLabel('Number of Independent Power Regions:')
            self.bnc845rf_power_zone_number_label.setFont(self.font)
            self.bnc845rf_power_zone_one_radio_button = QRadioButton("1")
            self.bnc845rf_power_zone_one_radio_button.setFont(self.font)
            self.bnc845rf_power_zone_one_radio_button.toggled.connect(self.select_power_zone)
            self.bnc845rf_power_zone_customized_radio_button = QRadioButton("Customize")
            self.bnc845rf_power_zone_customized_radio_button.setFont(self.font)
            self.bnc845rf_power_zone_customized_radio_button.toggled.connect(self.select_power_zone)

            self.bnc845rf_power_radio_buttom_layout.addWidget(self.bnc845rf_power_zone_one_radio_button)
            self.bnc845rf_power_radio_buttom_layout.addWidget(self.bnc845rf_power_zone_customized_radio_button)

            self.bnc845rf_loop_setting_content_layout.addWidget(self.bnc845rf_frequency_zone_number_label)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_frequency_radio_buttom_layout)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_frequency_zone_layout)
            self.bnc845rf_loop_setting_content_layout.addWidget(self.bnc845rf_power_zone_number_label)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_power_radio_buttom_layout)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_power_zone_layout)

    def bnc845rf_modulation_selection_ui(self):
        try:
            self.clear_layout(self.bnc845rf_modulation_selected_layout)
            if self.bnc845rf_modulation_combo.currentIndex() == 1:
                None
            elif self.bnc845rf_modulation_combo.currentIndex() == 2:
                self.bnc845rf_am_layout = QVBoxLayout()

                bnc845rf_am_freq_layout = QHBoxLayout()
                bnc845rf_am_freq_label = QLabel('Mod Frequency:')
                bnc845rf_am_freq_label.setFont(self.font)
                self.bnc845rf_am_freq_entry = QLineEdit()
                self.bnc845rf_am_freq_entry.setFont(self.font)
                bnc845rf_am_freq_unit_label = QLabel('Hz')
                bnc845rf_am_freq_unit_label.setFont(self.font)
                bnc845rf_am_freq_layout.addWidget(bnc845rf_am_freq_label)
                bnc845rf_am_freq_layout.addWidget(self.bnc845rf_am_freq_entry)
                bnc845rf_am_freq_layout.addWidget(bnc845rf_am_freq_unit_label)

                bnc845rf_am_depth_layout = QHBoxLayout()
                bnc845rf_am_depth_label = QLabel('Mod Frequency:')
                bnc845rf_am_depth_label.setFont(self.font)
                self.bnc845rf_am_depth_entry = QLineEdit()
                self.bnc845rf_am_depth_entry.setFont(self.font)
                bnc845rf_am_depth_unit_label = QLabel('%')
                bnc845rf_am_depth_unit_label.setFont(self.font)
                bnc845rf_am_depth_layout.addWidget(bnc845rf_am_depth_label)
                bnc845rf_am_depth_layout.addWidget(self.bnc845rf_am_depth_entry)
                bnc845rf_am_depth_layout.addWidget(bnc845rf_am_depth_unit_label)

                bnc845rf_am_source_layout = QHBoxLayout()
                bnc845rf_am_source_label = QLabel('Source:')
                bnc845rf_am_source_label.setFont(self.font)
                self.bnc845rf_am_source_combo = QComboBox()
                self.bnc845rf_am_source_combo.setFont(self.font)
                self.bnc845rf_am_source_combo.setStyleSheet(self.QCombo_stylesheet)
                self.bnc845rf_am_source_combo.addItems(
                    ["INT", "EXT"])
                bnc845rf_am_source_layout.addWidget(bnc845rf_am_source_label)
                bnc845rf_am_source_layout.addWidget(self.bnc845rf_am_source_combo)

                self.bnc845rf_am_modulation_on_off_button = QPushButton('On')
                self.bnc845rf_am_modulation_on_off_button.setFont(self.font)
                self.bnc845rf_am_modulation_on_off_button.setStyleSheet(self.Button_stylesheet)
                self.bnc845rf_am_modulation_on_off_button.clicked.connect(self.bnc845_am_control)

                self.bnc845rf_am_layout.addLayout(bnc845rf_am_freq_layout)
                self.bnc845rf_am_layout.addLayout(bnc845rf_am_depth_layout)
                self.bnc845rf_am_layout.addLayout(bnc845rf_am_source_layout)
                self.bnc845rf_am_layout.addWidget(self.bnc845rf_am_modulation_on_off_button)
                self.bnc845rf_modulation_selected_layout.addLayout(self.bnc845rf_am_layout)
            elif self.bnc845rf_modulation_combo.currentIndex() == 3:
                None
            else:
                None

        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def select_frequency_zone(self):
        try:
            if self.bnc845rf_frequency_zone_one_radio_button.isChecked() and self.bnc845rf_frequency_zone_1 == False:
                self.bnc845rf_frequency_zone_one_radio_button.setChecked(False)
                self.bnc845rf_frequency_zone_1 = True
                self.bnc845rf_frequency_zone_2 = False
                self.bnc845rf_frequency_zone_3 = False
                self.bnc845rf_frequency_zone_customized = False
                self.select_frequency_zone_one()
                self.bnc845rf_frequency_zone_one_radio_button.setChecked(False)
            elif self.bnc845rf_frequency_zone_two_radio_button.isChecked() and self.bnc845rf_frequency_zone_2 == False:
                self.bnc845rf_frequency_zone_two_radio_button.setChecked(False)
                self.bnc845rf_frequency_zone_1 = False
                self.bnc845rf_frequency_zone_2 = True
                self.bnc845rf_frequency_zone_3 = False
                self.bnc845rf_frequency_zone_customized = False
                self.select_frequency_zone_two()
                self.bnc845rf_frequency_zone_two_radio_button.setChecked(False)
            elif self.bnc845rf_frequency_zone_three_radio_button.isChecked() and self.bnc845rf_frequency_zone_3 == False:
                self.bnc845rf_frequency_zone_three_radio_button.setChecked(False)
                self.bnc845rf_frequency_zone_1 = False
                self.bnc845rf_frequency_zone_2 = False
                self.bnc845rf_frequency_zone_3 = True
                self.bnc845rf_frequency_zone_customized = False
                self.select_frequency_zone_three()
                self.bnc845rf_frequency_zone_three_radio_button.setChecked(False)
            elif self.bnc845rf_frequency_zone_customized_radio_button.isChecked() and self.bnc845rf_frequency_zone_customized == False:
                self.bnc845rf_frequency_zone_customized_radio_button.setChecked(False)
                self.bnc845rf_frequency_zone_1 = False
                self.bnc845rf_frequency_zone_2 = False
                self.bnc845rf_frequency_zone_3 = False
                self.bnc845rf_frequency_zone_customized = True
                self.select_frequency_zone_customize()
                self.bnc845rf_frequency_zone_customized_radio_button.setChecked(False)
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def select_power_zone(self):
        try:
            if self.bnc845rf_power_zone_one_radio_button.isChecked() and self.bnc845rf_power_zone_1 == False:
                self.bnc845rf_power_zone_one_radio_button.setChecked(False)
                self.bnc845rf_power_zone_1 = True
                self.bnc845rf_power_zone_customized = False
                self.select_power_zone_one()
                self.bnc845rf_power_zone_one_radio_button.setChecked(False)
            elif self.bnc845rf_power_zone_customized_radio_button.isChecked() and self.bnc845rf_power_zone_customized == False:
                self.bnc845rf_power_zone_customized_radio_button.setChecked(False)
                self.bnc845rf_power_zone_1 = False
                self.bnc845rf_power_zone_customized = True
                self.select_power_zone_customize()
                self.bnc845rf_power_zone_customized_radio_button.setChecked(False)
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def select_frequency_zone_one(self):
        self.bnc845rf_frequency_zone_one_freq_layout = QVBoxLayout()

        self.bnc845rf_frequency_zone_range_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_one_freq_from_label = QLabel('Range: From')
        self.bnc845rf_frequency_zone_one_freq_from_label.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_from_entry = QLineEdit()
        self.bnc845rf_frequency_zone_one_freq_from_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_to_label = QLabel(' to ')
        self.bnc845rf_frequency_zone_one_freq_to_label.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_to_entry = QLineEdit()
        self.bnc845rf_frequency_zone_one_freq_to_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_one_freq_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_one_freq_unit_combo.addItems(
            ["Select Unit", "Hz", "kHz", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_range_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_from_label)
        self.bnc845rf_frequency_zone_range_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_from_entry)
        self.bnc845rf_frequency_zone_range_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_to_label)
        self.bnc845rf_frequency_zone_range_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_to_entry)
        self.bnc845rf_frequency_zone_range_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_unit_combo)

        self.bnc845rf_frequency_zone_step_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_one_freq_step_label = QLabel('Step Size:')
        self.bnc845rf_frequency_zone_one_freq_step_label.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_step_entry = QLineEdit()
        self.bnc845rf_frequency_zone_one_freq_step_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_step_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_one_freq_step_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_step_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_one_freq_step_unit_combo.addItems(
            ["Select Unit", "Hz", "kHz", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_step_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_step_label)
        self.bnc845rf_frequency_zone_step_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_step_entry)
        self.bnc845rf_frequency_zone_step_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_step_unit_combo)

        self.bnc845rf_frequency_zone_one_freq_layout.addLayout(self.bnc845rf_frequency_zone_range_layout)
        self.bnc845rf_frequency_zone_one_freq_layout.addLayout(self.bnc845rf_frequency_zone_step_layout)

        self.clear_layout(self.bnc845rf_frequency_zone_layout)
        self.bnc845rf_frequency_zone_layout.addLayout(self.bnc845rf_frequency_zone_one_freq_layout)

    def select_power_zone_one(self):
        self.bnc845rf_power_zone_one_power_layout = QVBoxLayout()

        self.bnc845rf_power_zone_range_layout = QHBoxLayout()
        bnc845rf_power_zone_one_power_from_label = QLabel('Range: From')
        bnc845rf_power_zone_one_power_from_label.setFont(self.font)
        self.bnc845rf_power_zone_one_power_from_entry = QLineEdit()
        self.bnc845rf_power_zone_one_power_from_entry.setFont(self.font)
        bnc845rf_power_zone_one_power_to_label = QLabel(' to ')
        bnc845rf_power_zone_one_power_to_label.setFont(self.font)
        self.bnc845rf_power_zone_one_power_to_entry = QLineEdit()
        self.bnc845rf_power_zone_one_power_to_entry.setFont(self.font)
        bnc845rf_power_zone_one_power_unit_label = QLabel('dBm')
        bnc845rf_power_zone_one_power_unit_label.setFont(self.font)
        self.bnc845rf_power_zone_range_layout.addWidget(bnc845rf_power_zone_one_power_from_label)
        self.bnc845rf_power_zone_range_layout.addWidget(self.bnc845rf_power_zone_one_power_from_entry)
        self.bnc845rf_power_zone_range_layout.addWidget(bnc845rf_power_zone_one_power_to_label)
        self.bnc845rf_power_zone_range_layout.addWidget(self.bnc845rf_power_zone_one_power_to_entry)
        self.bnc845rf_power_zone_range_layout.addWidget(bnc845rf_power_zone_one_power_unit_label)

        self.bnc845rf_power_zone_step_layout = QHBoxLayout()
        bnc845rf_power_zone_one_power_step_label = QLabel('Step Size:')
        bnc845rf_power_zone_one_power_step_label.setFont(self.font)
        self.bnc845rf_power_zone_one_power_step_entry = QLineEdit()
        self.bnc845rf_power_zone_one_power_step_entry.setFont(self.font)
        bnc845rf_power_zone_one_power_step_unit_label = QLabel('dBm')
        bnc845rf_power_zone_one_power_step_unit_label.setFont(self.font)

        self.bnc845rf_power_zone_step_layout.addWidget(bnc845rf_power_zone_one_power_step_label)
        self.bnc845rf_power_zone_step_layout.addWidget(self.bnc845rf_power_zone_one_power_step_entry)
        self.bnc845rf_power_zone_step_layout.addWidget(bnc845rf_power_zone_one_power_step_unit_label)

        self.bnc845rf_power_zone_one_power_layout.addLayout(self.bnc845rf_power_zone_range_layout)
        self.bnc845rf_power_zone_one_power_layout.addLayout(self.bnc845rf_power_zone_step_layout)

        self.clear_layout(self.bnc845rf_power_zone_layout)
        self.bnc845rf_power_zone_layout.addLayout(self.bnc845rf_power_zone_one_power_layout)

    def select_frequency_zone_two(self):
        self.select_frequency_zone_one()
        self.bnc845rf_frequency_zone_two_freq_layout = QVBoxLayout()

        self.bnc845rf_frequency_zone_two_range_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_two_freq_from_label = QLabel('Range: From')
        self.bnc845rf_frequency_zone_two_freq_from_label.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_from_entry = QLineEdit()
        self.bnc845rf_frequency_zone_two_freq_from_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_to_label = QLabel(' to ')
        self.bnc845rf_frequency_zone_two_freq_to_label.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_to_entry = QLineEdit()
        self.bnc845rf_frequency_zone_two_freq_to_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_two_freq_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_two_freq_unit_combo.addItems(
            ["Select Unit", "Hz", "kHZ", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_two_range_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_from_label)
        self.bnc845rf_frequency_zone_two_range_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_from_entry)
        self.bnc845rf_frequency_zone_two_range_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_to_label)
        self.bnc845rf_frequency_zone_two_range_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_to_entry)
        self.bnc845rf_frequency_zone_two_range_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_unit_combo)

        self.bnc845rf_frequency_zone_two_step_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_two_freq_step_label = QLabel('Step Size:')
        self.bnc845rf_frequency_zone_two_freq_step_label.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_step_entry = QLineEdit()
        self.bnc845rf_frequency_zone_two_freq_step_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_step_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_two_freq_step_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_step_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_two_freq_step_unit_combo.addItems(
            ["Select Unit", "Hz", "kHZ", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_two_step_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_step_label)
        self.bnc845rf_frequency_zone_two_step_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_step_entry)
        self.bnc845rf_frequency_zone_two_step_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_step_unit_combo)

        self.bnc845rf_frequency_zone_two_freq_layout.addLayout(self.bnc845rf_frequency_zone_two_range_layout)
        self.bnc845rf_frequency_zone_two_freq_layout.addLayout(self.bnc845rf_frequency_zone_two_step_layout)

        self.bnc845rf_frequency_zone_layout.addLayout(self.bnc845rf_frequency_zone_two_freq_layout)

    def select_frequency_zone_three(self):
        self.select_frequency_zone_two()
        self.bnc845rf_frequency_zone_three_freq_layout = QVBoxLayout()

        self.bnc845rf_frequency_zone_three_range_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_three_freq_from_label = QLabel('Range: From')
        self.bnc845rf_frequency_zone_three_freq_from_label.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_from_entry = QLineEdit()
        self.bnc845rf_frequency_zone_three_freq_from_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_to_label = QLabel(' to ')
        self.bnc845rf_frequency_zone_three_freq_to_label.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_to_entry = QLineEdit()
        self.bnc845rf_frequency_zone_three_freq_to_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_three_freq_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_three_freq_unit_combo.addItems(
            ["Select Unit", "Hz", "kHZ", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_three_range_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_from_label)
        self.bnc845rf_frequency_zone_three_range_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_from_entry)
        self.bnc845rf_frequency_zone_three_range_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_to_label)
        self.bnc845rf_frequency_zone_three_range_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_to_entry)
        self.bnc845rf_frequency_zone_three_range_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_unit_combo)

        self.bnc845rf_frequency_zone_three_step_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_three_freq_step_label = QLabel('Step Size:')
        self.bnc845rf_frequency_zone_three_freq_step_label.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_step_entry = QLineEdit()
        self.bnc845rf_frequency_zone_three_freq_step_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_step_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_three_freq_step_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_step_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_three_freq_step_unit_combo.addItems(
            ["Select Unit", "Hz", "kHZ", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_three_step_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_step_label)
        self.bnc845rf_frequency_zone_three_step_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_step_entry)
        self.bnc845rf_frequency_zone_three_step_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_step_unit_combo)

        self.bnc845rf_frequency_zone_three_freq_layout.addLayout(self.bnc845rf_frequency_zone_three_range_layout)
        self.bnc845rf_frequency_zone_three_freq_layout.addLayout(self.bnc845rf_frequency_zone_two_step_layout)

        self.bnc845rf_frequency_zone_layout.addLayout(self.bnc845rf_frequency_zone_three_freq_layout)

    def select_frequency_zone_customize(self):
        self.bnc845rf_frequency_zone_customized_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_customized_label = QLabel('Frequency List: [')
        self.bnc845rf_frequency_zone_customized_label.setFont(self.font)
        self.bnc845rf_frequency_zone_customized_entry = QLineEdit()
        self.bnc845rf_frequency_zone_customized_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_customized_end_label = QLabel(']')
        self.bnc845rf_frequency_zone_customized_end_label.setFont(self.font)
        self.bnc845rf_frequency_zone_customized_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_customized_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_customized_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_customized_unit_combo.addItems(
            ["Select Unit", "Hz", "kHZ", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_customized_layout.addWidget(self.bnc845rf_frequency_zone_customized_label)
        self.bnc845rf_frequency_zone_customized_layout.addWidget(self.bnc845rf_frequency_zone_customized_entry)
        self.bnc845rf_frequency_zone_customized_layout.addWidget(self.bnc845rf_frequency_zone_customized_end_label)
        self.bnc845rf_frequency_zone_customized_layout.addWidget(self.bnc845rf_frequency_zone_customized_unit_combo)

        self.clear_layout(self.bnc845rf_frequency_zone_layout)
        self.bnc845rf_frequency_zone_layout.addLayout(self.bnc845rf_frequency_zone_customized_layout)

    def select_power_zone_customize(self):
        self.bnc845rf_power_zone_customized_layout = QHBoxLayout()
        bnc845rf_power_zone_customized_label = QLabel('Power List: [')
        bnc845rf_power_zone_customized_label.setFont(self.font)
        self.bnc845rf_power_zone_customized_entry = QLineEdit()
        self.bnc845rf_power_zone_customized_entry.setFont(self.font)
        bnc845rf_power_zone_customized_end_label = QLabel(']')
        bnc845rf_power_zone_customized_end_label.setFont(self.font)
        bnc845rf_power_zone_customized_unit_label = QLabel('dBm')
        bnc845rf_power_zone_customized_unit_label.setFont(self.font)
        self.bnc845rf_power_zone_customized_layout.addWidget(bnc845rf_power_zone_customized_label)
        self.bnc845rf_power_zone_customized_layout.addWidget(self.bnc845rf_power_zone_customized_entry)
        self.bnc845rf_power_zone_customized_layout.addWidget(bnc845rf_power_zone_customized_end_label)
        self.bnc845rf_power_zone_customized_layout.addWidget(bnc845rf_power_zone_customized_unit_label)

        self.clear_layout(self.bnc845rf_power_zone_layout)
        self.bnc845rf_power_zone_layout.addLayout(self.bnc845rf_power_zone_customized_layout)

    def bnc845_am_control(self):
        print(self.get_bnc845rf_settings())
        # if self.BNC845_AM_ON == False:
        #     self.BNC845_AM_ON = True
        #     self.bnc845rf_am_modulation_on_off_button.setText('OFF')
        #     BNC_845M_COMMAND().set_am_state(self.bnc845rf, 'ON')
        # else:
        #     self.BNC845_AM_ON = False
        #     self.bnc845rf_am_modulation_on_off_button.setText('ON')
        #     BNC_845M_COMMAND().set_am_state(self.bnc845rf, 'OFF')

    def get_bnc845rf_settings(self):
        """
        Get all BNC845RF settings and return them as a dictionary.
        Frequencies and power values are returned as lists.
        """
        settings = {}

        try:
            # Get loop setting type
            settings['loop_type'] = self.bnc845rf_loop_setting_combo.currentText()

            # Get frequency settings based on loop type
            if self.bnc845rf_loop_setting_combo.currentIndex() in [1, 3]:  # Frequency Dependent or Both
                settings['frequency_zones'] = {}

                # Determine which frequency zone is selected
                if hasattr(self, 'bnc845rf_frequency_zone_1') and self.bnc845rf_frequency_zone_1:
                    settings['frequency_zone_count'] = 1
                    settings['frequency_zones']['zone_1'] = self._get_frequency_zone_one()
                    settings['frequency_zones']['final_list'] = self._get_frequency_zone_one()['frequency_list']

                elif hasattr(self, 'bnc845rf_frequency_zone_2') and self.bnc845rf_frequency_zone_2:
                    settings['frequency_zone_count'] = 2
                    settings['frequency_zones']['zone_1'] = self._get_frequency_zone_one()
                    settings['frequency_zones']['zone_2'] = self._get_frequency_zone_two()
                    settings['frequency_zones']['final_list'] = self._get_frequency_zone_one()['frequency_list'] + self._get_frequency_zone_two()['frequency_list']

                elif hasattr(self, 'bnc845rf_frequency_zone_3') and self.bnc845rf_frequency_zone_3:
                    settings['frequency_zone_count'] = 3
                    settings['frequency_zones']['zone_1'] = self._get_frequency_zone_one()
                    settings['frequency_zones']['zone_2'] = self._get_frequency_zone_two()
                    settings['frequency_zones']['zone_3'] = self._get_frequency_zone_three()
                    settings['frequency_zones'][
                        'final_list'] = self._get_frequency_zone_one()['frequency_list'] + self._get_frequency_zone_two()['frequency_list'] + self._get_frequency_zone_three()['frequency_list']

                elif hasattr(self, 'bnc845rf_frequency_zone_customized') and self.bnc845rf_frequency_zone_customized:
                    settings['frequency_zone_count'] = 'customized'
                    settings['frequency_zones']['customized'] = self._get_frequency_zone_customized()
                    settings['frequency_zones']['final_list'] = self._get_frequency_zone_customized()

            # Get power settings based on loop type
            if self.bnc845rf_loop_setting_combo.currentIndex() == 1:  # Frequency Dependent only
                if hasattr(self, 'bnc845rf_power_setting_entry'):
                    settings['power'] = self.bnc845rf_power_setting_entry.text()

            elif self.bnc845rf_loop_setting_combo.currentIndex() in [2, 3]:  # Power Dependent or Both
                settings['power_zones'] = {}

                # Determine which power zone is selected
                if hasattr(self, 'bnc845rf_power_zone_1') and self.bnc845rf_power_zone_1:
                    settings['power_zone_count'] = 1
                    settings['power_zones']['zone_1'] = self._get_power_zone_one()

                elif hasattr(self, 'bnc845rf_power_zone_customized') and self.bnc845rf_power_zone_customized:
                    settings['power_zone_count'] = 'customized'
                    settings['power_zones']['customized'] = self._get_power_zone_customized()

            # Get frequency setting for Power Dependent mode
            if self.bnc845rf_loop_setting_combo.currentIndex() == 2:  # Power Dependent only
                if hasattr(self, 'bnc845rf_frequency_setting_entry'):
                    settings['frequency'] = self.bnc845rf_frequency_setting_entry.text()

            # Get modulation settings (input settings)
            settings['modulation_settings'] = self._get_modulation_settings()

            # Get modulation readings (from instrument)
            settings['modulation_readings'] = self._get_modulation_readings()

            # Get current instrument readings
            # settings['instrument_readings'] = self._get_instrument_readings()

            return settings

        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            print(f"Error getting BNC845RF settings: {tb_str} {str(e)}")
            return {}

    def _get_frequency_zone_one(self):
        """Get frequency zone 1 settings and return as list"""
        zone_data = {
            'from': self.bnc845rf_frequency_zone_one_freq_from_entry.text(),
            'to': self.bnc845rf_frequency_zone_one_freq_to_entry.text(),
            'step': self.bnc845rf_frequency_zone_one_freq_step_entry.text(),
            'unit': self.bnc845rf_frequency_zone_one_freq_unit_combo.currentText()
        }

        # Generate frequency list
        zone_data['frequency_list'] = self._generate_frequency_list(
            zone_data['from'],
            zone_data['to'],
            zone_data['step'],
            zone_data['unit']
        )

        return zone_data

    def _get_frequency_zone_two(self):
        """Get frequency zone 2 settings and return as list"""
        zone_data = {
            'from': self.bnc845rf_frequency_zone_two_freq_from_entry.text(),
            'to': self.bnc845rf_frequency_zone_two_freq_to_entry.text(),
            'step': self.bnc845rf_frequency_zone_two_freq_step_entry.text(),
            'unit': self.bnc845rf_frequency_zone_two_freq_unit_combo.currentText()
        }

        # Generate frequency list
        zone_data['frequency_list'] = self._generate_frequency_list(
            zone_data['from'],
            zone_data['to'],
            zone_data['step'],
            zone_data['unit']
        )

        return zone_data

    def _get_frequency_zone_three(self):
        """Get frequency zone 3 settings and return as list"""
        zone_data = {
            'from': self.bnc845rf_frequency_zone_three_freq_from_entry.text(),
            'to': self.bnc845rf_frequency_zone_three_freq_to_entry.text(),
            'step': self.bnc845rf_frequency_zone_three_freq_step_entry.text(),
            'unit': self.bnc845rf_frequency_zone_three_freq_unit_combo.currentText()
        }

        # Generate frequency list
        zone_data['frequency_list'] = self._generate_frequency_list(
            zone_data['from'],
            zone_data['to'],
            zone_data['step'],
            zone_data['unit']
        )

        return zone_data

    def _get_frequency_zone_customized(self):
        """Get customized frequency zone settings"""
        zone_data = {
            'raw_input': self.bnc845rf_frequency_zone_customized_entry.text(),
            'unit': self.bnc845rf_frequency_zone_customized_unit_combo.currentText()
        }

        # Parse the frequency list from the entry
        frequency_str = self.bnc845rf_frequency_zone_customized_entry.text()
        zone_data['frequency_list'] = self._parse_custom_list(frequency_str)

        return zone_data

    def _get_power_zone_one(self):
        """Get power zone 1 settings and return as list in dBm"""
        zone_data = {
            'from': self.bnc845rf_power_zone_one_power_from_entry.text(),
            'to': self.bnc845rf_power_zone_one_power_to_entry.text(),
            'step': self.bnc845rf_power_zone_one_power_step_entry.text(),
            'unit': 'dBm'
        }

        # Generate power list
        zone_data['power_list'] = self._generate_power_list(
            zone_data['from'],
            zone_data['to'],
            zone_data['step']
        )

        return zone_data

    def _get_power_zone_customized(self):
        """Get customized power zone settings"""
        zone_data = {
            'raw_input': self.bnc845rf_power_zone_customized_entry.text(),
            'unit': 'dBm'
        }

        # Parse the power list from the entry
        power_str = self.bnc845rf_power_zone_customized_entry.text()
        zone_data['power_list'] = self._parse_custom_list(power_str)

        return zone_data

    def _get_modulation_settings(self):
        """Get modulation settings (user input settings)"""
        modulation_data = {
            'type': self.bnc845rf_modulation_combo.currentText()
        }

        # Get modulation-specific settings
        if self.bnc845rf_modulation_combo.currentIndex() == 2:  # Amplitude Modulation
            if hasattr(self, 'bnc845rf_am_freq_entry'):
                modulation_data['am_frequency'] = self.bnc845rf_am_freq_entry.text()
                modulation_data['am_frequency_unit'] = 'Hz'

            if hasattr(self, 'bnc845rf_am_depth_entry'):
                modulation_data['am_depth'] = self.bnc845rf_am_depth_entry.text()
                modulation_data['am_depth_unit'] = '%'

            if hasattr(self, 'bnc845rf_am_source_combo'):
                modulation_data['am_source'] = self.bnc845rf_am_source_combo.currentText()

        return modulation_data

    def _get_modulation_readings(self):
        """
        Get all modulation readings from the instrument display.
        These are the actual measured/read values from the BNC845RF.
        """
        readings = {}

        try:
            # Get modulation type reading from label
            if hasattr(self, 'bnc845rf_modulation_reading_label'):
                readings['modulation_type'] = self.bnc845rf_modulation_reading_label.text()

            # Get modulation depth reading from label
            if hasattr(self, 'bnc845rf_modulation_depth_reading_label'):
                readings['modulation_depth'] = self.bnc845rf_modulation_depth_reading_label.text()

            # Get modulation frequency reading from label
            if hasattr(self, 'bnc845rf_modulation_frequency_reading_label'):
                readings['modulation_frequency'] = self.bnc845rf_modulation_frequency_reading_label.text()

            # Get modulation state reading from label
            if hasattr(self, 'bnc845rf_modulation_state_reading_label'):
                readings['modulation_state'] = self.bnc845rf_modulation_state_reading_label.text()

        except Exception as e:
            print(f"Error getting modulation readings: {str(e)}")

        return readings

    def _get_modulation_readings_from_instrument(self, instrument, bnc_cmd):
        """
        Query all modulation settings directly from the BNC845RF instrument.
        This queries the actual instrument state, not just the UI labels.

        Args:
            instrument: VISA instrument object
            bnc_cmd: BNC_845M_COMMAND instance

        Returns:
            Dictionary with all modulation readings from instrument
        """
        readings = {}

        try:
            # Query AM (Amplitude Modulation) settings
            try:
                readings['am_state'] = bnc_cmd.get_am_state(instrument).strip()
                readings['am_depth'] = bnc_cmd.get_am_depth(instrument).strip()
                readings['am_source'] = bnc_cmd.get_am_source(instrument).strip()
                readings['am_internal_frequency'] = bnc_cmd.get_am_internal_frequency(instrument).strip()
            except Exception as e:
                readings['am_error'] = str(e)

            # Query FM (Frequency Modulation) settings
            try:
                readings['fm_state'] = bnc_cmd.get_fm_state(instrument).strip()
                readings['fm_deviation'] = bnc_cmd.get_fm_deviation(instrument).strip()
                readings['fm_source'] = bnc_cmd.get_fm_source(instrument).strip()
                readings['fm_internal_frequency'] = bnc_cmd.get_fm_internal_frequency(instrument).strip()
                readings['fm_sensitivity'] = bnc_cmd.get_fm_sensitivity(instrument).strip()
                readings['fm_coupling'] = bnc_cmd.get_fm_coupling(instrument).strip()
            except Exception as e:
                readings['fm_error'] = str(e)

            # Query PM (Phase Modulation) settings
            try:
                readings['pm_state'] = bnc_cmd.get_pm_state(instrument).strip()
                readings['pm_deviation'] = bnc_cmd.get_pm_deviation(instrument).strip()
                readings['pm_source'] = bnc_cmd.get_pm_source(instrument).strip()
                readings['pm_sensitivity'] = bnc_cmd.get_pm_sensitivity(instrument).strip()
            except Exception as e:
                readings['pm_error'] = str(e)

            # Query Pulse Modulation settings
            try:
                readings['pulse_state'] = bnc_cmd.get_pulse_state(instrument).strip()
                readings['pulse_source'] = bnc_cmd.get_pulse_source(instrument).strip()
                readings['pulse_polarity'] = bnc_cmd.get_pulse_polarity(instrument).strip()
                readings['pulse_internal_frequency'] = bnc_cmd.get_pulse_internal_frequency(instrument).strip()
                readings['pulse_internal_period'] = bnc_cmd.get_pulse_internal_period(instrument).strip()
                readings['pulse_internal_width'] = bnc_cmd.get_pulse_internal_width(instrument).strip()
                readings['pulse_mode'] = bnc_cmd.get_pulse_mode(instrument).strip()
            except Exception as e:
                readings['pulse_error'] = str(e)

        except Exception as e:
            readings['general_error'] = str(e)
            print(f"Error querying modulation from instrument: {str(e)}")

        return readings

    def apply_modulation_settings_to_instrument(self, instrument, bnc_cmd):
        """
        Apply the current UI modulation settings to the BNC845RF instrument.

        Args:
            instrument: VISA instrument object
            bnc_cmd: BNC_845M_COMMAND instance

        Returns:
            Dictionary with success status and any errors
        """
        result = {
            'success': False,
            'applied_settings': {},
            'errors': []
        }

        try:
            modulation_type = self.bnc845rf_modulation_combo.currentIndex()

            # First, turn off all modulations
            try:
                bnc_cmd.set_am_state(instrument, 'OFF')
                bnc_cmd.set_fm_state(instrument, 'OFF')
                bnc_cmd.set_pm_state(instrument, 'OFF')
                bnc_cmd.set_pulse_state(instrument, 'OFF')
            except Exception as e:
                result['errors'].append(f"Error turning off modulations: {str(e)}")

            # Apply Pulse Modulation (index 1)
            if modulation_type == 1:
                try:
                    bnc_cmd.set_pulse_state(instrument, 'ON')
                    result['applied_settings']['modulation_type'] = 'Pulse Modulation'
                    result['applied_settings']['pulse_state'] = 'ON'
                except Exception as e:
                    result['errors'].append(f"Pulse modulation error: {str(e)}")

            # Apply Amplitude Modulation (index 2)
            elif modulation_type == 2:
                try:
                    if hasattr(self, 'bnc845rf_am_freq_entry') and self.bnc845rf_am_freq_entry.text():
                        am_freq = float(self.bnc845rf_am_freq_entry.text())
                        bnc_cmd.set_am_internal_frequency(instrument, am_freq, 'Hz')
                        result['applied_settings']['am_frequency'] = f"{am_freq} Hz"

                    if hasattr(self, 'bnc845rf_am_depth_entry') and self.bnc845rf_am_depth_entry.text():
                        am_depth = float(self.bnc845rf_am_depth_entry.text()) / 100.0  # Convert % to 0-0.99
                        bnc_cmd.set_am_depth(instrument, am_depth)
                        result['applied_settings']['am_depth'] = f"{am_depth}"

                    if hasattr(self, 'bnc845rf_am_source_combo'):
                        am_source = self.bnc845rf_am_source_combo.currentText()
                        bnc_cmd.set_am_source(instrument, am_source)
                        result['applied_settings']['am_source'] = am_source

                    bnc_cmd.set_am_state(instrument, 'ON')
                    result['applied_settings']['modulation_type'] = 'Amplitude Modulation'
                    result['applied_settings']['am_state'] = 'ON'

                except Exception as e:
                    result['errors'].append(f"AM modulation error: {str(e)}")

            # Apply Frequency Modulation (index 3)
            elif modulation_type == 3:
                try:
                    # Add FM settings here when FM UI is implemented
                    bnc_cmd.set_fm_state(instrument, 'ON')
                    result['applied_settings']['modulation_type'] = 'Frequency Modulation'
                    result['applied_settings']['fm_state'] = 'ON'
                except Exception as e:
                    result['errors'].append(f"FM modulation error: {str(e)}")

            # Apply Phase Modulation (index 4)
            elif modulation_type == 4:
                try:
                    # Add PM settings here when PM UI is implemented
                    bnc_cmd.set_pm_state(instrument, 'ON')
                    result['applied_settings']['modulation_type'] = 'Phase Modulation'
                    result['applied_settings']['pm_state'] = 'ON'
                except Exception as e:
                    result['errors'].append(f"PM modulation error: {str(e)}")

            # Check if there were any errors
            result['success'] = len(result['errors']) == 0

        except Exception as e:
            result['errors'].append(f"General error: {str(e)}")
            result['success'] = False

        return result

    def apply_frequency_settings_to_instrument(self, instrument, bnc_cmd):
        """
        Apply frequency settings from the UI to the BNC845RF instrument.

        Args:
            instrument: VISA instrument object
            bnc_cmd: BNC_845M_COMMAND instance

        Returns:
            Dictionary with success status and applied settings
        """
        result = {
            'success': False,
            'applied_settings': {},
            'errors': []
        }

        try:
            loop_type = self.bnc845rf_loop_setting_combo.currentIndex()

            # Frequency Dependent (index 1)
            if loop_type == 1:
                try:
                    bnc_cmd.set_frequency_mode(instrument, 'SWEep')

                    # Get frequency zone settings
                    settings = self.get_bnc845rf_settings()
                    if 'frequency_zones' in settings:
                        zones = settings['frequency_zones']

                        # For simplicity, use zone_1 settings
                        if 'zone_1' in zones:
                            zone = zones['zone_1']
                            freq_list = zone.get('frequency_list', [])

                            if freq_list:
                                bnc_cmd.set_frequency_start(instrument, freq_list[0], 'Hz')
                                bnc_cmd.set_frequency_stop(instrument, freq_list[-1], 'Hz')
                                bnc_cmd.set_sweep_points(instrument, len(freq_list))

                                result['applied_settings']['frequency_start'] = f"{freq_list[0]} Hz"
                                result['applied_settings']['frequency_stop'] = f"{freq_list[-1]} Hz"
                                result['applied_settings']['sweep_points'] = len(freq_list)

                    # Set fixed power
                    if hasattr(self, 'bnc845rf_power_setting_entry') and self.bnc845rf_power_setting_entry.text():
                        power = float(self.bnc845rf_power_setting_entry.text())
                        bnc_cmd.set_power_mode(instrument, 'FIXed')
                        bnc_cmd.set_power_level(instrument, power, 'dBm')
                        result['applied_settings']['power'] = f"{power} dBm"

                    result['applied_settings']['mode'] = 'Frequency Sweep'

                except Exception as e:
                    result['errors'].append(f"Frequency sweep error: {str(e)}")

            # Power Dependent (index 2)
            elif loop_type == 2:
                try:
                    bnc_cmd.set_power_mode(instrument, 'SWEep')

                    # Get power zone settings
                    settings = self.get_bnc845rf_settings()
                    if 'power_zones' in settings:
                        zones = settings['power_zones']

                        if 'zone_1' in zones:
                            zone = zones['zone_1']
                            power_list = zone.get('power_list', [])

                            if power_list:
                                bnc_cmd.set_power_start(instrument, power_list[0], 'dBm')
                                bnc_cmd.set_power_stop(instrument, power_list[-1], 'dBm')
                                bnc_cmd.set_sweep_points(instrument, len(power_list))

                                result['applied_settings']['power_start'] = f"{power_list[0]} dBm"
                                result['applied_settings']['power_stop'] = f"{power_list[-1]} dBm"
                                result['applied_settings']['sweep_points'] = len(power_list)

                    # Set fixed frequency
                    if hasattr(self,
                               'bnc845rf_frequency_setting_entry') and self.bnc845rf_frequency_setting_entry.text():
                        freq = float(self.bnc845rf_frequency_setting_entry.text())
                        bnc_cmd.set_frequency_mode(instrument, 'CW')
                        bnc_cmd.set_frequency_cw(instrument, freq, 'Hz')
                        result['applied_settings']['frequency'] = f"{freq} Hz"

                    result['applied_settings']['mode'] = 'Power Sweep'

                except Exception as e:
                    result['errors'].append(f"Power sweep error: {str(e)}")

            result['success'] = len(result['errors']) == 0

        except Exception as e:
            result['errors'].append(f"General error: {str(e)}")
            result['success'] = False

        return result

    def update_ui_from_instrument(self, instrument, bnc_cmd):
        """
        Update all UI labels with current readings from the BNC845RF instrument.

        Args:
            instrument: VISA instrument object
            bnc_cmd: BNC_845M_COMMAND instance
        """
        try:
            # Update current frequency reading
            if hasattr(self, 'bnc845rf_current_frequency_reading_label'):
                try:
                    freq = bnc_cmd.get_frequency_cw(instrument).strip()
                    self.bnc845rf_current_frequency_reading_label.setText(freq)
                except:
                    pass

            # Update current power reading
            if hasattr(self, 'bnc845rf_current_power_reading_label'):
                try:
                    power = bnc_cmd.get_power_level(instrument).strip()
                    self.bnc845rf_current_power_reading_label.setText(power)
                except:
                    pass

            # Update RF state
            if hasattr(self, 'bnc845rf_state_reading_label'):
                try:
                    state = bnc_cmd.get_output_state(instrument).strip()
                    self.bnc845rf_state_reading_label.setText(state)
                except:
                    pass

            # Update modulation type
            if hasattr(self, 'bnc845rf_modulation_reading_label'):
                try:
                    # Check which modulation is active
                    am_state = bnc_cmd.get_am_state(instrument).strip()
                    fm_state = bnc_cmd.get_fm_state(instrument).strip()
                    pm_state = bnc_cmd.get_pm_state(instrument).strip()
                    pulse_state = bnc_cmd.get_pulse_state(instrument).strip()

                    if am_state == '1' or am_state.upper() == 'ON':
                        self.bnc845rf_modulation_reading_label.setText('AM')
                    elif fm_state == '1' or fm_state.upper() == 'ON':
                        self.bnc845rf_modulation_reading_label.setText('FM')
                    elif pm_state == '1' or pm_state.upper() == 'ON':
                        self.bnc845rf_modulation_reading_label.setText('PM')
                    elif pulse_state == '1' or pulse_state.upper() == 'ON':
                        self.bnc845rf_modulation_reading_label.setText('PULSE')
                    else:
                        self.bnc845rf_modulation_reading_label.setText('OFF')
                except:
                    pass

            # Update modulation depth (for AM)
            if hasattr(self, 'bnc845rf_modulation_depth_reading_label'):
                try:
                    depth = bnc_cmd.get_am_depth(instrument).strip()
                    # Convert to percentage
                    depth_val = float(depth) * 100
                    self.bnc845rf_modulation_depth_reading_label.setText(f"{depth_val:.1f}%")
                except:
                    pass

            # Update modulation frequency (for AM)
            if hasattr(self, 'bnc845rf_modulation_frequency_reading_label'):
                try:
                    freq = bnc_cmd.get_am_internal_frequency(instrument).strip()
                    self.bnc845rf_modulation_frequency_reading_label.setText(freq)
                except:
                    pass

            # Update modulation state
            if hasattr(self, 'bnc845rf_modulation_state_reading_label'):
                try:
                    am_state = bnc_cmd.get_am_state(instrument).strip()
                    if am_state == '1' or am_state.upper() == 'ON':
                        self.bnc845rf_modulation_state_reading_label.setText('ON')
                    else:
                        self.bnc845rf_modulation_state_reading_label.setText('OFF')
                except:
                    pass

        except Exception as e:
            print(f"Error updating UI from instrument: {str(e)}")

    def _generate_frequency_list(self, from_val, to_val, step_val, unit):
        """
        Generate a list of frequencies from start to end with given step.
        Returns list in base unit (Hz).
        """
        try:
            start = float(from_val)
            end = float(to_val)
            step = float(step_val)

            # Convert to Hz based on unit
            unit_multiplier = {
                'Hz': 1,
                'kHz': 1e3,
                'MHz': 1e6,
                'GHz': 1e9
            }

            multiplier = unit_multiplier.get(unit, 1)

            start_hz = start * multiplier
            end_hz = end * multiplier
            step_hz = step * multiplier

            # Generate list
            frequency_list = []
            current = start_hz
            while current <= end_hz:
                frequency_list.append(current)
                current += step_hz

            return frequency_list

        except (ValueError, TypeError):
            return []

    def _generate_power_list(self, from_val, to_val, step_val):
        """
        Generate a list of power values from start to end with given step.
        Returns list in dBm.
        """
        try:
            start = float(from_val)
            end = float(to_val)
            step = float(step_val)

            # Generate list
            power_list = []
            current = start
            while current <= end:
                power_list.append(current)
                current += step

            return power_list

        except (ValueError, TypeError):
            return []

    def _parse_custom_list(self, list_string):
        """
        Parse a comma-separated string of values into a list of floats.
        Example: "1.0, 2.5, 3.7, 5.0" -> [1.0, 2.5, 3.7, 5.0]
        """
        try:
            # Remove brackets if present
            list_string = list_string.strip('[]')

            # Split by comma and convert to float
            values = [float(x.strip()) for x in list_string.split(',') if x.strip()]

            return values

        except (ValueError, TypeError, AttributeError):
            return []

    def fmr_setup_ui(self):
        None

    def fmr_measurement_status_ui(self):
        fmr_measurement_status_layout = QVBoxLayout()

        fmr_measurement_status_repetition_layout = QHBoxLayout()
        fmr_measurement_status_repetition_label = QLabel('Number of Repetition:')
        fmr_measurement_status_repetition_label.setFont(self.font)
        fmr_measurement_status_repetition_reading_label = QLabel('NA')
        fmr_measurement_status_repetition_reading_label.setFont(self.font)
        fmr_measurement_status_repetition_layout.addWidget(fmr_measurement_status_repetition_label)
        fmr_measurement_status_repetition_layout.addWidget(fmr_measurement_status_repetition_reading_label)

        fmr_measurement_status_time_remaining_layout = QHBoxLayout()
        fmr_measurement_status_time_remaining_label = QLabel('Estimated Time Remaining')
        fmr_measurement_status_time_remaining_label.setFont(self.font)
        fmr_measurement_status_time_remaining_layout.addWidget(fmr_measurement_status_time_remaining_label)

        fmr_measurement_status_time_remaining_in_days_layout = QHBoxLayout()
        fmr_measurement_status_time_remaining_in_days_label = QLabel('In Days:')
        fmr_measurement_status_time_remaining_in_days_label.setFont(self.font)
        fmr_measurement_status_time_remaining_in_days_reading_label = QLabel('NA')
        fmr_measurement_status_time_remaining_in_days_reading_label.setFont(self.font)
        fmr_measurement_status_time_remaining_in_days_layout.addWidget(fmr_measurement_status_time_remaining_in_days_label)
        fmr_measurement_status_time_remaining_in_days_layout.addWidget(fmr_measurement_status_time_remaining_in_days_reading_label)

        fmr_measurement_status_time_remaining_in_hours_layout = QHBoxLayout()
        fmr_measurement_status_time_remaining_in_hours_label = QLabel('In Hours:')
        fmr_measurement_status_time_remaining_in_hours_label.setFont(self.font)
        fmr_measurement_status_time_remaining_in_hours_reading_label = QLabel('NA')
        fmr_measurement_status_time_remaining_in_hours_reading_label.setFont(self.font)
        fmr_measurement_status_time_remaining_in_hours_layout.addWidget(
            fmr_measurement_status_time_remaining_in_hours_label)
        fmr_measurement_status_time_remaining_in_hours_layout.addWidget(
            fmr_measurement_status_time_remaining_in_hours_reading_label)

        fmr_measurement_status_time_remaining_in_mins_layout = QHBoxLayout()
        fmr_measurement_status_time_remaining_in_mins_label = QLabel('In Minutes:')
        fmr_measurement_status_time_remaining_in_mins_label.setFont(self.font)
        fmr_measurement_status_time_remaining_in_mins_reading_label = QLabel('NA')
        fmr_measurement_status_time_remaining_in_mins_reading_label.setFont(self.font)
        fmr_measurement_status_time_remaining_in_mins_layout.addWidget(
            fmr_measurement_status_time_remaining_in_mins_label)
        fmr_measurement_status_time_remaining_in_mins_layout.addWidget(
            fmr_measurement_status_time_remaining_in_mins_reading_label)

        fmr_measurement_status_cur_percent_layout = QHBoxLayout()
        fmr_measurement_status_cur_percent_label = QLabel('Current Percentage:')
        fmr_measurement_status_cur_percent_label.setFont(self.font)
        fmr_measurement_status_cur_percent_reading_label = QLabel('NA')
        fmr_measurement_status_cur_percent_reading_label.setFont(self.font)
        fmr_measurement_status_cur_percent_layout.addWidget(
            fmr_measurement_status_cur_percent_label)
        fmr_measurement_status_cur_percent_layout.addWidget(
            fmr_measurement_status_cur_percent_reading_label)

        fmr_measurement_status_layout.addLayout(fmr_measurement_status_repetition_layout)
        fmr_measurement_status_layout.addLayout(fmr_measurement_status_time_remaining_layout)
        fmr_measurement_status_layout.addLayout(fmr_measurement_status_time_remaining_in_days_layout)
        fmr_measurement_status_layout.addLayout(fmr_measurement_status_time_remaining_in_hours_layout)
        fmr_measurement_status_layout.addLayout(fmr_measurement_status_time_remaining_in_mins_layout)
        fmr_measurement_status_layout.addLayout(fmr_measurement_status_cur_percent_layout)
        return (fmr_measurement_status_layout,
                fmr_measurement_status_repetition_reading_label,
                fmr_measurement_status_time_remaining_in_days_reading_label,
                fmr_measurement_status_time_remaining_in_hours_reading_label,
                fmr_measurement_status_time_remaining_in_mins_reading_label,
                fmr_measurement_status_cur_percent_reading_label)

    def st_fmr_setting_ui(self):
        fmr_setting_layout = QVBoxLayout()

        fmr_setting_average_layout = QHBoxLayout()
        fmr_setting_repetition_label = QLabel('Number of Repetitions:')
        fmr_setting_repetition_label.setToolTip('This setting for how many repetitions should be.')
        fmr_setting_repetition_label.setFont(self.font)
        fmr_setting_average_line_edit = QLineEdit('1')
        fmr_setting_average_line_edit.setFont(self.font)
        fmr_setting_average_layout.addWidget(fmr_setting_repetition_label)
        fmr_setting_average_layout.addStretch(1)
        fmr_setting_average_layout.addWidget(fmr_setting_average_line_edit)
        fmr_setting_layout.addLayout(fmr_setting_average_layout)

        fmr_setting_init_temp_rate_layout = QHBoxLayout()
        fmr_setting_init_temp_rate_label = QLabel('Temperature Ramping Rate (K/min):')
        fmr_setting_init_temp_rate_label.setFont(self.font)
        fmr_setting_init_temp_rate_line_edit = QLineEdit('50')
        fmr_setting_init_temp_rate_line_edit.setFont(self.font)
        fmr_setting_init_temp_rate_layout.addWidget(fmr_setting_init_temp_rate_label)
        fmr_setting_init_temp_rate_layout.addStretch(1)
        fmr_setting_init_temp_rate_layout.addWidget(fmr_setting_init_temp_rate_line_edit)
        fmr_setting_layout.addLayout(fmr_setting_init_temp_rate_layout)

        return (fmr_setting_layout,
                fmr_setting_average_line_edit,
                fmr_setting_init_temp_rate_line_edit)


