import mimetypes

from PyQt6.QtWidgets import (
    QTreeWidgetItem, QMessageBox, QApplication, QWidget, QRadioButton, QGroupBox, QFileDialog, QVBoxLayout, QLabel,
    QHBoxLayout,QSizePolicy
, QDialog, QPushButton, QComboBox, QLineEdit, QScrollArea, QTreeWidget, QSplitter, QMainWindow)
from PyQt6.QtGui import QIcon, QFont, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread, QMimeData
import sys
import pandas as pd
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.patches as patches
import numpy as np
import traceback
import os
from ...VSM.qd import Loadfile

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
except ImportError as e:
    print(e)


class DragDropWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.initUI()

    def initUI(self):
        with open("GUI/SHG/QButtonWidget.qss", "r") as file:
            self.Browse_Button_stylesheet = file.read()
        self.setAcceptDrops(True)
        self.previous_folder_path = None
        self.setStyleSheet("background-color: #F5F6FA; border: none;")

        self.label = QLabel("Drag and drop a folder here", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #D4D5D9; font-weight: bold; font-size: 16px;")

        self.button = QPushButton("Browse", self)
        self.button.setStyleSheet(self.Browse_Button_stylesheet)
        self.button.clicked.connect(self.open_folder_dialog)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.label,5)
        main_layout.addWidget(self.button,3, alignment=Qt.AlignmentFlag.AlignRight)
        self.setLayout(main_layout)

        # self.main_widget.setStyleSheet("background-color: #F5F6FA;")

    def dragEnterEvent(self, event: QDragEnterEvent):
        try:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            else:
                event.ignore()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return
    def dropEvent(self, event: QDropEvent):
        try:
            urls = event.mimeData().urls()
            if urls:
                folder_path = urls[0].toLocalFile()
                self.main_window.display_files(folder_path + '/')
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def open_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.main_window.display_files(folder_path + '/')

    def reset(self):
        self.previous_folder_path = None

