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
Example new clock design

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "Wall Clock Example"
clock_out_dir= "out"
#choose whichever styles you fancy, they're only decorative
gear_style=GearStyle.ROUNDED_ARMS5
pillar_style = PillarStyle.PLAIN
# this is the only supported pendulum fixing that currently works
pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS


# this is very experimental
second_hand_centred = False

# choose how many teeth on your escape wheel and a reasonable amount of drop
escapement = AnchorEscapement.get_with_optimal_pallets(30, drop_deg=1.75)

# Choose and configure the power source of the clock, a cord barrel (cord that is wound up with a key) is the easiest and most reliable mechanism
powered_wheel = CordBarrel(diameter=26, ratchet_thick=6, rod_metric_size=4, screw_thread_metric=3, cord_thick=1, thick=15, style=gear_style, use_key=True,
                                 loose_on_rod=False, traditional_ratchet=True, power_clockwise=False, use_steel_tube=False)
# This represents the gear train that tells the time from the power source, to the minute hand (centre arbor) to the escapement
train = GoingTrain(pendulum_period=2, wheels=3, escapement=escapement, max_weight_drop=1000, use_pulley=True, chain_at_back=False,
                         powered_wheels=1, runtime_hours=7.5 * 24, powered_wheel=powered_wheel, escape_wheel_pinion_at_front=True)

# size ratio of each wheel to the next (can make train easier to calculate if the wheels get smaller)
module_reduction=0.9


# auto calculate a valid set of gear ratios.
train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=10, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, module_reduction=module_reduction)
train.calculate_powered_wheel_ratios()

pendulumSticksOut=10
backPlateFromWall=40
# manually adjust how long the pinions are - sometimes needed to ensure that wheels won't clash
pinion_extensions={}
# manually specify module size of the powered wheel + pinion, because this uses steel rods which only come in certain sizes
powered_modules=[WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2)]
train.gen_gears(module_size=0.9, thick=3, thickness_reduction=0.9, module_reduction=module_reduction,  powered_wheel_thick=6, pinion_thick_multiplier=3, style=gear_style,
                powered_wheel_module_sizes=powered_modules, powered_wheel_pinion_thick_multiplier=2, pendulum_fixing=pendulum_fixing, lanterns=[0],
                pinion_extensions=pinion_extensions, stack_away_from_powered_wheel=True)

train.print_info(weight_kg=2)

dial_d=160
dial_width = dial_d*0.1
moon_radius=10

moon = True

if not moon:
    motion_works = MotionWorks(extra_height=0, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True)
    moon_complication = None
    motion_works_angle_deg=360-40
else:
    moon_complication = MoonPhaseComplication3D(gear_style=gear_style, first_gear_angle_deg=205, on_left=False, bevel_module=1.0, module=0.8, moon_radius=moon_radius,
                                                      bevel_angle_from_hands_deg=90, moon_from_hands=(dial_d/2 - dial_width) - moon_radius - 3, moon_inside_dial=True,
                                                      lone_bevel_min_height=13)
    motion_works = MotionWorks(extra_height=20, style=gear_style, thick=3, compact=True, moon_complication=moon_complication)
    moon_complication.set_motion_works_sizes(motion_works)
    motion_works_angle_deg=180+40



pendulum = Pendulum(bob_d=60, bob_thick=10)

dial = Dial(outside_d=dial_d, bottom_fixing=True, top_fixing=False, style=DialStyle.LINES_INDUSTRIAL,
                  seconds_style=DialStyle.LINES_ARC, pillar_style=pillar_style, raised_detail=True)
plaque = Plaque(text_lines=["W40#0 {:.1f}cm L.Wallin".format(train.pendulum_length_m * 100), "2025 PLA Test"])

plates = RoundClockPlates(train, motion_works, name="Wall 40", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=20,
                                motion_works_angle_deg=motion_works_angle_deg, leg_height=0, fully_round=True, style=PlateStyle.RAISED_EDGING, pillar_style=pillar_style,
                                second_hand=False, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=True, moon_complication=moon_complication)

pulley = LightweightPulley(diameter=plates.get_diameter_for_pulley(), rope_diameter=2, use_steel_rod=False, style=gear_style)

hands = Hands(style=HandStyle.SWORD, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True, second_hand_centred=second_hand_centred)#, secondLength=dial.second_hand_mini_dial_d*0.45, seconds_hand_thick=1.5)

specific_instructions = [
"The front plate needs flipping over for printing (bug in logic about which way up it should be for exporting the STL)",
]

assembly = Assembly(plates, name=clock_name, hands=hands, time_seconds=30, pendulum=pendulum, pulley=pulley, specific_instructions=specific_instructions)

if not outputSTL:
    assembly.show_clock(show_object, with_rods=True, plate_colours=[Colour.DARKER_GREY, Colour.DARKER_GREY, Colour.BLACK],
                        dial_colours=[Colour.WHITE, Colour.BLACK], bob_colours=[Colour.BRIGHT_ORANGE],
                        gear_colours=[Colour.BRIGHT_ORANGE, Colour.LIME_GREEN],
                        motion_works_colours=[Colour.BRIGHT_ORANGE, Colour.BRIGHT_ORANGE, Colour.LIME_GREEN],
                        pulley_colour=Colour.LIME_GREEN, plaque_colours=[Colour.WHITE, Colour.BLACK])

if outputSTL:
    assembly.get_BOM().export(clock_out_dir)