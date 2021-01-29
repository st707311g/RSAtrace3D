#// a module of RSAtrace3D for showing root category

import os, sys

if __name__ == '__main__':
    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from mod.Traits.__backbone__ import RootTraitBackbone
from mod.Traits.__test__ import ModuleTest
from DATA import RSA_Vector, ID_Object

#// [single root] node category
class Root_Category(RootTraitBackbone):
    built_in = True
    label = 'category'
    tool_tip = 'Thee categories of nodes; base, root, or relay.'
    index = -2
    exportable = False
    updatable = False
    version = 1

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector, ID_string: ID_Object):
        if ID_string.is_base():
            return 'Base'
        if ID_string.is_root():
            return 'Root'
        if ID_string.is_relay():
            return 'Relay'

if __name__ == '__main__':
    ModuleTest(Root_Category)