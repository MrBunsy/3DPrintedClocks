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
Based on wall clock 07. Shortest pendulum that can provide a seconds hand. 30 hour runtime, but chain driven


TODO add the self-tapping bits to powered wheel

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_granny"
clockOutDir="out"
gearStyle = GearStyle.FLOWER


drop =1.5
lift =3
lock=1.5
escapement = AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, tooth_tip_angle=5, tooth_base_angle=4)

power = PocketChainWheel2(ratchet_thick=4, chain=REGULA_30_HOUR_CHAIN_older, max_diameter=21, ratchet_diameter=28, wall_thick=(13.2-11.82)-0.07, loose_on_rod=True)


print("chain wheel thick", power.get_height())

train=GoingTrain(pendulum_period=1.5, fourth_wheel=False, escapement=escapement, max_weight_drop=1900, chain_at_back=False, powered_wheels=0, runtime_hours=28, powered_wheel=power)

#, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4
# train.setEscapementDetails(drop=1.5, lift=3, lock=1.5)

train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)

#was 11.82mm thick in total (including washer)
# 61 links/ft 1-day regula chain. copied from clock 04
# train.gen_chain_wheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8)




#25 should comfortably stick out in front of the motion works
pendulumSticksOut=25

# train.gen_gears(module_size=1.25, module_reduction=0.875, thick=3, powered_wheel_thick=4, style=gearStyle, pinion_thick_multiplier=4, powered_wheel_pinion_thick_multiplier=4)

train.generate_arbors_dicts([
    {
        "wheel_thick": 4,
        "style": GearStyle.FLOWER,
        "pinion_at_front": True,
        "pinion_extension": 0,
        "pinion_type": PinionType.PLASTIC,
        "rod_diameter": 3,
        "module": 1.25
    },
    {
        "wheel_thick": 3,
        "style": GearStyle.FLOWER,
        "pinion_at_front": True,
        "pinion_extension": 0,
        "pinion_type": PinionType.PLASTIC,
        "rod_diameter": 3,
        "module": 1.09375,
        "pinion_thick": 16 - 0.45*2
    },
    {
        "wheel_thick": 3,
        "style": GearStyle.FLOWER,
        "pinion_at_front": False,
        "pinion_extension": 0,
        "pinion_type": PinionType.PLASTIC,
        "rod_diameter": 3,
        "pinion_thick": 12
    }
])

train.print_info(weight_kg=0.425)
# print(train.get_dicts_for_updating_to_generate_arbors())
motionWorks = MotionWorks(extra_height=pendulumSticksOut + 30, style=gearStyle)


#trying a thicker anchor and glue rather than nyloc
pendulum = Pendulum(bob_d=70, bob_thick=10, hand_avoider_inner_d=80)



dial = Dial(120)


plates = SimpleClockPlates(train, motionWorks, plate_thick=6, pendulum_sticks_out=pendulumSticksOut, name="Granny", gear_train_layout=GearTrainLayout.VERTICAL)

#old Plate distance 31.07
#Plate distance 31.069999999999997
print("plate distance", plates.plate_distance)

hands = Hands(style=HandStyle.SIMPLE, second_length=40, minute_fixing="square",
                    minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=100, thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False, include_seconds_hand=True)
# hands = Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)


#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = Assembly(plates, hands=hands, pendulum=pendulum, name=clockName)

assembly.print_info()

weight = Weight(height=130, diameter=35)
weight.printInfo()

# bigweight = Weight(height=125, diameter=45)
# bigweight.printInfo()
# show_object(train.getArbourWithConventionalNaming(0).get_assembled())
# show_object(train.getArbourWithConventionalNaming(0).poweredWheel.get_assembled())

# show_object(assembly.getClock())
assembly.show_clock(show_object, motion_works_colours=[Colour.LIGHTBLUE], with_rods=True)

if outputSTL:
    # train.output_STLs(clockName, clockOutDir)
    # motionWorks.output_STLs(clockName,clockOutDir)
    # pendulum.output_STLs(clockName, clockOutDir)
    # dial.output_STLs(clockName, clockOutDir)
    # plates.output_STLs(clockName, clockOutDir)
    # hands.output_STLs(clockName, clockOutDir)
    # weight.output_STLs(clockName, clockOutDir)
    # # bigweight.output_STLs(clockName+"_big", clockOutDir)
    # assembly.output_STLs(clockName, clockOutDir)
    assembly.get_BOM().export()