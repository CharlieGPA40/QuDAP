import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox, QHBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, polar=False, title="Plot"):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111, projection='polar' if polar else 'rectilinear')
        self.ax.set_title(title)
        super(MplCanvas, self).__init__(self.fig)

    def plot_data(self, theta, r):
        self.ax.clear()
        self.ax.set_title(self.ax.get_title())  # Keep the existing title
        self.ax.plot(theta, r)
        self.draw()

    def set_polar(self, polar, title):
        self.fig.clear()
        self.ax = self.fig.add_subplot(111, projection='polar' if polar else 'rectilinear')
        self.ax.set_title(title)
        self.draw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_plot_index = 0
        self.plots = [
            {"polar": False, "title": "Cartesian Plot 1"},
            {"polar": False, "title": "Cartesian Plot 2"},
            {"polar": True, "title": "Polar Plot 1"},
            {"polar": True, "title": "Polar Plot 2"}
        ]
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("PyQt6 Multiple Plots Example")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create an initial MplCanvas
        self.canvas = MplCanvas(self.central_widget, polar=self.plots[0]["polar"], title=self.plots[0]["title"])
        self.main_layout.addWidget(self.canvas)

        self.buttons_layout = QHBoxLayout()
        self.next_button = QPushButton("Next Plot")
        self.next_button.clicked.connect(self.next_plot)
        self.buttons_layout.addWidget(self.next_button)

        self.main_layout.addLayout(self.buttons_layout)

        self.plot_data()

    def plot_data(self):
        # Generate data
        self.theta = np.linspace(0, 2 * np.pi, 100)
        self.r = np.abs(np.sin(2 * self.theta) * np.cos(2 * self.theta))

        # Plot data on the canvas
        self.canvas.plot_data(self.theta, self.r)

    def next_plot(self):
        try:
            # Increment plot index
            self.current_plot_index = (self.current_plot_index + 1) % len(self.plots)
            plot_info = self.plots[self.current_plot_index]

            # Update canvas to the new plot type and title
            self.canvas.set_polar(plot_info["polar"], plot_info["title"])

            # Plot the data again with the new settings
            self.plot_data()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
