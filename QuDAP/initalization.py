from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QListWidgetItem, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QAbstractItemView, QFrame, QPushButton, QMessageBox)
from PyQt6.QtGui import QIcon, QFont, QPixmap
from PyQt6.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
import sys
import GUI.FMR.FMR as fmr
import GUI.Setting.Setting as Setting
import GUI.QDesign.PPMS as ppms
import GUI.QDesign.QD as qd
import GUI.VSM.VSM as vsm
import GUI.ETO.ETO as eto
import GUI.SHG.SHG as shg
import GUI.SHG.SHG_General as shg_general
import GUI.QDesign.DSP7265 as dsp
import GUI.QDesign.Keithley2182nv as nv
import GUI.QDesign.Keithley6221 as cs
import GUI.QDesign.BNC845RF as rf
import GUI.QDesign.measurement as m
import GUI.Dashboard.Dashboard as Dashboard
import GUI.Plot.plotting as pt

class Communicator(QObject):
    change_page = pyqtSignal(int, int, int)
# Individual Frames
class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Settings Page")
        layout.addWidget(label)
        self.setLayout(layout)
        self.setStyleSheet("background-color: lightgreen;")


class ProfilePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Profile Page")
        layout.addWidget(label)
        self.setLayout(layout)
        self.setStyleSheet("background-color: lightcoral;")


