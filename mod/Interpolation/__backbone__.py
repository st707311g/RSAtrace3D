import config
from DATA import RSA_Components


class InterpolationBackbone(object):
    built_in = False
    label = "Label name"
    index = 0
    version = 1

    def __init__(self, RSA_components: RSA_Components):
        super().__init__()
        self.__RSA_components = RSA_components

    def RSA_components(self):
        return self.__RSA_components

    @classmethod
    def check(cls):
        if cls.version < 0 or cls.version > config.version:
            raise Exception(
                f"The RSAtrace version should be >= {cls.version}. (class name: {cls.__name__})"
            )
        if cls.built_in == False:
            if cls.index < 0 or cls.index > 255:
                raise Exception(
                    f'The "index" should be >= 0 and <= 255. (class name: {cls.__name__})'
                )
