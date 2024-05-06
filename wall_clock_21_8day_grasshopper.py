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
This will be both a complete clock and produce retrofit components for grasshoppers 14 and 15, for testing a retrofit to the xmas clock
'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

# random.seed(6)
random.seed(7)

clockName="wall_clock_21_grasshopper"
clockOutDir="out"
gearStyle = clock.GearStyle.CURVES
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

need_space = clock.SimpleClockPlates.get_lone_anchor_bearing_holder_thick() + clock.WASHER_THICK_M3

#pre-calculated good values for a 9.75 escaping arc
#also -1 from frame_thick because I've reduced front_anchor_from_plate by one
escapement = clock.GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361, frame_thick=10 - need_space+1, composer_min_distance=need_space)#clock.GrasshopperEscapement.get_harrison_compliant_grasshopper(frame_thick=10-need_space)#(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361)

#TODO fix chain at back, there's some work to do in the arbours (and maybe plates)
train=clock.GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, max_weight_drop=1200, use_pulley=True,
                       chain_at_back=False, chain_wheels=1, runtime_hours=7 * 24 + 6, huygens_maintaining_power=True)

train.calculate_ratios(max_wheel_teeth=100, min_pinion_teeth=15, wheel_min_teeth=30, pinion_max_teeth=30, max_error=0.1)

# Trying the thinner 47 LPF regula chain
# train.genChainWheels(ratchetThick=4,  wire_thick=1.05,width=4.4, inside_length=8.4-1.05*2, tolerance=0.075, screwThreadLength=8)

#for the first draft let's stick to a chain I know works, and hope that we're not over its weight limit
# 61 links/ft 1-day regula chain. copied from clock 04
# train.genChainWheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8, holeD=3)
train.gen_chain_wheels2(clock.COUSINS_1_5MM_CHAIN, ratchetThick=4, arbourD=4, loose_on_rod=False, prefer_small=True, preferedDiameter=35, fixing_screws=clock.MachineScrew(3, countersunk=True))
# train.genChainWheels(ratchetThick=4,wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075, screwThreadLength=8, holeD=3)


#pendulum is on the back
pendulumSticksOut=20


#trying to reduce plate size as much as possible - works, but means I don't think I have anywhere to attach an extra front plate
# train.genGears(module_size=1,moduleReduction=1.4, thick=3, chainWheelThick=4, style=gearStyle, pinionThickMultiplier=2.5, chainWheelPinionThickMultiplier=2.5)
#just big enough module size that the escape wheel can be on the front and not clash with the hands arbour
train.gen_gears(module_size=1, module_reduction=1, thick=3, chain_wheel_thick=4, style=gearStyle, pinion_thick_multiplier=2, chain_wheel_pinion_thick_multiplier=2, pendulum_fixing=pendulumFixing)
train.print_info(weight_kg=0.5)

motionWorks = clock.MotionWorks(extra_height=20, style=gearStyle, compact=True, thick=2)

pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=80, bob_thick=10)

# dial = clock.Dial(outside_d=200, bottom_fixing=True, top_fixing=False, style=clock.DialStyle.LINES_ARC)
dial = None

plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=10, pendulum_sticks_out=pendulumSticksOut, name="clk 21", gear_train_layout=clock.GearTrainLayout.VERTICAL, pendulum_at_front=False,
                                 back_plate_from_wall=40, escapement_on_front=True, pendulum_fixing=pendulumFixing, heavy=True, extra_heavy=True, dial=dial, pillars_separate=True,
                                 chain_through_pillar_required=True, huygens_wheel_min_d=30, fixing_screws=clock.MachineScrew(4, countersunk=True), allow_bottom_pillar_height_reduction=True)
pulley = clock.LightweightPulley(diameter=plates.get_diameter_for_pulley())
print("Pulley thick = {}mm".format(pulley.get_total_thickness()))

pulley_no_pipe = clock.LightweightPulley(diameter=plates.get_diameter_for_pulley(), use_steel_rod=False)

hands = clock.Hands(style=clock.HandStyle.CIRCLES, chunky=True, second_length=25, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=120, thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=True)
assembly = clock.Assembly(plates, hands=hands, pulley=pulley, pendulum=pendulum)

assembly.printInfo()


weight_shell = clock.WeightShell(diameter=38, height=120, twoParts=False, solidBottom=True)

# show_object(plates.get_front_anchor_bearing_holder())
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
    pulley_no_pipe.output_STLs(clockName+"_no_pipe", clockOutDir)

    # pretty_bob.output_STLs(clockName, clockOutDir)
    # pretty_hand_avoider.output_STLs(clockName, clockOutDir)

    # out = os.path.join(clockOutDir, "anchor_white.stl")
    # print("Outputting ", out)
    # exporters.export(escapement.star_inset.rotate((0, 0, 0), (1, 0, 0), 180).translate((0,0,escapement.get_anchor_thick())), out)
    #
    # for i in ["_a", "_b", "_c"]:
    #     train.output_STLs(clockName+i, clockOutDir)
