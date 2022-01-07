import clocks.clock as clock


train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40)

train.genTrain()

train.printInfo()

train.genGears()

train.outputSTLs("wall_clock_01","out")

