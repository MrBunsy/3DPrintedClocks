'''
Copyright Luke Wallin 2025

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
from clocks import *
import json
'''
With the success of mantel clock 34 (attempting to shrink down the spring barrel) I want to try and see how small I can make a spring driven wall clock
so the gear train from mantel clock 34, but in a wall clock
'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "Wall Clock 43"
clock_out_dir= "out"
gear_style=GearStyle.ROUNDED_ARMS5


escapement = AnchorEscapement.get_with_optimal_pallets(36, drop_deg=2)


barrel_gear_thick = 5
powered_wheel = SpringBarrel(spring=SMITHS_EIGHT_DAY_MAINSPRING, pawl_angle=math.pi, click_angle=-math.pi/2, ratchet_at_back=True, style=gear_style, base_thick=barrel_gear_thick,
                        wall_thick=8)

train = GoingTrain(pendulum_period=2/3, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, powered_wheels=2,
                             runtime_hours=8 * 24, support_second_hand=True, escape_wheel_pinion_at_front=False, powered_wheel=powered_wheel)


module_reduction=0.9
train.set_powered_wheel_ratios([[61, 10], [64, 10]])

train.set_ratios([[75, 9], [72, 10], [55, 22]])
pinion_extensions =  {0: 1, 1: 15, 2: 0}
module_sizes = [0.8, 0.75, 0.75]

pillar_style = PillarStyle.CLASSIC

train.set_powered_wheel_ratios([[64, 10], [69, 10]])

train.print_info(for_runtime_hours=7*24)

pendulumSticksOut=10
backPlateFromWall=40

pinion_extensions={0:1.5, 1:4, 3:8}
powered_modules = [WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2), WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.0)]

lanterns=[0, 1]
train.gen_gears(module_sizes=module_sizes, module_reduction=module_reduction, thick=2.4, thickness_reduction=0.9, powered_wheel_thicks=[barrel_gear_thick, 4],
                pinion_thick_multiplier=3, style=gear_style,
                powered_wheel_module_increase=1.25, powered_wheel_pinion_thick_multiplier=1.875, pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS, stack_away_from_powered_wheel=True,
                pinion_extensions=pinion_extensions, lanterns=lanterns, pinion_thick_extra=5, powered_wheel_module_sizes=powered_modules)

motion_works = MotionWorks(extra_height=0, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True)
motion_works_angle_deg=360-40

pendulum = FancyPendulum(bob_d=40)
dial_d=175
seconds_dial_width = 7

dial_width=30

dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=DialStyle.ROMAN_NUMERALS, romain_numerals_style=RomanNumeralStyle.SIMPLE_ROUNDED,
            outer_edge_style=DialStyle.LINES_ARC, inner_edge_style=None, raised_detail=True, dial_width=dial_width, seconds_dial_width=seconds_dial_width)

plaque = Plaque(text_lines=["W43#0 {:.1f}cm".format(train.pendulum_length_m * 100), "L.Wallin 2025"])

plates = RoundClockPlates(train, motion_works, name="Wall 43", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=20,
                                motion_works_angle_deg=motion_works_angle_deg, leg_height=0, fully_round=True, style=PlateStyle.RAISED_EDGING, pillar_style=pillar_style,
                                second_hand=True, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=False, moon_complication=None, escapement_on_front=False)

hands = Hands(style=HandStyle.DIAMOND, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
              length=dial_d/2, thick=motion_works.minute_hand_slot_height, outline=0, seconds_hand_thick=1, second_length=dial.get_hand_length(HandType.SECOND))

specific_instructions = [
"The front plate needs flipping over for printing (bug in logic about which way up it should be for exporting the STL)",
]

assembly = Assembly(plates, name=clock_name, hands=hands, time_seconds=30, pendulum=pendulum, specific_instructions=specific_instructions)

if not outputSTL:
    assembly.show_clock(show_object, with_rods=True, plate_colours=[Colour.BROWN, Colour.BLACK, Colour.BLACK],
                        dial_colours=[Colour.WHITE, Colour.BLACK], bob_colours=[Colour.GOLD],
                        gear_colours=[Colour.GOLD],
                        motion_works_colours=[Colour.GOLD],
                        plaque_colours=[Colour.WHITE, Colour.BLACK],
                        ratchet_colour=Colour.GOLD,
                        hand_colours=[Colour.BRASS])

if outputSTL:
    assembly.get_BOM().export(clock_out_dir)