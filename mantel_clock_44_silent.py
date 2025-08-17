import math
import cadquery as cq
from clocks import *


output_STL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    output_STL = True
    def show_object(*args, **kwargs):
        pass

steampunk = False

clock_name = "Mantel_44_silent"

second_hand = True
tall = not second_hand
moon = False
gear_style = GearStyle.ROUNDED_ARMS5
pillar_style = PillarStyle.CLASSIC

if not steampunk:
    pillar_style = PillarStyle.TWISTY


teeth = 30 if not second_hand else 36
escapement_info = AnchorEscapement.get_with_optimal_pallets(teeth=teeth, drop_deg=2)
#nylon wire only 0.15, but need a hole big enough to print well
escapement = SilentPinPalletAnchorEscapement(teeth=teeth, drop=escapement_info.drop_deg, lift=escapement_info.lift_deg, run=escapement_info.run_deg, lock=escapement_info.lock_deg, pin_diameter=1.0)
barrel_gear_thick = 5

# this looks plausible, but not sure I want to push my luck
power = SpringBarrel(pawl_angle=-math.pi * 0.8125, click_angle=-math.pi * 0.2125, base_thick=barrel_gear_thick,
                     style=gear_style, wall_thick=8, ratchet_thick=8, spring=SMITHS_EIGHT_DAY_MAINSPRING, key_bearing=BEARING_10x15x4, lid_bearing=BEARING_10x15x4_FLANGED, barrel_bearing=BEARING_10x15x4)

train = GoingTrain(pendulum_period=2 / 3, wheels=4, escapement=escapement, powered_wheels=2, runtime_hours=8 * 24, support_second_hand=second_hand, powered_wheel=power)

train.set_powered_wheel_ratios([[61, 10], [64, 10]])

if second_hand:
    # 2/3s with second hand with 36 teeth
    train.set_ratios([[75, 9], [72, 10], [55, 22]])
    # pinion_extensions = {0: 1, 1: 15, 2: 0}
    pinion_extensions = [0, 0, 2, 25, 0, 10]
    module_sizes = [0.8, 0.75, 0.75]
else:
    # 2/3s without second hand with 30 teeth
    train.set_ratios([[72, 10], [70, 12], [60, 14]])
    # pinion_extensions = {0: 1, 1: 3, 3: 8}
    pinion_extensions = [0, 0, 2, 3, 0, 8]
    module_sizes = [1, 0.9, 0.9]

print(f"Pendulum period: {train.recalculate_pendulum_period():.2f}")

pendulum_sticks_out = 10
back_plate_from_wall = 30

#intermediate wheel pinion thicker than needed so it can use the one size of 1.2mm dowels I've got in stock
pinion_thicks = [-1, barrel_gear_thick*2, 7.5, 7, 7, 7]

powered_modules = [WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2), WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.0)]

all_modules = powered_modules + module_sizes

train.generate_arbors(modules=all_modules, thicknesses=[barrel_gear_thick, 4, 2.4], pinions_face_forwards=[True, True, True, False, True, True, False],
                      pinion_extensions=pinion_extensions, lanterns=[0, 1], reduction=0.9, pinion_thicks=pinion_thicks, styles=gear_style)


pendulum = Pendulum(hand_avoider_inner_d=100, bob_d=50, bob_thick=10)

dial_d = 160+15#165  # 205
dial_width = 20+15/2
seconds_dial_width = 7
if second_hand:
    dial_width = 22+6#25  # 31.5#32.5

moon_radius = 13

if moon:
    moon_complication = MoonPhaseComplication3D(gear_style=gear_style, first_gear_angle_deg=205, on_left=False, bevel_module=1.1, module=0.9, moon_radius=moon_radius,
                                                bevel_angle_from_hands_deg=90, moon_from_hands=(dial_d / 2 - dial_width) - moon_radius - 5, moon_inside_dial=True)
else:
    moon_complication = None

dial = None

