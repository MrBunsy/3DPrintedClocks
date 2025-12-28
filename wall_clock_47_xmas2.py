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
import random

from clocks import *
import json
'''
I printed the mini clock (clock 40) in PLA as an experiment. It works and hasn't warped, but seems to suffer badly with dust getting stuck in the pinions
so, what happens if we make the entire train lantern pinions?

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "Wall Clock 47 Xmas"
clock_out_dir= "out"
gear_style=GearStyle.SNOWFLAKE

random.seed(clock_name)

second_hand_centred = False

escapement_info = AnchorEscapement.get_with_optimal_pallets(20, drop_deg=3)#1.75
# escapement = SilentAnchorEscapement(teeth=escapement.teeth, drop=escapement.drop, lift=escapement.lift,l)
escapement = SilentPinPalletAnchorEscapement(gap_size=1.5*2 + 3 + 1, teeth=escapement_info.teeth, drop=escapement_info.drop_deg, lift=escapement_info.lift_deg, run=escapement_info.run_deg, lock=escapement_info.lock_deg,
                                             pin_diameter=1.0)#, pin_external_length=1.5*2 + 3 + 1)
spring=False
if spring:
    powered_wheel = SpringBarrel(spring=SMITHS_EIGHT_DAY_MAINSPRING, pawl_angle=-math.pi * 3 / 4, click_angle=-math.pi * 1 / 4, ratchet_at_back=True,
                                 style=gear_style, base_thick=BEARING_10x15x4_FLANGED.height,
                                 wall_thick=8, key_bearing=BEARING_10x15x4, lid_bearing=BEARING_10x15x4_FLANGED, barrel_bearing=BEARING_10x15x4_FLANGED,
                                 ratchet_screws=MachineScrew(2, grub=True), total_turns=4)
    powered_wheels = 2
    runtime_hours = 8*24
else:
    #usually use an M4 rod - forgot to set rod diameter correct for the arbor, but I've already printed the plates and don't have a 4x10x4 bearing, so switching to M3
    powered_wheel = CordBarrel(diameter=26, ratchet_thick=6, rod_metric_size=3, screw_thread_metric=3, cord_thick=1, thick=15, style=gear_style, use_key=True,
                                 loose_on_rod=False, traditional_ratchet=True, power_clockwise=False, use_steel_tube=False, pawl_screwed_from_front=True)
    powered_wheels = 1
    runtime_hours = 7.5 * 24

train = GoingTrain(pendulum_length_m=0.2, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=True, chain_at_back=False,
                         powered_wheels=powered_wheels, runtime_hours=runtime_hours, powered_wheel=powered_wheel, escape_wheel_pinion_at_front=True)

moduleReduction=0.85
pillar_style = PillarStyle.BARLEY_TWIST

# train.set_ratios([[70, 9], [60, 14], [54, 10]])

# train.set_ratios([[63, 10], [56, 10], [49, 10]])
# train.set_ratios([[63, 10], [56, 10], [50, 13]])

# train.calculate_ratios(module_reduction=1.0, pinion_max_teeth=11, min_pinion_teeth=10, wheel_min_teeth=50, max_wheel_teeth=75, max_error=100, loud=True)
# train.set_train([[63, 10], [56, 9], [50, 11]])
#[[63, 11], [56, 11], [50, 11]]
train.set_ratios([[63, 10], [56, 10], [49, 10]])
print(f"Pendulum period: {train.recalculate_pendulum_period()}")#:.2f


train.calculate_powered_wheel_ratios(prefer_large_second_wheel=False)
#[[75, 10], [64, 10]]
# train.set_powered_wheel_ratios([[64, 10], [68, 10]])


pendulumSticksOut=10
backPlateFromWall=40

pinion_extensions={1:16, 3:10}
# powered_modules=[WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)]
# train.gen_gears(module_sizes=[1, 0.95, 0.95], thick=3, thickness_reduction=2 / 2.4, powered_wheel_thick=6, pinion_thick_multiplier=3, style=gear_style,
#                 powered_wheel_module_sizes=powered_modules, powered_wheel_pinion_thick_multiplier=2, pendulum_fixing=pendulum_fixing, lanterns=[0],
#                 pinion_extensions=pinion_extensions, stack_away_from_powered_wheel=True)
powered_wheel_thick = 5
arbor_info = [


    {
        #centre wheel
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1),
        "wheel_thick" : 3,
        "pinion_thick": powered_wheel_thick + 1.5*2 + 2,
        "pinion_type": PinionType.LANTERN,
        "style": gear_style,
        "pinion_at_front": True
    },
    {
        #second wheel
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1),
        "wheel_thick" : 2.5,
        "pinion_thick": 9,
        # "pinion_type": PinionType.LANTERN_LOW_TORQUE,

        "style": gear_style,
        "pinion_extension": 25-1
    },
{
        # third wheel
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1),
        "wheel_thick" : 2.0,
        "pinion_thick": 7.5,
        # "pinion_type": PinionType.LANTERN,
        "style": gear_style,
        "pinion_at_front": True,
    },
    {
        # escape wheel
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1),
        "wheel_thick" : 2.0,
        "pinion_thick": 6.0,
        # "pinion_type": PinionType.LANTERN_LOW_TORQUE,
        "style": gear_style,
        "pinion_extension": 15-1,
        "pinion_at_front": True,
    }
]

if spring:
    arbor_info = [{
        #barrel
        "module":WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2),
        "wheel_thick": powered_wheel_thick,
        "style": gear_style,

    },
    {
        #intermediate wheel
        "module":WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.0),
        "pinion_type": PinionType.LANTERN,#_THIN
        "pinion_thick": powered_wheel_thick * 2,
        #space for stop works?
        "pinion_extension": 8,
        "wheel_thick": 4,
        "style": gear_style,

    }] + arbor_info
else:
    arbor_info = [
        {
        #great wheel (cord barrel)
        "rod_diameter":powered_wheel.threaded_rod.metric_thread,
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1),
        "wheel_thick" : powered_wheel_thick,
        "pinion_type": PinionType.LANTERN,
        "style": gear_style,
        "pinion_at_front": True
    }] + arbor_info

train.generate_arbors_dicts(arbor_info)

train.print_info(weight_kg=2, for_runtime_hours=24*8)

if spring:
    dial_d=180
    dial_width = 30#dial_d*0.125
else:
    dial_d=160
    dial_width = 27#dial_d*0.125




motion_works = MotionWorks(extra_height=0, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True)
moon_complication = None

motion_works.calculate_size(30)




#pendulum = Pendulum(bob_d=60, bob_thick=10)
pendulum = Pendulum(bob_d=60, bob_thick=10, hand_avoider_inner_d=120)
leaf_thick=1
# random.seed(clock_name + '2')
pud = ChristmasPudding(thick=leaf_thick, diameter=pendulum.bob_r * 2, cut_rect_width=pendulum.gap_width + 0.1, cut_rect_height=pendulum.gap_height + 0.1)

pendulum_bob = ItemWithCosmetics(pendulum.get_bob(hollow=True), name="bob_pud", background_colour="brown", cosmetics=pud.get_cosmetics(), colour_thick_overrides={"green":leaf_thick})


# dial = Dial(outside_d=dial_d, bottom_fixing=True, top_fixing=False, style=DialStyle.LINES_INDUSTRIAL,
#                   seconds_style=DialStyle.LINES_ARC, pillar_style=pillar_style, raised_detail=True, dial_width=dial_width)
dial = Dial(outside_d=dial_d, bottom_fixing=True, top_fixing=False, romain_numerals_style=RomanNumeralStyle.SIMPLE_SQUARE, style=DialStyle.ROMAN_NUMERALS,
                        outer_edge_style=DialStyle.EMPTY,
                  seconds_style=DialStyle.LINES_ARC, pillar_style=pillar_style, raised_detail=True, dial_width=dial_width)
plaque = Plaque(text_lines=["W47#0 {:.1f}cm 2025".format(train.pendulum_length_m * 100), " Xmas for Billy xxx"])
# plaque = None

if spring:
    extra_anchor_distance = 8

else:
    extra_anchor_distance = 0


gear_train_layout = GearLayout2D.get_compact_layout(train, start_on_right=True, extra_anchor_distance=extra_anchor_distance)

if spring:
    motion_works_angle_deg = 180 - rad_to_deg(gear_train_layout.get_angle_between(2, 1))
else:
    motion_works_angle_deg = rad_to_deg(gear_train_layout.get_angle_between(1, 2)) + 180


plates = RoundClockPlates(train, motion_works, name="Wall 47 (Xmas)", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=9,
                                motion_works_angle_deg=motion_works_angle_deg, leg_height=0, fully_round=True, style=PlateStyle.RAISED_EDGING, pillar_style=pillar_style,
                                second_hand=False, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=True, moon_complication=moon_complication,
                                gear_train_layout=gear_train_layout, back_plate_from_wall=27, fewer_arms=True)
pulley = None
if not spring:
    pulley = LightweightPulley(diameter=plates.get_diameter_for_pulley(), rope_diameter=2, use_steel_rod=False, style=gear_style)

# hands = Hands(style=HandStyle.XMAS_TREE, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
#                     length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True)#, secondLength=dial.second_hand_mini_dial_d*0.45, seconds_hand_thick=1.5)
hands = Hands(style=HandStyle.XMAS_TREE, chunky=True, second_length=25, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=True)
specific_instructions = [
"The front plate needs flipping over for printing (bug in logic about which way up it should be for exporting the STL)",
]

wreath_inner_d = dial_d-dial_width*0.4
wreath_outer_d = dial_d+dial_width*0.2

wreath = Wreath(diameter=wreath_inner_d, thick=leaf_thick, total_leaves=36, greens=["green", "lightgreen"])
# cosmetics={"green": wreath.get_leaves(),
#            "red": wreath.get_berries()}
wreath_base_thick = 1
wreath_base = cq.Workplane("XY").circle(wreath_outer_d/2).circle(wreath_inner_d/2).extrude(wreath_base_thick).faces(">Z").workplane().moveTo(0,0).circle(wreath_outer_d/2).circle(dial_d/2+0.2).extrude(wreath_base_thick)

wreath_cosmetics = wreath.get_cosmetics()
for colour in wreath_cosmetics:
    wreath_base = wreath_base.cut(wreath_cosmetics[colour])
wreath_cosmetics["brown"] = wreath_base
# dial_wreath = ItemWithCosmetics(shape = wreath_base, name="dial_wreath", background_colour="brown", cosmetics=wreath.get_cosmetics(), colour_thick_overrides={"green":leaf_thick, "lightgreen":leaf_thick})
dial_wreath = ItemWithCosmetics(shape = None, name="dial_wreath", background_colour="green", cosmetics=wreath_cosmetics, colour_thick_overrides={"green":leaf_thick, "lightgreen":LAYER_THICK, "brown":LAYER_THICK*2})


assembly = Assembly(plates, name=clock_name, hands=hands, time_seconds=30, pendulum=pendulum, pulley=pulley, specific_instructions=specific_instructions,
                    pretty_bob=pendulum_bob, cosmetics=[pendulum_bob, dial_wreath])

if not outputSTL:
    assembly.show_clock(show_object, with_rods=True, plate_colours=[Colour.DARK_GREEN, Colour.RED, Colour.BRASS],
                        dial_colours=[Colour.WHITE, Colour.BLACK], bob_colours=[Colour.BROWN],
                        gear_colours=[Colour.ICE_BLUE],
                        motion_works_colours=[Colour.ICE_BLUE],
                        pulley_colour=Colour.ICE_BLUE, plaque_colours=[Colour.WHITE, Colour.BLACK], with_key=True)
    dial_wreath.show(show_object, lambda w:w.rotate((0,0,0),(0,1,0),180).translate((plates.hands_position[0],plates.hands_position[1],plates.dial_z+dial.thick+assembly.front_of_clock_z + wreath_base_thick)))
    # pendulum_bob.show(show_object)
if outputSTL:
    assembly.get_BOM().export(clock_out_dir)