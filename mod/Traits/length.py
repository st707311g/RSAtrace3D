#// a module of RSAtrace3D for calculating root length

import os, sys

if __name__ == '__main__':
    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from mod.Traits.__backbone__ import RootTraitBackbone, RSATraitBackbone
from mod.Traits.__test__ import ModuleTest
from DATA import RSA_Vector, ID_Object
import math

#// [single root] root length
class Root_Length(RootTraitBackbone):
    built_in = True
    label = 'length [cm]'
    tool_tip = 'Root length of single root.'
    index = 0
    version = 1

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector, ID_string: ID_Object):
        if not ID_string.is_root():
            return ""

        resolution = RSA_vector.annotations.resolution() #// voxel resolution
        length = self.__calc_length(RSA_vector, ID_string, resolution)
        if length is not None:
            return round(length, 2)
        else:
            return ""

    #// text to be shown
    def str_value(self):
        #// displayed to the second decimal place
        if type(self.value) is float:
            return f'{self.value:5.1f}'
        else:
            return super().str_value()

    def __calc_distance(self, co1, co2):
        distance = math.sqrt(sum([(b-a)**2 for a,b in zip(co1, co2)]))
        return distance

    #// calculation of total root length
    def __calc_length(self, RSA_vector: RSA_Vector, ID_string: ID_Object, resolution: float):
        polyline = RSA_vector.root_node(ID_string=ID_string).interpolated_polyline()
        if len(polyline)==0:
            return None

        total_diff = 0
        for i in range(len(polyline)-1):
            total_diff += self.__calc_distance(polyline[i], polyline[i+1])

        return total_diff*resolution/10

#// [RSA] total root length
class RSA_TotalRootLength(RSATraitBackbone):
    built_in = False
    label = 'length [cm]'
    tool_tip = 'Total root length of single root.'
    index = 1
    version = 1

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector):
        root_length_list = []
        for ID_string in RSA_vector.iter_all(): #// For all ID_string
            if ID_string.is_root():
                root_length = Root_Length(RSA_vector, ID_string).value #// root length calculated
                root_length_list.append(root_length)
        return sum(root_length_list) #// return total

    #// text to be shown
    def str_value(self):
        #// displayed to the second decimal place
        if type(self.value) is float:
            return f'{self.value:5.1f}'
        else:
            return super().str_value()

if __name__ == '__main__':
    ModuleTest(Root_Length)
    ModuleTest(RSA_TotalRootLength)