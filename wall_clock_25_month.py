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
import clocks as clock

'''
Experiment to see if I have enough power to get a month runtime on a clock

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_25"
clockOutDir="out"
gearStyle=clock.GearStyle.BENT_ARMS5
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

#for period 1.5, 40 teeth
# drop =1.5
# lift =3
# lock=1.5
# # 30 teeth
# lift=2
# drop=3
# lock=2
# #increasing run only for asthetic reasons
# escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL)

escapement = clock.AnchorEscapement.get_with_45deg_pallets(teeth=30, drop_deg=2.75, lock_deg=1.5, diameter=45, force_diameter=True, anchor_thick=10)

train = clock.GoingTrain(pendulum_period=2.0, wheels=3, escapement=escapement, max_weight_drop=1500, use_pulley=True, chain_at_back=False,
                         chain_wheels=2, runtime_hours=32 * 24, support_second_hand=False)#, huygensMaintainingPower=True)

moduleReduction=0.9

train.calculate_ratios(max_wheel_teeth=120, min_pinion_teeth=12, wheel_min_teeth=70, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction, loud=True, favour_smallest=True)
# train.calculateRatios(max_wheel_teeth=70, min_pinion_teeth=12, wheel_min_teeth=50, pinion_max_teeth=15, max_error=0.1, moduleReduction=moduleReduction, loud=True)
# train.setRatios( [[72, 10], [75, 9], [60, 27]])

train.gen_cord_wheels(ratchet_thick=8, rod_metric_thread=4, cord_thick=2, cord_coil_thick=14, style=gearStyle, use_key=True, prefered_diameter=35, loose_on_rod=False, prefer_small=True,
                      min_wheel_teeth=70, traditional_ratchet=True, cap_diameter=65, ratchet_diameter=35)
#think this is promising for good compromise of size
#train.genCordWheels(ratchetThick=6, rodMetricThread=4, cordThick=1, cordCoilThick=14, style=gearStyle, useKey=True, preferedDiameter=29, loose_on_rod=False, prefer_small=True)
# train.genChainWheels2(clock.COUSINS_1_5MM_CHAIN, ratchetThick=6, arbourD=4, loose_on_rod=False, prefer_small=True, preferedDiameter=25, fixing_screws=clock.MachineScrew(3, countersunk=True),ratchetOuterThick=6)

train.calculate_powered_wheel_ratios(pinion_min=10, pinion_max=12, wheel_min=50, wheel_max=120)

pendulumSticksOut=10
backPlateFromWall=30

powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2)]

lanterns=[0, 1]
pinion_extensions = {0:2}
#want to make second powered wheel have chunkier rod, but really struggling to get the rest of the train to fit without a crazy small module.
#let's see if m3 is enough
rod_diameters = [4,3,3,3,3,3]

train.gen_gears(module_size=0.675, module_reduction=moduleReduction, thick=2.4, thickness_reduction=0.9, powered_wheel_thicks=[8,5], pinion_thick_extra=5, style=gearStyle,
                powered_wheel_pinion_thick_multiplier=1.5, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True,
                powered_wheel_module_sizes=powered_modules, lanterns=lanterns, pinion_extensions=pinion_extensions, rod_diameters=rod_diameters)
train.print_info(weight_kg=6)
train.get_arbour_with_conventional_naming(0).print_screw_length()

#although I can make really compact motion works now for the dial to be close, this results in a key that looks too short, so extending just so the key might be more stable
motionWorks = clock.MotionWorks(extra_height=10, style=gearStyle, thick=3, compensate_loose_arbour=True, compact=True)#, inset_at_base=clock.MotionWorks.STANDARD_INSET_DEPTH)
#slightly larger allows for the inset and thus dial and hands closer to the plate
motionWorks.calculate_size(arbor_distance=30)

pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=50, bob_thick=8)

# dial = clock.Dial(outside_d=180, bottom_fixing=True, top_fixing=True, style=clock.DialStyle.ROMAN, seconds_style=clock.DialStyle.CONCENTRIC_CIRCLES)
# dial = None
#same as mantle clock 29
# dial = clock.Dial(outside_d=190, bottom_fixing=True, top_fixing=False, style=clock.DialStyle.ARABIC_NUMBERS, font="Miriam Mono CLM", inner_edge_style=None,
#                   outer_edge_style=clock.DialStyle.DOTS, seconds_style=clock.DialStyle.CONCENTRIC_CIRCLES, pillar_style=clock.PillarStyle.BARLEY_TWIST)
dial = clock.Dial(outside_d=192.5, style=clock.DialStyle.LINES_INDUSTRIAL, pillar_style=clock.PillarStyle.BARLEY_TWIST, top_fixing=False)

plaque = clock.Plaque(text_lines=["M25#0 {:.1f}cm".format(train.pendulum_length_m * 100), "L.Wallin 2024"])


#dial diameter of 250 (printed in two parts) looks promising for second hand, 205 without
# plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=9, back_plate_thick=10, pendulum_sticks_out=pendulumSticksOut, name="Wall 24", gear_train_layout=clock.GearTrainLayout.COMPACT,
#                                  heavy=True, extra_heavy=True, pendulum_fixing=pendulumFixing, pendulum_at_front=False,
#                                  back_plate_from_wall=backPlateFromWall, fixing_screws=clock.MachineScrew(metric_thread=4, countersunk=True),
#                                  chain_through_pillar_required=False, pillars_separate=True, dial=dial, bottom_pillars=1, motion_works_angle_deg=360 - 35,
#                                  allow_bottom_pillar_height_reduction=False, endshake=1.5, second_hand=False, escapement_on_front=True, compact_zigzag=True)
plates = clock.RoundClockPlates(train, motionWorks, second_hand=False, style=clock.PlateStyle.RAISED_EDGING, pillar_style=clock.PillarStyle.BARLEY_TWIST, fully_round=True,
                                leg_height=0, plaque=plaque, dial=dial, motion_works_angle_deg=180+30, escapement_on_front=True, name="Clock 25", split_detailed_plate=True,
                                plate_thick=10)


# hands = clock.Hands(style=clock.HandStyle.SPADE, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
#                     length=plates.dial_diameter*0.45, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=plates.second_hand_mini_dial_d*0.45)
hands = clock.Hands(style=clock.HandStyle.INDUSTRIAL, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motionWorks.minute_hand_slot_height, outline=0, outline_same_as_body=False, chunky=True, second_length=20, seconds_hand_thick=1.5)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)

pulley = clock.BearingPulley(diameter=train.powered_wheel.diameter, bearing=clock.get_bearing_info(4), wheel_screws=clock.MachineScrew(2, countersunk=True, length=8))
print("pulley needs screws {} {}mm and {} {}mm".format(pulley.screws, pulley.getTotalThick(), pulley.hook_screws, pulley.getHookTotalThick()))


assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pulley = pulley, pendulum=pendulum)#, timeHours=12, timeMins=0)#weights=[clock.Weight(height=245,diameter=55)]

# show_object(plates.getPlate(back=True))
# show_object(assembly.getClock(with_key=False, with_pendulum=True))
#motion_works_colours=[clock.Colour.GREEN, clock.Colour.GREEN, clock.Colour.LIGHTBLUE]
assembly.show_clock(show_object, motion_works_colours=[clock.Colour.BRASS],
                    bob_colours=[clock.Colour.PURPLE], plate_colours=[clock.Colour.DARKBLUE, clock.Colour.BRASS, clock.Colour.BRASS, clock.Colour.BRASS],
                    hand_colours=[clock.Colour.RED], with_rods=True)

# show_object(plates.getDrillTemplate(6))

if outputSTL:
    #
    #
    # train.output_STLs(clockName,clockOutDir)
    plaque.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    pulley.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)


    # clock.outputSTLMultithreaded([train, motionWorks,pendulum,dial,plates,hands,pulley,assembly], clockName, clockOutDir)
