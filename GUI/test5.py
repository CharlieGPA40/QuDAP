import sys
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
import MultiPyVu as mpv
import traceback

class APIHandler(QObject):
    error_signal = pyqtSignal(str)
    server_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.server = None

    def connect_server(self):
        try:
            self.server = mpv.Server()
            self.server.open()
            self.server_signal.emit(self.server)
        except Exception as e:
            tb_str = traceback.format_exc()
            self.error_signal.emit(f'{tb_str} {str(e)}')

    def disconnect_server(self):
        if self.server:
            self.server.close()
            self.server = None

class ServerThread(QThread):
    def __init__(self, api_handler):
        super().__init__()
        self.api_handler = api_handler
        self.api_handler.error_signal.connect(self.handle_error)

    def run(self):
        self.api_handler.connect_server()

    def handle_error(self, error):
        print(f"Error in server thread: {error}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Server Connection Example')

        self.api_handler = APIHandler()
        self.api_handler.error_signal.connect(self.display_error)
        self.api_handler.server_signal.connect(self.handle_server_connected)

        self.server_thread = None

        self.init_ui()

    def init_ui(self):
        self.status_label = QLabel('Initializing...', self)
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.start_server_thread()

    def start_server_thread(self):
        self.server_thread = ServerThread(self.api_handler)
        self.server_thread.start()

    def handle_server_connected(self, server):
        self.status_label.setText('Server connected successfully.')

    def display_error(self, error_message):
        self.status_label.setText(f'Error: {error_message}')

    def stop_threads(self):
        if self.server_thread:
            self.api_handler.disconnect_server()
            self.server_thread.wait()

    def closeEvent(self, event):
        self.stop_threads()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    # window.start_server_thread()  # Start the server thread here
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
