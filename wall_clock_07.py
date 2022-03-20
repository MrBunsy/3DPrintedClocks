import clocks.clock as clock

'''
Simple one day clock with a short pendulum, but trying more teeth on the escape wheel
and the first to be printed using the cord wheel
'''


if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_07"
clockOutDir="out"

outputSTL=True

train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=45, maxChainDrop=1800, chainAtBack=False,chainWheels=0, hours=30)

train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)

train.genCordWheels(ratchetThick=5, cordThick=2, cordCoilThick=11)

train.printInfo()

pendulumSticksOut=20

train.genGears(module_size=1.2,moduleReduction=0.875, thick=3, chainWheelThick=6, useNyloc=False)


motionWorks = clock.MotionWorks(minuteHandHolderHeight=pendulumSticksOut+40 )


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0, bobD=60, bobThick=10, useNylocForAnchor=False)



dial = clock.Dial(120)


plates = clock.ClockPlates(train, motionWorks, pendulum, plateThick=6, pendulumSticksOut=pendulumSticksOut, name="Wall 07", style="vertical")


hands = clock.Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)


#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands)


show_object(assembly.getClock())

if outputSTL:
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    dial.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)