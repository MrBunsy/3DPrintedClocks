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
import clocks as clock
import math
'''
Wall Clock 01/02 has proven that the basic design of gears and escapement can work, but the frame was lacking - it bend with the weight
and this caused the gears to mesh badly and sometimes seize. It was also top heavy.

The main aim of this clock is to produce a design which can actually be hung on the wall and see if I can minimise friction a bit.
 
I'm still planning to stick with the same basic going train as the first clock, but trying thinner gears to see if that has slightly less friction
tempted to try improving the efficiency of the escapement, but since I know the current one works I'm reluctant. Might try swapping in a different one later
'''

generate_stl = False
if 'show_object' not in globals():
    generate_stl = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_03_v3"
clockOutDir="out"

# crutchLength=100

#keeping the old chain from an eight day hubert herr
powered_wheel = clock.PocketChainWheel(ratchet_thick=5, power_clockwise=True, max_circumference=70,
                                 wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15,
                                              holeD=3, screwThreadLength=10)


# train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
#pendulum period of 1.25 actually results in larger clock than period of 1
escapement = clock.AnchorEscapement.get_with_optimal_pallets(teeth=30, type=clock.EscapementType.RECOIL)#, style=clock.AnchorStyle.STRAIGHT)
train=clock.GoingTrain(pendulum_period=1.5, fourth_wheel=False, escapement_teeth=30, max_weight_drop=2100, chain_at_back=False, powered_wheel=powered_wheel, escapement=escapement)#

# train.calculateRatios()
#for one that works with the latest code
# train.set_ratios([[81, 12], [80, 9]])
#to retrofit a new ratchet:
train.set_ratios([[86, 10], [93, 10]])
# train.print_info()
'''
{'time': 3599.1000000000004, 'train': [[86, 10], [93, 10]], 'error': 0.8999999999996362, 'ratio': 79.98, 'teeth': -0.20999999999999996}
pendulum length: 0.5591029564863751m period: 1.5s
escapement time: 45.0s teeth: 30
cicumference: 67.25, run time of:29.4hours
'''

#chain size seems about right, trying reducing tolerance
# train.gen_chain_wheels(ratchetThick=5, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.1)

# train.set_powered_wheel_ratios()

pendulumSticksOut=20

train.gen_gears(module_size=1, module_reduction=0.85, thick=3, escape_wheel_max_d=0.75)
# train.output_STLs(clockName, clockOutDir)
'''
click inner d = 22.281692032865347
outer_thick = 4.45633840657307
outer d = 44.563384065730695
click_teeth = 8
outer_diameter=ratchetOuterD, inner_radius=0.9999 * self.outerDiameter / 2, thick=ratchet_thick, blocks_clockwise=power_clockwise, outer_thick=ratchetOuterThick,
                                    screws_radius=self.outerRadius*0.5, pawl_screws=MachineScrew(2, type=MachineScrewType.COUNTERSUNK), offset_angle=math.pi*0.25
'''
powered_wheel.ratchet = clock.InvertedRatchet(outer_diameter=44.563384065730695, inner_radius=powered_wheel.ratchet.get_inner_radius(), thick=powered_wheel.ratchet.thick,
                                              blocks_clockwise=powered_wheel.ratchet.is_clockwise(), outer_thick=4.45633840657307,
                                              screws_radius=powered_wheel.ratchet.screws_radius, pawl_screws=clock.MachineScrew(2, type=clock.MachineScrewType.COUNTERSUNK),
                                              offset_angle=math.pi*0.25, click_teeth = 8, click_wide=1.7/2)
motionWorks = clock.MotionWorks(extra_height=pendulumSticksOut + 20)
# motionWorks.output_STLs(clockName,clockOutDir)

#trying using same bearings and having the pendulum rigidly fixed to the anchor's arbour
pendulum = clock.Pendulum( hand_avoider_inner_d=80)#
#pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=8, nutMetricSize=3, crutchLength=0)

# pendulum.output_STLs(clockName, clockOutDir)

#printed the base in 10, seems much chunkier than needed at the current width. Adjusting to 8 for the front plate
plates = clock.SimpleClockPlates(train, motionWorks, plate_thick=8, back_plate_thick=10, pendulum_sticks_out=pendulumSticksOut)
# plates.output_STLs(clockName, clockOutDir)

hands = clock.Hands(minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=100, thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False)
# hands.output_STLs(clockName, clockOutDir)

assembly = clock.Assembly(plates, hands=hands, pendulum=pendulum, name=clockName)

assembly.show_clock(show_object, gear_colours=[clock.Colour.RED, clock.Colour.YELLOW, clock.Colour.LIGHTGREEN, clock.Colour.BLUE])

# show_object(train.powered_wheel.get_model())

if generate_stl:
    assembly.get_BOM().export()
# else:

