import clocks.clock as clock

'''
This is an attempt to make an eight day clock.

It has an asymetric design to try out making clock plates smaller. This works, but looks a bit odd.

It failed as the chain wheel couldn't take the weight (the lugs broke/bent) and the chain stretched.
It ran for about 4 days first though, proving that the going train can work. Plan is to remake this clock but with a symetric design and a cord wheel
'''


if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_05"
clockOutDir="out"

# crutchLength=100

# train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
#pendulum period of 1.25 actually results in larger clock than period of 1
train=clock.GoingTrain(pendulum_period=1,fourth_wheel=True,escapement_teeth=30, maxChainDrop=1800, chainAtBack=False,chainWheels=1, hours=180)

# train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)
# train.setRatios([[60, 14], [63, 12], [64, 12]])
train.setRatios([[64, 12], [63, 12], [60, 14]])
# train.setRatios([[81, 12], [80, 9]])
# train.setRatios([[108, 10], [80, 9]])
train.setChainWheelRatio([74, 11])

#chain size seems about right, trying reducing tolerance
#the 1.2mm 47links/ft regula chain
train.genChainWheels(ratchetThick=5, wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075)#, wire_thick=0.85, width=3.6, inside_length=6.65-0.85*2, tolerance=0.1)

train.printInfo()

pendulumSticksOut=0

train.genGears(module_size=1,moduleReduction=0.875, thick=3, chainWheelThick=6, useNyloc=False)#, chainModuleIncrease=1.1)
train.outputSTLs(clockName,clockOutDir)

motionWorks = clock.MotionWorks(minuteHandHolderHeight=30 )
motionWorks.outputSTLs(clockName,clockOutDir)

#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0, bobD=60, bobThick=10, useNylocForAnchor=False)

pendulum.outputSTLs(clockName, clockOutDir)

dial = clock.Dial(120)
dial.outputSTLs(clockName, clockOutDir)

#printed the base in 10, seems much chunkier than needed at the current width. Adjusting to 8 for the front plate
plates = clock.ClockPlates(train, motionWorks, pendulum, plateThick=8, pendulumSticksOut=pendulumSticksOut, name="Wall 05", style="round", heavy=True)
plates.outputSTLs(clockName, clockOutDir)

# hands = clock.Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False, outline=0.6)
hands.outputSTLs(clockName, clockOutDir)

#no weight for this clock, using the cheap 2.5kg weight from cousins
#which needs a shell to look better!
shell = clock.WeightShell(45,220, twoParts=True, holeD=5)
shell.outputSTLs(clockName, clockOutDir)

assembly = clock.Assembly(plates, hands=hands, timeMins=47)
assembly.outputSTLs(clockName, clockOutDir)