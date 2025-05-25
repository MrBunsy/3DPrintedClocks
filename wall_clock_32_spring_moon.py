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

from clocks import *

'''

This is based on mantel_clock_31, but bigger

Plan is a circular wall mounted clock with short pendulum and mini moon complication in a mini dial like the second hand 

clock works! few tweaks I think worth doing before making another:
 - change screwhole to be above the top bearing so we can adjust the beat setter more easily (it didn't exist when this was designed)
 - work out where to put a plaque on the back
 - optional plaque on front?

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "wall_clock_32.2_postrefactor"
clock_out_dir= "out"
gearStyle=GearStyle.CIRCLES
pendulumFixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

#after a huge amount of faffing about, the problem was the bearings, not the escapement. So I've used the new auto-calculated efficient escapement for a retrofit.
#was a drop of 2.75, but I think that was excessive
escapement = AnchorEscapement.get_with_optimal_pallets(teeth=30, drop_deg=2, wheel_thick=2.5)

train = GoingTrain(pendulum_period=1, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, powered_wheels=2,
                         runtime_hours=8 * 24, support_second_hand=False, escape_wheel_pinion_at_front=True)

barrel_gear_thick = 5#8

moduleReduction=0.95#0.85

#wall thick of 9 seemed fine, but I want it to be consistent with the arbor
#larger barrel wheel actually works out at a smaller plate than having a larger intermediate wheel
train.gen_spring_barrel(spring=SMITHS_EIGHT_DAY_MAINSPRING, pawl_angle=math.pi, click_angle=-math.pi/2, ratchet_at_back=True, style=gearStyle, base_thick=barrel_gear_thick,
                        wall_thick=10, chain_wheel_ratios=[[64, 10], [64, 10]], extra_barrel_height=1.5)
train.set_ratios([[65, 14], [60, 13], [56, 10]])

pendulumSticksOut=10
backPlateFromWall=30
dial_d = 205
dial_width=25

pinion_extensions = {0:1, 1:15, 2:10,3:18}

powered_modules = [WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5, leaves=train.chain_wheel_ratios[0][1]),
                    WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2)
                   ]
train.gen_gears(module_sizes=[1, 0.95, 0.95], module_reduction=moduleReduction, thick=3, thickness_reduction=0.85, style=gearStyle,
                powered_wheel_module_sizes=powered_modules, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True,
                pinion_extensions=pinion_extensions, lanterns=[0, 1], pinion_thick_extra=5, powered_wheel_pinion_thick_multiplier=1.875, powered_wheel_thicks=[barrel_gear_thick, 4])
train.print_info(for_runtime_hours=24*7)
moon_radius=13

moon_complication = MoonPhaseComplication3D(gear_style=gearStyle, first_gear_angle_deg=205, on_left=False, bevel_module=1.1, module=0.9, moon_radius=moon_radius,
                                                  bevel_angle_from_hands_deg=90, moon_from_hands=(dial_d/2 - dial_width) - moon_radius - 5, moon_inside_dial=True)
#no need to make inset, we've got lots of space here with the moon complication
motion_works = MotionWorks(extra_height=22, style=gearStyle, thick=3, compensate_loose_arbour=False, compact=True,
                                 moon_complication=moon_complication, cannon_pinion_to_hour_holder_gap_size=0.6)
# balance out the moon complication by making the motion works a bit bigger
motion_works.calculate_size(arbor_distance=30)
moon_complication.set_motion_works_sizes(motion_works)

pendulum = Pendulum(hand_avoider_inner_d=100, bob_d=60, bob_thick=12.5)

plaque = Plaque(text_lines=["W32#2 {:.1f}cm L.Wallin 2025".format(train.pendulum_length_m * 100), "Happy Birthday Mum"])


dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=DialStyle.DOTS, dial_width=dial_width, pillar_style=PillarStyle.BARLEY_TWIST)
plates = RoundClockPlates(train, motion_works, name="Wall Clock 32#2", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=20,
                                motion_works_angle_deg=180+45, leg_height=0, fully_round=True, style=PlateStyle.RAISED_EDGING, pillar_style=PillarStyle.BARLEY_TWIST,
                                moon_complication=moon_complication, second_hand=False, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=True)


hands = Hands(style=HandStyle.MOON, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=False,
                    outline_on_seconds=0, second_hand_centred=False)

assembly = Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, name="Wall Clock 32#2 (Moon) refactor")

assembly.get_arbor_rod_lengths()
plates.get_rod_lengths()

if not outputSTL:
    assembly.show_clock(show_object, hand_colours=[Colour.WHITE, Colour.DARKBLUE],
                        # motion_works_colours=[Colour.BLUE, Colour.ORANGE, Colour.BLUE],
                        motion_works_colours=[Colour.BLUE, Colour.LIGHTBLUE],
                        bob_colours=[Colour.SILVER], with_rods=True, with_key=True, ratchet_colour=Colour.PURPLE,
                        dial_colours=[Colour.BLUE, Colour.WHITE], key_colour=Colour.PURPLE,
                        plate_colours=[Colour.DARK_GREEN, Colour.BRASS, Colour.BRASS],
                        moon_complication_colours=[Colour.GREEN, Colour.YELLOW, Colour.RED, Colour.ORANGE])
                        # moon_complication_colours=[Colour.BLUE, Colour.ORANGE, Colour.BLUE, Colour.ORANGE])


if outputSTL:
    assembly.get_BOM().export(clock_out_dir)

