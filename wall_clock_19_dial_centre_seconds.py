'''
Copyright Luke Wallin 2023

This source describes Open Hardware and is licensed under the CERN-OHL-S v2.

You may redistribute and modify this source and make products using it under
the terms of the CERN-OHL-S v2 or any later version (https://ohwr.org/cern_ohl_s_v2.txt).

This source is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY,
INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A
PARTICULAR PURPOSE. Please see the CERN-OHL-S v2 for applicable conditions.

Source location: https://github.com/MrBunsy/3DPrintedClocks

As per CERN-OHL-S v2 section 4, should you produce hardware based on this
source, You must where practicable maintain the Source Location visible
on the external case of the clock or other products you make using this
source.
'''
import math

import clocks.utility
from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.clock import *
from clocks.utility import *
from clocks.leaves import HollyLeaf, Wreath, HollySprig
from clocks.cosmetics import *
from clocks.dial import *

'''
Based on wall clock 07. Shortest pendulum that can provide a seconds hand. 30 hour runtime, but chain driven

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_19b"
clockOutDir="out"
gearStyle = GearStyle.HONEYCOMB_SMALL
pendulumFixing=PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS


drop =1.5
lift =3
lock=1.5
escapement = AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4, anchorThick=10)
moduleReduction=0.875

#minute wheel ratio so we can use a pinion of 10 teeth to turn the standard motion works arbour and keep the cannon pinion rotating once an hour
train=GoingTrain(pendulum_period=1.5, fourth_wheel=False, escapement=escapement, max_weight_drop=1200, chain_at_back=False, chain_wheels=0, runtime_hours=30,
                 use_pulley=True, huygens_maintaining_power=True, escape_wheel_pinion_at_front=True)#, minuteWheelRatio=10/12)

#lie about module reduction, we don't want smallest possible clock, we want a clock where the 2nd arbour isn't too close to the motion works arbour
train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, module_reduction=1)

# train.genCordWheels(ratchetThick=5, cordThick=1, cordCoilThick=11, style=gearStyle)
# 61 links/ft 1-day regula chain. copied from clock 04
train.gen_chain_wheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8, holeD=3)
# train.genRopeWheels(ratchetThick=4, ropeThick=2.2, use_steel_tube=False)

pendulumSticksOut=25
# was attemptign to get the second arbour to line up with where I want the arbour for the motion works - but I think this is actually impossible
# to do without the gears overlapping
# ratio_of_teeth = sum(train.trains[0]["train"][0]) / sum(train.trains[0]["train"][1])
#
# first_module_size = 1.25
#
# module_sizes = [first_module_size, first_module_size * ratio_of_teeth]
module_sizes = None

train.gen_gears(module_size=1.25, module_reduction=moduleReduction, thick=2, chain_wheel_thick=3, useNyloc=False, style=gearStyle, pinion_thick_multiplier=3, chain_wheel_pinion_thick_multiplier=3,
                pendulum_fixing=pendulumFixing, module_sizes=module_sizes)
# train.printInfo(weight_kg=0.75-0.15)
train.print_info(weight_kg=0.32)

#reprinting these after the work to reduce module size back to 1, hoping it removes the jam problem
motionWorks = MotionWorks(extra_height=20, style=gearStyle, bearing=get_bearing_info(3), module=1, compensate_loose_arbour=False, compact=True, thick=1.8, pinion_thick=8)

pendulum = Pendulum(hand_avoider_inner_d=90, bob_d=70, bob_thick=10)


dial_diameter = 175
dial = Dial(outside_d=dial_diameter, bottom_fixing=False, top_fixing=True)

plates = SimpleClockPlates(train, motionWorks, pendulum, plate_thick=7, pendulum_sticks_out=pendulumSticksOut, name="clock 19",
                           style=ClockPlateStyle.VERTICAL, back_plate_from_wall=40, pendulum_fixing=pendulumFixing, pendulum_at_front=False, centred_second_hand=True, chain_through_pillar_required=True,
                           dial=dial, pillars_separate=True)
pulley_no_pipe = LightweightPulley(diameter=plates.get_diameter_for_pulley(), use_steel_rod=False)

hands = Hands(style=HandStyle.SIMPLE_ROUND, second_length=40, minute_fixing="circle", minute_fixing_d1=motionWorks.get_minute_hand_square_size(),
              hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=dial.outside_d / 2 - 10, thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False,
              second_hand_centred=True, second_fixing_d=get_diameter_for_die_cutting(3), outline_on_seconds=1, seconds_hand_thick=2.5)

assembly = Assembly(plates, hands=hands, timeSeconds=15, pulley=pulley_no_pipe)

assembly.printInfo()

weight = Weight(height=100, diameter=35)
weight.printInfo()

# bigweight = Weight(height=125, diameter=45)
# bigweight.printInfo()
# show_object(train.getArbourWithConventionalNaming(0).get_assembled())
# show_object(train.getArbourWithConventionalNaming(0).poweredWheel.get_assembled())

# show_object(assembly.getClock())
assembly.show_clock(show_object, dial_colours=[clocks.utility.Colour.LIGHTGREY,clocks.utility.Colour.BRASS],
                    motion_works_colours=[clocks.utility.Colour.ORANGE,clocks.utility.Colour.ORANGE,clocks.utility.Colour.YELLOW,clocks.utility.Colour.GREEN],
                    hand_colours=["white", "black", "red"],
                    plate_colour=clocks.utility.Colour.DARKGREY)


if outputSTL:
    train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    weight.output_STLs(clockName, clockOutDir)
    # bigweight.output_STLs(clockName+"_big", clockOutDir)
    pulley_no_pipe.output_STLs(clockName + "_no_pipe", clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)
