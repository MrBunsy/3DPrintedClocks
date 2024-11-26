from clocks import *


# from cq_warehouse.sprocket import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


key = WindingKey(key_containing_diameter=12,cylinder_length=50,key_hole_deep=20,key_sides=6,handle_length=40, crank=False, print_sideways=True)
# #
# show_object(key.get_let_down_adapter())
show_object(key.get_assembled())
show_object(key.get_key(for_printing=False))
