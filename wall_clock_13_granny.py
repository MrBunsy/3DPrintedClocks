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
Based on wall clock 07. Shortest pendulum that can provide a seconds hand. 30 hour runtime, but chain driven

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_granny"
clockOutDir="out"
gearStyle = clock.GearStyle.FLOWER


drop =1.5
lift =3
lock=1.5
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

train=clock.GoingTrain(pendulum_period=1.5, fourth_wheel=False, escapement=escapement, max_weight_drop=1900, chain_at_back=False, chain_wheels=0, runtime_hours=28)

#, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4
# train.setEscapementDetails(drop=1.5, lift=3, lock=1.5)

train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)

# train.genCordWheels(ratchetThick=5, cordThick=1, cordCoilThick=11, style=gearStyle)
# 61 links/ft 1-day regula chain. copied from clock 04
train.gen_chain_wheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8)


#25 should comfortably stick out in front of the motion works
pendulumSticksOut=25

train.gen_gears(module_size=1.25, moduleReduction=0.875, thick=3, chainWheelThick=4, useNyloc=False, style=gearStyle, pinionThickMultiplier=4, chainWheelPinionThickMultiplier=4)
train.print_info(weight_kg=0.425)

motionWorks = clock.MotionWorks(extra_height=pendulumSticksOut + 30, style=gearStyle)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(bob_d=70, bob_thick=10)



dial = clock.Dial(120)


plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=6, pendulum_sticks_out=pendulumSticksOut, name="Granny", style=clock.ClockPlateStyle.VERTICAL)


hands = clock.Hands(style=clock.HandStyle.CUCKOO, secondLength=40, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)


#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands, pendulum=pendulum)

assembly.printInfo()

weight = clock.Weight(height=130, diameter=35)
weight.printInfo()

# bigweight = clock.Weight(height=125, diameter=45)
# bigweight.printInfo()
# show_object(train.getArbourWithConventionalNaming(0).get_assembled())
# show_object(train.getArbourWithConventionalNaming(0).poweredWheel.get_assembled())

# show_object(assembly.getClock())
assembly.show_clock(show_object, motion_works_colours=[clock.Colour.LIGHTBLUE])

if outputSTL:
    train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    dial.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    weight.output_STLs(clockName, clockOutDir)
    # bigweight.output_STLs(clockName+"_big", clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)
