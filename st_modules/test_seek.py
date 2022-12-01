"""Functions for file and directory listing

Author:
    Shota Teramoto (st707311g@gmail.com)

Licence:
    NARO NON-COMMERCIAL LICENSE AGREEMENT Version 1.0

"""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from seek import walk_to_find_directories, walk_to_find_files


class TestSeek(unittest.TestCase):
    def setUp(self):
        self.temporary_directory_p = TemporaryDirectory()
        self.temporary_directory_path = Path(self.temporary_directory_p.name)

        # // making temporary directories and files
        self.num_of_test_directories = 10
        self.num_of_nested_test_directories = (
            self.num_of_test_directories**2 + self.num_of_test_directories
        )
        self.num_of_test_files = self.num_of_test_directories
        self.num_of_nested_test_files = (
            self.num_of_test_directories**2 + self.num_of_test_directories
        )
        self.test_file_extension = ".test"
        self.test_file_extension_negative = ".neg"
        for i in range(self.num_of_test_directories):
            dir_path = Path(self.temporary_directory_path, f"d{i:02}")
            os.makedirs(dir_path)
            Path(
                self.temporary_directory_path,
                f"f{i:02}{self.test_file_extension}",
            ).touch()
            for i in range(self.num_of_test_directories):
                os.makedirs(Path(dir_path, f"d{i:02}"))
                Path(dir_path, f"f{i:02}{self.test_file_extension}").touch()

    def tearDown(self) -> None:
        self.temporary_directory_p.cleanup()

    def test_seek_walk_to_find_directories(self):
        dir_list = list(
            walk_to_find_directories(path=self.temporary_directory_path)
        )
        self.assertEqual(len(dir_list), self.num_of_nested_test_directories)

        dir_list = list(
            walk_to_find_directories(
                path=self.temporary_directory_path, depth=1
            )
        )
        self.assertEqual(len(dir_list), self.num_of_test_directories)

        dir_list = list(
            walk_to_find_directories(
                path=self.temporary_directory_path,
                including_source_directoriy=True,
            )
        )
        self.assertEqual(
            len(dir_list), self.num_of_nested_test_directories + 1
        )

        dir_list = list(
            walk_to_find_directories(
                path=self.temporary_directory_path,
                depth=1,
                including_source_directoriy=True,
            )
        )
        self.assertEqual(len(dir_list), self.num_of_test_directories + 1)

    def test_seek_walk_to_find_files(self):
        # // test in nested directory
        file_list = list(
            walk_to_find_files(path=self.temporary_directory_path)
        )
        self.assertEqual(len(file_list), self.num_of_nested_test_files)

        # // test in not-nested directory
        file_list = list(
            walk_to_find_files(path=self.temporary_directory_path, depth=1)
        )
        self.assertEqual(len(file_list), self.num_of_test_files)

        # // test of extension filter positive
        file_list = list(
            walk_to_find_files(
                path=self.temporary_directory_path,
                extension_filter=self.test_file_extension,
            )
        )
        self.assertEqual(len(file_list), self.num_of_nested_test_files)

        # // test of extension filter negative
        file_list = list(
            walk_to_find_files(
                path=self.temporary_directory_path,
                extension_filter=self.test_file_extension_negative,
            )
        )
        self.assertEqual(len(file_list), 0)


if __name__ == "__main__":
    unittest.main()
