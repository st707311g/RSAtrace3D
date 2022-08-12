# // a module of RSAtrace3D for showing resolution

import os
import sys

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from DATA import RSA_Vector
from mod.Traits.__backbone__ import RSATraitBackbone
from mod.Traits.__test__ import ModuleTest


# // [RSA] voxel resolution
class RSA_Resolution(RSATraitBackbone):
    built_in = True
    label = "resolution [mm/voxel]"
    tool_tip = "Voxel resolution"
    index = -2
    version = 1

    # // the main function
    def calculate(self, RSA_vector: RSA_Vector):
        return RSA_vector.annotations.resolution()


if __name__ == "__main__":
    ModuleTest(RSA_Resolution)
