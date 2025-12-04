from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QListWidgetItem, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QAbstractItemView, QFrame, QPushButton, QMessageBox)
from PyQt6.QtGui import QIcon, QFont, QPixmap
from PyQt6.QtCore import QObject, Qt, pyqtSignal, pyqtSlot, QTimer
import sys
import traceback

from numpy.f2py.crackfortran import expectbegin

try:
    import QuDAP.GUI.FMR.FMR as fmr
    import QuDAP.GUI.Setting.Setting as Setting
    import QuDAP.GUI.Setting.AboutSoftware as AboutSoftware
    import QuDAP.GUI.Setting.Contact as Contact
    import QuDAP.GUI.Experiment.PPMS as ppms
    import QuDAP.GUI.Experiment.QD as qd
    import QuDAP.GUI.VSM.VSM as vsm
    import QuDAP.GUI.ETO.ETO as eto
    import QuDAP.GUI.SHG.SHG as shg
    import QuDAP.GUI.SHG.SHG_General as shg_general
    import QuDAP.GUI.Experiment.DSP7265 as dsp
    import QuDAP.GUI.Experiment.Keithley2182nv as nv
    import QuDAP.GUI.Experiment.Keithley6221 as cs
    import QuDAP.GUI.Experiment.BNC845RF as rf
    import QuDAP.GUI.Experiment.sr830 as sr
    import QuDAP.GUI.Experiment.measurement as m
    import QuDAP.GUI.Dashboard.Dashboard as Dashboard
    import QuDAP.GUI.Plot.plotting as pt
    import QuDAP.GUI.Experiment.ReadInstrument as reading_instrument
    import QuDAP.GUI.Experiment.integrated_experiment as integrated_measurement
    
except ImportError as e:
    import GUI.FMR.FMR as fmr
    import GUI.Setting.Setting as Setting
    import GUI.Setting.AboutSoftware as AboutSoftware
    import GUI.Setting.Contact as Contact
    import GUI.Experiment.PPMS as ppms
    import GUI.Experiment.QD as qd
    import GUI.VSM.VSM as vsm
    import GUI.ETO.ETO as eto
    import GUI.SHG.SHG as shg
    import GUI.SHG.SHG_General as shg_general
    import GUI.Experiment.DSP7265 as dsp
    import GUI.Experiment.Keithley2182nv as nv
    import GUI.Experiment.Keithley6221 as cs
    import GUI.Experiment.BNC845RF as rf
    import GUI.Experiment.sr830 as sr
    import GUI.Experiment.measurement as m
    import GUI.Dashboard.Dashboard as Dashboard
    import GUI.Plot.plotting as pt
    import GUI.Experiment.ReadInstrument as reading_instrument
    import GUI.Experiment.integrated_experiment as integrated_measurement

