import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Background Image")
        # Set the window dimensions
        self.setGeometry(100, 100, 600, 400)
        # Use a stylesheet to add a background image
        self.setStyleSheet("""
            QMainWindow {
                background-image: url('Icon/background.jpg');
                background-repeat: no-repeat;
                background-position: center;
            }
        """)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
