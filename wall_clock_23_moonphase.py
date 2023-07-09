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
Clock 12 but without the dial, to see how it looks

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
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4,
                                    style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, wheelThick=2)
# lift=4
# drop=2
# lock=2
# escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

train = clock.GoingTrain(pendulum_period=1.5, fourth_wheel=False, escapement=escapement, maxWeightDrop=1000, usePulley=True, chainAtBack=False, chainWheels=1, hours=7.5*24)#, huygensMaintainingPower=True)

moduleReduction=0.85

train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, moduleReduction=moduleReduction)

#think this is promising for good compromise of size
train.genCordWheels(ratchetThick=6, rodMetricThread=4, cordThick=1, cordCoilThick=14, style=gearStyle, useKey=True, preferedDiameter=29, looseOnRod=False, prefer_small=True)
# train.genChainWheels2(clock.COUSINS_1_5MM_CHAIN, ratchetThick=6, arbourD=4, looseOnRod=False, prefer_small=True, preferedDiameter=25, fixing_screws=clock.MachineScrew(3, countersunk=True),ratchetOuterThick=6)
# train.genChainWheels2(clock.COUSINS_1_5MM_CHAIN, ratchetThick=6, arbourD=4, looseOnRod=False, prefer_small=True, preferedDiameter=30, fixing_screws=clock.MachineScrew(3, countersunk=True),ratchetOuterThick=6)



pendulumSticksOut=10
backPlateFromWall=35

train.genGears(module_size=1.1, moduleReduction=moduleReduction, thick=2.4, thicknessReduction=2/2.4, chainWheelThick=4, pinionThickMultiplier=3, style=gearStyle,
               chainModuleIncrease=1, chainWheelPinionThickMultiplier=2, pendulumFixing=pendulumFixing)
train.printInfo(weight_kg=3)
train.getArbourWithConventionalNaming(0).printScrewLength()

#tweaking angle slightly so that the second gear doesn't line up with an arbor that's between the plates
moon_complication = clock.MoonPhaseComplication3D(gear_style=gearStyle, first_gear_angle_deg=205, on_left=False)

#not inset at base as there's not enough space for the moon complication to fit behind it
motionWorks = clock.MotionWorks(extra_height=20, style=gearStyle, thick=3, compensateLooseArbour=False, compact=True, moon_complication=moon_complication)


#TODO try out larger pinions on the motion works - it'll be a fiddle to slot together at the moment
moon_complication.set_motion_works_sizes(motionWorks)
#slightly larger allows for the inset and thus dial and hands closer to the plate
# motionWorks.calculateGears(arbourDistance=30)

pendulum = clock.Pendulum(handAvoiderInnerD=100, bobD=60, bobThick=10)

dial = clock.Dial(outside_d=200, bottom_fixing=True, top_fixing=False, style=clock.DialStyle.CIRCLES, seconds_style=clock.DialStyle.LINES_ARC)

plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=9, backPlateThick=11, pendulumSticksOut=pendulumSticksOut, name="Wall 23",style=clock.ClockPlateStyle.COMPACT,
                                 heavy=True, extraHeavy=False, pendulumFixing=pendulumFixing, pendulumAtFront=False,
                                 backPlateFromWall=backPlateFromWall, fixingScrews=clock.MachineScrew(metric_thread=4, countersunk=True),
                                 chainThroughPillarRequired=True, pillars_separate=True, dial=dial, bottom_pillars=1, moon_complication=moon_complication,
                                 second_hand=second_hand_centred, centred_second_hand=second_hand_centred, motion_works_angle_deg = 225)

hands = clock.Hands(style=clock.HandStyle.MOON,  minuteFixing="square",  minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
                    length=dial.get_hand_length(), thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, chunky=True, second_hand_centred=second_hand_centred)#, secondLength=dial.second_hand_mini_dial_d*0.45, seconds_hand_thick=1.5)

assembly = clock.Assembly(plates, hands=hands, timeSeconds=30)

# show_object(assembly.getClock(with_key=True, with_pendulum=True))
assembly.show_clock(show_object)

if outputSTL:
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    moon_complication.outputSTLs(clockName, clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)