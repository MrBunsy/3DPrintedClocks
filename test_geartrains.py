from clocks import *

drop =3
lift =3
lock=1.25
pendulum_period=2.0
escapement = AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock)
barrel_gear_thick = 8

train = GoingTrain(pendulum_period=pendulum_period, wheels=4, escapement=escapement, max_weight_drop=104*25.4/2, use_pulley=True, chain_at_back=False, chain_wheels=2, runtime_hours=8 * 24, support_second_hand=False)#, huygensMaintainingPower=True)

moduleReduction=0.85

# train.calculate_ratios(max_wheel_teeth=120, min_pinion_teeth=9, wheel_min_teeth=20, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction, loud=True, favour_smallest=False)

train.set_ratios([[54, 12], [54, 12], [54, 12]])


# train.gen_cord_wheels(ratchet_thick=6.25, rod_metric_thread=4, cord_thick=1, cord_coil_thick=32, style=None, use_key=True, prefered_diameter=25.4,
#                       loose_on_rod=False, prefer_small=True, traditional_ratchet=True)#, ratchet_diameter=29 + 27.5)

train.gen_spring_barrel(pawl_angle=-math.pi*3/4, click_angle=-math.pi/4, base_thick=barrel_gear_thick,
                        style=None, wall_thick=10, chain_wheel_ratios=[[66, 10], [76, 13]])#fraction_of_max_turns=0.35)#  chain_wheel_ratios=[[62, 10], [61, 10]]fraction_of_max_turns=0.35)#,, spring=clock.MAINSPRING_183535,

#Chain wheel multiplier: 6.1 ([[21, 10], [29, 10]])
#Chain wheel multiplier: 6.1 ([[61, 10]])

# train.set_chain_wheel_ratio([[54,24],[48,18]])

pendulumSticksOut=10
backPlateFromWall=30

train.gen_gears(module_size=1, module_reduction=moduleReduction, thick=2.4, thickness_reduction=0.9, chain_wheel_thick=6.25, pinion_thick_multiplier=3, style=None,
                powered_wheel_module_increase=1, chain_wheel_pinion_thick_multiplier=2, pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS, stack_away_from_powered_wheel=True, pinion_extensions={1:10})
# train.print_info(weight_kg=5)
train.print_info(for_runtime_hours=24*7)

#With a weight of 2.5kg, this results in an average power usage of 47.1uW