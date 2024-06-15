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

'''
Simple one day clock with shortest pendulum I can manage and first test of the ropewheel

Attempting to reduce plate distance and size of the one day clock

works, but I can't get rope wheels working reliably without big counterweights, so I'm not planning to persue this any further

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_11"
clockOutDir="out"
gearStyle=clock.GearStyle.CARTWHEEL

# drop =1
# lift =2.5
# lock=1.5
# escapement = clock.Escapement(drop=drop, lift=lift, teeth=48, lock=lock,  toothTipAngle=5, toothBaseAngle=4)

drop =1.5
lift =3
lock=1.5
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, tooth_tip_angle=5, tooth_base_angle=4)

train=clock.GoingTrain(pendulum_period=1, fourth_wheel=False, escapement=escapement, max_weight_drop=2000, chain_at_back=False, chain_wheels=0, runtime_hours=30)

#note, going below a module of 0.85 makes the pinions are bit hard to print - can do it, but I think it's worth sticking with 0.85 as an absolute minimum with a 0.4mm nozzle
moduleReduction=0.9
train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction)


# train.genCordWheels(ratchetThick=2.2, cordThick=1, cordCoilThick=6, style=gearStyle)
# train.genChainWheels(ratchetThick=2.5, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075,screwThreadLength=8)
train.gen_rope_wheels()

train.print_info()

pendulumSticksOut=8+15

#module size of 0.85 looks printable without stringing!
train.gen_gears(module_size=0.85, module_reduction=moduleReduction, thick=2, thickness_reduction=0.9, powered_wheel_thick=2, pinion_thick_multiplier=3, powered_wheel_pinion_thick_multiplier=3, style=gearStyle, ratchet_screws=clock.MachineScrew(2, countersunk=True))

train.get_arbour_with_conventional_naming(0).print_screw_length()
motionWorks = clock.MotionWorks(extra_height=15, style=gearStyle)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(bob_d=70, bob_thick=10)



dial = clock.Dial(120)


plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=6, pendulum_sticks_out=pendulumSticksOut, name="Wall 11", gear_train_layout=clock.GearTrainLayout.VERTICAL)


# hands = clock.Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=17)

hands = clock.Hands(style="cuckoo", minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=100, thick=motionWorks.minute_hand_slot_height, outline_same_as_body=False, outline=0.9)

#wall thick of 1.8 appears to work, but feels a bit more brittle than I'd like
weight = clock.Weight(height=150, diameter=35, wallThick=2.25)
weight.printInfo()

counterweight = clock.Weight(height=100, diameter=18, wallThick=1.35, bolt=clock.MachineScrew(2))
counterweight.printInfo()


assembly = clock.Assembly(plates, hands=hands,weights=[weight, counterweight], pendulum=pendulum)



# show_object(assembly.getClock())
assembly.show_clock(show_object, motion_works_colours=[clock.Colour.LIGHTBLUE], gear_colours=[clock.Colour.RED, clock.Colour.ORANGE, clock.Colour.YELLOW, clock.Colour.GREEN, clock.Colour.BLUE, clock.Colour.PURPLE])

if outputSTL:
    train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    dial.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    weight.output_STLs(clockName, clockOutDir)
    counterweight.output_STLs(clockName+"_counter", clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)
