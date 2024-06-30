import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QCompleter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('QLineEdit with Completer Example')

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.line_edit = QLineEdit(self)
        layout.addWidget(self.line_edit)

        hints = ["apple", "banana", "cherry", "date", "fig", "grape", "kiwi", "lemon", "mango"]
        completer = QCompleter(hints, self.line_edit)
        self.line_edit.setCompleter(completer)

        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    sys.exit(app.exec())
