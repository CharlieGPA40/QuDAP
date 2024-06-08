# ui_component.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox


class UIComponent(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.button1 = QPushButton("Button 1")
        self.button2 = QPushButton("Button 2")

        self.layout.addWidget(self.button1)
        self.layout.addWidget(self.button2)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_page)
        self.layout.addWidget(self.reset_button)

    def clear_layout(self):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            if child.layout() is not None:
                self.clear_layout(child.layout())

    def reset_page(self):
        try:
            print("Clearing layout...")
            # Clear the layout
            # self.clear_layout()
            print("Layout cleared. Reinitializing UI...")
            # Reinitialize the UI
            self.init_ui()
            print("UI reinitialized.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            print(f"Exception caught: {e}")

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.ui_component = UIComponent()
        self.main_layout.addWidget(self.ui_component)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())