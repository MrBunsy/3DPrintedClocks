import clocks.clock as clock

'''
A spherical weight clock with short pendulum

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="ball_clock_09"
clockOutDir="out"



drop =1.5
lift =2
lock=1.5
teeth = 48
toothTipAngle = 4
toothBaseAngle = 3
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=toothTipAngle, toothBaseAngle=toothBaseAngle)

train=clock.GoingTrain(pendulum_period=0.75, fourth_wheel=True, escapement=escapement, maxWeightDrop=1700, chainAtBack=False, chainWheels=0, hours=30)
train.calculateRatios(max_wheel_teeth=80, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1,loud=True)
'''
{'time': 3600.0, 'train': [[60, 14], [63, 12], [64, 12]], 'error': 0.0, 'ratio': 120.0, 'teeth': 187, 'weighting': 159.79}
pendulum length: 0.13977573912159377m period: 0.75s
escapement time: 30.0s teeth: 40
'''

#both three and four wheel trains have valid solutions, I think four wheels will end up giving me most flexibility in terms of space

# train=clock.GoingTrain(pendulum_period=0.75,fourth_wheel=False,escapement=escapement, maxChainDrop=1700, chainAtBack=False,chainWheels=0, hours=30)
# train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=20, max_error=0.1,loud=True)
'''
{'time': 3600.0, 'train': [[108, 10], [100, 9]], 'error': 0.0, 'ratio': 120.0, 'teeth': 208, 'weighting': 193.0}
pendulum length: 0.13977573912159377m period: 0.75s
escapement time: 30.0s teeth: 40
'''

train.genCordWheels(ratchetThick=5, cordThick=2, cordCoilThick=11)

train.printInfo()

pendulumSticksOut=8

train.genGears(module_size=1.25,moduleReduction=0.875, thick=3, chainWheelThick=6, useNyloc=False)


motionWorks = clock.MotionWorks(minuteHandHolderHeight=pendulumSticksOut+30 )


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=75, bobD=70, bobThick=10, useNylocForAnchor=False)



dial = clock.Dial(120)


plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=6, pendulumSticksOut=pendulumSticksOut, name="Wall 07", style="vertical")


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
