from .__backbone__ import RSATraitBackbone
from DATA import RSA_Vector

#// [RSA] node count
class NodeCount(RSATraitBackbone):
    built_in = True
    label = 'node count'
    tool_tip = 'Total number of nodes that have a clicked coordinate.'
    index = -1
    version = 1

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector):
        return len(list(RSA_vector.iter_all()))

#// [RSA] root node count
class RootCount(RSATraitBackbone):
    built_in = False
    label = 'root number'
    tool_tip = 'Total number of root nodes.'
    index = 0
    version = 1

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector):
        return len([ID_string for ID_string in RSA_vector.iter_all() if ID_string.is_root()])