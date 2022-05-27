import clocks.clock as clock

'''
Simple one day clock with shortest pendulum I can manage to also have a second hand on the esacpe wheel

Attempting to reduce plate distance of the one day cord wheel clock

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_11"
clockOutDir="out"


drop =1.5
lift =3
lock=1.5
escapement = clock.Escapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

# train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement=escapement, maxChainDrop=1600, chainAtBack=False,chainWheels=0, hours=30)
train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement=escapement, maxChainDrop=1800, chainAtBack=False,chainWheels=0, hours=30)
#, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4
# train.setEscapementDetails(drop=1.5, lift=3, lock=1.5)

train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)

# train.genCordWheels(ratchetThick=2.5, cordThick=1, cordCoilThick=8)
train.genChainWheels(ratchetThick=3, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075,screwThreadLength=8)

train.printInfo()

pendulumSticksOut=8

train.genGears(module_size=1.25,moduleReduction=0.875, thick=1.8, chainWheelThick=4.5, useNyloc=False, ratchetInset=True, pinionThickMultiplier=4, chainWheelPinionThickMultiplier=2)


motionWorks = clock.MotionWorks(minuteHandHolderHeight=pendulumSticksOut+30 )


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=75, bobD=70, bobThick=10, useNylocForAnchor=False)



dial = clock.Dial(120)


plates = clock.ClockPlates(train, motionWorks, pendulum, plateThick=6, pendulumSticksOut=pendulumSticksOut, name="Wall 07", style="vertical")


hands = clock.Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)


#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands)

weight = clock.Weight(height=100, diameter=35)
weight.printInfo()

bigweight = clock.Weight(height=125, diameter=45)
bigweight.printInfo()

show_object(assembly.getClock())

if outputSTL:
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    dial.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    weight.outputSTLs(clockName, clockOutDir)
    bigweight.outputSTLs(clockName+"_big", clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)
