import time
from PyQt6.QtCore import QThread, pyqtSignal

class DataFetcher(QThread):
    print('enter')
    update_data = pyqtSignal(float, str)  # Signal to emit all data

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.running = True

    def run(self):
        while self.running:
            try:
                T, sT = self.client.get_temperature()
                print(T, sT)
                time.sleep(2)
                # F, sF = self.client.get_field()
                # time.sleep(2)
                # C = self.client.get_chamber()
                self.update_data.emit(T, sT)
                time.sleep(2)  # Update every second
            except Exception as e:
                print(f"Error: {e}")
                self.running = False

    def stop(self):
        self.running = False


from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
import sys

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Create labels
        self.temperature_label = QLabel('Temperature: --')
        self.field_label = QLabel('Field: --')
        self.chamber_label = QLabel('Chamber: --')

        # Set up layout
        layout = QVBoxLayout()
        layout.addWidget(self.temperature_label)
        layout.addWidget(self.field_label)
        layout.addWidget(self.chamber_label)
        self.setLayout(layout)
        self.client_keep_going = True

        # Start the data fetcher thread
        import MultiPyVu as mpv
        with mpv.Server() as self.server:
            with mpv.Client() as self.client:
                while self.client_keep_going:
                    time.sleep(2)
                    # T, sT = self.client.get_temperature()
                    # print(T, sT)
                    self.thread = DataFetcher(self.client)
                    self.thread.update_data.connect(self.update_labels)
                    self.thread.start()

    def update_labels(self, T, sT):
        self.temperature_label.setText(f'Temperature: {T:.2f} ({sT})')
        # self.field_label.setText(f'Field: {F:.2f} ({sF})')
        # self.chamber_label.setText(f'Chamber: {C}')

    def closeEvent(self, event):
        self.thread.stop()
        self.thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)


    class MockClient:
        """Mock client to simulate server methods."""

        def get_temperature(self):
            import random
            return random.uniform(20.0, 25.0), 'Celsius'

        def get_field(self):
            import random
            return random.uniform(0.0, 10.0), 'Tesla'

        def get_chamber(self):
            import random
            return 'Closed' if random.random() > 0.5 else 'Open'
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
