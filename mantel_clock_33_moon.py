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
import clocks as clock

'''
Nothing particularly new, just had an idea for a clock that would look cool:

- black plates with raised brass edging
- symetric style
- fancy hands - maybe improve my existing fancy hands?
- Unsure of style of dial
- Maybe try the smaller spring and see if that's up to it? (uncertain since the centred second hand clock struggled to make a week)

Maybe one for printables?


This went through many iterations until I discovered that the dry stainless steel bearings were seizing up.
The original gear train was fine (and version e has gone back to it), but I've kept the work that reduced the thickness of the powered wheels (using ASA) and more lantern pinions.
Sticking with the 30 tooth escape wheel as I believe this should result in a more efficient train (reduced drop)

TODO before printing more:
thin wheels with lantern pinions should have holes all the way through
bit more wiggle room on the teeth bit of the spring barrel (separate now it's in ASA)
'''
output_STL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    output_STL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "mantel_clock_33.2"
# clock_name= "mantel_clock_33_retrofit"
clock_out_dir= "out"
gear_style=clock.GearStyle.ARCS
pendulum_fixing=clock.PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

moon = True

if moon:
    gear_style = clock.GearStyle.CIRCLES

#this much drop is needed to run reliably (I think it's the wiggle room from the m3 rods in 3mm bearings combined with a small escape wheel?) but a 0.25 nozzle is then needed to print well
lift=2
drop=3
lock=2

#this was orignially for 40tooth recoil, but I think I printed M33#1 like this! oops. wonder if the runtime is worse than M33#0...
# drop =2.5
# lift =2
# lock= 2
#42 as then a quarter span results in exactly the same distance as the old 30 tooth
#going back to 30 teeth, since it was a bearing problem
teeth = 30 if moon else 36 # 42
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=teeth, lock=lock, tooth_tip_angle=5, tooth_base_angle=4, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2,
                                    type=clock.EscapementType.DEADBEAT)

train = clock.GoingTrain(pendulum_period=2/3, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, powered_wheels=2,
                         runtime_hours=8 * 24, support_second_hand=not moon, escape_wheel_pinion_at_front=False)
barrel_gear_thick =5# 8
if moon:
    #can't fit without making the top pillars further apart or much higher up
    module_reduction = 0.9#1
else:
    module_reduction=0.9#0.85
#ratios from wall clock 32 but larger wheel for the intermediate wheel as we have a larger minute wheel on this clock
train.gen_spring_barrel(pawl_angle=-math.pi*3/4, click_angle=-math.pi/4, base_thick=barrel_gear_thick,
                        style=gear_style, wall_thick=8, chain_wheel_ratios=[[61, 10], [64, 10]], extra_barrel_height=1.5, ratchet_thick=8)
'''
0.35:
[[61, 10], [78, 10]]
spring_wound_coils: 23.53661753519562 spring unwound coils: 12.838105212872968, max theoretical barrel turns: 10.698512322322653
Over a runtime of 168.0hours the spring barrel will make 3.5 full rotations which is 33.0% of the maximum number of turns (10.7) and will take 5.3 key turns to wind back up

0.375:
[[61, 10], [77, 10]]
spring_wound_coils: 23.53661753519562 spring unwound coils: 12.838105212872968, max theoretical barrel turns: 10.698512322322653
Over a runtime of 168.0hours the spring barrel will make 3.6 full rotations which is 33.4% of the maximum number of turns (10.7) and will take 5.4 key turns to wind back up

[[61, 10], [72, 10]]
spring_wound_coils: 23.53661753519562 spring unwound coils: 12.838105212872968, max theoretical barrel turns: 10.698512322322653
Over a runtime of 168.0hours the spring barrel will make 3.8 full rotations which is 35.8% of the maximum number of turns (10.7) and will take 5.8 key turns to wind back u

designed plates around rhtis before the wall clock stopped after 1.5 days after winding first time
[[61, 10], [64, 10]]
spring_wound_coils: 23.53661753519562 spring unwound coils: 12.838105212872968, max theoretical barrel turns: 10.698512322322653
Over a runtime of 168.0hours the spring barrel will make 4.3 full rotations which is 40.2% of the maximum number of turns (10.7) and will take 6.6 key turns to wind back up

from (before) printed wall 32: (ended up printing 64-10, 61-10 apparently)
[[62, 10], [61, 10]]
spring_wound_coils: 23.53661753519562 spring unwound coils: 12.838105212872968, max theoretical barrel turns: 10.698512322322653
Over a runtime of 168.0hours the spring barrel will make 4.4 full rotations which is 41.5% of the maximum number of turns (10.7) and will take 6.8 key turns to wind back up
'''

