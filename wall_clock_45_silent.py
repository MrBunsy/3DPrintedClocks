import math
import cadquery as cq
from clocks import *
import random

'''
A wall clock version of mantel 44. Silent escapement with same style: sword hands, roman numeral dial and modern plates

plan is to keep pendulum length the same (1/3s) so it's not visibly below the clock, but also try and see if I can get the clock relatively thin
'''

output_STL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    output_STL = True
    def show_object(*args, **kwargs):
        pass


clock_name = "Wall_45_silent"

random.seed(clock_name)

gear_style = GearStyle.SNOWFLAKE#GearStyle.ROUNDED_ARMS5
pillar_style = PillarStyle.TWISTY
plate_thick=8

teeth = 24#36
escapement_info = AnchorEscapement.get_with_optimal_pallets(teeth=teeth, drop_deg=2)
#nylon wire only 0.15, but need a hole big enough to print well
escapement = SilentPinPalletAnchorEscapement(teeth=teeth, drop=escapement_info.drop_deg, lift=escapement_info.lift_deg, run=escapement_info.run_deg, lock=escapement_info.lock_deg, pin_diameter=1.4)
barrel_gear_thick = 5

# this looks plausible, but not sure I want to push my luck
power = SpringBarrel(pawl_angle=-math.pi * 3/4, click_angle=-math.pi * 1/4, base_thick=4, barrel_bearing=BEARING_12x18x4_FLANGED,
                     style=gear_style, wall_thick=8, ratchet_thick=8, spring=SMITHS_EIGHT_DAY_MAINSPRING,
                     ratchet_screws=MachineScrew(2, grub=True), seed_for_gear_styles=clock_name+"barrel")#, key_bearing=PlainBushing(12, fake_height=plate_thick))

#idea - try thicker cord/artifical gut so will need escape wheel with fewer teeth

train = GoingTrain(pendulum_period=2 / 3, wheels=4, escapement=escapement, powered_wheels=2, runtime_hours=8 * 24, support_second_hand=True, powered_wheel=power)

train.set_powered_wheel_ratios([[61, 10], [64, 10]])

# train.calculate_ratios(max_wheel_teeth=80, min_pinion_teeth=9, pinion_max_teeth=30, wheel_min_teeth=50, loud=True)
#[60, 16], [75, 20], [40,12]
train.set_ratios([[72, 10], [75, 9], [60, 16]])
pinion_extensions = [0, 0, 3, 25, 0, 10]
module_sizes = [1.0, 0.9, 0.9]

print(f"Pendulum period: {train.recalculate_pendulum_period():.2f}")

pendulum_sticks_out = 17
back_plate_from_wall = 34

#intermediate wheel pinion thicker than needed so it can use the one size of 1.2mm dowels I've got in stock
pinion_thicks = [-1, barrel_gear_thick*2, 7.5, 7, 7, 7]

powered_modules = [WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2)]

all_modules = powered_modules + module_sizes

# train.generate_arbors_lists(modules=all_modules, thicknesses=[barrel_gear_thick, 4, 2.4], pinions_face_forwards=[True, True, True, False, True, True, False],
#                             pinion_extensions=pinion_extensions, lanterns=[0, 1], reduction=0.9, pinion_thicks=pinion_thicks, styles=gear_style)

train.generate_arbors_dicts([
    {
        #barrel
        "module":WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5),
        "wheel_thick": barrel_gear_thick,
        "style": gear_style,

    },
    {
        #intermediate wheel
        "module":WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2),
        "pinion_type": PinionType.THIN_LANTERN,
        "pinion_thick": barrel_gear_thick*2,
        "wheel_thick": 4,

    },
    {
        #centre wheel
        "module": 1.0,
        "pinion_faces_forwards": True,
        # "pinion_thick": 7
        "pinion_type": PinionType.LANTERN,
        "wheel_thick": 2.4,

    },
    {
        #second wheel
        "module": 0.9,
        "pinion_extension": 25
    },
    {
        #third wheel
        "module": 0.9,
        "pinion_faces_forwards": True
    },
    {
        #escape wheel
        "pinion_faces_forwards": True,
        "pinion_extension": 10
    }
], pinion_thick_extra=5)


