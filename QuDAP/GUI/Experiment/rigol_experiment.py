from PyQt6.QtWidgets import (
    QSizePolicy, QWidget, QMessageBox, QGroupBox, QFileDialog, QVBoxLayout, QLabel, QHBoxLayout,
    QCheckBox, QTextEdit, QPushButton, QComboBox, QLineEdit, QScrollArea, QDialog, QRadioButton, QMainWindow,
    QDialogButtonBox, QProgressBar, QButtonGroup, QApplication, QCompleter, QToolButton
)
from PyQt6.QtGui import QIcon, QFont, QDoubleValidator, QIcon
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread, QSettings, QSize
from PyQt6.QtGui import QKeyEvent
import traceback

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=100, height=100, dpi=300):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class RIGOL_Measurement(QWidget):
    def __init__(self, rigol_connected: bool, bk_9205_connected: bool):
        super().__init__()
        try:
            with open("GUI/QSS/QButtonWidget.qss", "r") as file:
                self.Button_stylesheet = file.read()
            with open("GUI/QSS/QComboWidget.qss", "r") as file:
                self.QCombo_stylesheet = file.read()
            self.font = QFont("Arial", 13)
            self.RIGOL_CONNECTED = rigol_connected
            self.BK_9205_CONNECTED = bk_9205_connected
            self.init_ui()
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
            return

    def reset_preset(self):
        def safe_clear_layout(layout_attr_name):
            """Safely clear a layout if it exists"""
            if hasattr(self, layout_attr_name):
                layout = getattr(self, layout_attr_name)
                if layout is not None:
                    try:
                        self.clear_layout(layout)
                        return True
                    except Exception as e:
                        print(f"Error clearing {layout_attr_name}: {e}")
            return False

        safe_clear_layout('customize_layout')

    def init_ui(self):
        self.instrument_layout = QVBoxLayout()
        self.customize_layout = QVBoxLayout()
        self.customize_layout.addLayout(self.instrument_layout)
        self.customize_layout.addWidget(self.figure_layout_ui())
        self.customize_layout.addWidget(self.button_layout_ui())
        self.bk9205_layout_ui()
        return self.customize_layout

    def figure_layout_ui(self):
        try:
            from instrument.rigol_spectrum_analyzer import COMMAND
            from instrument.BK_precision_9129B import COMMAND
            from GUI.Experiment.measurement import WideComboBox
        except ImportError:
            from QuDAP.instrument.rigol_spectrum_analyzer import COMMAND
            from QuDAP.instrument.BK_precision_9129B import COMMAND
            from QuDAP.GUI.Experiment.measurement import WideComboBox

        figure_group_box = QGroupBox("Graph")
        figure_content_layout = QHBoxLayout()
        cumulative_figure_Layout = QVBoxLayout()
        self.cumulative_canvas = MplCanvas(self, width=100, height=4, dpi=100)
        cumulative_toolbar = NavigationToolbar(self.cumulative_canvas, self)
        cumulative_toolbar.setStyleSheet("""
                                                                                QWidget {
                                                                                    border: None;
                                                                                }
                                                                            """)
        cumulative_figure_Layout.addWidget(cumulative_toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
        cumulative_figure_Layout.addWidget(self.cumulative_canvas, alignment=Qt.AlignmentFlag.AlignCenter)
        figure_content_layout.addLayout(cumulative_figure_Layout)

        single_figure_Layout = QVBoxLayout()
        self.single_canvas = MplCanvas(self, width=100, height=4, dpi=100)
        single_toolbar = NavigationToolbar(self.single_canvas, self)
        single_toolbar.setStyleSheet("""
                                                                                       QWidget {
                                                                                           border: None;
                                                                                       }
                                                                                   """)
        single_figure_Layout.addWidget(single_toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
        single_figure_Layout.addWidget(self.single_canvas, alignment=Qt.AlignmentFlag.AlignCenter)
        figure_content_layout.addLayout(single_figure_Layout)

        figure_group_box.setLayout(figure_content_layout)
        figure_group_box.setFixedSize(1150, 400)
        return figure_group_box

    def button_layout_ui(self):
        self.buttons_layout = QHBoxLayout()
        self.start_measurement_btn = QPushButton('Start')
        # self.start_measurement_btn.clicked.connect(self.start_measurement)
        self.stop_btn = QPushButton('Stop')
        # self.stop_btn.clicked.connect(self.stop_measurement)
        self.rst_btn = QPushButton('Reset')
        # self.rst_btn.clicked.connect(self.rst)
        self.start_measurement_btn.setStyleSheet(self.Button_stylesheet)
        self.stop_btn.setStyleSheet(self.Button_stylesheet)
        self.rst_btn.setStyleSheet(self.Button_stylesheet)
        self.buttons_layout.addStretch(4)
        self.buttons_layout.addWidget(self.rst_btn)
        self.buttons_layout.addWidget(self.stop_btn)
        self.buttons_layout.addWidget(self.start_measurement_btn)
        self.button_container = QWidget()
        self.button_container.setLayout(self.buttons_layout)
        self.button_container.setFixedSize(1150, 80)
        return self.button_container

    def bk9205_layout_ui(self):
        self.bk9205_main_layout = QHBoxLayout()

        bk9205_reading_groupbox = QGroupBox("BK9205 Reading")
        bk9205_reading_groupbox.setLayout(self.bk9205_window_reading_ui())
        bk9205_reading_groupbox.setFixedWidth(560)

        bk9205_setting_groupbox = QGroupBox("BK9205 Setting")
        bk9205_setting_groupbox.setLayout(self.bk9205_window_setting_ui())
        bk9205_setting_groupbox.setFixedWidth(560)

        self.bk9205_main_layout.addWidget(bk9205_reading_groupbox)
        self.bk9205_main_layout.addWidget(bk9205_setting_groupbox)
        self.instrument_layout.addLayout(self.bk9205_main_layout)

    def bk9205_window_reading_ui(self):
        self.bk9205_window_reading_layout = QVBoxLayout()
        bk9205_channel_1_layout, self.bk9205_channel_1_state_reading_label, self.bk9205_channel_1_voltage_reading_label, self.bk9205_channel_1_current_reading_label = self.bk9205_reading_channel_layout('1')
        self.bk9205_window_reading_layout.addLayout(bk9205_channel_1_layout)

        bk9205_channel_2_layout, self.bk9205_channel_2_state_reading_label, self.bk9205_channel_2_voltage_reading_label, self.bk9205_channel_2_current_reading_label = self.bk9205_reading_channel_layout('2')
        self.bk9205_window_reading_layout.addLayout(bk9205_channel_2_layout)

        bk9205_channel_3_layout, self.bk9205_channel_3_state_reading_label, self.bk9205_channel_3_voltage_reading_label, self.bk9205_channel_3_current_reading_label = self.bk9205_reading_channel_layout('3')
        self.bk9205_window_reading_layout.addLayout(bk9205_channel_3_layout)
        return self.bk9205_window_reading_layout

    def bk9205_reading_channel_layout(self, current_channel):
        bk9205_channel_layout = QVBoxLayout()
        bk9205_channel_state_layout = QHBoxLayout()
        bk9205_channel_state_label = QLabel(f'Channel {current_channel} State:')
        bk9205_channel_state_label.setFont(self.font)
        bk9205_channel_state_reading_label = QLabel('Unknown')
        bk9205_channel_state_reading_label.setFont(self.font)
        bk9205_channel_state_layout.addWidget(bk9205_channel_state_label)
        bk9205_channel_state_layout.addWidget(bk9205_channel_state_reading_label)
        bk9205_channel_state_layout.addStretch(1)

        bk9205_channel_current_voltage_layout = QHBoxLayout()
        bk9205_channel_voltage_label = QLabel('Voltage:')
        bk9205_channel_voltage_label.setFont(self.font)
        bk9205_channel_voltage_reading_label = QLabel('N/A')
        bk9205_channel_voltage_reading_label.setFont(self.font)
        bk9205_channel_current_label = QLabel('Current:')
        bk9205_channel_current_label.setFont(self.font)
        bk9205_channel_current_reading_label = QLabel('N/A')
        bk9205_channel_current_reading_label.setFont(self.font)
        bk9205_channel_current_voltage_layout.addStretch(1)
        bk9205_channel_current_voltage_layout.addWidget(bk9205_channel_voltage_label)
        bk9205_channel_current_voltage_layout.addWidget(bk9205_channel_voltage_reading_label)
        bk9205_channel_current_voltage_layout.addStretch(1)
        bk9205_channel_current_voltage_layout.addWidget(bk9205_channel_current_label)
        bk9205_channel_current_voltage_layout.addWidget(bk9205_channel_current_reading_label)
        bk9205_channel_current_voltage_layout.addStretch(1)

        bk9205_channel_layout.addLayout(bk9205_channel_state_layout)
        bk9205_channel_layout.addLayout(bk9205_channel_current_voltage_layout)
        return bk9205_channel_layout, bk9205_channel_state_reading_label, bk9205_channel_voltage_reading_label, bk9205_channel_current_reading_label

    def bk9205_window_setting_ui(self):
        self.bk9205_setting_layout = QVBoxLayout()

        bk9205_channel_selection_layout = QHBoxLayout()
        bk9205_channel_selection_label = QLabel('Select Output Channel:')
        bk9205_channel_selection_label.setFont(self.font)
        from QuDAP.GUI.Experiment.measurement import WideComboBox
        self.bk9205_channel_selection_combo_box = WideComboBox()
        self.bk9205_channel_selection_combo_box.setFont(self.font)
        self.bk9205_channel_selection_combo_box.setStyleSheet(self.QCombo_stylesheet)
        self.bk9205_channel_selection_combo_box.addItems(
            ["Select Input Mode", "Channel 1 Voltage", "Channel 1 Current",
             "Channel 2 Voltage", "Channel 2 Current", "Channel 3 Voltage", "Channel 3 Current",
             "Ch1 and Ch2 in series", "Ch1 and Ch2 in parallel"])
        self.bk9205_channel_selection_combo_box.currentIndexChanged.connect(self.bk9205_window_setting_channel_ui)

        bk9205_channel_selection_layout.addWidget(bk9205_channel_selection_label)
        bk9205_channel_selection_layout.addWidget(self.bk9205_channel_selection_combo_box)

        self.bk9205_range_layout = QVBoxLayout()

        self.bk9205_setting_layout.addLayout(bk9205_channel_selection_layout)
        self.bk9205_setting_layout.addLayout(self.bk9205_range_layout)
        return self.bk9205_setting_layout

    def bk9205_window_setting_channel_ui(self):
        bk9205_channel_selection_index = self.bk9205_channel_selection_combo_box.currentIndex()
        self.safe_clear_layout("bk9205_range_layout")
        if bk9205_channel_selection_index == 0:
            self.safe_clear_layout("bk9205_range_layout")
        elif bk9205_channel_selection_index == 1:
            self.bk9205_channel1_voltage_range_setting_layout, self.bk9205_channel1_voltage_range_setting_from, self.bk9205_channel1_voltage_range_setting_to, self.bk9205_channel1_voltage_range_setting_step = self.bk9205_window_setting_voltage_range_ui(type='voltage')
            self.bk9205_range_layout.addLayout(self.bk9205_channel1_voltage_range_setting_layout)
        elif bk9205_channel_selection_index == 2:
            self.bk9205_channel1_current_range_setting_layout, self.bk9205_channel1_current_range_setting_from, self.bk9205_channel1_current_range_setting_to, self.bk9205_channel1_current_range_setting_step = self.bk9205_window_setting_voltage_range_ui(type='current')
            self.bk9205_range_layout.addLayout(self.bk9205_channel1_current_range_setting_layout)
        elif bk9205_channel_selection_index == 3:
            self.bk9205_channel2_voltage_range_setting_layout, self.bk9205_channel2_voltage_range_setting_from, self.bk9205_channel2_voltage_range_setting_to, self.bk9205_channel2_voltage_range_setting_step = self.bk9205_window_setting_voltage_range_ui(
                type='voltage')
            self.bk9205_range_layout.addLayout(self.bk9205_channel2_voltage_range_setting_layout)
        elif bk9205_channel_selection_index == 4:
            self.bk9205_channel2_current_range_setting_layout, self.bk9205_channel2_current_range_setting_from, self.bk9205_channel2_current_range_setting_to, self.bk9205_channel2_current_range_setting_step = self.bk9205_window_setting_voltage_range_ui(
                type='current')
            self.bk9205_range_layout.addLayout(self.bk9205_channel2_current_range_setting_layout)
        elif bk9205_channel_selection_index == 5:
            self.bk9205_channel3_voltage_range_setting_layout, self.bk9205_channel3_voltage_range_setting_from, self.bk9205_channel3_voltage_range_setting_to, self.bk9205_channel3_voltage_range_setting_step = self.bk9205_window_setting_voltage_range_ui(
                type='voltage')
            self.bk9205_range_layout.addLayout(self.bk9205_channel3_voltage_range_setting_layout)
        elif bk9205_channel_selection_index == 6:
            self.bk9205_channel3_current_range_setting_layout, self.bk9205_channel3_current_range_setting_from, self.bk9205_channel3_current_range_setting_to, self.bk9205_channel3_current_range_setting_step = self.bk9205_window_setting_voltage_range_ui(
                type='current')
            self.bk9205_range_layout.addLayout(self.bk9205_channel3_current_range_setting_layout)
        elif bk9205_channel_selection_index == 7:
            self.bk9205_channel1_range_setting_layout, self.bk9205_channel1_range_setting_from, self.bk9205_channel1_range_setting_to, self.bk9205_channel1_range_setting_step = self.bk9205_window_setting_voltage_range_ui('Channel 1')
            self.bk9205_range_layout.addLayout(self.bk9205_channel1_range_setting_layout)
            self.bk9205_channel2_range_setting_layout, self.bk9205_channel2_range_setting_from, self.bk9205_channel2_range_setting_to, self.bk9205_channel2_range_setting_step = self.bk9205_window_setting_voltage_range_ui(
                'Channel 2')
            self.bk9205_range_layout.addLayout(self.bk9205_channel2_range_setting_layout)
        elif bk9205_channel_selection_index == 8:
            self.bk9205_channel4_range_setting_layout, self.bk9205_channel4_range_setting_from, self.bk9205_channel4_range_setting_to, self.bk9205_channel4_range_setting_step = self.bk9205_window_setting_voltage_range_ui(
                'Ch1 & Ch2')
            self.bk9205_range_layout.addLayout(self.bk9205_channel4_range_setting_layout)

        self.bk9205_range_layout.update()
        if self.bk9205_setting_layout.parentWidget():
            self.bk9205_setting_layout.parentWidget().updateGeometry()

    def bk9205_window_setting_voltage_range_ui(self, channel='', type='voltage'):
        bk9205_setting_layout = QVBoxLayout()

        bk9205_range_layout = QHBoxLayout()
        range_from_label = QLabel(f'{channel} Range: From')
        range_from_label.setFont(self.font)
        range_from_entry = QLineEdit()
        range_from_entry.setFont(self.font)
        range_to_label = QLabel(' to ')
        range_to_label.setFont(self.font)
        range_to_entry = QLineEdit()
        range_to_entry.setFont(self.font)
        bk9205_range_unit_combo_box = QComboBox()
        bk9205_range_unit_combo_box.setFont(self.font)
        bk9205_range_unit_combo_box.setStyleSheet(self.QCombo_stylesheet)
        if type == 'voltage':
            bk9205_range_unit_combo_box.addItems(["Select Unit", "V", "kV", "mV", "µV"])
        else:
            bk9205_range_unit_combo_box.addItems(["Select Unit", "A", "mA", "µA"])
        bk9205_range_layout.addWidget(range_from_label)
        bk9205_range_layout.addWidget(range_from_entry)
        bk9205_range_layout.addWidget(range_to_label)
        bk9205_range_layout.addWidget(range_to_entry)
        bk9205_range_layout.addWidget(bk9205_range_unit_combo_box)

        bk9205_step_layout = QHBoxLayout()
        step_label = QLabel('Step Size:')
        step_label.setFont(self.font)
        step_entry = QLineEdit()
        step_entry.setFont(self.font)
        step_unit_combo_box = QComboBox()
        step_unit_combo_box.setFont(self.font)
        step_unit_combo_box.setStyleSheet(self.QCombo_stylesheet)
        if type == 'voltage':
            step_unit_combo_box.addItems(["Select Unit", "V", "kV", "mV", "µV"])
        else:
            step_unit_combo_box.addItems(["Select Unit", "A", "mA", "µA"])
        bk9205_step_layout.addWidget(step_label)
        bk9205_step_layout.addWidget(step_entry)
        bk9205_step_layout.addWidget(step_unit_combo_box)

        bk9205_setting_layout.addLayout(bk9205_range_layout)
        bk9205_setting_layout.addLayout(bk9205_step_layout)
        return bk9205_setting_layout, range_from_entry, range_to_entry, step_entry

    def safe_clear_layout(self, layout_attr_name):
        """Safely clear a layout if it exists"""
        if hasattr(self, layout_attr_name):
            layout = getattr(self, layout_attr_name)
            if layout is not None:
                try:
                    self.clear_layout(layout)
                    return True
                except Exception as e:
                    print(f"Error clearing {layout_attr_name}: {e}")
        return False

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                if child.layout() is not None:
                    self.clear_layout(child.layout())

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = RIGOL_Measurement(None, None)
    window.show()
    sys.exit(app.exec())