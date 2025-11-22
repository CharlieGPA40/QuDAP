from PyQt6.QtCore import QObject, pyqtSignal
import logging
from datetime import datetime
import os

class HybridLogger(QObject):
    """Logger that combines Qt signals with Python logging"""

    log_signal = pyqtSignal(str, str)  # (message, color)

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HybridLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        super().__init__()
        self._initialized = True

        # Setup Python logging
        self.logger = logging.getLogger('QuDAP')
        self.logger.setLevel(logging.DEBUG)

        # Formatter
        self.formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)

        self.file_handler = None

    def set_log_file(self, filepath):
        """Set log file"""
        if self.file_handler:
            self.logger.removeHandler(self.file_handler)
            self.file_handler.close()

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        self.file_handler = logging.FileHandler(filepath, mode='a', encoding='utf-8')
        self.file_handler.setFormatter(self.formatter)
        self.logger.addHandler(self.file_handler)

    def _log(self, level, message, color):
        """Internal log method"""
        # Log to file/console via Python logging
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(message)

        # Emit Qt signal for GUI
        self.log_signal.emit(message, color)

    def info(self, message):
        self._log('INFO', message, 'black')

    def warning(self, message):
        self._log('WARNING', message, 'orange')

    def error(self, message):
        self._log('ERROR', message, 'red')

    def success(self, message):
        self._log('INFO', message, 'green')

    def debug(self, message):
        self._log('DEBUG', message, 'blue')

    def purple(self, message):
        self._log('INFO', message, 'purple')


# Create singleton
logger = HybridLogger()