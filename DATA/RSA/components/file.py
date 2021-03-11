import os

class File(object):
    def __init__(self, volume_directory: str=''):
        super().__init__()
        self.clear()
        if volume_directory != '':
            self.set(directory=volume_directory)

    def clear(self):
        self.rinfo_file = ''

    def set(self, directory: str):
        self.directory = directory
        self.rinfo_file = self.directory+'.rinfo'
        self.root_traits_file = self.directory+'_root_traits.csv'
        self.trace_directory = self.directory+'_trace'
        self.volume = os.path.basename(self.directory)

        self.img_files = [os.path.join(self.directory, f) for f in os.listdir(self.directory)]
        self.img_files = [f for f in self.img_files if os.path.isfile(f) and f.lower().endswith(('.png', '.tif', '.tiff', '.jpg', '.jpeg'))]
        self.img_files.sort()

    def is_rinfo_file_available(self):
        return os.path.isfile(self.rinfo_file)

    def is_valid(self):
        return len(self.img_files) >= 64