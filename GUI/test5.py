import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax1 = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)
        self.setParent(parent)

    def plot(self):
        t = np.arange(0.01, 10.0, 0.01)
        s1 = np.exp(t)
        s2 = np.sin(2 * np.pi * t)

        self.ax1.plot(t, s1, 'b-')
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Exp', color='b')

        self.ax2 = self.ax1.twinx()
        self.ax2.plot(t, s2, 'r.')
        self.ax2.set_ylabel('Sin', color='r')

        self.ax1.grid()
        self.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Double Y-Axis Plot Example')

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.plot_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        layout.addWidget(self.plot_canvas)

        # Call the plot method from the MainWindow
        self.plot_canvas.plot()

        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    sys.exit(app.exec())
