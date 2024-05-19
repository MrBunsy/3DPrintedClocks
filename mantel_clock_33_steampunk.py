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

import clocks as clock

'''
Nothing particularly new, just had an idea for a clock that would look cool:

- black plates with raised brass edging
- symetric style
- fancy hands - maybe improve my existing fancy hands?
- Unsure of style of dial
- Maybe try the smaller spring and see if that's up to it? (uncertain since the centred second hand clock struggled to make a week)

Maybe one for printables?
'''
output_STL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    output_STL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "mantel_clock_33"
clock_out_dir= "out"
gear_style=clock.GearStyle.ARCS
pendulum_fixing=clock.PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

moon = True

if moon:
    gear_style = clock.GearStyle.CIRCLES

#for period 1.5
# drop =1.5
# lift =3
# lock=1.5
# escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, toothTipAngle=5, toothBaseAngle=4, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL)
# lift=4
# drop=2
# lock=2
# lift=3.5
# drop=2
# lock=1.75
#this much drop is needed to run reliably (I think it's the wiggle room from the m3 rods in 3mm bearings combined with a small escape wheel?) but a 0.25 nozzle is then needed to print well
lift=2
drop=3
lock=2
teeth = 30 if moon else 36
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=teeth, lock=lock, tooth_tip_angle=3,
                                    tooth_base_angle=3, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2)

train = clock.GoingTrain(pendulum_period=2/3, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, chain_wheels=2,
                         runtime_hours=8 * 24, support_second_hand=not moon, escape_wheel_pinion_at_front=False)
barrel_gear_thick = 8
if moon:
    #can't fit without making the top pillars further apart or much higher up
    module_reduction = 0.9#1
else:
    module_reduction=0.9#0.85
#ratios from wall clock 32 as these fit next to a module 1 minute wheel
train.gen_spring_barrel(pawl_angle=-math.pi*3/4, click_angle=-math.pi/4, base_thick=barrel_gear_thick,
                        style=gear_style, fraction_of_max_turns=0.35)#, chain_wheel_ratios=[[62, 10], [61, 10]]), spring=clock.MAINSPRING_183535,
'''
[[61, 10], [78, 10]]
spring_wound_coils: 23.53661753519562 spring unwound coils: 12.838105212872968, max theoretical barrel turns: 10.698512322322653
Over a runtime of 168.0hours the spring barrel will make 3.5 full rotations which is 33.0% of the maximum number of turns (10.7) and will take 5.3 key turns to wind back up
'''

if not moon:
    # 2/3s with second hand with 36 teeth
    train.set_ratios([[75, 9], [72, 10], [55, 22]])
else:
    #2/3s without second hand with 36 teeth
    # train.set_ratios([[75, 10], [65, 15], [60, 13]])
    #2/3s without second hand with 30 teeth
    train.set_ratios([[72, 10], [70, 12], [60, 14]])
    # train.calculate_ratios(module_reduction=module_reduction, min_pinion_teeth=10, max_wheel_teeth=80, pinion_max_teeth=16, wheel_min_teeth=60, loud=True)
# train.calculate_ratios(module_reduction=module_reduction, min_pinion_teeth=10, max_wheel_teeth=80, pinion_max_teeth=16, wheel_min_teeth=60, loud=True)

pendulum_sticks_out=10
back_plate_from_wall=30

pinion_extensions = {1:5, 3:8} if moon else {1:12, 2:5}
powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), 1]
train.gen_gears(module_sizes=[1,0.9,0.9], module_reduction=module_reduction, thick=2.4, thickness_reduction=0.9, chain_wheel_thick=barrel_gear_thick, pinion_thick_multiplier=3, style=gear_style,
                powered_wheel_module_increase=1.25, chain_wheel_pinion_thick_multiplier=1.875, pendulum_fixing=pendulum_fixing, stack_away_from_powered_wheel=True,
                pinion_extensions=pinion_extensions, lanterns=[0], pinion_thick_extra=5, powered_wheel_module_sizes=powered_modules)
