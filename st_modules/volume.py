"""Functions for 3D volume handling

Author:
    Shota Teramoto (st707311g@gmail.com)

Licence:
    NARO NON-COMMERCIAL LICENSE AGREEMENT Version 1.0

"""

import itertools
import json
import logging
import os
import tarfile
from dataclasses import dataclass, field
from operator import attrgetter
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Final, Generator, List, Tuple

import numpy as np
import open3d as o3d
from skimage import io

VOLUME_INFO_FILE_NAME: Final[str] = ".volume_info.json"
POINT_CLOUD_FILE_NAME: Final[str] = ".sbi_info.pcd"


class Volume3D(object):
    """
    A class for handling a 3D volume.

    Args:
        np_volume (np.ndarray): 3D volume data. Only grayscale images are acceptable.
        mm_resolution (float, optional): Spatioal resolution of np_volume.
    """

    def __init__(
        self,
        np_volume: np.ndarray,
        mm_resolution: float = 0,
        point_cloud: Any = None,
    ) -> None:
        self.np_volume = np_volume
        self.mm_resolution = mm_resolution
        self.point_cloud = point_cloud

        assert self.is_valid_volume_shape()

    def is_valid_volume_shape(self):
        return len(self.np_volume.shape) == 3

    @property
    def shape(self):
        return self.np_volume.shape

    @property
    def dtype(self):
        return self.np_volume.dtype

    @property
    def information_dict(self):
        """
        Return the dictionary object, including information of the 3D volume.
        """
        return_dict = {}
        if self.mm_resolution:
            return_dict.update({"mm_resolution": self.mm_resolution})

        return return_dict

    def astype(self, dtype):
        return Volume3D(
            np_volume=self.np_volume.astype(dtype),
            mm_resolution=self.mm_resolution,
            point_cloud=self.point_cloud,
        )

    @property
    def mm_resolution(self):
        return self.__mm_resolution

    @mm_resolution.setter
    def mm_resolution(self, value):
        assert value >= 0
        self.__mm_resolution = value

    @property
    def point_cloud(self):
        return self.__point_cloud

    @point_cloud.setter
    def point_cloud(self, item):
        assert item is None or isinstance(item, o3d.geometry.PointCloud)
        self.__point_cloud = item

    def __repr__(self) -> str:
        if self.point_cloud is None:
            point_cloud_str = "None"
        else:
            point_cloud_str = f"{len(self.point_cloud.points)} points"
        return {
            "shape": self.shape,
            "dtype": self.dtype,
            "mm_resolution": self.mm_resolution,
            "sbi_point_cloud": point_cloud_str,
        }.__str__()

    def __eq__(self, __o: object) -> bool:
        assert isinstance(__o, Volume3D)
        is_equal_resolution = self.mm_resolution == __o.mm_resolution
        is_equal_volume = (self.np_volume == __o.np_volume).all()
        is_equal_point_cloud = (
            self.point_cloud is None and __o.point_cloud is None
        ) or (
            np.asarray(self.point_cloud.points)
            == np.asarray(__o.point_cloud.points)
        ).all()
        return all(
            [is_equal_resolution, is_equal_volume, is_equal_point_cloud]
        )


@dataclass
class VolumeLoader(object):
    """
    A class for 3D volume loading.
    """

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
    volume_info_file_name: Final[str] = VOLUME_INFO_FILE_NAME
    point_cloud_file_name: Final[str] = POINT_CLOUD_FILE_NAME

    @property
    def DEFAULT_VOLUME_INFORMATION(self):
        return {"mm_resolution": 0.3}

    def __post_init__(self):
        assert os.path.isdir(self.volume_path) or os.path.isfile(
            self.volume_path
        )

        self.volume_path = str(self.volume_path)

        if os.path.isfile(self.volume_path):
            assert self.volume_path.endswith(".tar.gz")

    @property
    def image_file_list(self):
        img_files = []
        if os.path.isdir(self.volume_path):
            img_files = [
                os.path.join(self.volume_path, f)
                for f in os.listdir(self.volume_path)
            ]
        elif os.path.isfile(self.volume_path):
            with tarfile.open(name=self.volume_path, mode="r") as tar:
                for info in tar.getmembers():
                    if info.name.lower().endswith(self.extensions):
                        img_files.append(info.name)

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
        volume_information = self.DEFAULT_VOLUME_INFORMATION
        point_cloud = None
        image_list = []
        image_file_number = self.image_file_number

        if os.path.isdir(self.volume_path):
            for i, image_file_path in enumerate(self.image_file_list):
                image_list.append(io.imread(image_file_path))
                yield i, image_file_number

            volume_info_path = Path(
                self.volume_path, self.volume_info_file_name
            )
            if os.path.isfile(volume_info_path):
                with open(volume_info_path) as f:
                    volume_information.update(json.load(f))

            point_cloud_path = Path(
                self.volume_path, self.point_cloud_file_name
            )
            if os.path.isfile(point_cloud_path):
                point_cloud = o3d.io.read_point_cloud(str(point_cloud_path))

        elif os.path.isfile(self.volume_path):
            image_file_list = set(self.image_file_list)
            with tarfile.open(name=self.volume_path, mode="r") as tar:
                info_list = []
                for info in tar.getmembers():
                    if info.name in image_file_list:
                        info_list.append(info)
                    elif info.name == self.volume_info_file_name:
                        volume_information.update(
                            json.load(tar.extractfile(info))
                        )
                    elif info.name == self.point_cloud_file_name:
                        with TemporaryDirectory() as temporary_directory:
                            tar.extract(info, temporary_directory)
                            point_cloud = o3d.io.read_point_cloud(
                                os.path.join(temporary_directory, info.name)
                            )

                info_list.sort(key=attrgetter("name"))
                for i, info in enumerate(info_list):
                    image_list.append(io.imread(tar.extractfile(info)))
                    yield i, len(info_list)

        else:
            assert False

        self.__volume3d = Volume3D(
            np_volume=np.array(image_list),
            **volume_information,
            point_cloud=point_cloud,
        )

    def get(self):
        return self.__volume3d


