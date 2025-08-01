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
Eight day wall clock, inspired by a wall clock I saw on ebay

visible Brocot escapement, fancy hands and dial and octagonal case (which I might try doing as an extension of the vanity plate)

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "Wall Clock 42"
clock_out_dir= "out"
gear_style=GearStyle.ROUNDED_ARMS5
pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS
second_hand_centred = False
escapement_details = AnchorEscapement.get_with_optimal_pallets(30, drop_deg=1.75, anchor_teeth=9.5)
escapement = BrocotEscapment(teeth=escapement_details.teeth, anchor_teeth=escapement_details.anchor_teeth, lock=escapement_details.lock_deg, drop=escapement_details.drop_deg,
                             diameter=35)#47.5

barrel_gear_thick = 5
powered_wheel = SpringBarrel(spring=SMITHS_EIGHT_DAY_MAINSPRING, pawl_angle=math.pi, click_angle=-math.pi/2, ratchet_at_back=True, style=gear_style, base_thick=barrel_gear_thick,
                        wall_thick=10, extra_barrel_height=1.5, key_bearing=BEARING_10x15x4, lid_bearing=BEARING_10x15x4_FLANGED, barrel_bearing=BEARING_10x15x4)

train = GoingTrain(pendulum_period=1.1, wheels=3, escapement=escapement, max_weight_drop=1000, use_pulley=True, chain_at_back=False,
                         powered_wheels=2, runtime_hours=8 * 24, powered_wheel=powered_wheel, escape_wheel_pinion_at_front=False)
moduleReduction=1
pillar_style = PillarStyle.CLASSIC
#idea - larger error allowed as I don't care about the exact pendulum period, but I do want a small gear train.
#re-calculate pendulum period from smallest gear train
#setting error too large and it will just favour a longer pendulum. My aim is just to find one that's really a smaller ratio
train.calculate_ratios(max_wheel_teeth=150, min_pinion_teeth=9, wheel_min_teeth=50, pinion_max_teeth=15, max_error=200, module_reduction=moduleReduction)
#[[93, 9], [82, 9]]
print(f"Pendulum period: {train.recalculate_pendulum_period()}")#:.2f

train.set_powered_wheel_ratios([[64, 10], [69, 10]])

train.print_info(for_runtime_hours=7*24)

pendulumSticksOut=10
backPlateFromWall=40

pinion_extensions={0:1.5, 1:20}#{2:4}
powered_modules=[WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2), WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.0)]
train.gen_gears(module_sizes=[0.675, 0.675], thick=3, thickness_reduction=2 / 2.4, powered_wheel_thick=6, pinion_thick_multiplier=3, style=gear_style,
                powered_wheel_module_sizes=powered_modules, powered_wheel_pinion_thick_multiplier=2, pendulum_fixing=pendulum_fixing, lanterns=[0, 1],
                pinion_extensions=pinion_extensions, stack_away_from_powered_wheel=True, escapement_split=True)

dial_d=200
dial_width = 40#dial_d*0.15



motion_works = MotionWorks(extra_height=0, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True)
motion_works_angle_deg=360-40



pendulum = FancyPendulum(bob_d=40)

dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=DialStyle.ARABIC_NUMBERS, font=CustomFont(FancyFrenchArabicNumbers),
            outer_edge_style=DialStyle.LINES_RECT_DIAMONDS_INDICATORS, inner_edge_style=None, raised_detail=True, dial_width=dial_width)

#much faster to render while testing out other things
# dial = Dial(dial_d, DialStyle.ARABIC_NUMBERS, font="Royal Bavarian Plain", font_scale=0.8, font_path="../fonts/Royal Bavarian Plain PDF.ttf",
#             outer_edge_style=DialStyle.LINES_RECT_DIAMONDS_INDICATORS, inner_edge_style=None, raised_detail=True, dial_width=dial_width)

plaque = Plaque(text_lines=["W42#0 {:.1f}cm".format(train.pendulum_length_m * 100), "L.Wallin 2025"])
plaque = None

# layout = GearLayout2D.get_old_gear_train_layout(train, GearTrainLayout.VERTICAL_COMPACT)#(train)
# layout = GearLayout2D.get_compact_layout(train, centred_escape_wheel=True)
layout = GearLayout2D(train, centred_arbors=[0, 2, 4, 5], can_ignore_pinions=[4])

motion_works_angle_deg= rad_to_deg(layout.get_angle_between(2, 1))

# show_object(layout.get_demo())

plates = RoundClockPlates(train, motion_works, name="Wall 42", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=20,
                                motion_works_angle_deg=motion_works_angle_deg, leg_height=0, fully_round=True, style=PlateStyle.RAISED_EDGING, pillar_style=pillar_style,
                                second_hand=False, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=False, moon_complication=None, escapement_on_front=True,
                                gear_train_layout=layout)

# for i,arbor in enumerate(plates.arbors_for_plate):
#     show_object(arbor.get_assembled())#.translate(plates.bearing_positions[i]))

# show_object(plates.get_plate(back=False))
#
hands = Hands(style=HandStyle.FANCY_FRENCH, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
              length=dial_d/2, thick=motion_works.minute_hand_slot_height, outline=0)

specific_instructions = [
"The front plate needs flipping over for printing (bug in logic about which way up it should be for exporting the STL)",
]

assembly = Assembly(plates, name=clock_name, hands=hands, time_seconds=30, pendulum=pendulum, specific_instructions=specific_instructions)

if not outputSTL:
    assembly.show_clock(show_object, with_rods=True, plate_colours=[Colour.DARKER_GREY, Colour.BLACK, Colour.BLACK],
                        dial_colours=[Colour.WHITE, Colour.BLACK], bob_colours=[Colour.GOLD],
                        gear_colours=[Colour.GOLD],
                        motion_works_colours=[Colour.GOLD],
                        plaque_colours=[Colour.WHITE, Colour.BLACK],
                        ratchet_colour=Colour.GOLD,
                        hand_colours=[Colour.BRASS])

# if outputSTL:
#     assembly.get_BOM().export(clock_out_dir)