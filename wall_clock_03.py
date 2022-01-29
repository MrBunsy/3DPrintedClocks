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


clockName="wall_clock_03"
clockOutDir="out"

# crutchLength=100

# train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=30, maxChainDrop=2100, chainAtBack=False)

train.calculateRatios()

train.printInfo()

train.genChainWheels()
train.genGears(module_size=1.2,moduleReduction=0.85, thick=4)

train.outputSTLs(clockName,clockOutDir)

motionWorks = clock.MotionWorks(minuteHandHolderHeight=30)
motionWorks.outputSTLs(clockName,clockOutDir)

#HACK for now using same bearing as rest of the gears for the anchor
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=8)

pendulum.outputSTLs(clockName, clockOutDir)


plates = clock.ClockPlates(train, motionWorks, pendulum)
plates.outputSTLs(clockName, clockOutDir)

hands = clock.Hands(minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=50, thick=motionWorks.minuteHandSlotHeight)
hands.outputSTLs(clockName, clockOutDir)