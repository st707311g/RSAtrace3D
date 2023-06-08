import json
import logging
import os
from pathlib import Path

import numpy as np
import polars as pl
from PySide6.QtCore import QEvent, Qt, QThread, Signal
from PySide6.QtGui import QColor, QKeyEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QSplitter
from skimage import io

import config
from DATA.RSA import RSA_Components
from DATA.RSA.components.file import File
from DATA.RSA.components.rinfo import ID_Object, RootNode
from data_modules.df_for_drawing import get_dilate_df
from mod import Extensions, Interpolation, RootTraits, RSATraits
from modules.volume import VolumeLoader

from .QtMenubar import QtMenubar
from .QtProjectionView import QtProjectionView
from .QtSliceView import QtSliceView
from .QtStatusBar import QtStatusBarW
from .QtToolbar import QtToolBar
from .QtTreeView import QtTreeView


class GUI_Components(object):
    def __init__(self, parent):
        super().__init__()
        self.sliceview = QtSliceView(parent=parent)
        self.statusbar = QtStatusBarW(parent=parent)
        self.treeview = QtTreeView(parent=parent)
        self.menubar = QtMenubar(parent=parent)
        self.toolbar = QtToolBar(parent=parent)
        self.projectionview = QtProjectionView(parent=parent)


class QtMain(QMainWindow):
    __control_locked = False
    __spacekey_pressed = False

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

        self.interpolation = Interpolation()
        self.root_traits = RootTraits()
        self.RSA_traits = RSATraits()
        self.extensions = Extensions(parent=self)
        self.df_dict_for_drawing: dict[str, pl.DataFrame] = {}
        self.__RSA_components = RSA_Components(parent=self)
        self.__GUI_components = GUI_Components(parent=self)
        self.setStatusBar(self.GUI_components().statusbar.widget)

        self.init_interface()
        self.setAcceptDrops(True)

    def init_interface(self):
        self.resize(1200, 800)
        self.setWindowTitle()

        # // splitter setting
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.sub_splitter = QSplitter(Qt.Vertical)
        self.sub_splitter.addWidget(self.treeview)
        self.sub_splitter.addWidget(self.projectionview)
        self.main_splitter.addWidget(self.sliceview)
        self.main_splitter.addWidget(self.sub_splitter)
        self.main_splitter.setSizes([1024, 1024])
        self.sub_splitter.setSizes([1024, 1024])
        self.setCentralWidget(self.main_splitter)

        self.menubar.build()
        self.setMenuBar(self.menubar)
        self.addToolBar(self.GUI_components().toolbar)
        self.menubar.update()

        self.show_default_msg_in_statusbar()
        self.load_config()

    def load_config(self):
        config_dict = config.load()
        resolution = float(config_dict.get("resolution", 0.3))
        interpolation_name = config_dict.get("interpolation", "Straigth")

        self.set_resolution(resolution=resolution)
        self.interpolation.set_selected_by(label=interpolation_name)

    def save_config(self):
        config_dict = {
            "resolution": float(
                self.GUI_components().toolbar.voxel_lineedit.text()
            ),
            "interpolation": self.interpolation.get_selected_label(),
        }
        config.save(**config_dict)

    def GUI_components(self):
        return self.__GUI_components

    def RSA_components(self):
        return self.__RSA_components

    @property
    def RSA_vector(self):
        return self.RSA_components().vector

    @property
    def treeview(self):
        return self.GUI_components().treeview

    @property
    def selected_ID_string(self):
        return self.treeview.get_selected_ID_string()

    @property
    def projectionview(self):
        return self.GUI_components().projectionview

    @property
    def sliceview(self):
        return self.GUI_components().sliceview

    @property
    def menubar(self):
        return self.GUI_components().menubar

    def is_control_locked(self):
        return self.__control_locked

    def set_control(self, locked):
        if self.__control_locked == locked:
            return

        self.__control_locked = locked
        self.logger.debug(f"Control locked: {self.__control_locked}")
        self.menubar.update()

        if locked:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()

    def is_spacekey_pressed(self):
        return self.__spacekey_pressed

    def set_spacekey(self, pressed: bool):
        self.__spacekey_pressed = pressed
        self.logger.debug(f"Space key pressed: {self.__spacekey_pressed}")
        for w in [
            self.sliceview,
            self.projectionview,
        ]:
            w.on_spacekey_pressed(pressed=self.__spacekey_pressed)

    def dragEnterEvent(self, ev):
        ev.accept()

    def dropEvent(self, ev) -> bool:
        ev.accept()

        flist = [u.toLocalFile() for u in ev.mimeData().urls()]

        if len(flist) != 1:
            self.logger.error("Only 1 volume path at once is acceptable.")
            return False

        vol_parent_path = Path(flist[0])
        if not vol_parent_path.is_dir():
            self.logger.error("Indicate directory path.")
            return False

        return self.load_from(vol_parent_path)

    def load_from(self, vol_parent_path: Path, rinfo_dict: dict = {}):
        self.set_control(locked=True)
        statusbar = self.GUI_components().statusbar

        vl = VolumeLoader(vol_parent_path)
        vol_paths: list[Path] = []
        if vl.is_valid_volume():
            vol_paths = [vol_parent_path]
        else:
            vol_paths: list[Path] = []
            for d in sorted(os.listdir(vol_parent_path)):
                d = Path(vol_parent_path, d)
                if d.is_dir():
                    vl = VolumeLoader(d)
                    if vl.is_valid_volume():
                        vol_paths.append(d)

        if len(vol_paths) == 0:
            self.logger.error("No volume directories.")
            return False

        self.volume_loader = QtVolumeLoader(
            volume_paths=vol_paths,
            progressbar_signal=statusbar.pyqtSignal_update_progressbar,
        )

        VolumeFile = File(volume_path=str(vol_parent_path))
        self.rinfo_dict = rinfo_dict
        self.close_volume()
        self.RSA_components().file = VolumeFile

        self.volume_loader.finished.connect(self.on_volume_loaded)
        self.volume_loader.start()
        self.menubar.history.add(str(vol_parent_path))
        self.menubar.history.update_menu()

    def on_volume_loaded(self):
        file_instance = self.RSA_components().file
        self.set_volume_name(file_instance.volume_name)

        np_vols, vol_infos, labels = self.volume_loader.data()
        self.set_resolution(vol_infos[0].get("mm_resolution", 0.3))
        del self.volume_loader

        self.logger.info(
            f"[Loading succeeded] {self.RSA_components().file.volume_path}"
        )

        self.RSA_components().set_volumes(
            np_vols=np_vols,
            labels=labels,
        )
        self.sliceview.set_volume(volume=np_vols[0])
        self.projectionview.set_volume(volume=np_vols[0])

        loaded = False
        if self.rinfo_dict:
            loaded = self.load_rinfo_from_dict(self.rinfo_dict)
        elif self.RSA_components().file.is_rinfo_file_available():
            if config.ALWAYS_YES:
                replay = True
            else:
                ret = QMessageBox.information(
                    None,
                    "Information",
                    "The rinfo file is available. Do you want to import this?",
                    QMessageBox.Yes,
                    QMessageBox.No,
                )
                replay = ret == QMessageBox.Yes
            if replay:
                loaded = self.load_rinfo(
                    fname=self.RSA_components().file.rinfo_file
                )
                self.set_volume_name(
                    volume_name=self.RSA_vector.annotations.volume_name()
                )
                self.set_resolution(
                    resolution=self.RSA_vector.annotations.resolution()
                )

        if loaded is False:
            self.set_volume_name(
                volume_name=self.RSA_components().file.volume_name
            )

            interpolation = self.RSA_vector.interpolation
            self.RSA_vector.annotations.set_interpolation(
                interpolation.get_selected_label()
            )
            self.RSA_vector.annotations.set_volume_shape(np_vols[0].shape)

        self.set_control(locked=False)

        self.show_default_msg_in_statusbar()
        self.setWindowTitle()
        self.menubar.update()

    def load_rinfo_from_dict(self, rinfo_dict: dict, file: str = ""):
        ret = self.RSA_vector.load_from_dict(rinfo_dict, file=file)
        if ret is False:
            return False

        for ID_string in self.RSA_vector.iter_all():
            if ID_string.is_base():
                self.treeview.add_base(ID_string=ID_string)
            elif ID_string.is_root():
                self.treeview.add_root(ID_string=ID_string)
            else:
                self.treeview.add_relay(ID_string=ID_string)

        self.set_volume_name(
            volume_name=self.RSA_vector.annotations.volume_name()
        )
        self.set_resolution(
            resolution=self.RSA_vector.annotations.resolution()
        )

        self.update_df_dict_for_drawing_all()
        self.on_selected_item_changed(
            selected_ID_string=self.selected_ID_string
        )

        return True

    def load_rinfo(self, fname: str):
        with open(fname, "r") as f:
            trace_dict = json.load(f)

        return self.load_rinfo_from_dict(trace_dict, file=fname)

    def keyPressEvent(self, ev: QKeyEvent):
        ev.accept()
        if self.is_control_locked():
            return

        if ev.key() == Qt.Key_Space and not ev.isAutoRepeat():
            self.set_spacekey(pressed=True)
            return

        if ev.key() == Qt.Key_Delete and not ev.isAutoRepeat():
            if self.selected_ID_string is None:
                return

            # // choose ID_string that should be deleted
            target_node = None
            if self.selected_ID_string.is_base():
                target_node = self.RSA_vector.base_node(
                    ID_string=self.selected_ID_string
                )
            elif self.selected_ID_string.is_root():
                target_node = self.RSA_vector.root_node(
                    ID_string=self.selected_ID_string
                )
            elif self.selected_ID_string.is_relay():
                target_node = self.RSA_vector.root_node(
                    ID_string=self.selected_ID_string
                )
                if target_node is not None:
                    if target_node.child_count() > 1:
                        target_node = self.RSA_vector.relay_node(
                            ID_string=self.selected_ID_string
                        )

            if target_node is not None:
                self.set_control(True)
                ID_string = target_node.ID_string()
                self.treeview.select(ID_string=ID_string)
                target_node.delete()
                self.treeview.delete(ID_string=ID_string)
                if ID_string.is_base():
                    target_ID_strings = [
                        ID_Object(k) for k in self.df_dict_for_drawing.keys()
                    ]
                    for target_ID_string in target_ID_strings:
                        if (
                            ID_Object(target_ID_string).baseID()
                            == ID_Object(ID_string).baseID()
                        ):
                            del self.df_dict_for_drawing[target_ID_string]
                elif ID_string.is_root():
                    del self.df_dict_for_drawing[ID_string]
                else:
                    self.update_df_dict_for_drawing(
                        target_ID_string=ID_string.to_root()
                    )

                self.on_selected_item_changed(
                    selected_ID_string=self.selected_ID_string
                )
                self.set_control(False)

        return

    def keyReleaseEvent(self, ev):
        ev.accept()
        if self.is_control_locked():
            return

        if (
            ev.key() == Qt.Key_Tab
            and not ev.isAutoRepeat()
            and ev.modifiers() & Qt.ControlModifier
        ):
            self.logger.debug("[key released] Ctrl+Tab")
            if not self.RSA_components().volume.is_empty():
                self.RSA_components().shift_current_volume()
                self.sliceview.update_volume(self.RSA_components().volume.data)
                self.projectionview.update_volume(
                    self.RSA_components().volume.data
                )

        if ev.key() == Qt.Key_Space and not ev.isAutoRepeat():
            self.logger.debug("[key release] Space")
            self.set_spacekey(pressed=False)

    # // event hook
    def event(self, ev):
        if ev.type() == QEvent.StatusTip:
            if ev.tip() != "":
                self.GUI_components().statusbar.set_main_message(ev.tip())
            else:
                self.show_default_msg_in_statusbar()
            return True
        elif ev.type() == QEvent.WindowDeactivate:
            if self.is_spacekey_pressed():
                self.set_spacekey(pressed=False)
            return super().event(ev)
        else:
            return super().event(ev)

    def closeEvent(self, *args, **kwargs):
        self.menubar.history.save("recent.json")
        self.save_config()

        self.extensions.destroy_instance()

        self.GUI_components().statusbar.thread.quit()
        self.GUI_components().statusbar.thread.wait()

        super().closeEvent(*args, **kwargs)

    def close_volume(self):
        if self.RSA_components().volume.is_empty():
            return

        self.df_dict_for_drawing.clear()
        self.sliceview.update_slice_layer()
        self.RSA_components().clear()
        self.sliceview.clear()
        self.treeview.clear()
        self.menubar.update()
        self.projectionview.clear()

        self.show_default_msg_in_statusbar()
        self.setWindowTitle()

    def show_default_msg_in_statusbar(self):
        if self.RSA_components().volume.is_empty():
            msg = "Open your volume file."
        else:
            msg = "Add or delete the base, root, and relay nodes anywhere."
        self.GUI_components().statusbar.set_main_message(msg)

    def set_volume_name(self, volume_name):
        self.GUI_components().toolbar.volumename_edit.setText(str(volume_name))
        self.RSA_vector.annotations.set_volume_name(name=volume_name)

    def set_resolution(self, resolution):
        self.GUI_components().toolbar.voxel_lineedit.setText(str(resolution))
        self.RSA_vector.annotations.set_resolution(resolution=resolution)

    def setWindowTitle(self):
        text = f"RSAtrace3D (version {config.version_string()})"
        if not self.RSA_components().volume.is_empty():
            volume_path = self.RSA_components().file.volume_path
            text = f"{text} - {volume_path}"
        super().setWindowTitle(text)

    def update_df_dict_for_drawing_all(self):
        self.df_dict_for_drawing.clear()
        for base_node in self.RSA_vector:
            for root_node in base_node:
                self.update_df_dict_for_drawing(
                    target_ID_string=root_node.ID_string()
                )

    def update_df_dict_for_drawing(self, target_ID_string: ID_Object):
        target_node = self.RSA_vector[target_ID_string]

        if isinstance(target_node, RootNode):
            polyline = np.array(target_node.completed_polyline())

            z_array = polyline[:, 0]
            y_array = polyline[:, 1]
            x_array = polyline[:, 2]
            size = 3
            color = QColor("#8800ff00").getRgb()
            df = pl.DataFrame(
                (
                    pl.Series("z", z_array, dtype=pl.Int64),
                    pl.Series("y", y_array, dtype=pl.Int64),
                    pl.Series("x", x_array, dtype=pl.Int64),
                    pl.Series("size", [size] * len(x_array), dtype=pl.Int64),
                )
            )

            df = get_dilate_df(df, self.RSA_components().volume.data)

            self.df_dict_for_drawing.update(
                {target_ID_string: {"df": df, "color": color}}
            )
            self.logger.debug(
                f"df_dict_for_drawing was updated: {target_ID_string}"
            )

    def on_selected_item_changed(self, selected_ID_string: ID_Object):
        self.logger.debug(f"selected item changed: {selected_ID_string}")

        modified_df_dict = {}
        for ID_string, vars in self.df_dict_for_drawing.items():
            df = vars["df"]
            ID_string = ID_Object(ID_string)
            if ID_string.baseID() != selected_ID_string.baseID():
                color = QColor(config.COLOR_SELECTED_ROOT).getRgb()[0:3] + (
                    40,
                )
            elif (
                not selected_ID_string.is_base()
                and ID_string == selected_ID_string.to_root()
            ):
                color = QColor(config.COLOR_SELECTED_ROOT).getRgb()[0:3] + (
                    150,
                )
            else:
                color = QColor(config.COLOR_ROOT).getRgb()[0:3] + (150,)

            modified_df_dict.update({ID_string: {"df": df, "color": color}})

        self.df_dict_for_drawing.clear()
        self.df_dict_for_drawing.update(modified_df_dict)

        self.sliceview.update_slice_layer()

        self.projectionview.set_view_layer(self.df_dict_for_drawing)
        self.sliceview.pos_marks.draw(ID_string=selected_ID_string)

        if selected_ID_string is not None:
            if selected_ID_string.is_base():
                projection_image = None
            else:
                selected_ID_string = selected_ID_string.to_root()
                np_volume = self.RSA_components().volume.data
                projection_image = np.zeros(
                    shape=(np_volume.shape[1], np_volume.shape[2]),
                    dtype=np.uint8,
                )
                vars = self.df_dict_for_drawing[selected_ID_string]
                df_for_drawing = vars["df"]
                y_array = df_for_drawing["y"].to_numpy()
                x_array = df_for_drawing["x"].to_numpy()

                if len(y_array) != 0:
                    projection_image[y_array, x_array] = 255

            # if selected_ID_string is not None:
            self.sliceview.isocurve.draw(projection_image=projection_image)