@dataclass
class VolumeSaver(object):
    """
    A class for 3D volume saving.
    """

    volume3d: Final[Volume3D]
    digits: Final[int] = 4
    volume_info_file_name: Final[str] = VOLUME_INFO_FILE_NAME
    point_cloud_file_name: Final[str] = POINT_CLOUD_FILE_NAME

    def __post_init__(self):
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

        for i, img in enumerate(self.slice_generator):
            image_file_path = Path(
                destination_directory_path,
                f"img{str(i).zfill(self.digits)}.{extension}",
            )
            io.imsave(image_file_path, img)
            yield i, len(self.np_volume)

        # // saving volume infomartion data
        try:
            with open(
                Path(destination_directory_path, self.volume_info_file_name),
                "w",
            ) as f:
                json.dump(self.volume3d.information_dict, f)
        except:
            pass

        # // saving point cloud data
        try:
            o3d.io.write_point_cloud(
                str(
                    Path(
                        destination_directory_path, self.point_cloud_file_name
                    )
                ),
                self.volume3d.point_cloud,
            )
        except:
            pass

    def save_volume_as_archive_iterably(
        self, archive_path: str, extension="jpg"
    ):
        archive_path = str(archive_path)
        if not archive_path.lower().endswith(".tar.gz"):
            archive_path += ".tar.gz"

        archive_path: Path = Path(archive_path)

        with TemporaryDirectory() as temporary_directory:
            for i, total in self.save_files_iterably(
                destination_directory=temporary_directory,
                extension=extension,
            ):
                yield i, total

            with tarfile.open(archive_path, "w:gz") as tar:
                cwd = os.getcwd()
                os.chdir(temporary_directory)

                for f in sorted(os.listdir(".")):
                    tar.add(f)

                os.chdir(cwd)


@dataclass
class VolumeSeparator(object):
    """
    A class for 3D volume separating and assembling.
    """

    volume3d: Volume3D
    logger: logging.Logger = field(default=None, repr=False)
    block_size: Tuple[int] = (64, 64, 64)
    overlap: int = 8

    def __post_init__(self):
        assert min(self.block_size) > 8
        self.logger = self.logger or logging.getLogger(self.__class__.__name__)

        self.logger.debug(f"a class constructed: {self.__class__.__name__}")
        self.logger.debug(f"{self.volume3d.shape=}")
        self.logger.debug(f"{self.block_size=}")
        self.logger.debug(f"{self.padding_size=}")
        self.logger.debug(f"{self.padded_image_shape=}")

    @property
    def adjusted_block_size(self):
        return tuple([size - self.overlap * 2 for size in self.block_size])

    @property
    def padding_size(self):
        padding_size = tuple(
            [
                int(
                    np.ceil(
                        self.volume3d.shape[i] / self.adjusted_block_size[i]
                    )
                )
                * self.adjusted_block_size[i]
                - self.volume3d.shape[i]
                for i in range(3)
            ]
        )
        return tuple([(self.overlap, _ + self.overlap) for _ in padding_size])

    @property
    def padded_image_shape(self):
        return tuple(
            [
                self.volume3d.shape[i] + sum(self.padding_size[i])
                for i in range(3)
            ]
        )

    def get_separated_volumes(self) -> List[np.ndarray]:
        img = self.volume3d.np_volume.copy()
        img = np.pad(img, self.padding_size, mode="reflect")

        separated_images = []
        range_list = [
            range(img.shape[i] // self.adjusted_block_size[i])
            for i in range(3)
        ]
        for zi, yi, xi in itertools.product(*range_list):
            index_list = [zi, yi, xi]
            slice_list = [
                slice(
                    index_list[i] * self.adjusted_block_size[i],
                    (index_list[i] + 1) * self.adjusted_block_size[i]
                    + self.overlap * 2,
                )
                for i in range(3)
            ]
            cropped_image = img[tuple(slice_list)]
            separated_images.append(cropped_image)

        self.logger.debug(f"number of image tiles: {len(separated_images)}")

        return separated_images

    def get_assembled_volume(self, separated_volume_list: List[np.ndarray]):
        output_volume = np.zeros(self.padded_image_shape, dtype=np.uint8)

        i = 0
        range_list = [
            range(output_volume.shape[i] // self.adjusted_block_size[i])
            for i in range(3)
        ]
        for zi, yi, xi in itertools.product(*range_list):
            index_list = [zi, yi, xi]
            slice_list = [
                slice(
                    index_list[i] * self.adjusted_block_size[i] + self.overlap,
                    (index_list[i] + 1) * self.adjusted_block_size[i]
                    + self.overlap,
                )
                for i in range(3)
            ]
            output_volume[tuple(slice_list)] = separated_volume_list[i][
                self.overlap : -self.overlap,
                self.overlap : -self.overlap,
                self.overlap : -self.overlap,
            ]
            i += 1

        output_volume = output_volume[
            tuple(
                [
                    slice(self.padding_size[d][0], -self.padding_size[d][1])
                    for d in range(3)
                ]
            )
        ]
        volume3d = Volume3D(
            np_volume=output_volume, mm_resolution=self.volume3d.mm_resolution
        )
        return volume3d
