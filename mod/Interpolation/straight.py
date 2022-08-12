from typing import List

from .__backbone__ import InterpolationBackbone


# // straight
class Straight(InterpolationBackbone):
    built_in = True
    label = "Straight"
    status_tip = "No interpolation, straight polylines."

    # // the main function
    def interpolate(self, polyline: List[List[int]]):
        # // no interpolation, just return it
        return polyline
