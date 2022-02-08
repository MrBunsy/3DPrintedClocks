import clocks.clock as clock

'''
Wall Clock 01/02 has proven that the basic design of gears and escapement can work, but the frame was lacking - it bend with the weight
and this caused the gears to mesh badly and sometimes seize. It was also top heavy.

The main aim of this clock is to produce a design which can actually be hung on the wall and see if I can minimise friction a bit.
 
I'm still planning to stick with the same basic going train as the first clock, but trying thinner gears to see if that has slightly less friction
tempted to try improving the efficiency of the escapement, but since I know the current one works I'm reluctant. Might try swapping in a different one later
'''


if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_04"
clockOutDir="out"

# crutchLength=100

# train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
train=clock.GoingTrain(pendulum_period=1.2,fourth_wheel=False,escapement_teeth=30, hours=180, maxChainDrop=2000, chainAtBack=True, max_wheel_teeth=100, min_pinion_teeth=8, chainWheels=1)

train.calculateRatios()

train.printInfo()
'''
{'time': 3600.0, 'train': [[90, 8], [80, 9]], 'error': 0.0, 'ratio': 100.0, 'teeth': 0.0}
pendulum length: 0.3578258921512801m period: 1.2s
escapement time: 36.0s teeth: 30
cicumference: 67.25, run time of:29.4hours
'''
train.genChainWheels(thick=5)

pendulumSticksOut=20

train.genGears(module_size=1,moduleReduction=0.85, thick=4)
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