import argparse
import logging
import warnings

warnings.filterwarnings("ignore")

import GUI

parser = argparse.ArgumentParser(
    description="RSAtrace3D: 3D vectorization software for monocotyledonous RSA."
)
parser.add_argument("-d", "--debug", action="store_true")

args = parser.parse_args()
logger_level = logging.DEBUG if args.debug else logging.INFO

try:
    import coloredlogs

    coloredlogs.install(level=logger_level)
except:
    pass

if __name__ == "__main__":
    logging.basicConfig(level=logger_level)

    pil_logger = logging.getLogger("PIL")
    pil_logger.setLevel(logging.INFO)

    GUI.start()
