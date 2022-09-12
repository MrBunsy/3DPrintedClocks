from clocks import clock

'''
Experiment to see how large I could make a clock if I used wood for the plates
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

drop =1.5
lift =3
lock=1.5
escapement = clock.Escapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

# lift=4
# drop=2
# lock=2
# escapement = clock.Escapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

train = clock.GoingTrain(pendulum_period=1, wheels=2, escapement=escapement, maxWeightDrop=1200, usePulley=True, chainAtBack=False, chainWheels=1, hours=7.25*24)

moduleReduction=1

train.calculateRatios(max_wheel_teeth=100000, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, moduleReduction=moduleReduction,loud=True)
# train.setChainWheelRatio([93, 10])

train.genCordWheels(ratchetThick=4, rodMetricThread=4, cordThick=1.5, cordCoilThick=14, style=gearStyle, useKey=True, preferedDiameter=25)
#override default until it calculates an ideally sized wheel
train.calculatePoweredWheelRatios(wheel_max=100)
#3.5 should be enough, but plan is to bump it up to 4 if it isn't
train.printInfo(weight_kg=3.5)
exit()
pendulumSticksOut=30

train.genGears(module_size=0.9, moduleReduction=moduleReduction, thick=2.4, thicknessReduction=0.9, chainWheelThick=4, useNyloc=False, pinionThickMultiplier=3, style=gearStyle, chainModuleIncrease=1, chainWheelPinionThickMultiplier=2, ratchetInset=False)#, chainModuleIncrease=1.1)

train.getArbourWithConventionalNaming(0).printScrewLength()

motionWorks = clock.MotionWorks(minuteHandHolderHeight=pendulumSticksOut+30,style=gearStyle, thick=2, compensateLooseArbour=True)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=50, bobD=60, bobThick=10, useNylocForAnchor=False, handAvoiderHeight=100)



dial = clock.Dial(120)

#back plate of 15 thick is only just enough for the 3.5kg weight in a shell! it won't be enough for 4kg
plates = clock.ClockPlates(train, motionWorks, pendulum, plateThick=8, backPlateThick=15, pendulumSticksOut=pendulumSticksOut, name="Wall 12", style="vertical", motionWorksAbove=True, heavy=True, extraHeavy=True, usingPulley=True)


hands = clock.Hands(style=clock.HandStyle.SPADE, minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=25)
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