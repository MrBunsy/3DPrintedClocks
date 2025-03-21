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
Tony the Clock from Don't Hug Me I'm Scared

If I ever produce another version of this clock, consider putting the pendulum on the front of the plates (but still behind the dail) to improve visibility of the bow tie

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="tony"
clockOutDir="out"
gearStyle=clock.GearStyle.ARCS2
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

#for period 1.5
# drop =1.5
# lift =3
# lock=1.5
lift=4
drop=2
lock=2
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock, tooth_tip_angle=5, tooth_base_angle=4, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL)
# lift=4
# drop=2
# lock=2
# escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock,  toothTipAngle=5, toothBaseAngle=4)
#pendulum_length=0.225
train = clock.GoingTrain(pendulum_length_m=0.225, fourth_wheel=True, escapement=escapement, max_weight_drop=1400, use_pulley=False, chain_at_back=False, powered_wheels=1, runtime_hours=7.25 * 24)#, huygensMaintainingPower=True)

moduleReduction=1#0.85

# train.calculateRatios(max_wheel_teeth=150, min_pinion_teeth=10, wheel_min_teeth=50, pinion_max_teeth=20, max_error=0.1, moduleReduction=moduleReduction, loud=True)
# train.calculateRatios(max_wheel_teeth=80, min_pinion_teeth=10, wheel_min_teeth=50, pinion_max_teeth=20, max_error=0.1, moduleReduction=moduleReduction, loud=True)
#for 0.15m pendulum:
# train.setRatios( [[77, 10], [62, 10], [55, 17]])
#for 0.2m pendulum:
# train.setRatios( [[76, 10], [66, 14], [56, 15]])
#for 0.21m pendulum:
# train.setRatios([[68, 11], [61, 12], [54, 13]])
#for 0.22m pendulum:
# train.setRatios( [[77, 10], [60, 16], [53, 12]])
#for 0.225
train.set_ratios([[68, 10], [60, 11], [51, 15]])
#for 0.25m pendulum:
# train.setRatios([[73, 10], [59, 10], [50, 18]])
#1s pendulum:
# train.setRatios([[66, 10], [56, 11], [50, 14]])

'''
power wheel ratios [{'ratio': 7.7272727272727275, 'pair': [85, 11], 'error': 0.04742606790799542, 'teeth': 85}, {'ratio': 7.818181818181818, 'pair': [86, 11], 'error': 0.04348302300109541, 'teeth': 86}, {'ratio': 7.75, 'pair': [93, 12], 'error': 0.024698795180722932, 'teeth': 93}, {'ratio': 7.833333333333333, 'pair': [94, 12], 'error': 0.058634538152610105, 'teeth': 94}, {'ratio': 7.769230769230769, 'pair': [101, 13], 'error': 0.00546802594995377, 'teeth': 101}, {'ratio': 7.6923076923076925, 'pair': [100, 13], 'error': 0.08239110287303042, 'teeth': 100}, {'ratio': 7.846153846153846, 'pair': [102, 13], 'error': 0.07145505097312288, 'teeth': 102}, {'ratio': 7.785714285714286, 'pair': [109, 14], 'error': 0.011015490533562655, 'teeth': 109}, {'ratio': 7.714285714285714, 'pair': [108, 14], 'error': 0.06041308089500852, 'teeth': 108}, {'ratio': 7.857142857142857, 'pair': [110, 14], 'error': 0.08244406196213383, 'teeth': 110}, {'ratio': 7.8, 'pair': [117, 15], 'error': 0.02530120481927689, 'teeth': 117}, {'ratio': 7.733333333333333, 'pair': [116, 15], 'error': 0.04136546184738954, 'teeth': 116}, {'ratio': 7.75, 'pair': [124, 16], 'error': 0.024698795180722932, 'teeth': 124}, {'ratio': 7.866666666666666, 'pair': [118, 15], 'error': 0.09196787148594332, 'teeth': 118}, {'ratio': 7.8125, 'pair': [125, 16], 'error': 0.03780120481927707, 'teeth': 125}, {'ratio': 7.6875, 'pair': [123, 16], 'error': 0.08719879518072293, 'teeth': 123}, {'ratio': 7.764705882352941, 'pair': [132, 17], 'error': 0.009992912827781808, 'teeth': 132}, {'ratio': 7.705882352941177, 'pair': [131, 17], 'error': 0.0688164422395463, 'teeth': 131}, {'ratio': 7.823529411764706, 'pair': [133, 17], 'error': 0.04883061658398269, 'teeth': 133}, {'ratio': 7.777777777777778, 'pair': [140, 18], 'error': 0.003078982597054747, 'teeth': 140}, {'ratio': 7.722222222222222, 'pair': [139, 18], 'error': 0.05247657295850061, 'teeth': 139}, {'ratio': 7.833333333333333, 'pair': [141, 18], 'error': 0.058634538152610105, 'teeth': 141}, {'ratio': 7.7894736842105265, 'pair': [148, 19], 'error': 0.014774889029803617, 'teeth': 148}, {'ratio': 7.7368421052631575, 'pair': [147, 19], 'error': 0.03785668991756541, 'teeth': 147}, {'ratio': 7.684210526315789, 'pair': [146, 19], 'error': 0.09048826886493355, 'teeth': 146}, {'ratio': 7.842105263157895, 'pair': [149, 19], 'error': 0.06740646797717176, 'teeth': 149}]
{'time': 3600.0445681246924, 'train': [[76, 10], [66, 14], [56, 15]], 'error': 0.04456812469243232, 'ratio': 133.76, 'teeth': 198, 'weighting': 198.0}
'''

