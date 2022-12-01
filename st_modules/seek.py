"""Functions for file and directory listing

Author:
    Shota Teramoto (st707311g@gmail.com)

Licence:
    NARO NON-COMMERCIAL LICENSE AGREEMENT Version 1.0

"""

import math
import operator
import os
from pathlib import Path


def walk_to_find_directories(
    path: str, depth: int = math.inf, including_source_directoriy: bool = False
):
    """A function returning the generator generating the subdirectory paths.

    Args:
        path (str): Path to be explored.
        depth (int, optional): Depth of the maximum level to be explored. Defaults to unlimited.
        including_source_directoriy (bool, optional): Include the source directory in the resultd. Defaults to False.

    Yields:
        Path: directory path

    Examples:
        for directory_path in walk_to_find_directories(target_directory_path):
            print(directory_path)
    """
    if including_source_directoriy:
        yield Path(path)

    depth -= 1
    with os.scandir(path) as p:
        p = list(p)
        p.sort(key=operator.attrgetter("name"))
        for entry in p:
            if entry.is_dir():
                yield Path(entry.path)
            if entry.is_dir() and depth > 0:
                yield from walk_to_find_directories(entry.path, depth)


def walk_to_find_files(
    path: str, depth: int = math.inf, extension_filter: str = None
):
    """A function returning the generator generating the file paths.

    Args:
        path (str): Path to be explored.
        depth (int, optional): Depth of the maximum level to be explored. Defaults to unlimited.
        extension_filter (str, optional): Only results with extension listed in extension_filter will be returned. Defaults is no filtering.

    Yields:
        Path: file path.

    Examples:
        for file_path in walk_to_find_files(target_directory_path):
            print(file_path)
    """
    depth -= 1
    with os.scandir(path) as p:
        p = list(p)
        p.sort(key=operator.attrgetter("name"))
        for entry in list(p):
            if entry.is_file():
                if extension_filter is None:
                    yield Path(entry.path)
                else:
                    if entry.path.lower().endswith(extension_filter):
                        yield Path(entry.path)

            if entry.is_dir() and depth > 0:
                yield from walk_to_find_files(
                    entry.path, depth, extension_filter
                )
