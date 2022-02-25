import clocks.clock as clock

'''

'''

train=clock.GoingTrain(pendulum_period=1,fourth_wheel=True,escapement_teeth=30, maxChainDrop=1800, chainAtBack=False,chainWheels=1, hours=180)

train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, loud=True, moduleReduction=0.9)


train.setChainWheelRatio([74, 11])

#chain size seems about right, trying reducing tolerance
#the 1.2mm 47links/ft regula chain
train.genChainWheels(ratchetThick=5, wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075)#, wire_thick=0.85, width=3.6, inside_length=6.65-0.85*2, tolerance=0.1)

train.printInfo()
