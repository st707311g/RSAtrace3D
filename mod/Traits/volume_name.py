from .__backbone__ import RSATraitBackbone
from DATA import RSA_Vector

#// [RSA] volume name
class VolumeName(RSATraitBackbone):
    built_in = True
    label = 'volume name'
    tool_tip = 'Volume name'
    index = -3
    version = 1

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector):
        return RSA_vector.annotations.volume_name()