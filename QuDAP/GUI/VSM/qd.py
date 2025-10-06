import numpy as np
from PyQt6.QtWidgets import QApplication, QFileDialog


class Loadfile():
    def __init__(self, filename, filedialog=False, *args, **kwargs):
        self.filename = filename
        self.filedialog = filedialog
        self.metadata = {}
        self.data = None
        self.column_headers = []
        self.setas = {}
        self.load_qdfile()

    def load_qdfile(self):
        def string_to_type(s):
            try:
                return int(s)
            except ValueError:
                try:
                    return float(s)
                except ValueError:
                    return s.strip()

        def str2bytes(s):
            if isinstance(s, str):
                return s.encode('utf-8')
            return s

        if self.filedialog:
            app = QApplication([])  # An empty list is passed for the arguments
            # Open file dialog
            dialog = QFileDialog()
            dialog.setNameFilter("DAT files (*.dat);;All files (*.*)")
            dialog.setWindowTitle("Select a .dat file")
            if dialog.exec() == QFileDialog.DialogCode.Accepted:
                self.filename = dialog.selectedFiles()[0]
            else:
                return None  # If no file was selected, return None or raise an error

        self.setas = {}
        i = 0
        with open(self.filename, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if i == 0 and line != "[Header]":
                    print("Not a Quantum Design File !")
                if line == "[Header]" or line.startswith(";") or line == "":
                    continue
                if "[Data]" in line:
                    print('Data found')
                    break
                if "," not in line:
                    print("No data in file!\n")
                parts = [x.strip() for x in line.split(",")]
                if parts[1].split(":")[0] == "SEQUENCE FILE":
                    key = parts[1].split(":")[0].title()
                    value = parts[1].split(":")[1]
                elif parts[0] == "INFO":
                    if parts[1] == "APPNAME":
                        parts[1], parts[2] = parts[2], parts[1]
                    if len(parts) > 2:
                        key = f"{parts[0]}.{parts[2]}"
                    else:
                        print("No data in file!")
                    key = key.title()
                    value = parts[1]
                elif parts[0] in ["BYAPP", "FILEOPENTIME"]:
                    key = parts[0].title()
                    value = " ".join(parts[1:])
                elif parts[0] == "FIELDGROUP":
                    key = f"{parts[0]}.{parts[1]}".title()
                    value = f'[{",".join(parts[2:])}]'
                elif parts[0] == "STARTUPAXIS":
                    axis = parts[1][0].lower()
                    self.setas[axis] = self.setas.get(axis, []) + [int(parts[2])]
                    key = f"Startupaxis-{parts[1].strip()}"
                    value = parts[2].strip()
                else:
                    key = parts[0] + "," + parts[1]
                    key = key.title()
                    value = " ".join(parts[2:])
                self.metadata[key] = string_to_type(value)
            else:
                print("No data in file!")
            self.column_headers = f.readline().strip().split(",")
            data = np.genfromtxt([str2bytes(l) for l in f], dtype="float", delimiter=",", invalid_raise=False)
            if data.shape[0] == 0:
                print("No data in file!")
                data = np.empty((0, len(self.column_headers)))

            if data.shape[1] < len(self.column_headers):
                data = np.append(data, np.ones((data.shape[0], len(self.column_headers) - data.shape[1])) * np.nan, axis=1)
            elif data.shape[1] > len(self.column_headers):
                data = data[:, : len(self.column_headers) - data.shape[1]]
            self.data = data
        self.column_headers = self.column_headers
        # for i in range(len(self.filename) -1, 0, -1):
        #     if self.filename[i] == ".":
        #         file_name = self.filename[: i]
        #     if self.filename[i] == "/":
        #         file_name = file_name[i+1:]
        #         folder_name = self.filename[:i+1]
        #         break
        # with open('{}{}.csv'.format(folder_name, file_name), 'w', encoding='utf-8') as f:
        #     f.write(",".join(self.column_headers) + "\n")
        #     np.savetxt(f, data, delimiter=",", fmt="%s")

        combined_data = np.vstack((self.column_headers, self.data))
        return self.column_headers, self.data, combined_data
#
# loaded_data = Loadfile(None, filedialog=True)  # This will open the PyQt6 file dialog if filename is not provided
