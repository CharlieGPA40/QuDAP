import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLineEdit, QVBoxLayout, QWidget
from PyQt6.QtGui import QDoubleValidator

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("QDoubleValidator Example")
        self.setGeometry(100, 100, 400, 200)

        # Create a QLineEdit widget
        self.line_edit = QLineEdit(self)

        # Create a QDoubleValidator
        validator = QDoubleValidator(-999.99, 999.99, 2, self)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)

        # Set the validator to the QLineEdit
        self.line_edit.setValidator(validator)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.line_edit)

        # Create a central widget and set the layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
