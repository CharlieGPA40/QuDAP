import mimetypes

from PyQt6.QtWidgets import (
    QTreeWidgetItem, QMessageBox, QTableWidgetItem, QWidget, QHeaderView, QGroupBox, QFileDialog, QVBoxLayout, QLabel,
QHBoxLayout,QSizePolicy, QTableWidget
, QDialog, QPushButton, QMenu, QScrollArea, QTreeWidget, QWidgetAction, QMainWindow)
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import QPoint, Qt, QThread, QMimeData
import csv
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

import platform
system = platform.system()
if system != "Windows":
    print("Not running on Windows")
    from VSM.qd import *
else:
    version_info = platform.win32_ver()
    version, build, service_pack, extra = version_info
    build_number = int(build.split('.')[2])
    # try:
    #     if version == "10" and build_number >= 22000:
    #         from QuDAP.VSM.qd import *
    #
    #     elif version == "10":
    #         from VSM.qd import *
    #     else:
    #         print("Unknown Windows version")
    # except ImportError:
    try:
        from QuDAP.VSM.qd import *
    except ImportError:
        from VSM.qd import *

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

        self.label = QLabel("Drag and drop a dat file or folder here", self)
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
                paths = [url.toLocalFile() for url in urls]

                # Check if any of the dropped items is a directory
                directories = [path for path in paths if os.path.isdir(path)]
                dat_files = [path for path in paths if os.path.isfile(path) and path.lower().endswith('.dat')]

                if directories:
                    for directory in directories:
                        self.main_window.display_files(directory + '/')

                if dat_files:
                    self.main_window.display_multiple_files(dat_files)

                if not directories and not dat_files:
                    QMessageBox.warning(self, "Invalid File", "Please drop a .dat file or a folder.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def open_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.main_window.display_files(folder_path + '/')

    def reset(self):
        self.previous_folder_path = None

class VSM_Data_Extraction(QMainWindow):

    def __init__(self):
        super().__init__()

        try:
            self.isInit = False
            self.file_in_list = []
            self.init_ui()

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return


    def init_ui(self):
        try:
            if self.isInit == False:
                self.isInit = True
                self.rstpage()
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

                #  ---------------------------- PART 1 --------------------------------\
                with open("GUI/QSS/QButtonWidget.qss", "r") as file:
                    self.Button_stylesheet = file.read()
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
                self.file_selection_display_label = QLabel('Please Upload Files or Directory')
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
                self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                self.file_tree.customContextMenuRequested.connect(self.open_context_menu)

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
                self.fileupload_container.setFixedSize(1150, 300)

                self.table_layout = QVBoxLayout()
                self.table_widget = QTableWidget(100, 100)
                self.table_widget.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
                self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectColumns)
                self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                table_header = self.table_widget.horizontalHeader()
                table_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                self.table_widget.setFixedSize(1150, 350)
                self.table_layout.addWidget(self.table_widget)

                self.btn_layout = QHBoxLayout()

                self.rst_btn = QPushButton("Reset")
                self.rst_btn.clicked.connect(self.rstpage)
                self.export_btn = QPushButton("Export")
                self.export_btn.clicked.connect(self.export_selected_column_data)
                self.export_btn.setToolTip("Export single file")
                self.export_all_btn = QPushButton("Export All")
                self.export_all_btn.clicked.connect(self.export_selected_column_alldata)
                self.export_all_btn.setToolTip("Batch exporting files")
                self.rst_btn.setStyleSheet(self.Button_stylesheet)
                self.export_btn.setStyleSheet(self.Button_stylesheet)
                self.export_all_btn.setStyleSheet(self.Button_stylesheet)
                self.btn_layout.addStretch(2)
                self.btn_layout.addWidget(self.rst_btn)
                self.btn_layout.addWidget(self.export_btn)
                self.btn_layout.addWidget(self.export_all_btn)

                self.VSM_data_extraction_main_layout.addWidget(self.VSM_QD_EXTRACT_label, alignment=Qt.AlignmentFlag.AlignTop)
                self.VSM_data_extraction_main_layout.addWidget(self.fileupload_container)
                self.VSM_data_extraction_main_layout.addLayout(self.table_layout)
                self.VSM_data_extraction_main_layout.addLayout(self.btn_layout)
                self.VSM_data_extraction_main_layout.addStretch(1)

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
                if file_name.endswith('.dat') or file_name.endswith('.DAT'):

                    file_path = os.path.join(root, file_name)
                    self.file_in_list.append(file_path)
                    file_info = os.stat(file_path)
                    file_size_kb = file_info.st_size / 1024  # Convert size to KB
                    file_size_str = f"{file_size_kb:.2f} KB"  # Format size as a string with 2 decimal places
                    # file_type, _ = mimetypes.guess_type(file_path)
                    # file_type = file_type if file_type else "Unknown"
                    file_type = 'application/dat'
                    item = QTreeWidgetItem(self.file_tree, [file_name, file_type, file_size_str, ""])
                    item.setToolTip(0, file_path)
        self.file_tree.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.file_tree.resizeColumnToContents(0)
        self.file_tree.resizeColumnToContents(1)
        self.file_tree.resizeColumnToContents(2)

    def display_multiple_files(self, file_paths):
        current_files = {self.file_tree.topLevelItem(i).text(0): self.file_tree.topLevelItem(i) for i in range(self.file_tree.topLevelItemCount())}
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            if file_name not in current_files:
                self.file_in_list.append(file_path)
                file_info = os.stat(file_path)
                file_size_kb = file_info.st_size / 1024  # Convert size to KB
                file_size_str = f"{file_size_kb:.2f} KB"  # Format size as a string with 2 decimal places
                # file_type, _ = mimetypes.guess_type(file_path)
                # file_type = file_type if file_type else "Unknown"
                file_type = 'application/dat'
                item = QTreeWidgetItem(self.file_tree, [file_name, file_type, file_size_str, ""])
                item.setToolTip(0, file_path)
        self.file_tree.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.file_tree.resizeColumnToContents(0)
        self.file_tree.resizeColumnToContents(1)
        self.file_tree.resizeColumnToContents(2)

        self.file_selection_display_label.setText(f"{self.file_tree.topLevelItemCount()} Files Successfully Uploaded")
        self.file_selection_display_label.setStyleSheet("""
                   color: #4b6172; 
                   font-size: 12px;
                   background-color: #DfE7Ef; 
                   border-radius: 5px; 
                   padding: 5px;
               """)

    def on_item_selection_changed(self):
        selected_items = self.file_tree.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            self.file_path = selected_item.toolTip(0)
            self.open_file_in_table(self.file_path)

    def open_file_in_table(self, file_path):
        if file_path.endswith('.dat') or file_path.endswith('.DAT'):
            try:
                loaded_file = Loadfile(file_path)

                # Access the attributes
                headers = loaded_file.column_headers
                data = loaded_file.data
                self.table_widget.setColumnCount(len(headers))
                self.table_widget.setHorizontalHeaderLabels(headers)
                self.table_widget.setRowCount(len(data))

                for row_idx, row_data in enumerate(data):
                    for col_idx, item in enumerate(row_data):
                        if isinstance(item, np.generic):
                            item = item.item()
                        self.table_widget.setItem(row_idx, col_idx, QTableWidgetItem(str(item)))

                self.table_widget.resizeColumnsToContents()
                self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                for col in range(self.table_widget.columnCount()):
                    self.table_widget.resizeColumnToContents(col)
                table_header = self.table_widget.horizontalHeader()
                table_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                table_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
                # self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                # self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            except Exception as e:
                tb_str = traceback.format_exc()
                QMessageBox.warning(self, "Error", f"{str(e)}{str(tb_str)}")

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
                self.file_tree.clear()
                self.table_widget.clear()
                # self.table_widget = QTableWidget(100, 100)
                self.init_ui()
            except Exception as e:
                return
            self.file_selection_display_label.setText('Please Upload Files or Directory')
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

    def export_selected_column_data(self):
        try:
            selected_columns = set(item.column() for item in self.table_widget.selectedItems())
            selected_columns = sorted(selected_columns)
            column_data = {}
            for col in selected_columns:
                column_header = self.table_widget.horizontalHeaderItem(col).text()
                column_values = []
                for row in range(self.table_widget.rowCount()):
                    item = self.table_widget.item(row, col)
                    column_values.append(item.text() if item else "")
                column_data[column_header] = column_values
            for i in range(len(self.file_path)-1, 0, -1):
                if self.file_path[i] == ".":
                    file_name = self.file_path[: i]
                if self.file_path[i] == "/":
                    file_name = file_name[i+1:]
                    folder_name = self.file_path[:i+1]
                    break

            dialog = QFileDialog(self)
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            dialog.setDirectory(self.file_path)  # Set the default directory
            if dialog.exec():
                folder_name = dialog.selectedFiles()[0]

            export_file_name = '{}/{}.csv'.format(folder_name, file_name)
            self.export_to_csv(column_data, export_file_name)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def export_selected_column_alldata(self):
        try:
            selected_columns = set(item.column() for item in self.table_widget.selectedItems())
            selected_columns = sorted(selected_columns)
            dialog = QFileDialog(self)
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            dialog.setDirectory(self.file_path)  # Set the default directory
            if dialog.exec():
                folder_name = dialog.selectedFiles()[0]

            for file in self.file_in_list:
                # Extracting the data from selected columns
                column_data = {}
                loaded_file = Loadfile(file)
                headers = loaded_file.column_headers
                data = loaded_file.data
                for col in selected_columns:
                    column_header = headers[col]
                    column_values = data[:, col]
                    column_data[column_header] = column_values
                for i in range(len(file) - 1, 0, -1):
                    if file[i] == ".":
                        file_name = file[: i]
                    if file[i] == "/":
                        file_name = file_name[i + 1:]
                        # folder_name = file[:i + 1]
                        break
                export_file_name = '{}/{}.csv'.format(folder_name, file_name)
                with open(export_file_name, 'w', newline='') as file:
                    writer = csv.writer(file)
                    headers = list(column_data.keys())
                    writer.writerow(headers)
                    for row in zip(*column_data.values()):
                        writer.writerow(row)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def export_to_csv(self, column_data, file_name):
        try:
            with open(file_name, 'w', newline='') as file:
                writer = csv.writer(file)
                headers = list(column_data.keys())
                writer.writerow(headers)
                # Write the rows
                for row in zip(*column_data.values()):
                    writer.writerow(row)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def open_context_menu(self, position: QPoint):
        """Open the context menu on right-click."""
        menu = QMenu()

        # Using QWidgetAction instead of QAction
        remove_action = QWidgetAction(self)
        remove_label = QLabel("Remove")
        remove_label.mousePressEvent = lambda event: self.handle_remove_click(event)
        remove_action.setDefaultWidget(remove_label)
        menu.addAction(remove_action)
        menu.exec(self.file_tree.viewport().mapToGlobal(position))

    def handle_remove_click(self, event):
        """Handle right-click on remove label."""
        if event.button() == Qt.MouseButton.RightButton:
            print("right")
            self.remove_selected_item()

    def remove_selected_item(self):
        """Remove the selected item from the tree."""
        selected_item = self.file_tree.currentItem()
        self.file_in_list.remove(selected_item)
        if selected_item:
            index = self.file_tree.indexOfTopLevelItem(selected_item)
            if index != -1:
                self.file_tree.takeTopLevelItem(index)