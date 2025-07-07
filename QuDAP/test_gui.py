import pytest
from PyQt6.QtWidgets import QApplication
from initalization import MainWindow, Communicator  # Adjust import path as needed

@pytest.fixture
def main_window(qtbot):
    communicator = Communicator()
    window = MainWindow(communicator)
    qtbot.addWidget(window)
    window.show()
    return window

def test_starts_on_dashboard(main_window):
    # Check that Dashboard page is the current widget
    current_index = main_window.pages.currentIndex()
    assert current_index == 0, f"Expected Dashboard page at index 0, got {current_index}"

def test_switch_to_fmr(main_window, qtbot):
    # Select 'Data Processing' in left sidebar (row 1)
    main_window.left_sidebar.setCurrentRow(1)
    qtbot.wait(100)

    # Select 'FMR' in right sidebar (row 0)
    main_window.right_sidebar.setCurrentRow(0)
    qtbot.wait(100)

    assert main_window.pages.currentIndex() == 1, "Failed to switch to FMR page"
