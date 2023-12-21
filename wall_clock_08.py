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

train=clock.GoingTrain(pendulum_period=1.25, fourth_wheel=False, escapement=escapement, max_weight_drop=1700, chain_at_back=False, chain_wheels=0, runtime_hours=30)

train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)

train.gen_cord_wheels(ratchet_thick=5, cord_thick=2, cord_coil_thick=11)

train.print_info()

pendulumSticksOut=8

train.gen_gears(module_size=1.25, module_reduction=0.875, thick=3, chain_wheel_thick=6, useNyloc=False)


motionWorks = clock.MotionWorks(extra_height=pendulumSticksOut + 30)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(bob_d=70, bob_thick=10)



dial = clock.Dial(120)


plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=6, pendulum_sticks_out=pendulumSticksOut, name="Wall 07", style=clock.ClockPlateStyle.VERTICAL)


hands = clock.Hands(style="simple_rounded", minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=100, thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)


#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands, pendulum=pendulum)

weight = clock.Weight(height=100, diameter=35)
weight.printInfo()

bigweight = clock.Weight(height=125, diameter=45)
bigweight.printInfo()

show_object(assembly.get_clock())

if outputSTL:
    train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    dial.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    weight.output_STLs(clockName, clockOutDir)
    bigweight.output_STLs(clockName+"_big", clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)
