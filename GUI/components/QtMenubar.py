import logging
import os

import config
import imageio.v3 as imageio
import numpy as np
from config import History
from DATA import RSA_Components
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QAction, QFileDialog, QMenu, QMenuBar, QMessageBox
from st_modules.volume import Volume3D, VolumeSaver


class QtAction(QAction):
    def __init__(self, *args, **kwargs):
        self.auto_enable_volume = kwargs.pop("auto_enable_volume", False)
        super().__init__(*args, **kwargs)


class QtMenubar(QMenuBar):
    def __init__(self, parent):
        super().__init__(**{"parent": parent})
        self.logger = logging.getLogger(self.__class__.__name__)
        self.history = History(max_count=10, menu_label="Recent")
        self.history.load(file_name="recent.json")

    def RSA_components(self) -> RSA_Components:
        return self.parent().RSA_components()

    def GUI_components(self):
        return self.parent().GUI_components()

    def build(self):
        self.menu_file = QMenu("&File")
        self.addMenu(self.menu_file)

        # // file menu
        self.act_open_volume = QtAction(
            text="Open volume",
            parent=self.parent(),
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
            parent=self.parent(),
            shortcut="Ctrl+Q",
            statusTip="Exit application",
            triggered=self.parent().close,
        )
        self.menu_file.addAction(self.act_exit)

        # // interpolation menu
        interpolation = self.RSA_components().vector.interpolation
        self.menu_interpolation = interpolation.build_menu(
            menu_label="&Interpolation", triggered=self.on_menu_interpolation
        )
        self.RSA_components().vector.annotations.set_interpolation(
            interpolation.get_selected_label()
        )
        self.addMenu(self.menu_interpolation)

        # // extension menu
        self.menu_extensions = self.parent().extensions.build_menu(
            menu_label="&Extensions", triggered=self.on_menu_extensions
        )
        self.addMenu(self.menu_extensions)

        # // Help
        self.menu_help = QMenu("&Help")
        self.addMenu(self.menu_help)

        self.act_about = QtAction(
            text="About",
            parent=self.parent(),
            statusTip="About RSAtrace3D",
            triggered=self.on_act_about,
        )
        self.menu_help.addAction(self.act_about)

    def update(self):
        for m, item in self.__dict__.items():
            if m.lower().startswith(("act_", "menu_")):
                item.setEnabled(self.parent().is_control_locked() == False)

        if self.parent().is_control_locked():
            return

        for m, item in self.__dict__.items():
            if m.lower().startswith(("act_", "menu_")):
                if hasattr(item, "auto_enable_volume"):
                    if item.auto_enable_volume == True:
                        item.setEnabled(
                            self.RSA_components().volume.is_empty() == False
                        )

        self.menu_history.setEnabled(len(self.menu_history.actions()) != 0)

    def on_act_open_volume(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Volume directory", os.path.expanduser("~")
        )
        if directory == "":
            return False

        self.parent().load_from(directory=directory)

    def on_menu_history(self):
        obj = QObject.sender(self)
        name = obj.data()

        self.parent().load_from(directory=name)

    def on_act_close_volume(self):
        self.parent().close_volume()

    def on_act_save_rinfo(self):
        RSA_vector = self.RSA_components().vector
        rinfo_file_name = self.RSA_components().file.rinfo_file

        RSA_vector.save(rinfo_file_name)

    def on_act_export_root_csv(self):
        try:
            df = self.GUI_components().treeview.to_pandas_df()
            csv_fname = self.RSA_components().file.root_traits_file
            volume_name = (
                self.RSA_components().vector.annotations.volume_name()
            )
            resolution = self.RSA_components().vector.annotations.resolution()
            with open(csv_fname, "w", newline="") as f:
                f.write(
                    f"# This file is a summary of root traits measured by RSAtrace3D.\n"
                )
                f.write(
                    f"# Volume name: {volume_name}, Resolution: {resolution}\n"
                )
                df.to_csv(f)
                self.logger.info(f"[Saving succeeded] {csv_fname}")
        except:
            self.logger.error(f"[Saving failed]")

    def on_act_export_projections(self):
        try:
            projectionview = self.GUI_components().projectionview
            for i in range(3):
                view = projectionview.sub_view_widgets[i].view
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
                out_file = f"{self.RSA_components().file.directory}_projection{i+1}.png"

                imageio.imsave(out_file, out_image)
                self.logger.info(f"[Saving succeeded] {out_file}")
        except:
            self.logger.error(f"[Saving failed]")

    def on_act_export_trace_images(self):
        self.parent().set_control(locked=True)
        trace_directory = self.RSA_components().file.trace_directory
        try:
            trace_3d = self.RSA_components().trace.trace3D
            if trace_3d is None:
                return

            if os.path.isdir(trace_directory):
                self.logger.error(
                    f"[Saving failed] {trace_directory} already exists."
                )
                return

            os.mkdir(trace_directory)

            volume3d = Volume3D(
                np_volume=trace_3d.volume[..., 1],
                mm_resolution=self.RSA_components().vector.annotations.resolution(),
            )
            progressbar_signal = (
                self.GUI_components().statusbar.pyqtSignal_update_progressbar
            )
            volume_saver = VolumeSaver(volume3d=volume3d)
            for i, total in volume_saver.save_files_iterably(
                destination_directory=trace_directory, extension="png"
            ):
                progressbar_signal.emit(i, total, "File saving")

            self.logger.info(f"[Saving succeeded] {trace_directory}")
        except:
            self.logger.error(f"[Saving failed] {trace_directory}")
        self.parent().set_control(locked=False)
        self.parent().show_default_msg_in_statusbar()

    def on_menu_interpolation(self):
        obj = QObject.sender(self)
        name = obj.data()
        self.RSA_components().vector.annotations.set_interpolation(
            interpolation=name
        )

    def on_menu_extensions(self):
        obj = QObject.sender(self)
        name = obj.data()

        self.parent().extensions.activate_window(label=name)

    def on_act_about(self):
        msg = f"{config.application_name} version ({config.version}.{config.revision})\n\n"
        msg += f"Copyright\u00a9: the National Agriculture and Food Research Organization (2020)\n"
        msg += f"Author: Shota Teramoto"
        QMessageBox.information(None, config.application_name, msg)
