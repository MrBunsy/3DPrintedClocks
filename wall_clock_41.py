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
Same as 39, but chain driven and different style
'''
outputSTL = False

if 'show_object' not in globals():
    # don't output STL when we're in cadquery editor
    outputSTL = True


    def show_object(*args, **kwargs):
        pass

clock_name = "wall_clock_41"
clock_out_dir = "out"
gear_style = GearStyle.ROUNDED_ARMS5
pillar_style = PillarStyle.CLASSIC

chain = True

# use this to get best lift
escapement = AnchorEscapement.get_with_optimal_pallets(60, drop_deg=1.75, diameter=60, anchor_teeth=9.5)
# but we want to reconfigure the diameter and tooth size
big_escapement = AnchorEscapement(60, diameter=132, drop=escapement.drop_deg, lift=escapement.lift_deg, anchor_teeth=9.5, style=AnchorStyle.CURVED_MATCHING_WHEEL, tooth_height_fraction=0.1,
                                       tooth_tip_angle=5 / 2, tooth_base_angle=4 / 2, force_diameter=True, wheel_thick=2)

powered_wheel = PocketChainWheel2(ratchet_thick=6, chain=COUSINS_1_5MM_CHAIN, max_diameter=25)

max_weight_drop = 1400

train = GoingTrain(pendulum_period=1.0, wheels=3, escapement=big_escapement, max_weight_drop=max_weight_drop, use_pulley=not chain, chain_at_back=False, powered_wheels=1,
                         runtime_hours=7.5 * 24, support_second_hand=False, escape_wheel_pinion_at_front=True, powered_wheel=powered_wheel)
train.calculate_ratios(min_pinion_teeth=9, loud=True, max_error=0.001, max_wheel_teeth=80)
train.calculate_powered_wheel_ratios()
dial_d = 180


pinion_extensions = {1: 14}

powered_modules = [WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1, leaves=train.chain_wheel_ratios[0][1])]
train.gen_gears(module_sizes=[0.9, 0.8, 0.8], thick=3, thickness_reduction=2 / 2.4, powered_wheel_thick=4.5, pinion_thick_multiplier=3, style=gear_style,
                powered_wheel_module_sizes=powered_modules, powered_wheel_pinion_thick_multiplier=2, pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS, lanterns=[0],
                pinion_extensions=pinion_extensions, stack_away_from_powered_wheel=False, escapement_split=True)
train.print_info(weight_kg=2.0)

motion_works = MotionWorks(extra_height=10, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True,
                                 cannon_pinion_friction_ring=True, minute_hand_thick=2, bearing=get_bearing_info(3), reduced_jamming=True)

pendulum = Pendulum(bob_d=60, bob_thick=10)

plaque = Plaque(text_lines=["W41#0 {:.1f}cm L.Wallin 2024".format(train.pendulum_length_m * 100), "github.com/MrBunsy/3DPrintedClocks"])


# dial = Dial(dial_d, DialStyle.ROMAN_NUMERALS, romain_numerals_style=RomanNumeralStyle.SIMPLE_ROUNDED, outer_edge_style=DialStyle.CONCENTRIC_CIRCLES,
#                   inner_edge_style=None, dial_width=dial_d / 6, bottom_fixing=False, top_fixing=False, pillar_style=pillar_style, raised_detail=True)
dial = Dial(dial_d, DialStyle.FANCY_WATCH_NUMBERS, font="Eurostile Extended #2", font_scale=1.5, font_path="../fonts/Eurostile_Extended_2_Bold.otf",
                  outer_edge_style=DialStyle.LINES_ARC, inner_edge_style=None, dial_width=dial_d/6, seconds_style=DialStyle.CONCENTRIC_CIRCLES,
                  bottom_fixing=False, top_fixing=False, pillar_style=pillar_style, raised_detail=True)

plates = RoundClockPlates(train, motion_works, name="Wall Clock 41#0", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=25,
                                motion_works_angle_deg=45, leg_height=0, fully_round=True, style=PlateStyle.RAISED_EDGING, pillar_style=pillar_style,
                                second_hand=True, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=False, centred_second_hand=True, escapement_on_back=True)


# hands = Hands(style=HandStyle.SIMPLE_POINTED, minute_fixing="circle", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
#                     length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, second_hand_centred=True, chunky=True, outline_on_seconds=0,
#                     second_length=dial.get_hand_length(HandType.SECOND), second_fixing_thick=3, include_seconds_hand=True, second_style_override=HandStyle.SIMPLE_ROUND, hour_style_override=HandStyle.SPADE)
# hands = Hands(style=HandStyle.SIMPLE_POINTED, minute_fixing="circle", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
#                     length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, second_hand_centred=True, chunky=True, outline_on_seconds=0,
#                     second_length=dial.get_hand_length(HandType.SECOND), second_fixing_thick=3, include_seconds_hand=True, second_style_override=HandStyle.SIMPLE_ROUND, hour_style_override=HandStyle.SPADE)

hands = Hands(style=HandStyle.FANCY_WATCH, minute_fixing="circle", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=0, outline_same_as_body=False, second_hand_centred=True, chunky=True, outline_on_seconds=0,
                    second_length=dial.get_hand_length(HandType.SECOND), second_fixing_thick=3, include_seconds_hand=True)

# hands.show_hands(show_object=show_object, hand_colours=[Colour.BLACK, Colour.BRASS, Colour.RED])
assembly = Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, name="Wall Clock 41")

if outputSTL:
    bom = assembly.get_BOM()
    # clock specific instructions:
    bom.assembly_instructions = f"""{BillOfMaterials.GENERIC_INSTRUCTIONS_INTRO}

 - The pinion of arbor 3 must be printed with a 0.25mm nozzle as 0.4 is too big to print the teeth in a continuous perimeter
 - The front plate needs flipping over for printing (bug in logic about which way up it should be for exporting the STL)
"""
    bom.export(clock_out_dir)
else:
    assembly.show_clock(show_object, hand_colours=[Colour.WHITE, Colour.BRASS],
                        motion_works_colours=[Colour.BRASS, Colour.BRASS],
                        bob_colours=[Colour.BLUE], with_rods=True,
                        dial_colours=[Colour.BLACK, Colour.WHITE],
                        plate_colours=[Colour.DARKGREY, Colour.BRASS, Colour.BRASS],
                        hand_colours_overrides={"black":Colour.SILVER})




