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
from clocks import clock

'''
Clock with a phase complication, which mounts a 3D moon on the top of the clock. 

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_23"
clockOutDir="out"
gearStyle=clock.GearStyle.CIRCLES
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS
second_hand_centred = False
#for period 1.5
drop =1.5
lift =3
lock=1.5
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, tooth_tip_angle=5, tooth_base_angle=4,
                                    style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2)
# lift=4
# drop=2
# lock=2
# escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock,  toothTipAngle=5, toothBaseAngle=4)

train = clock.GoingTrain(pendulum_period=1.5, fourth_wheel=False, escapement=escapement, max_weight_drop=1000, use_pulley=True, chain_at_back=False, chain_wheels=1, runtime_hours=7.5 * 24)#, huygensMaintainingPower=True)

moduleReduction=0.85

train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction)

#think this is promising for good compromise of size
#TODO NEXT CLOCK add 1 mm to cord coil thick (so 15mm) so 25mm screws will fit properly!
train.gen_cord_wheels(ratchet_thick=6, rod_metric_thread=4, cord_thick=1, cord_coil_thick=14, style=gearStyle, use_key=True, prefered_diameter=29, loose_on_rod=False, prefer_small=True)
# train.genChainWheels2(clock.COUSINS_1_5MM_CHAIN, ratchetThick=6, arbourD=4, loose_on_rod=False, prefer_small=True, preferedDiameter=25, fixing_screws=clock.MachineScrew(3, countersunk=True),ratchetOuterThick=6)
# train.genChainWheels2(clock.COUSINS_1_5MM_CHAIN, ratchetThick=6, arbourD=4, loose_on_rod=False, prefer_small=True, preferedDiameter=30, fixing_screws=clock.MachineScrew(3, countersunk=True),ratchetOuterThick=6)



pendulumSticksOut=10
backPlateFromWall=40

train.gen_gears(module_size=1.1, module_reduction=moduleReduction, thick=2.4, thickness_reduction=2 / 2.4, chain_wheel_thick=4, pinion_thick_multiplier=3, style=gearStyle,
                powered_wheel_module_increase=1, chain_wheel_pinion_thick_multiplier=2, pendulum_fixing=pendulumFixing)
train.print_info(weight_kg=3)
train.print_info(weight_kg=2.5)
train.print_info(weight_kg=1)
train.print_info(weight_kg=2)
train.get_arbour_with_conventional_naming(0).print_screw_length()

#tweaking angle slightly so that the second gear doesn't line up with an arbor that's between the plates
moon_complication = clock.MoonPhaseComplication3D(gear_style=gearStyle, first_gear_angle_deg=205, on_left=False, bevel_module=1.2)

#not inset at base as there's not enough space for the moon complication to fit behind it
motionWorks = clock.MotionWorks(extra_height=25, style=gearStyle, thick=3, compensate_loose_arbour=False, compact=True, moon_complication=moon_complication)


#TODO try out larger pinions on the motion works - it'll be a fiddle to slot together at the moment
moon_complication.set_motion_works_sizes(motionWorks)
#slightly larger allows for the inset and thus dial and hands closer to the plate
# motionWorks.calculateGears(arbourDistance=30)

pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=80, bob_thick=10)

dial = clock.Dial(outside_d=200, bottom_fixing=True, top_fixing=False, style=clock.DialStyle.DOTS, seconds_style=clock.DialStyle.LINES_ARC)

plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=9, back_plate_thick=11, pendulum_sticks_out=pendulumSticksOut, name="Wall 23", style=clock.ClockPlateStyle.COMPACT,
                                 heavy=True, extra_heavy=False, pendulum_fixing=pendulumFixing, pendulum_at_front=False,
                                 back_plate_from_wall=backPlateFromWall, fixing_screws=clock.MachineScrew(metric_thread=4, countersunk=True),
                                 chain_through_pillar_required=True, pillars_separate=True, dial=dial, bottom_pillars=1, moon_complication=moon_complication,
                                 second_hand=second_hand_centred, centred_second_hand=second_hand_centred, motion_works_angle_deg = 225, endshake=1.75)#, screws_from_back=[True, False])

pulley = clock.BearingPulley(diameter=train.powered_wheel.diameter, bearing=clock.get_bearing_info(4), wheel_screws=clock.MachineScrew(2, countersunk=True, length=8))
print("pulley needs screws {} {}mm and {} {}mm".format(pulley.screws, pulley.getTotalThick(), pulley.hook_screws, pulley.getHookTotalThick()))

hands = clock.Hands(style=clock.HandStyle.MOON, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True, second_hand_centred=second_hand_centred)#, secondLength=dial.second_hand_mini_dial_d*0.45, seconds_hand_thick=1.5)

assembly = clock.Assembly(plates, hands=hands, timeSeconds=30, pendulum=pendulum)

# show_object(assembly.getClock(with_key=True, with_pendulum=True))
assembly.show_clock(show_object, with_rods=True, plate_colour=clock.Colour.DARKGREY, dial_colours=[clock.Colour.WHITE, clock.Colour.PINK])

assembly.get_arbour_rod_lengths()
if outputSTL:
    pulley.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    moon_complication.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)