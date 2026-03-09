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

from clocks import *

'''

Thought I'd do a quick experiment to see what clock 32 looked like weight driven.

current answer: struggling to find a good gear ratio that works. can be done with very large barrel and short drop.

will try with a month duration and see how that looks (clock 25 seems relatively successful!)

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_37"
clockOutDir="out"
gearStyle=GearStyle.CIRCLES
pendulumFixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

#after a huge amount of faffing about, the problem was the bearings, not the escapement. So I've used the new auto-calculated efficient escapement for a retrofit.
escapement = AnchorEscapement.get_with_optimal_pallets(teeth=30, drop_deg=2.75, lock_deg=1.5, wheel_thick=2.5)

# power = CordBarrel(ratchet_thick=6, rod_metric_size=4, cord_thick=1, thick=15, style=gearStyle,
#                          use_key=True, diameter=45, loose_on_rod=False, ratchet_diameter=30, traditional_ratchet=True, cap_diameter=65)


powered_wheel = PocketChainWheel2(chain=COUSINS_1_5MM_CHAIN, ratchet_thick=7, max_diameter=25, ratchet_diameter=35,
                                  fixing_screws=MachineScrew(3, type=MachineScrewType.COUNTERSUNK), wall_thick=1.5)
train = GoingTrain(pendulum_period=1, wheels=4, escapement=escapement, max_weight_drop=1600, use_pulley=True, chain_at_back=False,
                         powered_wheels=1, runtime_hours=32 * 24, support_second_hand=False, powered_wheel=powered_wheel)

barrel_gear_thick = 8

moduleReduction=0.95#0.85

#wall thick of 9 seemed fine, but I want it to be consistent with the arbor
#larger barrel wheel actually works out at a smaller plate than having a larger intermediate wheel
# train.gen_spring_barrel(spring=SMITHS_EIGHT_DAY_MAINSPRING, pawl_angle=math.pi, click_angle=-math.pi/2, ratchet_at_back=True, style=gearStyle, base_thick=barrel_gear_thick,
#                         wall_thick=10, chain_wheel_ratios=[[64, 10], [64, 10]], extra_barrel_height=1.5)
# train.gen_cord_wheels(ratchet_thick=6, rod_metric_thread=4, cord_thick=1, cord_coil_thick=15, style=gearStyle, use_key=True, prefered_diameter=60, loose_on_rod=False, prefer_small=True)

train.calculate_powered_weight_wheel_info()
# train.calculate_powered_wheel_ratios(prefer_small=True, wheel_min=20, prefer_large_second_wheel=False)

#TODO one screw goes straight through the hole used to tie the cord! printed clock is assembled with just three screws
#also reduced ratchet diameter slightly after initial print as the pawl looks like it can bump into the next pinion
# train.gen_cord_wheels(ratchet_thick=8, rod_metric_thread=4, cord_thick=1, cord_coil_thick=14, style=gearStyle, use_key=True, prefered_diameter=55, loose_on_rod=False, prefer_small=True,
#                       min_wheel_teeth=70, traditional_ratchet=True, cap_diameter=65, ratchet_diameter=30)

train.calculate_powered_wheel_ratios(pinion_min=10, pinion_max=20, wheel_min=50, wheel_max=200, prefer_large_second_wheel=False)
# train.chain_wheel_ratios = [[55, 10], [64, 10]]
# train.chain_wheel_ratios = [[58,10], [61,10]]

train.set_ratios([[65, 14], [60, 13], [56, 10]])

pendulumSticksOut=10
backPlateFromWall=30
dial_d = 205
dial_width=25

pinion_extensions = {0:1, 1:15, 2:0,3:5}

#powered_modules = [WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)]
powered_modules = [WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5, leaves=train.chain_wheel_ratios[0][1]),
                    # 1.2
                    WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2)
                   ]

rod_diameters = [4,3,3,3,3,3,3]


train.generate_arbors_dicts([
    {
        # chain sprocket
        "wheel_thick": 5,
        "style": GearStyle.CIRCLES,
        "pinion_at_front": True,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 0,
        "pinion_type": PinionType.LANTERN,
        "rod_diameter": 4,
        "module": 1.4311998089071878
    },
    # {
    #     #intermediate wheel
    #     "wheel_thick": 4,
    #     "pinion_at_front": True,
    #     "arbor_split": SplitArborType.NORMAL_ARBOR,
    #     "pinion_extension": 0,
    #     "pinion_type": PinionType.LANTERN_THIN,
    #     "rod_diameter": 3,
    #     "module": 1.14495984712575,
    #     "pinion_thick": 9.375
    # },
    {
        #centre wheel
        "wheel_thick": 3,
        "pinion_at_front": True,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 1,
        "pinion_type": PinionType.LANTERN,
        "rod_diameter": 3,
        "module": 1,
        "pinion_thick": 9
    },
    {
        #second wheel
        "wheel_thick": 2.55,
        "pinion_at_front": False,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 15,
        "pinion_type": PinionType.PLASTIC,
        "rod_diameter": 3,
        "module": 0.95,
        "pinion_thick": 8
    },
    {
        #third wheel
        "wheel_thick": 2.1674999999999995,
        "pinion_at_front": False,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 10,
        "pinion_type": PinionType.PLASTIC,
        "rod_diameter": 3,
        "module": 0.95,
        "pinion_thick": 7.55
    },
    {
        #escape wheel
        "wheel_thick": 2.5,
        "pinion_at_front": True,
        # "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 18,
        "pinion_type": PinionType.PLASTIC,
        "rod_diameter": 3,
        "pinion_thick": 7.1674999999999995
    }
])

train.print_info(for_runtime_hours=24*32, weight_kg=4)
moon_radius=13
train.get_arbor_with_conventional_naming(0).print_screw_length()
moon_complication = MoonPhaseComplication3D(gear_style=gearStyle, first_gear_angle_deg=205, on_left=False, bevel_module=1.1, module=0.9, moon_radius=moon_radius,
                                                  bevel_angle_from_hands_deg=90, moon_from_hands=(dial_d/2 - dial_width) - moon_radius - 5, moon_inside_dial=True)
#no need to make inset, we've got lots of space here with the moon complication
motion_works = MotionWorks(extra_height=22, style=gearStyle, thick=3, compensate_loose_arbour=False, compact=True,
                                 moon_complication=moon_complication, cannon_pinion_to_hour_holder_gap_size=0.6)
# balance out the moon complication by making the motion works a bit bigger
#but smaller than their equivalent on the spring clock because the key is too close on this clock
motion_works.calculate_size(arbor_distance=28)
moon_complication.set_motion_works_sizes(motion_works)
print("motion works widest r: ", motion_works.get_widest_radius())
pendulum = Pendulum(hand_avoider_inner_d=100, bob_d=60, bob_thick=12.5)

plaque = Plaque(text_lines=["M32#1 {:.1f}cm L.Wallin 2024".format(train.pendulum_length_m * 100), "Insert Message Here"])


dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=DialStyle.DOTS, dial_width=dial_width, pillar_style=PillarStyle.BARLEY_TWIST)
plates = RoundClockPlates(train, motion_works, name="Wall 32b", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=20,
                                motion_works_angle_deg=205, leg_height=0, fully_round=True, style=PlateStyle.RAISED_EDGING, pillar_style=PillarStyle.BARLEY_TWIST,
                                moon_complication=moon_complication, second_hand=False, standoff_pillars_separate=True, plaque=plaque, fewer_arms=True)

print("plate radius: ", plates.radius)
hands = Hands(style=HandStyle.MOON, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=False,
                    outline_on_seconds=0, second_hand_centred=False)
# show_object(plates.get_fixing_screws_cutter())

pulley = BearingPulley(diameter=train.powered_wheel.diameter, bearing=get_bearing_info(4), wheel_screws=MachineScrew(2, countersunk=True, length=8))
print("pulley needs screws {} {}mm and {} {}mm".format(pulley.screws, pulley.get_total_thick(), pulley.hook_screws, pulley.get_hook_total_thick()))


assembly = Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, pulley=pulley)#weights=[Weight(height=245,diameter=55)]

assembly.get_arbor_rod_lengths()
plates.get_rod_lengths()

# show_object(moon_complication.get_assembled())

# show_object(plates.getPlate(back=True))
# show_object(assembly.getClock(with_key=False, with_pendulum=True))
# show_object(plates.get_fixing_screws_cutter())

# show_object(plates.get_plate())
# show_object(plates.get_fixing_screws_cutter())
#, Colour.LIGHTBLUE, Colour.GREEN
if not outputSTL or True:
    assembly.show_clock(show_object, hand_colours=[Colour.WHITE, Colour.DARKBLUE], motion_works_colours=[Colour.BRASS],
                        bob_colours=[Colour.SILVER], with_rods=True, with_key=True, ratchet_colour=Colour.GOLD,
                        dial_colours=[Colour.BLUE, Colour.WHITE], key_colour=Colour.DARKBLUE,
                        plate_colours=[Colour.DARK_GREEN, Colour.BLACK, Colour.BRASS])
if outputSTL:
    assembly.get_BOM().export()
