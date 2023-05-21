'''
Copyright Luke Wallin 2023

This source describes Open Hardware and is licensed under the CERN-OHL-S v2.

You may redistribute and modify this source and make products using it under
the terms of the CERN-OHL-S v2 or any later version (https://ohwr.org/cern_ohl_s_v2.txt).

This source is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY,
INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A
PARTICULAR PURPOSE. Please see the CERN-OHL-S v2 for applicable conditions.

Source location: https://github.com/MrBunsy/3DPrintedClocks

As per CERN-OHL-S v2 section 4, should you produce hardware based on this
source, You must where practicable maintain the Source Location visible
on the external case of the clock or other products you make using this
source.
'''
from clocks import clock

'''
Another attempt at an eight day, this time symetric and using a cord wheel

Both printed versions of this work, with different issues. The top cap of the cord wheel isn't thick enough (so it bends and catches on teh front plate)

06b is an attempt to reprint just the cord wheel to make use of the new thicker cap tested on clock 10, increase drop rate and 
try out a loose wheel and fixed cord barrel.


second printing of clock6, hopefully:
chain wheel ratio: [103, 10]
module 1
cord wheel diameter: 26
cap diameter 52

plate distance 43.8

setting escapeWheelPinionAtFront to true just so reprinted bits are compatible with the old design (could re-print all the gear train, but that seems unnecessary)

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_06b"
clockOutDir="out"
gearStyle=clock.GearStyle.CIRCLES

# drop =1.5
# lift =3
# lock=1.5
lift=4
drop=2
lock=2
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

train = clock.GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, maxWeightDrop=2090-270, chainAtBack=False, chainWheels=1, hours=24*7.25, escapeWheelPinionAtFront=True)

train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)
# train.calculateRatios()
# train.setRatios([[60, 14], [63, 12], [64, 12]])
# train.setRatios([[64, 12], [63, 12], [60, 14]])
# train.setRatios([[81, 12], [80, 9]])
# train.setRatios([[108, 10], [80, 9]])
# train.setChainWheelRatio([74, 11])



#chain size seems about right, trying reducing tolerance
#the 1.2mm 47links/ft regula chain
# train.genChainWheels(ratchetThick=5, wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075)#, wire_thick=0.85, width=3.6, inside_length=6.65-0.85*2, tolerance=0.1)

#thickness of 17 works well for using 25mm countersunk screws to hold it together, not being too much space between plates and a not-awful gear ratio
train.genCordWheels(ratchetThick=5, rodMetricThread=4, cordThick=2, cordCoilThick=16, style=gearStyle, useKey=True,preferedDiameter=29.5, looseOnRod=False)
'''
with drop of 1.8m and max d of 28:
pendulum length: 0.9939608115313336m period: 2s
escapement time: 60s teeth: 30
[102, 10]
layers of cord: 3, cord per hour: 1.2cm to 0.9cm
runtime: 179.6hours. Chain wheel multiplier: 10.2

with 1675mm and 26mm diameter:
[103, 10]
layers of cord: 3, cord per hour: 1.1cm to 0.9cm
runtime: 180.0hours. Chain wheel multiplier: 10.3

'''
# train.calculatePoweredWheelRatios()
train.setChainWheelRatio([103, 10])
# train.printInfo(weight_kg=2.5)

pendulumSticksOut=28

train.genGears(module_size=1,moduleReduction=0.875,  thick=2, chainWheelThick=6, useNyloc=False, pinionThickMultiplier=4, style=gearStyle,chainModuleIncrease=1, chainWheelPinionThickMultiplier=2)#, chainModuleIncrease=1.1)


motionWorks = clock.MotionWorks(extra_height=pendulumSticksOut + 30, style=gearStyle, thick=2)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(bobD=80, bobThick=10)



dial = clock.Dial(120)

plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=8, backPlateThick=10, pendulumSticksOut=pendulumSticksOut, name="Wall 06",style=clock.ClockPlateStyle.VERTICAL, motionWorksAbove=True, heavy=True)


hands = clock.Hands(style=clock.HandStyle.CIRCLES, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=25)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)


#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands, timeMins=0, timeSeconds=00)

assembly.printInfo()
train.printInfo(weight_kg=2.5)
train.printInfo(weight_kg=2)
print("Plate distance: ", plates.plateDistance)

# show_object(train.getArbourWithConventionalNaming(0).getAssembled())
# show_object(train.getArbourWithConventionalNaming(0).poweredWheel.getAssembled())
# show_object(train.getArbourWithConventionalNaming(0).getShape())

#
# show_object(assembly.getClock())
#
assembly.show_clock(show_object, plate_colour=clock.Colour.DARKGREY, motion_works_colours=[clock.Colour.GREEN,clock.Colour.GREEN,clock.Colour.YELLOW])
if outputSTL:
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    dial.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)