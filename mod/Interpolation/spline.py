from typing import List

import numpy as np
from scipy import interpolate

from .__backbone__ import InterpolationBackbone


# // spline interpolation
class Spline(InterpolationBackbone):
    built_in = True
    label = "Spline"
    status_tip = "Interpolate nodes to make a spline curve."
    index = -2
    version = 1

    # // the main function
    def interpolate(self, polyline: List[List[int]]):
        # // if node count <= 2
        if len(polyline) <= 2:
            return polyline

        # // spline interpolation
        co_lsit = list(zip(*polyline))
        tck, u = interpolate.splprep(
            [np.array(co_lsit[2]), np.array(co_lsit[1]), np.array(co_lsit[0])],
            s=2,
            k=2,
        )
        u_fine = np.linspace(0, 1, len(polyline) * 8)
        x_fine, y_fine, z_fine = interpolate.splev(u_fine, tck)

        # // return as List[List[int]] formatting
        return [
            [int(z), int(y), int(x)] for z, y, x in zip(z_fine, y_fine, x_fine)
        ]
