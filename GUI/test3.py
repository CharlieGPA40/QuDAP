import time
from PyQt6.QtCore import QThread, pyqtSignal
from MultiPyVu.exceptions import MultiPyVuError  # Import the specific exception
# import distutils

class DataFetcher(QThread):
    update_data = pyqtSignal(float, str, float, str, str)  # Signal to emit all data
    error_signal = pyqtSignal(str)  # Signal to emit errors

    def __init__(self, client_cls):
        super().__init__()
        self.client_cls = client_cls
        self.running = True

    def run(self):
        try:
            with self.client_cls() as client:
                while self.running:
                    try:
                        T, sT = client.get_temperature()
                        F, sF = client.get_field()
                        try:
                            C = client.get_chamber()
                        except MultiPyVuError as e:
                            C = "Error"
                            self.error_signal.emit(f"Error fetching chamber data: {str(e)}")
                        self.update_data.emit(T, sT, F, sF, C)
                    except Exception as e:
                        self.error_signal.emit(str(e))
                    time.sleep(1)  # Update every second
        except Exception as e:
            self.error_signal.emit(f"Error initializing client: {e}")

    def stop(self):
        self.running = False
        self.wait()  # Ensure the thread stops properly


from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QMessageBox
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt6 Example")
        self.setGeometry(100, 100, 400, 300)
        self.initUI()

    def initUI(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Labels
        self.temperature_label = QLabel('Temperature: --')
        self.field_label = QLabel('Field: --')
        self.chamber_label = QLabel('Chamber: --')

        main_layout.addWidget(self.temperature_label)
        main_layout.addWidget(self.field_label)
        main_layout.addWidget(self.chamber_label)

        # Start the data fetcher thread
        client_cls = MockClient  # Replace with actual client class
        self.thread = DataFetcher(client_cls)
        self.thread.update_data.connect(self.update_labels)
        self.thread.error_signal.connect(self.show_error)
        self.thread.start()

    def update_labels(self, T, sT, F, sF, C):
        self.temperature_label.setText(f'Temperature: {T:.2f} ({sT})')
        self.field_label.setText(f'Field: {F:.2f} ({sF})')
        self.chamber_label.setText(f'Chamber: {C}')

    def show_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()


if __name__ == "__main__":
    class MockClient:
        """Mock client to simulate server methods."""

        def __enter__(self):
            # Simulate connection time
            time.sleep(2)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            # Close connection
            pass

        def get_temperature(self):
            import random
            return random.uniform(20.0, 25.0), 'Celsius'

        def get_field(self):
            import random
            return random.uniform(0.0, 10.0), 'Tesla'

        def get_chamber(self):
            import random
            if random.random() > 0.5:
                raise MultiPyVuError("Simulated chamber error")
            return 'Closed' if random.random() > 0.5 else 'Open'


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