class Communicator(QObject):
    change_page = pyqtSignal(int, int, int)


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
        self.LIST_WIDGET_FONT = 13
        self.MENU_IS_HIDE = False  # Flag for hide menu; the ture flag means the hide button is selected, vice versa
        self.MENU_IS_INIT = True  # Flag for first initialization of the program; this essential to avoid the auto select of hide function
        self.CURRENT_INDEX_PARENT = 0  # Index for menu bar; this tells which row of the menu bar has been selected (FMR, VSM, etc.)
        self.CURRENT_INDEX_HELP_SETTING = 0  # Index for help menu and setting menu selection
        self.PARENT_SIDE_BAR_SELECTION = 0  # Index for which side bar on the left side has been selected; 1 means menu sidebar; 2 means tool menu bar
        self.CURRENT_INDEX_CHILD = 0
        self.communicator = communicator
        try:
            self.initUI()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f"{e}")

    def initUI(self):
        self.parent_side_bar = QListWidget()
        self.parent_side_bar.setFont(QFont("Arial", self.LIST_WIDGET_FONT))
        with open("GUI/QSS/QListWidget.qss", "r") as file:
            self.QListWidget_stylesheet = file.read()

        with open("GUI/QSS/QListWidget_middle.qss", "r") as file:
            self.QListWidget_middle_stylesheet = file.read()

        self.parent_side_bar.setStyleSheet(self.QListWidget_stylesheet)
        dashboard_list_widget = QListWidgetItem(QIcon("GUI/Icon/Dashboard.svg"), "Dashboard")
        data_processing_list_widget = QListWidgetItem(QIcon("GUI/Icon/codesandbox.svg"), "Data Processing")
        experiment_list_widget = QListWidgetItem(QIcon("GUI/Icon/cpu.svg"), 'Experiment')

        with open("GUI/QSS/QComboWidget.qss", "r") as file:
            self.SideWidget_stylesheet = file.read()

        self.parent_side_bar.addItem(dashboard_list_widget)
        self.parent_side_bar.addItem(data_processing_list_widget)
        self.parent_side_bar.addItem(experiment_list_widget)
        # ==================================================================
        # This part potentially need to replace the current experiment tab
        experiment_test_list_widget = QListWidgetItem(QIcon("GUI/Icon/cpu.svg"), 'Test')
        self.parent_side_bar.addItem(experiment_test_list_widget)
        # ==================================================================
        self.parent_side_bar.currentRowChanged.connect(self.update_menu_bar)

        # Left Sidebar
        self.help_setting_side_bar = QListWidget()
        self.help_setting_side_bar.setFont(QFont("Arial", self.LIST_WIDGET_FONT))
        self.help_setting_side_bar.setStyleSheet(self.QListWidget_stylesheet)
        help_Item = QListWidgetItem(QIcon("GUI/Icon/help-circle.svg"), "Help")
        settings_item = QListWidgetItem(QIcon("GUI/Icon/settings.svg"), "Settings")

        self.help_setting_side_bar.addItem(help_Item)
        self.help_setting_side_bar.addItem(settings_item)
        # Disable item selection in the QListWidget
        self.help_setting_side_bar.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.help_setting_side_bar.currentRowChanged.connect(self.update_tool_bar)
        self.help_setting_side_bar.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.help_setting_side_bar.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.help_setting_side_bar.setMinimumHeight(30)

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

        parent_side_bar_layout = QVBoxLayout()
        parent_side_bar_layout.addLayout(self.logolayout)
        parent_side_bar_layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignCenter)
        # parent_side_bar_layout.addStretch(3)
        parent_side_bar_layout.addWidget(self.parent_side_bar, 12)
        parent_side_bar_layout.addStretch(9)
        parent_side_bar_layout.addWidget(self.help_setting_side_bar, 3)
        parent_side_bar_layout.setSpacing(0)
        parent_side_bar_layout.setContentsMargins(2, 0, 0, 0)
        # # Create a main widget to host both the left sidebar and the checkbox
        self.parent_side_bar_container = QWidget()
        self.parent_side_bar_container.setLayout(parent_side_bar_layout)

        # Right Sidebar
        self.child_sidebar = QListWidget()
        self.child_sidebar.setFont(QFont("Arial", self.LIST_WIDGET_FONT))
        self.child_sidebar.setStyleSheet(self.QListWidget_middle_stylesheet)
        self.hide_button_container = QWidget()
        self.hide_button_container.setStyleSheet(
            """ 
            QWidget{background-color: #ECECEB  ; border-radius: 15px;}

            """)
        self.hide_button_layout = QVBoxLayout()
        self.hide_button_container.setFixedSize(30,910)
        self.hide_button = QPushButton(QIcon("GUI/Icon/arrow-left.svg"),'')
        self.hide_button.clicked.connect(self.hide_show_child_sidebar)
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
        self.pages.addWidget(Setting.NotificationSettings())  # 6
        self.pages.addWidget(ppms.PPMS())  # 7
        self.pages.addWidget(nv.NV())  # 8
        self.pages.addWidget(cs.CurrentSource6221())  # 9
        self.pages.addWidget(rf.BNC845RF())  # 10
        self.pages.addWidget(m.Measurement())  # 11
        self.pages.addWidget(shg_general.General())  # 12
        self.pages.addWidget(pt.plotting())  # 13
        self.pages.addWidget(dsp.Lockin())  # 14
        self.pages.addWidget(sr.sr830Lockin())  # 15
        self.pages.addWidget(reading_instrument.InstrumentDetector())  # 16
        self.pages.addWidget(AboutSoftware.AboutQuDAP())  # 17
        self.pages.addWidget(Contact.ContactQuDAP()) # 18
        try:
            self.pages.addWidget(integrated_measurement.INTEGRATED_EXPERIMENT()) # 19
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
        # self.toggle_dark_mode()
        # Main Layout
        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(self.parent_side_bar_container, 1)  # Left sidebar stretch factor 1
        self.main_layout.addWidget(self.hide_button_container, 1)
        self.main_layout.addWidget(self.child_sidebar, 2)  # Right sidebar stretch factor 1

        self.main_layout.addWidget(self.pages, 13)  # Central content area stretch factor 4
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.container = QWidget()
        self.container.setLayout(self.main_layout)
        self.setCentralWidget(self.container)

        # Set initial window size
        self.setMinimumSize(1620,800)

    @pyqtSlot(int, int, int)
    def set_page(self, page, parent_side_bar, child_sidebar):
        self.pages.setCurrentIndex(page)
        self.parent_side_bar.setCurrentRow(parent_side_bar)
        self.child_sidebar.setCurrentRow(child_sidebar)

    def hide_show_child_sidebar(self):
        self.show = self.child_sidebar.isVisible()
        if not self.show:
            try:
                if self.CURRENT_INDEX_PARENT == 1 or self.CURRENT_INDEX_PARENT == 2 or self.PARENT_SIDE_BAR_SELECTION == 2:
                    self.child_sidebar.show()
                    self.hide_button.setIcon(QIcon("GUI/Icon/arrow-left.svg"))
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))
        else:
            if self.CURRENT_INDEX_PARENT == 1 or self.CURRENT_INDEX_PARENT == 2 or self.PARENT_SIDE_BAR_SELECTION == 2:
                # self.child_sidebar.show()
                self.hide_button.setIcon(QIcon("GUI/Icon/arrow-right.svg"))
                self.child_sidebar.hide()

    def update_menu_bar(self, current_row):
        self.PARENT_SIDE_BAR_SELECTION = 1
        self.help_setting_side_bar.setCurrentRow(-1)  # Force clearing selection
        self.child_sidebar.clear()

        if current_row == 0 or current_row == 3:  # dashboard page
            self.child_sidebar.hide()
            self.hide_button.setEnabled(False)
            self.pages.setCurrentIndex(0)
            self.CURRENT_INDEX_PARENT = 0
        else:
            self.child_sidebar.show()

        if current_row == 1:  # data processing page
            self.hide_button.setEnabled(True)
            self.hide_button.setIcon(QIcon("GUI/Icon/arrow-left.svg"))
            fmr = QListWidgetItem(QIcon("GUI/Icon/FMR.svg"), "FMR")
            vsm = QListWidgetItem(QIcon("GUI/Icon/VSM.svg"), "VSM")
            eto = QListWidgetItem(QIcon("GUI/Icon/ETO.svg"), "ETO")
            shg = QListWidgetItem(QIcon("GUI/Icon/SHG.svg"), "SHG")
            data_visualization = QListWidgetItem(QIcon("GUI/Icon/bar-chart-2.svg"), "Plotting")
            self.child_sidebar.addItem(QListWidgetItem(fmr))
            self.child_sidebar.addItem(QListWidgetItem(vsm))
            self.child_sidebar.addItem(QListWidgetItem(eto))
            self.child_sidebar.addItem(QListWidgetItem(shg))
            self.child_sidebar.addItem(QListWidgetItem(data_visualization))
            self.child_sidebar.currentRowChanged.connect(self.update_data_processing)
            self.pages.setCurrentIndex(0)
            self.CURRENT_INDEX_PARENT = 1
            # self.parent_side_bar.setEnabled(True)

        elif current_row == 2:  # experiment page
            self.hide_button.setEnabled(True)
            self.hide_button.setIcon(QIcon("GUI/Icon/arrow-left.svg"))
            self.child_sidebar.addItem(QListWidgetItem("PPMS"))
            self.child_sidebar.addItem(QListWidgetItem("Keithley 2182 NV"))
            self.child_sidebar.addItem(QListWidgetItem("Keithley 6221"))
            self.child_sidebar.addItem(QListWidgetItem("BNC 845 RF"))
            self.child_sidebar.addItem(QListWidgetItem("DSP Lock-in 7265"))
            self.child_sidebar.addItem(QListWidgetItem("sr830 Lock-in"))
            self.child_sidebar.addItem(QListWidgetItem("Connection"))
            self.child_sidebar.addItem(QListWidgetItem("Measure"))
            self.child_sidebar.addItem(QListWidgetItem("Quick Test"))
            self.child_sidebar.currentRowChanged.connect(self.update_exp_processing)
            self.pages.setCurrentIndex(0)
            self.CURRENT_INDEX_PARENT = 2

        elif current_row == 3:
            self.pages.setCurrentIndex(19)
            self.CURRENT_INDEX_PARENT = 3

        # elif current_row == 3:  # ETO
        #     self.child_sidebar.addItem(QListWidgetItem("Edit Profile"))
        #     self.child_sidebar.addItem(QListWidgetItem("Notifications"))
        #     self.child_sidebar.addItem(QListWidgetItem("Logout"))
        #     self.child_sidebar.setCurrentRow(0)
        #     self.pages.setCurrentIndex(3)
        #     self.CURRENT_INDEX_PARENT = 3
        #
        # elif current_row == 4:  # SHG
        #     self.child_sidebar.addItem(QListWidgetItem("General Processing"))
        #     self.child_sidebar.addItem(QListWidgetItem("Temperature Dependence"))
        #     self.child_sidebar.addItem(QListWidgetItem("Imaging Mode"))
        #     self.child_sidebar.currentRowChanged.connect(self.update_SHG)
        #     self.child_sidebar.setCurrentRow(0)
        #     self.pages.setCurrentIndex(6)
        #     self.CURRENT_INDEX_PARENT = 4

    def update_data_processing(self, current_row):
        if current_row == 0:  # FMR
            self.child_sidebar.setCurrentRow(0)
            self.pages.setCurrentIndex(1)
            self.CURRENT_INDEX_CHILD = 0

        elif current_row == 1:  # VSM
            self.child_sidebar.setCurrentRow(1)
            self.pages.setCurrentIndex(2)
            self.CURRENT_INDEX_CHILD = 1

        elif current_row == 2:  # ETO
            self.child_sidebar.setCurrentRow(2)
            self.pages.setCurrentIndex(3)
            self.CURRENT_INDEX_CHILD = 2

        elif current_row == 3:  # SHG
            self.child_sidebar.setCurrentRow(3)
            self.pages.setCurrentIndex(4)
            self.CURRENT_INDEX_CHILD = 3

        elif current_row == 4:  # Plotting
            self.child_sidebar.setCurrentRow(4)
            self.pages.setCurrentIndex(13)
            self.CURRENT_INDEX_CHILD = 4

    def update_exp_processing(self, current_row):
        if current_row == 0:  # PPMS
            self.child_sidebar.setCurrentRow(0)
            self.pages.setCurrentIndex(7)
            self.CURRENT_INDEX_CHILD = 0

        elif current_row == 1:  # 2182
            self.child_sidebar.setCurrentRow(1)
            self.pages.setCurrentIndex(8)
            self.CURRENT_INDEX_CHILD = 1

        elif current_row == 2:  # 6221
            self.child_sidebar.setCurrentRow(2)
            self.pages.setCurrentIndex(9)
            self.CURRENT_INDEX_CHILD = 2

        elif current_row == 3:  # 845
            self.child_sidebar.setCurrentRow(3)
            self.pages.setCurrentIndex(10)
            self.CURRENT_INDEX_CHILD = 3

        elif current_row == 4:  # 7265
            self.child_sidebar.setCurrentRow(4)
            self.pages.setCurrentIndex(14)
            self.CURRENT_INDEX_CHILD = 4

        elif current_row == 5:  # sr830
            self.child_sidebar.setCurrentRow(5)
            self.pages.setCurrentIndex(15)
            self.CURRENT_INDEX_CHILD = 5

        elif current_row == 6:  # InstrumentDetector
            self.child_sidebar.setCurrentRow(6)
            self.pages.setCurrentIndex(16)
            self.CURRENT_INDEX_CHILD = 6

        elif current_row == 7:  # Measure
            self.child_sidebar.setCurrentRow(7)
            self.pages.setCurrentIndex(11)
            self.CURRENT_INDEX_CHILD = 7

        elif current_row == 8:  # Quick Test
            self.child_sidebar.setCurrentRow(8)
            self.pages.setCurrentIndex(11)
            self.CURRENT_INDEX_CHILD = 8

    def update_tool_bar(self, current_row):
        self.child_sidebar.show()
        self.hide_button.setEnabled(True)
        self.hide_button.setIcon(QIcon("GUI/Icon/arrow-left.svg"))
        self.PARENT_SIDE_BAR_SELECTION = 2
        self.child_sidebar.clear()
        self.parent_side_bar.setCurrentRow(-1)  # Force clearing selection

        if current_row == 0:  # Home
            self.child_sidebar.addItem(QListWidgetItem("About Software"))
            self.child_sidebar.addItem(QListWidgetItem("Contact"))
            self.help_setting_side_bar.setCurrentRow(0)
            self.child_sidebar.currentRowChanged.connect(self.update_about)
            self.pages.setCurrentIndex(0)
            self.CURRENT_INDEX_HELP_SETTING = 1

        elif current_row == 1:  # Settings
            self.child_sidebar.addItem(QListWidgetItem("Notification"))
            self.help_setting_side_bar.setCurrentRow(1)
            self.child_sidebar.currentRowChanged.connect(self.update_setting)
            self.pages.setCurrentIndex(0)
            self.CURRENT_INDEX_HELP_SETTING = 2

    def update_setting(self, current_row):
        if current_row == 0:  # Setting
            self.child_sidebar.setCurrentRow(0)
            self.pages.setCurrentIndex(6)
            self.CURRENT_INDEX_CHILD = 0


    def update_about(self, current_row):
        if current_row == 0:  # About this software
            self.child_sidebar.setCurrentRow(0)
            self.pages.setCurrentIndex(17)
            self.CURRENT_INDEX_CHILD = 0
        elif current_row == 1:  # Contact
            self.child_sidebar.setCurrentRow(1)
            self.pages.setCurrentIndex(18)
            self.CURRENT_INDEX_CHILD = 1

def main(test_mode=False):
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    communicator = Communicator()
    app.setStyleSheet("QWidget { background-color: #ECECEB; }")
    window = MainWindow(communicator)
    window.show()

    app.communicator = communicator

    if test_mode:
       QTimer.singleShot(100, app.quit)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
