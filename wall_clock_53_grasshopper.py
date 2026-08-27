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
from clocks import *

'''
second attempt at a grasshopper. Same as teh first attempt (clock 14) but with space to fit hands on properly and less drooping of the escape wheel and frame
A regenerated clock 14 will benefit from the improvements to the plates, but this rejigged the gear train so there's more space

'''
export_stls=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    export_stls = True
    def show_object(*args, **kwargs):
        pass


clock_name= "wall_clock_53"
clock_out_dir= "out"
gear_style=GearStyle.BENT_ARMS5
pillar_style=PillarStyle.DOUBLE_BARLEY_TWIST


#copied from clock 15, make sure there's space for the front anchor bearing holder to not clash with the arms
need_space = SimpleClockPlates.get_lone_anchor_bearing_holder_thick() + WASHER_THICK_M3
#also -1 from frame_thick because I've reduced front_anchor_from_plate by one

#although we're planning to stick this on a shorter pendulum, so it won't meet harrison's stipulations, but should work fine. I'm not going for mega accuracy
escapement = GrasshopperEscapement.get_harrison_compliant_grasshopper(frame_thick=10 - need_space+1, composer_min_distance=need_space)

#hoping that a slightly thicker spring and using more of its turns we can pull just enough extra power for the grasshopper
power = SpringBarrel(pawl_angle=-math.pi * 3/4, click_angle=-math.pi * 1/4, base_thick=6, barrel_bearing=BEARING_12x18x4_FLANGED,
                     style=gear_style, wall_thick=8, ratchet_thick=8, spring=MAINSPRING_185045,
                     ratchet_screws=MachineScrew(3, grub=True), seed_for_gear_styles=clock_name+"barrel", ratchet_pawl_screwed_from_front=True, fraction_of_max_turns=0.6,
                     key_bearing=BEARING_12x18x4_THIN)

train = GoingTrain(pendulum_period=1.5, wheels=3, escapement=escapement,powered_wheels=2, runtime_hours=7.5 * 24, powered_wheel=power)

# train.calculate_powered_wheel_ratios(prefer_large_second_wheel=False)
# train.calculate_ratios()

#the results of above, just to save processing time
# train.set_powered_wheel_ratios([[58, 11], [55, 10]])
train.set_powered_wheel_ratios([[59, 11], [55, 10]])
train.set_ratios([[50, 13], [52, 10]])

train.generate_arbors_dicts([
    {
        #spring barrel
        "wheel_thick": 6,
        "style": gear_style,
        "pinion_at_front": True,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 3,
        "pinion_type": PinionType.LANTERN,
        "rod_diameter": 11.9,
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.6, leaves=train.chain_wheel_ratios[0][1]),
    },
    {
        #intermediate wheel
        "wheel_thick": 4,
        "pinion_at_front": True,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_type": PinionType.LANTERN_THIN,
        "rod_diameter": 3,
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2, leaves=train.chain_wheel_ratios[1][1]),
        "pinion_thick": 9
    },
    {
        #centre wheel
        "wheel_thick": 3,
        "pinion_at_front": True,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 1,
        "pinion_type": PinionType.LANTERN,
        "rod_diameter": 3,
        "module": 1.2,
        "pinion_thick": 7,
    },
    {
        #second wheel
        "wheel_thick": 2.5,
        "pinion_at_front": False,
        "arbor_split": SplitArborType.NORMAL_ARBOR,
        "pinion_extension": 20,
        "pinion_type": PinionType.PLASTIC,
        "rod_diameter": 3,
        "module": 1.2,
        "pinion_thick": 7
    },
    {
        #escape wheel
        "wheel_thick": 8,
        "pinion_at_front": False,
        "arbor_split": SplitArborType.WHEEL_OUT_FRONT_WITH_PLATE,
        # "pinion_extension": 9,
        "pinion_type": PinionType.PLASTIC,
        "rod_diameter": 3,
        "pinion_thick": 7
    },
    {
        #anchor
        "arbor_split": SplitArborType.WHEEL_OUT_FRONT_WITH_PLATE,
    }
])
#would love to have this on the clock, but it really doesn't fit. Might still have another go later
days = False
if days:
    #module=0.8
    days_complication = DayOfWeekComplication(module=0.7, style=gear_style, bevel_module=1.1, angle_deg=-60, extra_z_height=0, cylinder_length=28)
