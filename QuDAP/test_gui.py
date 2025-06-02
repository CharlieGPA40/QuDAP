from pathlib import Path

import initalization


def test_startup(qtbot):

	app = initalization.main(test_mode=True)
	qtbot.addWidget(app)