import logging
from typing import List

import pandas as pd
from DATA import RinfoFiles, RSA_Vector
from GUI import QtMain
from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QAction, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QProgressBar,
    QSizePolicy,
    QStatusBar,
    QTableView,
)

from .__backbone__ import ExtensionBackbone


class RSA_summary_window(QMainWindow, ExtensionBackbone):
    built_in = True
    label = "RSA summary"
    status_tip = "Pop a window for summarizing rinfo files up."
    index = -1
    version = 1

    def __init__(self, parent: QtMain):
        super().__init__(parent=parent)
        self.__logger = logging.getLogger(self.__class__.__name__)
        self.setWindowTitle("Summary window")
        self.resize(1200, 800)
        self.__parent = parent
        self.__control_locked = False
        self.tableview = SummaryTableview(parent=self)
        self.setCentralWidget(self.tableview)
        self.setAcceptDrops(True)

        self.statusbar = QtStatusBarW(parent=self)
        self.setStatusBar(self.statusbar.widget)

        self.menubar = QtMenubar(parent=self)
        self.setMenuBar(self.menubar)
        self.menubar.update()

        self.show_default_msg_in_statusbar()

    def destroy_instance(self):
        self.statusbar.thread.quit()
        self.statusbar.thread.wait()

    def parent(self):
        return self.__parent

    def logger(self):
        return self.__logger

    def is_control_locked(self):
        return self.__control_locked

    def set_control(self, locked):
        self.__control_locked = locked
        self.menubar.update()

        if self.is_control_locked():
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.statusbar.set_main_message("")
        else:
            QApplication.restoreOverrideCursor()
            self.show_default_msg_in_statusbar()

    def dragEnterEvent(self, ev):
        ev.accept()

    def dropEvent(self, ev):
        ev.accept()

        files = [u.toLocalFile() for u in ev.mimeData().urls()]
        self.add_from_files(files=files)

    def RSA_traits(self):
        return self.parent().RSA_traits

    def closeEvent(self, *args, **kwargs):
        super().closeEvent(*args, **kwargs)

    def generate_RSA_Vector(self, file_name: str):
        RSA_vector = RSA_Vector()
        RSA_vector.load_from_file(fname=file_name)

        return RSA_vector

    def create_row(self, RSA_vector: RSA_Vector):
        row = []
        for class_ in self.RSA_traits().class_container:
            ret = class_(RSA_vector).QStandardItem()
            row.append(ret)

        return row

    def add_item(self, RSA_vector: RSA_Vector):
        row = self.create_row(RSA_vector=RSA_vector)
        self.tableview.model.appendRow(row)

    def show_default_msg_in_statusbar(self):
        msg = "Add rinfo files."
        self.statusbar.set_main_message(msg)

    def add_from_files(self, files: List[str]):
        rinfo_files = RinfoFiles(files=files).list_files()

        if len(rinfo_files) == 0:
            self.logger().error("There is no .rinfo files.")
            return

        self.set_control(locked=True)
        self.rinfo_loader = RinfoLoader(
            parent=self,
            files=rinfo_files,
            progressbar_signal=self.statusbar.pyqtSignal_update_progressbar,
        )
        self.rinfo_loader.finished.connect(self.on_rinfo_list_loaded)
        self.rinfo_loader.start()

    def on_rinfo_list_loaded(self):
        RSA_vector_list = self.rinfo_loader.RSA_vector_list
        del self.rinfo_loader
        for RSA_vector in RSA_vector_list:
            self.add_item(RSA_vector=RSA_vector)

        if len(RSA_vector_list):
            self.tableview.selectRow(self.tableview.model.rowCount() - 1)
            self.tableview.repaint()
            self.tableview.setFocus()

        self.set_control(locked=False)


class TreeViewHeader(QHeaderView):
    def __init__(self):
        super().__init__(*(Qt.Horizontal,))

        self.setSectionsMovable(True)
        self.setDefaultAlignment(Qt.AlignLeft)


