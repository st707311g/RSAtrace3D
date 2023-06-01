from .components.file import File
from .components.rinfo import RSA_Vector
from .components.volume import Volume
import numpy as np
from GUI.components import QtMain
import logging


class RSA_Components(object):
    def __init__(self, parent: QtMain):
        super().__init__()
        self.main = parent
        self.logger = logging.getLogger(self.__class__.__name__)
        self.__volumes = [Volume(parent=self)]
        self.__current_volume_index = 0
        self.file = File()
        self.vector = RSA_Vector()

        self.vector.register_RSA_components(RSA_components=self)
        self.vector.register_interpolation(parent.interpolation)

    @property
    def volume(self):
        return self.__volumes[self.__current_volume_index]

    def set_volumes(self, np_vols: list[np.ndarray], labels: list[str]):
        assert len(np_vols) == len(labels)
        assert len(np_vols) >= 1

        self.__volumes: list[Volume] = []
        for np_vol, label in zip(np_vols, labels):
            self.__volumes.append(Volume(parent=self))
            self.__volumes[-1].init_from_volume(volume=np_vol)

    def shift_current_volume(self):
        self.__current_volume_index = (self.__current_volume_index + 1) % len(
            self.__volumes
        )
        self.logger.debug(
            f"[volume index changed] {self.__current_volume_index}"
        )

    def clear(self):
        self.__volumes = [Volume(parent=self)]
        self.__current_volume_index = 0
        self.vector.clear()
        self.file.clear()
