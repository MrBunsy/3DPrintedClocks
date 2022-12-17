from clocks import clock

'''
1 Day chain driven clock, short pendulum and no second hand, this was the first to use the new plate design and should remain compatible with future changes to the plate design
The first build of this had the maths for plate distance broken

Wall clock 03 proved the new design of clock plates and that smaller gears can work.

This is an attempt to minimise the new clock plates further
'''

outputSTL=False
if 'show_object' not in globals():
    # don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_04b"
clockOutDir="out"

# drop =1.5
# lift =3
# lock=1.5
# escapement = clock.Escapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)
#
#


# crutchLength=100

# train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
#pendulum period of 1.25 actually results in larger clock than period of 1
train=clock.GoingTrain(pendulum_period=1.25, fourth_wheel=False, escapement_teeth=30, maxWeightDrop=2100, chainAtBack=False, escapeWheelPinionAtFront=True)#, escapement=escapement)

# train.calculateRatios(max_wheel_teeth=120, min_pinion_teeth=9)
# train.setRatios([[81, 12], [80, 9]])
train.setRatios([[108, 10], [80, 9]])
# 61 links/ft 1-day regula chain. Size seems about right, trying reducing tolerance
train.genChainWheels(ratchetThick=3, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075,screwThreadLength=8)
# train.genCordWheels(ratchetThick=4, cordThick=2, cordCoilThick=11)

train.printInfo()
'''
{'train': [[81, 12], [80, 9]]}
pendulum length: 0.9939608115313336m period: 2s
escapement time: 60s teeth: 30
cicumference: 68.60000000000001, run time of:28.9hours
'''
pendulumSticksOut=20
#keeping chain wheel slightly thicker so it might be less wonky on the rod?
train.genGears(module_size=1,moduleReduction=0.85, thick=2, chainWheelThick=5, useNyloc=False, escapeWheelMaxD=0.75,ratchetInset=False)


motionWorks = clock.MotionWorks(minuteHandHolderHeight=pendulumSticksOut+40, )


#trying using same bearings and having the pendulum rigidly fixed to the anchor's arbour
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0, handAvoiderInnerD=50, bobD=60, bobThick=10, useNylocForAnchor=False)

pendulum.outputSTLs(clockName, clockOutDir)

dial = clock.Dial(110, supportLength=pendulumSticksOut+20)

#printed the base in 10, seems much chunkier than needed at the current width. Adjusting to 8 for the front plate
plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=6, pendulumSticksOut=pendulumSticksOut, name="Wall 04")#, dial=dial)


hands = clock.Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=80, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)


weight = clock.Weight(height=100, diameter=35)

weight.printInfo()

assembly = clock.Assembly(plates, hands=hands)

show_object(assembly.getClock())

if outputSTL:
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    weight.outputSTLs(clockName, clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)