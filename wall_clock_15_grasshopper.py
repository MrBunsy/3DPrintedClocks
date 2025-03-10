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
from clocks import *

'''
second attempt at a grasshopper. Same as teh first attempt (clock 14) but with space to fit hands on properly and less drooping of the escape wheel and frame
A regenerated clock 14 will benefit from the improvements to the plates, but this rejigged the gear train so there's more space

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_15_grasshopper_retrofit"
clockOutDir="out"
gearStyle = GearStyle.HONEYCOMB

pendulumFixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

need_space = SimpleClockPlates.get_lone_anchor_bearing_holder_thick() + WASHER_THICK_M3

#pre-calculated good values for a 9.75 escaping arc
#also -1 from frame_thick because I've reduced front_anchor_from_plate by one
escapement = GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361, frame_thick=10 - need_space+1, composer_min_distance=need_space)#GrasshopperEscapement.get_harrison_compliant_grasshopper(frame_thick=10-need_space)#(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361)

power = PocketChainWheel2(ratchet_thick=4, loose_on_rod=False)

#TODO fix chain at back, there's some work to do in the arbours (and maybe plates)
train=GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, max_weight_drop=1200, use_pulley=True,
                       chain_at_back=False, powered_wheels=0, runtime_hours=28, huygens_maintaining_power=True, powered_wheel=power)

train.calculate_ratios(max_wheel_teeth=100, min_pinion_teeth=15, wheel_min_teeth=30, pinion_max_teeth=30, max_error=0.1)

# Trying the thinner 47 LPF regula chain
# train.genChainWheels(ratchetThick=4,  wire_thick=1.05,width=4.4, inside_length=8.4-1.05*2, tolerance=0.075, screwThreadLength=8)

#for the first draft let's stick to a chain I know works, and hope that we're not over its weight limit
# 61 links/ft 1-day regula chain. copied from clock 04
# train.gen_chain_wheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8, holeD=3)

#pendulum is on the back
pendulumSticksOut=20


#trying to reduce plate size as much as possible - works, but means I don't think I have anywhere to attach an extra front plate
# train.genGears(module_size=1,moduleReduction=1.4, thick=3, chainWheelThick=4, style=gearStyle, pinionThickMultiplier=2.5, chainWheelPinionThickMultiplier=2.5)
#just big enough module size that the escape wheel can be on the front and not clash with the hands arbour
train.gen_gears(module_size=1.1, module_reduction=1.1, thick=3, powered_wheel_thick=4, style=gearStyle, pinion_thick_multiplier=2, powered_wheel_pinion_thick_multiplier=2,
                pendulum_fixing=pendulumFixing, escapement_split=True)
train.print_info(weight_kg=1)

motionWorks = MotionWorks(extra_height=40, style=gearStyle, compact=True, thick=2)

pendulum = Pendulum(bob_d=80, bob_thick=10, hand_avoider_inner_d=100)

plates = SimpleClockPlates(train, motionWorks, pendulum, plate_thick=6, pendulum_sticks_out=pendulumSticksOut, name="wall clock 15", gear_train_layout=GearTrainLayout.VERTICAL, pendulum_at_front=False,
                                 back_plate_from_wall=40, escapement_on_front=True, pendulum_fixing=pendulumFixing, direct_arbor_d=6)
pulley = LightweightPulley(diameter=plates.get_diameter_for_pulley())
print("Pulley thick = {}mm".format(pulley.get_total_thickness()))

hands = Hands(style=HandStyle.SPADE, chunky=True, second_length=25, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=120, thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False)
assembly = Assembly(plates, hands=hands, time_hours=12, pulley=pulley, pendulum=pendulum)
#
# assembly.print_info()
#
#
#
# weight = Weight(height=130, diameter=50)
# weight.printInfo()
# ring_colour = assembly.gear_colours[(assembly.going_train.wheels + assembly.going_train.powered_wheels + 1) % len(assembly.gear_colours)]
# show_object(pendulum.get_hand_avoider().translate(assembly.ring_pos), options={"color": Colour.YELLOW}, name="Pendulum Ring")

# show_object(assembly.getClock())
assembly.show_clock(show_object)
#
if outputSTL:
    # train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    # weight.output_STLs(clockName, clockOutDir)
    # bigweight.output_STLs(clockName+"_big", clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)
    pulley.output_STLs(clockName, clockOutDir)
