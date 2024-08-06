from PyQt6.QtWidgets import (
    QApplication, QTabWidget, QWidget, QMainWindow, QListWidgetItem, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QAbstractItemView)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import QSize, Qt
import sys

class FMR(QMainWindow):

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
        self.tab_widget.addTab(self.tab1, "FMR Data Sorting (UNO)")
        self.tab_widget.addTab(self.tab2, "Data Interpolation")
        self.tab_widget.addTab(self.tab3, "Heatmap Generation")
        self.tab_widget.addTab(self.tab4, "Data Fitting")

        # Create layouts for each tab
        self.tab1_layout = QVBoxLayout()
        self.tab2_layout = QVBoxLayout()
        self.tab3_layout = QVBoxLayout()
        self.tab4_layout = QVBoxLayout()

        # Add content to each tab
        # self.uno_widget = sg.General()
        # self.tab1_layout.addWidget(self.uno_widget)
        # self.tab2_layout.addWidget(QLabel("Content of Tab 2"))
        # self.tab3_layout.addWidget(QLabel("Content of Tab 3"))

        # Set the layout for each tab
        self.tab1.setLayout(self.tab1_layout)
        self.tab2.setLayout(self.tab2_layout)
        self.tab3.setLayout(self.tab3_layout)

        # Set the central widget of the main window to the QTabWidget
        self.setCentralWidget(self.tab_widget)