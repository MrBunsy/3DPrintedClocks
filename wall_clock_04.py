import clocks.clock as clock

'''
Wall clock 03 proved the new design of clock plates and that smaller gears can work.

This is an attempt to minimise the new clock plates further
'''


if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_04"
clockOutDir="out"

# crutchLength=100

# train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
#pendulum period of 1.25 actually results in larger clock than period of 1
train=clock.GoingTrain(pendulum_period=2,fourth_wheel=False,escapement_teeth=30, maxChainDrop=2100, chainAtBack=False, max_wheel_teeth=120, min_pinion_teeth=9)

# train.calculateRatios()
train.setRatios([[81, 12], [80, 9]])

# 61 links/ft 1-day regula chain. Size seems about right, trying reducing tolerance
train.genChainWheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.1)

train.printInfo()
'''
{'train': [[81, 12], [80, 9]]}
pendulum length: 0.9939608115313336m period: 2s
escapement time: 60s teeth: 30
cicumference: 68.60000000000001, run time of:28.9hours
'''



pendulumSticksOut=20

train.genGears(module_size=1,moduleReduction=0.85, thick=3)
train.outputSTLs(clockName,clockOutDir)

motionWorks = clock.MotionWorks(minuteHandHolderHeight=pendulumSticksOut+20, )
motionWorks.outputSTLs(clockName,clockOutDir)

#trying using same bearings and having the pendulum rigidly fixed to the anchor's arbour
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=8, nutMetricSize=3, crutchLength=0)

pendulum.outputSTLs(clockName, clockOutDir)

#printed the base in 10, seems much chunkier than needed at the current width. Adjusting to 8 for the front plate
plates = clock.ClockPlates(train, motionWorks, pendulum, plateThick=8, pendulumSticksOut=pendulumSticksOut)
plates.outputSTLs(clockName, clockOutDir)

hands = clock.Hands(minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
hands.outputSTLs(clockName, clockOutDir)

