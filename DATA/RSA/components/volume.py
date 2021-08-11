
import logging

import numpy as np


class Volume(object):
    def __init__(self, parent):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.clear()

    def clear(self):
        self.data = None
        self.logger.debug(f'The volume data cleared.')

    def is_empty(self):
        return self.data is None

    def shape(self):
        if self.data is not None:
            return self.data.shape

    def init_from_volume(self, volume):
        self.data = volume
        self.logger.debug(f'The volume data initialized.')

    def get_trimed_volume(self, center, radius):
        if self.data is not None:
            S = radius*2+1
            pos = [int(i) for i in center]

            #// slices for cropping
            slices = []
            slice_indented = []
            for d in range(3):
                slices.append(slice(max(pos[d]-radius, 0), min(pos[d]+radius+1, self.data.shape[d])))
                indent = -min(pos[d]-radius, 0)
                slice_indented.append(slice(indent, slices[d].stop-slices[d].start+indent))

            cropped = np.zeros((S, S, S), dtype=np.uint8)
            cropped[tuple(slice_indented)] = self.data[tuple(slices)]

            return cropped



        