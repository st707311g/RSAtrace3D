"""Functions for file and directory listing

Author:
    Shota Teramoto (st707311g@gmail.com)

Licence:
    NARO NON-COMMERCIAL LICENSE AGREEMENT Version 1.0

"""

# todo
# VolumeLoader SBIファイルに対応


import os
import unittest
from copy import deepcopy
from glob import glob
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import List

import numpy as np
import open3d as o3d

from volume import Volume3D, VolumeLoader, VolumeSaver, VolumeSeparator


def get_np_volume_test_data():
    return np.random.randint(0, 255, size=(128, 64, 32), dtype=np.uint8)


def get_mm_resolution_test_data():
    return np.random.rand()


def get_point_cloud_test_data():
    xyz = []
    for _ in range(64):
        xyz.append(
            [
                np.random.randint(0, 127),
                np.random.randint(0, 63),
                np.random.randint(0, 31),
            ]
        )

    xyz = np.array(xyz)
    point_cloud_data = o3d.geometry.PointCloud()
    point_cloud_data.points = o3d.utility.Vector3dVector(xyz)

    return point_cloud_data


def get_Volume3D_test_data(
    np_volume: np.ndarray = get_np_volume_test_data(),
    mm_resolution: float = np.random.rand(),
    point_cloud=get_point_cloud_test_data(),
):
    volume3d = Volume3D(
        np_volume=np_volume,
        mm_resolution=mm_resolution,
        point_cloud=point_cloud,
    )

    return volume3d


class TestVolume3D(unittest.TestCase):
    def test_resolution(self):
        mm_resolution = get_mm_resolution_test_data()
        volume3d = get_Volume3D_test_data(mm_resolution=mm_resolution)

        self.assertEqual(volume3d.mm_resolution, mm_resolution)

        with self.assertRaises(AssertionError):
            get_Volume3D_test_data(mm_resolution=-1)

        with self.assertRaises(AssertionError):
            volume3d.mm_resolution = -1

    def test_shape(self):
        np_volume = get_np_volume_test_data()
        volume3d = get_Volume3D_test_data(np_volume=np_volume)

        self.assertEqual(volume3d.shape, np_volume.shape)

        with self.assertRaises(AssertionError):
            get_Volume3D_test_data(
                np_volume=np_volume.reshape(np_volume.shape + (1,))
            )

    def test_equal(self):
        volume3d_1 = get_Volume3D_test_data()
        volume3d_2 = deepcopy(volume3d_1)
        volume3d_2.mm_resolution /= 2

        volume3d_3 = deepcopy(volume3d_1)
        volume3d_3.np_volume = volume3d_3.np_volume // 2

        volume3d_4 = deepcopy(volume3d_1)
        volume3d_4.point_cloud.points = o3d.utility.Vector3dVector(
            np.asarray(volume3d_3.point_cloud.points) // 2
        )

        self.assertTrue(volume3d_1 == volume3d_1)
        self.assertFalse(volume3d_1 == volume3d_2)
        self.assertFalse(volume3d_1 == volume3d_3)
        self.assertFalse(volume3d_1 == volume3d_4)

        self.assertFalse(volume3d_1 != volume3d_1)
        self.assertTrue(volume3d_1 != volume3d_2)
        self.assertTrue(volume3d_1 != volume3d_3)
        self.assertTrue(volume3d_1 != volume3d_4)


class TestVolumeLoader(unittest.TestCase):
    def setUp(self):
        # // making test volume
        self.test_volume3d_instance = get_Volume3D_test_data()

        # // making temporary directory
        self.temporary_directory_p = TemporaryDirectory()
        self.temporary_directory_path = Path(self.temporary_directory_p.name)

        volume_saver = VolumeSaver(self.test_volume3d_instance)
        for i, total in volume_saver.save_files_iterably(
            destination_directory=self.temporary_directory_path,
            extension="png",
        ):
            pass

        # // making temporary archive
        self.temporary_archive_p = NamedTemporaryFile(suffix=".tar.gz")
        self.temporary_archive_path = Path(self.temporary_archive_p.name)

        for i, total in volume_saver.save_volume_as_archive_iterably(
            archive_path=self.temporary_archive_path, extension="png"
        ):
            pass

    def tearDown(self) -> None:
        self.temporary_directory_p.cleanup()
        self.temporary_archive_p.close()

    def test_volume_load(self):
        with self.assertRaises(AssertionError):
            volume_loader = VolumeLoader(
                volume_path=Path(str(self.temporary_directory_path) + "_")
            )

        # // test loading
        for target in [
            self.temporary_directory_path,
            str(self.temporary_directory_path),
            self.temporary_archive_path,
            str(self.temporary_archive_path),
        ]:
            volume_loader = VolumeLoader(volume_path=target)
            self.assertTrue(volume_loader.is_valid_volume())

            self.assertEqual(
                volume_loader.image_file_number,
                self.test_volume3d_instance.shape[0],
            )

            for i, total in volume_loader.load_files_iterably():
                pass
            self.assertEqual(i + 1, total)

            volume3d = volume_loader.get()
            self.assertTrue(
                volume3d == self.test_volume3d_instance,
            )


