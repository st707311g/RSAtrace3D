from pathlib import Path

from PySide6.QtWidgets import QApplication

from .components import QtMain


def start(volume_path: Path = None):
    app = QApplication([])
    main = QtMain()
    main.show()
    if volume_path:
        main.load_from(volume_path=volume_path)
    app.exec_()
