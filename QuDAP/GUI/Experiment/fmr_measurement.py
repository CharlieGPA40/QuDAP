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
        None

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


