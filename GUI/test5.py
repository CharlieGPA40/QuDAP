import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Log Box Example")

        self.layout = QVBoxLayout()

        self.log_box = QTextEdit(self)
        self.log_box.setReadOnly(True)  # Make the log box read-only

        self.button = QPushButton("Add Log", self)
        self.button.clicked.connect(self.add_log_message)

        self.layout.addWidget(self.log_box)
        self.layout.addWidget(self.button)

        self.container = QWidget()
        self.container.setLayout(self.layout)

        self.setCentralWidget(self.container)

    def add_log_message(self):
        log_message = "This is a log message."
        self.log_box.append(log_message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
