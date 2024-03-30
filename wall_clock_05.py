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
This is an attempt to make an eight day clock.

It has an asymetric design to try out making clock plates smaller. This works, but looks a bit odd.

It failed as the chain wheel couldn't take the weight (the lugs broke/bent) and the chain stretched.
It ran for about 4 days first though, proving that the going train can work. Plan is to remake this clock but with a symetric design and a cord wheel (this ended up being clock 06)
'''

outputSTL = False
if 'show_object' not in globals():
    outputSTL=True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_05_new"
clockOutDir="out"

# crutchLength=100

# train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
#pendulum period of 1.25 actually results in larger clock than period of 1
train=clock.GoingTrain(pendulum_period=1, fourth_wheel=True, escapement_teeth=30, max_weight_drop=1800, chain_at_back=False, chain_wheels=1, runtime_hours=180)

# train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)
# train.setRatios([[60, 14], [63, 12], [64, 12]])
train.set_ratios([[64, 12], [63, 12], [60, 14]])
# train.setRatios([[81, 12], [80, 9]])
# train.setRatios([[108, 10], [80, 9]])
train.set_chain_wheel_ratio([74, 11])

#chain size seems about right, trying reducing tolerance
#the 1.2mm 47links/ft regula chain
# train.genChainWheels(ratchetThick=5, wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075)#, wire_thick=0.85, width=3.6, inside_length=6.65-0.85*2, tolerance=0.1)
#new_chainwheel = PocketChainWheel2(chain=REGULA_8_DAY_1_05MM_CHAIN, ratchet_thick=5, ratchetOuterD=46, ratchetOuterThick=4.6, max_diameter=25, power_clockwise=False, loose_on_rod=True, arbor_d=3, fixings=2, wall_thick=1.5)
train.gen_chain_wheels2(clock.REGULA_8_DAY_1_05MM_CHAIN, ratchetThick=5, preferedDiameter=25, prefer_small=True)

train.print_info()

pendulumSticksOut=15

train.gen_gears(module_size=1, module_reduction=0.875, thick=3, chain_wheel_thick=6, useNyloc=False)#, chainModuleIncrease=1.1)

motionWorks = clock.MotionWorks(extra_height=10)

#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(bob_d=60, bob_thick=10)


#printed the base in 10, seems much chunkier than needed at the current width. Adjusting to 8 for the front plate
plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=8, pendulum_sticks_out=pendulumSticksOut, name="Wall 05", gear_train_layout=clock.GearTrainLayout.ROUND, heavy=True)

# hands = clock.Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
#outline of 0.6 works but this clock was actually printed with old cuckoo hands without an outline, so set without outline for the preview
hands = clock.Hands(style=clock.HandStyle.CUCKOO, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=60, thick=motionWorks.minute_hand_slot_height, outline_same_as_body=False)#, outline=0.6)

#no weight for this clock, using the cheap 2.5kg weight from cousins
#which needs a shell to look better!
shell = clock.WeightShell(45,220, twoParts=True, holeD=5)

assembly = clock.Assembly(plates, hands=hands, time_mins=47, pendulum=pendulum)

assembly.show_clock(show_object, bob_colours=[clock.Colour.PURPLE], motion_works_colours=[clock.Colour.LIGHTBLUE,clock.Colour.LIGHTBLUE,clock.Colour.BLUE])

if outputSTL:
    train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName, clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    dial.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    shell.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)
