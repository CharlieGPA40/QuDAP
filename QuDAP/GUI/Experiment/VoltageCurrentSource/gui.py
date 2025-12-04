from PyQt6.QtWidgets import (
    QApplication, QTabWidget, QWidget, QMainWindow, QListWidgetItem, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QAbstractItemView)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import QSize, Qt
import sys

try:
    from GUI.Experiment.PPMS import PPMS
    from GUI.FMR.FMRDataInterpolation import FMR_DATA_INTERPOLATION
    from misc.FileExport import FileExport
except ImportError:
    from QuDAP.GUI.Experiment.PPMS import PPMS
    from QuDAP.GUI.FMR.FMRDataInterpolation import FMR_DATA_INTERPOLATION
    from QuDAP.misc.FileExport import FileExport

class VCS_GUI(QMainWindow):

    def __init__(self):
        super().__init__()

        # Create a QTabWidget
        self.tab_widget = QTabWidget()

        # Create tabs
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        self.tab5 = QWidget()
        self.tab6 = QWidget()
        self.tab7 = QWidget()
        self.tab8 = QWidget()
        self.tab9 = QWidget()

        # Add tabs to the QTabWidget
        self.tab_widget.addTab(self.tab1, "PPMS")
        self.tab_widget.addTab(self.tab2, "Lock-in Amplifiers")
        self.tab_widget.addTab(self.tab3, "Voltage & Current Source")
        self.tab_widget.addTab(self.tab4, "Nanovoltmeter")
        self.tab_widget.addTab(self.tab5, "Spectrum Analyzer")
        self.tab_widget.addTab(self.tab6, "RF Source")
        self.tab_widget.addTab(self.tab7, "Measurement")
        # self.tab_widget.addTab(self.tab8, "Data Fitting")
        # self.tab_widget.addTab(self.tab9, "Data Fitting")


        # Create layouts for each tab
        self.tab1_layout = QVBoxLayout()
        self.tab2_layout = QVBoxLayout()
        self.tab3_layout = QVBoxLayout()
        self.tab4_layout = QVBoxLayout()
        self.tab5_layout = QVBoxLayout()
        self.tab6_layout = QVBoxLayout()
        self.tab7_layout = QVBoxLayout()
        self.tab8_layout = QVBoxLayout()
        self.tab9_layout = QVBoxLayout()

        # Add content to each tab
        self.tab1_layout.addWidget(PPMS())
        self.tab2_layout.addWidget(FMR_DATA_INTERPOLATION())

        # Set the layout for each tab
        self.tab1.setLayout(self.tab1_layout)
        self.tab2.setLayout(self.tab2_layout)
        self.tab3.setLayout(self.tab3_layout)

        # Set the central widget of the main window to the QTabWidget
        self.setCentralWidget(self.tab_widget)