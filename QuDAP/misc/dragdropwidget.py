from PyQt6.QtWidgets import (
    QMessageBox, QWidget, QVBoxLayout, QLabel, QFileDialog, QPushButton, QComboBox, QHBoxLayout)
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt

import os

class DragDropWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.initUI()

    def initUI(self):
        with open("GUI/SHG/QButtonWidget.qss", "r") as file:
            self.Browse_Button_stylesheet = file.read()
        with open("GUI/QSS/QComboWidget.qss", "r") as file:
            self.QCombo_stylesheet = file.read()
        self.setAcceptDrops(True)
        self.previous_folder_path = None
        self.setStyleSheet("background-color: #F5F6FA; border: none;")

        self.label = QLabel("Please select the data file type", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: #D4D5D9; font-weight: bold; font-size: 16px;")

        self.button = QPushButton("Browse", self)
        self.button.setStyleSheet(self.Browse_Button_stylesheet)
        self.button.clicked.connect(self.open_folder_dialog)

        self.file_type_selection_layout = QHBoxLayout()
        file_type_label = QLabel("Select File Type:", self)
        file_type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        file_type_label.setStyleSheet("background-color: #FFFFFF; font-size: 16px;")
        self.file_type_selector = QComboBox(self)
        self.file_type_selector.addItems(["Select Type", ".dat", ".csv", ".xls", ".xlsx", ".txt", ])
        self.file_type_selector.setCurrentIndex(0)
        self.file_type_selector.currentIndexChanged.connect(self.fileTypeChange)
        self.file_type_selector.setStyleSheet(self.QCombo_stylesheet)
        self.file_type_selection_layout.addWidget(file_type_label)
        self.file_type_selection_layout.addStretch(1)
        self.file_type_selection_layout.addWidget(self.file_type_selector)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self.file_type_selection_layout)
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

    def fileTypeChange(self):
        self.selected_type = self.file_type_selector.currentText().lower()
        self.label.setText(f"Drag and drop a {self.selected_type} file or folder here")

    def dropEvent(self, event: QDropEvent):
        try:
            urls = event.mimeData().urls()
            if urls:
                paths = [url.toLocalFile() for url in urls]


                # Check if any of the dropped items is a directory
                directories = [path for path in paths if os.path.isdir(path)]
                data_files = [path for path in paths if os.path.isfile(path) and path.lower().endswith(self.selected_type)]

                if directories:
                    for directory in directories:
                        self.main_window.display_files(directory + '/', self.selected_type)

                if data_files:
                    self.main_window.display_multiple_files(data_files, self.selected_type)

                if not directories and not data_files:
                    QMessageBox.warning(self, "Invalid File", f"Please drop a {self.selected_type} file or a folder.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            return

    def open_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.main_window.display_files(folder_path + '/', self.selected_type)

    def reset(self):
        self.previous_folder_path = None
        self.label.setText("Please select the data file type")
        self.file_type_selector.setCurrentIndex(0)

    def get_selected_file_type(self):
        self.selected_type = self.file_type_selector.currentText().lower()
        return self.selected_type