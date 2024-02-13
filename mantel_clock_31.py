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

Continuation of the mantel clocks, but I want to see how small I can make them (now the spring barrel properly calculates its dimensions)
and I'd like to test out the new brocot escapment on the front.

Planning to make it styled on some fancy clocks I've seen, need to find out how large the movement is before I can decide on a style

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="mantel_clock_31"
clockOutDir="out"
gearStyle=clock.GearStyle.CIRCLES
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS


#this much drop is needed to run reliably (I think it's the wiggle room from the m3 rods in 3mm bearings combined with a small escape wheel?) but a 0.25 nozzle is then needed to print well
lift=2
drop=3
lock=2
escapement = clock.BrocotEscapment(drop=drop, lift=lift, teeth=30, lock=lock, wheel_thick=2, diameter=40)
train = clock.GoingTrain(pendulum_length_m=0.20, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, chain_wheels=2,
                         runtime_hours=8 * 24, support_second_hand=False, escape_wheel_pinion_at_front=True)

barrel_gear_thick = 8

moduleReduction=0.9#0.85
#train.gen_spring_barrel(click_angle=-math.pi*0.25)
#smiths ratios but with more teeth on the first pinion (so I can print it with two perimeters, with external perimeter at 0.435 and perimeter at 0.43)
#could swap the wheels round but I don't think I can get the pinions printable with two perimeters at any smaller a module
#[[61, 10], [62, 10]] auto generated but putting here to save time
# train.gen_spring_barrel(pawl_angle=-math.pi*3/4, click_angle=-math.pi/4, ratchet_at_back=False, style=gearStyle, base_thick=barrel_gear_thick,
#                         chain_wheel_ratios=[[61, 10], [62, 10]])#[[66, 10], [76,13]])#, [[61, 10], [62, 10]]

train.gen_spring_barrel(spring=clock.MAINSPRING_183535, pawl_angle=math.pi, click_angle=0, ratchet_at_back=True, style=gearStyle, base_thick=barrel_gear_thick,
                        wall_thick=9)#chain_wheel_ratios=[[67, 10], [61, 10]],

#TODO new option to favour large escape wheel?
# train.calculate_ratios(max_wheel_teeth=70, min_pinion_teeth=9, wheel_min_teeth=50, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction, loud=True)
                      # penultimate_wheel_min_ratio=0.8, allow_integer_ratio=True)
#0.15m pendulum
# train.set_ratios([[58, 9], [58, 11], [50, 11]])
train.set_ratios([[66, 9], [65, 14], [55, 14]])



pendulumSticksOut=10
backPlateFromWall=30

pinion_extensions = {1:25}#, 2:5}

#powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)]
powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), 1]
#[1.6, 1.25]
#endshake is 1.5 by default for mantel plates, so double and some more that for pinion extra length
train.gen_gears(module_size=0.75, module_reduction=moduleReduction, thick=3, thickness_reduction=0.85, chain_wheel_thick=barrel_gear_thick, style=gearStyle,
                powered_wheel_module_sizes=powered_modules, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True,
                pinion_extensions=pinion_extensions, lanterns=[0], pinion_thick_extra=3 + 2, rod_diameters=[12,3,3,2,2,2,2])
# train.print_info(weight_kg=1.5)
train.get_arbour_with_conventional_naming(0).print_screw_length()

#although I can make really compact motion works now for the dial to be close, this results in a key that looks too short, so extending just so the key might be more stable
motionWorks = clock.MotionWorks(extra_height=20, style=gearStyle, thick=3, compensate_loose_arbour=False, compact=True, inset_at_base=clock.MotionWorks.STANDARD_INSET_DEPTH)
#slightly larger allows for the inset and thus dial and hands closer to the plate
motionWorks.calculate_size(arbor_distance=30)

print("motion works widest r: ", motionWorks.get_widest_radius())

pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=50, bob_thick=10)

dial = clock.Dial(outside_d=170, bottom_fixing=True, top_fixing=False, font="Gill Sans Medium", style=clock.DialStyle.ARABIC_NUMBERS, font_scale=0.8, font_path="../fonts/GillSans/Gill Sans Medium.otf", inner_edge_style=clock.DialStyle.LINES_ARC, outer_edge_style=None)




plates = clock.SkeletonCarriageClockPlates(train, motionWorks, name="Mantel 30", dial=dial, plate_thick=6, layer_thick=0.3, escapement_on_front=True, pendulum_sticks_out=20,
                                           vanity_plate_radius=75, motion_works_angle_deg=180+45)


hands = clock.Hands(style=clock.HandStyle.BREGUET, minute_fixing="circle", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True,
                    outline_on_seconds=1, second_hand_centred=True)

assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum)#weights=[clock.Weight(height=245,diameter=55)]

# assembly.get_arbour_rod_lengths()

# show_object(plates.getPlate(back=True))
# show_object(assembly.getClock(with_key=False, with_pendulum=True))
# show_object(plates.get_fixing_screws_cutter())

# show_object(plates.get_plate())
# show_object(plates.get_fixing_screws_cutter())
#, clock.Colour.LIGHTBLUE, clock.Colour.GREEN
if not outputSTL or True:
    assembly.show_clock(show_object, hand_colours=[clock.Colour.WHITE, clock.Colour.BLACK, clock.Colour.RED], motion_works_colours=[clock.Colour.BRASS],
                    bob_colours=[clock.Colour.GOLD], with_rods=False, with_key=True, ratchet_colour=clock.Colour.GOLD, dial_colours=[clock.Colour.WHITE, clock.Colour.BLACK], key_colour=clock.Colour.GOLD)

# show_object(plates.getDrillTemplate(6))

if outputSTL:

    lantern_test = plates.arbors_for_plate[1].get_shapes()["wheel"].intersect(cq.Workplane("XY").circle(plates.arbors_for_plate[1].arbor.pinion.outer_r).extrude(100))

    out = os.path.join(clockOutDir, "{}_lantern_test.stl".format(clockName))
    print("Outputting ", out)
    exporters.export(lantern_test, out)

    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)

