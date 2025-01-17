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
import random
import os
import clocks as clock
from cadquery import exporters

'''
UNPRINTED

Experimental eight day grasshopper

latest idea: spring powered, but put the escape wheel BEHIND the back plate so it can be centred on the hands, resulting in a fairly compact shape
could put bearings on the escape wheel itself so it can use the same rod as the minute wheel

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass



clockName="wall_clock_18"
clockOutDir="out"
gearStyle = clock.GearStyle.FLOWER
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOR

escapement = clock.GrasshopperEscapement.get_harrison_compliant_grasshopper()

#TODO fix chain at back, there's some work to do in the arbours (and maybe plates)
train=clock.GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, max_weight_drop=1250, use_pulley=True,
                       chain_at_back=False, powered_wheels=1, runtime_hours=24 * 7 + 6, huygens_maintaining_power=True)

train.calculate_ratios(max_wheel_teeth=100, min_pinion_teeth=15, wheel_min_teeth=30, pinion_max_teeth=30, max_error=0.1)

# Trying the thinner 47 LPF regula chain
# train.genChainWheels(ratchetThick=4,  wire_thick=1.05,width=4.4, inside_length=8.4-1.05*2, tolerance=0.075, screwThreadLength=8)

#for the first draft let's stick to a chain I know works, and hope that we're not over its weight limit
# 61 links/ft 1-day regula chain. copied from clock 04
# train.genChainWheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8, holeD=3)
# train.genChainWheels(ratchetThick=4,wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075, screwThreadLength=8, holeD=3)
train.gen_chain_wheels2(clock.COUSINS_1_5MM_CHAIN, ratchetThick=6, arbourD=4, loose_on_rod=False, prefer_small=True, preferedDiameter=30,
                        fixing_screws=clock.MachineScrew(3, countersunk=True), ratchetOuterThick=6)


#pendulum is on the back
pendulumSticksOut=20


#trying to reduce plate size as much as possible - works, but means I don't think I have anywhere to attach an extra front plate
# train.genGears(module_size=1,moduleReduction=1.4, thick=3, chainWheelThick=4, style=gearStyle, pinionThickMultiplier=2.5, chainWheelPinionThickMultiplier=2.5)
#just big enough module size that the escape wheel can be on the front and not clash with the hands arbour
train.gen_gears(module_size=1, module_reduction=1.1, thick=2.4, powered_wheel_thick=5, style=gearStyle, pinion_thick_multiplier=2, powered_wheel_pinion_thick_multiplier=2,
                pendulum_fixing=pendulumFixing, escapement_split=True)
train.print_info(weight_kg=3)

motionWorks = clock.MotionWorks(extra_height=40, style=gearStyle, compact=True, thick=2)

pendulum = clock.Pendulum(bob_d=80, bob_thick=10)

#need thicker plates to holder the bigger bearings for the direct arbour pendulum fixing
plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=10, pendulum_sticks_out=pendulumSticksOut, name="clk 18", gear_train_layout=clock.GearTrainLayout.VERTICAL, pendulum_at_front=False,
                                 back_plate_from_wall=40, escapement_on_front=True, pendulum_fixing=pendulumFixing, bottom_pillars=2)
pulley = clock.LightweightPulley(diameter=plates.get_diameter_for_pulley())
print("Pulley thick = {}mm".format(pulley.get_total_thickness()))

hands = clock.Hands(style=clock.HandStyle.BREGUET, chunky=True, second_length=25, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=120, thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=True)
assembly = clock.Assembly(plates, hands=hands, pulley=pulley, pendulum=pendulum)

assembly.print_info()


weight_shell = clock.WeightShell(diameter=38, height=120, twoParts=False, solidBottom=True)

show_object(assembly.get_clock())

if outputSTL:

    train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    weight_shell.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)
    pulley.output_STLs(clockName, clockOutDir)
