import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Final, List, Tuple, Union

import numpy as np
from skimage import io

VOLUME_INFO_FILE_NAME: Final[str] = ".volume_info.json"


class VolumeLoader(object):
    def __init__(
        self,
        volume_path: Union[str, Path],
        minimum_file_number: int = 64,
        extensions: Tuple = (
            ".cb",
            ".png",
            ".tif",
            ".tiff",
            ".jpg",
            ".jpeg",
        ),
        volume_info_file_name: str = VOLUME_INFO_FILE_NAME,
    ) -> None:
        self.volume_path = Path(volume_path).resolve()
        self.minimum_file_number = minimum_file_number
        self.extensions = extensions
        self.volume_info_path = Path(self.volume_path, volume_info_file_name)

        self.__image_files: List[Path] = None

        assert self.volume_path.is_dir()

    @property
    def DEFAULT_VOLUME_INFORMATION(self) -> Dict[Any, Any]:
        return {"mm_resolution": 0.3}

    @property
    def image_files(self):
        if self.__image_files:
            return self.__image_files

        files = [
            Path(self.volume_path, f) for f in os.listdir(self.volume_path)
        ]

        ext_count = []
        for ext in self.extensions:
            ext_count.append(
                len([f for f in files if str(f).lower().endswith(ext)])
            )

        target_extension = self.extensions[ext_count.index(max(ext_count))]
        self.__image_files = sorted(
            [f for f in files if str(f).lower().endswith(target_extension)]
        )
        return self.__image_files

    @property
    def image_file_number(self):
        return len(self.image_files)

    def is_valid_volume(self):
        return self.image_file_number >= self.minimum_file_number

    def load(self):
        return np.array([io.imread(f) for f in self.image_files])

    def load_volume_info(self):
        volume_information = self.DEFAULT_VOLUME_INFORMATION

        if self.volume_info_path.is_file():
            with open(self.volume_info_path) as f:
                volume_information.update(json.load(f))

        return volume_information


@dataclass
class VolumeSaver(object):
    np_volume: Final[np.ndarray]
    volume_info: Final[Dict]
    digits: Final[int] = 4
    volume_info_file_name: Final[str] = VOLUME_INFO_FILE_NAME

    def __post_init__(self):
        assert self.is_valid_volume_dtype()
        assert self.is_valid_volume_shape()
        assert self.digits > 0

    def is_valid_volume_dtype(self):
        return self.np_volume.dtype == np.uint8

    def is_valid_volume_shape(self):
        return len(self.np_volume.shape) == 3

    def save_iterably(self, dst_path: Path, extension="jpg"):
        os.makedirs(dst_path, exist_ok=True)

        for i, img in enumerate(self.np_volume):
            slice_dst_path = Path(
                dst_path,
                f"img{str(i).zfill(self.digits)}.{extension}",
            )
            io.imsave(slice_dst_path, img)
            yield i, len(self.np_volume)

        # // saving volume infomartion data
        if len(self.volume_info):
            with open(
                Path(dst_path, self.volume_info_file_name),
                "w",
            ) as f:
                json.dump(self.volume_info, f)
