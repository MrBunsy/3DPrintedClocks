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

first attempt at a deadbeat on teh front, to match the grasshopper
one day, but since we're using pulleys aiming for a drop of 1.5m

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_16_grasshopper"
clockOutDir="out"
gearStyle = clock.GearStyle.FLOWER


drop =1.5
lift =3
lock=1.5
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4, forceDiameter=True, diameter=100)

train=clock.GoingTrain(pendulum_period=1.25, fourth_wheel=False, escapement=escapement, max_weight_drop=1200, use_pulley=True,
                       chain_at_back=False, chain_wheels=0, runtime_hours=28, huygens_maintaining_power=True)

train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)

# 61 links/ft 1-day regula chain. copied from clock 04
train.gen_chain_wheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8, holeD=3)

#pendulum is on the back
pendulumSticksOut=20


#trying to reduce plate size as much as possible - works, but means I don't think I have anywhere to attach an extra front plate
# train.genGears(module_size=1,moduleReduction=1.4, thick=3, chainWheelThick=4, useNyloc=False, style=gearStyle, pinionThickMultiplier=2.5, chainWheelPinionThickMultiplier=2.5)
#just big enough module size that the escape wheel can be on the front and not clash with the hands arbour
train.gen_gears(module_size=1, module_reduction=0.875, thick=3, chain_wheel_thick=4, useNyloc=False, style=gearStyle, pinion_thick_multiplier=2, chain_wheel_pinion_thick_multiplier=2)

train.print_info(weight_kg=0.75)

motionWorks = clock.MotionWorks(extra_height=40, style=gearStyle, compact=True, thick=2)

pendulum = clock.Pendulum(bob_d=80, bob_thick=10)



dial = clock.Dial(120)


plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=6, pendulum_sticks_out=pendulumSticksOut, name="wall clock 16", style=clock.ClockPlateStyle.VERTICAL, pendulum_at_front=False,
                                 back_plate_from_wall=40, escapement_on_front=True)
pulley = clock.LightweightPulley(diameter=plates.get_diameter_for_pulley())
print("Pulley thick = {}mm".format(pulley.get_total_thickness()))

hands = clock.Hands(style=clock.HandStyle.SPADE, chunky=True, second_length=25, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=120, thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False)
assembly = clock.Assembly(plates, hands=hands, timeHours=12, pulley=pulley, pendulum=pendulum)

assembly.printInfo()



weight = clock.Weight(height=130, diameter=35)
weight.printInfo()

show_object(assembly.get_clock())

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
    pulley.output_STLs(clockName, clockOutDir)
