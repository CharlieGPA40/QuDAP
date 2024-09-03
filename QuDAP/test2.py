import sys
import csv
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, \
    QWidget, QFileDialog, QHeaderView
from PyQt6.QtCore import Qt


class CSVTable(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CSV Viewer")
        self.setGeometry(100, 100, 800, 600)

        self.table_widget = QTableWidget()
        self.table_widget.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        load_button = QPushButton("Load CSV")
        load_button.clicked.connect(self.load_csv)

        export_button = QPushButton("Export Selected Indices")
        export_button.clicked.connect(self.export_selected_indices)

        layout = QVBoxLayout()
        layout.addWidget(load_button)
        layout.addWidget(self.table_widget)
        layout.addWidget(export_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_csv(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("CSV files (*.csv)")
        if file_dialog.exec():
            file_name = file_dialog.selectedFiles()[0]
            self.populate_table(file_name)

    def populate_table(self, file_name):
        with open(file_name, newline='') as csv_file:
            reader = csv.reader(csv_file)
            headers = next(reader)
            self.table_widget.setColumnCount(len(headers))
            self.table_widget.setHorizontalHeaderLabels(headers)

            self.table_widget.setRowCount(0)
            for row_data in reader:
                row = self.table_widget.rowCount()
                self.table_widget.insertRow(row)
                for column, item in enumerate(row_data):
                    self.table_widget.setItem(row, column, QTableWidgetItem(item))

        self.table_widget.resizeColumnsToContents()
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def export_selected_indices(self):
        selected_rows = set()
        selected_columns = set()

        for item in self.table_widget.selectedItems():
            selected_rows.add(item.row())
            selected_columns.add(item.column())

        print("Selected Rows:", sorted(selected_rows))
        print("Selected Columns:", sorted(selected_columns))

        # Here, you can also write the selected indices to a file if needed.


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CSVTable()
    window.show()
    sys.exit(app.exec())