if not moon:
    # 2/3s with second hand with 36 teeth
    train.set_ratios([[75, 9], [72, 10], [55, 22]])
else:
    #2/3s without second hand with 36 teeth
    # train.set_ratios([[75, 10], [65, 15], [60, 13]])
    #2/3s without second hand with 30 teeth
    train.set_ratios([[72, 10], [70, 12], [60, 14]])
    # constraint = lambda train : train["train"][0][0] == 72 and train["train"][0][1] == 10
    # train.calculate_ratios(module_reduction=module_reduction, min_pinion_teeth=10, max_wheel_teeth=72, pinion_max_teeth=20, wheel_min_teeth=50, loud=True, constraint=constraint)
    # train.calculate_ratios(module_reduction=module_reduction, min_pinion_teeth=10, max_wheel_teeth=72, pinion_max_teeth=15, wheel_min_teeth=60, loud=True)#, constraint=constraint)
    # 2/3s with 40 teeth
    # train.set_ratios([[65, 10], [63, 14], [60, 13]])
    #2/3s with 42 teeth
    # train.set_ratios([[65, 10], [60, 13], [60, 14]])
# train.calculate_ratios(module_reduction=module_reduction, min_pinion_teeth=10, max_wheel_teeth=80, pinion_max_teeth=16, wheel_min_teeth=60, loud=True)



#2/3s without second hand 40 teeth
# [[65, 10], [63, 14], [60, 13]]

#2/3s without second hand 40 teeth for retrofitting
# train.set_ratios([[72, 10], [70, 12], [45, 14]])

pendulum_sticks_out=10
back_plate_from_wall=30

# pair = clock.WheelPinionPair(64, 10, 1.2)
# distance = pair.centre_distance
# print("old distance", distance)
# print("old wheel r", pair.wheel.get_max_radius(), "old pinion r", pair.pinion.get_max_radius())
# intermediate_wheel_module = clock.WheelPinionPair.get_module_size_for_distance(distance, 61, 10)
# print("intermediate_wheel_module", intermediate_wheel_module)
#
# newpair = clock.WheelPinionPair(61, 10, intermediate_wheel_module)
# print("new distance", newpair.centre_distance)
# print("new wheel r", newpair.wheel.get_max_radius(), "new pinion r", newpair.pinion.get_max_radius())
#this was a mistake, should have been clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2) (but this doesn't fit current design)
intermediate_wheel_module=1.2
#TODO centre wheel and intemediate wheel can rub against each other.
pinion_extensions = {0:1, 1:3, 3:8} if moon else {0:1, 1:12, 2:5}
powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2)]

old_train = [[72, 10], [70, 12], [60, 14]]
old_modules = [1,0.9,0.9]
# last_module = clock.WheelPinionPair.get_replacement_module_size(60,14, 0.9, 45, 14)
last_module = 0.9

#for retrofitting new train to existing plates
# module_sizes=[clock.WheelPinionPair.get_replacement_module_size(old_train[i][0], old_train[i][1], old_modules[i], train.trains[0]["train"][i][0],  train.trains[0]["train"][i][1]) for i in range(len(old_modules))]
#if printing fresh let's have default sizes?
module_sizes = old_modules

