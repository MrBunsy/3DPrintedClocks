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

clockName="wall_clock_20"
clockOutDir="out"
gearStyle=clock.GearStyle.DIAMONDS
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS

#for period 1.5
# drop =1.5
# lift =3
# lock=1.5
# escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)
# escapement = clock.GrasshopperEscapement(acceptableError=0.001, teeth=60, tooth_span=9.5, pendulum_length_m=clock.getPendulumLength(1.5), mean_torque_arm_length=10, loud_checks=True, skip_failed_checks=True, ax_deg=89)
lift=4
drop=2
lock=2
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

train = clock.GoingTrain(pendulum_period=1.25, fourth_wheel=False, escapement=escapement, maxWeightDrop=1200, usePulley=True, chainAtBack=False, chainWheels=1, hours=7.25*24)#, huygensMaintainingPower=True)

moduleReduction=0.85

train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, moduleReduction=moduleReduction)
# train.setChainWheelRatio([93, 10])

#original test
# train.genCordWheels(ratchetThick=4, rodMetricThread=4, cordThick=1, cordCoilThick=18, style=gearStyle, useKey=True, preferedDiameter=42.5, looseOnRod=False)
#think this is promising for good compromise of size
train.genCordWheels(ratchetThick=4, rodMetricThread=4, cordThick=1, cordCoilThick=14, style=gearStyle, useKey=True, preferedDiameter=29, looseOnRod=False, prefer_small=True)
#the 1.2mm 47links/ft regula chain
# train.genChainWheels(ratchetThick=5, wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075)

#override default until it calculates an ideally sized wheel
# train.calculatePoweredWheelRatios(wheel_max=100)

#for pulley
# train.genRopeWheels(ratchetThick = 4, arbour_d=4, ropeThick=2.2, wallThick=2, preferedDiameter=40,o_ring_diameter=2)
# train.genRopeWheels(ratchetThick = 4, arbour_d=4, ropeThick=2.2, wallThick=2, preferedDiameter=35,o_ring_diameter=2, prefer_small=True)



pendulumSticksOut=20

train.genGears(module_size=1, moduleReduction=moduleReduction, thick=2.4, thicknessReduction=0.9, chainWheelThick=4, pinionThickMultiplier=3, style=gearStyle,
               chainModuleIncrease=1, chainWheelPinionThickMultiplier=2, pendulumFixing=pendulumFixing)
train.printInfo(weight_kg=4)
train.getArbourWithConventionalNaming(0).printScrewLength()

cordwheel = train.getArbourWithConventionalNaming(0)

# show_object(cordwheel.poweredWheel.getAssembled())
# show_object(cordwheel.poweredWheel.getSegment(front=False))
#
motionWorks = clock.MotionWorks(extra_height=0, style=gearStyle, thick=3, compensateLooseArbour=False, compact=True)

pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=100,
                          bobD=60, bobThick=10, useNylocForAnchor=False)#, handAvoiderHeight=100)

# plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=9, backPlateThick=11, pendulumSticksOut=pendulumSticksOut, name="Wall 12", style="vertical",
#                                  motionWorksAbove=False, heavy=True, extraHeavy=True, pendulumFixing=pendulumFixing, pendulumAtFront=False,
#                                  backPlateFromWall=pendulumSticksOut*2, fixingScrews=clock.MachineScrew(metric_thread=3, countersunk=True, length=40),
#                                  chainThroughPillar=False, dial_diameter=250, second_hand_mini_dial_d=65)#, centred_second_hand=True

'''
Ideas:

side arms for the dial, then it can be smaller and not overlap with the key
use a rounded square shape for the minute hand, then the minute hand can be used to adjust the time.

or just stick with original plan of arm on top with rounded suqare for hand?
'''

plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=9, backPlateThick=11, pendulumSticksOut=pendulumSticksOut, name="Wall 12", style="vertical",
                                 motionWorksAbove=True, heavy=True, extraHeavy=True, pendulumFixing=pendulumFixing, pendulumAtFront=False,
                                 backPlateFromWall=pendulumSticksOut*2, fixingScrews=clock.MachineScrew(metric_thread=3, countersunk=True, length=40),
                                 chainThroughPillarRequired=False, pillars_separate=True, dial_diameter=205, dial_bottom_fixing=True)


# hands = clock.Hands(style=clock.HandStyle.SPADE, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
#                     length=plates.dial_diameter*0.45, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=plates.second_hand_mini_dial_d*0.45)
hands = clock.Hands(style=clock.HandStyle.SWORD,  minuteFixing="circle",  minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
                    length=plates.dial_diameter*0.45, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, chunky=True)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)

# # pulley = clock.Pulley(diameter=train.poweredWheel.diameter, bearing=clock.getBearingInfo(4))
# pulley = clock.BearingPulley(diameter=26, bearing=clock.getBearingInfo(4), screwMetricSize=2, screwsCountersunk=False)
# #no weight for this clock, as it's going to probably be too heavy to make myself.
pulley = None

assembly = clock.Assembly(plates, hands=hands, timeSeconds=30, pulley = pulley, showPendulum=True)#weights=[clock.Weight(height=245,diameter=55)]

# show_object(plates.getPlate(back=True))
show_object(assembly.getClock())

# show_object(plates.getDrillTemplate(6))

if outputSTL:
    #
    #
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    # pulley.outputSTLs(clockName, clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)

    # clock.outputSTLMultithreaded([train, motionWorks,pendulum,dial,plates,hands,pulley,assembly], clockName, clockOutDir)
