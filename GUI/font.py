import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget
from PyQt6.QtGui import QFontDatabase

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Available Fonts")
        self.setGeometry(100, 100, 400, 300)

        # Create a central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a QListWidget to display the fonts
        self.font_list_widget = QListWidget(self)

        # Get the list of font families using QFontDatabase
        font_families = QFontDatabase.families()

        # Add font families to the QListWidget
        self.font_list_widget.addItems(font_families)

        # Create and set the layout
        layout = QVBoxLayout(central_widget)
        layout.addWidget(self.font_list_widget)

        central_widget.setLayout(layout)

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
