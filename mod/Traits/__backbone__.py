import config
from DATA import ID_Object, RSA_Vector
from PySide6.QtGui import QFont, QStandardItem


class RootTraitBackbone(object):
    class_type = "root"
    built_in = False
    label = "Label name"
    sublabels = []
    index = 0
    exportable = True
    updatable = True
    version = -1

    def __init__(self, RSA_vector: RSA_Vector, ID_string: ID_Object):
        super().__init__()
        self.__RSA_vector = RSA_vector
        self.__ID_string = ID_string
        self.value = self.calculate(self.__RSA_vector, self.__ID_string)

    def calculate(self, RSA_vector: RSA_Vector, ID_string: ID_Object):
        return ""

    def update(self):
        if self.updatable:
            self.value = self.calculate(self.__RSA_vector, self.__ID_string)
            self.item.setText(self.str_value())

    def str_value(self):
        if self.value is None:
            return ""
        return str(self.value)

    def QStandardItem(self):
        self.item = QStandardItem(self.str_value())
        self.item.setData(self)

        font = self.item.font()
        font.setFamily("Monospace")
        font.setStyleHint(QFont.Monospace)
        self.item.setFont(font)

        return self.item

    @classmethod
    def check(cls):
        if cls.version < 0 or cls.version > config.version:
            raise Exception(
                f"The RSAtrace version should be >= {cls.version}. "
                "(class name: {cls.__name__})"
            )
        if cls.built_in is False:
            if cls.index < 0 or cls.index > 255:
                raise Exception(
                    'The "index" should be >= 0 and <= 255.'
                    f"(class name: {cls.__name__})"
                )


class RSATraitBackbone(object):
    class_type = "RSA"
    built_in = False
    label = "Label name"
    sublabels = []
    index = 0
    exportable = True
    updatable = True
    version = -1

    def __init__(self, RSA_vector: RSA_Vector):
        super().__init__()
        self.__RSA_vector = RSA_vector
        self.value = self.calculate(self.__RSA_vector)

    def calculate(self, RSA_vector: RSA_Vector):
        return ""

    def update(self):
        if self.updatable:
            self.value = self.calculate(self.__RSA_vector)
            self.item.setText(self.str_value())

    def str_value(self):
        return str(self.value)

    def QStandardItem(self):
        self.item = QStandardItem(self.str_value())
        self.item.setData(self)
        self.item.setEditable(False)

        font = self.item.font()
        font.setFamily("Monospace")
        font.setStyleHint(QFont.Monospace)
        self.item.setFont(font)

        return self.item

    @classmethod
    def check(cls):
        if cls.version < 0 or cls.version > config.version:
            raise Exception(
                f"The RSAtrace version should be >= {cls.version}. "
                f"(class name: {cls.__name__})"
            )
        if cls.built_in is False:
            if cls.index < 0 or cls.index > 255:
                raise Exception(
                    'The "index" should be >= 0 and <= 255. '
                    f"(class name: {cls.__name__})"
                )
