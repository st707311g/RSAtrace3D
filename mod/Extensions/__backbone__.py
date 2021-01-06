import config

class ExtensionBackbone(object):
    built_in = False
    label = 'Label name'
    index = 0
    version = 1

    def __init__(self, *args, **kwargs):
        super().__init__()

    @classmethod
    def check(cls):
        if cls.version < 0 or cls.version > config.version:
            raise Exception(f'The RSAtrace version should be >= {cls.version}. (class name: {cls.__name__})')
        if cls.built_in == False:
            if cls.index < 0 or cls.index > 255:
                raise Exception(f'The "index" should be >= 0 and <= 255. (class name: {cls.__name__})')