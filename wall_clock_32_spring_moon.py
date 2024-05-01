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

from clocks import clock

'''

This is based on mantel_clock_31, but bigger

Plan is a circular wall mounted clock with short pendulum and mini moon complication in a mini dial like the second hand 


'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_32"
clockOutDir="out"
gearStyle=clock.GearStyle.CIRCLES
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS


#this much drop is needed to run reliably (I think it's the wiggle room from the m3 rods in 3mm bearings combined with a small escape wheel?) but a 0.25 nozzle is then needed to print well
lift=2
drop=3
lock=2
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=36, lock=lock, tooth_tip_angle=3,
                                    tooth_base_angle=3, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2)
train = clock.GoingTrain(pendulum_period=1, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, chain_wheels=2,
                         runtime_hours=8 * 24, support_second_hand=False, escape_wheel_pinion_at_front=False)

barrel_gear_thick = 8

moduleReduction=0.95#0.85
#train.gen_spring_barrel(click_angle=-math.pi*0.25)
#smiths ratios but with more teeth on the first pinion (so I can print it with two perimeters, with external perimeter at 0.435 and perimeter at 0.43)
#could swap the wheels round but I don't think I can get the pinions printable with two perimeters at any smaller a module
#[[61, 10], [62, 10]] auto generated but putting here to save time
# train.gen_spring_barrel(pawl_angle=-math.pi*3/4, click_angle=-math.pi/4, ratchet_at_back=False, style=gearStyle, base_thick=barrel_gear_thick,
#                         chain_wheel_ratios=[[61, 10], [62, 10]])#[[66, 10], [76,13]])#, [[61, 10], [62, 10]]

train.gen_spring_barrel(spring=clock.SMITHS_EIGHT_DAY_MAINSPRING, pawl_angle=math.pi, click_angle=0, ratchet_at_back=True, style=gearStyle, base_thick=barrel_gear_thick,
                        wall_thick=9, chain_wheel_ratios=[[64, 10], [60, 11]])

#TODO new option to favour large escape wheel?
# train.calculate_ratios(max_wheel_teeth=90, min_pinion_teeth=9, wheel_min_teeth=55, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction, loud=True)
                      # penultimate_wheel_min_ratio=0.8, allow_integer_ratio=True)
#1s period
train.set_ratios([[65, 12], [60, 14], [56, 13]])


pendulumSticksOut=10
backPlateFromWall=30
dial_d = 205
dial_width=25

#was 25, extending to 32 was meant to move the pinion closer to the edge so there's less wobble, but it appears to have made the plates slightly wider
#so reprints are a mix of old and new STLs...
pinion_extensions = {1:5,3:5} #{1:25}

#powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)]
powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), 1.2]
#[1.6, 1.25]
#endshake is 1.5 by default for mantel plates, so double and some more that for pinion extra length
train.gen_gears(module_size=1, module_reduction=moduleReduction, thick=3, thickness_reduction=0.85, chain_wheel_thick=barrel_gear_thick, style=gearStyle,
                powered_wheel_module_sizes=powered_modules, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True,
                pinion_extensions=pinion_extensions, lanterns=[0], pinion_thick_extra=3 + 3)#, rod_diameters=[12,3,3,2,2,2,2,2])
# train.print_info(weight_kg=1.5)#
moon_radius=13
train.get_arbour_with_conventional_naming(0).print_screw_length()
moon_complication = clock.MoonPhaseComplication3D(gear_style=gearStyle, first_gear_angle_deg=205, on_left=False, bevel_module=1.1, module=0.9, moon_radius=moon_radius,
                                                  bevel_angle_from_hands_deg=90, moon_from_hands=(dial_d/2 - dial_width) - moon_radius - 5, moon_inside_dial=True)
# moon_complication = None
#although I can make really compact motion works now for the dial to be close, this results in a key that looks too short, so extending just so the key might be more stable
motionWorks = clock.MotionWorks(extra_height=23, style=gearStyle, thick=3, compensate_loose_arbour=False, compact=True,
                                moon_complication=moon_complication)#, inset_at_base=clock.MotionWorks.STANDARD_INSET_DEPTH
#slightly larger allows for the inset and thus dial and hands closer to the plate
motionWorks.calculate_size(arbor_distance=30)
moon_complication.set_motion_works_sizes(motionWorks)
print("motion works widest r: ", motionWorks.get_widest_radius())
# # show_object(moon_complication.get_arbor_shape(3))
# show_object(motionWorks.get_assembled())
# show_object(moon_complication.get_assembled())


pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=50, bob_thick=10)

# dial = clock.Dial(outside_d=180, bottom_fixing=True, top_fixing=False, font="Gill Sans Medium", style=clock.DialStyle.ROMAN_NUMERALS,
#                   font_scale=0.75, font_path="../fonts/GillSans/Gill Sans Medium.otf", inner_edge_style=clock.DialStyle.RING, outer_edge_style=clock.DialStyle.LINES_ARC,
#                   dial_width=20)


dial = clock.Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=clock.DialStyle.DOTS, dial_width=dial_width)
plates = clock.RoundClockPlates(train, motionWorks, name="Wall 32", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=25,
                                motion_works_angle_deg=180+45, leg_height=0, fully_round=True, style=clock.PlateStyle.RAISED_EDGING, fancy_pillars=True,
                                moon_complication=moon_complication, second_hand=False)


hands = clock.Hands(style=clock.HandStyle.MOON, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=False,
                    outline_on_seconds=0, second_hand_centred=False)
# show_object(plates.get_fixing_screws_cutter())
assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum)#weights=[clock.Weight(height=245,diameter=55)]

assembly.get_arbour_rod_lengths()
plates.get_rod_lengths()

# show_object(plates.getPlate(back=True))
# show_object(assembly.getClock(with_key=False, with_pendulum=True))
# show_object(plates.get_fixing_screws_cutter())

# show_object(plates.get_plate())
# show_object(plates.get_fixing_screws_cutter())
#, clock.Colour.LIGHTBLUE, clock.Colour.GREEN
if not outputSTL or True:
    assembly.show_clock(show_object, hand_colours=[clock.Colour.WHITE, clock.Colour.BLACK], motion_works_colours=[clock.Colour.GOLD],
                        bob_colours=[clock.Colour.SILVER], with_rods=True, with_key=True, ratchet_colour=clock.Colour.GOLD,
                        dial_colours=[clock.Colour.DARKBLUE, clock.Colour.WHITE], key_colour=clock.Colour.GOLD,
                        plate_colours=[clock.Colour.DARK_GREEN, clock.Colour.BLACK, clock.Colour.BRASS])

# show_object(plates.getDrillTemplate(6))

if outputSTL:

    moon_complication.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)

