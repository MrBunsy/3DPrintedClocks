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
With the success of mantel clock 34 (attempting to shrink down the spring barrel) I want to try and see how small I can make a spring driven wall clock
so the gear train from mantel clock 34, but in a wall clock

not printed.

Plan: make this a good test case for improving timekeeping with silent escapement
 - Reduce gap in anchor so the string is slightly more taunt
 - have a go at geneva stopworks!
'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "Wall Clock 43"
clock_out_dir= "out"
gear_style=GearStyle.ROUNDED_ARMS5

teeth=30
#escapement = AnchorEscapement.get_with_optimal_pallets(36, drop_deg=2)
escapement_info = AnchorEscapement.get_with_optimal_pallets(teeth, drop_deg=2)
#nylon wire only 0.15, but need a hole big enough to print well
#pin_external_length is the badly named gap between arms of the anchor. This will be double endshake + escape wheel thick + 1
escapement = SilentPinPalletAnchorEscapement(teeth=teeth, drop=escapement_info.drop_deg, lift=escapement_info.lift_deg, run=escapement_info.run_deg, lock=escapement_info.lock_deg,
                                             pin_diameter=1.0, pin_external_length=1.5*2 + 3 + 1)

barrel_gear_thick = 5
powered_wheel = SpringBarrel(spring=SMITHS_EIGHT_DAY_MAINSPRING, pawl_angle=-math.pi * 3/4, click_angle=-math.pi * 1/4, ratchet_at_back=True, style=gear_style, base_thick=BEARING_10x15x4_FLANGED.height,
                        wall_thick=8, key_bearing=BEARING_10x15x4, lid_bearing=BEARING_10x15x4_FLANGED, barrel_bearing=BEARING_10x15x4_FLANGED, ratchet_screws=MachineScrew(2, grub=True))

train = GoingTrain(pendulum_length_m=0.20, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False, powered_wheels=2,
                             runtime_hours=8 * 24, support_second_hand=False, escape_wheel_pinion_at_front=False, powered_wheel=powered_wheel)


module_reduction=0.9
train.set_powered_wheel_ratios([[61, 10], [64, 10]])

#found gear train with large error so it's not huge as we don't actually care about the exact length of pendulum.
# train.calculate_ratios(max_wheel_teeth=80, min_pinion_teeth=10, wheel_min_teeth=50, pinion_max_teeth=15, max_error=200, module_reduction=1, loud=True)
train.set_ratios([[63, 10], [56, 10], [50, 13]])
print(f"Pendulum period: {train.recalculate_pendulum_period()}")#:.2f


pinion_extensions =  {0: 1, 1: 15, 2: 0}
module_sizes = [0.8, 0.75, 0.75]

pillar_style = PillarStyle.CLASSIC

train.print_info(for_runtime_hours=7*24)

pendulumSticksOut=10
backPlateFromWall=40

train.generate_arbors_dicts([
    {
        #barrel
        "module":WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2),
        "wheel_thick": barrel_gear_thick,
        "style": gear_style,

    },
    {
        #intermediate wheel
        "module":WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.0),
        "pinion_type": PinionType.LANTERN_THIN,
        "pinion_thick": barrel_gear_thick*2,
        "wheel_thick": 4,
        "style": gear_style,

    },
    {
        #centre wheel
        "module": 0.925,
        "pinion_at_front": True,
        # "pinion_thick": 7
        "pinion_type": PinionType.LANTERN,
        "wheel_thick": 2.4,

    },
    {
        #second wheel
        "module": 0.925,
        "pinion_extension": 25,

    },
    {
        #third wheel
        "module": 0.925,
        "pinion_at_front":False,
        "pinion_thick":6

    },
    {
        #escape wheel
        "pinion_at_front": True,
        "pinion_extension": 19,
        "pinion_thick":6
    }
], pinion_thick_extra=5)
# motion_works = MotionWorks(extra_height=0, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True)


motion_works = MotionWorks(extra_height=8, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True, reduced_jamming=True,
                                module=1, inset_at_base=TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT-1)#, cannon_pinion_to_hour_holder_gap_size=0.6)#, bearing=clock.get_bearing_info(3)
#make furtehr apart so we get a big enough cannon pinion for the inset_at_base, which we want so we don't clash with the escape wheel
motion_works.calculate_size(arbor_distance=35)

pendulum = FancyPendulum(bob_d=40)
dial_d=175
seconds_dial_width = 7

dial_width=30

dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=DialStyle.ROMAN_NUMERALS, romain_numerals_style=RomanNumeralStyle.SIMPLE_ROUNDED,
            outer_edge_style=DialStyle.CONCENTRIC_CIRCLES, inner_edge_style=None, raised_detail=True, dial_width=dial_width, seconds_dial_width=seconds_dial_width, pillar_style=pillar_style)

plaque = Plaque(text_lines=["W43#0 {:.1f}cm".format(train.pendulum_length_m * 100), "L.Wallin 2025"])

gear_train_layout = GearLayout2D.get_compact_layout(train, start_on_right=True, extra_anchor_distance=8)

# motion_works_angle_deg=360-40
motion_works_angle_deg= 180-rad_to_deg(gear_train_layout.get_angle_between(2,1))
plates = RoundClockPlates(train, motion_works, name="Wall 43", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=12,
                                motion_works_angle_deg=motion_works_angle_deg, leg_height=0, fully_round=True, style=PlateStyle.RAISED_EDGING, pillar_style=pillar_style,
                                second_hand=False, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=False, moon_complication=None, escapement_on_front=False,
                          gear_train_layout=gear_train_layout, fewer_arms=True, back_plate_from_wall=30)

# hands = Hands(style=HandStyle.DIAMOND, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
#               length=dial_d/2, thick=motion_works.minute_hand_slot_height, outline=0, seconds_hand_thick=1, second_length=25)
hands = Hands(style=HandStyle.SPADE, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
              length=dial.get_hand_length(reach_outer_edge=True), thick=motion_works.minute_hand_slot_height, outline=1, seconds_hand_thick=1, second_length=25)
specific_instructions = [
"The front plate needs flipping over for printing (bug in logic about which way up it should be for exporting the STL)",
]


assembly = Assembly(plates, name=clock_name, hands=hands, time_seconds=30, pendulum=pendulum, specific_instructions=specific_instructions,
                    key_angle_deg=360/12)

if not outputSTL:
    assembly.show_clock(show_object, with_rods=True, plate_colours=[Colour.BROWN, Colour.BLACK, Colour.BLACK],
                        dial_colours=[Colour.WHITE, Colour.BLACK], bob_colours=[Colour.GOLD],
                        gear_colours=[Colour.GOLD],
                        motion_works_colours=[Colour.GOLD],
                        plaque_colours=[Colour.WHITE, Colour.BLACK],
                        ratchet_colour=Colour.GOLD,
                        # hand_colours=[Colour.BLACK, Colour.GOLD],
                        # hand_colours=[Colour.GOLD],
                        with_key=True)

if outputSTL:
    assembly.get_BOM().export(clock_out_dir)