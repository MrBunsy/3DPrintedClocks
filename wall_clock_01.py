import clocks.clock as clock

if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_02"
clockOutDir="out"

crutchLength=100

# train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=30, maxChainDrop=2100)

train.calculateRatios()

train.printInfo()

train.genChainWheels()
train.genGears(module_size=1.2,moduleReduction=0.85)

show_object(train.arbours[0])
print("anchor centre distnace", train.escapement.anchor_centre_distance)
train.outputSTLs(clockName,clockOutDir)

motionWorks = clock.MotionWorks()
motionWorks.outputSTLs(clockName,clockOutDir)

#HACK for now using same bearing as rest of the gears for the anchor
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3)

pendulum.outputSTLs(clockName, clockOutDir)


plates = clock.ClockPlates(train, motionWorks, pendulum)
plates.outputSTLs(clockName, clockOutDir)

hands = clock.Hands(minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=50, thick=motionWorks.minuteHandSlotHeight)
hands.outputSTLs(clockName, clockOutDir)