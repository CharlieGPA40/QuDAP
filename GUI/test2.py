import time
from PyQt6.QtCore import QThread, pyqtSignal

class DataFetcher(QThread):
    update_data = pyqtSignal(float, str, float, str, str)  # Signal to emit all data

    def __init__(self, client):
        super().__init__()
        self.client = client
        self.running = True

    def run(self):
        while self.running:
            try:
                T, sT = self.client.get_temperature()
                F, sF = self.client.get_field()
                C = self.client.get_chamber()
                self.update_data.emit(T, sT, F, sF, C)
                time.sleep(1)  # Update every second
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

        # Instantiate the client here
        self.client = self.create_client()

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

        # Start the data fetcher thread
        self.thread = DataFetcher(self.client)
        self.thread.update_data.connect(self.update_labels)
        self.thread.start()


    def update_labels(self, T, sT, F, sF, C):
        self.temperature_label.setText(f'Temperature: {T:.2f} ({sT})')
        self.field_label.setText(f'Field: {F:.2f} ({sF})')
        self.chamber_label.setText(f'Chamber: {C}')

    def closeEvent(self, event):
        self.thread.stop()
        self.thread.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
