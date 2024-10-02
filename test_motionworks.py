from clocks import *
from clocks.cq_gears import SpurGear
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

# spur_gear = SpurGear(module=1.0, teeth_number=19, width=5.0, bore_d=5.0)


motionWorks = MotionWorks(extra_height=10, style=GearStyle.DIAMONDS, thick=3, compensate_loose_arbour=False, compact=True, module=1.5,
                          bearing=get_bearing_info(3),
                                minute_hand_thick=2, cannon_pinion_friction_ring=True, lone_pinion_inset_at_base=1, reduced_jamming=True)
motionWorks.calculate_size(42.01250000000002)


show_object(motionWorks.get_assembled())

#With a weight of 2.5kg, this results in an average power usage of 47.1uW