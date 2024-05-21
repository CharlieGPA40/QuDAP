from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QVBoxLayout,
    QGridLayout, QMessageBox
)
from PyQt6.QtGui import QMouseEvent, QPalette, QColor
from PyQt6.QtCore import Qt, pyqtSignal
import sys

class CustomButtonWidget(QWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Set the widget to be clickable and set a border
        self.setAutoFillBackground(True)
        self.setStyleSheet("""
            QWidget {
                border: 2px solid black;
                border-radius: 5px;
                background-color: lightgrey;
            }
            QWidget:pressed {
                background-color: grey;
            }
        """)

        # Main layout for the custom widget
        main_layout = QVBoxLayout(self)

        # Top label with grey background
        top_label = QLabel("Top Label", self)
        top_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_label.setStyleSheet("background-color: grey; color: white;")
        main_layout.addWidget(top_label)

        # Grid layout for labels and entry boxes
        grid_layout = QGridLayout()

        self.entry_boxes = []
        for i in range(3):
            label = QLabel(f"Label {i+1}")
            entry = QLineEdit()
            grid_layout.addWidget(label, i, 0)
            grid_layout.addWidget(entry, i, 1)
            self.entry_boxes.append(entry)

        main_layout.addLayout(grid_layout)

        # Connect the clicked signal to the handler
        self.clicked.connect(self.on_button_click)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setStyleSheet("""
                QWidget {
                    border: 2px solid black;
                    border-radius: 5px;
                    background-color: grey;
                }
                QWidget:pressed {
                    background-color: darkgrey;
                }
            """)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setStyleSheet("""
                QWidget {
                    border: 2px solid black;
                    border-radius: 5px;
                    background-color: lightgrey;
                }
                QWidget:pressed {
                    background-color: grey;
                }
            """)
            self.clicked.emit()

    def on_button_click(self):
        values = [entry.text() for entry in self.entry_boxes]
        QMessageBox.information(self, "Entry Values", f"Values: {', '.join(values)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt6 Custom Button Example")
        self.setGeometry(100, 100, 400, 300)
        self.initUI()

    def initUI(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Custom button widget
        custom_button_widget = CustomButtonWidget(self)
        main_layout.addWidget(custom_button_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
