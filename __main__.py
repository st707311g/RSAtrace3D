import logging, warnings
warnings.filterwarnings('ignore')

try:
    import coloredlogs
    coloredlogs.install(level=logging.INFO)
except:
    pass

import GUI

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    pil_logger = logging.getLogger('PIL')
    pil_logger.setLevel(logging.INFO)

    GUI.start()