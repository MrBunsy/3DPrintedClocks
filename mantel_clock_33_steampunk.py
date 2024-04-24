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

from clocks import clock

'''
Nothing particularly new, just had an idea for a clock that would look cool:

- black plates with raised brass edging
- symetric style
- fancy hands - maybe improve my existing fancy hands?
- Unsure of style of dial
- Maybe try the smaller spring and see if that's up to it? (uncertain since the centred second hand clock struggled to make a week)

Maybe one for printables?
'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="mantel_clock_33"
clockOutDir="out"
gearStyle=clock.GearStyle.ARCS
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS

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
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=36, lock=lock, tooth_tip_angle=3,
                                    tooth_base_angle=3, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2)

train = clock.GoingTrain(pendulum_period=2/3, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, chain_wheels=2,
                         runtime_hours=7.5 * 24, support_second_hand=True, escape_wheel_pinion_at_front=True)

moduleReduction=0.9#0.85
train.gen_spring_barrel(pawl_angle=-math.pi/4, click_angle=-math.pi*3/4)
#2/3s
train.set_ratios([[75, 9], [72, 10], [55, 22]])

pendulumSticksOut=10
backPlateFromWall=30

pinion_extensions = {1:12, 2:5}

train.gen_gears(module_size=1, module_reduction=moduleReduction, thick=2.4, thickness_reduction=0.9, chain_wheel_thick=6, pinion_thick_multiplier=3, style=gearStyle,
                powered_wheel_module_increase=1.25, chain_wheel_pinion_thick_multiplier=2, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True,
                pinion_extensions=pinion_extensions, lanterns=[0])
# train.print_info(weight_kg=1.5)
train.get_arbour_with_conventional_naming(0).print_screw_length()

#although I can make really compact motion works now for the dial to be close, this results in a key that looks too short, so extending just so the key might be more stable
motionWorks = clock.MotionWorks(extra_height=10, style=gearStyle, thick=3, compensate_loose_arbour=True, compact=True)#, inset_at_base=clock.MotionWorks.STANDARD_INSET_DEPTH)
#slightly larger allows for the inset and thus dial and hands closer to the plate
# motionWorks.calculateGears(arbourDistance=30)

pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=50, bob_thick=8)

#as printed
# dial = clock.Dial(outside_d=200, bottom_fixing=False, top_fixing=True,style=clock.DialStyle.ARABIC_NUMBERS, font="Arial", outer_edge_style=clock.DialStyle.RING, inner_edge_style=clock.DialStyle.LINES_ARC, seconds_style=clock.DialStyle.CONCENTRIC_CIRCLES)
#if I were to print again
dial = clock.Dial(outside_d=200, bottom_fixing=False, top_fixing=False, style=clock.DialStyle.ARABIC_NUMBERS, font="Gill Sans Medium", font_scale=0.9, font_path="../fonts/GillSans/Gill Sans Medium.otf", outer_edge_style=clock.DialStyle.RING, inner_edge_style=clock.DialStyle.LINES_ARC, seconds_style=clock.DialStyle.CONCENTRIC_CIRCLES)

# dial=None

plates = clock.MantelClockPlates(train, motionWorks, name="Mantel 33", dial=dial, plate_thick=6, screws_from_back=[[True, False],[False,False]], style=clock.PlateStyle.RAISED_EDGING)


# show_object(plates.get_plate_detail(back=True))


hands = clock.Hands(style=clock.HandStyle.BAROQUE, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=dial.outside_d*0.45, thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True,
                    second_length=dial.second_hand_mini_dial_d * 0.45, seconds_hand_thick=1.5, outline_on_seconds=1)


assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum)#weights=[clock.Weight(height=245,diameter=55)]

assembly.show_clock(show_object, hand_colours=[clock.Colour.WHITE, clock.Colour.BLACK], motion_works_colours=[clock.Colour.BRASS],
                    bob_colours=[clock.Colour.GOLD], with_rods=True, with_key=True, ratchet_colour=clock.Colour.BRASS, dial_colours=[clock.Colour.WHITE, clock.Colour.BLACK],
                    plate_colours=[clock.Colour.BLACK, clock.Colour.SILVER, clock.Colour.BRASS])

# show_object(plates.getDrillTemplate(6))

if outputSTL:
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)