class TestVolumeSaver(unittest.TestCase):
    def test_volume_save_dtype(self):
        volume3d = get_Volume3D_test_data()

        volume3d = volume3d.astype(np.float64)
        with self.assertRaises(AssertionError):
            VolumeSaver(volume3d=volume3d)

    def test_volume_slice_generator(self):
        volume3d = get_Volume3D_test_data()

        slice_images = list(VolumeSaver(volume3d).slice_generator)
        self.assertEqual(volume3d.shape[0], len(slice_images))
        self.assertTrue((volume3d.np_volume == np.array(slice_images)).all())

    def test_volume_save_files_iterably(self):
        volume3d = get_Volume3D_test_data()
        volume_saver = VolumeSaver(volume3d)

        with TemporaryDirectory() as temporary_directory:
            for i, total in volume_saver.save_files_iterably(
                destination_directory=temporary_directory
            ):
                pass
            self.assertEqual(i + 1, total)

            volume_loader = VolumeLoader(volume_path=temporary_directory)

            self.assertEqual(
                volume_loader.image_file_number,
                volume3d.shape[0],
            )

            self.assertTrue(
                Path(
                    temporary_directory, volume_saver.volume_info_file_name
                ).is_file()
            )

            self.assertTrue(
                Path(
                    temporary_directory, volume_saver.point_cloud_file_name
                ).is_file()
            )

    def test_save_volume_as_archive_iterably(self):
        volume3d = get_Volume3D_test_data()
        volume_saver = VolumeSaver(volume3d)

        with NamedTemporaryFile(suffix=".tar.gz") as temporary_file:
            for i, total in volume_saver.save_volume_as_archive_iterably(
                archive_path=temporary_file.name
            ):
                pass
            self.assertEqual(i + 1, total)
            self.assertTrue(Path(temporary_file.name).is_file())


class TestVolumeSeparator(unittest.TestCase):
    def setUp(self):
        # // making test volume
        self.test_volume3d_instance = Volume3D(
            np_volume=np.random.randint(
                0, 255, size=(128, 64, 32), dtype=np.uint8
            ),
            mm_resolution=0.3,
        )

        # // making temporary directory
        self.temporary_directory_p = TemporaryDirectory()
        self.temporary_directory_path = self.temporary_directory_p.name

    def tearDown(self) -> None:
        self.temporary_directory_p.cleanup()

    def test_volume_separator(self):
        test_block_size, test_overlap = (64, 64, 64), 8

        volume_separator = VolumeSeparator(
            volume3d=self.test_volume3d_instance,
            block_size=test_block_size,
            overlap=test_overlap,
        )

        # // test adjusted_block_size
        self.assertTrue(
            all(
                [
                    size_x == size_y - test_overlap * 2
                    for size_x, size_y in zip(
                        volume_separator.adjusted_block_size, test_block_size
                    )
                ]
            )
        )
        with self.assertRaises(AssertionError):
            VolumeSeparator(
                volume3d=self.test_volume3d_instance,
                block_size=(64, 64, 8),
                overlap=test_overlap,
            )
        separated_volumes = volume_separator.get_separated_volumes()
        self.assertTrue(len(separated_volumes) != 0)

        # // separation test
        for i, subvolume in enumerate(separated_volumes):
            out_file_name = f"image{i:05}.npy"
            np.save(
                Path(self.temporary_directory_path, out_file_name), subvolume
            )

        # // assemble test
        loaded_subvolumes: List[np.ndarray] = []
        for f in sorted(
            glob(str(Path(self.temporary_directory_path, "*.npy")))
        ):
            loaded_subvolumes.append(np.load(f))

        assembled_volume3d = volume_separator.get_assembled_volume(
            loaded_subvolumes
        )
        self.assertTrue(
            (
                self.test_volume3d_instance.np_volume
                == assembled_volume3d.np_volume
            ).all()
        )


if __name__ == "__main__":
    unittest.main()
