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
import math
import cadquery as cq
from cadquery import exporters
import os
import cProfile



from clocks.plates import *

'''


'''
outputSTL = False
profile = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    # profile = True
    def show_object(*args, **kwargs):
        pass

if profile:
    pr = cProfile.Profile()
    pr.enable()

# class RollingBallGoingTrain(GoingTrain):
#     '''
#     The rolling ball isn't a going train optimised for being small - the escapement has a very large period so the going train has to actually be physically large enough
#     to have the escapement far enough away from the minute wheel
#     '''
#     def __init__(self, rolling_ball_escapement, style=GearStyle.CIRCLES):
#         # super().__init__(pendulum_period=rolling_ball_escapement.get_period(), pendulum_length_m=-1, wheels=3, fourth_wheel=None, escapement_teeth=30, chain_wheels=0, runtime_hours=30, chain_at_back=True, max_weight_drop=1800,
#         #                  escapement=None, escape_wheel_pinion_at_front=None, use_pulley=False, huygens_maintaining_power=False, minute_wheel_ratio=1, support_second_hand=False)
#         self.powered_wheels = 1
#         self.wheels = 3
#         self.powered_wheel = SpringBarrel(style=style)

clockName="congreve_clock_32"
clockOutDir="out"
gearStyle=GearStyle.CIRCLES
pendulumFixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS


#this much drop is needed to run reliably (I think it's the wiggle room from the m3 rods in 3mm bearings combined with a small escape wheel?) but a 0.25 nozzle is then needed to print well
lift=2
drop=3
lock=2
escapement = AnchorEscapement(drop=drop, lift=lift, teeth=2, lock=lock, tooth_tip_angle=3,
                              tooth_base_angle=3, style=AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2)
#escape wheel this way around allows for a slightly larger diameter
train = GoingTrain(pendulum_period=10, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, chain_wheels=1,
                         runtime_hours=24, support_second_hand=True, escape_wheel_pinion_at_front=False)

barrel_gear_thick = 8

moduleReduction=0.9#0.85
#train.gen_spring_barrel(click_angle=-math.pi*0.25)
#smiths ratios but with more teeth on the first pinion (so I can print it with two perimeters, with external perimeter at 0.435 and perimeter at 0.43)
#could swap the wheels round but I don't think I can get the pinions printable with two perimeters at any smaller a module
#[[61, 10], [62, 10]] auto generated but putting here to save time
train.gen_spring_barrel(pawl_angle=-math.pi*3/4, click_angle=-math.pi/4, ratchet_at_back=False, style=gearStyle, base_thick=barrel_gear_thick, wheel_min_teeth=40,
                        chain_wheel_ratios=[[46, 10]])
train.calculate_ratios(max_wheel_teeth=80, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=12, max_error=0.1, module_reduction=moduleReduction, loud=True,
                      allow_integer_ratio=True)
# train.set_ratios([[75, 9], [72, 10], [60, 24]])



pendulumSticksOut=10
backPlateFromWall=30

pinion_extensions = {}

powered_modules = [WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(2)]

train.gen_gears(module_size=0.9, module_reduction=moduleReduction, thick=3, thickness_reduction=0.85, powered_wheel_thick=barrel_gear_thick, style=gearStyle,
                powered_wheel_module_sizes=powered_modules, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True,
                pinion_extensions=pinion_extensions, lanterns=[0], pinion_thick_extra=3 + 2)


train.get_arbour_with_conventional_naming(0).print_screw_length()

plates = RollingBallClockPlates(train, name="Congreve 32")


hands = plates.get_hands()


assembly = Assembly(plates, hands=hands, time_seconds=30)#weights=[Weight(height=245,diameter=55)]


if not outputSTL or True:
    assembly.show_clock(show_object, hand_colours=[Colour.WHITE, Colour.BLACK, Colour.RED], motion_works_colours=[Colour.BRASS],
                    bob_colours=[Colour.GOLD], with_rods=False, with_key=True, ratchet_colour=Colour.GOLD, dial_colours=[Colour.WHITE, Colour.BLACK], key_colour=Colour.GOLD)

if outputSTL:
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)

if profile:
    pr.disable()
    pr.print_stats(sort="calls")