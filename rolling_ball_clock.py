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



from clocks import *

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
#
# if profile:
#     pr = cProfile.Profile()
#     pr.enable()

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

clock_name= "congreve_clock_47"
clockOutDir="out"
gear_style=GearStyle.CIRCLES
pendulumFixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS
plate_thick=6

#don't actually need an anchor, just a quick way to generate a gear train
escapement = AnchorEscapement(teeth=2)


power = SpringBarrel(pawl_angle=-math.pi * 3/4, click_angle=-math.pi * 1/4, base_thick=4, barrel_bearing=BEARING_12x18x4_FLANGED,
                     style=gear_style, wall_thick=8, ratchet_thick=8, spring=SMITHS_EIGHT_DAY_MAINSPRING,
                     ratchet_screws=MachineScrew(2, grub=True), seed_for_gear_styles=clock_name+"barrel", key_bearing=PlainBushing(12, fake_height=plate_thick))

#escape wheel this way around allows for a slightly larger diameter
train = GoingTrain(pendulum_period=30, wheels=3, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, powered_wheels=1,
                         runtime_hours=24, support_second_hand=True, escape_wheel_pinion_at_front=False, powered_wheel=power)

barrel_gear_thick = 8

moduleReduction=0.9#0.85

train.calculate_ratios(max_wheel_teeth=90, min_pinion_teeth=10, wheel_min_teeth=50, pinion_max_teeth=12, max_error=2, module_reduction=moduleReduction, loud=True,
                      allow_integer_ratio=False)
# train.set_ratios([[75, 9], [72, 10], [60, 24]])

train.set_powered_wheel_ratios([101,10])

pendulumSticksOut=10
backPlateFromWall=30

pinion_extensions = {}

powered_modules = [WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(2)]
#
# train.gen_gears(module_size=0.9, module_reduction=moduleReduction, thick=3, thickness_reduction=0.85, powered_wheel_thick=barrel_gear_thick, style=gear_style,
#                 powered_wheel_module_sizes=powered_modules, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True,
#                 pinion_extensions=pinion_extensions, lanterns=[0], pinion_thick_extra=3 + 2)

train.generate_arbors_dicts([
    {
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.0),
        "wheel_thick": barrel_gear_thick,
        "style": gear_style,
    },
    {
        "module":  WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.0),
        "pinion_type":PinionType.LANTERN
    },
    {
        "pinion_type":PinionType.LANTERN
    }
])


plates = RollingBallClockPlates(train, name="Congreve 32")


# hands = plates.get_hands()

# for arbor in plates.arbors_for_plate[:-1]:
#     show_object(arbor.get_assembled())

rolling_ball = RollingBallEscapement()

tray = rolling_ball.get_track_assembled()

show_object(tray)
out = "tray.stl"
print("Outputting ", out)
exporters.export(rolling_ball.get_track(), out)

# show_object(plates.get)
#
# assembly = Assembly(plates, hands=hands, time_seconds=30)#weights=[Weight(height=245,diameter=55)]
#
#
# if not outputSTL or True:
#     assembly.show_clock(show_object, hand_colours=[Colour.WHITE, Colour.BLACK, Colour.RED], motion_works_colours=[Colour.BRASS],
#                     bob_colours=[Colour.GOLD], with_rods=False, with_key=True, ratchet_colour=Colour.GOLD, dial_colours=[Colour.WHITE, Colour.BLACK], key_colour=Colour.GOLD)
#
# if outputSTL:
#     plates.output_STLs(clock_name, clockOutDir)
#     hands.output_STLs(clock_name, clockOutDir)
#     assembly.output_STLs(clock_name, clockOutDir)
#
# if profile:
#     pr.disable()
#     pr.print_stats(sort="calls")