# train.print_info(weight_kg=1.5)
train.print_info(for_runtime_hours=24*7)
train.get_arbour_with_conventional_naming(0).print_screw_length()

pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=50, bob_thick=8)
pillar_style=clock.PillarStyle.CLASSIC

dial_d=205
dial_width=25
moon_radius=13
if moon:
    dial = clock.Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=clock.DialStyle.DOTS, dial_width=dial_width, pillar_style=pillar_style)
    moon_complication = clock.MoonPhaseComplication3D(gear_style=gear_style, first_gear_angle_deg=205, on_left=False, bevel_module=1.1, module=0.9, moon_radius=moon_radius,
                                                      bevel_angle_from_hands_deg=90, moon_from_hands=(dial_d / 2 - dial_width) - moon_radius - 5, moon_inside_dial=True)
else:
    dial = clock.Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, romain_numerals_style=clock.RomanNumeralStyle.SIMPLE_SQUARE, style=clock.DialStyle.ROMAN_NUMERALS,
                  outer_edge_style=clock.DialStyle.DOTS, seconds_style=clock.DialStyle.CONCENTRIC_CIRCLES, dial_width=dial_width, pillar_style=pillar_style)
    moon_complication = None

motion_works_height = 22 if moon else 10

motion_works = clock.MotionWorks(extra_height=motion_works_height, style=gear_style, thick=3, compensate_loose_arbour=True, compact=True, moon_complication=moon_complication)

motion_works_angle_deg=180+90

if moon:
    motion_works_angle_deg=180+40
    motion_works.calculate_size(arbor_distance=30)
    moon_complication.set_motion_works_sizes(motion_works)

plates = clock.MantelClockPlates(train, motion_works, name="Mantel 33", dial=dial, plate_thick=6, style=clock.PlateStyle.RAISED_EDGING,
                                 pillar_style=pillar_style, moon_complication=moon_complication, second_hand=not moon, symetrical=moon, pendulum_sticks_out=25,
                                 standoff_pillars_separate=True, fixing_screws=clock.MachineScrew(4, countersunk=False), motion_works_angle_deg=motion_works_angle_deg)


# show_object(plates.get_plate_detail(back=True))

hand_style = clock.HandStyle.MOON if moon else clock.HandStyle.SPADE
hands = clock.Hands(style=hand_style, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.outside_d*0.45, thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True,
                    second_length=dial.second_hand_mini_dial_d * 0.45 if not moon else 1, seconds_hand_thick=1.5, outline_on_seconds=0.5)


assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum)#weights=[clock.Weight(height=245,diameter=55)]
dial_colours =  [clock.Colour.WHITE, clock.Colour.BLACK]
if moon:
    dial_colours =  [clock.Colour.BLUE, clock.Colour.WHITE]
assembly.show_clock(show_object, hand_colours=[clock.Colour.WHITE, clock.Colour.BLACK], motion_works_colours=[clock.Colour.BRASS],
                    bob_colours=[clock.Colour.GOLD], with_rods=True, with_key=True, ratchet_colour=clock.Colour.GOLD, dial_colours=dial_colours,
                    plate_colours=[clock.Colour.DARK_GREEN, clock.Colour.BLACK, clock.Colour.BRASS])#, gear_colours=[clock.Colour.GOLD])
#plate_colours=[clock.Colour.BLACK, clock.Colour.SILVER, clock.Colour.BRASS]
# show_object(plates.getDrillTemplate(6))

if output_STL:
    motion_works.output_STLs(clock_name, clock_out_dir)
    pendulum.output_STLs(clock_name, clock_out_dir)
    plates.output_STLs(clock_name, clock_out_dir)
    hands.output_STLs(clock_name, clock_out_dir)
    assembly.output_STLs(clock_name, clock_out_dir)

