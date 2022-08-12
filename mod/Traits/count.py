# // a module of RSAtrace3D for calculating root and node count

import os
import sys

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from DATA import RSA_Vector
from mod.Traits.__backbone__ import RSATraitBackbone
from mod.Traits.__test__ import ModuleTest


# // [RSA] node count
class RSA_NodeCount(RSATraitBackbone):
    built_in = True
    label = "node count"
    tool_tip = "Total number of nodes that have a clicked coordinate."
    index = -1
    version = 1

    # // the main function
    def calculate(self, RSA_vector: RSA_Vector):
        return len(list(RSA_vector.iter_all()))


# // [RSA] root node count
class RSA_RootCount(RSATraitBackbone):
    built_in = False
    label = "root number"
    tool_tip = "Total number of root nodes."
    index = 0
    version = 1

    # // the main function
    def calculate(self, RSA_vector: RSA_Vector):
        return len(
            [
                ID_string
                for ID_string in RSA_vector.iter_all()
                if ID_string.is_root()
            ]
        )


if __name__ == "__main__":
    ModuleTest(RSA_NodeCount)
    ModuleTest(RSA_RootCount)
