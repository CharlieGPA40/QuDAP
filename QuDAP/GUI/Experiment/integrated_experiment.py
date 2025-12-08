from PyQt6.QtWidgets import (QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QListWidget, QStackedWidget,
                             QLabel, QFrame, QTabWidget, QPushButton)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
import sys

try:
    from GUI.Experiment.PPMS import PPMS
    from GUI.Experiment.VoltageCurrentSource.gui import Keithley6221
    from GUI.Experiment.RF.gui import BNC845RF
    from GUI.Experiment.Nanovoltmeter.gui import NV
    from GUI.Experiment.LockInAmplifier.dsp_gui import DSP7265
    from GUI.Experiment.LockInAmplifier.sr_gui import SR830
    from GUI.Experiment.PPMS.gui import PPMS
    from GUI.Experiment.PresetMeasurement.main import MeasurementSystemMainWindow
    from GUI.FMR.FMRDataInterpolation import FMR_DATA_INTERPOLATION
except ImportError:
    from QuDAP.GUI.Experiment.PPMS_old import PPMS
    from QuDAP.GUI.Experiment.VoltageCurrentSource.keithley_gui import Keithley6221
    from QuDAP.GUI.Experiment.RF.gui import BNC845RF
    from QuDAP.GUI.Experiment.Nanovoltmeter.gui import NV
    from QuDAP.GUI.Experiment.LockInAmplifier.dsp_gui import DSP7265
    from QuDAP.GUI.Experiment.LockInAmplifier.sr_gui import SR830
    from QuDAP.GUI.Experiment.PPMS.gui import PPMS
    from QuDAP.GUI.Experiment.PresetMeasurement.main import MeasurementSystemMainWindow


class INTEGRATED_EXPERIMENT(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuDAP - Integrated Experiment")
        self.setMinimumSize(1200, 800)

        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create main tab bar (horizontal)
        self.main_tab_widget = QTabWidget()
        self.main_tab_widget.setDocumentMode(True)

        # Add main tabs
        self.setup_main_tabs()

        main_layout.addWidget(self.main_tab_widget)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Apply styles
        self.apply_styles()

    def setup_main_tabs(self):
        """Setup main tabs"""
        request_text = 'Request new instrument integration at chunli.tang@auburn.edu'
        # Tab 1: PPMS (no subtabs)
        ppms_widget = QWidget()
        ppms_layout = QVBoxLayout()
        ppms_layout.setContentsMargins(10, 10, 10, 10)
        ppms_layout.addWidget(PPMS())
        ppms_widget.setLayout(ppms_layout)
        self.main_tab_widget.addTab(ppms_widget, "PPMS")

        # Tab 2: Lock-in Amplifiers (with subtabs)
        lock_in_tab = self.create_tab_with_subtabs(
            [("Signal Recovery", DSP7265()), ("Stanford Research", SR830()),
             ("Coming Soon", QLabel(request_text))])
        self.main_tab_widget.addTab(lock_in_tab, "Lock-in amplifier")


        # Tab 3: Voltage & Current Source (with subtabs)
        vcs_tab = self.create_tab_with_subtabs([("Keithley", Keithley6221()), ("B&K Precision", QLabel("Monitor content")),
            ("Coming Soon", QLabel(request_text))])
        self.main_tab_widget.addTab(vcs_tab, "Voltage/Current Source")

        # Tab 4: Nanovoltmeter
        nano_tab = self.create_tab_with_subtabs(
            [("Keithley", NV()), ("Coming Soon", QLabel(request_text))])
        self.main_tab_widget.addTab(nano_tab, "Nanovoltmeter")

        # Tab 5: Spectrum Analyzer (with subtabs)
        spectrum_tab = self.create_tab_with_subtabs(
            [("Live View", QLabel("Live spectrum")), ("Sweep", QLabel("Sweep configuration")),
                ("Analysis", QLabel("Analysis tools"))])
        self.main_tab_widget.addTab(spectrum_tab, "Spectrum Analyzer")

        # Tab 6: RF Source
        rf_tab = self.create_tab_with_subtabs([("BNC", BNC845RF()), ("Coming Soon", QLabel("Request new instrument integration at chunli.tang@auburn.edu"))])
        self.main_tab_widget.addTab(rf_tab, "RF Source")

        # Tab 7: Measurement (with subtabs)
        measurement_tab = self.create_tab_with_subtabs(
            [("Setup", MeasurementSystemMainWindow()), ("Run", QLabel("Run measurement")),
                ("Results", QLabel("Results"))])
        self.main_tab_widget.addTab(measurement_tab, "Measurement")

    def create_tab_with_subtabs(self, subtabs):
        """
        Create a tab with subtabs

        Args:
            subtabs: List of tuples (tab_name, widget)
        """
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Create subtab widget
        subtab_widget = QTabWidget()
        subtab_widget.setDocumentMode(True)

        # Add subtabs
        for tab_name, widget in subtabs:
            tab_container = QWidget()
            tab_layout = QVBoxLayout()
            tab_layout.setContentsMargins(10, 10, 10, 10)
            tab_layout.addWidget(widget)
            tab_container.setLayout(tab_layout)
            subtab_widget.addTab(tab_container, tab_name)

        container_layout.addWidget(subtab_widget)
        container.setLayout(container_layout)

        return container

    def apply_styles(self):
        """Apply custom styles matching the uploaded image"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }

            /* Main Tab Widget */
            QTabWidget::pane {
                border: none;
                background-color: #ffffff;
                top: 0px;
            }

            QTabWidget::tab-bar {
                alignment: left;
            }

            /* Main Tabs */
            QTabBar::tab {
                background-color: transparent;
                color: #666666;
                padding: 10px 20px;
                margin-right: 5px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 14px;
                font-weight: 500;
            }

            QTabBar::tab:selected {
                color: #000000;
                border-bottom: 2px solid #ff5733;
                background-color: transparent;
            }

            QTabBar::tab:hover {
                color: #000000;
                background-color: #f5f5f5;
            }

            /* Subtabs - lighter style */
            QTabWidget QTabWidget::pane {
                border: none;
                border-top: 1px solid #e0e0e0;
                background-color: #fafafa;
            }

            QTabWidget QTabWidget QTabBar::tab {
                background-color: transparent;
                color: #888888;
                padding: 8px 16px;
                margin-right: 3px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 13px;
                font-weight: normal;
            }

            QTabWidget QTabWidget QTabBar::tab:selected {
                color: #ff5733;
                border-bottom: 2px solid #ff5733;
                background-color: transparent;
            }

            QTabWidget QTabWidget QTabBar::tab:hover {
                color: #333333;
                background-color: #f0f0f0;
            }

            /* Content area */
            QWidget {
                background-color: #ffffff;
            }

            QLabel {
                color: #333333;
                font-size: 14px;
            }
        """)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = INTEGRATED_EXPERIMENT()
    window.show()
    sys.exit(app.exec())