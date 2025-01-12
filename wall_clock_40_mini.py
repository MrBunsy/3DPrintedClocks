'''
Copyright Luke Wallin 2025

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
import json
'''
Eight day wall clock, weight driven, small enough to print on an 18x18cm build plate

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_40"
clockOutDir="out"
gearStyle=clock.GearStyle.HONEYCOMB_CHUNKY
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS
second_hand_centred = False
#for period 1.5
#could use new auto-config for this, but this is a proven design so I'll leave it alone
drop =1.5
lift =3
lock=1.5
escapement = clock.AnchorEscapement.get_with_45deg_pallets(30, drop_deg=1.75)
#downside of configuring power outside going train - need to give going train a mechanism to set power direction!
powered_wheel = clock.CordWheel(diameter=26, ratchet_thick=6, rod_metric_size=4,screw_thread_metric=3, cord_thick=1, thick=15, style=gearStyle, use_key=True,
                                loose_on_rod=False, traditional_ratchet=True, power_clockwise=False, use_steel_tube=False)
train = clock.GoingTrain(pendulum_period=1, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=True, chain_at_back=False,
                         powered_wheels=1, runtime_hours=7.5 * 24, powered_wheel=powered_wheel, escape_wheel_pinion_at_front=True)
# print(powered_wheel.get_BOM(wheel_thick=6))
moduleReduction=0.85
pillar_style = clock.PillarStyle.PLAIN
# train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=10, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction)
train.set_ratios([[65, 14], [60, 13], [56, 10]])
train.calculate_powered_wheel_ratios()
# train.gen_cord_wheels(ratchet_thick=6, rod_metric_thread=4, cord_thick=1, cord_coil_thick=15, style=gearStyle, use_key=True, prefered_diameter=29, loose_on_rod=False, prefer_small=True)


pendulumSticksOut=10
backPlateFromWall=40
# pinion_extensions={1:3, 2:6}
pinion_extensions={1:16, 3:10}
powered_modules=[clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)]
train.gen_gears(module_sizes=[1, 0.95, 0.95], thick=3, thickness_reduction=2 / 2.4, powered_wheel_thick=6, pinion_thick_multiplier=3, style=gearStyle,
                powered_wheel_module_sizes=powered_modules, powered_wheel_pinion_thick_multiplier=2, pendulum_fixing=pendulumFixing, lanterns=[0],
                pinion_extensions=pinion_extensions, stack_away_from_powered_wheel=True)
# train.print_info(weight_kg=3)
# train.print_info(weight_kg=2.5)
# train.print_info(weight_kg=1)
train.print_info(weight_kg=2)
train.get_arbour_with_conventional_naming(0).print_screw_length()
dial_d=160
dial_width = dial_d*0.1
moon_radius=10
# motion_works = clock.MotionWorks(extra_height=0, style=gearStyle, thick=3, compensate_loose_arbour=False, compact=True)
# moon_complication = None
# motion_works_angle_deg=360-40

moon_complication = clock.MoonPhaseComplication3D(gear_style=gearStyle, first_gear_angle_deg=205, on_left=False, bevel_module=1.0, module=0.8, moon_radius=moon_radius,
                                                  bevel_angle_from_hands_deg=90, moon_from_hands=(dial_d/2 - dial_width) - moon_radius - 3, moon_inside_dial=True,
                                                  lone_bevel_min_height=13)
#no need to make inset, we've got lots of space here with the moon complication
motion_works = clock.MotionWorks(extra_height=20, style=gearStyle, thick=3, compact=True, moon_complication=moon_complication)
# balance out the moon complication by making the motion works a bit bigger
#but smaller than their equivalent on the spring clock because the key is too close on this clock
# motion_works.calculate_size(arbor_distance=28)
moon_complication.set_motion_works_sizes(motion_works)
motion_works_angle_deg=180+40



pendulum = clock.Pendulum(bob_d=60, bob_thick=10)

dial = clock.Dial(outside_d=dial_d, bottom_fixing=True, top_fixing=False, style=clock.DialStyle.LINES_INDUSTRIAL,
                  seconds_style=clock.DialStyle.LINES_ARC, pillar_style=pillar_style, raised_detail=True)
plaque = clock.Plaque(text_lines=["W40#0 {:.1f}cm L.Wallin".format(train.pendulum_length_m * 100), "2025 PLA Test"])
# plates = clock.SimpleClockPlates(train, motion_works, pendulum, plate_thick=9, back_plate_thick=11, pendulum_sticks_out=pendulumSticksOut, name="Wall 23", gear_train_layout=clock.GearTrainLayout.COMPACT,
#                                  heavy=True, extra_heavy=False, pendulum_fixing=pendulumFixing, pendulum_at_front=False,
#                                  back_plate_from_wall=backPlateFromWall, fixing_screws=clock.MachineScrew(metric_thread=4, countersunk=True),
#                                  chain_through_pillar_required=True, pillars_separate=True, dial=dial, bottom_pillars=1,
#                                  second_hand=second_hand_centred, centred_second_hand=second_hand_centred, motion_works_angle_deg = 225, endshake=1.75)#, screws_from_back=[True, False])

plates = clock.RoundClockPlates(train, motion_works, name="Wall 40", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=20,
                                motion_works_angle_deg=motion_works_angle_deg, leg_height=0, fully_round=True, style=clock.PlateStyle.RAISED_EDGING, pillar_style=pillar_style,
                                second_hand=False, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=True, moon_complication=moon_complication)

# pulley = clock.BearingPulley(diameter=train.powered_wheel.diameter, bearing=clock.get_bearing_info(4), wheel_screws=clock.MachineScrew(2, countersunk=True, length=8))
pulley = clock.LightweightPulley(diameter=train.powered_wheel.diameter, rope_diameter=2, use_steel_rod=False)
# print("pulley needs screws {} {}mm and {} {}mm".format(pulley.screws, pulley.get_total_thick(), pulley.hook_screws, pulley.getHookTotalThick()))
# print(pulley.get_BOM())
hands = clock.Hands(style=clock.HandStyle.SWORD, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True, second_hand_centred=second_hand_centred)#, secondLength=dial.second_hand_mini_dial_d*0.45, seconds_hand_thick=1.5)

assembly = clock.Assembly(plates, name=clockName, hands=hands, time_seconds=30, pendulum=pendulum, pulley=pulley)
# print(assembly.get_BOM())
# print(assembly.get_BOM().get_consolidated_items())
# print(json.dumps(assembly.get_BOM().get_consolidated_items(), sort_keys=True, indent=4))
# print(json.dumps(assembly.get_BOM().to_json(), indent=4, default=str))
#[clock.Colour.ORANGE, clock.Colour.ORANGE, clock.Colour.GREEN, clock.Colour.GREEN, clock.Colour.GREEN, clock.Colour.DARK_GREEN]
assembly.show_clock(show_object, with_rods=True, plate_colours=[clock.Colour.DARKGREY, clock.Colour.BLACK, clock.Colour.BLACK],
                    dial_colours=[clock.Colour.WHITE, clock.Colour.BLACK], bob_colours=[clock.Colour.ORANGE],
                    gear_colours=[clock.Colour.ORANGE, clock.Colour.GREEN], motion_works_colours=[clock.Colour.ORANGE, clock.Colour.ORANGE, clock.Colour.GREEN], pulley_colour=clock.Colour.GREEN)

assembly.get_arbor_rod_lengths()
if outputSTL:
    plaque.output_STLs(clockName, clockOutDir)
    pulley.output_STLs(clockName, clockOutDir)
    motion_works.output_STLs(clockName, clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)