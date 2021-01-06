from .__backbone__ import RootTraitBackbone
from DATA import RSA_Vector, ID_Object

#// [single root] Clicked position
class Position(RootTraitBackbone):
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
        return '(x:{2}, y:{1}, z:{0})'.format(*self.value) if self.value is not None else ''