class TreeModel(QStandardItemModel):
    def __init__(self):
        super().__init__()


class SummaryTableview(QTableView):
    def __init__(self, parent):
        super().__init__(**{"parent": parent})
        self.__parent = parent
        self.model = TreeModel()
        self.tv_header = TreeViewHeader()
        self.setHorizontalHeader(self.tv_header)
        self.model.setHorizontalHeaderLabels(
            self.RSA_traits().class_container.labels()
        )

        for ci, cls_ in enumerate(self.RSA_traits().class_container):
            item = self.model.horizontalHeaderItem(ci)
            try:
                item.setToolTip(cls_.tool_tip)
            except:  # NOQA
                pass

        self.setModel(self.model)

    def parent(self):
        return self.__parent

    def RSA_traits(self):
        return self.__parent.RSA_traits()

    def selectionChanged(self, selected, deselected):
        if not self.parent().is_control_locked():
            pass

        try:
            self.parent().menubar.update()
        except:  # NOQA
            pass
        return super().selectionChanged(selected, deselected)

    def to_pandas_df(self):
        labels = []
        sublabels = []
        column_data = []

        exportable_list = self.RSA_traits().class_container.expotable_list()
        for ci in range(self.model.columnCount()):
            if exportable_list[ci] is False:
                continue

            label = self.model.horizontalHeaderItem(ci).text()
            cls_ = self.RSA_traits().get(label=label)

            sublabels = cls_.sublabels
            n_sublabel = len(sublabels)

            if n_sublabel == 0:
                labels.append(label)
                data = []
                for ri in range(self.model.rowCount()):
                    item = self.model.item(ri, ci)
                    data.append(item.text())
                column_data.append(data)
            else:
                for i in range(n_sublabel):
                    labels.append(f"{label}_{sublabels[i]}")
                    data = []
                    for ri in range(self.model.rowCount()):
                        item = self.model.item(ri, ci)
                        data.append(item.data().value[i])
                    column_data.append(data)

        df = pd.DataFrame(column_data, index=labels)
        df = df.transpose()

        return df


class QtStatusBarW(QObject):
    pyqtSignal_update_progressbar = Signal(int, int, str)

    def __init__(self, parent):
        super().__init__()
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.start()

        self.widget = QtStatusBar(parent=parent)
        self.pyqtSignal_update_progressbar.connect(self.widget.update_progress)

    def set_main_message(self, msg):
        self.widget.set_main_message(msg=msg)


class QtStatusBar(QStatusBar):
    def __init__(self, parent):
        super().__init__(**{"parent": parent})

        self.progress = QProgressBar()
        self.status_msg = QLabel("")

        self.addWidget(self.progress)
        self.addWidget(self.status_msg, 2048)

        self.progress.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        )
        self.progress.setValue(0)

    def update_progress(self, i, maximum, msg):
        self.progress.setMaximum(maximum)
        self.progress.setValue(i + 1)

        self.set_main_message(f"{msg}: {i+1} / {maximum}")

    def set_main_message(self, msg):
        if self.parent().is_control_locked():
            msg = "BUSY: " + msg
        else:
            msg = "READY: " + msg

        self.status_msg.setText(msg)


