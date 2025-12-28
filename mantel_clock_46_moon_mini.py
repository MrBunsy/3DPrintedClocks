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
from clocks import *

'''
idle thought: can I shrink the mantel moon clock down a bit?

answer: probably but I need to tidy up where the pillars go so works 
'''
output_STL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    output_STL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "mantel_clock_46"
clock_out_dir= "out"
gear_style=GearStyle.ARCS
pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

moon = True

if moon:
    gear_style = GearStyle.CIRCLES

#this much drop is needed to run reliably (I think it's the wiggle room from the m3 rods in 3mm bearings combined with a small escape wheel?) but a 0.25 nozzle is then needed to print well
lift=2
drop=3
lock=2

#this was orignially for 40tooth recoil, but I think I printed M33#1 like this! oops. wonder if the runtime is worse than M33#0...
# drop =2.5
# lift =2
# lock= 2
#42 as then a quarter span results in exactly the same distance as the old 30 tooth
#going back to 30 teeth, since it was a bearing problem
teeth = 30 if moon else 36 # 42
escapement = AnchorEscapement(drop=drop, lift=lift, teeth=teeth, lock=lock, tooth_tip_angle=5, tooth_base_angle=4, style=AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2,
                                    type=EscapementType.DEADBEAT)
barrel_gear_thick=5
power = SpringBarrel(pawl_angle=-math.pi * 0.8125, click_angle=-math.pi * 0.2125, base_thick=barrel_gear_thick,
                     style=gear_style, wall_thick=8, ratchet_thick=8, spring=SMITHS_EIGHT_DAY_MAINSPRING, key_bearing=BEARING_10x15x4, lid_bearing=BEARING_10x15x4_FLANGED,
                     barrel_bearing=BEARING_10x15x4, ratchet_screws=MachineScrew(2, grub=True))

train = GoingTrain(pendulum_period=2/3, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, powered_wheels=2,
                         runtime_hours=8 * 24, support_second_hand=not moon, escape_wheel_pinion_at_front=False, powered_wheel=power)
if moon:
    #can't fit without making the top pillars further apart or much higher up
    module_reduction = 0.9#1
else:
    module_reduction=0.9#0.85
#ratios from wall clock 32 but larger wheel for the intermediate wheel as we have a larger minute wheel on this clock
# train.gen_spring_barrel(pawl_angle=-math.pi*3/4, click_angle=-math.pi/4, base_thick=barrel_gear_thick,
#                         style=gear_style, wall_thick=8, chain_wheel_ratios=[[61, 10], [64, 10]], extra_barrel_height=1.5, ratchet_thick=8)

train.set_powered_wheel_ratios([[61, 10], [64, 10]])
if not moon:
    # 2/3s with second hand with 36 teeth
    train.set_ratios([[75, 9], [72, 10], [55, 22]])
else:
    #2/3s without second hand with 36 teeth
    # train.set_ratios([[75, 10], [65, 15], [60, 13]])
    #2/3s without second hand with 30 teeth
    train.set_ratios([[72, 10], [70, 12], [60, 14]])
    # constraint = lambda train : train["train"][0][0] == 72 and train["train"][0][1] == 10
    # train.calculate_ratios(module_reduction=module_reduction, min_pinion_teeth=10, max_wheel_teeth=72, pinion_max_teeth=20, wheel_min_teeth=50, loud=True, constraint=constraint)
    # train.calculate_ratios(module_reduction=module_reduction, min_pinion_teeth=10, max_wheel_teeth=72, pinion_max_teeth=15, wheel_min_teeth=60, loud=True)#, constraint=constraint)
    # 2/3s with 40 teeth
    # train.set_ratios([[65, 10], [63, 14], [60, 13]])
    #2/3s with 42 teeth
    # train.set_ratios([[65, 10], [60, 13], [60, 14]])
# train.calculate_ratios(module_reduction=module_reduction, min_pinion_teeth=10, max_wheel_teeth=80, pinion_max_teeth=16, wheel_min_teeth=60, loud=True)



#2/3s without second hand 40 teeth
# [[65, 10], [63, 14], [60, 13]]

#2/3s without second hand 40 teeth for retrofitting
# train.set_ratios([[72, 10], [70, 12], [45, 14]])

pendulum_sticks_out=10
back_plate_from_wall=25

scale = 1.0/1.2


#TODO centre wheel and intemediate wheel can rub against each other.
pinion_extensions = {0:1, 1:3, 3:8} if moon else {0:1, 1:12, 2:5}
powered_modules = [WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2), WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.0)]


old_modules = [1,0.9,0.9]

last_module = 0.9


module_sizes = old_modules

