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
The first iteration of this clock was just some parts before I realised I needed to tweak the ratios. 
Wall_clock_02 was the new ratios and actually got finished
'''

if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_02"
clockOutDir="out"

crutchLength=100

# train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
train=clock.GoingTrain(pendulum_period=1.5, fourth_wheel=False, escapement_teeth=30, max_weight_drop=2100)

train.calculate_ratios()

train.print_info()

train.gen_chain_wheels()
train.gen_gears(module_size=1.2, module_reduction=0.85)

show_object(train.arbors[0])
print("anchor centre distnace", train.escapement.anchor_centre_distance)
train.output_STLs(clockName, clockOutDir)

motionWorks = clock.MotionWorks()
motionWorks.output_STLs(clockName,clockOutDir)

#HACK for now using same bearing as rest of the gears for the anchor
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3)

pendulum.output_STLs(clockName, clockOutDir)


plates = clock.SimpleClockPlates(train, motionWorks, pendulum)
plates.output_STLs(clockName, clockOutDir)

hands = clock.Hands(minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=50, thick=motionWorks.minute_hand_slot_height)
hands.output_STLs(clockName, clockOutDir)