from typing import List

import numpy as np

from .__backbone__ import InterpolationBackbone


#// interpolation by COG tracking
class COG_tracking(InterpolationBackbone):
    built_in = True
    label = 'COG tracking'
    status_tip = 'Interpolate nodes by center-of-gravity-based root tracking.'
    index = -1
    version = 1

    #// the main function
    def interpolate(self, polyline: List[List[int]]):
        self.window_size = 3
        self.unit_length = 4

        #// preparing
        self.func_get_subvolume = self.RSA_components().volume.get_trimed_volume #// a function returning a local subvolume
        polyline = np.array(polyline[::-1], dtype=np.float32)

        self.log = []
        for i in range(len(polyline)-1):
            start_pos = polyline[i]
            end_pos = polyline[i+1]

            self.log.append(start_pos.copy())

            self.velocity = None
            for _ in range(1000): #// 1000 iterations
                if self.is_terminated(start_pos, end_pos):
                    self.log.append(end_pos.copy())
                    break
                start_pos = self.move_particle(start_pos, end_pos)
                self.log.append(start_pos.copy())

        self.log = np.array(self.log, dtype=np.int)
        return self.log.tolist()

    def distance_between(self, aryA, aryB):
        return np.sqrt(np.square(aryB-aryA).sum())

    def is_terminated(self, start_pos, end_pos):
        return self.distance_between(start_pos, end_pos) < self.window_size*5

    def get_vector(self, from_, to_, prev_v):
        #// a root vector foward to the base node
        root_v = to_-from_ 
        #// the last vector
        prev_v = prev_v if prev_v is not None else root_v
        #// the root vector and the last vector are mixed to represent 'inertia'
        root_v = (root_v/np.linalg.norm(root_v)+prev_v/np.linalg.norm(prev_v))/2*self.unit_length 

        #//get a subvolume from where the root vector will move to
        subvol = self.func_get_subvolume(from_+root_v, self.window_size)
        if subvol is None:
            raise Exception

        #// COG calculation
        sum_ = np.sum(subvol)
        if sum_ == 0:
            cog_v = [0,0,0]
        else:
            cog_v = [np.sum(np.sum(indices*subvol, axis=axis)/np.sum(subvol)) for indices, axis in zip(np.indices(subvol.shape), [2, 1,0])]
            cog_v = np.array(cog_v)-self.window_size

        #// the root vector adjusted by the COG
        return root_v+cog_v

    def move_particle(self, start_pos, end_pos):
        self.velocity = self.get_vector(from_=start_pos, to_=end_pos, prev_v=self.velocity)
        return start_pos+self.velocity
