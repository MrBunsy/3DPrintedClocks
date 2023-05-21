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
first attempt at a grasshopper. Plan:

Escapment on teh front of the clock (new)
pendulum on the back (new)
hyugens maintaining power using a loop of chain (new)

one day, but since we're using pulleys aiming for a drop of 1.5m

This worked (went for drop of 1.2m in the end) but needed some fudging to the grasshopper dimensions because the escape wheel and frame both "droop" in different directions.
There was also not enough space to put the motion works behind the escape wheel.
clock 15 fixed this and is otherwise teh same design.

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_14_grasshopper"
clockOutDir="out"
gearStyle = clock.GearStyle.HONEYCOMB


#pre-calculated good values for a 9.75 escaping arc
escapement = clock.GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361)

#TODO fix chain at back, there's some work to do in the arbours (and maybe plates)
train=clock.GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, maxWeightDrop=1200, usePulley=True,
                       chainAtBack=False, chainWheels=0, hours=28, huygensMaintainingPower=True)

train.calculateRatios(max_wheel_teeth=50, min_pinion_teeth=9, wheel_min_teeth=30, pinion_max_teeth=30, max_error=0.1)

# Trying the thinner 47 LPF regula chain
# train.genChainWheels(ratchetThick=4,  wire_thick=1.05,width=4.4, inside_length=8.4-1.05*2, tolerance=0.075, screwThreadLength=8)

#for the first draft let's stick to a chain I know works, and hope that we're not over its weight limit
# 61 links/ft 1-day regula chain. copied from clock 04
train.genChainWheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8)

#planning to put hte pendulum on the back
pendulumSticksOut=20

#just big enough module size that the escape wheel can be on the front and not clash with the hands arbour
train.genGears(module_size=1.6,moduleReduction=0.875, thick=3, chainWheelThick=4, useNyloc=False, style=gearStyle, pinionThickMultiplier=2, chainWheelPinionThickMultiplier=2)
train.printInfo(weight_kg=1)

motionWorks = clock.MotionWorks(extra_height=30, style=gearStyle)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(handAvoiderInnerD=100, bobD=70, bobThick=10)



dial = clock.Dial(120)


plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=6, pendulumSticksOut=pendulumSticksOut, name="clk 14",style=clock.ClockPlateStyle.VERTICAL, pendulumAtFront=False,
                                 backPlateFromWall=40, escapementOnFront=True)


hands = clock.Hands(style=clock.HandStyle.CUCKOO, secondLength=40, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
                    length=120, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
assembly = clock.Assembly(plates, hands=hands)

assembly.printInfo()

weight = clock.Weight(height=130, diameter=35)
weight.printInfo()

show_object(assembly.getClock())

if outputSTL:
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    dial.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    weight.outputSTLs(clockName, clockOutDir)
    # bigweight.outputSTLs(clockName+"_big", clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)