if dial is None:
    if moon:
        dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=DialStyle.DOTS, dial_width=dial_width, pillar_style=pillar_style)
    else:
        if steampunk or True:
            dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, romain_numerals_style=RomanNumeralStyle.SIMPLE_SQUARE, style=DialStyle.ROMAN_NUMERALS,
                        outer_edge_style=DialStyle.CONCENTRIC_CIRCLES, seconds_style=DialStyle.CONCENTRIC_CIRCLES, dial_width=dial_width, pillar_style=pillar_style, raised_detail=True,
                        seconds_dial_width=seconds_dial_width)
        else:
            dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=DialStyle.LINES_INDUSTRIAL, dial_width=dial_width, pillar_style=pillar_style, seconds_style=DialStyle.CONCENTRIC_CIRCLES)


else:
    dial.dial_width = dial_width
    # just want to set outside d, everything else will be overriden by plates
    dial.configure_dimensions(10, 10, outside_d=dial_d)
    dial.seconds_dial_width = seconds_dial_width
    dial.pillar_style = pillar_style

motion_works_height = 22 if moon else 10

# tiny bit extra gap as the brass PETG seems to need it
motion_works = MotionWorks(extra_height=motion_works_height, style=gear_style, thick=3, compact=True, moon_complication=moon_complication,
                           cannon_pinion_to_hour_holder_gap_size=0.6, reduced_jamming=True)

motion_works_angle_deg = -1

if moon:
    motion_works_angle_deg = 180 + 40
    # if not zig_zag_side:
    #     motion_works_angle_deg = 360 - 40
    motion_works.calculate_size(arbor_distance=30)
    moon_complication.set_motion_works_sizes(motion_works)

plate_style = PlateStyle.RAISED_EDGING

if not steampunk:
    plate_style = PlateStyle.SIMPLE

plaque = Plaque(text_lines=["M44#0 {:.1f}cm ".format(train.pendulum_length_m * 100), "L.Wallin 2025"])#github.com/MrBunsy/3DPrintedClocks


plates = MantelClockPlates(train, motion_works, name="Mantel 44", dial=dial, plate_thick=7, back_plate_thick=6, style=plate_style,
                           pillar_style=pillar_style, moon_complication=moon_complication, second_hand=second_hand, symetrical=True, pendulum_sticks_out=21,
                           standoff_pillars_separate=True, fixing_screws=MachineScrew(4, countersunk=False), motion_works_angle_deg=motion_works_angle_deg,
                           plaque=plaque, split_detailed_plate=True, prefer_tall=tall, gears_start_on_right=False, feet_extension=5)

# show_object(plates.gear_train_layout.get_demo())

hands = None
if hands is None:
    hand_style = HandStyle.SWORD
    hands = Hands(style=hand_style, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                  length=dial.outside_d * 0.45, thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True,
                  second_length=dial.second_hand_mini_dial_d * 0.5 - seconds_dial_width / 2 if second_hand else 25, seconds_hand_thick=1.5, outline_on_seconds=0.5, include_seconds_hand=True)
    #dial.second_hand_mini_dial_d * 0.5 - seconds_dial_width / 2 if second_hand else 1
else:
    hands.configure_motion_works(motion_works)
    hands.configure_length(dial.outside_d * 0.5 - dial_width / 2, second_length=dial.second_hand_mini_dial_d * 0.5 - seconds_dial_width / 2 if second_hand else 1)

# hands.show_hands(show_object)
#
assembly = Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, with_mat=True, name=clock_name, key_angle_deg=360 / 12)

# plate_colours = [Colour.DARK_PURPLE, Colour.BRASS, Colour.BRASS]
plate_colours = [Colour.BLACK, Colour.GOLD, Colour.GOLD]
motion_works_colours=[Colour.BRASS]
# plate_colours = [Colour.DARKBLUE, Colour.BRASS, Colour.BRASS]
if not steampunk:
    plate_colours = [Colour.LIGHTGREY, Colour.DARKGREY]
    motion_works_colours = [Colour.LIGHTBLUE, Colour.LIGHTBLUE, Colour.BLUE]

if output_STL:
    assembly.get_BOM().export()
else:
    #, hand_colours=[Colour.WHITE, Colour.BLACK], motion_works_colours=[Colour.BRASS]
    assembly.show_clock(show_object,
                        bob_colours=[Colour.GOLD], with_rods=True, with_key=True, ratchet_colour=Colour.PURPLE, dial_colours=[Colour.WHITE, Colour.BLACK],
                        plate_colours=plate_colours, motion_works_colours=motion_works_colours)
    # show_object(plates.arbors_for_plate[5].get_escape_wheel())