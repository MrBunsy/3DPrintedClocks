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

Inspired by the round moon clock (wall 32) and the recent success at retrofitting a better centred seconds hand to clocks 12 and 28.

This is an attempt to make a round wall clock with centred second hand. Idea is at first glance it looks like a boring quartz clock,
and only looking again do you realise it's a 3D printed mechanical clock (ended up with a longer pendulum so it's fairly obviously not)

with the smaller escape wheel and usual span of anchor this seems to work.

TODO for future: change arrangement of top pillars so you can view the new wider anchor more easily
also consider something to auto-calcualte size of escape wheel so the anchor is exactly in the radius of the round clock plates

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "wall_clock_39"
clock_out_dir= "out"
gear_style=GearStyle.DIAMONDS
pillar_style=PillarStyle.TWISTY

chain = False

#use this to get best lift
#first print was drop with 1.75
escapement = AnchorEscapement.get_with_optimal_pallets(60, drop_deg=1.75, diameter=60, anchor_teeth=9.5)
#but we want to reconfigure the diameter and tooth size
big_escapement = AnchorEscapement(60, diameter=132, drop=escapement.drop_deg, lift=escapement.lift_deg, anchor_teeth=9.5, style=AnchorStyle.CURVED_MATCHING_WHEEL,
                                        tooth_height_fraction=0.1, tooth_tip_angle=5/2, tooth_base_angle=4/2, force_diameter=True, wheel_thick=2)
#old anchor distance
anchor_centre_distance = big_escapement.anchor_centre_distance

#trying with normal tooth span and retrofitting

teeth = 60
anchor_teeth = math.floor(teeth / 4) + 0.5
wheel_angle = math.pi * 2 * anchor_teeth / teeth
radius  = anchor_centre_distance * math.cos(wheel_angle / 2)

big_escapement = AnchorEscapement(teeth, diameter=radius*2, drop=escapement.drop_deg, lift=escapement.lift_deg, anchor_teeth=anchor_teeth, style=AnchorStyle.CURVED_MATCHING_WHEEL,
                                        tooth_height_fraction=0.15, tooth_tip_angle=2, tooth_base_angle=1.5, force_diameter=True, wheel_thick=2, run=5)

powered_wheel = CordBarrel(diameter=26, ratchet_thick=6, rod_metric_size=4, screw_thread_metric=3, cord_thick=1, thick=15, style=gear_style, use_key=True,
                                 loose_on_rod=False, traditional_ratchet=True, power_clockwise=False, use_steel_tube=False)
if chain:
    powered_wheel = PocketChainWheel2(ratchet_thick=6, chain=COUSINS_1_5MM_CHAIN, max_diameter=25)
max_weight_drop = 1000
if chain:
    max_weight_drop=1400
train = GoingTrain(pendulum_period=1.0, wheels=3, escapement=big_escapement, max_weight_drop=max_weight_drop, use_pulley=not chain, chain_at_back=False, powered_wheels=1,
                         runtime_hours=7.5 * 24, support_second_hand=False, escape_wheel_pinion_at_front=True, powered_wheel=powered_wheel)
train.calculate_ratios(min_pinion_teeth=9, loud=True, max_error=0.001, max_wheel_teeth=80)
train.calculate_powered_wheel_ratios()
dial_d = 175

if chain:
    pinion_extensions = {1:14}
else:
    pinion_extensions={1:18}

powered_modules = [WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1, leaves=train.chain_wheel_ratios[0][1])]
train.gen_gears(module_sizes=[0.9, 0.8, 0.8], thick=3, thickness_reduction=2 / 2.4, powered_wheel_thick=4.5, pinion_thick_multiplier=3, style=gear_style,
                powered_wheel_module_sizes=powered_modules, powered_wheel_pinion_thick_multiplier=2, pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS, lanterns=[0],
                pinion_extensions=pinion_extensions, stack_away_from_powered_wheel=False, escapement_split=True)
