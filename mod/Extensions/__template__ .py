from PySide6.QtWidgets import QMainWindow

from .__backbone__ import ExtensionBackbone


# // an template for Extensions
# // Create a class that inherits from QMainWindow and ExtensionBackbone.
# // Implement the window application
class Template(QMainWindow, ExtensionBackbone):
    label = "Template"  # // label name here
    status_tip = "test message"  # // shown as a status tip
    index = -1  # // determines the order in which the labels are displayed.
    version = 1  # // the version of RSAtrace3D

    def __init__(self, parent):
        super().__init__(parent=parent)
