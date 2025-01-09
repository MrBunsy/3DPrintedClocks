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

import clocks as clock

'''
Copy of clock 20, but with a larger module size (might fix reliability issues) and 1/3s pendulum

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

#b was reprinting the escapement
#c is reprinting the dial (note, hard coded +1 to the dial support length as this has changed)
clockName="mantel_clock_27c"
clockOutDir="out"
gearStyle=clock.GearStyle.FLOWER
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

#for period 1.5
# drop =1.5
# lift =3
# lock=1.5
# escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, toothTipAngle=5, toothBaseAngle=4, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL)
# lift=4
# drop=2
# lock=2
# lift=3.5
# drop=2
# lock=1.75
#this much drop is needed to run reliably (I think it's the wiggle room from the m3 rods in 3mm bearings combined with a small escape wheel?) but a 0.25 nozzle is then needed to print well
lift=2
drop=3
lock=2
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=36, lock=lock, tooth_tip_angle=3,
                                    tooth_base_angle=3, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2)

train = clock.GoingTrain(pendulum_period=2/3, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, powered_wheels=2,
                         runtime_hours=7.5 * 24, support_second_hand=True, escape_wheel_pinion_at_front=True)

moduleReduction=0.9#0.85
#train.gen_spring_barrel(click_angle=-math.pi*0.25)
train.gen_spring_barrel(pawl_angle=-math.pi/4, click_angle=-math.pi*3/4, chain_wheel_ratios=[[66, 10], [76,13]])
# train.calculateRatios(max_wheel_teeth=120, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, moduleReduction=moduleReduction, loud=True,penultimate_wheel_min_ratio=0.75)
# train.calculateRatios(max_wheel_teeth=80, min_pinion_teeth=10, wheel_min_teeth=50, pinion_max_teeth=15, max_error=0.1, moduleReduction=moduleReduction, loud=True, allow_integer_ratio=False)
#1s
# train.setRatios( [[75, 9], [72, 10], [55, 33]])
#2/3s
train.set_ratios([[75, 9], [72, 10], [55, 22]])




pendulumSticksOut=10
backPlateFromWall=30

pinion_extensions = {1:12, 2:5}

train.gen_gears(module_size=1, module_reduction=moduleReduction, thick=2.4, thickness_reduction=0.9, powered_wheel_thick=6, pinion_thick_multiplier=3, style=gearStyle,
                powered_wheel_module_increase=1.25, powered_wheel_pinion_thick_multiplier=2, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True, pinion_extensions=pinion_extensions)
# train.print_info(weight_kg=1.5)
train.print_info(for_runtime_hours=24*7)
train.get_arbour_with_conventional_naming(0).print_screw_length()

#although I can make really compact motion works now for the dial to be close, this results in a key that looks too short, so extending just so the key might be more stable
motionWorks = clock.MotionWorks(extra_height=10, style=gearStyle, thick=3, compensate_loose_arbour=True, compact=True)#, inset_at_base=clock.MotionWorks.STANDARD_INSET_DEPTH)
#slightly larger allows for the inset and thus dial and hands closer to the plate
# motionWorks.calculateGears(arbourDistance=30)

pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=50, bob_thick=8)

#as printed
# dial = clock.Dial(outside_d=200, bottom_fixing=False, top_fixing=True,style=clock.DialStyle.ARABIC_NUMBERS, font="Arial", outer_edge_style=clock.DialStyle.RING, inner_edge_style=clock.DialStyle.LINES_ARC, seconds_style=clock.DialStyle.CONCENTRIC_CIRCLES)
#if I were to print again
dial = clock.Dial(outside_d=200, bottom_fixing=False, top_fixing=True,style=clock.DialStyle.ARABIC_NUMBERS, font="Gill Sans Medium", font_scale=0.9, font_path="../fonts/GillSans/Gill Sans Medium.otf", outer_edge_style=clock.DialStyle.RING, inner_edge_style=clock.DialStyle.LINES_ARC, seconds_style=clock.DialStyle.CONCENTRIC_CIRCLES)

# dial=None

plates = clock.MantelClockPlates(train, motionWorks, name="Mantel 27", dial=dial, plate_thick=6, screws_from_back=[[True, False],[False,False]])


# hands = clock.Hands(style=clock.HandStyle.SPADE, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
#                     length=plates.dial_diameter*0.45, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=plates.second_hand_mini_dial_d*0.45)
#would like sword, need to fix second hand outline for it
hands = clock.Hands(style=clock.HandStyle.SWORD, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=dial.outside_d*0.45, thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True,
                    second_length=dial.second_hand_mini_dial_d * 0.45, seconds_hand_thick=1.5, outline_on_seconds=1)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)


assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum)#weights=[clock.Weight(height=245,diameter=55)]

# show_object(plates.getPlate(back=True))
# show_object(assembly.getClock(with_key=False, with_pendulum=True))

# show_object(plates.get_plate())
# show_object(plates.get_fixing_screws_cutter())
#, clock.Colour.LIGHTBLUE, clock.Colour.GREEN
assembly.show_clock(show_object, hand_colours=[clock.Colour.WHITE, clock.Colour.BLACK], motion_works_colours=[clock.Colour.BRASS],
                    bob_colours=[clock.Colour.GOLD], with_rods=True, with_key=True, ratchet_colour=clock.Colour.BRASS, dial_colours=[clock.Colour.WHITE, clock.Colour.BLACK])

# show_object(plates.getDrillTemplate(6))

if outputSTL:
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)

