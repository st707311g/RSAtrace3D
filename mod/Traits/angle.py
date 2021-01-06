from .__backbone__ import RootTraitBackbone, RSATraitBackbone
from DATA import RSA_Vector, ID_Object

from statistics import mean, stdev
import math

#// [single root] root angle calculation
class Root_Angle(RootTraitBackbone):
    built_in = True
    label = 'angle [\u00B0]'
    tool_tip = 'The angle from the base node to the terminal node.'
    index = 1
    version = 1

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector, ID_string: ID_Object):
        #// only root nodes to be processed
        if not ID_string.is_root():
            return ""

        #// interpolated polyline obtained
        polyline = RSA_vector.root_node(ID_string=ID_string).interpolated_polyline()
        if len(polyline)==0:
            return ""

        #// angle calculated
        angle = self.__calc_angle(polyline[0], polyline[-1])
        return angle

    #// text to be shown
    def str_value(self):
        #// displayed to the second decimal place
        if type(self.value) is float:
            return f'{self.value:.2f}'
        else:
            return super().str_value()

    #// angle calculation
    #// The angle between the first and last node against the horizontal plane are calculated.
    def __calc_angle(self, co1, co2):
        z1, y1, x1 = co1
        z2, y2, x2 = co2

        y = abs(z2-z1)
        x = math.sqrt((x2-x1)**2+(y2-y1)**2)
        angle = math.degrees(math.atan2(y,x))
        return angle

#// [RSA] root angle calculation
class RSA_RootAngle(RSATraitBackbone):
    built_in = False
    label = 'angle [\u00B0]'
    tool_tip = 'The average angle from the base node to the terminal node.'
    sublabels = ['mean', 'sd'] #// two parameters to be calculated
    index = 2
    version = 1

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector):
        root_angle_list = []
        for ID_string in RSA_vector.iter_all():
            root_angle = Root_Angle(RSA_vector, ID_string).value
            if type(root_angle) is float:
                root_angle_list.append(root_angle)

        if len(root_angle_list) == 0:
            return [None, None]

        ret = []
        ret.append(mean(root_angle_list))

        if len(root_angle_list) >= 3:
            ret.append(stdev(root_angle_list))
        else:
            ret.append(None)
        
        return ret

    #// text to be shown
    def str_value(self):
        #// without mean value
        if self.value[0] is None:
            return ''
        #// with only mean value, without standard deviation value
        elif self.value[1] is None:
            return f'{self.value[0]:.2f}'
        #// with both
        else:
            return f'{self.value[0]:.2f} ± {self.value[1]:.2f}'