# Main Window
class MainWindow(QMainWindow):
    def __init__(self, communicator):
        super().__init__()
        self.setWindowTitle("QuDAP")
        self.setWindowIcon(QIcon("GUI/Icon/QEP.svg"))
        self.Listwidgets_Font = 13
        self.ishide = False  # Flag for hide menu; the ture flag means the hide button is selected, vice versa
        self.isinital = True  # Flag for first initialization of the program; this essential to avoid the auto select of hide function
        self.currentindex = 0  # Index for menu bar; this tells which row of the menu bar has been selected (FMR, VSM, etc.)
        self.currentToolIndex = 0  # Index for help menu and setting menu selection
        self.whichSideBar = 0  # Index for which side bar on the left side has been selected; 1 means menu sidebar; 2 means tool menu bar
        self.currentdpindex = 0
        self.communicator = communicator
        self.initUI()

    def initUI(self):
        self.left_sidebar = QListWidget()
        self.left_sidebar.setFont(QFont("Arial", self.Listwidgets_Font))
        with open("GUI/QSS/QListWidget.qss", "r") as file:
            self.QListWidget_stylesheet = file.read()

        with open("GUI/QSS/QListWidget_middle.qss", "r") as file:
            self.QListWidget_middle_stylesheet = file.read()

        self.left_sidebar.setStyleSheet(self.QListWidget_stylesheet)
        dashboard = QListWidgetItem(QIcon("GUI/Icon/Dashboard.svg"), "Dashboard")
        Data_processing = QListWidgetItem(QIcon("GUI/Icon/codesandbox.svg"), "Data Processing")
        experiment = QListWidgetItem(QIcon("GUI/Icon/cpu.svg"), 'Experiment')

        with open("GUI/QSS/QComboWidget.qss", "r") as file:
            self.SideWidget_stylesheet = file.read()

        self.left_sidebar.addItem(dashboard)
        self.left_sidebar.addItem(Data_processing)
        self.left_sidebar.addItem(experiment)
        self.left_sidebar.currentRowChanged.connect(self.update_menu_bar)

        # Left Sidebar
        self.Tool_menu = QListWidget()
        self.Tool_menu.setFont(QFont("Arial", self.Listwidgets_Font))
        self.Tool_menu.setStyleSheet(self.QListWidget_stylesheet)
        tool_home_item = QListWidgetItem(QIcon("GUI/Icon/help-circle.svg"), "Help")
        tool_settings_item = QListWidgetItem(QIcon("GUI/Icon/settings.svg"), "Settings")

        self.Tool_menu.addItem(tool_home_item)
        self.Tool_menu.addItem(tool_settings_item)
        # Disable item selection in the QListWidget
        self.Tool_menu.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.Tool_menu.currentRowChanged.connect(self.update_tool_bar)
        self.Tool_menu.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.Tool_menu.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.Tool_menu.setMinimumHeight(30)

        self.logolayout = QHBoxLayout()
        icon_label = QLabel(self)

        # Load the icon image and set it to the QLabel
        pixmap = QPixmap("GUI/Icon/logo.svg")  # Ensure this path is correct
        resized_pixmap = pixmap.scaled(200,88, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        icon_label.setPixmap(resized_pixmap)
        icon_label.setStyleSheet("background-color: #ECECEB;")

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)  # Horizontal line
        # line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #ff5733;")  # Set the color of the line
        line.setFixedHeight(5)  # Set the thickness of the line
        line.setFixedWidth(170)  # Set the length of the line


        self.logolayout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.logolayout.addStretch(1)
        self.logolayout.setSpacing(0)
        self.logolayout.setContentsMargins(0, 0, 0, 0)
        left_sidebar_layout = QVBoxLayout()
        left_sidebar_layout.addLayout(self.logolayout)
        left_sidebar_layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignCenter)
        # left_sidebar_layout.addStretch(3)
        left_sidebar_layout.addWidget(self.left_sidebar, 12)
        left_sidebar_layout.addStretch(10)

        left_sidebar_layout.addWidget(self.Tool_menu, 3)
        left_sidebar_layout.setSpacing(0)
        left_sidebar_layout.setContentsMargins(2, 0, 0, 0)

        # # Create a main widget to host both the left sidebar and the checkbox
        self.left_sidebar_container = QWidget()
        self.left_sidebar_container.setLayout(left_sidebar_layout)

        # Right Sidebar
        self.right_sidebar = QListWidget()
        self.right_sidebar.setFont(QFont("Arial", self.Listwidgets_Font))
        self.right_sidebar.setStyleSheet(self.QListWidget_middle_stylesheet)
        self.hide_button_container = QWidget()
        self.hide_button_container.setStyleSheet(
            """ 
            QWidget{background-color: #ECECEB  ; border-radius: 15px;}

            """)
        self.hide_button_layout = QVBoxLayout()
        self.hide_button_container.setFixedSize(30,910)
        self.hide_button = QPushButton(QIcon("GUI/Icon/arrow-left.svg"),'')
        self.hide_button.clicked.connect(self.hide_show_right_sidebar)
        self.hide_button.setStyleSheet("""
        QPushButton {
                                       background-color: #ECECEB ; /* Green background */
                                       color: #2b2b2b; /* White text */
                                       border-style: solid;
                                       border-color: #F9F9F9;
                                       border-width: 2px;
                                       border-radius: 5px; /* Rounded corners */
                                       padding: 2px;
                                       min-height: 2px;
                                       max-width: 130px;
                                       font-size: 16px;;
                                   }
                                   QPushButton:hover {
                                       background-color: #CECFCE  ; /* Slightly darker green */
                                   }
                                   QPushButton:pressed {
                                       background-color: #c8c9c8; /* Even darker green */
                                   }""")
        self.hide_button_layout.addWidget(self.hide_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.hide_button_container.setLayout(self.hide_button_layout)
        self.communicator.change_page.connect(self.set_page)
        # Content Pages
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background-color: white;")
        self.pages.addWidget(Dashboard.Dash())  # 0
        self.pages.addWidget(fmr.FMR())  # 1
        self.pages.addWidget(vsm.VSM())  # 2
        self.pages.addWidget(eto.ETO())  # 3
        self.pages.addWidget(shg.SHG())  # 4
        self.pages.addWidget(qd.QD())  # 5
        self.pages.addWidget(Setting.Settings())  # 6
        self.pages.addWidget(ppms.PPMS())  # 7
        self.pages.addWidget(nv.NV())  # 8
        self.pages.addWidget(cs.CurrentSource6221())  # 9
        self.pages.addWidget(rf.BNC845RF())  # 10
        self.pages.addWidget(m.Measurement())  # 11
        self.pages.addWidget(shg_general.General())  # 12
        self.pages.addWidget(pt.plotting())  # 13
        self.pages.addWidget(dsp.Lockin())  # 14

        # self.toggle_dark_mode()
        # Main Layout
        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(self.left_sidebar_container, 1)  # Left sidebar stretch factor 1
        self.main_layout.addWidget(self.hide_button_container, 1)
        self.main_layout.addWidget(self.right_sidebar, 2)  # Right sidebar stretch factor 1

        self.main_layout.addWidget(self.pages, 13)  # Central content area stretch factor 4
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget()
        self.container.setLayout(self.main_layout)
        self.setCentralWidget(self.container)

        # Set initial window size
        self.setMinimumSize(1620,800)

    @pyqtSlot(int, int, int)
    def set_page(self, page, left_sidebar, right_sidebar):
        self.pages.setCurrentIndex(page)
        self.left_sidebar.setCurrentRow(left_sidebar)
        self.right_sidebar.setCurrentRow(right_sidebar)

    def hide_show_right_sidebar(self):
        self.show = self.right_sidebar.isVisible()
        if not self.show:
            try:
                if self.currentindex == 1 or self.currentindex == 2:
                    self.right_sidebar.show()
                    self.hide_button.setIcon(QIcon("GUI/Icon/arrow-left.svg"))
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
        else:
            if self.currentindex == 1 or self.currentindex == 2:
                # self.right_sidebar.show()
                # self.hide_button.setIcon(QIcon("GUI/Icon/arrow-left.svg"))
                self.hide_button.setIcon(QIcon("GUI/Icon/arrow-right.svg"))
                self.right_sidebar.hide()

    def update_menu_bar(self, current_row):
        self.whichSideBar = 1
        self.Tool_menu.setCurrentRow(0)  # Force clearing selection
        self.right_sidebar.clear()

        if current_row == 0:  # FMR
            # self.show = False
            self.right_sidebar.hide()
            self.hide_button.setEnabled(False)
            self.pages.setCurrentIndex(0)
            self.currentindex = 0
        else:
            self.right_sidebar.show()


        if current_row == 1:  # FMR
            self.hide_button.setEnabled(True)
            self.hide_button.setIcon(QIcon("GUI/Icon/arrow-left.svg"))
            FMR = QListWidgetItem(QIcon("GUI/Icon/FMR.svg"), "FMR")
            VSM = QListWidgetItem(QIcon("GUI/Icon/VSM.svg"), "VSM")
            ETO = QListWidgetItem(QIcon("GUI/Icon/ETO.svg"), "ETO")
            SHG = QListWidgetItem(QIcon("GUI/Icon/SHG.svg"), "SHG")
            data_visualization = QListWidgetItem(QIcon("GUI/Icon/bar-chart-2.svg"), "Plotting")
            self.right_sidebar.addItem(QListWidgetItem(FMR))
            self.right_sidebar.addItem(QListWidgetItem(VSM))
            self.right_sidebar.addItem(QListWidgetItem(ETO))
            self.right_sidebar.addItem(QListWidgetItem(SHG))
            self.right_sidebar.addItem(QListWidgetItem(data_visualization))
            self.right_sidebar.currentRowChanged.connect(self.update_data_processing)
            self.right_sidebar.setCurrentRow(7)
            self.pages.setCurrentIndex(0)
            self.currentindex = 1
            # self.left_sidebar.setEnabled(True)

        elif current_row == 2:  # VSM
            self.hide_button.setEnabled(True)
            self.hide_button.setIcon(QIcon("GUI/Icon/arrow-left.svg"))
            self.right_sidebar.addItem(QListWidgetItem("PPMS"))
            self.right_sidebar.addItem(QListWidgetItem("Keithley 2182 NV"))
            self.right_sidebar.addItem(QListWidgetItem("Keithley 6221"))
            self.right_sidebar.addItem(QListWidgetItem("BNC 845 RF"))
            self.right_sidebar.addItem(QListWidgetItem("DSP Lock-in 7265"))
            self.right_sidebar.addItem(QListWidgetItem("Measure"))
            self.right_sidebar.addItem(QListWidgetItem("Quick Test"))
            self.right_sidebar.currentRowChanged.connect(self.update_exp_processing)
            self.right_sidebar.setCurrentRow(7)
            self.pages.setCurrentIndex(0)
            self.currentindex = 2

        elif current_row == 3:  # ETO
            self.right_sidebar.addItem(QListWidgetItem("Edit Profile"))
            self.right_sidebar.addItem(QListWidgetItem("Notifications"))
            self.right_sidebar.addItem(QListWidgetItem("Logout"))
            self.right_sidebar.setCurrentRow(0)
            self.pages.setCurrentIndex(3)
            self.currentindex = 3

        elif current_row == 4:  # SHG
            self.right_sidebar.addItem(QListWidgetItem("General Processing"))
            self.right_sidebar.addItem(QListWidgetItem("Temperature Dependence"))
            self.right_sidebar.addItem(QListWidgetItem("Imaging Mode"))
            self.right_sidebar.currentRowChanged.connect(self.update_SHG)
            self.right_sidebar.setCurrentRow(0)
            self.pages.setCurrentIndex(6)
            self.currentindex = 4


    def update_data_processing(self, current_row):
        if current_row == 0:  # PPMS
            self.right_sidebar.setCurrentRow(0)
            self.pages.setCurrentIndex(1)
            self.currentdpindex = 0

        elif current_row == 1:  # NV
            self.right_sidebar.setCurrentRow(1)
            self.pages.setCurrentIndex(2)
            self.currentqdindex = 1

        elif current_row == 2:  # DC AC Current
            self.right_sidebar.setCurrentRow(2)
            self.pages.setCurrentIndex(3)
            self.currentqdindex = 2

        elif current_row == 3:  # RF
            self.right_sidebar.setCurrentRow(3)
            self.pages.setCurrentIndex(4)
            self.currentqdindex = 3

        elif current_row == 4:  # RF
            self.right_sidebar.setCurrentRow(4)
            self.pages.setCurrentIndex(13)
            self.currentqdindex = 4


    def update_exp_processing(self, current_row):
        if current_row == 0:  # General Processing
            self.right_sidebar.setCurrentRow(0)
            self.pages.setCurrentIndex(7)
            self.currentqdindex = 0

        elif current_row == 1:  # Temp Dep
            self.right_sidebar.setCurrentRow(1)
            self.pages.setCurrentIndex(8)
            self.currentqdindex = 1

        elif current_row == 2:  # Imaging
            self.right_sidebar.setCurrentRow(2)
            self.pages.setCurrentIndex(9)
            self.currentqdindex = 2

        elif current_row == 3:  # Imaging
            self.right_sidebar.setCurrentRow(3)
            self.pages.setCurrentIndex(10)
            self.currentqdindex = 3

        elif current_row == 4:  # Imaging
            self.right_sidebar.setCurrentRow(4)
            self.pages.setCurrentIndex(14)
            self.currentqdindex = 4

        elif current_row == 5:  # Imaging
            self.right_sidebar.setCurrentRow(5)
            self.pages.setCurrentIndex(11)
            self.currentqdindex = 5

        elif current_row == 6:  # Imaging
            self.right_sidebar.setCurrentRow(6)
            self.pages.setCurrentIndex(11)
            self.currentqdindex = 6


    def update_tool_bar(self, current_row):
        self.whichSideBar = 2
        self.right_sidebar.clear()
        self.left_sidebar.setCurrentRow(-1)  # Force clearing selection
        if current_row == 0:  # Home
            self.right_sidebar.addItem(QListWidgetItem("About this Software"))
            self.right_sidebar.addItem(QListWidgetItem("About Us"))
            self.right_sidebar.addItem(QListWidgetItem("Contact"))
            self.Tool_menu.setCurrentRow(0)
            self.pages.setCurrentIndex(5)
            self.currentToolIndex = 0

        elif current_row == 1:  # Settings
            self.right_sidebar.addItem(QListWidgetItem("Theme"))
            self.right_sidebar.addItem(QListWidgetItem("Notification"))
            self.right_sidebar.addItem(QListWidgetItem("Privacy"))
            self.Tool_menu.setCurrentRow(1)
            self.pages.setCurrentIndex(5)
            self.currentToolIndex = 1


def main():
    app = QApplication(sys.argv)
    communicator = Communicator()
    app.setStyleSheet("QWidget { background-color: #ECECEB; }")
    window = MainWindow(communicator)
    window.show()

    app.communicator = communicator
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
