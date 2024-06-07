import sys
import json
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QThread, pyqtSignal
from websocket import create_connection, WebSocketApp

class UpdateThread(QThread):
    update_received = pyqtSignal(str)

    def run(self):
        self.ws = WebSocketApp("ws://localhost:5000/socket.io/?EIO=4&transport=websocket",
                               on_message=self.on_message)
        self.ws.run_forever()

    def on_message(self, ws, message):
        try:
            message_data = json.loads(message)
            if isinstance(message_data, dict) and message_data.get('type') == 'message':
                self.update_received.emit(message_data['data'])
        except json.JSONDecodeError:
            pass

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.update_thread = UpdateThread()
        self.update_thread.update_received.connect(self.handle_update)
        self.update_thread.start()

    def initUI(self):
        self.setWindowTitle('Real-Time Updates')
        self.setGeometry(100, 100, 400, 200)

        self.layout = QVBoxLayout()

        self.label = QLabel('Waiting for updates...', self)
        self.layout.addWidget(self.label)

        self.setLayout(self.layout)

    def handle_update(self, message):
        self.label.setText(f'Update received: {message}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec())
