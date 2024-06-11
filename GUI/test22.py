import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget
from PyQt6.QtCore import Qt

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Create a QListWidget
        list_widget = QListWidget(self)

        # Add some items to the QListWidget
        list_widget.addItem("Item 1")
        list_widget.addItem("Item 2")
        list_widget.addItem("Item 3")
        list_widget.addItem("Item 4")
        list_widget.addItem("Item 5")
        list_widget.addItem("Item 6")
        list_widget.addItem("Item 7")

        # Hide the scroll bars
        list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Add the QListWidget to the layout
        layout.addWidget(list_widget)

        self.setLayout(layout)
        self.setWindowTitle('Hide Scroll Bars in QListWidget')
        self.setGeometry(300, 300, 300, 200)

def main():
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
