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
UNPRINTED

clock 06 redone:

Eight days, 1s tick with second hand.

Trying to make this one as small as possible, and going to increase the threaded rod through the cord wheel to m4
Turns out that I can't make it any smaller without reducing the rod size for the escape wheel. Parking this idea for now and just re-printing a finished clock 6
'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_09"
clockOutDir="out"
gearStyle=clock.GearStyle.SIMPLE4

# drop =1.5
# lift =3
# lock=1.5
lift=4
drop=2
lock=2
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

train = clock.GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, max_weight_drop=1800, chain_at_back=False, chain_wheels=1, runtime_hours=180, max_chain_wheel_d=28)

train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)
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
train.gen_cord_wheels(ratchet_thick=5, cord_thick=2, cord_coil_thick=17, style=gearStyle, use_key=True, rod_metric_thread=4)

train.calculate_powered_wheel_ratios()

train.print_info()

pendulumSticksOut=20

train.gen_gears(module_size=1
                , moduleReduction=0.875, thick=2, chainWheelThick=6, useNyloc=False, pinionThickMultiplier=4, style=gearStyle, chain_module_increase=1, chainWheelPinionThickMultiplier=2)#, chainModuleIncrease=1.1)


motionWorks = clock.MotionWorks(extra_height=pendulumSticksOut + 30, style=gearStyle, thick=2)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(bob_d=80, bob_thick=10)



dial = clock.Dial(120)

plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=8, pendulum_sticks_out=pendulumSticksOut, name="Wall 06", style=clock.ClockPlateStyle.VERTICAL, motion_works_above=True, heavy=True)


hands = clock.Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=25)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)


#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands, timeMins=0, timeSeconds=30, pendulum=pendulum)


show_object(assembly.get_clock())
# show_object(train.getArbourWithConventionalNaming(0).getShape())

if outputSTL:
    train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    dial.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)