print("module_sizes", module_sizes)
lanterns=[0, 1]
train.gen_gears(module_sizes=module_sizes, module_reduction=module_reduction, thick=2.4, thickness_reduction=0.9, powered_wheel_thicks=[barrel_gear_thick, 4],
                pinion_thick_multiplier=3, style=gear_style,
                powered_wheel_module_increase=1.25, powered_wheel_pinion_thick_multiplier=1.875, pendulum_fixing=pendulum_fixing, stack_away_from_powered_wheel=True,
                pinion_extensions=pinion_extensions, lanterns=lanterns, pinion_thick_extra=5, powered_wheel_module_sizes=powered_modules)
# train.powered_wheel_arbors[1].wheel.fake_outer_r = pair.wheel.get_max_radius()
print("train.powered_wheel_arbors[0].centre_distance, ", train.powered_wheel_arbors[0].distance_to_next_arbor)
print("train.powered_wheel_arbors[1].centre_distance, ", train.powered_wheel_arbors[1].distance_to_next_arbor)
# train.print_info(weight_kg=1.5)
train.print_info(for_runtime_hours=24*7)

#had been using the leftover bob from wall clock 32 before I made it thicker, so bumping up to 10 from 8 and 8 was a bit fiddly to get any weight into
pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=50, bob_thick=10)
pillar_style=clock.PillarStyle.CLASSIC

# if not output_STL:
#     #hack to make preview render faster
#     pillar_style = clock.PillarStyle.SIMPLE

dial_d=205
dial_width=25
moon_radius=13
if moon:
    dial = clock.Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=clock.DialStyle.DOTS, dial_width=dial_width, pillar_style=pillar_style)
    moon_complication = clock.MoonPhaseComplication3D(gear_style=gear_style, first_gear_angle_deg=205, on_left=False, bevel_module=1.1, module=0.9, moon_radius=moon_radius,
                                                      bevel_angle_from_hands_deg=90, moon_from_hands=(dial_d / 2 - dial_width) - moon_radius - 5, moon_inside_dial=True)
else:
    dial = clock.Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, romain_numerals_style=clock.RomanNumeralStyle.SIMPLE_SQUARE, style=clock.DialStyle.ROMAN_NUMERALS,
                  outer_edge_style=clock.DialStyle.DOTS, seconds_style=clock.DialStyle.CONCENTRIC_CIRCLES, dial_width=dial_width, pillar_style=pillar_style)
    moon_complication = None

motion_works_height = 22 if moon else 10

#tiny bit extra gap as the brass PETG seems to need it
motion_works = clock.MotionWorks(extra_height=motion_works_height, style=gear_style, thick=3, compensate_loose_arbour=True, compact=True, moon_complication=moon_complication,
                                 cannon_pinion_to_hour_holder_gap_size=0.6)

motion_works_angle_deg=180+90

if moon:
    motion_works_angle_deg=180+40
    motion_works.calculate_size(arbor_distance=30)
    moon_complication.set_motion_works_sizes(motion_works)

plaque = clock.Plaque(text_lines=["M33#2 {:.1f}cm L.Wallin 2024".format(train.pendulum_length_m * 100), "github.com/MrBunsy/3DPrintedClocks"])

plates = clock.MantelClockPlates(train, motion_works, name="Mantel 33", dial=dial, plate_thick=7, back_plate_thick=6, style=clock.PlateStyle.RAISED_EDGING,
                                 pillar_style=pillar_style, moon_complication=moon_complication, second_hand=not moon, symetrical=moon, pendulum_sticks_out=21,
                                 standoff_pillars_separate=True, fixing_screws=clock.MachineScrew(4, countersunk=False), motion_works_angle_deg=motion_works_angle_deg,
                                 plaque=plaque, split_detailed_plate=True)
print("plate pillar y", plates.bottom_pillar_positions[0][1])

