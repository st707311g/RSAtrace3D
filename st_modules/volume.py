import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Generator, Tuple

import imageio.v3 as imageio
import numpy as np

VOLUME_INFO_FILE_NAME: Final[str] = ".volume_info.json"


class Volume3D(object):
    def __init__(self, np_volume: np.ndarray, mm_resolution: float, **kwargs):
        self.np_volume = np_volume
        self.mm_resolution = mm_resolution

        assert self.is_valid_volume_shape()
        assert self.mm_resolution > 0

    def is_valid_volume_shape(self):
        return len(self.np_volume.shape) == 3

    @property
    def information_dict(self):
        return {"mm_resolution": self.mm_resolution}


@dataclass
class VolumeLoader(object):
    volume_path: Final[str]
    minimum_file_number: Final[int] = 64
    extensions: Final[Tuple] = (
        ".cb",
        ".png",
        ".tif",
        ".tiff",
        ".jpg",
        ".jpeg",
    )
    logger: logging.Logger = field(default=None, repr=False)
    volume_info_file_name: Final[str] = VOLUME_INFO_FILE_NAME

    @property
    def DEFAULT_VOLUME_INFORMATION(self):
        return {"mm_resolution": 0.3}

    def __post_init__(self):
        super().__init__()
        self.logger = self.logger or logging.getLogger(self.__class__.__name__)

        assert os.path.isdir(self.volume_path)

    @property
    def image_file_list(self):
        img_files = []
        if os.path.isdir(self.volume_path):
            img_files = [
                os.path.join(self.volume_path, f)
                for f in os.listdir(self.volume_path)
            ]

        ext_count = []
        for ext in self.extensions:
            ext_count.append(
                len([f for f in img_files if f.lower().endswith(ext)])
            )

        target_extension = self.extensions[ext_count.index(max(ext_count))]
        return sorted(
            [f for f in img_files if f.lower().endswith(target_extension)]
        )

    @property
    def image_file_number(self):
        return len(self.image_file_list)

    def is_valid_volume(self):
        return self.image_file_number >= self.minimum_file_number

    def load_files_iterably(self):
        self.logger.info(f"Loading image files: {self.volume_path}")

        image_list = []
        image_file_number = self.image_file_number
        for i, image_file_path in enumerate(self.image_file_list):
            image_list.append(imageio.imread(image_file_path))
            yield i + 1, image_file_number

        volume_information = self.DEFAULT_VOLUME_INFORMATION
        volume_info_path = Path(self.volume_path, self.volume_info_file_name)
        if os.path.isfile(volume_info_path):
            with open(volume_info_path) as f:
                volume_information.update(json.load(f))

        self.__volume3d = Volume3D(
            np_volume=np.array(image_list),
            **volume_information,
        )

    def get(self):
        return self.__volume3d


@dataclass
class VolumeSaver(object):
    volume3d: Final[Volume3D]
    logger: logging.Logger = field(default=None, repr=False)
    digits: Final[int] = 4
    volume_info_file_name: Final[str] = VOLUME_INFO_FILE_NAME

    def __post_init__(self):
        super().__init__()
        self.logger = self.logger or logging.getLogger(self.__class__.__name__)

        assert self.is_valid_volume_dtype()
        assert self.is_valid_volume_shape()
        assert self.digits > 0

    @property
    def np_volume(self):
        return self.volume3d.np_volume

    def is_valid_volume_dtype(self):
        return self.np_volume.dtype == np.uint8

    def is_valid_volume_shape(self):
        return len(self.np_volume.shape) == 3

    @property
    def slice_generator(self) -> Generator[np.ndarray, None, None]:
        for slice_image in self.np_volume:
            yield slice_image

    def save_files_iterably(self, destination_directory: str, extension="jpg"):
        destination_directory_path = Path(destination_directory)
        os.makedirs(destination_directory_path, exist_ok=True)

        self.logger.info(
            f"Saving {self.np_volume.shape[0]} image files: {destination_directory_path}"
        )
        for i, img in enumerate(self.np_volume):
            image_file_path = Path(
                destination_directory_path,
                f"img{str(i).zfill(self.digits)}.{extension}",
            )
            imageio.imwrite(image_file_path, img)
            yield i + 1, len(self.np_volume)

        with open(
            Path(destination_directory_path, self.volume_info_file_name), "w"
        ) as f:
            json.dump(self.volume3d.information_dict, f)
