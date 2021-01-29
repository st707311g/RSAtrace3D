#// a module of RSAtrace3D for showing ID_string 

import os, sys

if __name__ == '__main__':
    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from mod.Traits.__backbone__ import RootTraitBackbone
from mod.Traits.__test__ import ModuleTest
from DATA import RSA_Vector, ID_Object

#// [single root] ID string
class Root_ID_String(RootTraitBackbone):
    built_in = True
    label = 'ID string'
    tool_tip = 'An identifier given to each node.'
    index = -1
    exportable = False
    updatable = False
    version = 1

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector, ID_string: ID_Object):
        return ID_string

if __name__ == '__main__':
    ModuleTest(Root_ID_String)