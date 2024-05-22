import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QFrame


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SHG Simulation Package")
        self.setGeometry(100, 100, 600, 400)

        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Title label
        title_label = QLabel("Please select your function:")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 20px;")
        main_layout.addWidget(title_label)

        # Horizontal layout for Fitting and Simulation
        hor_layout = QHBoxLayout()

        # Fitting frame
        fitting_frame = QFrame()
        fitting_layout = QVBoxLayout()
        fitting_label = QLabel("Fitting")
        fitting_label.setStyleSheet("font-size: 18px;")
        fitting_layout.addWidget(fitting_label)
        fitting_desc = QLabel("Description:")
        fitting_desc.setStyleSheet("background-color: lightgray; padding: 10px;")
        fitting_layout.addWidget(fitting_desc)
        fitting_button = QPushButton("Select")
        fitting_button.setStyleSheet("margin: 10px;")
        fitting_layout.addWidget(fitting_button)
        fitting_frame.setLayout(fitting_layout)
        hor_layout.addWidget(fitting_frame)

        # Simulation frame
        simulation_frame = QFrame()
        simulation_layout = QVBoxLayout()
        simulation_label = QLabel("Simulation")
        simulation_label.setStyleSheet("font-size: 18px;")
        simulation_layout.addWidget(simulation_label)
        simulation_desc = QLabel("Description:")
        simulation_desc.setStyleSheet("background-color: lightgray; padding: 10px;")
        simulation_layout.addWidget(simulation_desc)
        simulation_button = QPushButton("Select")
        simulation_button.setStyleSheet("margin: 10px;")
        simulation_layout.addWidget(simulation_button)
        simulation_frame.setLayout(simulation_layout)
        hor_layout.addWidget(simulation_frame)

        main_layout.addLayout(hor_layout)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
