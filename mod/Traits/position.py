#// a module of RSAtrace3D for showing node coordinate

import os, sys

if __name__ == '__main__':
    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from mod.Traits.__backbone__ import RootTraitBackbone
from mod.Traits.__test__ import ModuleTest
from DATA import RSA_Vector, ID_Object

#// [single root] Clicked position
class Root_Position(RootTraitBackbone):
    built_in = True
    label = 'position'
    tool_tip = 'Clicked coordinates of the node.'
    index = 256
    exportable = False
    updatable = False
    version = 1

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector, ID_string: ID_Object):
        return RSA_vector[ID_string]['coordinate']

    #// text to be shown
    def str_value(self):
        return '(x:{2:3}, y:{1:3}, z:{0:3})'.format(*self.value) if self.value is not None else ''

if __name__ == '__main__':
    ModuleTest(Root_Position)