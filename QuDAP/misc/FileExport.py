from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QScrollArea, QSizePolicy,
    QMenu, QWidgetAction, QApplication, QTableView
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QFont, QBrush, QColor, QStandardItemModel, QStandardItem
import os
import numpy as np
import traceback
import csv
import pandas as pd

try:
    from QuDAP.GUI.VSM.qd import Loadfile
    import QuDAP.misc.dragdropwidget as ddw
except ImportError:
    from GUI.VSM.qd import *
    from misc.dragdropwidget import *


class FileExport(QMainWindow):
    def __init__(self, label):
        super().__init__()
        self.process_type_label = label
        # Selection tracking variables for ordered selection
        self.x_column = None  # Store X column index
        self.y_columns = []  # Store Y column indices in order

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
                # Load stylesheets (adjust paths as needed)
                try:
                    with open("GUI/VSM/QButtonWidget.qss", "r") as file:
                        self.Browse_Button_stylesheet = file.read()
                except:
                    self.Browse_Button_stylesheet = ""

                titlefont = QFont("Arial", 20)
                self.font = QFont("Arial", 12)
                self.setStyleSheet("background-color: white;")

                try:
                    with open("GUI/QSS/QScrollbar.qss", "r") as file:
                        self.scrollbar_stylesheet = file.read()
                except:
                    self.scrollbar_stylesheet = ""

                # Create a QScrollArea
                self.scroll_area = QScrollArea()
                self.scroll_area.setWidgetResizable(True)
                self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
                self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                self.scroll_area.setStyleSheet(self.scrollbar_stylesheet)

                # Create a widget to hold the main layout
                self.content_widget = QWidget()
                self.scroll_area.setWidget(self.content_widget)

                # Set the content widget to expand
                self.main_layout = QVBoxLayout(self.content_widget)
                self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.main_layout.setContentsMargins(20, 20, 20, 20)
                self.content_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

                #  ---------------------------- PART 1 --------------------------------
                try:
                    with open("GUI/QSS/QButtonWidget.qss", "r") as file:
                        self.Button_stylesheet = file.read()
                except:
                    self.Button_stylesheet = ""

                self.label = QLabel(f"{self.process_type_label} Data Extraction")
                self.label.setFont(titlefont)
                self.label.setStyleSheet("""
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

                # Create placeholder for drag-drop widget
                self.drag_drop_widget = ddw.DragDropWidget(self)
                self.selected_file_type = ddw.DragDropWidget(self).get_selected_file_type()
                # self.drag_drop_widget = QWidget()  # Placeholder
                self.drag_drop_layout.addWidget(self.drag_drop_widget, 4)
                self.drag_drop_layout.addWidget(self.file_selection_display_label, 1,
                                                alignment=Qt.AlignmentFlag.AlignCenter)
                self.file_selection_group_box.setLayout(self.drag_drop_layout)

                # Create the file browser area
                self.file_tree = QTreeWidget()
                self.file_tree_layout = QHBoxLayout()
                self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                self.file_tree.customContextMenuRequested.connect(self.open_context_menu)
                self.file_tree.setHeaderLabels(["Name", "Type", "Size"])
                self.file_tree_layout.addWidget(self.file_tree)

                try:
                    with open("GUI/SHG/QTreeWidget.qss", "r") as file:
                        self.QTree_stylesheet = file.read()
                    self.file_tree.setStyleSheet(self.QTree_stylesheet)
                except:
                    pass

                self.file_view_group_box.setLayout(self.file_tree_layout)
                self.fileUpload_layout.addWidget(self.file_selection_group_box, 1)
                self.fileUpload_layout.addWidget(self.file_view_group_box, 1)
                self.fileupload_container = QWidget(self)
                self.fileupload_container.setLayout(self.fileUpload_layout)
                self.fileupload_container.setFixedSize(1150, 260)

                # ---------------------------- SELECTION INSTRUCTION ---------------------
                self.instruction_label = QLabel(
                    "Column Selection: Click = Set as X (blue) | Ctrl+Click = Add as Y (red) | Shift+Click = Remove")
                self.instruction_label.setStyleSheet("""
                    QLabel {
                        color: #666;
                        padding: 8px;
                        background-color: #f0f0f0;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                """)

                # Selection display
                self.selection_display = QLabel("X: None | Y: None")
                self.selection_display.setStyleSheet("""
                    QLabel {
                        padding: 8px;
                        background-color: #e8f4ff;
                        border: 1px solid #ccc;
                        border-radius: 5px;
                        font-weight: bold;
                    }
                """)

                # Clear button
                self.clear_selection_btn = QPushButton("Clear All Selections")
                self.clear_selection_btn.clicked.connect(self.clear_column_selection)
                self.clear_selection_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #95a5a6;
                        color: white;
                        padding: 5px 15px;
                        border-radius: 3px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #7f8c8d;
                    }
                """)

                selection_info_layout = QHBoxLayout()
                selection_info_layout.addWidget(self.instruction_label)
                selection_info_layout.addWidget(self.selection_display)
                selection_info_layout.addWidget(self.clear_selection_btn)
                selection_info_layout.addStretch()

                # ---------------------------- TABLE WIDGET ---------------------
                # self.table_layout = QVBoxLayout()
                # self.table_widget = QTableWidget(100, 100)
                # # Enable multi-column selection
                # # self.table_widget.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
                # self.table_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                # self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectColumns)
                # self.table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                # self.table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
                # table_header = self.table_widget.horizontalHeader()
                # table_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                # self.table_widget.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
                # self.table_widget.setFixedSize(1150, 320)
                # self.table_layout.addWidget(self.table_widget)

                self.table_layout = QVBoxLayout()

                # Replace QTableWidget with QTableView
                self.table_view = QTableView()

                # Create the model
                self.table_model = QStandardItemModel()
                self.table_view.setModel(self.table_model)

                # Enable column selection behavior
                self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectColumns)

                # Set scrollbar policies
                self.table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

                # Configure header
                header = self.table_view.horizontalHeader()
                header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

                # Connect header click signal
                self.table_view.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

                self.table_view.setFixedSize(1150, 320)
                self.table_layout.addWidget(self.table_view)

                # ---------------------------- BUTTONS ---------------------
                self.btn_layout = QHBoxLayout()

                self.rst_btn = QPushButton("Reset")
                self.rst_btn.clicked.connect(self.rstpage)
                self.export_btn = QPushButton("Export")
                self.export_btn.clicked.connect(self.export_selected_column_data)
                self.export_btn.setToolTip("Export single file with selected columns")
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

                # ---------------------------- MAIN LAYOUT ---------------------
                self.main_layout.addWidget(self.label,
                                                               alignment=Qt.AlignmentFlag.AlignTop)
                self.main_layout.addWidget(self.fileupload_container)
                self.main_layout.addLayout(selection_info_layout)
                self.main_layout.addLayout(self.table_layout)
                self.main_layout.addLayout(self.btn_layout)
                self.main_layout.addStretch(1)

                self.setCentralWidget(self.scroll_area)
                self.content_widget.adjustSize()

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def display_dataframe(self, df):
        """Display a pandas DataFrame in the table view"""
        try:
            # Clear the model
            self.table_model.clear()

            # Set headers
            headers = list(df.columns)
            self.table_model.setHorizontalHeaderLabels(headers)

            # Store original headers
            self.original_headers = {}
            for col, header in enumerate(headers):
                self.original_headers[col] = str(header)

            # Set row and column count
            self.table_model.setRowCount(len(df))
            self.table_model.setColumnCount(len(df.columns))

            # Fill model with data
            for row in range(len(df)):
                for col in range(len(df.columns)):
                    value = df.iloc[row, col]

                    # Handle different data types
                    if pd.isna(value):
                        item_text = ""
                    elif isinstance(value, (int, float)):
                        if isinstance(value, float):
                            item_text = f"{value:.6g}"
                        else:
                            item_text = str(value)
                    else:
                        item_text = str(value)

                    item = QStandardItem(item_text)
                    self.table_model.setItem(row, col, item)

            # Adjust column widths
            self.table_view.resizeColumnsToContents()

            # Limit column width for better display
            for col in range(self.table_model.columnCount()):
                if self.table_view.columnWidth(col) > 200:
                    self.table_view.setColumnWidth(col, 200)

        except Exception as e:
            raise Exception(f"Error displaying data: {str(e)}")

    def on_header_clicked(self, logical_index):
        """Handle header clicks with modifiers for column selection"""
        modifiers = QApplication.keyboardModifiers()

        if modifiers == Qt.KeyboardModifier.ControlModifier:
            # Ctrl+Click: Add as Y column
            if logical_index not in self.y_columns:
                if logical_index == self.x_column:
                    self.x_column = None
                self.y_columns.append(logical_index)

        elif modifiers == Qt.KeyboardModifier.ShiftModifier:
            # Shift+Click: Remove from selection
            if logical_index == self.x_column:
                self.x_column = None
            elif logical_index in self.y_columns:
                self.y_columns.remove(logical_index)

        else:
            # Normal click: Set as X column
            if logical_index in self.y_columns:
                self.y_columns.remove(logical_index)
            self.x_column = logical_index

        self.update_column_colors()
        self.update_selection_display()

    def clear_column_selection(self):
        """Clear all column selections"""
        self.x_column = None
        self.y_columns = []
        self.update_column_colors()
        self.update_selection_display()

    def update_selection_display(self):
        """Update the selection display label"""
        x_text = "X: None"
        if self.x_column is not None and self.table_widget.horizontalHeaderItem(self.x_column):
            x_text = f"X: {self.table_widget.horizontalHeaderItem(self.x_column).text()}"

        y_text = "Y: None"
        if self.y_columns:
            y_headers = []
            for col in self.y_columns:
                header_item = self.table_widget.horizontalHeaderItem(col)
                if header_item:
                    y_headers.append(header_item.text())
            if y_headers:
                y_text = f"Y: {', '.join(y_headers)}"

        self.selection_display.setText(f"{x_text} | {y_text}")

    # def update_column_colors(self):
    #     """Update table and header colors based on selection"""
    #     # Store original header texts
    #     if not hasattr(self, 'original_headers'):
    #         self.original_headers = {}
    #         for col in range(self.table_widget.columnCount()):
    #             header_item = self.table_widget.horizontalHeaderItem(col)
    #             if header_item:
    #                 self.original_headers[col] = header_item.text()
    #
    #     # Reset all columns to default
    #     for col in range(self.table_widget.columnCount()):
    #         # Reset cells
    #         for row in range(self.table_widget.rowCount()):
    #             item = self.table_widget.item(row, col)
    #             if item:
    #                 item.setBackground(QBrush(Qt.GlobalColor.white))
    #
    #         # Reset header
    #         header_item = self.table_widget.horizontalHeaderItem(col)
    #         if header_item and col in self.original_headers:
    #             header_item.setText(self.original_headers[col])
    #             header_item.setBackground(QBrush())
    #             header_item.setForeground(QBrush())
    #
    #     # Color X column (blue)
    #     if self.x_column is not None:
    #         for row in range(self.table_widget.rowCount()):
    #             item = self.table_widget.item(row, self.x_column)
    #             if item:
    #                 item.setBackground(QBrush(QColor(52, 152, 219, 80)))  # Light blue
    #
    #         # Color header
    #         header_item = self.table_widget.horizontalHeaderItem(self.x_column)
    #         if header_item:
    #             header_item.setBackground(QBrush(QColor(52, 152, 219)))
    #             header_item.setForeground(QBrush(Qt.GlobalColor.white))
    #             if self.x_column in self.original_headers:
    #                 header_item.setText(f"[X] {self.original_headers[self.x_column]}")
    #
    #     # Color Y columns (red with varying intensity)
    #     for idx, col in enumerate(self.y_columns):
    #         # Vary the red intensity based on selection order
    #         alpha = 60 + (idx * 30) if idx < 5 else 200  # Cap at reasonable alpha
    #
    #         for row in range(self.table_widget.rowCount()):
    #             item = self.table_widget.item(row, col)
    #             if item:
    #                 item.setBackground(QBrush(QColor(231, 76, 60, alpha)))
    #
    #         # Color header
    #         header_item = self.table_widget.horizontalHeaderItem(col)
    #         if header_item:
    #             header_item.setBackground(QBrush(QColor(231, 76, 60)))
    #             header_item.setForeground(QBrush(Qt.GlobalColor.white))
    #             if col in self.original_headers:
    #                 header_item.setText(f"[Y{idx + 1}] {self.original_headers[col]}")
    def update_column_colors(self):
        """Update table view colors based on selection"""
        # Store original header texts if not already stored
        if not hasattr(self, 'original_headers'):
            self.original_headers = {}
            for col in range(self.table_model.columnCount()):
                header_item = self.table_model.horizontalHeaderItem(col)
                if header_item:
                    self.original_headers[col] = header_item.text()

        # Reset all columns to default
        for col in range(self.table_model.columnCount()):
            # Reset cells
            for row in range(self.table_model.rowCount()):
                item = self.table_model.item(row, col)
                if item:
                    item.setBackground(QBrush(Qt.GlobalColor.white))

            # Reset header
            header_text = self.original_headers.get(col, f"Column {col}")
            self.table_model.setHorizontalHeaderItem(col, QStandardItem(header_text))

        # Color X column (blue)
        if self.x_column is not None:
            for row in range(self.table_model.rowCount()):
                item = self.table_model.item(row, self.x_column)
                if item:
                    item.setBackground(QBrush(QColor(52, 152, 219, 80)))

            # Update header
            if self.x_column in self.original_headers:
                header_item = QStandardItem(f"[X] {self.original_headers[self.x_column]}")
                header_item.setBackground(QBrush(QColor(52, 152, 219)))
                header_item.setForeground(QBrush(Qt.GlobalColor.white))
                self.table_model.setHorizontalHeaderItem(self.x_column, header_item)

        # Color Y columns (red with varying intensity)
        for idx, col in enumerate(self.y_columns):
            alpha = 60 + (idx * 30) if idx < 5 else 200

            for row in range(self.table_model.rowCount()):
                item = self.table_model.item(row, col)
                if item:
                    item.setBackground(QBrush(QColor(231, 76, 60, alpha)))

            # Update header
            if col in self.original_headers:
                header_item = QStandardItem(f"[Y{idx + 1}] {self.original_headers[col]}")
                header_item.setBackground(QBrush(QColor(231, 76, 60)))
                header_item.setForeground(QBrush(Qt.GlobalColor.white))
                self.table_model.setHorizontalHeaderItem(col, header_item)


    def display_files(self, folder_path, selected_file_type):
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
                if file_name.endswith.lower(selected_file_type):
                    file_path = os.path.join(root, file_name)
                    self.file_in_list.append(file_path)
                    file_info = os.stat(file_path)
                    file_size_kb = file_info.st_size / 1024
                    file_size_str = f"{file_size_kb:.2f} KB"
                    if selected_file_type == '.dat':
                        file_type = 'application/dat'
                    elif selected_file_type == '.xls' or selected_file_type == '.xlsx':
                        file_type = 'excel'
                    elif selected_file_type == '.csv':
                        file_type = 'csv'
                    elif selected_file_type == '.txt':
                        file_type = 'text'
                    else:
                        file_type = 'other'
                    item = QTreeWidgetItem(self.file_tree, [file_name, file_type, file_size_str, ""])
                    item.setToolTip(0, file_path)

        self.file_tree.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.file_tree.resizeColumnToContents(0)
        self.file_tree.resizeColumnToContents(1)
        self.file_tree.resizeColumnToContents(2)

    def display_multiple_files(self, file_paths, selected_file_type):
        current_files = {self.file_tree.topLevelItem(i).text(0): self.file_tree.topLevelItem(i)
                         for i in range(self.file_tree.topLevelItemCount())}
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            if file_name not in current_files:
                self.file_in_list.append(file_path)
                file_info = os.stat(file_path)
                file_size_kb = file_info.st_size / 1024
                file_size_str = f"{file_size_kb:.2f} KB"
                if selected_file_type == '.dat':
                    file_type = 'application/dat'
                elif selected_file_type == '.xls' or selected_file_type == '.xlsx':
                    file_type = 'excel'
                elif selected_file_type == '.csv':
                    file_type = 'csv'
                elif selected_file_type == '.txt':
                    file_type = 'text'
                else:
                    file_type = 'other'
                item = QTreeWidgetItem(self.file_tree, [file_name, file_type, file_size_str, ""])
                item.setToolTip(0, file_path)

        self.file_tree.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.file_tree.resizeColumnToContents(0)
        self.file_tree.resizeColumnToContents(1)
        self.file_tree.resizeColumnToContents(2)

        self.file_selection_display_label.setText(
            f"{self.file_tree.topLevelItemCount()} Files Successfully Uploaded")
        self.file_selection_display_label.setStyleSheet("""
            color: #4b6172; 
            font-size: 12px;
            background-color: #DfE7Ef; 
            border-radius: 5px; 
            padding: 5px;
        """)

    def on_item_selection_changed(self):
        self.clear_column_selection()
        self.table_widget.clear()
        selected_items = self.file_tree.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            self.file_path = selected_item.toolTip(0)
            self.open_file_in_table(self.file_path)

    def open_file_in_table(self, file_path):
        # self.clear_column_selection()
        if file_path.lower().endswith('.dat'):
            try:
                # Comment out for testing without Loadfile
                loaded_file = Loadfile(file_path)
                headers = loaded_file.column_headers
                data = loaded_file.data

                self.table_widget.setColumnCount(len(headers))
                self.table_widget.setHorizontalHeaderLabels(headers)
                self.table_widget.setRowCount(len(data))

                # Store original headers
                self.original_headers = {}
                for col in range(len(headers)):
                    self.original_headers[col] = headers[col]

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

            except Exception as e:
                tb_str = traceback.format_exc()
                QMessageBox.warning(self, "Error", f"{str(e)}{str(tb_str)}")
        elif file_path.lower().endswith('.xls') or file_path.lower().endswith('.xlsx'):
            None
        elif file_path.lower().endswith('.csv'):
            None
        elif file_path.lower().endswith('.txt'):
            None

    def showDialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            folder = folder + "/"
            self.folder = folder
            self.file_selection_display_label.setText("Current Folder: {}".format(self.folder))

    def rstpage(self):
        try:
            # Clear selections
            self.x_column = None
            self.y_columns = []

            try:
                self.drag_drop_widget.reset()
                self.file_tree.clear()
                self.table_widget.clear()
                self.table_widget.setRowCount(100)
                self.table_widget.setColumnCount(100)
                self.file_selection_display_label.setText('Please Upload Files or Directory')
                self.file_selection_display_label.setStyleSheet("""
                                    color: white; 
                                    font-size: 12px;
                                    background-color:  #f38d76 ; 
                                    border-radius: 5px; 
                                    padding: 5px;
                                """)
                # self.scroll_area.deleteLater()
                # self.scroll_area = QScrollArea()
                # self.scroll_area.setWidgetResizable(True)
                #
                # self.content_widget = QWidget()
                # self.scroll_area.setWidget(self.content_widget)
                #
                # # Set new central widget
                # self.setCentralWidget(self.scroll_area)

                self.init_ui()
            except Exception as e:
                return


        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def export_selected_column_data(self):
        """Export data with X column first, then Y columns in order"""
        try:
            if self.x_column is None:
                QMessageBox.warning(self, "No X Column", "Please select an X column first (normal click on header)")
                return

            if not self.y_columns:
                QMessageBox.warning(self, "No Y Columns",
                                    "Please select at least one Y column (Ctrl+Click on headers)")
                return

            # Prepare data with X first, then Y columns in order
            column_data = {}

            # Add X column
            x_header = self.original_headers.get(self.x_column,
                                                 self.table_widget.horizontalHeaderItem(self.x_column).text())
            x_values = []
            for row in range(self.table_widget.rowCount()):
                item = self.table_widget.item(row, self.x_column)
                x_values.append(item.text() if item else "")
            column_data[x_header] = x_values

            # Add Y columns in the order they were selected
            for col in self.y_columns:
                column_header = self.original_headers.get(col,
                                                          self.table_widget.horizontalHeaderItem(col).text())
                column_values = []
                for row in range(self.table_widget.rowCount()):
                    item = self.table_widget.item(row, col)
                    column_values.append(item.text() if item else "")
                column_data[column_header] = column_values

            # Get file name
            if hasattr(self, 'file_path'):
                for i in range(len(self.file_path) - 1, 0, -1):
                    if self.file_path[i] == ".":
                        file_name = self.file_path[: i]
                    if self.file_path[i] == "/" or self.file_path[i] == "\\":
                        file_name = file_name[i + 1:]
                        folder_name = self.file_path[:i + 1]
                        break
            else:
                file_name = "exported_data"

            dialog = QFileDialog(self)
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            if hasattr(self, 'file_path'):
                dialog.setDirectory(os.path.dirname(self.file_path))

            if dialog.exec():
                folder_name = dialog.selectedFiles()[0]
                export_file_name = os.path.join(folder_name, f"{file_name}.csv")
                self.export_to_csv(column_data, export_file_name)
                QMessageBox.information(self, "Success", f"Data exported to {export_file_name}")

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def export_selected_column_alldata(self):
        """Export all files with selected columns"""
        try:
            if self.x_column is None:
                QMessageBox.warning(self, "No X Column", "Please select an X column first")
                return

            if not self.y_columns:
                QMessageBox.warning(self, "No Y Columns", "Please select at least one Y column")
                return

            dialog = QFileDialog(self)
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            if hasattr(self, 'file_path'):
                dialog.setDirectory(os.path.dirname(self.file_path))

            if dialog.exec():
                folder_name = dialog.selectedFiles()[0]

                # Export all files with selected columns
                for file in self.file_in_list:
                    column_data = {}

                    # Comment out for testing
                    loaded_file = Loadfile(file)
                    headers = loaded_file.column_headers
                    data = loaded_file.data

                    # Add X column
                    if self.x_column < len(headers):
                        column_header = headers[self.x_column] if isinstance(headers, list) else list(headers)[
                            self.x_column]
                        column_values = data[:, self.x_column]
                        column_data[column_header] = column_values

                    # Add Y columns
                    for col in self.y_columns:
                        if col < len(headers):
                            column_header = headers[col] if isinstance(headers, list) else list(headers)[col]
                            column_values = data[:, col]
                            column_data[column_header] = column_values

                    # Get file name
                    file_name = os.path.splitext(os.path.basename(file))[0]
                    export_file_name = os.path.join(folder_name, f"{file_name}.csv")

                    with open(export_file_name, 'w', newline='') as f:
                        writer = csv.writer(f)
                        headers = list(column_data.keys())
                        writer.writerow(headers)
                        for row in zip(*column_data.values()):
                            writer.writerow(row)

                QMessageBox.information(self, "Success", f"All files exported to {folder_name}")

        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def export_to_csv(self, column_data, file_name):
        try:
            with open(file_name, 'w', newline='') as file:
                writer = csv.writer(file)
                headers = list(column_data.keys())
                writer.writerow(headers)
                for row in zip(*column_data.values()):
                    writer.writerow(row)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def open_context_menu(self, position: QPoint):

        """Open the context menu on right-click."""
        menu = QMenu()

        remove_action = QWidgetAction(self)
        remove_label = QLabel("Remove")
        remove_label.mousePressEvent = lambda event: self.handle_remove_click(event)
        remove_action.setDefaultWidget(remove_label)
        menu.addAction(remove_action)
        menu.exec(self.file_tree.viewport().mapToGlobal(position))

    def handle_remove_click(self, event):
        """Handle right-click on remove label."""
        if event.button() == Qt.MouseButton.LeftButton:
            print("right")
            self.file_tree.clearSelection()
            self.clear_column_selection()
            self.remove_selected_item()
        # if event.button() == Qt.MouseButton.LeftButton:
        #     self.on_item_selection_changed()

    def remove_selected_item(self):
        """Remove the selected item from the tree."""
        selected_item = self.file_tree.currentItem()
        if selected_item:
            file_path = selected_item.toolTip(0)
            if file_path in self.file_in_list:
                self.file_in_list.remove(file_path)
            index = self.file_tree.indexOfTopLevelItem(selected_item)
            if index != -1:
                self.file_tree.takeTopLevelItem(index)

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                if child.layout() is not None:
                    self.clear_layout(child.layout())