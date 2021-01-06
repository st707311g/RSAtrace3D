
from .__backbone__ import RootTraitBackbone
from DATA import RSA_Vector, ID_Object

#// [single root] ID string
class ID_string(RootTraitBackbone):
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