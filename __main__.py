import argparse
import logging
import warnings
from pathlib import Path

import config
import GUI

warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser(
    description="RSAtrace3D: 3D vectorization software for monocotyledonous RSA."
)
parser.add_argument("-d", "--debug", action="store_true")
parser.add_argument("-s", "--source", type=str, help="source volume path")
parser.add_argument("--always_yes", action="store_true")

args = parser.parse_args()
logger_level = logging.DEBUG if args.debug else logging.INFO

try:
    import coloredlogs

    coloredlogs.install(level=logger_level)
except ModuleNotFoundError:
    pass

if __name__ == "__main__":
    logging.basicConfig(level=logger_level)

    pil_logger = logging.getLogger("PIL")
    pil_logger.setLevel(logging.INFO)

    volume_path: Path = None
    if args.source:
        volume_path = Path(args.source)

    logger = logging.getLogger("RSAtrace3D")
    logger.debug(f"{args=}")

    config.ALWAYS_YES = args.always_yes

    GUI.start(volume_path=volume_path)
