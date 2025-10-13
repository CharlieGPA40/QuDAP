import sys
import pyvisa
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem,
                             QLabel, QStatusBar, QProgressBar, QTextEdit, QSplitter,
                             QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QColor, QFont


class InstrumentScanner(QThread):
    """Background thread for scanning instruments"""

    progress = pyqtSignal(int, str)  # Progress percentage and message
    finished = pyqtSignal(dict)  # Results dictionary
    error = pyqtSignal(str)  # Error message

    def __init__(self, timeout=2000):
        super().__init__()
        self.timeout = timeout
        self.is_running = True

    def query_instrument_id(self, inst):
        """Try multiple identification commands"""
        id_commands = [
            "*IDN?", "ID?", "ID", "*ID?", "IDENTIFY?",
            "MODEL?", "I", "++ver", "VER?", "VERSION?"
        ]

        for cmd in id_commands:
            try:
                response = inst.query(cmd).strip()
                if response and len(response) > 0:
                    return (response, cmd)
            except:
                continue

        return (None, None)

    def categorize_instrument(self, resource_name):
        """Determine connection type"""
        if "GPIB" in resource_name:
            return "GPIB"
        elif "USB" in resource_name:
            return "USB"
        elif "TCPIP" in resource_name:
            return "Ethernet"
        elif "ASRL" in resource_name:
            return "Serial"
        elif "PXI" in resource_name:
            return "PXI"
        else:
            return "Other"

    def run(self):
        """Scan for instruments"""
        try:
            rm = pyvisa.ResourceManager()

            self.progress.emit(10, "Initializing VISA...")

            resources = rm.list_resources()

            if not resources:
                self.finished.emit({})
                return

            # Organize by type
            instruments_by_type = {
                "GPIB": [],
                "USB": [],
                "Ethernet": [],
                "Serial": [],
                "PXI": [],
                "Other": []
            }

            total = len(resources)

            for idx, resource in enumerate(resources):
                if not self.is_running:
                    break

                progress_pct = 10 + int((idx / total) * 80)
                self.progress.emit(progress_pct, f"Scanning {resource}...")

                conn_type = self.categorize_instrument(resource)

                instrument_info = {
                    "resource": resource,
                    "id": "Unknown",
                    "command": None,
                    "status": "Not responding",
                    "error": None
                }

                try:
                    inst = rm.open_resource(resource)
                    inst.timeout = self.timeout

                    try:
                        inst.read_termination = '\n'
                        inst.write_termination = '\n'
                    except:
                        pass

                    idn, cmd_used = self.query_instrument_id(inst)

                    if idn:
                        instrument_info["id"] = idn
                        instrument_info["command"] = cmd_used
                        instrument_info["status"] = "Connected"
                    else:
                        instrument_info["status"] = "No ID response"

                    inst.close()

                except Exception as e:
                    instrument_info["status"] = "Error"
                    instrument_info["error"] = str(e)

                instruments_by_type[conn_type].append(instrument_info)

            self.progress.emit(100, "Scan complete!")
            self.finished.emit(instruments_by_type)

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        """Stop the scanning thread"""
        self.is_running = False


