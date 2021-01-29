import os, sys

if __name__ == '__main__':
    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from mod.Traits.__backbone__ import RootTraitBackbone, RSATraitBackbone
from mod.Traits.__test__ import ModuleTest
from DATA import RSA_Vector, ID_Object

#// an template for root trait measurements
#// create a class that inherits from RootTraitBackbone.
class Root_Template(RootTraitBackbone):
    built_in = False #// please use False only
    label = 'template' #// label name here
    tool_tip = 'Tips.' #// show this message when the mouse cursor hovers on the item
    sublabels = ['a', 'b'] #// if you store multiple items in csv, please provide as many sub-labels as you want
    index = 0 #// determines the order in which the labels are displayed
    version = 1 #// the version of RSAtrace3D for which this plugin was developed

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector, ID_string: ID_Object):
        """
        The RSA_vector contains RSA vector data. 
        The ID string is a unique string, with one ID for each node.
        Use these two arguments to compute the root trait and return the value.

        Usage:
        #// When ID_string indicates the root node
        if ID_string.is_root():
            #// getting the root node
            root_node = RSA_vector.root_node(ID_string=ID_string)
            
            ...

        #// voxel resolution can be obtained
        voxel_resolution = RSA_vector.annotations.resolution()

        See angle.py, category.py, id_string.py, length.py, and position.py for examples.
        """

        return ''

#// an template for RSA trait measurements
#// Create a class that inherits from RSATraitBackbone.
class RSA_Template(RSATraitBackbone):
    built_in = False #// please use False only
    label = 'length [cm]' #// label name here
    tool_tip = 'Tips.' #// Show this message when the mouse cursor hovers on the item
    sublabels = ['a', 'b'] #// If you store multiple items in csv, please provide as many sub-labels as you want
    index = 1 #// determines the order in which the labels are displayed
    version = 1 #// The version of RSAtrace3D for which this plugin was developed

    #// the main function
    def calculate(self, RSA_vector: RSA_Vector):
        """
        Usage:
        #All ID_string is obtained like this:
        for ID_string in RSA_vector.iter_all():
            ...

        #// So, if you are going to obtain all root nodes:
        for ID_string in RSA_vector.iter_all():
            if ID_string.is_root():
                root_node = RSA_vector.root_node(ID_string=ID_string)
                ...

        See angle.py, length.py, count.py, rdi.py, resolution.py, and volume_name.py for examples.
        """
        return ''

if __name__ == '__main__':
    #// Debugging of the calculation can be performed with the following command.
    ModuleTest(Root_Template)
    ModuleTest(RSA_Template)