from clocks import clock

'''
Repeat of Clock 10 but with improvements. Eight days, with pulley.

Changes from clock 10 planned:

 - Pendulum needs to stick out further to cope with larger weights
 - Why not try a second hand without a visible hole?

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_12"
clockOutDir="out"
gearStyle=clock.GearStyle.CARTWHEEL

# drop =1.5
# lift =3
# lock=1.5
lift=4
drop=2
lock=2
escapement = clock.Escapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

train = clock.GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, maxWeightDrop=1900, chainAtBack=False, chainWheels=1, hours=180, max_chain_wheel_d=21)

moduleReduction=0.9

train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, moduleReduction=moduleReduction)
train.setChainWheelRatio([93, 10])
train.genCordWheels(ratchetThick=4, rodMetricThread=4, cordThick=1.5, cordCoilThick=10, style=gearStyle, useKey=True)
train.printInfo()

pendulumSticksOut=30

train.genGears(module_size=1,moduleReduction=moduleReduction,  thick=2, thicknessReduction=0.9, chainWheelThick=3, useNyloc=False, pinionThickMultiplier=3, style=gearStyle,chainModuleIncrease=1, chainWheelPinionThickMultiplier=2,ratchetInset=True, ratchetScrewsPanHead=False)#, chainModuleIncrease=1.1)

train.getArbourWithConventionalNaming(0).printScrewLength()

motionWorks = clock.MotionWorks(minuteHandHolderHeight=pendulumSticksOut+30,style=gearStyle, thick=2, compensateLooseArbour=True)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=120, bobD=80, bobThick=10, useNylocForAnchor=False)



dial = clock.Dial(120)

#rear plate super thick mainly just to ensure there's enough space for the weight to not bump into the wall!
plates = clock.ClockPlates(train, motionWorks, pendulum, plateThick=8, backPlateThick=15, pendulumSticksOut=pendulumSticksOut, name="Wall 10", style="vertical", motionWorksAbove=True, heavy=True, extraHeavy=True, usingPulley=True)


hands = clock.Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=25)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)

# pulley = clock.Pulley(diameter=train.poweredWheel.diameter, bearing=clock.getBearingInfo(4))
pulley = clock.Pulley(diameter=26, bearing=clock.getBearingInfo(4), screwMetricSize=2, screwsCountersunk=False)
#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands, timeMins=0, timeSeconds=30, pulley = pulley)

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
