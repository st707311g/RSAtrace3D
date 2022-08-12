from DATA import RSA_Components
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import QLabel, QLineEdit, QSizePolicy, QToolBar


class QtToolBar(QToolBar):
    def __init__(self, parent):
        super().__init__(*("Main",))
        self.__parent = parent
        self.setMovable(False)
        self.init_interface()

    def parent(self):
        return self.__parent

    def RSA_components(self) -> RSA_Components:
        return self.parent().RSA_components()

    def GUI_components(self):
        return self.parent().GUI_components()

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
            self.RSA_components().vector.annotations.set_volume_name(
                name=volume_name
            )
            self.volumename_edit.setModified(False)

        # // resolution
        if self.voxel_lineedit.isModified():
            resolution = float(self.voxel_lineedit.text())
            self.RSA_components().vector.annotations.set_resolution(
                resolution=resolution
            )
            self.GUI_components().treeview.update_all_text()
            self.voxel_lineedit.setModified(False)

        self.parent().GUI_components().sliceview.setFocus()


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
