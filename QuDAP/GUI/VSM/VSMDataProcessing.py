import mimetypes

from PyQt6.QtWidgets import (
    QTreeWidgetItem, QMessageBox, QTableWidgetItem, QWidget, QHeaderView, QGroupBox, QFileDialog, QVBoxLayout, QLabel,
    QHBoxLayout, QSizePolicy, QTableWidget
, QLineEdit, QPushButton, QMenu, QScrollArea, QTreeWidget, QWidgetAction, QMainWindow, QRadioButton, QCheckBox)
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
    if version == "10" and build_number >= 22000:
        print("Windows 11")
        from QuDAP.VSM.qd import *
    elif version == "10":
        print("Windows 10")
        from VSM.qd import *
    else:
        print("Unknown Windows version")


try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
except ImportError as e:
    print(e)

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=10, dpi=1000):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        # if polar:
        self.fig.clear()
        self.ax = self.fig.add_subplot(111, projection='rectilinear')

        super(MplCanvas, self).__init__(self.fig)

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

        self.label = QLabel("Drag and drop a csv file or folder here", self)
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
                dat_files = [path for path in paths if os.path.isfile(path) and path.lower().endswith('.csv')]

                if directories:
                    for directory in directories:
                        self.main_window.display_files(directory + '/')

                if dat_files:
                    self.main_window.display_multiple_files(dat_files)

                if not directories and not dat_files:
                    QMessageBox.warning(self, "Invalid File", "Please drop a .csv file or a folder.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def open_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.main_window.display_files(folder_path + '/')

    def reset(self):
        self.previous_folder_path = None

class VSM_Data_Processing(QMainWindow):
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
                self.VSM_QD_EXTRACT_label = QLabel("VSM Data Processing")
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
                self.drag_drop_layout.addWidget(self.file_selection_display_label, 1, alignment=Qt.AlignmentFlag.AlignCenter)
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

                self.figure_layout = QHBoxLayout()
                self.raw_canvas_layout = QVBoxLayout()
                self.raw_canvas = MplCanvas(self, width=5, height=4, dpi=100)
                self.raw_toolbar = NavigationToolbar(self.raw_canvas, self)
                self.raw_toolbar.setStyleSheet("""
                                                                              QWidget {
                                                                                  border: None;
                                                                              }
                                                                          """)
                self.raw_canvas.ax.set_title("Hysteresis Loop")
                self.raw_canvas_layout.addWidget(self.raw_toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
                self.raw_canvas_layout.addWidget(self.raw_canvas)

                self.fit_canvas_layout = QVBoxLayout()
                self.fit_canvas = MplCanvas(self, width=5, height=4, dpi=100)
                self.fit_toolbar = NavigationToolbar(self.fit_canvas, self)
                self.fit_toolbar.setStyleSheet("""
                                                                                              QWidget {
                                                                                                  border: None;
                                                                                              }
                                                                                          """)
                self.fit_canvas.ax.set_title("Fitting")
                self.fit_canvas_layout.addWidget(self.fit_toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
                self.fit_canvas_layout.addWidget(self.fit_canvas)

                self.summary_canvas_layout = QVBoxLayout()
                self.summary_canvas = MplCanvas(self, width=5, height=4, dpi=100)
                self.summary_toolbar = NavigationToolbar(self.summary_canvas, self)
                self.summary_toolbar.setStyleSheet("""
                                                                                                              QWidget {
                                                                                                                  border: None;
                                                                                                              }
                                                                                                          """)
                self.summary_canvas.ax.set_title("Fitting Summary")
                self.summary_canvas_layout.addWidget(self.summary_toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
                self.summary_canvas_layout.addWidget(self.summary_canvas)

                self.figure_layout.addLayout(self.raw_canvas_layout)
                self.figure_layout.addLayout(self.fit_canvas_layout)
                self.figure_layout.addLayout(self.summary_canvas_layout)
                self.figure_container = QWidget(self)
                self.figure_container.setLayout(self.figure_layout)
                self.figure_container.setFixedSize(1150, 380)

                self.fitting_parameter_layout = QHBoxLayout()
                self.plot_control_group_box = QGroupBox("Plot Control")
                self.fit_control_group_box = QGroupBox("Fit Control")
                self.fit_summary_group_box = QGroupBox("Fit Summary")
                self.fitting_parameter_layout.addWidget(self.plot_control_group_box)
                self.fitting_parameter_layout.addWidget(self.fit_control_group_box)
                self.fitting_parameter_layout.addWidget(self.fit_summary_group_box)

                self.plot_control_layout = QVBoxLayout()
                self.fit_control_layout = QVBoxLayout()
                self.fit_summary_layout = QVBoxLayout()

                self.raw_plot_check_box = QCheckBox("Show Raw Data")
                self.processed_plot_check_box = QCheckBox("Show Processed Data")
                self.area_plot_check_box = QCheckBox("Show Area")
                self.x_correction_check_box = QCheckBox("Show Hc corrected plot")
                self.y_correction_check_box = QCheckBox("Show Ms corrected plot")
                self.xy_correction_check_box = QCheckBox("Show both corrected plot")

                self.plot_control_layout.addWidget(self.raw_plot_check_box)
                self.plot_control_layout.addWidget(self.processed_plot_check_box)
                self.plot_control_layout.addWidget(self.area_plot_check_box)
                self.plot_control_layout.addWidget(self.x_correction_check_box)
                self.plot_control_layout.addWidget(self.y_correction_check_box)
                self.plot_control_layout.addWidget(self.xy_correction_check_box)

                self.plot_control_group_box.setLayout(self.plot_control_layout)

                self.area_fit_results_layout = QHBoxLayout()
                self.area_text_label = QLabel('Area: ')
                self.area_entry = QLineEdit()
                self.area_fit_results_layout.addWidget(self.area_text_label)
                self.area_fit_results_layout.addWidget(self.area_entry)
                self.Hc_fit_results_layout = QHBoxLayout()
                self.hc_text_label = QLabel('Coercivity: ')
                self.hc_entry = QLineEdit()
                self.Hc_fit_results_layout.addWidget(self.hc_text_label)
                self.Hc_fit_results_layout.addWidget(self.hc_entry)
                self.ms_fit_results_layout = QHBoxLayout()
                self.ms_text_label = QLabel('Saturation Magnetization: ')
                self.ms_entry = QLineEdit()
                self.ms_fit_results_layout.addWidget(self.ms_text_label)
                self.ms_fit_results_layout.addWidget(self.ms_entry)
                self.eb_fit_results_layout = QHBoxLayout()
                self.eb_text_label = QLabel('Exchange Bias: ')
                self.eb_entry = QLineEdit()
                self.eb_fit_results_layout.addWidget(self.eb_text_label)
                self.eb_fit_results_layout.addWidget(self.eb_entry)

                self.fit_control_layout.addLayout(self.area_fit_results_layout)
                self.fit_control_layout.addLayout(self.Hc_fit_results_layout)
                self.fit_control_layout.addLayout(self.ms_fit_results_layout)
                self.fit_control_layout.addLayout(self.eb_fit_results_layout)

                self.fit_control_group_box.setLayout(self.fit_control_layout)


                self.area_check_box = QCheckBox("Area")
                self.coercivity_check_box = QCheckBox("Coercivity")
                self.ms_check_box = QCheckBox("Saturation Magnetization")
                self.eb_check_box = QCheckBox("Exchange Bias")

                self.fit_summary_layout.addWidget(self.area_check_box)
                self.fit_summary_layout.addWidget(self.coercivity_check_box)
                self.fit_summary_layout.addWidget(self.ms_check_box)
                self.fit_summary_layout.addWidget(self.eb_check_box)

                self.fit_summary_group_box.setLayout(self.fit_summary_layout)

                self.plot_control_group_box.setFixedSize(380,200)
                self.fit_control_group_box.setFixedSize(380,200)
                self.fit_summary_group_box.setFixedSize(380,200)

                self.VSM_data_extraction_main_layout.addWidget(self.VSM_QD_EXTRACT_label, alignment=Qt.AlignmentFlag.AlignTop)
                self.VSM_data_extraction_main_layout.addWidget(self.fileupload_container)
                self.VSM_data_extraction_main_layout.addWidget(self.figure_container)
                self.VSM_data_extraction_main_layout.addLayout(self.fitting_parameter_layout)
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
                if file_name.endswith('.csv'):

                    file_path = os.path.join(root, file_name)
                    self.file_in_list.append(file_path)
                    file_info = os.stat(file_path)
                    file_size_kb = file_info.st_size / 1024  # Convert size to KB
                    file_size_str = f"{file_size_kb:.2f} KB"  # Format size as a string with 2 decimal places
                    # file_type, _ = mimetypes.guess_type(file_path)
                    # file_type = file_type if file_type else "Unknown"
                    file_type = 'csv'
                    item = QTreeWidgetItem(self.file_tree, [file_name, file_type, file_size_str, ""])
                    item.setToolTip(0, file_path)
        self.process_data()
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
                file_type = 'csv'
                item = QTreeWidgetItem(self.file_tree, [file_name, file_type, file_size_str, ""])
                item.setToolTip(0, file_path)
        self.process_data()
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
                self.table_widget = QTableWidget(100, 100)
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

    def export_selected_column_alldata(self):
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

    def export_to_csv(self, column_data, file_name):
        """Export selected column data to a CSV file."""
        with open(file_name, 'w', newline='') as file:
            writer = csv.writer(file)
            headers = list(column_data.keys())
            writer.writerow(headers)
            # Write the rows
            for row in zip(*column_data.values()):
                writer.writerow(row)

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

    def run(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setDirectory(self.file_path)  # Set the default directory
        if dialog.exec():
            self.folder_selected = dialog.selectedFiles()[0]
        self.folder_selected = self.folder_selected + "/"
        self.ProcessedDatapath = self.folder_selected + 'Processed_Data'  # Processed data directory
        isExist = os.path.exists(self.ProcessedDatapath)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(self.ProcessedDatapath)
            self.process_raw()
            self.process_data()
        else:
            self.process_data()

    def process_raw(self):
        dat_list_path = self.folder_selected + '*.DAT'
        dat_list = glob.glob(dat_list_path)
        number_DAT = len(dat_list)

        for j in range(0, number_DAT, 1):
            for i in range(len(dat_list[j]) - 1, 0, -1):
                if dat_list[j][i] == '/':
                    dat_list[j] = dat_list[j][i + 1:]
                    break

        for j in range(0, number_DAT, 1):
            if dat_list[j] == 'zfc.DAT' or dat_list[j] == 'fc.DAT' or dat_list[j] == 'ZFC.DAT' or dat_list[j] == 'FC.DAT':
                vsm_data = Stoner.Data.load(self.folder_selected + dat_list[j],
                                            filetype=Stoner.formats.instruments.QDFile)
                vsm_data.setas(x="Temperature (K)", y="Moment (emu)", z="Temperature (K)")
                vsm_data = vsm_data.del_column(vsm_data.setas.not_set)
                vsm_data = Stoner.formats.generic.CSVFile(vsm_data)
                if dat_list[j] == 'ZFC.DAT' or dat_list[j] == 'zfc.DAT':
                    file_name = 'zfc'
                elif dat_list[j] == 'FC.DAT' or dat_list[j] == 'fc.DAT':
                    file_name = 'fc'
                vsm_data.save(self.ProcessedDatapath + '/{}.csv'.format(file_name))
            else:
                vsm_data = Stoner.Data.load(self.folder_selected + dat_list[j],
                                            filetype=Stoner.formats.instruments.QDFile)
                temp = vsm_data.column(['Temperature (K)', 0])
                temp = round(temp[0][0])
                vsm_data.setas(x="Magnetic Field (Oe)", y="Moment (emu)", z="Temperature (K)")
                vsm_data = vsm_data.del_column(vsm_data.setas.not_set)
                # temp = int(np.ceil(temp[0][0]))
                vsm_data = Stoner.formats.generic.CSVFile(vsm_data)
                vsm_data.save(self.ProcessedDatapath + '/{}K.csv'.format(temp))

    def y_range(self, number_CSV, csv_list_path, csv_list, plot_y_range_positive, plot_y_range_negative):
        for j in range(0, number_CSV, 1):
            Temp_Hyst = pd.read_csv(csv_list_path + csv_list[j], header=None, engine='c')
            y = Temp_Hyst.iloc[:, 1]
            YMax = y.max(axis=0)
            YMin = y.min(axis=0)
            if YMax > plot_y_range_positive:
                plot_y_range_positive = YMax
            if YMin < plot_y_range_negative:
                plot_y_range_negative = YMin

        if abs(plot_y_range_positive) > abs(plot_y_range_negative):
            hyst_lim = abs(plot_y_range_positive)
        else:
            hyst_lim = abs(plot_y_range_negative)
        return hyst_lim

    def Process_individual_Hys(self, number_CSV, csv_list, csv_list_path, hyst_lim, folder):
        for j in range(0, number_CSV, 1):


            for i in range(len(csv_list[j]) - 1, 0, -1):
                if csv_list[j][i] == 'K':
                    Cur_Temp = csv_list[j][:i]
                    break
            Temp_Hyst = pd.read_csv(csv_list_path + csv_list[j], header=0, engine='c')
            x = Temp_Hyst.iloc[:, 0]
            y = Temp_Hyst.iloc[:, 1]
            fig, ax_hys = plt.subplots()
            ax_hys.scatter(x, y, color='black', s=0.5)
            ax_hys.set_xlabel('Magnetic Field (Oe)', fontsize=14)
            ax_hys.set_ylabel('Magnetic Moment (emu)', fontsize=14)
            ax_hys.set_ylim(bottom=hyst_lim * -1.05, top=hyst_lim * 1.05)
            plt.title('{} K Hysteresis Loop'.format(Cur_Temp), pad=10, wrap=True, fontsize=14)
            plt.tight_layout()
            plt.savefig(folder + "/{}K_Hysteresis.png".format(Cur_Temp))
            plt.close()


    def process_data(self):
        self.ProcessedRAW = self.folder_selected + 'Processed_Graph'
        isExist = os.path.exists(self.ProcessedRAW)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(self.ProcessedRAW)

        self.ProcCal = self.folder_selected + 'Proc_Cal'
        isExist = os.path.exists(self.ProcCal)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(self.ProcCal)

        csv_list_path = self.folder_selected + 'Processed_Data/'
        csv_list = os.listdir(csv_list_path)
        number_CSV = len(csv_list)
        plot_y_range_positive = 0
        plot_y_range_negative = 0

        for j in range(0, number_CSV, 1):
            if csv_list[j] != 'zfc.csv' or csv_list[j] != 'fc.csv':
                Temp_Hyst = pd.read_csv(csv_list_path + csv_list[j], header=0, engine='c')
                YMax = Temp_Hyst['Moment (emu)'].max(axis=0)
                YMin = Temp_Hyst['Moment (emu)'].min(axis=0)
                # YMax = Temp_Hyst.iloc[:, 2].max(axis=0)
                # YMin = Temp_Hyst.iloc[:, 2].min(axis=0)
                # Loop to find the peak and valley
                if YMax > plot_y_range_positive:
                    plot_y_range_positive = YMax
                if YMin < plot_y_range_negative:
                    plot_y_range_negative = YMin

        if abs(plot_y_range_positive) > abs(plot_y_range_negative):
            hyst_lim = abs(plot_y_range_positive)
        else:
            hyst_lim = abs(plot_y_range_negative)

        area_df = pd.DataFrame(columns=['Temperature', 'Area'])
        Ms_df = pd.DataFrame(columns=['Temperature', 'Saturation Field','Upper','Lower'])
        Coercivity_df = pd.DataFrame(columns=['Temperature', 'Coercivity'])
        for j in range(0, number_CSV, 1):
            self.hys_folder = self.ProcessedRAW + '/Hysteresis'
            isExist = os.path.exists(self.hys_folder)
            if not isExist:  # Create a new directory because it does not exist
                os.makedirs(self.hys_folder)
            if csv_list[j] == 'zfc.csv' or csv_list[j] == 'fc.csv':
                ZFC_FC = pd.read_csv(csv_list_path + csv_list[j], header=0, engine='c')
                x = ZFC_FC.iloc[:, 0]
                y = ZFC_FC.iloc[:, 1]
                plt.rc('xtick', labelsize=13)  # fontsize of the tick labels
                plt.rc('ytick', labelsize=13)  # fontsize of the tick labels
                fig, ax = plt.subplots()
                ax.scatter(x, y, color='black', s=0.5)
                ax.set_xlabel('Magnetic Field (Oe)', fontsize=14)
                ax.set_ylabel('Magnetic Moment (emu)', fontsize=14)
                ax.set_ylim(bottom=hyst_lim * -1.05, top=hyst_lim * 1.05)
                if csv_list[j] == 'zfc.csv':
                    plt.title('Zero Field Cooled'.format(Cur_Temp), pad=10, wrap=True, fontsize=14)
                    plt.tight_layout()
                    plt.savefig(self.hys_folder + "/zfc.png")
                else:
                    plt.title('Field Cooled'.format(Cur_Temp), pad=10, wrap=True, fontsize=14)
                    plt.tight_layout()
                    plt.savefig(self.hys_folder + "/fc.png")
                plt.close()
            else:
                for i in range(len(csv_list[j]) - 1, 0, -1):
                    if csv_list[j][i] == 'K':
                        Cur_Temp = csv_list[j][:i]
                        break

                Temp_Hyst = pd.read_csv(csv_list_path + csv_list[j], header=0, engine='c')
                thermal = Temp_Hyst.iloc[:, 0]
                x = Temp_Hyst.iloc[:, 1]
                y = Temp_Hyst.iloc[:, 2]

                Temp_Hyst_area = Temp_Hyst.dropna()
                x_drop = Temp_Hyst_area.iloc[:, 1]
                y_drop = Temp_Hyst_area.iloc[:, 2]
                area = np.trapz(y_drop, x_drop)
                area_temp = pd.DataFrame({'Temperature': [int(Cur_Temp)], 'Area': [abs(area)]})
                area_df = pd.concat([area_df, area_temp], ignore_index=True)

                plt.plot(x_drop, y_drop)
                # Fill the area under the curve with color
                plt.fill_between(x_drop, y_drop, alpha=0.3)
                # Add a legend with the calculated area
                plt.legend()
                plt.title("Trapezoidal Area")
                plt.xlabel('Temperature (K)')
                plt.ylabel('Magnetic Moment (emu)')
                # plt.grid(True)
                plt.tight_layout()
                self.Area_folder = self.ProcessedRAW + '/Area'
                isExist = os.path.exists(self.Area_folder)
                if not isExist:  # Create a new directory because it does not exist
                    os.makedirs(self.Area_folder)
                plt.savefig(self.Area_folder + "/{}K_Area.png".format(Cur_Temp))
                plt.close()

                thermal = 100 * (thermal - int(Cur_Temp)) / int(Cur_Temp)

                plt.rc('xtick', labelsize=13)  # fontsize of the tick labels
                plt.rc('ytick', labelsize=13)  # fontsize of the tick labels
                fig, ax_thermal = plt.subplots()
                ax_thermal.scatter(x, thermal, color='black', s=0.5)
                ax_thermal.set_xlabel('Magnetic Field (Oe)', fontsize=14)
                ax_thermal.set_ylabel('Temperature Fluctuation (%)', fontsize=14)
                plt.title('{} K Hysteresis Loop Temperature'.format(Cur_Temp), pad=10, wrap=True, fontsize=14)
                plt.tight_layout()
                self.ther_folder = self.ProcessedRAW + '/Thermal_difference'
                isExist = os.path.exists(self.ther_folder)
                if not isExist:  # Create a new directory because it does not exist
                    os.makedirs(self.ther_folder)
                plt.savefig(self.ther_folder + "/{}K_Thermal.png".format(Cur_Temp))
                plt.close()

                fig, ax_hys = plt.subplots()
                ax_hys.scatter(x, y, color='black', s=0.5)
                ax_hys.set_xlabel('Magnetic Field (Oe)', fontsize=14)
                ax_hys.set_ylabel('Magnetic Moment (emu)', fontsize=14)
                ax_hys.set_ylim(bottom=hyst_lim * -1.05, top=hyst_lim * 1.05)
                plt.title('{} K Hysteresis Loop'.format(Cur_Temp), pad=10, wrap=True, fontsize=14)
                plt.tight_layout()
                plt.savefig(self.hys_folder + "/{}K_Hysteresis.png".format(Cur_Temp))
                plt.close()

                index = Temp_Hyst.iloc[:, 1].idxmin(axis=0)
                list1 = Temp_Hyst.iloc[:index].dropna()
                list2 = Temp_Hyst.iloc[index:].dropna()

                list1_x = list1["Magnetic Field (Oe)"].values
                list1_y = list1["Moment (emu)"].values
                list2_x = list2["Magnetic Field (Oe)"].values
                list2_y = list2["Moment (emu)"].values

                self.split_folder = self.ProcessedRAW + '/Split_folder'
                isExist = os.path.exists(self.split_folder)
                if not isExist:  # Create a new directory because it does not exist
                    os.makedirs(self.split_folder)
                fig, axs = plt.subplots()
                plt.title("{}K Split Hysteresis".format(Cur_Temp), pad=10, wrap=True, fontsize=14)
                axs.scatter(list1_x, list1_y, s=10)
                axs.scatter(list2_x, list2_y, s=10, alpha=0.1)
                ax_hys.set_xlabel('Magnetic Field (Oe)', fontsize=14)
                ax_hys.set_ylabel('Magnetic Moment (emu)', fontsize=14)
                # axs.fill_between(x, list1_y, list2_y)
                plt.tight_layout()
                plt.savefig(self.split_folder + "/{}K_spliting.png".format(Cur_Temp))
                plt.close()
                list1_x_concat = pd.Series(list1_x)
                list1_y_concat = pd.Series(list1_y)
                list2_x_concat = pd.Series(list2_x)
                list2_y_concat = pd.Series(list2_y)
                spilt_df = pd.concat([list1_x_concat, list1_y_concat,list2_x_concat,list2_y_concat], ignore_index=True, axis=1)
                spilt_df.to_csv(self.ProcCal + '/{}K_spliting_org.csv'.format(Cur_Temp), index=False,
                                header=False)
                self.fit_folder = self.ProcessedRAW + '/Fitted_Raw'
                isExist = os.path.exists(self.fit_folder)
                if not isExist:  # Create a new directory because it does not exist
                    os.makedirs(self.fit_folder)

                def L_d(params, x, data=None):
                    m = params['m']
                    s = params['s']
                    c = params['c']
                    a = params['a']
                    b = params['b']
                    model = m * np.tanh(s * (x - c)) + a * x + b
                    if data is None:
                        return model
                    return model - data

                # Create a Parameters object
                params = lmfit.Parameters()
                params.add('m', value=0.00001)
                params.add('s', value=0.001)
                params.add('c', value=190)
                params.add('a', value=1)
                params.add('b', value=1)
                result_lower = lmfit.minimize(L_d, params, args=(list1_x,), kws={'data': list1_y})
                result_upper = lmfit.minimize(L_d, params, args=(list2_x,), kws={'data': list2_y})
                lower_slope = result_lower.params['a'].value
                upper_slope = result_upper.params['a'].value
                lower_offset = result_lower.params['b'].value
                upper_offset = result_upper.params['b'].value
                final_slope = np.mean([lower_slope, upper_slope])
                final_offset = np.mean([lower_offset, upper_offset])
                slope_final = final_slope * list1_x + final_offset

                # Plot the fitted Graph with slope
                fig, ax = plt.subplots()
                ax.scatter(list1_x, list1_y, label='Data', s=0.5, alpha=0.5, color='green')
                ax.scatter(list2_x, list2_y, s=0.5, alpha=0.5, color='green')
                ax.plot(list1_x, result_lower.residual + list1_y, label='Fitted tanh', color='coral', linewidth=3)
                ax.plot(list2_x, result_upper.residual + list2_y, color='coral', linewidth=3)
                ax.plot(list1_x, slope_final, 'r--', label='Final Slope', linewidth=1, )
                plt.xlabel('Magnetic Field (Oe)', fontsize=14)
                plt.ylabel('Moment (emu)', fontsize=14)
                plt.title("{} Time {}K Fitted Hysteresis".format('First', Cur_Temp), pad=10, wrap=True, fontsize=14)
                plt.legend()
                plt.tight_layout()
                plt.savefig(self.fit_folder + "/{}_{}K_fitted_data.png".format('First', Cur_Temp))
                plt.close()

                # First iteration of linear background removal full trace
                y_slope_removal = y - final_slope * x - final_offset

                self.slope_removal_folder = self.ProcessedRAW + '/Slope_Removal'
                isExist = os.path.exists(self.slope_removal_folder)
                if not isExist:  # Create a new directory because it does not exist
                    os.makedirs(self.slope_removal_folder)

                # Plot the fitted Graph with slope (Entire)
                plt.rc('xtick', labelsize=13)  # fontsize of the tick labels
                plt.rc('ytick', labelsize=13)  # fontsize of the tick labels
                fig, ax = plt.subplots()
                ax.scatter(x, y_slope_removal, color='black', s=0.5, label='slope removal')
                ax.set_xlabel('Magnetic Field (Oe)', fontsize=14)
                ax.set_ylabel('Magnetic Moment (emu)', fontsize=14)
                plt.title('{} Time {} K Hysteresis Loop Slope Removal Full Trace'.format('First', Cur_Temp), pad=15, wrap=True,
                          fontsize=14)
                plt.tight_layout()
                plt.savefig(
                    self.slope_removal_folder + "/{}_{}K_Slope_Removal_Hysteresis.png".format('First', Cur_Temp))
                plt.close()

                # First iteration of linear background removal half trace
                y_slope_removal_lower = list1_y - final_slope * list1_x - final_offset
                y_slope_removal_upper = list2_y - final_slope * list2_x - final_offset

                # Second iteration of linear background removal fitting
                result_lower_second = lmfit.minimize(L_d, params, args=(list1_x,), kws={'data': y_slope_removal_lower})
                result_upper_second = lmfit.minimize(L_d, params, args=(list2_x,), kws={'data': y_slope_removal_upper})
                lower_slope = result_lower_second.params['a'].value
                upper_slope = result_upper_second.params['a'].value
                lower_offset = result_lower_second.params['b'].value
                upper_offset = result_upper_second.params['b'].value
                final_slope = (lower_slope + upper_slope) / 2
                final_offset = (lower_offset + upper_offset) / 2
                slope_final = final_slope * list1_x + final_offset
                # Plot the original data and the fitted curve
                fig, ax = plt.subplots()
                ax.scatter(list1_x, y_slope_removal_lower, label='Data', s=0.5, alpha=0.5, color='green')
                ax.scatter(list2_x, y_slope_removal_upper, s=0.5, alpha=0.5, color='green')
                ax.plot(list1_x, result_lower.residual + y_slope_removal_lower, label='Fitted tanh', color='coral', linewidth=3)
                ax.plot(list2_x, result_upper.residual + y_slope_removal_upper, color='coral', linewidth=3)
                ax.plot(list1_x, slope_final, 'r--', label='Final Slope', linewidth=1, )
                plt.xlabel('Magnetic Field (Oe)', fontsize=14)
                plt.ylabel('Moment (emu)', fontsize=14)
                plt.title("{} Time {}K Fitted Hysteresis".format('Second', Cur_Temp), pad=10, wrap=True, fontsize=14)
                plt.legend()
                plt.tight_layout()
                self.fit_folder = self.ProcessedRAW + '/Fitted_Raw'
                isExist = os.path.exists(self.fit_folder)
                if not isExist:  # Create a new directory because it does not exist
                    os.makedirs(self.fit_folder)
                plt.savefig(self.fit_folder + "/{}_{}K_fitted_data.png".format('Second', Cur_Temp))
                plt.close()

                # Second iteration of linear background removal entire trace
                y_slope_removal = y_slope_removal - final_slope * x - final_offset
                plt.rc('xtick', labelsize=13)  # fontsize of the tick labels
                plt.rc('ytick', labelsize=13)  # fontsize of the tick labels
                fig, ax = plt.subplots()
                ax.scatter(x, y_slope_removal, color='black', s=0.5, label='slope removal')
                ax.set_xlabel('Magnetic Field (Oe)', fontsize=14)
                ax.set_ylabel('Magnetic Moment (emu)', fontsize=14)
                plt.title('{} Time {} K Hysteresis Loop Slope Removal'.format('Second', Cur_Temp), pad=10, wrap=True,
                          fontsize=14)
                plt.tight_layout()
                self.slope_removal_folder = self.ProcessedRAW + '/Slope_Removal'
                isExist = os.path.exists(self.slope_removal_folder)
                if not isExist:  # Create a new directory because it does not exist
                    os.makedirs(self.slope_removal_folder)
                plt.savefig(
                    self.slope_removal_folder + "/{}_{}K_Slope_Removal_Hysteresis.png".format('Second', Cur_Temp))
                plt.close()

                # Second iteration of linear background removal half trace
                y_slope_removal_lower = y_slope_removal_lower - final_slope * list1_x - final_offset
                y_slope_removal_upper = y_slope_removal_upper - final_slope * list2_x - final_offset

                y_slope_removal_lower_concat = pd.Series(y_slope_removal_lower)
                y_slope_removal_upper_concat = pd.Series(y_slope_removal_upper)
                spilt_df = pd.concat([list1_x_concat,y_slope_removal_lower_concat, list2_x_concat,y_slope_removal_upper_concat], ignore_index=True, axis=1)
                spilt_df.to_csv(self.ProcCal + '/{}K_spliting_second_slope_removal.csv'.format(Cur_Temp), index=False,
                                header=False)


                # -------------------------------------------------------------
                #  Fit the slope removal data and find the Ms and x0
                # -------------------------------------------------------------
                result_lower_slope_removal = lmfit.minimize(L_d, params, args=(list1_x,),
                                                            kws={'data': y_slope_removal_lower})
                result_upper_slope_removal = lmfit.minimize(L_d, params, args=(list2_x,),
                                                            kws={'data': y_slope_removal_upper})

                # Plot the original data and the fitted curve
                plt.scatter(list1_x, y_slope_removal_lower, label='Data', s=0.5, alpha=0.5, color='green')
                plt.scatter(list2_x, y_slope_removal_upper, s=0.5, alpha=0.5, color='green')
                plt.plot(list1_x, result_lower_slope_removal.residual + y_slope_removal_lower,
                         label='Fitted tanh', color='coral', linewidth=3)
                plt.plot(list2_x, result_upper_slope_removal.residual + y_slope_removal_upper,
                         color='coral', linewidth=3)
                plt.xlabel('Magnetic Field (Oe)', fontsize=14)
                plt.ylabel('Moment (emu)', fontsize=14)
                plt.title("{}K Fitted Slope Removal Hysteresis".format(Cur_Temp), pad=10, wrap=True, fontsize=14)
                plt.legend()
                plt.tight_layout()
                self.fit_folder = self.ProcessedRAW + '/Fitted_Raw'
                isExist = os.path.exists(self.fit_folder)
                if not isExist:  # Create a new directory because it does not exist
                    os.makedirs(self.fit_folder)
                plt.savefig(self.fit_folder + "/{}K_Slope_Removal_fitted_data.png".format(Cur_Temp))
                plt.close()

                y_slope_removal_lower_concat = pd.Series(y_slope_removal_lower)
                y_slope_removal_upper_concat = pd.Series(y_slope_removal_upper)
                slope_removal_df = pd.concat(
                    [list1_x_concat, y_slope_removal_lower_concat, list2_x_concat, y_slope_removal_upper_concat],
                    ignore_index=True, axis=1)
                slope_removal_df.to_csv(self.ProcCal + '/{}K_Slope_Removal_spliting.csv'.format(Cur_Temp), index=False,
                                        header=False)

                lower_x_shift = result_lower_slope_removal.params['c'].value
                upper_x_shift = result_upper_slope_removal.params['c'].value
                lower_y_shift = result_lower_slope_removal.params['m'].value
                upper_y_shift = result_upper_slope_removal.params['m'].value
                x_offset = lower_x_shift + (abs(lower_x_shift) + abs(upper_x_shift)) / 2
                y_offset = upper_y_shift - (abs(lower_y_shift) + abs(upper_y_shift)) / 2

                Temp_Hyst_Raw = pd.read_csv(csv_list_path + csv_list[j], header=0, engine='c')
                x_raw = Temp_Hyst_Raw.iloc[:, 1]
                y_raw = Temp_Hyst_Raw.iloc[:, 2]

                x_raw = x_raw - x_offset
                y_raw = y_raw - y_offset

                self.processed_final_raw_folder = self.ProcessedRAW + '/RAW_Offset_Removal'
                isExist = os.path.exists(self.processed_final_raw_folder)
                if not isExist:  # Create a new directory because it does not exist
                    os.makedirs(self.processed_final_raw_folder)

                plt.scatter(x_raw, y_raw, label='Processed', s=0.7, alpha=0.8)
                plt.xlabel('Magnetic Field (Oe)', fontsize=14)
                plt.ylabel('Moment (emu)', fontsize=14)
                plt.title("{}K Fitted Hysteresis".format(Cur_Temp), pad=10, wrap=True, fontsize=14)
                plt.legend()
                plt.tight_layout()
                plt.savefig(self.processed_final_raw_folder + "/{}K_RAW_WO_Offset.png".format(Cur_Temp))
                plt.close()

                self.ProcCalFinalRAW = self.ProcCal + '/Final_Processed_RAW_Data'
                isExist = os.path.exists(self.ProcCalFinalRAW)
                if not isExist:  # Create a new directory because it does not exist
                    os.makedirs(self.ProcCalFinalRAW)
                final_RAW_df = pd.DataFrame()
                final_RAW_df_comb = pd.DataFrame(
                    list(zip(x_raw, y_raw)))
                final_df = pd.concat([final_RAW_df, final_RAW_df_comb], ignore_index=True, axis=1)
                final_df.to_csv(self.ProcCalFinalRAW + '/{}K_Final_RAW.csv'.format(Cur_Temp), index=False,
                                header=False)

                x_processed = x - x_offset
                y_processed = y_slope_removal - y_offset

                x_processed_lower = list1_x - x_offset
                x_processed_upper = list2_x - x_offset
                y_processed_lower = y_slope_removal_lower - y_offset
                y_processed_upper = y_slope_removal_upper - y_offset

                plt.scatter(x, y_slope_removal, label='Data', s=0.5, color='coral')
                plt.scatter(x_processed, y_processed, label='Offset', s=0.5, alpha=0.5, color='blue')
                plt.xlabel('Magnetic Field (Oe)', fontsize=14)
                plt.ylabel('Moment (emu)', fontsize=14)
                plt.title("{}K Fitted Final Hysteresis".format(Cur_Temp), pad=10, wrap=True, fontsize=14)
                plt.legend()
                plt.tight_layout()
                self.final_folder = self.ProcessedRAW + '/Final_Processed_Comparison'
                isExist = os.path.exists(self.final_folder)
                if not isExist:  # Create a new directory because it does not exist
                    os.makedirs(self.final_folder)
                plt.savefig(self.final_folder + "/{}K_Proceesed_data_Comparison.png".format(Cur_Temp))
                plt.close()

                plt.scatter(x_processed, y_processed, label='Processed', s=0.7, alpha=0.8)
                plt.xlabel('Magnetic Field (Oe)', fontsize=14)
                plt.ylabel('Moment (emu)', fontsize=14)
                plt.title("{}K Fitted Hysteresis".format(Cur_Temp), pad=10, wrap=True, fontsize=14)
                plt.legend()
                plt.tight_layout()
                self.final_folder = self.ProcessedRAW + '/Final_Processed'
                isExist = os.path.exists(self.final_folder)
                if not isExist:  # Create a new directory because it does not exist
                    os.makedirs(self.final_folder)
                plt.savefig(self.final_folder + "/{}K_Proceesed_data.png".format(Cur_Temp))
                plt.close()

                final_spilt_df = pd.DataFrame()
                x_processed_lower_concat = pd.Series(x_processed_lower)
                y_processed_lower_concat = pd.Series(y_processed_lower)
                x_processed_upper_concat = pd.Series(x_processed_upper)
                y_processed_upper_concat = pd.Series(y_processed_lower)
                final_spilt_df = pd.concat([x_processed_lower_concat, y_processed_lower_concat,
                                            x_processed_upper_concat, y_processed_upper_concat], ignore_index=True,
                                           axis=1)
                final_spilt_df.to_csv(self.ProcCal + '/{}K_Final_spliting.csv'.format(Cur_Temp),
                                      index=False, header=False)

                self.ProcCalFinal = self.ProcCal + '/Final_Processed_Data'
                isExist = os.path.exists(self.ProcCalFinal)
                if not isExist:  # Create a new directory because it does not exist
                    os.makedirs(self.ProcCalFinal)
                final_df = pd.DataFrame()
                final_df_comb = pd.DataFrame(
                    list(zip(x_processed, y_processed)))
                final_df = pd.concat([final_df, final_df_comb], ignore_index=True, axis=1)
                final_df.to_csv(self.ProcCalFinal + '/{}K_Final.csv'.format(Cur_Temp), index=False,
                                header=False)

                lower_final = lmfit.minimize(L_d, params, args=(x_processed_lower,),
                                                            kws={'data': y_processed_lower})
                upper_final = lmfit.minimize(L_d, params, args=(x_processed_upper,),
                                                            kws={'data': y_processed_upper})
                lower_coercivity = lower_final.params['c'].value
                upper_coercivity = upper_final.params['c'].value
                lower_Ms = lower_final.params['m'].value
                upper_Ms = upper_final.params['m'].value

                coercivity = abs(lower_coercivity - upper_coercivity)
                Ms = abs(abs(upper_Ms) + abs(lower_Ms))/2

                Ms_temp = pd.DataFrame({'Temperature': [int(Cur_Temp)], 'Saturation Field': [Ms], 'Upper': [upper_Ms], 'Lower': [lower_Ms]})
                Ms_df = pd.concat([Ms_df, Ms_temp], ignore_index=True)
                Coercivity_temp = pd.DataFrame({'Temperature': [int(Cur_Temp)], 'Coercivity': [coercivity]})
                Coercivity_df = pd.concat([Coercivity_df, Coercivity_temp], ignore_index=True)


        area_df = area_df.sort_values('Temperature')
        x_temp = area_df.iloc[:, 0]
        y_area = area_df.iloc[:, 1]
        plt.rc('xtick', labelsize=13)  # fontsize of the tick labels
        plt.rc('ytick', labelsize=13)
        fig, ax = plt.subplots()
        ax.plot(x_temp, y_area, color='black', marker='s', linewidth=2, markersize=5)
        ax.set_xlabel('Temperature (K)', fontsize=14)
        ax.set_ylabel('Area', fontsize=14)
        plt.tight_layout()
        plt.savefig(self.ProcessedRAW + "/Area_Relation.png")
        area_df.to_csv(self.ProcCal + '/Area_Relation.csv', index=False)
        plt.close()

        Ms_df = Ms_df.sort_values('Temperature')
        x_temp = Ms_df.iloc[:, 0]
        y_ms = Ms_df.iloc[:, 1]
        y_ms_upper = Ms_df.iloc[:, 2]
        y_ms_lower = Ms_df.iloc[:, 3]

        plt.rc('xtick', labelsize=13)  # fontsize of the tick labels
        plt.rc('ytick', labelsize=13)
        fig, ax = plt.subplots()
        ax.plot(x_temp, y_ms, color='black', marker='s', linewidth=2, markersize=5)
        ax.set_xlabel('Temperature (K)', fontsize=14)
        ax.set_ylabel('Saturation Field Ms', fontsize=14)
        plt.tight_layout()
        plt.savefig(self.ProcessedRAW + "/Saturation_Field.png")
        Ms_df.to_csv(self.ProcCal + '/Saturation_Field.csv', index=False)
        plt.close()

        plt.rc('xtick', labelsize=13)  # fontsize of the tick labels
        plt.rc('ytick', labelsize=13)
        fig, ax = plt.subplots()
        ax.plot(x_temp, y_ms_upper, color='#922B21', marker='s', linewidth=2, markersize=5,label="upper")
        ax.plot(x_temp, y_ms_lower, color='#212F3D', marker='s', linewidth=2, markersize=5, label="lower")
        ax.set_xlabel('Temperature (K)', fontsize=14)
        ax.set_ylabel('Saturation Field Ms', fontsize=14)
        plt.tight_layout()
        plt.legend()
        plt.savefig(self.ProcessedRAW + "/Saturation_Field_Split.png")
        Ms_df.to_csv(self.ProcCal + '/Saturation_Field_Split.csv', index=False)
        plt.close()

        Coercivity_df = Coercivity_df.sort_values('Temperature')
        x_temp = Coercivity_df.iloc[:, 0]
        y_coerc = Coercivity_df.iloc[:, 1]
        plt.rc('xtick', labelsize=13)  # fontsize of the tick labels
        plt.rc('ytick', labelsize=13)
        fig, ax = plt.subplots()
        ax.plot(x_temp, y_coerc, color='black', marker='s', linewidth=2, markersize=5)
        ax.set_xlabel('Temperature (K)', fontsize=14)
        ax.set_ylabel('Coercivity', fontsize=14)
        plt.tight_layout()
        plt.savefig(self.ProcessedRAW + "/Coercivity.png")
        Coercivity_df.to_csv(self.ProcCal + '/Coercivity.csv', index=False)
        plt.close()

        y_range_positive = 0
        y_range_negative = 0
        data_csv_list_path = self.ProcCal + '/Final_Processed_Data/'
        data_csv_list = os.listdir(data_csv_list_path)
        data_number_CSV = len(data_csv_list)
        self.Final_Hysteresis = self.ProcessedRAW + '/Final_Hysteresis'
        isExist = os.path.exists(self.Final_Hysteresis)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(self.Final_Hysteresis)

        data_hyst_lim = self.y_range(data_number_CSV, data_csv_list_path, data_csv_list, y_range_positive,
                                     y_range_negative)
        self.Process_individual_Hys(data_number_CSV, data_csv_list, data_csv_list_path,
                                    data_hyst_lim, self.Final_Hysteresis)

        y_range_positive = 0
        y_range_negative = 0
        data_csv_list_path = self.ProcCal + '/Final_Processed_RAW_Data/'
        data_csv_list = os.listdir(data_csv_list_path)
        data_number_CSV = len(data_csv_list)
        self.Final_Hysteresis_RAW = self.ProcessedRAW + '/Final_Hysteresis_RAW'
        isExist = os.path.exists(self.Final_Hysteresis_RAW)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(self.Final_Hysteresis_RAW)


        data_hyst_lim = self.y_range(data_number_CSV, data_csv_list_path, data_csv_list, y_range_positive,
                                     y_range_negative)
        self.Process_individual_Hys(data_number_CSV, data_csv_list, data_csv_list_path,
                                    data_hyst_lim, self.Final_Hysteresis_RAW)

        self.to_ppt()

    def to_ppt(self):

        if os.path.exists(self.ProcCal + '/Processed_Hyst.pptx'):
            prs = Presentation(self.ProcCal + '/Processed_Hyst.pptx')
            prs.slide_width = Inches(13.33)
            prs.slide_height = Inches(7.5)
        else:
            prs = Presentation()
            prs.slide_width = Inches(13.33)
            prs.slide_height = Inches(7.5)
            prs.save(self.ProcCal + '/Processed_Hyst.pptx')
            prs = Presentation(self.ProcCal + '/Processed_Hyst.pptx')
            prs.slide_width = Inches(13.33)
            prs.slide_height = Inches(7.5)

        if os.path.exists(self.ProcCal + '/Processed_Hyst_RAW.pptx'):
            prs_RAW = Presentation(self.ProcCal + '/Processed_Hyst_RAW.pptx')
            prs_RAW.slide_width = Inches(13.33)
            prs_RAW.slide_height = Inches(7.5)
        else:
            prs_RAW = Presentation()
            prs_RAW.slide_width = Inches(13.33)
            prs_RAW.slide_height = Inches(7.5)
            prs_RAW.save(self.ProcCal + '/Processed_Hyst_RAW.pptx')
            prs_RAW = Presentation(self.ProcCal + '/Processed_Hyst_RAW.pptx')
            prs_RAW.slide_width = Inches(13.33)
            prs_RAW.slide_height = Inches(7.5)

        # self.Final_Hysteresis
        dat_list_path = self.folder_selected + '*.DAT'
        dat_list = glob.glob(dat_list_path)
        file_name = dat_list[0]
        for i in range(len(file_name) - 1, 0, -1):
            if file_name[i] == ' ':
                file_name = file_name[:i]
                break

        for i in range(len(file_name) - 1, 0, -1):
            if file_name[i] == '/':
                file_name = file_name[i+1:]
                break



        Final_png_path = self.Final_Hysteresis + '/' + '*.png'
        Final_png_list = glob.glob(Final_png_path)
        data_number_Final_png_list = len(Final_png_list)
        for i in range(0, data_number_Final_png_list, 1):
            for j in range(len(Final_png_list[i]) - 1, 0, -1):
                if Final_png_list[i][j] == '/':
                    Final_png_list[i] = Final_png_list[i][j+1:]
                    break
        def extract_number(f):
            return int(f.split('K')[0])

        # Sort the file names using the custom sorting function
        Final_png_list = sorted(Final_png_list, key=extract_number)

        Final_png_RAW_path = self.Final_Hysteresis_RAW + '/' + '*.png'
        Final_png_RAW_list = glob.glob(Final_png_RAW_path)
        data_number_Final_png_RAW_list = len(Final_png_RAW_list)
        for i in range(0, data_number_Final_png_RAW_list, 1):
            for j in range(len(Final_png_RAW_list[i]) - 1, 0, -1):
                if Final_png_RAW_list[i][j] == '/':
                    Final_png_RAW_list[i] = Final_png_RAW_list[i][j + 1:]
                    break

        Final_png_RAW_list = sorted(Final_png_RAW_list, key=extract_number)

        inital_x = 0
        initial_y = 0.89
        image_width = 2.15
        x_offset = 2.24
        y_offset = 1.67
        iteration = 0

        blank_slide_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_slide_layout)
        text_frame = slide.shapes.add_textbox(Inches(5.67), Inches(0.06), Inches(2.03), Inches(0.57))
        text_frame = text_frame.text_frame
        p = text_frame.paragraphs[0]
        run = p.add_run()
        run.text = str(file_name)
        font = run.font
        font.name = 'Calibri'
        font.size = Pt(28)
        for k in range(0, data_number_Final_png_list, 1):
            VSM =  self.Final_Hysteresis + '/' + Final_png_list[k]
            if iteration == 6:
                inital_x = 0
                initial_y = initial_y + y_offset
                iteration = 0
            VSM_image = slide.shapes.add_picture(VSM, Inches(inital_x), Inches(initial_y), Inches(image_width)) #x,y & width
            inital_x += x_offset
            iteration += 1

        prs.save(self.ProcCal + '/Processed_Hyst.pptx')

        blank_slide_layout = prs_RAW.slide_layouts[6]
        slide = prs_RAW.slides.add_slide(blank_slide_layout)
        text_frame = slide.shapes.add_textbox(Inches(5.67), Inches(0.06), Inches(2.03), Inches(0.57))
        text_frame = text_frame.text_frame
        p = text_frame.paragraphs[0]
        run = p.add_run()
        run.text = str(file_name)
        font = run.font
        font.name = 'Calibri'
        font.size = Pt(28)

        inital_x = 0
        initial_y = 0.89
        image_width = 2.15
        x_offset = 2.24
        y_offset = 1.67
        iteration = 0
        for k in range(0, data_number_Final_png_RAW_list, 1):
            VSM =  self.Final_Hysteresis_RAW + '/' + Final_png_RAW_list[k]
            if iteration == 6:
                inital_x = 0
                initial_y = initial_y + y_offset
                iteration = 0
            VSM_image = slide.shapes.add_picture(VSM, Inches(inital_x), Inches(initial_y), Inches(image_width)) #x,y & width
            inital_x += x_offset
            iteration += 1

        prs_RAW.save(self.ProcCal + '/Processed_Hyst_RAW.pptx')