class Data_Extraction(QMainWindow):

    def __init__(self):
        super().__init__()

        try:
            self.isInit = False
            self.init_ui()

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return


    def init_ui(self):
        try:
            if self.isInit == False:
                self.isInit = True
                with open("GUI/VSM/QButtonWidget.qss", "r") as file:
                    self.Browse_Button_stylesheet = file.read()
                titlefont = QFont("Arial", 20)
                self.font = QFont("Arial", 12)
                self.setStyleSheet("background-color: white;")
                with open("GUI/QSS/QScrollbar.qss", "r") as file:
                    self.scrollbar_stylesheet = file.read()
                    # Create a QScrollArea
                self.scroll_area = QScrollArea()
                self.scroll_area.setWidgetResizable(True)
                self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                self.scroll_area.setStyleSheet(self.scrollbar_stylesheet)
                # Create a widget to hold the main layout
                self.content_widget = QWidget()
                self.scroll_area.setWidget(self.content_widget)

                # Set the content widget to expand
                self.VSM_data_extraction_main_layout = QVBoxLayout(self.content_widget)
                self.VSM_data_extraction_main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

                #  ---------------------------- PART 1 --------------------------------
                self.VSM_QD_EXTRACT_label = QLabel("VSM Data Extraction")
                self.VSM_QD_EXTRACT_label.setFont(titlefont)
                self.VSM_QD_EXTRACT_label.setStyleSheet("""
                                                    QLabel{
                                                        background-color: white;
                                                        }
                                                        """)
                #  ---------------------------- PART 2 --------------------------------
                self.fileUpload_layout = QHBoxLayout()
                self.drag_drop_layout = QVBoxLayout()
                self.file_selection_group_box = QGroupBox("Upload Directory")
                self.file_view_group_box = QGroupBox("View Files")
                self.file_selection_group_box.setStyleSheet("""
                            QGroupBox {

                                max-width: 600px;
                                max-height: 230px;
                            }

                        """)
                self.file_view_group_box.setStyleSheet("""
                                            QGroupBox {

                                                max-width: 650px;
                                                max-height: 230px;
                                            }

                                        """)
                self.file_selection_display_label = QLabel('Please Upload Directory')
                self.file_selection_display_label.setStyleSheet("""
                                   color: white; 
                                   font-size: 12px;
                                   background-color:  #f38d76 ; 
                                    border-radius: 5px; 
                                   padding: 5px;
                               """)
                # self.file_selection_display_label.setWordWrap(True)
                self.drag_drop_widget = DragDropWidget(self)
                self.drag_drop_layout.addWidget(self.drag_drop_widget,4)
                self.drag_drop_layout.addWidget(self.file_selection_display_label,1, alignment=Qt.AlignmentFlag.AlignCenter)
                self.file_selection_group_box.setLayout(self.drag_drop_layout)


                # # Create the file browser area
                self.file_tree = QTreeWidget()
                # self.file_tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                self.file_tree_layout = QHBoxLayout()

                self.file_tree.setHeaderLabels(["Name", "Type", "Size"])
                self.file_tree_layout.addWidget(self.file_tree)
                with open("GUI/SHG/QTreeWidget.qss", "r") as file:
                    self.QTree_stylesheet = file.read()
                self.file_tree.setStyleSheet( self.QTree_stylesheet)
                self.file_view_group_box.setLayout(self.file_tree_layout)
                self.fileUpload_layout.addWidget(self.file_selection_group_box,1)
                self.fileUpload_layout.addWidget(self.file_view_group_box,1)
                self.fileupload_container = QWidget(self)
                self.fileupload_container.setLayout(self.fileUpload_layout)
                self.fileupload_container.setFixedSize(1200,160)

                self.VSM_data_extraction_main_layout.addWidget(self.SHG_General_label, alignment=Qt.AlignmentFlag.AlignTop)
                self.VSM_data_extraction_main_layout.addWidget(self.fileupload_container)
                self.VSM_data_extraction_main_layout.addStretch(1)
                self.rstpage()
                self.setCentralWidget(self.scroll_area)
                # self.scrollArea.setWidget(self.scrollContent)

                # Add the scroll area to the main layout
                # self.master_layout.addWidget(self.scrollArea)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def display_files(self, folder_path):
        self.file_tree.clear()
        self.folder = folder_path
        self.file_selection_display_label.setText("Directory Successfully Uploaded")
        self.file_selection_display_label.setStyleSheet("""
                   color: #4b6172; 
                   font-size: 12px;
                   background-color: #DfE7Ef; 
                   border-radius: 5px; 
                   padding: 5px;
               """)
        for root, dirs, files in os.walk(folder_path):
            for file_name in files:
                if file_name.endswith('.dat'):
                    file_path = os.path.join(root, file_name)
                    file_info = os.stat(file_path)
                    file_size_kb = file_info.st_size / 1024  # Convert size to KB
                    file_size_str = f"{file_size_kb:.2f} KB"  # Format size as a string with 2 decimal places
                    file_type, _ = mimetypes.guess_type(file_path)
                    file_type = file_type if file_type else "Unknown"
                    item = QTreeWidgetItem(self.file_tree, [file_name, file_type, file_size_str, ""])
                    item.setToolTip(0, file_path)
        self.file_tree.resizeColumnToContents(0)
        # self.file_tree.resizeColumnToContents(1)
        self.file_tree.resizeColumnToContents(2)

    def showDialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            folder = folder + "/"
            self.folder = folder
            self.file_selection_display_label.setText("Current Folder: {}".format(self.folder))

    def rstpage(self):
        try:
            try:
                DragDropWidget(self).reset()
                self.Process_button.setEnabled(True)
                self.file_tree.clear()
            except Exception as e:
                return
            self.plot_index = 0
            self.file_selection_display_label.setText('Please Upload Directory')
            self.file_selection_display_label.setStyleSheet("""
                                              color: white; 
                                              font-size: 12px;
                                              background-color:  #f38d76 ; 
                                               border-radius: 5px; 
                                              padding: 5px;
                                          """)

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return