import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem, QSplitter
from PyQt6.QtCore import Qt, QMimeData, QDir
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

class DragDropWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: lightgray; border: 2px dashed black;")

        self.label = QLabel("Drag and drop a folder here or click the button to select a folder", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("color: blue; font-weight: bold; font-size: 16px;")

        self.button = QPushButton("Select Folder", self)
        self.button.clicked.connect(self.open_folder_dialog)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            folder_path = urls[0].toLocalFile()
            self.label.setText(f"Selected folder: {folder_path}")
            self.parent().display_files(folder_path)

    def open_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.label.setText(f"Selected folder: {folder_path}")
            self.parent().display_files(folder_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Folder Selection and File Browser Example")
        self.setGeometry(100, 100, 800, 600)

        # Create main widget and layout
        main_widget = QWidget(self)
        main_layout = QVBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Create a splitter to separate drag-and-drop area and file browser
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create the drag-and-drop area
        self.drag_drop_widget = DragDropWidget()
        splitter.addWidget(self.drag_drop_widget)

        # Create the file browser area
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Name", "Size", "Comment"])
        splitter.addWidget(self.file_tree)

        # Add splitter to the main layout
        main_layout.addWidget(splitter)

    def display_files(self, folder_path):
        self.file_tree.clear()
        for root, dirs, files in os.walk(folder_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_info = os.stat(file_path)
                file_size = file_info.st_size
                item = QTreeWidgetItem(self.file_tree, [file_name, str(file_size), ""])
                item.setToolTip(0, file_path)

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
