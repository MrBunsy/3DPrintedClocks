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

Based on wall 32 but having another go at a spring brocot

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_35"
clockOutDir="out"
gearStyle=clock.GearStyle.CURVES
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

lift=3
drop=3
lock=2

# escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock,style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2.5, type=clock.EscapementType.BROCOT, tooth_tip_angle=6, tooth_base_angle=4)
escapement = clock.BrocotEscapment(drop=drop, lift=lift, teeth=30, lock=lock, diameter=45)
train = clock.GoingTrain(pendulum_period=2, wheels=3, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, chain_wheels=2,
                         runtime_hours=8 * 24, support_second_hand=False, escape_wheel_pinion_at_front=True)

barrel_gear_thick = 5

moduleReduction=1

#wall thick of 9 seemed fine, but I want it to be consistent with the arbor
#larger barrel wheel actually works out at a smaller plate than having a larger intermediate wheel
train.gen_spring_barrel(spring=clock.SMITHS_EIGHT_DAY_MAINSPRING, pawl_angle=math.pi, click_angle=-math.pi/2, ratchet_at_back=True, style=gearStyle, base_thick=barrel_gear_thick,
                        wall_thick=10, chain_wheel_ratios=[[64, 10], [64, 10]], extra_barrel_height=1.5)

'''
[[61, 10], [83, 10]]
spring_wound_coils: 23.53661753519562 spring unwound coils: 12.838105212872968, max theoretical barrel turns: 10.698512322322653
Over a runtime of 168.0hours the spring barrel will make 3.3 full rotations which is 31.0% of the maximum number of turns (10.7) and will take 5.0 key turns to wind back up
'''

train.calculate_ratios(max_wheel_teeth=150, min_pinion_teeth=8, wheel_min_teeth=55, pinion_max_teeth=12, max_error=0.1, module_reduction=moduleReduction, loud=True)
#1s period with 36 teeth
# train.set_ratios([[65, 12], [60, 14], [56, 13]])
#1s period with 30 teeth
#[[65, 10], [60, 14], [56, 13]]
# train.set_ratios([[65, 14], [60, 13], [56, 10]])

pendulumSticksOut=10
backPlateFromWall=30
dial_d = 205
dial_width=25
pillar_style=clock.PillarStyle.CLASSIC

pinion_extensions = None#{0:1, 1:15, 2:10,3:18}

#powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)]
powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5, leaves=train.chain_wheel_ratios[0][1]),
                    # 1.2
                    clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2)
                   ]
#[1.6, 1.25]
#endshake is 1.5 by default for mantel plates, so double and some more that for pinion extra length
#module_sizes=[1, 0.95, 0.95]
train.gen_gears(module_sizes=[0.8, 0.8], module_reduction=moduleReduction, thick=3, thickness_reduction=0.85, style=gearStyle,
                powered_wheel_module_sizes=powered_modules, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True,
                pinion_extensions=pinion_extensions, lanterns=[0, 1], pinion_thick_extra=5, powered_wheel_pinion_thick_multiplier=1.875, powered_wheel_thicks=[barrel_gear_thick, 4])
train.print_info(for_runtime_hours=24*7)

train.get_arbour_with_conventional_naming(0).print_screw_length()

#no need to make inset, we've got lots of space here with the moon complication
motion_works = clock.MotionWorks(extra_height=22, style=gearStyle, thick=3, compensate_loose_arbour=False, compact=True, cannon_pinion_to_hour_holder_gap_size=0.6)
# balance out the moon complication by making the motion works a bit bigger
motion_works.calculate_size(arbor_distance=30)

print("motion works widest r: ", motion_works.get_widest_radius())
pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=60, bob_thick=12.5)

plaque = clock.Plaque(text_lines=["W35#0 {:.1f}cm L.Wallin 2024".format(train.pendulum_length_m * 100), "Brocot Again Yay"])


# dial = clock.Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, romain_numerals_style=clock.RomanNumeralStyle.SIMPLE_SQUARE, style=clock.DialStyle.ROMAN_NUMERALS,
#                    inner_edge_style=clock.DialStyle.RING, outer_edge_style=clock.DialStyle.LINES_ARC,
#                    dial_width=dial_width, pillar_style=pillar_style)
# dial = clock.Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=clock.DialStyle.DOTS, dial_width=dial_width, pillar_style=clock.PillarStyle.BARLEY_TWIST)
dial = None
plates = clock.RoundClockPlates(train, motion_works, name="Wall 35", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=20,
                                motion_works_angle_deg=180+45, leg_height=0, fully_round=True, style=clock.PlateStyle.RAISED_EDGING, pillar_style=pillar_style,
                                second_hand=False, standoff_pillars_separate=True, plaque=plaque, escapement_on_front=True)

print("plate radius: ", plates.radius)
# dial.get_hand_length()
hands = clock.Hands(style=clock.HandStyle.BREGUET, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=100, thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=False,
                    outline_on_seconds=0, second_hand_centred=False)

assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum)#weights=[clock.Weight(height=245,diameter=55)]

assembly.get_arbor_rod_lengths()
plates.get_rod_lengths()

if not outputSTL or True:
    assembly.show_clock(show_object, hand_colours=[clock.Colour.WHITE, clock.Colour.BLACK], motion_works_colours=[clock.Colour.BRASS],
                        bob_colours=[clock.Colour.SILVER], with_rods=True, with_key=True, ratchet_colour=clock.Colour.GOLD,
                        dial_colours=[clock.Colour.WHITE, clock.Colour.BLACK], key_colour=clock.Colour.DARKBLUE,
                        plate_colours=[clock.Colour.DARK_GREEN, clock.Colour.BRASS, clock.Colour.BRASS])

# show_object(plates.getDrillTemplate(6))

if outputSTL:

    motion_works.output_STLs(clockName, clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)