#think this is promising for good compromise of size
# train.genCordWheels(ratchetThick=4, rodMetricThread=4, cordThick=1, cordCoilThick=14, style=gearStyle, useKey=True, preferedDiameter=29, loose_on_rod=False, prefer_small=True)
#fixing chain wheel to the rod and having the wheel loose (with a steel rod) as this worked really well with the cord wheel and i suspect it will with the chain wheel too
train.gen_chain_wheels2(clock.COUSINS_1_5MM_CHAIN, ratchetThick=6, arbourD=4, loose_on_rod=False, prefer_small=True, preferedDiameter=30, fixing_screws=clock.MachineScrew(3, countersunk=True), ratchetOuterThick=6)

pendulumSticksOut=15

#0.9 with no module reduction produces gears that slice perfectly
#0.8 looks printable, but with only one perimeter in the teeth - will they be strong enough? Will the escapement work?
train.gen_gears(module_size=0.8, module_reduction=moduleReduction, thick=2.4, thickness_reduction=0.9, powered_wheel_thick=4, pinion_thick_multiplier=3, style=gearStyle,
                powered_wheel_module_increase=1, powered_wheel_pinion_thick_multiplier=2, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True)
train.print_info(weight_kg=1.5)
train.get_arbor_with_conventional_naming(0).print_screw_length()


motionWorks = clock.MotionWorks(extra_height=25, style=gearStyle, thick=3, compensate_loose_arbour=False, compact=True)#, inset_at_base=clock.MotionWorks.STANDARD_INSET_DEPTH)
# motionWorks.calculateGears(arbourDistance=30)

pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=60, bob_thick=10)

dial = clock.Dial(outside_d=200, bottom_fixing=True, top_fixing=True, style=clock.DialStyle.TONY_THE_CLOCK, detail_thick=clock.LAYER_THICK*3)

#using non-countersunk screws and screwing from front so I can build this with threaded rod before the long screws are delivered
plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=9, back_plate_thick=11, pendulum_sticks_out=pendulumSticksOut, name="Wall22 Tony", gear_train_layout=clock.GearTrainLayout.COMPACT,
                                 motion_works_above=False, heavy=True, extra_heavy=False, pendulum_fixing=pendulumFixing, pendulum_at_front=False,
                                 back_plate_from_wall=pendulumSticksOut * 2, fixing_screws=clock.MachineScrew(metric_thread=4, countersunk=False),
                                 chain_through_pillar_required=False, pillars_separate=True, dial=dial, allow_bottom_pillar_height_reduction=False, bottom_pillars=2)


# hands = clock.Hands(style=clock.HandStyle.SPADE, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
#                     length=plates.dial_diameter*0.45, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=plates.second_hand_mini_dial_d*0.45)
hands = clock.Hands(style=clock.HandStyle.ARROWS, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=dial.get_tony_dimension("minute_hand_length"), thick=motionWorks.minute_hand_slot_height, outline=0, outline_same_as_body=False, chunky=True)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)

# pulley = clock.BearingPulley(diameter=train.poweredWheel.diameter, bearing=clock.getBearingInfo(4), wheel_screws=clock.MachineScrew(2, countersunk=True, length=8))
# print("pulley needs screws {} {}mm and {} {}mm".format(pulley.screws, pulley.get_total_thick(), pulley.hook_screws, pulley.getHookTotalThick()))



bow_tie = clock.BowTie(width=dial.outside_d*clock.tony_the_clock["bow_tie_width"]/clock.tony_the_clock["diameter"], bob_nut_width=pendulum.gap_width, bob_nut_height=pendulum.gap_height)
cosmetics={"red": bow_tie.get_red(),
           "yellow": bow_tie.get_yellow()}

#yellow is slightly translucent - a layer of solid white behind two layers of yellow works well.
pretty_bob = clock.ItemWithCosmetics(shape = pendulum.get_bob(), name="bow_tie_bob", background_colour="black", cosmetics=cosmetics, colour_thick_overrides={"yellow": clock.LAYER_THICK * 3})

assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pretty_bob=pretty_bob, pendulum=pendulum)#,weights=[clock.Weight(height=245,diameter=55)])


# show_object(plates.getPlate(back=True))
# show_object(assembly.getClock(with_key=False, with_pendulum=True, with_rods=True))
assembly.show_clock(show_object, hand_colours=["red"], dial_colours=["blue", "yellow"], motion_works_colours=["red"])
# show_object(plates.getDrillTemplate(6))

if outputSTL:

    pretty_bob.output_STLs(clockName, clockOutDir)
    train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    # pulley.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)