pendulum = Pendulum(hand_avoider_inner_d=100, bob_d=50, bob_thick=9, bob_nut_d=12)

dial_d = 175
seconds_dial_width = 7
dial_width = 28# + 2.5

dial_d=210
dial_width = 33#dial_d*0.15

dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False,  style=DialStyle.ARABIC_NUMBERS, font=CustomFont(FancyFrenchArabicNumbers),
            outer_edge_style=DialStyle.LINES_RECT_DIAMONDS_INDICATORS, inner_edge_style=None, raised_detail=True, dial_width=dial_width, seconds_style=DialStyle.CONCENTRIC_CIRCLES,
            seconds_dial_width=seconds_dial_width, pillar_style=pillar_style)

motion_works_height = 10

# tiny bit extra gap as the brass PETG seems to need it
motion_works = MotionWorks(extra_height=motion_works_height, style=gear_style, thick=3, compact=True,
                           cannon_pinion_to_hour_holder_gap_size=0.6, reduced_jamming=True)


plate_style = PlateStyle.SIMPLE

plaque = Plaque(text_lines=["W45#0 {:.1f}cm 2025".format(train.pendulum_length_m * 100), "3DPrintedClocks.co.uk"])#github.com/MrBunsy/3DPrintedClocks

gear_train_layout = GearLayout2D.get_compact_layout(train, start_on_right=False, minimum_anchor_distance=True)
bearing_positions = gear_train_layout.get_positions()
arm_dir = (bearing_positions[1][0] - bearing_positions[2][0], bearing_positions[1][1] - bearing_positions[2][1])
motion_works_angle_deg = rad_to_deg(math.atan2(arm_dir[1], -arm_dir[0]))
'''
TODO:
 - motion works along an arm DONE
 - new option for plates? reduce arms. this could have only two arsm at an angle from teh spring arbor,and no arm for the escape wheel PARTIALLY DONE
 - increase radius or have little arm for anchor? - see below, will try and bring anchor down
 - fix ratchet positionion (might be broken for all round spring clocks?)
 - potentially move anchor downwards, since we can ensure it completely avoids clashing with any wheels. Will require some tweaks to GearLayout2D. Will the pendulum still fit?
 - pinion extensions for lantern pinions could just have a solid extension if above a certain amount? like normal pinion extensions.
'''

plates = RoundClockPlates(train, motion_works, name="Wall 45", dial=dial, plate_thick=plate_thick, layer_thick=0.2, pendulum_sticks_out=pendulum_sticks_out,
                                motion_works_angle_deg=motion_works_angle_deg, leg_height=0, fully_round=True, style=plate_style, pillar_style=pillar_style,
                                second_hand=True, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=False,
                                gear_train_layout=gear_train_layout, fewer_arms=True, back_plate_from_wall=back_plate_from_wall)

hand_style = HandStyle.FANCY_FRENCH
hands = Hands(style=hand_style, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
              length=dial.outside_d * 0.5, thick=motion_works.minute_hand_slot_height, outline=0, outline_same_as_body=False, chunky=True,
              second_length=dial.second_hand_mini_dial_d * 0.5 - seconds_dial_width / 2, seconds_hand_thick=1.5, outline_on_seconds=0, include_seconds_hand=True)

# hands.show_hands(show_object)
#
assembly = Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, with_mat=False, name=clock_name, key_angle_deg=360 / 12, time_mins=15)

plate_colours = [Colour.LIGHTGREY, Colour.DARKGREY]
motion_works_colours = [Colour.LIGHTBLUE, Colour.LIGHTBLUE, Colour.BLUE]
hand_colours=[Colour.GOLD]

if output_STL:
    assembly.get_BOM().export()
else:
    # show_object(plates.arbors_for_plate[1].get_assembled())
    # show_object(plates.arbors_for_plate[0].get_shapes()["wheel"])
    assembly.show_clock(show_object,
                        bob_colours=[Colour.GOLD], with_rods=True, with_key=True, ratchet_colour=Colour.PURPLE, dial_colours=[Colour.WHITE, Colour.BLACK],
                        plate_colours=plate_colours, motion_works_colours=motion_works_colours, hand_colours=hand_colours)