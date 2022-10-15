from clocks import clock

'''
Eight days, with pulley. 1.2m drop so it should have more power to play with than clock 10

Changes from clock 10 planned:

 - Pendulum needs to stick out further to cope with larger weights (or maybe put it at the back?)
 - Why not try a second hand without a visible hole?
 - go back to slightly thicker gears to increase robustness (I'm worried about long term life of the clock and seen the escape wheel teeth bend) and make up for friction with longer drop

Decided to try out the new short pendulum since it worked well on clock 11, so I think I can get away with having the pendulum really close to the plates as it'll never reach the weight

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_12"
clockOutDir="out"
gearStyle=clock.GearStyle.FLOWER
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOUR

drop =1.5
lift =3
lock=1.5
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

# lift=4
# drop=2
# lock=2
# escapement = clock.Escapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

train = clock.GoingTrain(pendulum_period=1.5, fourth_wheel=False, escapement=escapement, maxWeightDrop=1240, usePulley=True, chainAtBack=False, chainWheels=1, hours=7.25*24)

moduleReduction=1

train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, moduleReduction=moduleReduction)
# train.setChainWheelRatio([93, 10])

train.genCordWheels(ratchetThick=4, rodMetricThread=4, cordThick=1, cordCoilThick=18, style=gearStyle, useKey=True, preferedDiameter=42.5, looseOnRod=False)
#override default until it calculates an ideally sized wheel
train.calculatePoweredWheelRatios(wheel_max=100)

pendulumSticksOut=30

train.genGears(module_size=0.9, moduleReduction=moduleReduction, thick=2.4, thicknessReduction=0.9, chainWheelThick=4, pinionThickMultiplier=3, style=gearStyle,
               chainModuleIncrease=1, chainWheelPinionThickMultiplier=2, pendulumFixing=pendulumFixing)
train.printInfo(weight_kg=3.5)
train.getArbourWithConventionalNaming(0).printScrewLength()

cordwheel = train.getArbourWithConventionalNaming(0)

# show_object(cordwheel.poweredWheel.getAssembled())
# show_object(cordwheel.poweredWheel.getSegment(front=False))
#
motionWorks = clock.MotionWorks(minuteHandHolderHeight=pendulumSticksOut+30,style=gearStyle, thick=2, compensateLooseArbour=True)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=50,
                          bobD=60, bobThick=10, useNylocForAnchor=False, handAvoiderHeight=100)



dial = clock.Dial(120)

#back plate of 15 thick is only just enough for the 3.5kg weight in a shell! it won't be enough for 4kg
plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=8, backPlateThick=15, pendulumSticksOut=pendulumSticksOut, name="Wall 12", style="vertical",
                                 motionWorksAbove=True, heavy=True, extraHeavy=True, usingPulley=True, pendulumFixing=pendulumFixing)


hands = clock.Hands(style=clock.HandStyle.SPADE, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
                    length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=25)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)

# pulley = clock.Pulley(diameter=train.poweredWheel.diameter, bearing=clock.getBearingInfo(4))
pulley = clock.Pulley(diameter=26, bearing=clock.getBearingInfo(4), screwMetricSize=2, screwsCountersunk=False)
#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands, timeMins=0, timeSeconds=30, pulley = pulley, showPendulum=True)#weights=[clock.Weight(height=245,diameter=55)]

# show_object(plates.getPlate(back=True))
show_object(assembly.getClock())

if outputSTL:
    #
    #
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    dial.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    pulley.outputSTLs(clockName, clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)

    # clock.outputSTLMultithreaded([train, motionWorks,pendulum,dial,plates,hands,pulley,assembly], clockName, clockOutDir)