class InstrumentDetector(QWidget):
    def __init__(self):
        super().__init__()
        self.scanner_thread = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        titlefont = QFont("Arial", 20)
        self.setStyleSheet("background-color: white;")
        self.current_intrument_label = QLabel("Current Connection")
        self.current_intrument_label.setFont(titlefont)
        self.current_intrument_label.setStyleSheet("""
                                                    QLabel{
                                                        background-color: white;
                                                        }
                                                        """)
        title_layout.addWidget(self.current_intrument_label)
        main_layout.addLayout(title_layout)
        with open("GUI/QSS/QButtonWidget.qss", "r") as file:
            self.Button_stylesheet = file.read()
        # Top controls
        controls_layout = QHBoxLayout()
        self.scan_button = QPushButton("🔍 Scan")
        # self.scan_button.setFixedHeight(40)
        self.scan_button.setStyleSheet(self.Button_stylesheet)
        self.scan_button.clicked.connect(self.scan_instruments)

        self.refresh_button = QPushButton("🔄 Refresh")
        # self.refresh_button.setFixedHeight(40)
        self.refresh_button.setStyleSheet(self.Button_stylesheet)
        self.refresh_button.clicked.connect(self.scan_instruments)

        self.test_button = QPushButton("🔧 Test")
        # self.test_button.setFixedHeight(40)
        self.test_button.setStyleSheet(self.Button_stylesheet)
        self.test_button.clicked.connect(self.test_selected_instrument)
        self.test_button.setEnabled(False)

        controls_layout.addWidget(self.scan_button)
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addWidget(self.test_button)
        controls_layout.addStretch()

        main_layout.addLayout(controls_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Splitter for tree and details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - Instrument tree
        tree_group = QGroupBox("Detected Instruments")
        tree_layout = QVBoxLayout()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Connection Type / Instrument", "Status"])
        self.tree.setColumnWidth(0, 500)
        self.tree.itemSelectionChanged.connect(self.on_selection_changed)
        tree_layout.addWidget(self.tree)

        tree_group.setLayout(tree_layout)
        splitter.addWidget(tree_group)

        # Right side - Details panel
        details_group = QGroupBox("Instrument Details")
        details_layout = QVBoxLayout()

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)

        details_group.setLayout(details_layout)
        splitter.addWidget(details_group)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        splitter.setFixedHeight(650)
        main_layout.addWidget(splitter)

        # Status bar
        self.status_label = QLabel("Ready. Click 'Scan Instruments' to begin.")
        self.status_label.setFixedHeight(30)
        self.status_label.setStyleSheet("QLabel { padding: 5px; background-color: #f0f0f0; }")
        main_layout.addWidget(self.status_label)

        # Store instrument data
        self.instruments_data = {}

    def scan_instruments(self):
        """Start scanning for instruments"""
        if self.scanner_thread and self.scanner_thread.isRunning():
            return

        self.scan_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.test_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.tree.clear()
        self.details_text.clear()

        self.scanner_thread = InstrumentScanner(timeout=2000)
        self.scanner_thread.progress.connect(self.update_progress)
        self.scanner_thread.finished.connect(self.scan_finished)
        self.scanner_thread.error.connect(self.scan_error)
        self.scanner_thread.start()

    def update_progress(self, value, message):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def scan_finished(self, instruments_by_type):
        """Handle scan completion"""
        self.instruments_data = instruments_by_type

        # Populate tree
        total_count = 0
        connection_icons = {
            "GPIB": "📟",
            "USB": "🔌",
            "Ethernet": "🌐",
            "Serial": "🔗",
            "PXI": "💾",
            "Other": "❓"
        }

        for conn_type in ["GPIB", "USB", "Ethernet", "Serial", "PXI", "Other"]:
            instruments = instruments_by_type.get(conn_type, [])

            if instruments:
                # Create parent item for connection type
                icon = connection_icons.get(conn_type, "")
                parent = QTreeWidgetItem(self.tree)
                parent.setText(0, f"{icon} {conn_type} ({len(instruments)})")
                parent.setExpanded(True)

                # Set bold font for parent
                font = parent.font(0)
                font.setBold(True)
                parent.setFont(0, font)

                # Add child items for each instrument
                for inst in instruments:
                    child = QTreeWidgetItem(parent)
                    child.setText(0, inst["resource"])
                    child.setText(1, inst["status"])

                    # Color code by status
                    if inst["status"] == "Connected":
                        child.setForeground(1, QColor(0, 150, 0))
                        total_count += 1
                    elif inst["status"] == "No ID response":
                        child.setForeground(1, QColor(200, 150, 0))
                        total_count += 1
                    else:
                        child.setForeground(1, QColor(200, 0, 0))

                    # Store full data
                    child.setData(0, Qt.ItemDataRole.UserRole, inst)

        self.progress_bar.setVisible(False)
        self.scan_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.status_label.setText(f"Scan complete. Found {total_count} responding instrument(s).")

    def scan_error(self, error_msg):
        """Handle scan error"""
        self.progress_bar.setVisible(False)
        self.scan_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        QMessageBox.critical(self, "Scan Error", f"Error during scan:\n{error_msg}")

    def on_selection_changed(self):
        """Handle tree selection change"""
        selected_items = self.tree.selectedItems()

        if not selected_items:
            self.details_text.clear()
            self.test_button.setEnabled(False)
            return

        item = selected_items[0]
        inst_data = item.data(0, Qt.ItemDataRole.UserRole)

        if inst_data:
            # Display details
            details = f"<h3>Instrument Details</h3>"
            details += f"<b>Resource:</b> {inst_data['resource']}<br>"
            details += f"<b>Status:</b> {inst_data['status']}<br>"

            if inst_data['command']:
                details += f"<b>ID Command:</b> {inst_data['command']}<br>"

            if inst_data['id'] != "Unknown":
                details += f"<b>Identification:</b><br><pre>{inst_data['id']}</pre>"

            if inst_data.get('error'):
                details += f"<br><b>Error:</b> <font color='red'>{inst_data['error']}</font>"

            self.details_text.setHtml(details)
            self.test_button.setEnabled(True)
        else:
            self.details_text.clear()
            self.test_button.setEnabled(False)

    def test_selected_instrument(self):
        """Test communication with selected instrument"""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        inst_data = item.data(0, Qt.ItemDataRole.UserRole)

        if not inst_data:
            return

        resource = inst_data['resource']

        try:
            rm = pyvisa.ResourceManager()
            inst = rm.open_resource(resource)
            inst.timeout = 3000

            # Try common test commands
            test_results = "<h3>Test Results</h3>"
            test_results += f"<b>Testing:</b> {resource}<br><br>"

            commands = ["ID", "*IDN?", "ID?", "*RST", "*TST?"]

            for cmd in commands:
                try:
                    if "?" in cmd:
                        response = inst.query(cmd).strip()
                        test_results += f"<b>{cmd}</b>: {response}<br>"
                    else:
                        inst.write(cmd)
                        test_results += f"<b>{cmd}</b>: OK (write only)<br>"
                except Exception as e:
                    test_results += f"<b>{cmd}</b>: <font color='red'>Failed - {str(e)[:50]}</font><br>"

            inst.close()
            self.details_text.setHtml(test_results)

        except Exception as e:
            QMessageBox.warning(self, "Test Error", f"Could not test instrument:\n{str(e)}")

    def closeEvent(self, event):
        """Handle window close"""
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.scanner_thread.stop()
            self.scanner_thread.wait()
        event.accept()


# def main():
#     app = QApplication(sys.argv)
#     window = InstrumentDetector()
#     window.show()
#     sys.exit(app.exec())
#
#
# if __name__ == "__main__":
#     main()