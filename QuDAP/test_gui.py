from pathlib import Path

import initalization
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

def test_startup(qtbot):
	communicator = Communicator()
	window = MainWindow(communicator)
	qtbot.addWidget(window)
	window.show()  # Explicitly show the window
	assert window.isVisible()  # Check if it's visible
	assert window.windowTitle() == "QuDAP"