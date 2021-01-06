from .__backbone__ import RootTraitBackbone
from DATA import RSA_Vector, ID_Object

#// [single root] node category
class Category(RootTraitBackbone):
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