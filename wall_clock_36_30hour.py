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

from clocks import *

'''
Intended to be a potentially good clock for a child interested in clocks - simple with everything visible and cord driven

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_36"
clockOutDir="out"
gearStyle = GearStyle.HONEYCOMB_SMALL
pendulumFixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS


drop =1.5
lift =3
lock=1.5
escapement = AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, tooth_tip_angle=5, tooth_base_angle=4, anchor_thick=10, style=AnchorStyle.CURVED_MATCHING_WHEEL)
moduleReduction=1

#minute wheel ratio so we can use a pinion of 10 teeth to turn the standard motion works arbour and keep the cannon pinion rotating once an hour
train=GoingTrain(pendulum_period=1.5, fourth_wheel=False, escapement=escapement, max_weight_drop=1000, chain_at_back=False, powered_wheels=0, runtime_hours=30,
                 use_pulley=True, huygens_maintaining_power=False, escape_wheel_pinion_at_front=True)#, minuteWheelRatio=10/12)

train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=10, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction)

train.gen_cord_wheels(ratchet_thick=5, cord_thick=1, ratchet_diameter=20, cap_diameter=60)

pendulumSticksOut=25

module_sizes = None

train.gen_gears(module_size=1.25, module_reduction=moduleReduction, thick=2, powered_wheel_thick=3, style=gearStyle, pinion_thick_multiplier=3, powered_wheel_pinion_thick_multiplier=3,
                pendulum_fixing=pendulumFixing, module_sizes=module_sizes)
# train.printInfo(weight_kg=0.75-0.15)
train.print_info(weight_kg=0.32)

motionWorks = MotionWorks(extra_height=0, style=gearStyle, module=1, compensate_loose_arbour=False, compact=True, inset_at_base=MotionWorks.STANDARD_INSET_DEPTH)
motionWorks.calculate_size(30)


pendulum = Pendulum(hand_avoider_inner_d=90, bob_d=70, bob_thick=10)


dial_diameter = 140
dial = Dial(outside_d=dial_diameter, bottom_fixing=False, top_fixing=True)

plates = SimpleClockPlates(train, motionWorks, pendulum, plate_thick=7, pendulum_sticks_out=pendulumSticksOut, name="clock 36",
                           gear_train_layout=GearTrainLayout.VERTICAL, back_plate_from_wall=40, pendulum_fixing=pendulumFixing, pendulum_at_front=False, centred_second_hand=False, chain_through_pillar_required=True,
                           dial=dial, pillars_separate=True, escapement_on_front=True)
pulley_no_pipe = LightweightPulley(diameter=plates.get_diameter_for_pulley(), use_steel_rod=False)

hands = Hands(style=HandStyle.SIMPLE_ROUND, second_length=40, minute_fixing_d1=motionWorks.get_minute_hand_square_size(),
              hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=dial.outside_d / 2 - 10, thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False,
              second_hand_centred=False, second_fixing_d=get_diameter_for_die_cutting(3), outline_on_seconds=1, seconds_hand_thick=2.5)

assembly = Assembly(plates, hands=hands, time_seconds=15, pulley=pulley_no_pipe, pendulum=pendulum)

assembly.print_info()

weight = Weight(height=100, diameter=35)
weight.printInfo()

# bigweight = Weight(height=125, diameter=45)
# bigweight.printInfo()
# show_object(train.getArbourWithConventionalNaming(0).get_assembled())
# show_object(train.getArbourWithConventionalNaming(0).poweredWheel.get_assembled())

# show_object(assembly.getClock())
assembly.show_clock(show_object, dial_colours=[Colour.LIGHTGREY,Colour.BRASS],
                    motion_works_colours=[Colour.ORANGE,Colour.ORANGE,Colour.YELLOW,Colour.GREEN],
                    hand_colours=["white", "black", "red"],
                    plate_colours=Colour.DARKGREY)
# show_object(plates.arbors_for_plate[0].get_assembled())

# show_object(plates.get_assembled())
# show_object(dial.get_assembled())

if outputSTL:
    # train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    print("plates")
    plates.output_STLs(clockName, clockOutDir)
    print("after plates")
    hands.output_STLs(clockName, clockOutDir)
    weight.output_STLs(clockName, clockOutDir)
    # bigweight.output_STLs(clockName+"_big", clockOutDir)
    pulley_no_pipe.output_STLs(clockName + "_no_pipe", clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)
