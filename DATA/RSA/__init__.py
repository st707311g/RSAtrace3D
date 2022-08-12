from .components import (
    File,
    ID_Object,
    RinfoFiles,
    RSA_Vector,
    Trace,
    TraceObject,
    Volume,
)


class RSA_Components(object):
    def __init__(self, parent):
        super().__init__()

        self.volume = Volume(parent=self)
        self.file = File()
        self.vector = RSA_Vector()
        self.trace = Trace()

        self.vector.register_RSA_components(RSA_components=self)
        self.vector.register_interpolation(parent.interpolation)

    def clear(self):
        self.volume.clear()
        self.trace.clear()
        self.vector.clear()
        self.file.clear()
