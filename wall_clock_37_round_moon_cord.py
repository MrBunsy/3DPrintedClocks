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

Thought I'd do a quick experiment to see what clock 32 looked like weight driven.

current answer: struggling to find a good gear ratio that works. can be done with very large barrel and short drop.

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_37"
clockOutDir="out"
gearStyle=clock.GearStyle.CIRCLES
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

#after a huge amount of faffing about, the problem was the bearings, not the escapement. So I've used the new auto-calculated efficient escapement for a retrofit.
escapement = clock.AnchorEscapement.get_with_45deg_pallets(teeth=30, drop_deg=2.75, lock_deg=1.5, wheel_thick=2.5)

power = clock.CordWheel(ratchet_thick=6, rod_metric_size=4, cord_thick=1, thick=15, style=gearStyle, use_key=True, diameter=50, loose_on_rod=False)

# escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock,style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2.5, type=clock.EscapementType.DEADBEAT, tooth_tip_angle=6, tooth_base_angle=4)
train = clock.GoingTrain(pendulum_period=1, wheels=4, escapement=escapement, max_weight_drop=500, use_pulley=True, chain_at_back=False, chain_wheels=2,
                         runtime_hours=8 * 24, support_second_hand=False, escape_wheel_pinion_at_front=True, powered_wheel=power)

barrel_gear_thick = 5#8

moduleReduction=0.95#0.85

#wall thick of 9 seemed fine, but I want it to be consistent with the arbor
#larger barrel wheel actually works out at a smaller plate than having a larger intermediate wheel
# train.gen_spring_barrel(spring=clock.SMITHS_EIGHT_DAY_MAINSPRING, pawl_angle=math.pi, click_angle=-math.pi/2, ratchet_at_back=True, style=gearStyle, base_thick=barrel_gear_thick,
#                         wall_thick=10, chain_wheel_ratios=[[64, 10], [64, 10]], extra_barrel_height=1.5)
# train.gen_cord_wheels(ratchet_thick=6, rod_metric_thread=4, cord_thick=1, cord_coil_thick=15, style=gearStyle, use_key=True, prefered_diameter=60, loose_on_rod=False, prefer_small=True)

train.calculate_powered_weight_wheel_info()
train.calculate_powered_wheel_ratios(prefer_small=True, wheel_min=20, prefer_large_second_wheel=False)
'''
[[61, 10], [83, 10]]
spring_wound_coils: 23.53661753519562 spring unwound coils: 12.838105212872968, max theoretical barrel turns: 10.698512322322653
Over a runtime of 168.0hours the spring barrel will make 3.3 full rotations which is 31.0% of the maximum number of turns (10.7) and will take 5.0 key turns to wind back up
'''

# train.calculate_ratios(max_wheel_teeth=80, min_pinion_teeth=10, wheel_min_teeth=55, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction, loud=True)
#1s period with 36 teeth
# train.set_ratios([[65, 12], [60, 14], [56, 13]])
#1s period with 30 teeth
#[[65, 10], [60, 14], [56, 13]]
train.set_ratios([[65, 14], [60, 13], [56, 10]])

pendulumSticksOut=10
backPlateFromWall=30
dial_d = 205
dial_width=25

pinion_extensions = {0:1, 1:15, 2:10,3:18}

#powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)]
powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5, leaves=train.chain_wheel_ratios[0][1]),
                    # 1.2
                    clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2)
                   ]
#[1.6, 1.25]
#endshake is 1.5 by default for mantel plates, so double and some more that for pinion extra length
#module_sizes=[1, 0.95, 0.95]
train.gen_gears(module_sizes=[0.9, 0.85, 0.85], module_reduction=moduleReduction, thick=3, thickness_reduction=0.85, style=gearStyle,
                powered_wheel_module_sizes=powered_modules, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True,
                pinion_extensions=pinion_extensions, lanterns=[0, 1], pinion_thick_extra=5, powered_wheel_pinion_thick_multiplier=1.875, powered_wheel_thicks=[barrel_gear_thick, 4])
train.print_info(for_runtime_hours=24*7, weight_kg=2.5)
moon_radius=13
train.get_arbour_with_conventional_naming(0).print_screw_length()
moon_complication = clock.MoonPhaseComplication3D(gear_style=gearStyle, first_gear_angle_deg=205, on_left=False, bevel_module=1.1, module=0.9, moon_radius=moon_radius,
                                                  bevel_angle_from_hands_deg=90, moon_from_hands=(dial_d/2 - dial_width) - moon_radius - 5, moon_inside_dial=True)
#no need to make inset, we've got lots of space here with the moon complication
motion_works = clock.MotionWorks(extra_height=22, style=gearStyle, thick=3, compensate_loose_arbour=False, compact=True,
                                 moon_complication=moon_complication, cannon_pinion_to_hour_holder_gap_size=0.6)
# balance out the moon complication by making the motion works a bit bigger
motion_works.calculate_size(arbor_distance=30)
moon_complication.set_motion_works_sizes(motion_works)
print("motion works widest r: ", motion_works.get_widest_radius())
pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=60, bob_thick=12.5)

plaque = clock.Plaque(text_lines=["M32#1 {:.1f}cm L.Wallin 2024".format(train.pendulum_length_m * 100), "Insert Message Here"])


dial = clock.Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=clock.DialStyle.DOTS, dial_width=dial_width, pillar_style=clock.PillarStyle.BARLEY_TWIST)
plates = clock.RoundClockPlates(train, motion_works, name="Wall 32b", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=20,
                                motion_works_angle_deg=180+45, leg_height=0, fully_round=True, style=clock.PlateStyle.RAISED_EDGING, pillar_style=clock.PillarStyle.BARLEY_TWIST,
                                moon_complication=moon_complication, second_hand=False, standoff_pillars_separate=True, plaque=plaque)

print("plate radius: ", plates.radius)
hands = clock.Hands(style=clock.HandStyle.MOON, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=False,
                    outline_on_seconds=0, second_hand_centred=False)
# show_object(plates.get_fixing_screws_cutter())
assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum)#weights=[clock.Weight(height=245,diameter=55)]

assembly.get_arbor_rod_lengths()
plates.get_rod_lengths()

# show_object(moon_complication.get_assembled())

# show_object(plates.getPlate(back=True))
# show_object(assembly.getClock(with_key=False, with_pendulum=True))
# show_object(plates.get_fixing_screws_cutter())

# show_object(plates.get_plate())
# show_object(plates.get_fixing_screws_cutter())
#, clock.Colour.LIGHTBLUE, clock.Colour.GREEN
if not outputSTL or True:
    assembly.show_clock(show_object, hand_colours=[clock.Colour.WHITE, clock.Colour.DARKBLUE], motion_works_colours=[clock.Colour.BRASS],
                        bob_colours=[clock.Colour.SILVER], with_rods=True, with_key=True, ratchet_colour=clock.Colour.GOLD,
                        dial_colours=[clock.Colour.BLUE, clock.Colour.WHITE], key_colour=clock.Colour.DARKBLUE,
                        plate_colours=[clock.Colour.DARK_GREEN, clock.Colour.BLACK, clock.Colour.BRASS])

# show_object(plates.getDrillTemplate(6))

if outputSTL:

    # moon_complication.output_STLs(clockName, clockOutDir)
    motion_works.output_STLs(clockName, clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)

