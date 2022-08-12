from PyQt5.QtWidgets import QApplication

from .components import QtMain


def start():
    app = QApplication([])
    main = QtMain()
    main.show()
    app.exec_()
