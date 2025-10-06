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
from pathlib import Path

try:
    from GUI.VSM.qd import Loadfile
    import misc.dragdropwidget as ddw
except ImportError:
    try:
        from QuDAP.GUI.VSM.qd import Loadfile
        import QuDAP.misc.dragdropwidget as ddw
    except ImportError:
        # Create a dummy Loadfile class if not available
        class Loadfile:
            def __init__(self, filepath):
                raise NotImplementedError("Loadfile class not available")


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

                # Button stylesheet
                try:
                    with open("GUI/QSS/QButtonWidget.qss", "r") as file:
                        self.Button_stylesheet = file.read()
                except:
                    self.Button_stylesheet = """
                        QPushButton {
                            background-color: #1e88e5;
                            color: white;
                            padding: 10px 20px;
                            border-radius: 5px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #1976d2;
                        }
                    """

                self.label = QLabel(f"{self.process_type_label} Data Extraction")
                self.label.setFont(titlefont)
                self.label.setStyleSheet("QLabel{background-color: white;}")

                # File Upload Section
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
                    background-color: #f38d76; 
                    border-radius: 5px; 
                    padding: 5px;
                """)

                # Create drag-drop widget
                try:
                    self.drag_drop_widget = ddw.DragDropWidget(self)
                    self.selected_file_type = self.drag_drop_widget.get_selected_file_type()
                except:
                    # Fallback if drag-drop widget not available
                    self.drag_drop_widget = QWidget()
                    browse_btn = QPushButton("Browse Files")
                    browse_btn.clicked.connect(self.browse_files_fallback)
                    fallback_layout = QVBoxLayout(self.drag_drop_widget)
                    fallback_layout.addWidget(browse_btn)

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

                # Selection Instruction
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

                # Table Widget with QTableView
                self.table_layout = QVBoxLayout()
                self.table_view = QTableView()
                self.table_model = QStandardItemModel()
                self.table_view.setModel(self.table_model)
                self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectColumns)
                self.table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

                header = self.table_view.horizontalHeader()
                header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                self.table_view.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
                self.table_view.setFixedSize(1150, 320)
                self.table_layout.addWidget(self.table_view)

                # Buttons
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

                # Main Layout Assembly
                self.main_layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignTop)
                self.main_layout.addWidget(self.fileupload_container)
                self.main_layout.addLayout(selection_info_layout)
                self.main_layout.addLayout(self.table_layout)
                self.main_layout.addLayout(self.btn_layout)
                self.main_layout.addStretch(1)

                self.setCentralWidget(self.scroll_area)
                self.content_widget.adjustSize()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Initialization error: {str(e)}")
            return

    def browse_files_fallback(self):
        """Fallback file browser if drag-drop widget not available"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Data Files",
            "",
            "Data Files (*.csv *.txt *.dat *.xlsx *.xls);;All Files (*.*)"
        )
        if files:
            self.display_multiple_files(files)

    def display_dataframe(self, df):
        """Display a pandas DataFrame in the table view"""
        try:
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

    def update_column_colors(self):
        """Update table view colors based on selection"""
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

    def update_selection_display(self):
        """Update the selection display label"""
        x_text = "X: None"
        if self.x_column is not None and self.x_column in self.original_headers:
            x_text = f"X: {self.original_headers[self.x_column]}"

        y_text = "Y: None"
        if self.y_columns:
            y_headers = []
            for col in self.y_columns:
                if col in self.original_headers:
                    y_headers.append(self.original_headers[col])
            if y_headers:
                y_text = f"Y: {', '.join(y_headers)}"

        self.selection_display.setText(f"{x_text} | {y_text}")

    def display_files(self, folder_path, selected_file_type=None):
        """Display files from a folder"""
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

        supported_extensions = ['.dat', '.csv', '.xlsx', '.xls', '.txt']

        for root, dirs, files in os.walk(folder_path):
            for file_name in files:
                file_ext = os.path.splitext(file_name)[1].lower()
                if file_ext in supported_extensions:
                    file_path = os.path.join(root, file_name)
                    self.file_in_list.append(file_path)
                    file_info = os.stat(file_path)
                    file_size_kb = file_info.st_size / 1024
                    if file_size_kb < 1024:
                        file_size_str = f"{file_size_kb:.2f} KB"
                    elif file_size_kb < 1024 ** 2:
                        file_size_mb = file_size_kb / 1024
                        file_size_str = f"{file_size_mb:.2f} MB"
                    else:
                        file_size_gb = file_size_kb / (1024 ** 2)
                        file_size_str = f"{file_size_gb:.2f} GB"

                    file_type_map = {
                        '.dat': 'application/dat',
                        '.csv': 'CSV',
                        '.xlsx': 'Excel',
                        '.xls': 'Excel',
                        '.txt': 'Text'
                    }
                    file_type = file_type_map.get(file_ext, 'other')

                    item = QTreeWidgetItem(self.file_tree, [file_name, file_type, file_size_str, ""])
                    item.setToolTip(0, file_path)

        self.file_tree.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.file_tree.resizeColumnToContents(0)
        self.file_tree.resizeColumnToContents(1)
        self.file_tree.resizeColumnToContents(2)

    def display_multiple_files(self, file_paths, selected_file_type=None):
        """Display multiple files"""
        current_files = {self.file_tree.topLevelItem(i).text(0): self.file_tree.topLevelItem(i)
                         for i in range(self.file_tree.topLevelItemCount())}

        supported_extensions = ['.dat', '.csv', '.xlsx', '.xls', '.txt']

        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()

            if file_ext not in supported_extensions:
                continue

            if file_name not in current_files:
                self.file_in_list.append(file_path)
                file_info = os.stat(file_path)
                file_size_kb = file_info.st_size / 1024
                if file_size_kb < 1024:
                    file_size_str = f"{file_size_kb:.2f} KB"
                elif file_size_kb < 1024 ** 2:
                    file_size_mb = file_size_kb / 1024
                    file_size_str = f"{file_size_mb:.2f} MB"
                else:
                    file_size_gb = file_size_kb / (1024 ** 2)
                    file_size_str = f"{file_size_gb:.2f} GB"

                file_type_map = {
                    '.dat': 'application/dat',
                    '.csv': 'CSV',
                    '.xlsx': 'Excel',
                    '.xls': 'Excel',
                    '.txt': 'Text'
                }
                file_type = file_type_map.get(file_ext, 'other')

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
        """Handle file selection in tree"""
        self.clear_column_selection()
        selected_items = self.file_tree.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            self.file_path = selected_item.toolTip(0)
            self.open_file_in_table(self.file_path)

    def detect_headers(self, df, file_path):
        """
        Detect if DataFrame has headers or if first row is data
        Returns: (has_headers: bool, df: DataFrame)
        """
        try:
            # Check if first row looks like numeric data
            first_row = df.iloc[0]
            numeric_count = sum(pd.to_numeric(first_row, errors='coerce').notna())

            # If most of first row is numeric and column names are also numeric-like,
            # likely no headers
            col_numeric = sum(pd.to_numeric(df.columns, errors='coerce').notna())

            if numeric_count > len(first_row) * 0.7 and col_numeric > len(df.columns) * 0.5:
                # Likely no headers - first row is data
                return False, df

            return True, df

        except Exception as e:
            # Default to assuming headers exist
            return True, df

    def open_file_in_table(self, file_path):
        """Load and display file data in table view"""
        try:
            df = None
            has_headers = True
            file_ext = Path(file_path).suffix.lower()

            # Load file based on extension
            if file_ext == '.dat':
                try:
                    loaded_file = Loadfile(file_path)
                    headers = loaded_file.column_headers
                    data = loaded_file.data
                    df = pd.DataFrame(data, columns=headers)
                    has_headers = True
                except Exception as e:
                    raise Exception(f"Error loading .dat file: {str(e)}")

            elif file_ext == '.csv':
                # Try with header first
                df = pd.read_csv(file_path)
                has_headers, df = self.detect_headers(df, file_path)

                if not has_headers:
                    # Reload without header
                    df = pd.read_csv(file_path, header=None)
                    df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]

            elif file_ext == '.xlsx':
                df = pd.read_excel(file_path, engine='openpyxl')
                has_headers, df = self.detect_headers(df, file_path)

                if not has_headers:
                    df = pd.read_excel(file_path, engine='openpyxl', header=None)
                    df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]

            elif file_ext == '.xls':
                df = pd.read_excel(file_path)
                has_headers, df = self.detect_headers(df, file_path)

                if not has_headers:
                    df = pd.read_excel(file_path, header=None)
                    df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]

            elif file_ext == '.txt':
                # Try different separators
                df = None
                for sep in ['\t', ',', None]:
                    try:
                        if sep is None:
                            df = pd.read_csv(file_path, delim_whitespace=True)
                        else:
                            df = pd.read_csv(file_path, sep=sep)
                        break
                    except:
                        continue

                if df is None:
                    raise Exception("Unable to parse .txt file format")

                has_headers, df = self.detect_headers(df, file_path)

                if not has_headers:
                    # Reload without header
                    if sep is None:
                        df = pd.read_csv(file_path, delim_whitespace=True, header=None)
                    else:
                        df = pd.read_csv(file_path, sep=sep, header=None)
                    df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]

            else:
                raise Exception(f"Unsupported file type: {file_ext}")

            # Display the dataframe
            if df is not None:
                self.display_dataframe(df)

                # Show info message if no headers detected
                if not has_headers:
                    self.file_selection_display_label.setText(
                        f"File loaded (no headers detected - using Column_1, Column_2, etc.)")
                    self.file_selection_display_label.setStyleSheet("""
                        color: #856404; 
                        font-size: 12px;
                        background-color: #fff3cd; 
                        border-radius: 5px; 
                        padding: 5px;
                    """)

        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error Loading File", f"{str(e)}\n\n{tb_str}")

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
            x_header = self.original_headers.get(self.x_column, f"Column {self.x_column}")
            x_values = []
            for row in range(self.table_model.rowCount()):
                item = self.table_model.item(row, self.x_column)
                x_values.append(item.text() if item else "")
            column_data[x_header] = x_values

            # Add Y columns in the order they were selected
            for col in self.y_columns:
                column_header = self.original_headers.get(col, f"Column {col}")
                column_values = []
                for row in range(self.table_model.rowCount()):
                    item = self.table_model.item(row, col)
                    column_values.append(item.text() if item else "")
                column_data[column_header] = column_values

            # Get file name
            if hasattr(self, 'file_path'):
                file_name = Path(self.file_path).stem
                folder_name = str(Path(self.file_path).parent)
            else:
                file_name = "exported_data"
                folder_name = os.getcwd()

            dialog = QFileDialog(self)
            dialog.setFileMode(QFileDialog.FileMode.Directory)
            dialog.setDirectory(folder_name)

            if dialog.exec():
                folder_name = dialog.selectedFiles()[0]
                export_file_name = os.path.join(folder_name, f"{file_name}.csv")
                self.export_to_csv(column_data, export_file_name)
                QMessageBox.information(self, "Success", f"Data exported to {export_file_name}")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Export failed: {str(e)}\n\n{traceback.format_exc()}")

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
                exported_count = 0
                failed_files = []

                for file in self.file_in_list:
                    try:
                        df = None
                        file_ext = Path(file).suffix.lower()

                        # Load with header detection
                        if file_ext == '.dat':
                            try:
                                loaded_file = Loadfile(file)
                                headers = loaded_file.column_headers
                                data = loaded_file.data
                                df = pd.DataFrame(data, columns=headers)
                            except Exception as e:
                                failed_files.append(f"{Path(file).name} (Loadfile error)")
                                continue

                        elif file_ext == '.csv':
                            df = pd.read_csv(file)
                            has_headers, df = self.detect_headers(df, file)
                            if not has_headers:
                                df = pd.read_csv(file, header=None)
                                df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]

                        elif file_ext == '.xlsx':
                            df = pd.read_excel(file, engine='openpyxl')
                            has_headers, df = self.detect_headers(df, file)
                            if not has_headers:
                                df = pd.read_excel(file, engine='openpyxl', header=None)
                                df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]

                        elif file_ext == '.xls':
                            df = pd.read_excel(file)
                            has_headers, df = self.detect_headers(df, file)
                            if not has_headers:
                                df = pd.read_excel(file, header=None)
                                df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]

                        elif file_ext == '.txt':
                            for sep in ['\t', ',', None]:
                                try:
                                    df = pd.read_csv(file, sep=sep, delim_whitespace=(sep is None))
                                    break
                                except:
                                    continue

                            if df is not None:
                                has_headers, df = self.detect_headers(df, file)
                                if not has_headers:
                                    if sep is None:
                                        df = pd.read_csv(file, delim_whitespace=True, header=None)
                                    else:
                                        df = pd.read_csv(file, sep=sep, header=None)
                                    df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]

                        if df is None:
                            failed_files.append(f"{Path(file).name} (could not load)")
                            continue

                        # Create export dataframe
                        column_data = {}

                        if self.x_column < len(df.columns):
                            x_header = df.columns[self.x_column]
                            column_data[x_header] = df.iloc[:, self.x_column]

                        for col in self.y_columns:
                            if col < len(df.columns):
                                y_header = df.columns[col]
                                column_data[y_header] = df.iloc[:, col]

                        export_df = pd.DataFrame(column_data)
                        file_name = os.path.splitext(os.path.basename(file))[0]
                        export_file_name = os.path.join(folder_name, f"{file_name}.csv")
                        export_df.to_csv(export_file_name, index=False)
                        exported_count += 1

                    except Exception as e:
                        failed_files.append(f"{Path(file).name} ({str(e)})")

                message = f"Successfully exported {exported_count} files to {folder_name}"
                if failed_files:
                    message += f"\n\nFailed: {len(failed_files)} files:\n" + "\n".join(failed_files[:5])
                    if len(failed_files) > 5:
                        message += f"\n... and {len(failed_files) - 5} more"

                QMessageBox.information(self, "Export Complete", message)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Export failed: {str(e)}\n\n{traceback.format_exc()}")

    def export_to_csv(self, column_data, file_name):
        """Export data dictionary to CSV file"""
        try:
            with open(file_name, 'w', newline='') as file:
                writer = csv.writer(file)
                headers = list(column_data.keys())
                writer.writerow(headers)
                for row in zip(*column_data.values()):
                    writer.writerow(row)
        except Exception as e:
            raise Exception(f"Error writing CSV: {str(e)}")

    def open_context_menu(self, position: QPoint):
        """Open the context menu on right-click"""
        menu = QMenu()

        remove_action = QWidgetAction(self)
        remove_label = QLabel("Remove")
        remove_label.setStyleSheet("""
                QLabel {
                    padding: 5px 10px;
                    color: #c0392b;
                    font-weight: bold;
                }
                QLabel:hover {
                    background-color: #ecf0f1;
                }
            """)
        remove_label.mousePressEvent = lambda event: self.handle_remove_click(event)
        remove_action.setDefaultWidget(remove_label)
        menu.addAction(remove_action)
        menu.exec(self.file_tree.viewport().mapToGlobal(position))

    def handle_remove_click(self, event):
        """Handle right-click on remove label"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.file_tree.clearSelection()
            self.clear_column_selection()
            self.remove_selected_item()

    def remove_selected_item(self):
        """Remove the selected item from the tree"""
        selected_item = self.file_tree.currentItem()
        if selected_item:
            file_path = selected_item.toolTip(0)
            if file_path in self.file_in_list:
                self.file_in_list.remove(file_path)
            index = self.file_tree.indexOfTopLevelItem(selected_item)
            if index != -1:
                self.file_tree.takeTopLevelItem(index)

            # Update display label
            count = self.file_tree.topLevelItemCount()
            if count == 0:
                self.file_selection_display_label.setText('Please Upload Files or Directory')
                self.file_selection_display_label.setStyleSheet("""
                        color: white; 
                        font-size: 12px;
                        background-color: #f38d76; 
                        border-radius: 5px; 
                        padding: 5px;
                    """)
            else:
                self.file_selection_display_label.setText(f"{count} Files Loaded")

    def rstpage(self):
        """Reset the page to initial state"""
        try:
            # Clear selections
            self.x_column = None
            self.y_columns = []
            self.file_in_list = []

            try:
                if hasattr(self, 'drag_drop_widget'):
                    try:
                        self.drag_drop_widget.reset()
                    except:
                        pass

                if hasattr(self, 'file_tree'):
                    self.file_tree.clear()

                if hasattr(self, 'table_model'):
                    self.table_model.clear()
                    self.table_model.setRowCount(0)
                    self.table_model.setColumnCount(0)

                if hasattr(self, 'file_selection_display_label'):
                    self.file_selection_display_label.setText('Please Upload Files or Directory')
                    self.file_selection_display_label.setStyleSheet("""
                            color: white; 
                            font-size: 12px;
                            background-color: #f38d76; 
                            border-radius: 5px; 
                            padding: 5px;
                        """)

                if hasattr(self, 'selection_display'):
                    self.selection_display.setText("X: None | Y: None")

                if hasattr(self, 'original_headers'):
                    self.original_headers = {}

            except Exception as e:
                print(f"Reset error: {str(e)}")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Reset failed: {str(e)}")

    def clear_layout(self, layout):
        """Clear all widgets from a layout"""
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                if child.layout() is not None:
                    self.clear_layout(child.layout())

# Main execution
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Create main window
    window = FileExport("Multi-Format")
    window.setWindowTitle("QuDAP - Data Extraction Tool")
    window.setGeometry(100, 100, 1200, 900)
    window.show()

    sys.exit(app.exec())