train.print_info(weight_kg=2.0)

motion_works = MotionWorks(extra_height=10, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True,
                                 cannon_pinion_friction_ring=True, minute_hand_thick=2, bearing=get_bearing_info(3), reduced_jamming=True)

# retrofit_motion_works_test = MotionWorks(extra_height=10, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True,
#                                  cannon_pinion_friction_ring=True, minute_hand_thick=2, bearing=get_bearing_info(3))#, reduced_jamming=True)

pendulum = Pendulum(bob_d=60, bob_thick=10)

plaque = Plaque(text_lines=["W39#0 {:.1f}cm L.Wallin 2024".format(train.pendulum_length_m * 100), "github.com/MrBunsy/3DPrintedClocks"])

dial = Dial(dial_d, DialStyle.FANCY_WATCH_NUMBERS, font="Eurostile Extended #2", font_scale=1.5, font_path="../fonts/Eurostile_Extended_2_Bold.otf",
                  outer_edge_style=DialStyle.LINES_ARC, inner_edge_style=None, dial_width=dial_d/6, seconds_style=DialStyle.CONCENTRIC_CIRCLES,
                  bottom_fixing=False, top_fixing=False, pillar_style=pillar_style, raised_detail=True)

plates = RoundClockPlates(train, motion_works, name="Wall Clock 39#0", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=25,
                                motion_works_angle_deg=45, leg_height=0, fully_round=True, style=PlateStyle.SIMPLE, pillar_style=pillar_style,
                                second_hand=True, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=False, centred_second_hand=True, escapement_on_back=True,
                                gear_train_layout=GearTrainLayout.COMPACT_CENTRE_SECONDS)

#BODGE wnat to retrofit just one gear reprinted with reduced jamming
#this may have been unecessary - I think the friction clip was catching on the cannon pinion seam. I've filed the seam and it seems promising.
#but I also fitted a reprinted motion arbor with reduced jamming
#next iteration - set this true at the beginning anyway?
# motion_works.override(reduced_jamming=True)

hands = Hands(style=HandStyle.FANCY_WATCH, minute_fixing="circle", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=0, outline_same_as_body=False, second_hand_centred=True, chunky=True, outline_on_seconds=0,
                    second_length=dial.get_hand_length(HandType.SECOND), second_fixing_thick=3, include_seconds_hand=True)


if not chain:

    pulley = LightweightPulley(diameter=plates.get_diameter_for_pulley(), rope_diameter=2, use_steel_rod=False, style=gear_style)
else:
    pulley = None
# show_object(plates.get_cannon_pinion_friction_clip(for_printing=False))

specific_instructions = [
"The cord wheel and its top cap are best printed with Arachne perimeter generation and the seam chosen to avoid the narrow section in the diamond cut outs.",
"The pinion of arbor 3 must be printed with a 0.25mm nozzle as 0.4 is too big to print the teeth in a continuous perimeter",
"The front plate needs flipping over for printing (bug in logic about which way up it should be for exporting the STL)",
]

assembly = Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, name="Wall Clock 39", pulley=pulley, specific_instructions=specific_instructions)

if outputSTL:
    bom = assembly.get_BOM()
    bom.export(clock_out_dir)
else:
    assembly.show_clock(show_object, hand_colours=[Colour.WHITE, Colour.BRASS],
                        motion_works_colours=[Colour.WHITE, Colour.BRASS, Colour.BRASS, Colour.BRASS],
                        bob_colours=[Colour.BLUE], with_rods=True, with_key=True, ratchet_colour=Colour.GOLD,
                        dial_colours=[Colour.BLACK, Colour.WHITE], key_colour=Colour.DARKBLUE,
                        plate_colours=[Colour.LIGHTGREY, Colour.DARKGREY, Colour.BLACK],
                        hand_colours_overrides={"black":Colour.DARKGREY})




