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
I really like the little HAC wall clocks with the window underneath to see the pendulum

So, can I build a really small spring driven wall clock, intended to be enclosed with a pendulum window?
'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "wall_clock_55"
clock_out_dir= "out"
gear_style=GearStyle.ROUNDED_ARMS5


barrel_gear_thick = 5
escapement = AnchorEscapement.get_with_optimal_pallets(teeth=30, drop_deg=2, wheel_thick=2.5)
# proven small(ish) spring barrel from mantel clocks
# can I reduce its size further by using a smaller spring and tweaking the ratio?
power = SpringBarrel(pawl_angle=-math.pi * 3/4, click_angle=-math.pi * 1/4, base_thick=barrel_gear_thick,
                         style=gear_style, wall_thick=8, ratchet_thick=8, spring=MAINSPRING_144040,
                     key_bearing=BEARING_10x15x4, lid_bearing=BEARING_10x15x4_FLANGED, barrel_bearing=BEARING_10x15x4,
                     fraction_of_max_turns=0.55)



train = GoingTrain(pendulum_period=0.9, wheels=4, escapement=escapement, powered_wheels=2,
                         runtime_hours=8 * 24, powered_wheel=power)


module_reduction=0.95
# don't care about pendulum length or exact power ratio
# train.calculate_ratios(module_reduction=module_reduction, max_error=2, loud=True,max_wheel_teeth=70, pinion_max_teeth=15)
# train.set_ratios([[63, 10], [56, 10], [51, 12]])
train.set_ratios([[57, 10], [55, 10], [55, 12]])
# train.set_ratios([[63, 10], [55, 10], [50, 13]])
train.recalculate_pendulum_period()
# train.calculate_powered_wheel_ratios(inaccurate=True)
# train.set_powered_wheel_ratios([[51, 10], [52, 10]])
train.set_powered_wheel_ratios([[58, 10], [55, 10]])
train.print_info()

pendulumSticksOut=10
backPlateFromWall=30

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
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2, leaves=train.chain_wheel_ratios[0][1]),
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
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.0),
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
        "module": 0.9,
        "pinion_thick": 8,
        #haven't got 14mm dowels, so support 12mm
        "max_trundle_length": 13,
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
        "module": 0.9,#1.14,
        #there appears to be a bug which has left this pinion butted right up to the back plate - temp fix, try and force it to produce a standoff without changing full plate distance
        "pinion_thick": 7-0.4
    },
    {
        #third wheel
        "wheel_thick": 2.5,
        "style": gear_style,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 2,
        "pinion_type": PinionType.PLASTIC,
        "rod_diameter": 3,
        "module": 0.85,#1.14,
        "pinion_thick": 7,
        "pinion_at_front": True
    },
    {
        #escape wheel
        "wheel_thick": 2.5,
        "style": gear_style,
        "pinion_at_front": False,
        # "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 12,
        "pinion_type": PinionType.PLASTIC,
        "rod_diameter": 3,
        "pinion_thick": 7
    },
])



motion_works = MotionWorks(extra_height=14, style=gear_style, thick=3, compensate_loose_arbor=False, compact=True)

motion_works.calculate_size(arbor_distance=30)

pendulum = FancyPendulum()#Pendulum(hand_avoider_inner_d=100, bob_d=50, bob_thick=15)

plaque = Plaque(text_lines=["W55#1 {:.1f}cm L.Wallin 2026".format(train.pendulum_length_m * 100), "3DPrintedClocks.co.uk"])

pillar_style = PillarStyle.CLASSIC
dial_d = 152
dial_width=20

dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, romain_numerals_style=RomanNumeralStyle.SIMPLE_SQUARE, style=DialStyle.ROMAN_NUMERALS,
                        outer_edge_style=DialStyle.CONCENTRIC_CIRCLES, seconds_style=DialStyle.CONCENTRIC_CIRCLES, dial_width=dial_width, pillar_style=pillar_style, raised_detail=True)
motion_works_angle_deg=None

gear_train_layout = GearLayout2D.get_old_gear_train_layout(train, GearTrainLayout.COMPACT, extra_anchor_distance=4.5)

motion_works_angle_deg = rad_to_deg(math.pi*1.5 - (gear_train_layout.get_angle_between(2,1) - math.pi*1.5))

plates = RoundClockPlates(train, motion_works, name="Wall Clock 52#0", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=17.5,back_plate_from_wall=35,
                                motion_works_angle_deg=motion_works_angle_deg, leg_height=0, fully_round=True, pillar_style=pillar_style,
                                second_hand=False, standoff_pillars_separate=True, plaque=plaque,  fewer_arms=True, endshake=1, gear_train_layout=gear_train_layout,style=PlateStyle.RAISED_EDGING)

hand_style = HandStyle.SWORD
hands = Hands(style=hand_style, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                  length=dial.outside_d * 0.45, thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True,
                   seconds_hand_thick=1.5, outline_on_seconds=1, include_seconds_hand=True)

assembly = Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, name=clock_name, key_angle_deg=360/12)


dial_colours=[Colour.WHITE, Colour.BLACK]
hand_colours=[Colour.WHITE, Colour.BLACK]
# hand_colours = None
plate_colours = [Colour.DARK_PURPLE, Colour.BRASS, Colour.BRASS, Colour.BRASS]

if not outputSTL:
    assembly.show_clock(show_object, hand_colours=hand_colours,#, Colour.DARKBLUE
                        motion_works_colours=[Colour.GREEN, Colour.LIGHTBLUE],
                        # motion_works_colours=[Colour.DARKGREY],
                        bob_colours=[Colour.BRASS], with_rods=True, with_key=True, ratchet_colour=Colour.PURPLE,
                        dial_colours=dial_colours, key_colour=Colour.PURPLE,
                        plate_colours=plate_colours,
                        day_complication_colours=[Colour.ORANGE, Colour.ORANGE, Colour.DARKBLUE, Colour.WHITE, Colour.BRASS]
                        # day_complication_colours=[Colour.DARKGREY]
                        )


if outputSTL:
    assembly.get_BOM().export(clock_out_dir)