hand_style = clock.HandStyle.MOON if moon else clock.HandStyle.SPADE
hands = clock.Hands(style=hand_style, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.outside_d*0.45, thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True,
                    second_length=dial.second_hand_mini_dial_d * 0.45 if not moon else 1, seconds_hand_thick=1.5, outline_on_seconds=0.5)


assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, with_mat=True)
dial_colours =  [clock.Colour.WHITE, clock.Colour.BLACK]
if moon:
    dial_colours =  [clock.Colour.BLUE, clock.Colour.WHITE]


if moon and False:
    #hack to retrofit missing motion works holder!
    plates.little_arm_to_motion_works=False
    mini_arm_width = plates.motion_works_screws.get_nut_containing_diameter() * 2
    extra = 0.6
    thick = plates.get_plate_thick(back=False)
    centre = plates.bearing_positions[train.powered_wheels][:2]
    holder = clock.get_stroke_line([plates.motion_works_pos, centre], wide=mini_arm_width, thick=thick+extra)
    holder = holder.cut(cq.Workplane("XY").moveTo(centre[0], centre[1]).circle(plates.arbors_for_plate[train.powered_wheels].bearing.outer_d).extrude(thick+extra))
    holder = holder.cut(plates.motion_works_screws.get_cutter().translate(plates.motion_works_pos))
    holder = holder.translate((0,0,-extra))
    holder = holder.cut(plates.get_plate(back=False))


    show_object(holder.translate((0,0, plates.get_plate_thick(True) + plates.plate_distance)))
    clock.export_STL(holder, "motion_works_holder_retrofit", clock_name=clock_name, path=clock_out_dir)

# show_object(plates.get_plate(back=True))
# show_object(plaque.get_plaque().rotate((0,0,0), (0,0,1), clock.rad_to_deg(plates.plaque_angle)).translate(plates.plaque_pos).translate((0,0,-plaque.thick)))

# show_object(plates.get_plate(back=False))
# for a, arbor in enumerate(assembly.plates.arbors_for_plate):
#         show_object(arbor.get_assembled(), name="Arbour {}".format(a))
assembly.show_clock(show_object, hand_colours=[clock.Colour.WHITE, clock.Colour.BLACK], motion_works_colours=[clock.Colour.BRASS],
                    bob_colours=[clock.Colour.GOLD], with_rods=True, with_key=True, ratchet_colour=clock.Colour.GOLD, dial_colours=dial_colours,
                    plate_colours=[clock.Colour.DARK_GREEN, clock.Colour.BRASS, clock.Colour.BRASS])#, gear_colours=[clock.Colour.GOLD])
#plate_colours=[clock.Colour.BLACK, clock.Colour.SILVER, clock.Colour.BRASS]
# show_object(plates.getDrillTemplate(6))

if output_STL:

    a = clock.polar(0, 100)
    b = clock.polar(math.pi * 2 / 3, 100)
    wedge_height = plates.plate_distance / 2 + 2
    wedge = cq.Workplane("XY").lineTo(a[0], a[1]).lineTo(b[0], b[1]).close().extrude(wedge_height).translate((0, 0, plates.plate_distance - wedge_height))
    special_pillar = plates.get_pillar(top=True).cut(wedge)

    clock.export_STL(special_pillar, "special_pillar", clock_name, clock_out_dir)

    plaque.output_STLs(clock_name, clock_out_dir)
    if moon:
        moon_complication.output_STLs(clock_name, clock_out_dir)
    motion_works.output_STLs(clock_name, clock_out_dir)
    pendulum.output_STLs(clock_name, clock_out_dir)
    plates.output_STLs(clock_name, clock_out_dir)
    hands.output_STLs(clock_name, clock_out_dir)
    assembly.output_STLs(clock_name, clock_out_dir)
    # clock.export_STL(mat, "mat", clock_name, clock_out_dir)
    # clock.export_STL(mat_detail, "mat_detail", clock_name, clock_out_dir)






