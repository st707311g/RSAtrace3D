"""Functions for file and directory listing

Author:
    Shota Teramoto (st707311g@gmail.com)

Licence:
    NARO NON-COMMERCIAL LICENSE AGREEMENT Version 1.0

"""

import os
import unittest
from glob import glob
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import List

import numpy as np

from volume import Volume3D, VolumeLoader, VolumeSaver, VolumeSeparator


class TestVolume3D(unittest.TestCase):
    def setUp(self):
        self.np_volume_for_test = np.random.randint(
            0, 255, size=(128, 64, 32), dtype=np.uint8
        )
        self.mm_resolution_for_test = np.random.rand()

    def test_resolution(self):
        volume3d = Volume3D(
            np_volume=self.np_volume_for_test,
            mm_resolution=self.mm_resolution_for_test,
        )
        self.assertEqual(volume3d.mm_resolution, self.mm_resolution_for_test)

        with self.assertRaises(AssertionError):
            volume3d = Volume3D(
                np_volume=self.np_volume_for_test,
                mm_resolution=-1,
            )

        with self.assertRaises(AssertionError):
            volume3d.mm_resolution = -1

    def test_shape(self):
        volume3d = Volume3D(
            np_volume=self.np_volume_for_test,
            mm_resolution=self.mm_resolution_for_test,
        )
        self.assertEqual(volume3d.shape, self.np_volume_for_test.shape)

        with self.assertRaises(AssertionError):
            volume3d = Volume3D(
                np_volume=self.np_volume_for_test.reshape(
                    self.np_volume_for_test.shape + (1,)
                ),
                mm_resolution=self.mm_resolution_for_test,
            )


class TestVolumeLoader(unittest.TestCase):
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
            self.assertEqual(
                volume3d.mm_resolution,
                self.test_volume3d_instance.mm_resolution,
            )
            self.assertTrue(
                (
                    self.test_volume3d_instance.np_volume == volume3d.np_volume
                ).all()
            )


class TestVolumeSaver(unittest.TestCase):
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

    def test_volume_save_dtype(self):
        self.assertTrue(
            VolumeSaver(self.test_volume3d_instance).is_valid_volume_dtype()
        )

        self.test_volume3d_instance = self.test_volume3d_instance.astype(
            np.float64
        )
        with self.assertRaises(AssertionError):
            VolumeSaver(self.test_volume3d_instance)

    def test_volume_slice_generator(self):
        slice_images = list(
            VolumeSaver(self.test_volume3d_instance).slice_generator
        )

        self.assertEqual(
            self.test_volume3d_instance.shape[0], len(slice_images)
        )
        self.assertTrue(
            (
                self.test_volume3d_instance.np_volume == np.array(slice_images)
            ).all()
        )

    def test_volume_save_files_iterably(self):
        volume_saver = VolumeSaver(self.test_volume3d_instance)

        with TemporaryDirectory() as temporary_directory:
            for i, total in volume_saver.save_files_iterably(
                destination_directory=temporary_directory
            ):
                pass

            self.assertEqual(
                len(os.listdir(temporary_directory)),
                self.test_volume3d_instance.shape[0] + 1,
            )

            self.assertTrue(
                os.path.isfile(
                    Path(
                        temporary_directory, volume_saver.volume_info_file_name
                    )
                )
            )

    def test_save_volume_as_archive_iterably(self):
        volume_saver = VolumeSaver(self.test_volume3d_instance)

        with NamedTemporaryFile(suffix=".tar.gz") as temporary_file:
            for i, total in volume_saver.save_volume_as_archive_iterably(
                archive_path=temporary_file.name
            ):
                pass
            self.assertEqual(i + 1, total)

            self.assertTrue(os.path.isfile(temporary_file.name))


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
