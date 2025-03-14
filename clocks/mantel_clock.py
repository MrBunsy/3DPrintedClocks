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

from .escapements import AnchorEscapement, Pendulum
from .gear_trains import GoingTrain
from .assembly import *
from .power import *
from .dial import *
from .cosmetics import *
from .plates import *

'''
based on mantel clock 33 (the moon one) but designed to be configurable.

This clock has a proven gear train and I've stuggled to reduce its size, so it seems like a good one to use as a base for other styles of mantle clock
'''

def get_mantel_clock(clock_name = "mantel_clock_x", gear_style=GearStyle.ARCS, moon = False, second_hand=False, dial=None, hands=None, pillar_style=PillarStyle.CLASSIC,
                     prefer_tall=True, zig_zag_side=True):
    '''
    return the assembly object
    '''
    pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

    teeth = 30 if not second_hand else 36
    escapement = AnchorEscapement.get_with_optimal_pallets(teeth=teeth, drop_deg=2)
    barrel_gear_thick = 5

    power = SpringBarrel(pawl_angle=-math.pi * 3 / 4, click_angle=-math.pi / 4, base_thick=barrel_gear_thick,
                         style=gear_style, wall_thick=8, ratchet_thick=8, spring=SMITHS_EIGHT_DAY_MAINSPRING)

    train = GoingTrain(pendulum_period=2/3, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, powered_wheels=2,
                             runtime_hours=8 * 24, support_second_hand=second_hand, escape_wheel_pinion_at_front=False, powered_wheel=power)


    module_reduction=0.9
    train.set_powered_wheel_ratios([[61, 10], [64, 10]])

    if second_hand:
        # 2/3s with second hand with 36 teeth
        train.set_ratios([[75, 9], [72, 10], [55, 22]])
    else:
        #2/3s without second hand with 30 teeth
        train.set_ratios([[72, 10], [70, 12], [60, 14]])

    
    

    pendulum_sticks_out=10
    back_plate_from_wall=30

    pinion_extensions = {0:1, 1:3, 3:8} if not second_hand else {0:1, 1:12, 2:5}
    powered_modules = [WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2)]

    module_sizes = [1,0.9,0.9]

    lanterns=[0, 1]
    train.gen_gears(module_sizes=module_sizes, module_reduction=module_reduction, thick=2.4, thickness_reduction=0.9, powered_wheel_thicks=[barrel_gear_thick, 4],
                    pinion_thick_multiplier=3, style=gear_style,
                    powered_wheel_module_increase=1.25, powered_wheel_pinion_thick_multiplier=1.875, pendulum_fixing=pendulum_fixing, stack_away_from_powered_wheel=True,
                    pinion_extensions=pinion_extensions, lanterns=lanterns, pinion_thick_extra=5, powered_wheel_module_sizes=powered_modules)

    pendulum = Pendulum(hand_avoider_inner_d=100, bob_d=50, bob_thick=10)

    
    dial_d=205
    dial_width=25
    moon_radius=13

    if moon:
        moon_complication = MoonPhaseComplication3D(gear_style=gear_style, first_gear_angle_deg=205, on_left=False, bevel_module=1.1, module=0.9, moon_radius=moon_radius,
                                                    bevel_angle_from_hands_deg=90, moon_from_hands=(dial_d / 2 - dial_width) - moon_radius - 5, moon_inside_dial=True)
    else:
        moon_complication = None

    if dial is None:
        if moon:
            dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=DialStyle.DOTS, dial_width=dial_width, pillar_style=pillar_style)
        else:
            dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, romain_numerals_style=RomanNumeralStyle.SIMPLE_SQUARE, style=DialStyle.ROMAN_NUMERALS,
                          outer_edge_style=DialStyle.DOTS, seconds_style=DialStyle.CONCENTRIC_CIRCLES, dial_width=dial_width, pillar_style=pillar_style)
    else:
        #just want to set outside d, everything else will be overriden by plates
        dial.configure_dimensions(10, 10, outside_d=dial_d)
        dial.pillar_style = pillar_style
    
    motion_works_height = 22 if moon else 10
    
    #tiny bit extra gap as the brass PETG seems to need it
    motion_works = MotionWorks(extra_height=motion_works_height, style=gear_style, thick=3, compensate_loose_arbour=True, compact=True, moon_complication=moon_complication,
                                     cannon_pinion_to_hour_holder_gap_size=0.6)
    
    motion_works_angle_deg=360-32

    if moon:
        motion_works_angle_deg = 180 + 40
        motion_works.calculate_size(arbor_distance=30)
        moon_complication.set_motion_works_sizes(motion_works)
    
    plaque = Plaque(text_lines=["M33#2 {:.1f}cm L.Wallin 2024".format(train.pendulum_length_m * 100), "github.com/MrBunsy/3DPrintedClocks"])
    
    plates = MantelClockPlates(train, motion_works, name="Mantel 33", dial=dial, plate_thick=7, back_plate_thick=6, style=PlateStyle.RAISED_EDGING,
                                     pillar_style=pillar_style, moon_complication=moon_complication, second_hand=second_hand, symetrical=True, pendulum_sticks_out=21,
                                     standoff_pillars_separate=True, fixing_screws=MachineScrew(4, countersunk=False), motion_works_angle_deg=motion_works_angle_deg,
                                     plaque=plaque, split_detailed_plate=True, prefer_tall=prefer_tall, zig_zag_side=zig_zag_side)
    print("plate pillar y", plates.bottom_pillar_positions[0][1])

    if hands is None:
        hand_style = HandStyle.SPADE
        hands = Hands(style=hand_style, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                        length=dial.outside_d*0.45, thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True,
                        second_length=dial.second_hand_mini_dial_d * 0.45 if second_hand else 1, seconds_hand_thick=1.5, outline_on_seconds=0.5)
    else:
        hands.configure_motion_works(motion_works)
        hands.configure_length(dial.outside_d*0.45)

    
    
    assembly = Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, with_mat=True, name=clock_name)

    return assembly





