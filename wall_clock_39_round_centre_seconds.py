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
import cadquery as cq
from cadquery import exporters
import os

import clocks as clock

'''

Inspired by the round moon clock (wall 32) and the recent success at retrofitting a better centred seconds hand to clocks 12 and 28.

This is an attempt to make a round wall clock with centred second hand. Idea is at first glance it looks like a boring quartz clock,
and only looking again do you realise it's a 3D printed mechanical clock

Spring barrel and powered wheel ratios from wall clock 32, but might take going train from mantel clock 29 (a previous centre seconds which has proven reliable)

TODO re-arrange gear train so that the second to last wheel is in the centre. Might need to move the spring barrel from the bottom?
'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_39"
clockOutDir="out"
gearStyle=clock.GearStyle.CIRCLES
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

#after a huge amount of faffing about, the problem was the bearings, not the escapement. So I've used the new auto-calculated efficient escapement for a retrofit.
escapement = clock.AnchorEscapement.get_with_45deg_pallets(teeth=30, drop_deg=2.75, lock_deg=1.5, wheel_thick=2.5)

barrel_gear_thick = 5
power = clock.SpringBarrel(spring=clock.SMITHS_EIGHT_DAY_MAINSPRING, pawl_angle=math.pi, click_angle=-math.pi/2, ratchet_at_back=True, style=gearStyle, base_thick=barrel_gear_thick,
                        wall_thick=10, extra_barrel_height=1.5)

# escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock,style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2.5, type=clock.EscapementType.DEADBEAT, tooth_tip_angle=6, tooth_base_angle=4)
train = clock.GoingTrain(pendulum_period=2/3, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, powered_wheels=2,
                         runtime_hours=8 * 24, support_second_hand=False, escape_wheel_pinion_at_front=True, powered_wheel=power)
#from wall clock 32
train.set_chain_wheel_ratio([[64, 10], [64, 10]])
#from mantel clock 29
train.set_ratios([[75, 9], [72, 10], [55, 22]])

moduleReduction=0.95

pendulumSticksOut=10
backPlateFromWall=30
dial_d = 205
dial_width=35

pinion_extensions = {0:1, 1:15, 2:10,3:18}

powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5, leaves=train.chain_wheel_ratios[0][1]),
                    # 1.2
                    clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2)
                   ]
train.gen_gears(module_sizes=[1, 0.95, 0.95], module_reduction=moduleReduction, thick=3, thickness_reduction=0.85, style=gearStyle,
                powered_wheel_module_sizes=powered_modules, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True,
                pinion_extensions=pinion_extensions, lanterns=[0, 1], pinion_thick_extra=5, powered_wheel_pinion_thick_multiplier=1.875, powered_wheel_thicks=[barrel_gear_thick, 4])
train.print_info(for_runtime_hours=24*7)

train.get_arbour_with_conventional_naming(0).print_screw_length()

motion_works = clock.MotionWorks(extra_height=0, style=gearStyle, thick=3, compensate_loose_arbour=False, compact=True,
                                 cannon_pinion_friction_ring=True, minute_hand_thick=2)

# motion_works.calculate_size(arbor_distance=30)

print("motion works widest r: ", motion_works.get_widest_radius())
pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=60, bob_thick=12.5)

plaque = clock.Plaque(text_lines=["W39#0 {:.1f}cm L.Wallin 2024".format(train.pendulum_length_m * 100), "github.com/MrBunsy/3DPrintedClocks"])

pillar_style=clock.PillarStyle.SIMPLE

dial = clock.Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=clock.DialStyle.LINES_INDUSTRIAL, dial_width=dial_width, pillar_style=pillar_style)

plates = clock.RoundClockPlates(train, motion_works, name="Wall Clock 39#0", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=20,
                                motion_works_angle_deg=180+45, leg_height=0, fully_round=True, style=clock.PlateStyle.RAISED_EDGING, pillar_style=pillar_style,
                                second_hand=True, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=True)

# print("plate radius: ", plates.radius)
hands = clock.Hands(style=clock.HandStyle.SIMPLE_ROUND, minute_fixing="circle", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=0, outline_same_as_body=False, second_hand_centred=True, chunky=True, outline_on_seconds=0,
                    second_length=dial.get_hand_length(clock.HandType.SECOND), second_fixing_thick=3)

assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum)

assembly.get_arbor_rod_lengths()
plates.get_rod_lengths()

if not outputSTL or True:
    # assembly.show_clock(show_object, hand_colours=[clock.Colour.WHITE, clock.Colour.DARKBLUE], motion_works_colours=[clock.Colour.BRASS],
    #                     bob_colours=[clock.Colour.SILVER], with_rods=True, with_key=True, ratchet_colour=clock.Colour.GOLD,
    #                     dial_colours=[clock.Colour.BLUE, clock.Colour.WHITE], key_colour=clock.Colour.DARKBLUE,
    #                     plate_colours=[clock.Colour.DARK_GREEN, clock.Colour.BLACK, clock.Colour.BRASS])
    assembly.show_clock(show_object, hand_colours=[clock.Colour.WHITE, clock.Colour.BLACK],
                        motion_works_colours=[clock.Colour.WHITE, clock.Colour.LIGHTBLUE, clock.Colour.GREEN],
                        bob_colours=[clock.Colour.SILVER], with_rods=True, with_key=True, ratchet_colour=clock.Colour.GOLD,
                        dial_colours=[clock.Colour.BLUE, clock.Colour.WHITE], key_colour=clock.Colour.DARKBLUE,
                        plate_colours=[clock.Colour.LIGHTGREY, clock.Colour.DARKGREY, clock.Colour.BLACK])

# show_object(plates.getDrillTemplate(6))

if outputSTL:
    plaque.output_STLs(clockName, clockOutDir)
    motion_works.output_STLs(clockName, clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)

