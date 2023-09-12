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
1 Day chain driven clock, short pendulum and no second hand, this was the first to use the new plate design and should remain compatible with future changes to the plate design
The first build of this had the maths for plate distance broken

Wall clock 03 proved the new design of clock plates and that smaller gears can work.

This is an attempt to minimise the new clock plates further
'''

outputSTL=False
if 'show_object' not in globals():
    # don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_04c"
clockOutDir="out"

# drop =1.5
# lift =3
# lock=1.5
# escapement = clock.Escapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)
#
#


# crutchLength=100

# train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
#pendulum period of 1.25 actually results in larger clock than period of 1
train=clock.GoingTrain(pendulum_period=1.25, fourth_wheel=False, escapement_teeth=30, max_weight_drop=2100, chain_at_back=False, escape_wheel_pinion_at_front=False)#, escapement=escapement)

# train.calculateRatios(max_wheel_teeth=120, min_pinion_teeth=9)
# train.setRatios([[81, 12], [80, 9]])
train.set_ratios([[108, 10], [80, 9]])
# 61 links/ft 1-day regula chain. Size seems about right, trying reducing tolerance
train.gen_chain_wheels(ratchetThick=3, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8)
# train.genCordWheels(ratchetThick=4, cordThick=2, cordCoilThick=11)

train.print_info()
'''
{'train': [[81, 12], [80, 9]]}
pendulum length: 0.9939608115313336m period: 2s
escapement time: 60s teeth: 30
cicumference: 68.60000000000001, run time of:28.9hours
'''
pendulumSticksOut=30
#keeping chain wheel slightly thicker so it might be less wonky on the rod?
train.gen_gears(module_size=1, moduleReduction=0.85, thick=2, chainWheelThick=5, useNyloc=False, escapeWheelMaxD=0.75)


motionWorks = clock.MotionWorks(extra_height=40)


#trying using same bearings and having the pendulum rigidly fixed to the anchor's arbour
pendulum = clock.Pendulum(hand_avoider_inner_d=50, bob_d=60, bob_thick=10)



# dial = clock.Dial(110, support_length=pendulumSticksOut + 20)

#printed the base in 10, seems much chunkier than needed at the current width. Adjusting to 8 for the front plate
plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=6, pendulum_sticks_out=pendulumSticksOut, name="Wall 04")#, dial=dial)


hands = clock.Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=80, thick=motionWorks.minute_hand_slot_height, outline=1, outlineSameAsBody=False)


weight = clock.Weight(height=100, diameter=35)

weight.printInfo()

assembly = clock.Assembly(plates, hands=hands, pendulum=pendulum)

# show_object(assembly.getClock())
assembly.show_clock(show_object)

if outputSTL:
    train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    weight.output_STLs(clockName, clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)