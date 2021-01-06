from .__backbone__ import RSATraitBackbone
from DATA import RSA_Vector

#// [RSA] voxel resolution
class Resolution(RSATraitBackbone):
    built_in = True
    label = 'resolution [mm/voxel]'
    tool_tip = 'Voxel resolution'
    index = -2
    version = 1

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector):
        return RSA_vector.annotations.resolution()