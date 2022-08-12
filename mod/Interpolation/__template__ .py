from typing import List

from .__backbone__ import InterpolationBackbone


# // an template for interpolation
# // Create a class that inherits from InterpolationBackbone.
class Template(InterpolationBackbone):
    label = "Template"  # // label name here
    index = 1  # // determines the order in which the labels are displayed.
    version = 1  # // the version of RSAtrace3D

    # // the main function
    def interpolate(self, polyline: List[List[int]]):
        """
        The list of coordinates of the nodes (in the order z,x,y) is passed as an argument.
        Interpolate the lsit and return it.
        If you return it without modification, it will be a straight line.

        See straight.py, spline.py, and cog.py for examples.
        """

        return polyline
