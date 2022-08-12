import os
import sys

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from DATA import RSA_Vector
from mod.Traits.__backbone__ import RSATraitBackbone
from mod.Traits.__test__ import ModuleTest


# // [RSA] volume name
class RSA_VolumeName(RSATraitBackbone):
    built_in = True
    label = "volume name"
    tool_tip = "Volume name"
    index = -3
    version = 1

    # // the main function
    def calculate(self, RSA_vector: RSA_Vector):
        return RSA_vector.annotations.volume_name()


if __name__ == "__main__":
    ModuleTest(RSA_VolumeName)
