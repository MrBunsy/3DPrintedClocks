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

clock_name= "Wall Clock 46"
clock_out_dir= "out"
gear_style=GearStyle.HONEYCOMB_CHUNKY

second_hand_centred = False

escapement = AnchorEscapement.get_with_optimal_pallets(24, drop_deg=1.75)

powered_wheel = CordBarrel(diameter=26, ratchet_thick=6, rod_metric_size=4, screw_thread_metric=3, cord_thick=1, thick=15, style=gear_style, use_key=True,
                                 loose_on_rod=False, traditional_ratchet=True, power_clockwise=False, use_steel_tube=False)
train = GoingTrain(pendulum_length_m=0.2, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=True, chain_at_back=False,
                         powered_wheels=1, runtime_hours=7.5 * 24, powered_wheel=powered_wheel, escape_wheel_pinion_at_front=True)

moduleReduction=0.85
pillar_style = PillarStyle.PLAIN

# train.set_ratios([[70, 9], [60, 14], [54, 10]])

# train.set_ratios([[63, 10], [56, 10], [49, 10]])
# train.set_ratios([[63, 10], [56, 10], [50, 13]])

# train.calculate_ratios(module_reduction=1.0, pinion_max_teeth=11, min_pinion_teeth=10, wheel_min_teeth=50, max_wheel_teeth=75, max_error=100, loud=True)
# train.set_train([[63, 10], [56, 9], [50, 11]])
#[[63, 11], [56, 11], [50, 11]]
train.set_ratios([[63, 10], [56, 10], [49, 10]])
print(f"Pendulum period: {train.recalculate_pendulum_period()}")#:.2f


train.calculate_powered_wheel_ratios()



pendulumSticksOut=10
backPlateFromWall=40

pinion_extensions={1:16, 3:10}
# powered_modules=[WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)]
# train.gen_gears(module_sizes=[1, 0.95, 0.95], thick=3, thickness_reduction=2 / 2.4, powered_wheel_thick=6, pinion_thick_multiplier=3, style=gear_style,
#                 powered_wheel_module_sizes=powered_modules, powered_wheel_pinion_thick_multiplier=2, pendulum_fixing=pendulum_fixing, lanterns=[0],
#                 pinion_extensions=pinion_extensions, stack_away_from_powered_wheel=True)

train.generate_arbors_dicts([
    {
        #great wheel
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1),
        "wheel_thick" : 6,
        "pinion_type": PinionType.LANTERN,
        "style": gear_style,
        "pinion_faces_forwards": True
    },
    {
        #centre wheel
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1),
        "wheel_thick" : 3,
        "pinion_thick": 12,
        "pinion_type": PinionType.LANTERN,
        "style": gear_style,
        "pinion_faces_forwards": True
    },
    {
        #second wheel
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1),
        "wheel_thick" : 2.5,
        "pinion_thick": 9,
        "pinion_type": PinionType.LANTERN,
        "style": gear_style,
        "pinion_extension": 18
    },
{
        # third wheel
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1),
        "wheel_thick" : 2.0,
        "pinion_thick": 7.5,
        "pinion_type": PinionType.LANTERN,
        "style": gear_style,
        "pinion_faces_forwards": True,
    },
    {
        # escape wheel
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1),
        "wheel_thick" : 2.0,
        "pinion_thick": 6.0,
        "pinion_type": PinionType.LANTERN,
        "style": gear_style,
        "pinion_extension": 8,
        "pinion_faces_forwards": True,
    }
])

train.print_info(weight_kg=2)

dial_d=160
dial_width = dial_d*0.125
moon_radius=10

moon = False

if not moon:
    motion_works = MotionWorks(extra_height=0, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True)
    moon_complication = None
    motion_works_angle_deg=360-40
else:
    moon_complication = MoonPhaseComplication3D(gear_style=gear_style, first_gear_angle_deg=205, on_left=False, bevel_module=1.0, module=0.8, moon_radius=moon_radius,
                                                      bevel_angle_from_hands_deg=90, moon_from_hands=(dial_d/2 - dial_width) - moon_radius - 3, moon_inside_dial=True,
                                                      lone_bevel_min_height=13)
    motion_works = MotionWorks(extra_height=20, style=gear_style, thick=3, compact=True, moon_complication=moon_complication)
    moon_complication.set_motion_works_sizes(motion_works)
    motion_works_angle_deg=180+40



pendulum = Pendulum(bob_d=60, bob_thick=10)

dial = Dial(outside_d=dial_d, bottom_fixing=True, top_fixing=False, style=DialStyle.LINES_INDUSTRIAL,
                  seconds_style=DialStyle.LINES_ARC, pillar_style=pillar_style, raised_detail=True, dial_width=dial_width)
# plaque = Plaque(text_lines=["W40#0 {:.1f}cm L.Wallin".format(train.pendulum_length_m * 100), "2025 PLA Test"])
plaque = None
gear_train_layout=GearLayout2D.get_compact_layout(train, start_on_right=False)


plates = RoundClockPlates(train, motion_works, name="Wall 40", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=9,
                                motion_works_angle_deg=motion_works_angle_deg, leg_height=0, fully_round=True, style=PlateStyle.RAISED_EDGING, pillar_style=pillar_style,
                                second_hand=False, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=True, moon_complication=moon_complication,
                                gear_train_layout=gear_train_layout, back_plate_from_wall=27, fewer_arms=True)

pulley = LightweightPulley(diameter=plates.get_diameter_for_pulley(), rope_diameter=2, use_steel_rod=False, style=gear_style)

hands = Hands(style=HandStyle.SWORD, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True, second_hand_centred=second_hand_centred)#, secondLength=dial.second_hand_mini_dial_d*0.45, seconds_hand_thick=1.5)

specific_instructions = [
"The front plate needs flipping over for printing (bug in logic about which way up it should be for exporting the STL)",
]

assembly = Assembly(plates, name=clock_name, hands=hands, time_seconds=30, pendulum=pendulum, pulley=pulley, specific_instructions=specific_instructions)

if not outputSTL:
    assembly.show_clock(show_object, with_rods=True, plate_colours=[Colour.DARKER_GREY, Colour.DARKER_GREY, Colour.BLACK],
                        dial_colours=[Colour.WHITE, Colour.BLACK], bob_colours=[Colour.BRIGHT_ORANGE],
                        gear_colours=[Colour.BRIGHT_ORANGE, Colour.LIME_GREEN],
                        motion_works_colours=[Colour.BRIGHT_ORANGE, Colour.BRIGHT_ORANGE, Colour.LIME_GREEN],
                        pulley_colour=Colour.LIME_GREEN, plaque_colours=[Colour.WHITE, Colour.BLACK], with_key=True)

if outputSTL:
    assembly.get_BOM().export(clock_out_dir)