class QtVolumeLoader(QThread):
    def __init__(self, volume_paths: list[Path], progressbar_signal: Signal):
        super().__init__()
        self.volume_paths = volume_paths.copy()
        self.progressbar_signal = progressbar_signal

    @property
    def volume_number(self):
        return len(self.volume_paths)

    def run(self):
        self.__np_volume: list[np.ndarray] = []
        self.__volume_info: list[dict] = []
        self.__labels: list[str] = []
        for i, volume_path in enumerate(self.volume_paths):
            volume_path = Path(volume_path)
            vl = VolumeLoader(volume_path)
            img_paths = vl.image_files

            imgs = []
            for j, p in enumerate(img_paths):
                imgs.append(io.imread(p))
                self.progressbar_signal.emit(
                    i * len(img_paths) + j + 1,
                    len(img_paths) * self.volume_number,
                    f"[loading] {volume_path.name} ({j+1} / {len(img_paths)})",
                )

            self.__np_volume.append(np.asarray(imgs))
            self.__volume_info.append(vl.load_volume_info())
            self.__labels.append(str(volume_path.name))
        self.quit()

    def is_valid_volume(self):
        vl = VolumeLoader(self.volume_path)
        return vl.is_valid_volume()

    def data(self):
        return (self.__np_volume, self.__volume_info, self.__labels)
