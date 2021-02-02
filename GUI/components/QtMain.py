from PyQt5.QtCore import Qt, QThread, QEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QSplitter, QMessageBox
from .QtSliceView import QtSliceView
from .QtStatusBar import QtStatusBarW
from .QtTreeView import QtTreeView
from .QtProjectionView import QtProjectionView
from .QtToolbar import QtToolBar
from .QtMenubar import QtMenubar

import numpy as np
from skimage import io
import os, logging, json

from mod import RootTraits, RSATraits, Interpolation, Extensions
from DATA import RSA_Components, File
import config

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
        self.__RSA_components = RSA_Components(parent=self)
        self.__GUI_components = GUI_Components(parent=self)
        self.setStatusBar(self.GUI_components().statusbar.widget)

        self.init_interface()
        self.setAcceptDrops(True)

    def init_interface(self):
        self.resize(1200,800)
        self.setWindowTitle()

        #// splitter setting
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.sub_splitter = QSplitter(Qt.Vertical)
        self.sub_splitter.addWidget(self.GUI_components().treeview)
        self.sub_splitter.addWidget(self.GUI_components().projectionview)
        self.main_splitter.addWidget(self.GUI_components().sliceview)
        self.main_splitter.addWidget(self.sub_splitter)
        self.main_splitter.setSizes([1024,1024])
        self.sub_splitter.setSizes([1024,1024])
        self.setCentralWidget(self.main_splitter)

        self.GUI_components().menubar.build()
        self.setMenuBar(self.GUI_components().menubar)
        self.addToolBar(self.GUI_components().toolbar)
        self.GUI_components().menubar.update()

        self.show_default_msg_in_statusbar()
        self.load_config()

    def load_config(self):
        config_dict = config.load()
        resolution = float(config_dict.get('resolution', 0.3))
        interpolation_name = config_dict.get('interpolation', 'Straigth')

        self.set_resolution(resolution=resolution)
        self.interpolation.set_selected_by(label=interpolation_name)

    def save_config(self):
        config_dict = {
            'resolution': float(self.GUI_components().toolbar.voxel_lineedit.text()),
            'interpolation': self.interpolation.get_selected_label()
        }
        config.save(**config_dict)

    def GUI_components(self):
        return self.__GUI_components

    def RSA_components(self):
        return self.__RSA_components

    def is_control_locked(self):
        return self.__control_locked

    def set_control(self, locked):
        self.__control_locked=locked
        self.logger.debug(f'Control locked: {self.__control_locked}')
        self.GUI_components().menubar.update()

        if locked:
            QApplication.setOverrideCursor(Qt.WaitCursor)
        else:
            QApplication.restoreOverrideCursor()

    def is_spacekey_pressed(self):
        return self.__spacekey_pressed

    def set_spacekey(self, pressed: bool):
        self.__spacekey_pressed = pressed
        self.logger.debug(f'Space key pressed: {self.__spacekey_pressed}')
        for w in [self.GUI_components().sliceview, self.GUI_components().projectionview]:
            w.on_spacekey_pressed(pressed=self.__spacekey_pressed)

    def dragEnterEvent(self, ev):
        ev.accept()
        
    def dropEvent(self, ev):
        ev.accept()

        flist = [u.toLocalFile() for u in ev.mimeData().urls()]

        if len(flist) != 1 or not os.path.isdir(flist[0]):
            self.logger.error('Only 1 directory at once is acceptable.')
            return

        self.load_from(directory=flist[0])

    def load_from(self, directory, rinfo_dict: dict = {}):
        VolumeFile = File(volume_directory=directory)
        if not VolumeFile.is_valid():
            self.logger.error(f'[Loading error] {directory}')
            self.logger.error(f'At least 64 slice images required.')
            return False
            
        self.rinfo_dict = rinfo_dict
        self.close_volume()
        self.RSA_components().file = VolumeFile
        flist = self.RSA_components().file.img_files

        self.set_control(locked=True)
        self.floader = VolumeLoader(flist, progressbar_signal=self.GUI_components().statusbar.pyqtSignal_update_progressbar)
        self.floader.finished.connect(self.on_volume_loaded)
        self.floader.start()
        self.GUI_components().menubar.history.add(directory)
        self.GUI_components().menubar.history.update_menu()

    def on_volume_loaded(self):
        volume = self.floader.data()
        del self.floader

        self.logger.info(f'[Loading succeeded] {self.RSA_components().file.directory}')

        self.RSA_components().volume.init_from_volume(volume=volume)
        self.RSA_components().trace.init_from_volume(volume=volume)
        self.GUI_components().sliceview.update_volume(volume=volume)
        self.GUI_components().projectionview.set_volume(volume=volume)

        trace3D = self.RSA_components().trace.trace3D
        if trace3D is not None:
            self.GUI_components().sliceview.update_trace3D(trace3D)

        loaded = False
        if self.rinfo_dict:
            loaded = self.load_rinfo_from_dict(self.rinfo_dict)
        elif self.RSA_components().file.is_rinfo_file_available():
            ret = QMessageBox.information(None, "Information", "The rinfo file is available. Do you want to import this?", QMessageBox.Yes, QMessageBox.No)
            if ret == QMessageBox.Yes:
                loaded = self.load_rinfo(fname=self.RSA_components().file.rinfo_file)
                self.set_volume_name(volume_name=self.RSA_components().vector.annotations.volume_name())
                self.set_resolution(resolution=self.RSA_components().vector.annotations.resolution())

        if loaded == False:
            self.set_volume_name(volume_name=self.RSA_components().file.volume)
            self.set_resolution(resolution=0.301)

            interpolation = self.RSA_components().vector.interpolation
            self.RSA_components().vector.annotations.set_interpolation(interpolation.get_selected_label())
            self.RSA_components().vector.annotations.set_volume_shape(volume.shape)

        self.set_control(locked=False)
        selected_ID_string = self.GUI_components().treeview.get_selected_ID_string()
        if selected_ID_string is not None:
            self.GUI_components().projectionview.on_selected_item_changed(ID_string=selected_ID_string)

        self.show_default_msg_in_statusbar()
        self.setWindowTitle()
        self.GUI_components().menubar.update()

    def load_rinfo_from_dict(self, rinfo_dict: dict, file: str = ""):
        RSA_vector = self.RSA_components().vector
        treeview = self.GUI_components().treeview
        ret = RSA_vector.load_from_dict(rinfo_dict, file=file)
        if ret == False:
            return False
            
        for ID_string in RSA_vector.iter_all():
            if ID_string.is_base():
                treeview.add_base(ID_string=ID_string)
            elif ID_string.is_root():
                treeview.add_root(ID_string=ID_string)
            else:
                treeview.add_relay(ID_string=ID_string)

        self.GUI_components().sliceview.update_trace_graphics()

        return True

    def load_rinfo(self, fname: str):
        with open(fname, 'r') as f:
            trace_dict = json.load(f)

        return self.load_rinfo_from_dict(trace_dict, file=fname)

    #// key press event
    def keyPressEvent(self, ev):
        ev.accept()
        if self.is_control_locked():
            return

        if ev.key() == Qt.Key_Space and not ev.isAutoRepeat():
            self.set_spacekey(pressed=True)

        if ev.key() == Qt.Key_Delete and not ev.isAutoRepeat():
            selected_ID_string = self.GUI_components().treeview.get_selected_ID_string()
            if selected_ID_string is None:
                return

            #// choose ID_string that should be deleted
            if selected_ID_string.is_base():
                target_node = self.RSA_components().vector.base_node(ID_string=selected_ID_string)
            elif selected_ID_string.is_root():
                target_node = self.RSA_components().vector.root_node(ID_string=selected_ID_string)
            else:
                root_node = self.RSA_components().vector.root_node(ID_string=selected_ID_string)
                if root_node.child_count() > 1:
                    target_node = self.RSA_components().vector.relay_node(ID_string=selected_ID_string)
                else:
                    target_node = self.RSA_components().vector.root_node(ID_string=selected_ID_string)

            ID_string = target_node.ID_string()
            self.GUI_components().treeview.select(ID_string=ID_string)
            target_node.delete()
            self.GUI_components().treeview.delete(ID_string=ID_string)
            self.GUI_components().sliceview.update_trace_graphics()

        return

    #// key release event
    def keyReleaseEvent(self, ev):
        ev.accept()
        if self.is_control_locked():
            return
            
        if ev.key() == Qt.Key_Space and not ev.isAutoRepeat():
            self.set_spacekey(pressed=False)

    #// event hook
    def event(self, ev):
        if ev.type() == QEvent.StatusTip:
            if ev.tip() != '':
                self.GUI_components().statusbar.set_main_message(ev.tip())
            else:
                self.show_default_msg_in_statusbar()
            return True
        elif ev.type()==QEvent.WindowDeactivate:
                self.set_spacekey(pressed=False)
                return super().event(ev)
        else:
            return super().event(ev)

    def closeEvent(self, *args, **kwargs):
        self.GUI_components().menubar.history.save('recent.json')
        self.save_config()
        super().closeEvent(*args, **kwargs)

    def close_volume(self):
        if self.RSA_components().volume.is_empty():
            return

        self.RSA_components().clear()
        self.GUI_components().sliceview.clear()
        self.GUI_components().treeview.clear()
        self.GUI_components().menubar.update()
        self.GUI_components().projectionview.clear()

        self.show_default_msg_in_statusbar()
        self.setWindowTitle()

    def show_default_msg_in_statusbar(self):
        if self.RSA_components().volume.is_empty():
            msg = 'Open your volume file.'
        else:
            msg = 'Add or delete the base, root, and relay nodes anywhere.'
        self.GUI_components().statusbar.set_main_message(msg)

    def set_volume_name(self, volume_name):
        self.GUI_components().toolbar.volumename_edit.setText(volume_name)
        self.RSA_components().vector.annotations.set_volume_name(name=volume_name)

    def set_resolution(self, resolution):
        self.GUI_components().toolbar.voxel_lineedit.setText(str(resolution))
        self.RSA_components().vector.annotations.set_resolution(resolution=resolution)

    def setWindowTitle(self):
        text = f'RSAtrace3D (version {config.version_string()})'
        if not self.RSA_components().volume.is_empty():
            dir_name = self.RSA_components().file.volume
            text = f'{text} - {dir_name}'
        super().setWindowTitle(text)
    
class VolumeLoader(QThread):
    def __init__(self, files, progressbar_signal):
        super().__init__()
        self.files = files
        self.progressbar_signal = progressbar_signal

    def run(self):
        def fun(f, i, total):
            self.progressbar_signal.emit(i, total, 'File loading')
            return io.imread(f)

        self.__data = [fun(f, i, len(self.files)) for i, f in enumerate(self.files)]
        self.quit()

    def data(self):
        return np.array(self.__data, dtype=np.uint8)