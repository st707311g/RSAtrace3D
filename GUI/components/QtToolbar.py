from GUI.components import QtMain
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QLabel, QLineEdit, QSizePolicy, QToolBar


class QtToolBar(QToolBar):
    def __init__(self, parent: QtMain):
        super().__init__(*("Main",))
        self.__parent = parent
        self.setMovable(False)
        self.init_interface()

    @property
    def main_window(self):
        return self.__parent

    @property
    def RSA_components(self):
        return self.main_window.RSA_components()

    @property
    def RSA_vector(self):
        return self.RSA_components.vector

    @property
    def GUI_components(self):
        return self.main_window.GUI_components()

    @property
    def treeview(self):
        return self.GUI_components.treeview

    @property
    def sliceview(self):
        return self.GUI_components.sliceview

    def init_interface(self):
        self.volumename_edit = VolumeNameEdit("")
        self.addWidget(self.volumename_edit)

        self.addSeparator()

        self.voxel_lineedit = VoxelLineEdit("0.3")
        self.addWidget(self.voxel_lineedit)
        self.addWidget(QLabel(" mm / voxel"))

        self.volumename_edit.editingFinished.connect(self.on_lineedit_changed)
        self.voxel_lineedit.editingFinished.connect(self.on_lineedit_changed)

    def keyPressEvent(self, ev):
        ev.ignore()

    def keyReleaseEvent(self, ev):
        ev.ignore()

    def on_lineedit_changed(self):
        # // volume name lineedit
        if self.volumename_edit.isModified():
            volume_name = self.volumename_edit.text()
            self.RSA_vector.annotations.set_volume_name(name=volume_name)
            self.volumename_edit.setModified(False)

        # // resolution
        if self.voxel_lineedit.isModified():
            resolution = float(self.voxel_lineedit.text())
            self.RSA_vector.annotations.set_resolution(resolution=resolution)
            self.treeview.update_all_text()
            self.voxel_lineedit.setModified(False)

        self.sliceview.setFocus()


class VolumeNameEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setToolTip("Volume name")
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

        self.default_msg = "Volume name"
        self.setText(self.default_msg)

    def focusInEvent(self, ev):
        super().focusInEvent(ev)
        if self.text() == self.default_msg:
            self.setText("")

    def focusOutEvent(self, ev):
        super().focusOutEvent(ev)
        if self.text() == "":
            self.setText(self.default_msg)

    def setText(self, *args, **kwargs):
        super().setText(*args, **kwargs)
        if self.text() == self.default_msg:
            self.setStyleSheet("color: rgb(200, 200, 200);")
        else:
            self.setStyleSheet("color: rgb(0, 0, 0);")


class VoxelLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setToolTip("Voxel resolution (double)")
        self.setValidator(QDoubleValidator())
        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
