import clocks.clock as clock

'''
Another attempt at an eight day, this time symetric and using a cord wheel
'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_06"
clockOutDir="out"
gearStyle="circles"

drop =1.5
lift =3
lock=1.5
escapement = clock.Escapement(drop=drop, lift=lift, type="deadbeat",teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

train=clock.GoingTrain(pendulum_period=1.75,fourth_wheel=False,escapement=escapement , maxChainDrop=1800, chainAtBack=False,chainWheels=1, hours=180)

train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)
# train.calculateRatios()
# train.setRatios([[60, 14], [63, 12], [64, 12]])
# train.setRatios([[64, 12], [63, 12], [60, 14]])
# train.setRatios([[81, 12], [80, 9]])
# train.setRatios([[108, 10], [80, 9]])
train.setChainWheelRatio([74, 11])

#chain size seems about right, trying reducing tolerance
#the 1.2mm 47links/ft regula chain
# train.genChainWheels(ratchetThick=5, wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075)#, wire_thick=0.85, width=3.6, inside_length=6.65-0.85*2, tolerance=0.1)
train.genCordWheels(ratchetThick=5, cordThick=2, cordCoilThick=11, style=gearStyle)

train.printInfo()

pendulumSticksOut=8

train.genGears(module_size=1.2,moduleReduction=0.875, thick=2, chainWheelThick=6, useNyloc=False, pinionThickMultiplier=4, style=gearStyle)#, chainModuleIncrease=1.1)


motionWorks = clock.MotionWorks(minuteHandHolderHeight=pendulumSticksOut+30 )


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=75, bobD=70, bobThick=10, useNylocForAnchor=False)



dial = clock.Dial(120)

plates = clock.ClockPlates(train, motionWorks, pendulum, plateThick=8, pendulumSticksOut=pendulumSticksOut, name="Wall 06", style="vertical")


hands = clock.Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)


#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands, timeMins=47)


show_object(assembly.getClock())

if outputSTL:
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    dial.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)