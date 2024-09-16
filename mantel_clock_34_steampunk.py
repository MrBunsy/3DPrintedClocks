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
Tinkering with using a smaller spring in a similar gear train to clocks 32/33
'''
output_STL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    output_STL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "mantel_clock_34"
clock_out_dir= "out"

pendulum_fixing=clock.PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

gear_style = clock.GearStyle.ROUNDED_ARMS5
#
# lift=3
# drop=3
# lock=2
# teeth = 30
# escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=teeth, lock=lock, tooth_tip_angle=5, tooth_base_angle=4, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2,
#                                     type=clock.EscapementType.DEADBEAT)

escapement = clock.AnchorEscapement.get_with_45deg_pallets(teeth=30, drop_deg=2, lock_deg=1.5, force_diameter=False, anchor_thick=10)


train = clock.GoingTrain(pendulum_period=2/3, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, chain_wheels=2,
                         runtime_hours=8 * 24, support_second_hand=False, escape_wheel_pinion_at_front=False)
barrel_gear_thick =5

module_reduction=0.9
#chain_wheel_ratios=[[61, 10], [62, 10]],
#, chain_wheel_ratios=[[81, 10], [61, 10]])
#can't decide between trying smaller spring or higher ratio with standard smiths spring - so slightly more even power and potentially longer total runtime if I
#don't care about accuracy
#, spring=clock.MAINSPRING_183535
train.gen_spring_barrel(pawl_angle=-math.pi*3/4, click_angle=-math.pi/4, base_thick=barrel_gear_thick,
                        style=gear_style, wall_thick=6, ratchet_thick=8, spring=clock.MAINSPRING_183535, chain_wheel_ratios=[[75, 10], [61, 10]])#fraction_of_max_turns=0.375)# chain_wheel_ratios=[[64, 10], [64, 10]])#,fraction_of_max_turns=0.4)#, chain_wheel_ratios=[[64, 10], [62, 10]])#, fraction_of_max_turns=0.5)
#, chain_wheel_ratios=[[61, 10], [62, 10]])#
# train.calculate_ratios(module_reduction=module_reduction, min_pinion_teeth=9, max_wheel_teeth=150, pinion_max_teeth=12, wheel_min_teeth=100, loud=True)
#2/3s without second hand with 30 teeth
train.set_ratios([[72, 10], [70, 12], [60, 14]])

pendulum_sticks_out=25
back_plate_from_wall=30


pinion_extensions = {0:1, 1:3, 3:8}
powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1), clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)]

module_sizes = [0.8,0.7,0.7]

print("module_sizes", module_sizes)
lanterns=[0, 1]
train.gen_gears(module_sizes=module_sizes, module_reduction=module_reduction, thick=2.4, thickness_reduction=0.9, powered_wheel_thicks=[barrel_gear_thick, 4],
                pinion_thick_multiplier=3, style=gear_style,
                powered_wheel_module_increase=1.25, powered_wheel_pinion_thick_multiplier=1.875, pendulum_fixing=pendulum_fixing, stack_away_from_powered_wheel=True,
                pinion_extensions=pinion_extensions, lanterns=lanterns, pinion_thick_extra=5, powered_wheel_module_sizes=powered_modules)

train.print_info(for_runtime_hours=24*7)
train.get_arbour_with_conventional_naming(0).print_screw_length()

pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=50, bob_thick=8)
pillar_style=clock.PillarStyle.COLUMN

#dial_d=175
dial_d=205
dial_width=25

dial = clock.Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, romain_numerals_style=clock.RomanNumeralStyle.SIMPLE_SQUARE, style=clock.DialStyle.ROMAN_NUMERALS,
              outer_edge_style=clock.DialStyle.CONCENTRIC_CIRCLES, seconds_style=clock.DialStyle.CONCENTRIC_CIRCLES, dial_width=dial_width, pillar_style=pillar_style)
moon_complication = None

motion_works_height = 10

#tiny bit extra gap as the brass PETG seems to need it
motion_works = clock.MotionWorks(extra_height=motion_works_height, style=gear_style, thick=3, compensate_loose_arbour=True, compact=True, moon_complication=moon_complication,
                                 cannon_pinion_to_hour_holder_gap_size=0.6)

motion_works_angle_deg=180+90+57


plaque = clock.Plaque(text_lines=["M34#0 {:.1f}cm L.Wallin".format(train.pendulum_length_m * 100), "2024"])

plates = clock.MantelClockPlates(train, motion_works, name="Mantel 34", dial=dial, plate_thick=7, back_plate_thick=6, style=clock.PlateStyle.RAISED_EDGING,
                                 pillar_style=pillar_style, moon_complication=moon_complication, second_hand=False, symetrical=True, pendulum_sticks_out=pendulum_sticks_out,
                                 standoff_pillars_separate=True, fixing_screws=clock.MachineScrew(4, countersunk=False), motion_works_angle_deg=motion_works_angle_deg,
                                 plaque=plaque, vanity_plate_radius=-1, escapement_on_front=False, prefer_tall=True)
plates.little_arm_to_motion_works = False
print("plate pillar y", plates.bottom_pillar_positions[0][1])

hand_style = clock.HandStyle.SWORD
hands = clock.Hands(style=hand_style, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.outside_d*0.45, thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True,
                    second_length=1, seconds_hand_thick=1.5, outline_on_seconds=0.5)


assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, with_mat=True)
dial_colours =  [clock.Colour.WHITE, clock.Colour.BLACK]



# show_object(plates.get_plate(back=True))
# show_object(plaque.get_plaque().rotate((0,0,0), (0,0,1), clock.rad_to_deg(plates.plaque_angle)).translate(plates.plaque_pos).translate((0,0,-plaque.thick)))

assembly.show_clock(show_object, hand_colours=[clock.Colour.WHITE, clock.Colour.BLACK], motion_works_colours=[clock.Colour.BRASS],
                    bob_colours=[clock.Colour.GOLD], with_rods=True, with_key=True, ratchet_colour=clock.Colour.GOLD, dial_colours=dial_colours,
                    plate_colours=[clock.Colour.DARKGREY, clock.Colour.BRASS, clock.Colour.BRASS])
plate_colours=[clock.Colour.DARK_GREEN, clock.Colour.BRASS, clock.Colour.BRASS]
#plate_colours=[clock.Colour.BLACK, clock.Colour.SILVER, clock.Colour.BRASS]
# show_object(plates.getDrillTemplate(6))

if output_STL:

    a = clock.polar(0, 100)
    b = clock.polar(math.pi * 2 / 3, 100)
    wedge_height = plates.plate_distance / 2 + 2
    wedge = cq.Workplane("XY").lineTo(a[0], a[1]).lineTo(b[0], b[1]).close().extrude(wedge_height).translate((0, 0, plates.plate_distance - wedge_height))
    special_pillar = plates.get_pillar(top=True).cut(wedge)

    # clock.export_STL(special_pillar, "special_pillar", clock_name, clock_out_dir)

    plaque.output_STLs(clock_name, clock_out_dir)
    motion_works.output_STLs(clock_name, clock_out_dir)
    pendulum.output_STLs(clock_name, clock_out_dir)
    plates.output_STLs(clock_name, clock_out_dir)
    hands.output_STLs(clock_name, clock_out_dir)
    assembly.output_STLs(clock_name, clock_out_dir)





