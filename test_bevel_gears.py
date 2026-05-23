from clocks import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


bevel_pair = WheelPinionBeveledPair(18, 13)


# show_object(bevel_pair.pinion)
# show_object(bevel_pair.wheel)
show_object(bevel_pair.get_assembled())
# show_object(bevel_pair.get_pinion_with_tooth_at(0))