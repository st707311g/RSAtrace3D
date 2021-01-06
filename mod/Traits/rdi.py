
from .__backbone__ import RSATraitBackbone
from DATA import RSA_Vector
from statistics import mean

#// [RDI] root distribution index
class RSA_RDI(RSATraitBackbone):
    built_in = True
    label = 'RDI [cm]'
    tool_tip = 'Root distribution index'
    index = 3
    version = 1

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector):
        if len(RSA_vector) == 0:
            return None

        polyline = []
        base_node = None
        for ID_string in RSA_vector.iter_all():
            if ID_string.is_base():
                base_node = RSA_vector.base_node(ID_string=ID_string)
            elif ID_string.is_root():
                root_node = RSA_vector.root_node(ID_string=ID_string)
                polyline.extend(root_node.completed_polyline())

        if base_node is None:
            return None

        z_offset = base_node['coordinate'][0] #// 1st: z, 2nd: y, 3rd: x
        resolution = RSA_vector.annotations.resolution() #// voxel resolution

        if len(polyline) == 0:
            return 0

        RDI = (mean([p[0] for p in polyline])-z_offset)*resolution/10
        return RDI

    #// text to be shown
    def str_value(self):
        if type(self.value) is float:
            return f'{self.value:.2f}'
        else:
            return super().str_value()