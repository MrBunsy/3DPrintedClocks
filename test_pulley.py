from clocks import *


# from cq_warehouse.sprocket import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

diameter = 40
cord_thick = 2

heavy = BearingPulley(diameter, cord_diameter=cord_thick, bearing=get_bearing_info(4), style=GearStyle.BENT_ARMS4)
light = LightweightPulley(diameter, rope_diameter=cord_thick)


# show_object(heavy.get_hook_half())
show_object(heavy.get_assembled())
# show_object(light.get_assembled())

print(heavy.get_BOM().to_json())
