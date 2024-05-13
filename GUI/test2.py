import sys
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QRadioButton,
                             QHBoxLayout, QGroupBox, QPushButton)

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

    def plot(self, plot_type='line'):
        self.axes.clear()
        if plot_type == 'line':
            self.axes.plot([1, 2, 3, 4, 5], [1, 4, 9, 16, 25], 'r')
        elif plot_type == 'scatter':
            self.axes.scatter([1, 2, 3, 4, 5], [1, 4, 9, 16, 25])
        elif plot_type == 'bar':
            self.axes.bar([1, 2, 3, 4, 5], [1, 4, 9, 16, 25])
        self.axes.set_title(f'{plot_type.capitalize()} Plot')
        self.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)

        self.plot_canvas = PlotCanvas(self, width=5, height=4)
        layout.addWidget(self.setup_radio_buttons())
        layout.addWidget(self.plot_canvas)

        self.setWindowTitle("PyQt6 Matplotlib Example")
        self.setGeometry(100, 100, 800, 600)

    def setup_radio_buttons(self):
        group_box = QGroupBox("Plot Types")
        hbox_layout = QHBoxLayout()

        # Creating radio buttons
        line_btn = QRadioButton("Line Plot")
        line_btn.setChecked(True)
        line_btn.plot_type = 'line'
        scatter_btn = QRadioButton("Scatter Plot")
        scatter_btn.plot_type = 'scatter'
        bar_btn = QRadioButton("Bar Plot")
        bar_btn.plot_type = 'bar'

        # Connecting signals
        line_btn.toggled.connect(self.on_radio_button_toggled)
        scatter_btn.toggled.connect(self.on_radio_button_toggled)
        bar_btn.toggled.connect(self.on_radio_button_toggled)

        # Adding to layout
        hbox_layout.addWidget(line_btn)
        hbox_layout.addWidget(scatter_btn)
        hbox_layout.addWidget(bar_btn)
        group_box.setLayout(hbox_layout)

        return group_box

    def on_radio_button_toggled(self):
        radio_button = self.sender()
        if radio_button.isChecked():
            self.plot_canvas.plot(radio_button.plot_type)

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
