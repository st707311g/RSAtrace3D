import os
from pathlib import Path

from st_modules.volume import VolumeLoader


class File(object):
    def __init__(self, volume_path: str = ""):
        super().__init__()
        self.clear()
        if volume_path != "":
            self.set(volume_path=volume_path)

    def clear(self):
        self.volume_path = Path("")
        self.rinfo_file = Path("")

    def extensions(self):
        return (".cb", ".png", ".tif", ".tiff", ".jpg", ".jpeg")

    def set(self, volume_path: str):
        self.volume_path = Path(volume_path).resolve()
        if self.volume_path.is_dir():
            self.volume_stem = self.volume_path
        else:
            self.volume_stem = Path(
                self.volume_path.parent,
                self.volume_path.name[: self.volume_path.name.index(".")],
            )
        self.rinfo_file = Path(str(self.volume_stem) + ".rinfo")
        self.root_traits_file = Path(
            str(self.volume_stem) + "_root_traits.csv"
        )
        self.trace_directory = Path(str(self.volume_stem) + "_trace")
        self.volume_name = self.volume_stem.name

    def is_rinfo_file_available(self):
        return os.path.isfile(self.rinfo_file)

    def is_valid(self):
        return len(self.img_files) >= 64

    def __str__(self):
        return f"Number of image files: {len(self.img_files)}"


if __name__ == "__main__":
    pass

    a = Path("/media/teramotos154/no3/wrc/wrc_control/14das/001.tar.gz")
    str(Path(a.parent, a.name[: a.name.index(".")]))
