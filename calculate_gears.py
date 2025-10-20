from clocks import *

'''

'''
gear_style = None
escapement = AnchorEscapement.get_with_optimal_pallets()
power = CordBarrel(diameter=26, ratchet_thick=6, rod_metric_size=4, screw_thread_metric=3, cord_thick=1, thick=15, style=gear_style, use_key=True,
                                 loose_on_rod=False, traditional_ratchet=True, power_clockwise=False, use_steel_tube=False)
# train=clock.GoingTrain(pendulum_period=1/3, fourth_wheel=True, escapement_teeth=30, max_weight_drop=1800, chain_at_back=False, powered_wheels=1, runtime_hours=180)
train = GoingTrain(pendulum_period=2 / 3, wheels=4, escapement=escapement, powered_wheels=2, runtime_hours=8 * 24, support_second_hand=False, powered_wheel=power)

#
train.calculate_ratios(max_wheel_teeth=85, min_pinion_teeth=9, wheel_min_teeth=50, pinion_max_teeth=15, max_error=0.1, loud=True, module_reduction=1.0)
#
#
# train.set_powered_wheel_ratios([74, 11])
train.calculate_powered_wheel_ratios()
#
# #chain size seems about right, trying reducing tolerance
# #the 1.2mm 47links/ft regula chain
# train.gen_chain_wheels(ratchetThick=5, wire_thick=1.2, width=4.5, inside_length=8.75 - 1.2 * 2, tolerance=0.075)#, wire_thick=0.85, width=3.6, inside_length=6.65-0.85*2, tolerance=0.1)
#
train.print_info()


# seconds = 60
#
# teeth = 24
# period = 2/3
#
# escape_wheel_seconds = teeth*period
# ratio = seconds / escape_wheel_seconds
#
# print(f"escape_wheel_seconds: {escape_wheel_seconds} ratio: {ratio}")