else:
    days_complication = None

motion_works = MotionWorks(extra_height=20, style=gear_style, thick=3, compensate_loose_arbor=False, compact=True, inset_at_base=TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT-3, drives_complication=days_complication)
motion_works.calculate_size(30)

if days_complication is not None:
    days_complication.set_motion_works_sizes(motion_works)

plaque = None
dial_d=190
dial_width = 30

#the art deco style I like, but already have one of
# dial = Dial(dial_d, DialStyle.ARABIC_NUMBERS, font="Dutch Courage", font_scale=0.9,
#                 font_path="../fonts/dutch_courage/CCDutchCourageLite/CCDutchCourageLite.ttf", outer_edge_style=DialStyle.LINES_RECT, inner_edge_style=None,
#                 dial_width=dial_width, pillar_style=pillar_style, raised_detail=True)

#got one of these in teh office, would like one at home
dial = Dial(outside_d=dial_d, bottom_fixing=False, top_fixing=False, style=DialStyle.ROMAN_NUMERALS, romain_numerals_style=RomanNumeralStyle.SIMPLE_ROUNDED, inner_edge_style=None,
                  outer_edge_style=DialStyle.CONCENTRIC_CIRCLES, raised_detail=True, dial_width=dial_width, pillar_style=pillar_style)

gear_layout =  GearLayout2D.get_eight_day_grasshopper(train)

motion_works_angle = math.pi*1.5 - (gear_layout.get_angle_between(2,1) - math.pi*1.5)

print(f"dial support lengths: {dial.support_length}")

plaque = Plaque(text_lines=["W53#0 {:.1f}cm L.Wallin 2026".format(train.pendulum_length_m * 100), "3DPrintedClocks.co.uk"])





plates = GrasshopperRoundPlates(train, motion_works, name="Wall Clock 53#0", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=12,back_plate_from_wall=40,
                                motion_works_angle_deg=rad_to_deg(motion_works_angle), leg_height=0, fully_round=True, style=PlateStyle.SIMPLE, pillar_style=pillar_style,
                                second_hand=False, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=True, fewer_arms=True, gear_train_layout=gear_layout, endshake=1,
                                days_complication = days_complication)
print(f"dial support lengths: {dial.support_length}")
print(plates.bearing_positions)

hands = Hands(style=HandStyle.ART_DECO2, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                  length=dial.get_hand_length(), thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True,
                  outline_on_seconds=0, second_hand_centred=False, include_seconds_hand=False)

pendulum = Pendulum(bob_d=80, bob_thick=15)


assembly = Assembly(plates, hands=hands, time_seconds=30, pendulum=pendulum, name=clock_name, key_angle_deg=360/12)
print(f"dial support lengths: {dial.support_length}")

assembly.show_clock(show_object, with_key=True, with_rods=True, with_pendulum=True,
                    # gear_colours=[Colour.RED, Colour.ORANGE, Colour.YELLOW, Colour.GREEN, Colour.TEAL, Colour.LIGHTBLUE, Colour.BLUE, Colour.PURPLE],
                    gear_colours=[Colour.RED, Colour.ORANGE, Colour.YELLOW, Colour.GREEN, Colour.LIGHTBLUE, Colour.BLUE, Colour.DARKBLUE, Colour.PURPLE, Colour.DARK_PURPLE],
                    # motion_works_colours=[Colour.LIGHTBLUE, Colour.LIGHTBLUE, Colour.BLUE])
                    motion_works_colours=[Colour.BLUE, Colour.BLUE, Colour.LIGHTBLUE],
                    dial_colours = [Colour.WHITE, Colour.BLACK],
                    plate_colours=[Colour.DARKGREY, Colour.BRASS],
                    ratchet_colour=Colour.PURPLE)

if export_stls:
    assembly.get_BOM().export()