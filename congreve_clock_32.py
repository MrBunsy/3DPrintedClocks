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


'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="congreve_clock_32"
clockOutDir="out"
gearStyle=clock.GearStyle.CIRCLES
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS


#this much drop is needed to run reliably (I think it's the wiggle room from the m3 rods in 3mm bearings combined with a small escape wheel?) but a 0.25 nozzle is then needed to print well
lift=2
drop=3
lock=2
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=36, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=3,
                                    toothBaseAngle=3, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, wheelThick=2)
#escape wheel this way around allows for a slightly larger diameter
train = clock.GoingTrain(pendulum_period=2/3, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, chain_wheels=2,
                         runtime_hours=7 * 24, support_second_hand=True, escape_wheel_pinion_at_front=False)

barrel_gear_thick = 8

moduleReduction=0.9#0.85
#train.gen_spring_barrel(click_angle=-math.pi*0.25)
#smiths ratios but with more teeth on the first pinion (so I can print it with two perimeters, with external perimeter at 0.435 and perimeter at 0.43)
#could swap the wheels round but I don't think I can get the pinions printable with two perimeters at any smaller a module
#[[61, 10], [62, 10]] auto generated but putting here to save time
train.gen_spring_barrel(pawl_angle=-math.pi*3/4, click_angle=-math.pi/4, ratchet_at_back=False, style=gearStyle, base_thick=barrel_gear_thick,
                        chain_wheel_ratios=[[61, 10], [62, 10]])#[[66, 10], [76,13]])#, [[61, 10], [62, 10]]
# train.calculate_ratios(max_wheel_teeth=80, min_pinion_teeth=9, wheel_min_teeth=70, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction, loud=True,
#                       penultimate_wheel_min_ratio=0.8, allow_integer_ratio=True)
train.set_ratios([[75, 9], [72, 10], [60, 24]])



pendulumSticksOut=10
backPlateFromWall=30

pinion_extensions = {1:15}#, 2:5}

#powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)]
powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), 1.25]
#[1.6, 1.25]
#endshake is 1.5 by default for mantel plates, so double and some more that for pinion extra length
train.gen_gears(module_size=0.9, module_reduction=moduleReduction, thick=3, thickness_reduction=0.85, chain_wheel_thick=barrel_gear_thick, style=gearStyle,
                powered_wheel_module_sizes=powered_modules, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True,
                pinion_extensions=pinion_extensions, lanterns=[0], pinion_thick_extra=3 + 2)
# train.print_info(weight_kg=1.5)
train.get_arbour_with_conventional_naming(0).print_screw_length()

#although I can make really compact motion works now for the dial to be close, this results in a key that looks too short, so extending just so the key might be more stable
motionWorks = clock.MotionWorks(extra_height=0, style=gearStyle, thick=3, compensate_loose_arbour=False, compact=True, bearing=clock.get_bearing_info(3))#, inset_at_base=clock.MotionWorks.STANDARD_INSET_DEPTH)
#slightly larger allows for the inset and thus dial and hands closer to the plate
# motionWorks.calculateGears(arbourDistance=30)

pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=50, bob_thick=10)
#140 looks good, but might be easier to assemble if it didn't overlap the motion works?
dial = clock.Dial(outside_d=160, bottom_fixing=False, top_fixing=True, style=clock.DialStyle.ARABIC_NUMBERS, font="Comic Sans MS", outer_edge_style=clock.DialStyle.CONCENTRIC_CIRCLES,
                  inner_edge_style=clock.DialStyle.RING, seconds_style=clock.DialStyle.CONCENTRIC_CIRCLES)
# dial=None

plates = clock.MantelClockPlates(train, motionWorks, name="Congreve 32", dial=dial, plate_thick=6,
                                 motion_works_angle_deg=180+50, centred_second_hand=True, layer_thick=0.4   )


# hands = clock.Hands(style=clock.HandStyle.SPADE, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
#                     length=plates.dial_diameter*0.45, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=plates.second_hand_mini_dial_d*0.45)
#would like sword, need to fix second hand outline for it
hands = clock.Hands(style=clock.HandStyle.SIMPLE_ROUND, minuteFixing="circle", minuteFixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motionWorks.minute_hand_slot_height, outline=1, outlineSameAsBody=False, chunky=True,
                    outline_on_seconds=1, second_hand_centred=True)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)


assembly = clock.Assembly(plates, hands=hands, timeSeconds=30, pendulum=pendulum)#weights=[clock.Weight(height=245,diameter=55)]

assembly.get_arbour_rod_lengths()

# show_object(plates.getPlate(back=True))
# show_object(assembly.getClock(with_key=False, with_pendulum=True))

# show_object(plates.get_plate())
# show_object(plates.get_fixing_screws_cutter())
#, clock.Colour.LIGHTBLUE, clock.Colour.GREEN
if not outputSTL:
    assembly.show_clock(show_object, hand_colours=[clock.Colour.WHITE, clock.Colour.BLACK, clock.Colour.RED], motion_works_colours=[clock.Colour.BRASS],
                    bob_colours=[clock.Colour.GOLD], with_rods=True, with_key=True, ratchet_colour=clock.Colour.GOLD, dial_colours=[clock.Colour.WHITE, clock.Colour.BLACK], key_colour=clock.Colour.GOLD)

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