print("module_sizes", module_sizes)
lanterns=[0, 1]
# train.gen_gears(module_sizes=module_sizes, module_reduction=module_reduction, thick=2.4, thickness_reduction=0.9, powered_wheel_thicks=[barrel_gear_thick, 4],
#                 pinion_thick_multiplier=3, style=gear_style,
#                 powered_wheel_module_increase=1.25, powered_wheel_pinion_thick_multiplier=1.875, pendulum_fixing=pendulum_fixing, stack_away_from_powered_wheel=True,
#                 pinion_extensions=pinion_extensions, lanterns=lanterns, pinion_thick_extra=5, powered_wheel_module_sizes=powered_modules)

train.generate_arbors_dicts([
    {
        #spring barrel
        "module":WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2),
        "style":gear_style,

    },
    {
        #intermediate wheel
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.0),
        "pinion_type": PinionType.LANTERN_THIN,
        "pinion_thick":1.875*barrel_gear_thick,
        "wheel_thick":4
    },
    {
        #centre wheel
        "module": 1*scale,
        "pinion_type": PinionType.LANTERN,
        "pinion_thick":4*1.875,
        "pinion_at_front":True
    },
    {
        "module":0.9*scale,
        "pinion_extension":3
    },
    {
        "module":0.9*scale,
        "pinion_at_front":False

    },
    {
        #escape wheel
        "pinion_extension": 8,
        "pinion_at_front":False
    }
], pinion_thick_extra=5)



train.print_info(for_runtime_hours=24*7)

#had been using the leftover bob from wall clock 32 before I made it thicker, so bumping up to 10 from 8 and 8 was a bit fiddly to get any weight into
pendulum = Pendulum(bob_d=50*scale, bob_thick=10)
pillar_style=PillarStyle.CLASSIC

dial_d=205*scale
dial_width=25*scale
moon_radius=13*scale
if moon:
    dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=DialStyle.DOTS, dial_width=dial_width, pillar_style=pillar_style)
    moon_complication = MoonPhaseComplication3D(gear_style=gear_style, first_gear_angle_deg=205, on_left=False, bevel_module=1.1*scale, module=0.9*scale, moon_radius=moon_radius,
                                                      bevel_angle_from_hands_deg=90, moon_from_hands=(dial_d / 2 - dial_width) - moon_radius - 5, moon_inside_dial=True)
else:
    dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, romain_numerals_style=RomanNumeralStyle.SIMPLE_SQUARE, style=DialStyle.ROMAN_NUMERALS,
                  outer_edge_style=DialStyle.DOTS, seconds_style=DialStyle.CONCENTRIC_CIRCLES, dial_width=dial_width, pillar_style=pillar_style)
    moon_complication = None

motion_works_height = 22 if moon else 10

#tiny bit extra gap as the brass PETG seems to need it
motion_works = MotionWorks(extra_height=motion_works_height, style=gear_style, thick=3, compensate_loose_arbour=True, compact=True, moon_complication=moon_complication,
                                 cannon_pinion_to_hour_holder_gap_size=0.6, module=1*scale)

motion_works_angle_deg=180+90

if moon:
    motion_works_angle_deg=180+40
    motion_works.calculate_size(arbor_distance=30*scale)
    moon_complication.set_motion_works_sizes(motion_works)

plaque = Plaque(text_lines=["M33#2 {:.1f}cm L.Wallin 2025".format(train.pendulum_length_m * 100), "3DPrintedClocks.co.uk"])

plates = MantelClockPlates(train, motion_works, name="Mantel 46", dial=dial, plate_thick=7, back_plate_thick=6, style=PlateStyle.RAISED_EDGING,
                                 pillar_style=pillar_style, moon_complication=moon_complication, second_hand=not moon, symetrical=moon, pendulum_sticks_out=21,
                                 standoff_pillars_separate=True, fixing_screws=MachineScrew(4, countersunk=False), motion_works_angle_deg=motion_works_angle_deg,
                                 plaque=plaque, split_detailed_plate=True)
print("plate pillar y", plates.bottom_pillar_positions[0][1])

hand_style = HandStyle.MOON if moon else HandStyle.SPADE
hands = Hands(style=hand_style, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.outside_d*0.45, thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True,
                    second_length=dial.second_hand_mini_dial_d * 0.45 if not moon else 1, seconds_hand_thick=1.5, outline_on_seconds=0.5)


assembly = Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, with_mat=True)
dial_colours =  [Colour.WHITE, Colour.BLACK]
if moon:
    dial_colours =  [Colour.BLUE, Colour.WHITE]




if output_STL:
    assembly.get_BOM().export()
else:
    assembly.show_clock(show_object, hand_colours=[Colour.WHITE, Colour.BLACK], motion_works_colours=[Colour.BRASS],
                        bob_colours=[Colour.GOLD], with_rods=True, with_key=True, ratchet_colour=Colour.GOLD, dial_colours=dial_colours,
                        plate_colours=[Colour.DARK_GREEN, Colour.BRASS, Colour.BRASS])  # , gear_colours=[Colour.GOLD])