class QtMenubar(QMenuBar):
    def __init__(self, parent):
        super().__init__(**{"parent": parent})
        self.__parent = parent
        self.build()

    def parent(self) -> RSA_summary_window:
        return self.__parent

    def logger(self):
        return self.parent().logger()

    def tableview(self):
        return self.parent().tableview

    def build(self):
        self.menu_file = QMenu("&File")
        self.addMenu(self.menu_file)

        # // file menu
        self.act_import_rinfo = QAction(
            text="Import rinfo file(s)",
            parent=self.parent(),
            shortcut="Ctrl+O",
            triggered=self.on_act_import_rinfo_file,
        )
        self.menu_file.addAction(self.act_import_rinfo)

        self.act_import_rinfo_from_directory = QAction(
            text="Import rinfo file(s) from a directory",
            parent=self.parent(),
            shortcut="Ctrl+Shift+O",
            triggered=self.on_act_import_rinfo_from_directory,
        )
        self.menu_file.addAction(self.act_import_rinfo_from_directory)

        self.act_export_root_csv = QAction(
            text="Export root traits (csv)",
            shortcut="Ctrl+E",
            triggered=self.on_act_export_root_csv,
        )
        self.menu_file.addAction(self.act_export_root_csv)

        self.menu_file.addSeparator()
        self.act_exit = QAction(
            text="Exit",
            parent=self.parent(),
            shortcut="Ctrl+Q",
            triggered=self.parent().close,
        )
        self.menu_file.addAction(self.act_exit)

        self.menu_edit = QMenu("&Edit")
        self.addMenu(self.menu_edit)

        # // Edit menu
        self.act_edit_remove_row = QAction(
            text="Remove selected row(s)",
            parent=self.parent(),
            shortcut="Delete",
            triggered=self.on_act_edit_remove_selected,
        )
        self.menu_edit.addAction(self.act_edit_remove_row)

        self.act_edit_clear = QAction(
            text="Remove all rows",
            parent=self.parent(),
            shortcut="Ctrl+Delete",
            triggered=self.on_act_edit_clear,
        )
        self.menu_edit.addAction(self.act_edit_clear)

    def update(self):
        for m, item in self.__dict__.items():
            if m.lower().startswith(("act_", "menu_")):
                item.setEnabled(self.parent().is_control_locked() is False)

        if self.parent().is_control_locked():
            return

        nrow = self.tableview().model.rowCount()
        self.act_edit_clear.setEnabled(nrow != 0)
        self.act_export_root_csv.setEnabled(nrow != 0)
        nrow_selected = len(self.tableview().selectionModel().selectedRows())
        self.act_edit_remove_row.setEnabled(nrow_selected != 0)

    def on_act_import_rinfo_file(self):
        files = QFileDialog.getOpenFileNames(
            self, "Import rinfo file(s)", "", "rinfo Files (*.rinfo)"
        )[0]
        if len(files) == 0:
            return

        self.parent().add_from_files(files=files)

    def on_act_import_rinfo_from_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Volume directory", ""
        )
        if directory == "":
            return False

        self.parent().add_from_files(files=[directory])

    def on_act_edit_clear(self):
        row_count = self.tableview().model.rowCount()
        if row_count > 0:
            self.tableview().model.removeRows(0, row_count)
        self.update()

    def on_act_edit_remove_selected(self):
        selection_model = self.tableview().selectionModel()
        for index in selection_model.selectedRows()[::-1]:
            self.tableview().model.removeRow(index.row())
        self.update()

    def on_act_export_root_csv(self):
        csv_fname = QFileDialog.getSaveFileName(
            None, "Save file", "", "*.csv"
        )[0]
        if csv_fname:
            try:
                if not csv_fname.lower().endswith(".csv"):
                    csv_fname += ".csv"
                df = self.parent().tableview.to_pandas_df()
                with open(csv_fname, "w", newline="") as f:
                    df.to_csv(f)

                self.logger().info(f"[Saving succeeded] {csv_fname}")
            except:  # NOQA
                self.logger().error(f"[Saving failed] {csv_fname}")


class RinfoLoader(QThread):
    def __init__(self, parent, files, progressbar_signal):
        super().__init__()
        self.__parent = parent
        self.files = files
        self.progressbar_signal = progressbar_signal

    def parent(self):
        return self.__parent

    def run(self):
        total = len(self.files)
        self.RSA_vector_list = []
        for i, f in enumerate(self.files):
            self.progressbar_signal.emit(i, total, "File loading")
            RSA_vector = RSA_Vector()
            succeeded = RSA_vector.load_from_file(fname=f)
            if succeeded is True:
                self.RSA_vector_list.append(RSA_vector)

        self.quit()
