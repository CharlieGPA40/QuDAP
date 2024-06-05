from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QListWidgetItem, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QRadioButton, QAbstractItemView)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import QSize, Qt
import sys
import GUI.FMR.FMR as fmr
import GUI.Setting.Setting as Setting
import GUI.QDesign.PPMS as ppms
import GUI.QDesign.QD as qd
import GUI.VSM.VSM as vsm
import GUI.ETO.ETO as eto
import GUI.SHG.SHG as shg
import GUI.SHG.SHG_General as shg_general
import GUI.SHG.SHG_Temp_Dep as shg_tempdep
import GUI.SHG.SHG_Imaging as shg_imaging
import GUI.QDesign.Keithley2182nv as nv
import GUI.QDesign.Keithley6221 as cs
import GUI.QDesign.BNC845RF as rf
import GUI.QDesign.measurement as m
import GUI


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
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quantum Data Processing")
        self.setWindowIcon(QIcon("Icon/QEP.svg"))
        self.Listwidgets_Font = 15
        self.ishide = False  # Flag for hide menu; the ture flag means the hide button is selected, vice versa
        self.isinital = True  # Flag for first initialization of the program; this essential to avoid the auto select of hide function
        self.currentindex = 0  # Index for menu bar; this tells which row of the menu bar has been selected (FMR, VSM, etc.)
        self.currentToolIndex = 0  # Index for help menu and setting menu selection
        self.whichSideBar = 0  # Index for which side bar on the left side has been selected; 1 means menu sidebar; 2 means tool menu bar
        self.currentqdindex = 0
        self.initUI()

    def initUI(self):
        self.left_sidebar = QListWidget()
        self.left_sidebar.setFont(QFont("Arial", self.Listwidgets_Font))
        self.left_sidebar.setStyleSheet("""
            QListWidget {
                outline: none;  /* Removes focus outline */
                
            }
            QListWidget::item {
                border: none;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #E0E0E0;  /* Background color for selected item */
                border-left: 5px solid #0078D7;  /* Blue color bar on the left */
            }
            QListWidget::item:hover {
                background-color: #F0F0F0;  /* Light grey background on hover */
            }
            
        """)

        FMR = QListWidgetItem(QIcon("Icon/FMR.svg"), "FMR")
        VSM = QListWidgetItem(QIcon("Icon/VSM.svg"), "VSM")
        ETO = QListWidgetItem(QIcon("Icon/ETO.svg"), "ETO")
        SHG = QListWidgetItem(QIcon("Icon/SHG.svg"), "SHG")
        PPMS = QListWidgetItem(QIcon("Icon/PPMS.svg"), "Quantum Design")

        self.left_sidebar.addItem(FMR)
        self.left_sidebar.addItem(VSM)
        self.left_sidebar.addItem(ETO)
        self.left_sidebar.addItem(SHG)
        self.left_sidebar.addItem(PPMS)
        self.left_sidebar.currentRowChanged.connect(self.update_menu_bar)

        # Left Sidebar
        self.Tool_menu = QListWidget()
        self.Tool_menu.setFont(QFont("Arial", self.Listwidgets_Font))
        self.Tool_menu.setStyleSheet("""
                QListWidget {
                outline: none;  /* Removes focus outline */
            }
            QListWidget::item {
                border: none;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #E0E0E0;  /* Background color for selected item */
                border-left: 5px solid #0078D7;  /* Blue color bar on the left */
            }
            QListWidget::item:hover {
                background-color: #F0F0F0;  /* Light grey background on hover */
            }
               """)
        tool_home_item = QListWidgetItem(QIcon("Icon/help-circle.svg"), "Help")
        tool_settings_item = QListWidgetItem(QIcon("Icon/settings.svg"), "Settings")

        self.Tool_menu.addItem(tool_home_item)
        self.Tool_menu.addItem(tool_settings_item)
        # Disable item selection in the QListWidget
        self.Tool_menu.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.Tool_menu.currentRowChanged.connect(self.update_tool_bar)

        self.Tool_menu.setMinimumHeight(30)
        # Left Sidebar hide menu
        self.hide_menu = QListWidget()
        self.hide_menu.setFont(QFont("Arial", self.Listwidgets_Font))
        self.hide_menu.setStyleSheet("""
                    QListWidget {
                        outline: none;  /* Removes focus outline */
                    }
                    QListWidget::item {
                        border: none;
                        padding: 5px;
                    }
                
                    QListWidget::item:selected {
                        background-color: #E0E0E0;  /* Background color for selected item */
                        border-lefft: 0px solid #E0E0E0;  /* Blue color bar on the left */
                    }
                    QListWidget::item:hover {
                        background-color: #F0F0F0;  /* Light grey background on hover */
                    }
                       """)
        hide_menu_item = QListWidgetItem(QIcon("Icon/align-justify.svg"), "Hide")

        self.hide_menu.addItem(hide_menu_item)
        # Disable item selection in the QListWidget
        self.hide_menu.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        # Layo

        self.hide_menu.currentRowChanged.connect(self.hide_left_sidebar)
        # self.hide_menu.setFixedWidth(200)  # Sets a fixed width for the sidebar
        self.hide_menu.setMinimumHeight(40)  # Sets a minimum height while allowing expansion

        left_sidebar_layout = QVBoxLayout()
        left_sidebar_layout.addWidget(self.hide_menu, 1)
        left_sidebar_layout.addWidget(self.left_sidebar, 18)
        left_sidebar_layout.addStretch()
        left_sidebar_layout.addWidget(self.Tool_menu, 2)
        left_sidebar_layout.setSpacing(0)
        left_sidebar_layout.setContentsMargins(2, 0, 0, 0)

        # # Create a main widget to host both the left sidebar and the checkbox
        self.left_sidebar_container = QWidget()
        self.left_sidebar_container.setLayout(left_sidebar_layout)

        # Right Sidebar
        self.right_sidebar = QListWidget()
        self.right_sidebar.setFont(QFont("Arial", self.Listwidgets_Font))
        self.right_sidebar.setStyleSheet("""
            QListWidget {
                outline: none;  /* Removes focus outline */
            }
            QListWidget::item {
                border: none;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #E0E0E0;  /* Background color for selected item */
                border-left: 5px solid #0078D7;  /* Blue color bar on the left */
            }
            QListWidget::item:hover {
                background-color: #F0F0F0;  /* Light grey background on hover */
            }
        """)

        # Content Pages
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background-color: white;")
        self.pages.addWidget(fmr.FMR())  # 0
        self.pages.addWidget(vsm.VSM())  # 1
        self.pages.addWidget(eto.ETO())  # 2
        self.pages.addWidget(shg.SHG())  # 3
        self.pages.addWidget(qd.QD())  # 4
        self.pages.addWidget(Setting.Settings())  # 5
        self.pages.addWidget(ppms.PPMS())  # 6
        self.pages.addWidget(nv.NV())  # 7
        self.pages.addWidget(cs.CurrentSource6221())  # 8
        self.pages.addWidget(rf.BNC845RF())  # 9
        self.pages.addWidget(m.Measurement())  # 10
        self.pages.addWidget(shg_general.General())  # 11
        self.pages.addWidget(shg_tempdep.Tempdep())  # 12
        self.pages.addWidget(shg_imaging.Imaging())  # 13

        # self.toggle_dark_mode()
        # Main Layout
        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(self.left_sidebar_container, 3)  # Left sidebar stretch factor 1
        self.main_layout.addWidget(self.right_sidebar, 4)  # Right sidebar stretch factor 1
        self.main_layout.addWidget(self.pages, 10)  # Central content area stretch factor 4
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget()
        self.container.setLayout(self.main_layout)
        self.setCentralWidget(self.container)

        # Set initial window size
        self.resize(1500, 800)

    def toggle_dark_mode(self):
        # if is_checked == 0:
        print("ENTER DARK")
        self.apply_dark_mode()
        # elif is_checked == 1:
        print("ENTER Bright")
        self.apply_light_mode()

    def apply_dark_mode(self):
        self.setStyleSheet("""
               QMainWindow {
                   background-color: #2E2E2E;
                   color: white;
               }
               QListWidget {
                   background-color: #3B3B3B;
                   color: #FFFFFF;
                   border: none;
                   font-size: 24px;
               }
               QListWidget::item:selected {
                   background-color: #595959;
               }
               # QCheckBox {
               #     color: #FFFFFF;
               # }
           """)

    def apply_light_mode(self):
        self.setStyleSheet("""
               QMainWindow {
                   background-color: #E0E0E0;
                   color: black;
               }
               QListWidget {
                   background-color: #FFFFFF;
                   color: black;
                   border: none;
                   font-size: 24px;
               }
               QListWidget::item:selected {
                   background-color: #C0C0C0;
               }
               # QCheckBox {
               #     color: black;
               # }
           """)

    def hide_left_sidebar(self):
        if self.ishide == False and self.isinital == False:
            self.hide_menu.clear()
            self.Tool_menu.clear()
            FMR = QListWidgetItem(QIcon("Icon/FMR.svg"), "")
            VSM = QListWidgetItem(QIcon("Icon/VSM.svg"), "")
            ETO = QListWidgetItem(QIcon("Icon/ETO.svg"), "")
            SHG = QListWidgetItem(QIcon("Icon/SHG.svg"), "")
            PPMS = QListWidgetItem(QIcon("Icon/PPMS.svg"), "")
            self.left_sidebar.clear()
            self.left_sidebar.addItem(FMR)
            self.left_sidebar.addItem(VSM)
            self.left_sidebar.addItem(ETO)
            self.left_sidebar.addItem(SHG)
            self.left_sidebar.addItem(PPMS)
            # self.left_sidebar.currentRowChanged.connect(self.update_right_sidebar)

            tool_home_item = QListWidgetItem(QIcon("Icon/help-circle.svg"), "")
            tool_settings_item = QListWidgetItem(QIcon("Icon/settings.svg"), "")
            self.Tool_menu.addItem(tool_home_item)
            self.Tool_menu.addItem(tool_settings_item)

            hide_menu_item = QListWidgetItem(QIcon("Icon/align-justify.svg"), "")
            self.hide_menu.addItem(hide_menu_item)
            # self.hide_menu.currentRowChanged.connect(self.hide_left_sidebar)
            self.ishide = True

            left_sidebar_layout = QVBoxLayout()
            left_sidebar_layout.addWidget(self.hide_menu, 1)
            left_sidebar_layout.addWidget(self.left_sidebar, 18)
            left_sidebar_layout.addStretch()
            left_sidebar_layout.addWidget(self.Tool_menu, 3)
            left_sidebar_layout.setSpacing(0)
            left_sidebar_layout.setContentsMargins(2, 0, 0, 0)

            self.main_layout = QHBoxLayout()
            self.main_layout.addWidget(self.left_sidebar_container, 1)  # Left sidebar stretch factor 1
            self.main_layout.addWidget(self.right_sidebar, 5)  # Right sidebar stretch factor 1
            self.main_layout.addWidget(self.pages, 30)  # Central content area stretch factor 4
            self.main_layout.setSpacing(0)
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.container = QWidget()
            self.container.setLayout(self.main_layout)
            self.setCentralWidget(self.container)
        else:
            self.initUI()
            self.ishide = False
            self.isinital = False

        if self.whichSideBar == 1:
            self.left_sidebar.setCurrentRow(self.currentindex)
            self.update_menu_bar(self.currentindex)
            self.update_qd(self.currentqdindex)
        #     place to add more page
        elif self.whichSideBar == 2:
            self.Tool_menu.setCurrentRow(self.currentToolIndex)
            self.update_tool_bar(self.currentToolIndex)

    def update_menu_bar(self, current_row):
        self.whichSideBar = 1
        self.Tool_menu.setCurrentRow(-1)  # Force clearing selection
        self.right_sidebar.clear()
        if current_row == 0:  # FMR
            self.right_sidebar.addItem(QListWidgetItem("RAW Data Processing"))
            self.right_sidebar.addItem(QListWidgetItem("Data Interpolation"))
            self.right_sidebar.addItem(QListWidgetItem("Heatmap Generation"))
            self.right_sidebar.addItem(QListWidgetItem("FMR Profile Fitting"))
            self.right_sidebar.addItem(QListWidgetItem("Kittel Fitting"))
            self.right_sidebar.setCurrentRow(0)
            self.pages.setCurrentIndex(0)
            self.currentindex = 0
            # self.left_sidebar.setEnabled(True)

        elif current_row == 1:  # VSM
            self.right_sidebar.addItem(QListWidgetItem("General Settings"))
            self.right_sidebar.addItem(QListWidgetItem("Security"))
            self.right_sidebar.addItem(QListWidgetItem("Privacy"))
            self.right_sidebar.setCurrentRow(1)
            self.pages.setCurrentIndex(1)
            self.currentindex = 1

        elif current_row == 2:  # ETO
            self.right_sidebar.addItem(QListWidgetItem("Edit Profile"))
            self.right_sidebar.addItem(QListWidgetItem("Notifications"))
            self.right_sidebar.addItem(QListWidgetItem("Logout"))
            self.right_sidebar.setCurrentRow(2)
            self.pages.setCurrentIndex(2)
            self.currentindex = 2

        elif current_row == 3:  # SHG
            self.right_sidebar.addItem(QListWidgetItem("General Processing"))
            self.right_sidebar.addItem(QListWidgetItem("Temperature Dependence"))
            self.right_sidebar.addItem(QListWidgetItem("Imaging Mode"))
            self.right_sidebar.currentRowChanged.connect(self.update_SHG)
            self.right_sidebar.setCurrentRow(3)
            self.pages.setCurrentIndex(3)
            self.currentindex = 3

        elif current_row == 4:  # PPMS
            self.right_sidebar.addItem(QListWidgetItem("PPMS"))
            self.right_sidebar.addItem(QListWidgetItem("Keithley 2182 NV"))
            self.right_sidebar.addItem(QListWidgetItem("Keithley 6221"))
            self.right_sidebar.addItem(QListWidgetItem("BNC 845 RF"))
            self.right_sidebar.addItem(QListWidgetItem("DSP Lock-in 7265"))
            self.right_sidebar.addItem(QListWidgetItem("Measure"))
            self.right_sidebar.currentRowChanged.connect(self.update_qd)
            self.right_sidebar.setCurrentRow(4)
            self.pages.setCurrentIndex(4)
            self.currentindex = 4

    def update_qd(self, current_row):
        if current_row == 0:  # PPMS
            self.right_sidebar.setCurrentRow(0)
            # Enter the corresponding function
            self.pages.setCurrentIndex(6)
            self.currentqdindex = 0
            # self.left_sidebar.setEnabled(True)

        elif current_row == 1:  # NV

            self.right_sidebar.setCurrentRow(1)
            self.pages.setCurrentIndex(7)
            self.currentqdindex = 1

        elif current_row == 2:  # DC AC Current

            self.right_sidebar.setCurrentRow(2)
            self.pages.setCurrentIndex(8)
            self.currentqdindex = 2

        elif current_row == 3:  # RF
            self.right_sidebar.setCurrentRow(3)
            self.pages.setCurrentIndex(9)
            self.currentqdindex = 3

        elif current_row == 4:  # Measure
            # self.right_sidebar.currentRowChanged.connect(self.update_PPMS)
            self.right_sidebar.setCurrentRow(4)
            self.pages.setCurrentIndex(1)
            self.currentqdindex = 4

        elif current_row == 5:  # Measure
            # self.right_sidebar.currentRowChanged.connect(self.update_PPMS)
            self.right_sidebar.setCurrentRow(5)
            self.pages.setCurrentIndex(10)
            self.currentqdindex = 5

    def update_SHG(self, current_row):
        if current_row == 0:  # General Processing
            self.right_sidebar.setCurrentRow(0)
            # Enter the corresponding function
            self.pages.setCurrentIndex(11)
            self.currentqdindex = 0
            # self.left_sidebar.setEnabled(True)

        elif current_row == 1:  # Temp Dep

            self.right_sidebar.setCurrentRow(1)
            self.pages.setCurrentIndex(12)
            self.currentqdindex = 1

        elif current_row == 2:  # Imaging

            self.right_sidebar.setCurrentRow(2)
            self.pages.setCurrentIndex(13)
            self.currentqdindex = 2

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
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
