from PyQt6.QtWidgets import (
    QApplication, QTabWidget, QWidget, QMainWindow, QListWidgetItem, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QAbstractItemView)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import QSize, Qt
import sys
import platform

system = platform.system()
if system != "Windows":
    print("Not running on Windows")
    from GUI.VSM.VSMDataExtraction import *
    from GUI.VSM.VSMDataProcessing import *
else:
    version_info = platform.win32_ver()
    version, build, service_pack, extra = version_info
    build_number = int(build.split('.')[2])
    if version == "10" and build_number >= 22000:
        # print("Windows 11")
        from GUI.VSM.VSMDataExtraction import *
        from GUI.VSM.VSMDataProcessing import *
    elif version == "10":
        # print("Windows 10")
        from GUI.VSM.VSMDataExtraction import *
        from GUI.VSM.VSMDataProcessing import *
    else:
        print("Unknown Windows version")

class VSM(QMainWindow):

    def __init__(self):
        super().__init__()

        # Create a QTabWidget
        self.tab_widget = QTabWidget()

        # Create tabs
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()

        # Add tabs to the QTabWidget
        self.tab_widget.addTab(self.tab1, "QD Data File Extraction")
        self.tab_widget.addTab(self.tab2, "Data Processing")
        self.tab_widget.addTab(self.tab3, "Background Removal")
        # self.tab_widget.addTab(self.tab4, "Data Fitting")

        # Create layouts for each tab
        self.tab1_layout = QVBoxLayout()
        self.tab2_layout = QVBoxLayout()
        self.tab3_layout = QVBoxLayout()
        # self.tab4_layout = QVBoxLayout()

        # Add content to each tab
        self.qd_data_extract_widget = VSM_Data_Extraction()
        self.qd_data_proc_widget = VSM_Data_Processing()
        self.tab1_layout.addWidget(self.qd_data_extract_widget)
        self.tab2_layout.addWidget(self.qd_data_proc_widget)
        # self.tab2_layout.addWidget(QLabel("Content of Tab 2"))
        # self.tab3_layout.addWidget(QLabel("Content of Tab 3"))

        # Set the layout for each tab
        self.tab1.setLayout(self.tab1_layout)
        self.tab2.setLayout(self.tab2_layout)
        self.tab3.setLayout(self.tab3_layout)

        # Set the central widget of the main window to the QTabWidget
        self.setCentralWidget(self.tab_widget)