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
from clocks import deg_to_rad

'''

Spring driven silent round wall clock with day of the week.

Plan:

 - stop works to see if spring driven silent can be more accurate
 - geneva gearing for day of week

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

art_deco = True

clock_name= "wall_clock_52"
clock_out_dir= "out"
gear_style=GearStyle.ARCS
pendulumFixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS


#after a huge amount of faffing about, the problem was the bearings, not the escapement. So I've used the new auto-calculated efficient escapement for a retrofit.
#was a drop of 2.75, but I think that was excessive
escapement_info = AnchorEscapement.get_with_optimal_pallets(teeth=30, drop_deg=2, wheel_thick=2.5)
#nylon wire only 0.15, but need a hole big enough to print well
escapement = SilentPinPalletAnchorEscapement(teeth=escapement_info.teeth, drop=escapement_info.drop_deg, lift=escapement_info.lift_deg, run=escapement_info.run_deg, lock=escapement_info.lock_deg, pin_diameter=1.0)

power = SpringBarrel(pawl_angle=-math.pi * 3/4, click_angle=-math.pi * 1/4, base_thick=5, barrel_bearing=BEARING_12x18x4_FLANGED,
                     style=gear_style, wall_thick=8, ratchet_thick=8, spring=SMITHS_EIGHT_DAY_MAINSPRING,
                     ratchet_screws=MachineScrew(2, grub=True), seed_for_gear_styles=clock_name+"barrel", ratchet_pawl_screwed_from_front=True, stop_works=True)


train = GoingTrain(pendulum_period=1, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, powered_wheels=2,
                         runtime_hours=8 * 24, support_second_hand=False, escape_wheel_pinion_at_front=True, powered_wheel=power)

barrel_gear_thick = 5#8

moduleReduction=0.95#0.85

train.set_powered_wheel_ratios([[61, 10], [64, 10]])
train.set_ratios([[65, 14], [60, 13], [56, 10]])

pendulumSticksOut=10
backPlateFromWall=30
dial_d = 205
dial_width=25

pinion_extensions = {0:1, 1:15, 2:10,3:18}

powered_modules = [WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5, leaves=train.chain_wheel_ratios[0][1]),
                    WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2)
                   ]
train.generate_arbors_dicts([
    {
        #spring barrel
        "wheel_thick": 5,
        "style": gear_style,
        "pinion_at_front": True,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 3,
        "pinion_type": PinionType.LANTERN,
        "rod_diameter": 11.9,
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5, leaves=train.chain_wheel_ratios[0][1]),
    },
    {
        #intermediate wheel
        "wheel_thick": 4,
        "style": gear_style,
        "pinion_at_front": True,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 5,
        "pinion_type": PinionType.LANTERN,
        "rod_diameter": 3,
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2),
        "pinion_thick": 9
    },
    {
        #centre wheel
        "wheel_thick": 3,
        "style": gear_style,
        "pinion_at_front": True,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 1,
        "pinion_type": PinionType.LANTERN,
        "rod_diameter": 3,
        "module": 1.14,
        "pinion_thick": 8
    },
    {
        #second wheel
        "wheel_thick": 2.5,
        "style": gear_style,
        "pinion_at_front": False,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 20,
        "pinion_type": PinionType.PLASTIC,
        "rod_diameter": 3,
        "module": 1.14,#1.14,
        "pinion_thick": 7
    },
    {
        #third wheel
        "wheel_thick": 2.5,
        "style": gear_style,
        "pinion_at_front": False,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 9,
        "pinion_type": PinionType.PLASTIC,
        "rod_diameter": 3,
        "module": 1.15,#1.14,
        "pinion_thick": 7
    },
    {
        #escape wheel
        "wheel_thick": 2.5,
        "style": gear_style,
        "pinion_at_front": True,
        # "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 18,
        "pinion_type": PinionType.PLASTIC,
        "rod_diameter": 3,
        "pinion_thick": 7
    },
])

#wanted to see if we could fit both complications on the same clock. Not easily and I'm not sure I'm desperate enough to do the work to make it happen
moon = False
moon_radius=13

gear_layout =  GearLayout2D.get_old_gear_train_layout(train, GearTrainLayout.COMPACT)
#angle_deg=-60
days_angle = 60
if moon:
    days_angle = -60

days_complication = DayOfWeekComplication(module=0.8, style=gear_style, bevel_module=1.1, angle_deg=days_angle, extra_z_height=0, cylinder_length=28)
# days_complication = DayOfWeekComplication(module=0.8, style=gear_style, bevel_module=1.1, angle_deg=rad_to_deg(gear_layout.get_angle_between(2,5)), extra_z_height=0, cylinder_length=25)
# days_complication = DayOfWeekComplication(module=0.6, style=gear_style, bevel_module=1.1, angle_deg=rad_to_deg(gear_layout.get_angle_between(2,1)), extra_z_height=0, cylinder_length=25)

if moon:
    moon_complication = MoonPhaseComplication3D(gear_style=gear_style, first_gear_angle_deg=205, on_left=True, bevel_module=1.1, module=0.9, moon_radius=moon_radius,
                                                  bevel_angle_from_hands_deg=90, moon_from_hands=(dial_d/2 - dial_width) - moon_radius - 5, moon_inside_dial=True)
else:
    moon_complication = None

motion_works = MotionWorks(extra_height=14, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True,
                           cannon_pinion_to_hour_holder_gap_size=0.6, drives_complication=days_complication)
#WANT a small motion works to provide more space for the days of week prism to fit behind the dial
# motion_works.calculate_size(arbor_distance=30)
days_complication.set_motion_works_sizes(motion_works)
if moon:
    moon_complication.set_motion_works_sizes(motion_works)

pendulum = Pendulum(hand_avoider_inner_d=100, bob_d=60, bob_thick=12.5)

plaque = Plaque(text_lines=["W32#2 {:.1f}cm L.Wallin 2026".format(train.pendulum_length_m * 100), "3DPrintedClocks.co.uk"])


pillar_style=PillarStyle.CLASSIC
motion_works_angle_deg=rad_to_deg(gear_layout.get_angle_between(2,3))

if moon:
    motion_works_angle_deg = -90
if art_deco:
    dial = Dial(dial_d, DialStyle.ARABIC_NUMBERS, font="Dutch Courage", font_scale=0.9,
                font_path="../fonts/dutch_courage/CCDutchCourageLite/CCDutchCourageLite.ttf", outer_edge_style=DialStyle.LINES_RECT, inner_edge_style=None,
                dial_width=dial_width, pillar_style=pillar_style)
else:
    dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=DialStyle.LINES_INDUSTRIAL, dial_width=dial_width, pillar_style=pillar_style)

plates = RoundClockPlates(train, motion_works, name="Wall Clock 52#0", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=12,back_plate_from_wall=30,
                                motion_works_angle_deg=motion_works_angle_deg, leg_height=0, fully_round=True, style=PlateStyle.RAISED_EDGING, pillar_style=pillar_style,
                                second_hand=False, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=True, fewer_arms=True, gear_train_layout=gear_layout, endshake=1,
                          days_complication = days_complication, moon_complication=moon_complication)

if art_deco:
    hands = Hands(style=HandStyle.ART_DECO, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                  length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=False,
                  outline_on_seconds=0, second_hand_centred=False)
else:
    hands = Hands(style=HandStyle.INDUSTRIAL, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=0, outline_same_as_body=False, chunky=False,
                    outline_on_seconds=0, second_hand_centred=False)

assembly = Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, name=clock_name)

# assembly.get_arbor_rod_lengths()
# plates.get_rod_lengths()

dial_colours=[Colour.WHITE, Colour.BLACK]
hand_colours=[Colour.RED]
plate_colours = [Colour.DARKBLUE, Colour.BRASS, Colour.BRASS, Colour.BRASS]
if art_deco:
    dial_colours = [Colour.WHITE, Colour.BRASS]
    hand_colours = [Colour.WHITE, Colour.BRASS]
    plate_colours = [Colour.BLACK, Colour.BRASS, Colour.BRASS, Colour.BRASS]

if not outputSTL:
    assembly.show_clock(show_object, hand_colours=hand_colours,#, Colour.DARKBLUE
                        motion_works_colours=[Colour.GREEN, Colour.LIGHTBLUE],
                        bob_colours=[Colour.SILVER], with_rods=True, with_key=True, ratchet_colour=Colour.PURPLE,
                        dial_colours=dial_colours, key_colour=Colour.PURPLE,
                        plate_colours=plate_colours)


if outputSTL:
    assembly.get_BOM().export(clock_out_dir)

