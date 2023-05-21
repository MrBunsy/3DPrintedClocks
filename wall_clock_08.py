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
import clocks.clock as clock

'''
UNPRINTED

An attempt at a smaller (but still only 1.25s) pendulum, otherwise same as clock 07: one day, cord with second complication

never saw light of day, I can't reliably get teh anchor escapement with enough teeth
'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_08"
clockOutDir="out"



drop =1.5
lift =2
lock=1.5
teeth = 48
toothTipAngle = 4
toothBaseAngle = 3
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=48, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=toothTipAngle, toothBaseAngle=toothBaseAngle)

train=clock.GoingTrain(pendulum_period=1.25, fourth_wheel=False, escapement=escapement, maxWeightDrop=1700, chainAtBack=False, chainWheels=0, hours=30)

train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)

train.genCordWheels(ratchetThick=5, cordThick=2, cordCoilThick=11)

train.printInfo()

pendulumSticksOut=8

train.genGears(module_size=1.25,moduleReduction=0.875, thick=3, chainWheelThick=6, useNyloc=False)


motionWorks = clock.MotionWorks(extra_height=pendulumSticksOut + 30)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(bobD=70, bobThick=10)



dial = clock.Dial(120)


plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=6, pendulumSticksOut=pendulumSticksOut, name="Wall 07",style=clock.ClockPlateStyle.VERTICAL)


hands = clock.Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)


#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands)

weight = clock.Weight(height=100, diameter=35)
weight.printInfo()

bigweight = clock.Weight(height=125, diameter=45)
bigweight.printInfo()

show_object(assembly.get_clock())

if outputSTL:
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    dial.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    weight.outputSTLs(clockName, clockOutDir)
    bigweight.outputSTLs(clockName+"_big", clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)
