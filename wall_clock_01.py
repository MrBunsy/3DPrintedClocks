import clocks.clock as clock

if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass


train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)

train.genTrain()

train.printInfo()

train.genChainWheels()
train.genGears(module_size=1.3,moduleReduction=0.85)

show_object(train.arbours[0])

train.outputSTLs("wall_clock_01","out")

