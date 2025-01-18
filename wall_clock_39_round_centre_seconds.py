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

clock_name= "wall_clock_39"
clock_out_dir= "out"
gear_style=clock.GearStyle.DIAMONDS
pillar_style=clock.PillarStyle.TWISTY

#use this to get best lift
escapement = clock.AnchorEscapement.get_with_optimal_pallets(60, drop_deg=1.75, diameter=60, anchor_teeth=9.5)
#but we want to reconfigure the diameter and tooth size
big_escapement = clock.AnchorEscapement(60, diameter=132, drop=escapement.drop_deg, lift=escapement.lift_deg, anchor_teeth=9.5, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, tooth_height_fraction=0.1,
                                  tooth_tip_angle=5/2, tooth_base_angle=4/2, force_diameter=True)
powered_wheel = clock.CordWheel(diameter=26, ratchet_thick=6, rod_metric_size=4, screw_thread_metric=3, cord_thick=1, thick=15, style=gear_style, use_key=True,
                                loose_on_rod=False, traditional_ratchet=True, power_clockwise=False, use_steel_tube=False)
train = clock.GoingTrain(pendulum_period=1.0, wheels=3, escapement=big_escapement, max_weight_drop=1000, use_pulley=True, chain_at_back=False, powered_wheels=1,
                         runtime_hours=7.5 * 24, support_second_hand=False, escape_wheel_pinion_at_front=True, powered_wheel=powered_wheel)
train.calculate_ratios(min_pinion_teeth=9, loud=True, max_error=0.001, max_wheel_teeth=80)
train.calculate_powered_wheel_ratios()
dial_d = 175

pinion_extensions={1:18, 3:10}

powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1, leaves=train.chain_wheel_ratios[0][1])]
train.gen_gears(module_sizes=[0.9, 0.8, 0.8], thick=3, thickness_reduction=2 / 2.4, powered_wheel_thick=4.5, pinion_thick_multiplier=3, style=gear_style,
                powered_wheel_module_sizes=powered_modules, powered_wheel_pinion_thick_multiplier=2, pendulum_fixing=clock.PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS, lanterns=[0],
                pinion_extensions=pinion_extensions, stack_away_from_powered_wheel=False, escapement_split=True)
train.print_info(weight_kg=2.0)

motion_works = clock.MotionWorks(extra_height=10, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True,
                                 cannon_pinion_friction_ring=True, minute_hand_thick=2, bearing=clock.get_bearing_info(3))


pendulum = clock.Pendulum(bob_d=60, bob_thick=10)

plaque = clock.Plaque(text_lines=["W39#0 {:.1f}cm L.Wallin 2024".format(train.pendulum_length_m * 100), "github.com/MrBunsy/3DPrintedClocks"])

dial = clock.Dial(dial_d, clock.DialStyle.FANCY_WATCH_NUMBERS, font="Eurostile Extended #2", font_scale=1.5, font_path="../fonts/Eurostile_Extended_2_Bold.otf",
                  outer_edge_style=clock.DialStyle.LINES_ARC, inner_edge_style=None, dial_width=dial_d/6, seconds_style=clock.DialStyle.CONCENTRIC_CIRCLES,
                  bottom_fixing=False, top_fixing=False, pillar_style=pillar_style, raised_detail=True)

plates = clock.RoundClockPlates(train, motion_works, name="Wall Clock 39#0", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=25,
                                motion_works_angle_deg=45, leg_height=0, fully_round=True, style=clock.PlateStyle.SIMPLE, pillar_style=pillar_style,
                                second_hand=True, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=False, centred_second_hand=True, escapement_on_back=True)

hands = clock.Hands(style=clock.HandStyle.FANCY_WATCH, minute_fixing="circle", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=0, outline_same_as_body=False, second_hand_centred=True, chunky=True, outline_on_seconds=0,
                    second_length=dial.get_hand_length(clock.HandType.SECOND), second_fixing_thick=3, include_seconds_hand=True)

pulley = clock.LightweightPulley(diameter=train.powered_wheel.diameter+powered_wheel.cord_thick*2, rope_diameter=2, use_steel_rod=False)

# show_object(plates.get_cannon_pinion_friction_clip(for_printing=False))


assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, name="Wall Clock 39", pulley=pulley)

if outputSTL:
    assembly.get_BOM().export(clock_out_dir)
else:
    assembly.show_clock(show_object, hand_colours=[clock.Colour.WHITE, clock.Colour.BRASS],
                        motion_works_colours=[clock.Colour.WHITE, clock.Colour.BRASS, clock.Colour.BRASS, clock.Colour.BRASS],
                        bob_colours=[clock.Colour.BLUE], with_rods=True, with_key=True, ratchet_colour=clock.Colour.GOLD,
                        dial_colours=[clock.Colour.BLACK, clock.Colour.WHITE], key_colour=clock.Colour.DARKBLUE,
                        plate_colours=[clock.Colour.LIGHTGREY, clock.Colour.DARKGREY, clock.Colour.BLACK],
                        hand_colours_overrides={"black":clock.Colour.DARKGREY})




