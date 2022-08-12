import os


class File(object):
    def __init__(self, volume_directory: str = ""):
        super().__init__()
        self.clear()
        if volume_directory != "":
            self.set(directory=volume_directory)

    def clear(self):
        self.directory = ""
        self.rinfo_file = ""

    def extensions(self):
        return (".cb", ".png", ".tif", ".tiff", ".jpg", ".jpeg")

    def set(self, directory: str):
        self.directory = directory
        self.rinfo_file = self.directory + ".rinfo"
        self.root_traits_file = self.directory + "_root_traits.csv"
        self.trace_directory = self.directory + "_trace"
        self.volume = os.path.basename(self.directory)

        self.img_files = [
            os.path.join(self.directory, f) for f in os.listdir(self.directory)
        ]
        ext_count = []
        for ext in self.extensions():
            ext_count.append(
                len([f for f in self.img_files if f.lower().endswith(ext)])
            )

        target_ext = self.extensions()[ext_count.index(max(ext_count))]

        self.img_files = [
            f for f in self.img_files if f.lower().endswith(target_ext)
        ]
        self.img_files.sort()

    def is_rinfo_file_available(self):
        return os.path.isfile(self.rinfo_file)

    def is_valid(self):
        return len(self.img_files) >= 64

    def __str__(self):
        return f"Number of image files: {len(self.img_files)}"


if __name__ == "__main__":
    pass
