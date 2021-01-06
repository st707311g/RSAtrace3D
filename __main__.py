import logging, warnings
warnings.filterwarnings('ignore')

import GUI

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    pil_logger = logging.getLogger('PIL')
    pil_logger.setLevel(logging.INFO)

    GUI.start()