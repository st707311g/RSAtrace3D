import logging
import os

import imageio.v3 as imageio
import numpy as np
from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QFileDialog,
    QMenu,
    QMenuBar,
    QMessageBox,
)

import config
from config.history import History
from GUI.components import QtMain
from modules.volume import VolumeSaver


class QtAction(QAction):
    def __init__(self, *args, **kwargs):
        self.auto_enable_volume = kwargs.pop("auto_enable_volume", False)
        super().__init__(*args, **kwargs)


class QtMenubar(QMenuBar):
    def __init__(self, parent: QtMain):
        super().__init__(**{"parent": parent})
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__parent = parent
        self.history = History(max_count=10, menu_label="Recent")
        self.history.load(file_name="recent.json")

    @property
    def main_window(self) -> QtMain:
        return self.parent()

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
    def projectionview(self):
        return self.GUI_components.projectionview

    def build(self):
        self.menu_file = QMenu("&File")
        self.addMenu(self.menu_file)

        # // file menu
        self.act_open_volume = QtAction(
            text="Open volume",
            parent=self,
            shortcut="Ctrl+O",
            statusTip="Open volume",
            triggered=self.on_act_open_volume,
        )
        self.menu_file.addAction(self.act_open_volume)

        self.menu_history = self.history.build_menu(
            parent=self, triggered=self.on_menu_history
        )
        self.menu_file.addMenu(self.menu_history)

        self.act_close_volume = QtAction(
            text="Close volume",
            parent=self,
            shortcut="Ctrl+D",
            statusTip="Close volume",
            triggered=self.on_act_close_volume,
            auto_enable_volume=True,
        )
        self.menu_file.addAction(self.act_close_volume)
        self.menu_file.addSeparator()

        self.act_save_rinfo = QtAction(
            text="Save rinfo file",
            parent=self,
            shortcut="Ctrl+S",
            statusTip="Save rinfo file",
            triggered=self.on_act_save_rinfo,
            auto_enable_volume=True,
        )
        self.menu_file.addAction(self.act_save_rinfo)

        self.act_export_projections = QtAction(
            text="Export projection images",
            parent=self,
            shortcut="Ctrl+P",
            statusTip="Export projection images",
            triggered=self.on_act_export_projections,
            auto_enable_volume=True,
        )
        self.menu_file.addAction(self.act_export_projections)

        self.act_export_trace_images = QtAction(
            text="Export trace images",
            parent=self,
            shortcut="Ctrl+T",
            statusTip="Export trace images (Z-stack image)",
            triggered=self.on_act_export_trace_images,
            auto_enable_volume=True,
        )
        self.menu_file.addAction(self.act_export_trace_images)

        self.act_export_root_csv = QtAction(
            text="Export root traits (csv)",
            shortcut="Ctrl+E",
            statusTip="Export root traits (csv)",
            triggered=self.on_act_export_root_csv,
            auto_enable_volume=True,
        )
        self.menu_file.addAction(self.act_export_root_csv)

        self.menu_file.addSeparator()
        self.act_exit = QtAction(
            text="Exit",
            parent=self,
            shortcut="Ctrl+Q",
            statusTip="Exit application",
            triggered=self.main_window.close,
        )
        self.menu_file.addAction(self.act_exit)

        # // interpolation menu
        interpolation = self.RSA_vector.interpolation
        self.menu_interpolation = interpolation.build_menu(
            menu_label="&Interpolation", triggered=self.on_menu_interpolation
        )
        self.RSA_vector.annotations.set_interpolation(
            interpolation.get_selected_label()
        )
        self.addMenu(self.menu_interpolation)

        # // extension menu
        self.menu_extensions = self.main_window.extensions.build_menu(
            menu_label="&Extensions", triggered=self.on_menu_extensions
        )
        self.addMenu(self.menu_extensions)

        # // Setting
        self.menu_setting = QMenu("&Setting")
        self.addMenu(self.menu_setting)

        self.menu_color = QMenu("&Color")
        self.menu_setting.addMenu(self.menu_color)

        self.act_change_color_root = QtAction(
            text="Root",
            parent=self,
            statusTip="change the color for root segments.",
            triggered=self.on_act_color_root,
        )
        self.menu_color.addAction(self.act_change_color_root)

        self.act_change_color_selected_root = QtAction(
            text="Selected root",
            parent=self,
            statusTip="change the color for selected root segments.",
            triggered=self.on_act_color_selected_root,
        )
        self.menu_color.addAction(self.act_change_color_selected_root)

        self.menu_color.addSeparator()
        self.act_reset_color = QtAction(
            text="Reset colors",
            parent=self,
            statusTip="reset color setting.",
            triggered=self.on_act_reset_colors,
        )
        self.menu_color.addAction(self.act_reset_color)

        # // Help
        self.menu_help = QMenu("&Help")
        self.addMenu(self.menu_help)

        self.act_about = QtAction(
            text="About",
            parent=self,
            statusTip="About RSAtrace3D",
            triggered=self.on_act_about,
        )
        self.menu_help.addAction(self.act_about)

    def update(self):
        for m, item in self.__dict__.items():
            if m.lower().startswith(("act_", "menu_")):
                item.setEnabled(self.main_window.is_control_locked() is False)

        if self.main_window.is_control_locked():
            return

        for m, item in self.__dict__.items():
            if m.lower().startswith(("act_", "menu_")):
                if hasattr(item, "auto_enable_volume"):
                    if item.auto_enable_volume is True:
                        item.setEnabled(
                            self.RSA_components.volume.is_empty() is False
                        )

        self.menu_history.setEnabled(len(self.menu_history.actions()) != 0)

    def on_act_open_volume(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Volume directory", os.path.expanduser("~")
        )
        if directory == "":
            return False

        self.main_window.load_from(vol_parent_path=directory)

    def on_menu_history(self):
        obj = QObject.sender(self)
        name = obj.data()

        self.main_window.load_from(vol_parent_path=name)

    def on_act_close_volume(self):
        self.main_window.close_volume()

    def on_act_save_rinfo(self):
        rinfo_file_name = self.RSA_components.file.rinfo_file
        self.RSA_vector.save(rinfo_file_name)

    def on_act_export_root_csv(self):
        df = self.treeview.to_pandas_df()
        csv_fname = self.RSA_components.file.root_traits_file
        volume_name = self.RSA_vector.annotations.volume_name()
        resolution = self.RSA_vector.annotations.resolution()
        with open(csv_fname, "w", newline="") as f:
            f.write(
                "# This file is a summary of root traits measured by RSAtrace3D.\n"
            )
            f.write(
                f"# Volume name: {volume_name}, Resolution: {resolution}\n"
            )
            df.to_csv(f)
            self.logger.info(f"[Saving succeeded] {csv_fname}")

    def on_act_export_projections(self):
        for i in range(3):
            view = self.projectionview.sub_view_widgets[i].view
            projection_image = view.projection_image.image
            trace_image = view.trace_image.image
            alpha = trace_image[[..., 3]] / 255
            alpha = np.array(np.stack([alpha, alpha, alpha], axis=2))
            out_image = np.zeros(projection_image.shape + (3,))
            out_image = np.stack(
                [projection_image, projection_image, projection_image],
                axis=2,
            )

            out_image = np.array(
                out_image * (1 - alpha) + trace_image[..., 0:3] * alpha,
                dtype=np.uint8,
            ).transpose(1, 0, 2)
            volume_stem = self.RSA_components.file.volume_stem
            out_file = f"{volume_stem}_projection{i+1}.png"

            imageio.imwrite(out_file, out_image)
            self.logger.info(f"[Saving succeeded] {out_file}")

    def on_act_export_trace_images(self):
        np_volume = self.RSA_components.volume.data
        df_dict_for_drawing = self.main_window.df_dict_for_drawing
        df_list = [v["df"] for v in df_dict_for_drawing.values()]
        trace_object = np.zeros((np_volume.shape[0:3]), dtype=np.uint8)

        for df in df_list:
            z_array = df["z"].to_numpy()
            y_array = df["y"].to_numpy()
            x_array = df["x"].to_numpy()

            if len(z_array) != 0:
                trace_object[z_array, y_array, x_array] = 255

        self.main_window.set_control(locked=True)
        trace_directory = self.RSA_components.file.trace_directory

        if trace_directory.is_dir():
            self.logger.error(
                f"[Saving failed] {trace_directory} already exists."
            )
            return

        os.mkdir(trace_directory)

        progressbar_signal = (
            self.GUI_components.statusbar.pyqtSignal_update_progressbar
        )
        volume_saver = VolumeSaver(trace_object, {})
        for i, total in volume_saver.save_iterably(
            trace_directory, extension="png"
        ):
            progressbar_signal.emit(i + 1, total, "File saving")

        self.logger.info(f"[Saving succeeded] {trace_directory}")

        self.main_window.set_control(locked=False)
        self.main_window.show_default_msg_in_statusbar()

    def on_menu_interpolation(self):
        obj = QObject.sender(self)
        name = obj.data()
        self.RSA_vector.annotations.set_interpolation(interpolation=name)

    def on_menu_extensions(self):
        obj = QObject.sender(self)
        name = obj.data()

        self.main_window.extensions.activate_window(label=name)

    def on_act_color_root(self):
        color = QColorDialog.getColor(
            initial=QColor(config.COLOR_ROOT),
            options=QColorDialog.DontUseNativeDialog,
        )
        if color.isValid():
            config.COLOR_ROOT = color.name()
            self.main_window.on_selected_item_changed(
                selected_ID_string=self.treeview.get_selected_ID_string()
            )

    def on_act_color_selected_root(self):
        color = QColorDialog.getColor(
            initial=QColor(config.COLOR_SELECTED_ROOT),
            options=QColorDialog.DontUseNativeDialog,
        )
        if color.isValid():
            config.COLOR_SELECTED_ROOT = color.name()
            self.main_window.on_selected_item_changed(
                selected_ID_string=self.treeview.get_selected_ID_string()
            )

    def on_act_reset_colors(self):
        config.reset_root_color()
        self.main_window.on_selected_item_changed(
            selected_ID_string=self.treeview.get_selected_ID_string()
        )

    def on_act_about(self):
        app_name = config.application_name
        ver = config.version
        rev = config.revision
        msg = f"{app_name} version ({ver}.{rev})\n\n"
        msg += "Copyright\u00a9: "
        msg += (
            "the National Agriculture and Food Research Organization (2020)\n"
        )
        msg += "Author: Shota Teramoto"
        QMessageBox.information(None, config.application_name, msg)
