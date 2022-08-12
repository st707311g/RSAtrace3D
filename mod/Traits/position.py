# // a module of RSAtrace3D for showing node coordinate

import os
import sys

if __name__ == "__main__":
    sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from DATA import ID_Object, RSA_Vector
from mod.Traits.__backbone__ import RootTraitBackbone
from mod.Traits.__test__ import ModuleTest


# // [single root] Clicked position
class Root_Position(RootTraitBackbone):
    built_in = True
    label = "position"
    tool_tip = "Clicked coordinates of the node."
    index = 256
    exportable = False
    updatable = False
    version = 1

    # // the main function
    def calculate(self, RSA_vector: RSA_Vector, ID_string: ID_Object):
        node = RSA_vector[ID_string]
        if node is None:
            raise Exception
        return node["coordinate"]

    # // text to be shown
    def str_value(self):
        return (
            "(x:{2:3}, y:{1:3}, z:{0:3})".format(*self.value)
            if self.value is not None
            else ""
        )


if __name__ == "__main__":
    ModuleTest(Root_Position)
