import sys
from PyQt6.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QMainWindow, QWidget, QGroupBox, QPushButton
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        super(PlotCanvas, self).__init__(self.fig)
        self.setParent(parent)

    def plot(self, data):
        self.ax.clear()
        self.ax.plot(data)
        self.draw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.plot_index = 0
        self.plots = [np.sin(np.linspace(0, 2 * np.pi, 100)),
                      np.cos(np.linspace(0, 2 * np.pi, 100)),
                      np.tan(np.linspace(0, 2 * np.pi, 100))]

        self.initUI()

    def initUI(self):
        self.setWindowTitle('PyQt6 with Matplotlib')

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout(main_widget)

        self.group_box = QGroupBox("Matplotlib Plot")
        group_box_layout = QVBoxLayout()

        self.canvas = PlotCanvas(self, width=5, height=4)
        group_box_layout.addWidget(self.canvas)
        self.group_box.setLayout(group_box_layout)

        layout.addWidget(self.group_box)

        button_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.show_previous_plot)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.show_next_plot)

        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)

        layout.addLayout(button_layout)

        self.show_plot(self.plot_index)

    def show_plot(self, index):
        self.canvas.plot(self.plots[index])

    def show_previous_plot(self):
        self.plot_index = (self.plot_index - 1) % len(self.plots)
        self.show_plot(self.plot_index)

    def show_next_plot(self):
        self.plot_index = (self.plot_index + 1) % len(self.plots)
        self.show_plot(self.plot_index)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
