import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Main vertical layout
        main_layout = QVBoxLayout(self)

        # Create a horizontal layout with a border
        hbox_layout = QHBoxLayout()
        hbox_widget = QWidget()  # Container widget for the horizontal layout
        hbox_widget.setLayout(hbox_layout)
        hbox_widget.setStyleSheet("QWidget { border: 2px solid black; }")

        # Create a vertical layout with a border
        vbox_layout = QVBoxLayout()
        vbox_widget = QWidget()  # Container widget for the vertical layout
        vbox_widget.setLayout(vbox_layout)
        vbox_widget.setStyleSheet("QWidget { border: 2px solid red; }")

        # Add widgets to the horizontal layout
        hbox_layout.addWidget(QPushButton("Button 1"))
        hbox_layout.addWidget(QPushButton("Button 2"))

        # Add widgets to the vertical layout
        vbox_layout.addWidget(QLabel("Enter your name:"))
        vbox_layout.addWidget(QLineEdit())

        # Add the layout widgets to the main layout
        main_layout.addWidget(hbox_widget)
        main_layout.addWidget(vbox_widget)

        self.setLayout(main_layout)
        self.setWindowTitle("Layout Borders Example")

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
