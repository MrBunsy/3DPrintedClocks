from clocks import *


# from cq_warehouse.sprocket import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

diameter = 25
cord_thick = 1

heavy = BearingPulley(diameter, cord_diameter=cord_thick, bearing=get_bearing_info(4))
light = LightweightPulley(diameter, rope_diameter=cord_thick)

show_object(heavy.get_assembled())
show_object(light.get_assembled())