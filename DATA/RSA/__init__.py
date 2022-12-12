from .components.file import File
from .components.rinfo import RSA_Vector
from .components.volume import Volume


class RSA_Components(object):
    def __init__(self, parent):
        super().__init__()

        self.volume = Volume(parent=self)
        self.file = File()
        self.vector = RSA_Vector()

        self.vector.register_RSA_components(RSA_components=self)
        self.vector.register_interpolation(parent.interpolation)

    def clear(self):
        self.volume.clear()
        self.vector.clear()
        self.file.clear()
