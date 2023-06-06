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
Clock 12 but without the dial

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_24"
clockOutDir="out"
gearStyle=clock.GearStyle.CURVES
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS

#for period 1.5
drop =1.5
lift =3
lock=1.5
#increasing run only for asthetic reasons
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4,
                                    style=clock.AnchorStyle.CURVED_MATCHING_WHEEL)

train = clock.GoingTrain(pendulum_period=1.5, wheels=3, escapement=escapement, maxWeightDrop=1100, usePulley=True, chainAtBack=False, chainWheels=1, hours=7.5*24, supportSecondHand=True)#, huygensMaintainingPower=True)

moduleReduction=1#0.85

train.calculateRatios(max_wheel_teeth=120, min_pinion_teeth=9, wheel_min_teeth=20, pinion_max_teeth=15, max_error=0.1, moduleReduction=moduleReduction, loud=True, favour_smallest=False)
# train.calculateRatios(max_wheel_teeth=70, min_pinion_teeth=12, wheel_min_teeth=50, pinion_max_teeth=15, max_error=0.1, moduleReduction=moduleReduction, loud=True)
# train.setRatios( [[72, 10], [75, 9], [60, 27]])

#think this is promising for good compromise of size
train.genCordWheels(ratchetThick=6, rodMetricThread=4, cordThick=1, cordCoilThick=14, style=gearStyle, useKey=True, preferedDiameter=29, looseOnRod=False, prefer_small=True)
# train.genChainWheels2(clock.COUSINS_1_5MM_CHAIN, ratchetThick=6, arbourD=4, looseOnRod=False, prefer_small=True, preferedDiameter=25, fixing_screws=clock.MachineScrew(3, countersunk=True),ratchetOuterThick=6)



pendulumSticksOut=10
backPlateFromWall=30

train.genGears(module_size=1, moduleReduction=moduleReduction, thick=2.4, thicknessReduction=0.9, chainWheelThick=4, pinionThickMultiplier=3, style=gearStyle,
               chainModuleIncrease=1, chainWheelPinionThickMultiplier=2.25, pendulumFixing=pendulumFixing, stack_away_from_powered_wheel=True)
train.printInfo(weight_kg=3)
train.getArbourWithConventionalNaming(0).printScrewLength()

#although I can make really compact motion works now for the dial to be close, this results in a key that looks too short, so extending just so the key might be more stable
motionWorks = clock.MotionWorks(extra_height=10, style=gearStyle, thick=3, compensateLooseArbour=True, compact=True)#, inset_at_base=clock.MotionWorks.STANDARD_INSET_DEPTH)
#slightly larger allows for the inset and thus dial and hands closer to the plate
motionWorks.calculateGears(arbourDistance=30)

pendulum = clock.Pendulum(handAvoiderInnerD=100, bobD=50, bobThick=8)

# dial = clock.Dial(outside_d=180, bottom_fixing=True, top_fixing=True, style=clock.DialStyle.ROMAN, seconds_style=clock.DialStyle.CONCENTRIC_CIRCLES)
dial = None

#dial diameter of 250 (printed in two parts) looks promising for second hand, 205 without
plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=9, backPlateThick=10, pendulumSticksOut=pendulumSticksOut, name="Wall 24",style=clock.ClockPlateStyle.COMPACT,
                                 heavy=True, extraHeavy=True, pendulumFixing=pendulumFixing, pendulumAtFront=False,
                                 backPlateFromWall=backPlateFromWall, fixingScrews=clock.MachineScrew(metric_thread=4, countersunk=True),
                                 chainThroughPillarRequired=True, pillars_separate=True, dial=dial, bottom_pillars=1, motion_works_angle_deg=360-40,
                                 allow_bottom_pillar_height_reduction=False, endshake=1.5, second_hand=False, escapementOnFront=True)


# hands = clock.Hands(style=clock.HandStyle.SPADE, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
#                     length=plates.dial_diameter*0.45, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=plates.second_hand_mini_dial_d*0.45)
hands = clock.Hands(style=clock.HandStyle.SPADE,  minuteFixing="square",  minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
                    length=150, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, chunky=True, secondLength=20, seconds_hand_thick=1.5)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)

pulley = clock.BearingPulley(diameter=train.poweredWheel.diameter, bearing=clock.getBearingInfo(4), wheel_screws=clock.MachineScrew(2, countersunk=True, length=8))
print("pulley needs screws {} {}mm and {} {}mm".format(pulley.screws, pulley.getTotalThick(), pulley.hook_screws, pulley.getHookTotalThick()))


assembly = clock.Assembly(plates, hands=hands, timeSeconds=30, pulley = pulley, timeHours=12, timeMins=0)#weights=[clock.Weight(height=245,diameter=55)]

# show_object(plates.getPlate(back=True))
# show_object(assembly.getClock(with_key=False, with_pendulum=True))

assembly.show_clock(show_object, motion_works_colours=[clock.Colour.GREEN, clock.Colour.GREEN, clock.Colour.LIGHTBLUE], bob_colours=[clock.Colour.PURPLE])

# show_object(plates.getDrillTemplate(6))

if outputSTL:
    #
    #
    # train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    pulley.outputSTLs(clockName, clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)

    # clock.outputSTLMultithreaded([train, motionWorks,pendulum,dial,plates,hands,pulley,assembly], clockName, clockOutDir)