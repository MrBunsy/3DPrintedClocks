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
Plan: make a clock a 6 year old could assemble.

 - nylon M8ish machine screws to hold plates together - can get nylon dome nuts for front. hex head so it can slot into the back
 - old double cord barrel - if the lengths are correct it won't be possible to overwind the weight, so we don't need the cords to go through a hole in the bottom pillar, making the plates easier
 - will need a counterweight for the winding up cord, but can fashion this as a handle
 - ideas for the arbors:
    - make them mega-chunky. Still an M3 rod, but with a 6mm diameter plastic bit around it for a 6mm bearing?
    - Or, put bearings into the arbors itself and then then simply slot over fixed machine screws/printed parts that stick out the back plate. Then how to make it easy to line up the front plate? Cone holes on the inside?
    cone holes would be easy to line up, but then how do we stop arbors rubbing agsint the inside of the front plate? do we have a special nut we can screw on? or a plastic part we can slot over the ends?
     will this be a small part that is too small?
     what if the top ends of the arbors have a much larger bearing, and then there's an insert on the inside of this bearing with a cone, then the top plate can have a cone for the rod but also a standoff for the bearing?
     could even have cone-inserts into larger bearings on both ends, making it easy to slot together? 
     
     new idea - bearings attached to the arbors, and fixed rods on teh back plate, but with the arbor extensions threaded over the rods, like my very first clock
     then the top plate can have arbor extensions too, but with cone shaped recesses and holes slightly larger than the threaded rods, so it can slot over cleanly
     will need to have pinions without caps so they can slot together easily like the motion works
     will need bearing standoffs on the extensions. How will I do the cone recess on teh top plate?
     how will I do the crutch for the motino works? ring magnets?
     
     
     new thoughts - could use nylon bushings instead of bearings?
     also, if I did have a new design of arbor with bearings (or bushings) on the arbor, and a fixed rod - this means I could have multiple wheels on one rod
     which would result in a potentially very compact design
     although, for this to remain a simple clock, easy to understand for a child, is this an advantage or not? might still be worth investigating for future ultra-compact designs?
     
     
     idea for the centre wheel - long rod fixed to back plate, then wheel + arbor with nylon bushings. Reduce diameter on inside of front plate, then reduce diameter (or end?) just outside 
     front plate, then in that end embed a circular magnet for the crutch. 
     Then the motion works:
      - cannon pinion with magnet in base. Will need nylon bushings. End can be square - maybe with a slight lip? or taper?
      - hour wheel and minute wheel as per normal
      
    this whole idea will have a lot more friction - going to have to see how good the nylon bushings are. Most will be nylon busing on threaded rod, but the centre wheel will have 
    3D printed rod through a nylon bushing in the front plate
    
    I think I want to do this as an experiment with nylon bushings, and aim to produce a child friendly clock as a good test case.
    Key wound? careful two cord? chain?
    
    wondering about key-wound (maybe with built-in knob rather than separate key?), but will need to add soething under the plate to stop over-winding.
    
    plan for pendulum: bring back knife-edge. Can keep anchor arbor almost the same: square arbor behind the anchor, just need to change start and end z. I'll add the crutch with a collet
    
    crutch collet idea:
    
    () - collet ring that slots over anchor arbor
    ||
    || - 3d printed flat plastic
    |.| - machine screw that  will face out backwareds, so it can go into a slot in the pendulum holder
'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clock_name= "Wall Clock 49"
clock_out_dir= "out"
gear_style=GearStyle.BENT_ARMS5

second_hand_centred = False

escapement = AnchorEscapement.get_with_optimal_pallets(30, drop_deg=2)#, drop_deg=1.75)

powered_wheel = CordBarrel(diameter=45, ratchet_thick=6, rod_metric_size=4, screw_thread_metric=3, cord_thick=1, thick=15, style=gear_style, use_key=False,
                                 loose_on_rod=False, traditional_ratchet=True, power_clockwise=False, use_steel_tube=False, pawl_screwed_from_front=True)
train = GoingTrain(pendulum_period=1.5, wheels=4, escapement=escapement, max_weight_drop=1000, use_pulley=False, chain_at_back=False,
                         powered_wheels=1, runtime_hours=30, powered_wheel=powered_wheel, escape_wheel_pinion_at_front=True)

moduleReduction=0.85
pillar_style = PillarStyle.PLAIN


# train.calculate_ratios(module_reduction=1.0, pinion_max_teeth=20, min_pinion_teeth=15, wheel_min_teeth=80, max_wheel_teeth=120, max_error=0.1, loud=True)
train.set_ratios([[100, 11], [90, 10], [88, 10]])
# train.set_ratios([[88, 10], [75, 11], [80, 10]])
# train.calculate_powered_wheel_ratios()
# train.set_powered_wheel_ratios([[48*2, 10*2]])
train.set_powered_wheel_ratios([[43*2, 10*2]])


pendulumSticksOut=10
backPlateFromWall=40

# pinion_extensions={1:16, 3:10}
# powered_modules=[WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)]
# train.gen_gears(module_sizes=[1, 0.95, 0.95], thick=3, thickness_reduction=2 / 2.4, powered_wheel_thick=6, pinion_thick_multiplier=3, style=gear_style,
#                 powered_wheel_module_sizes=powered_modules, powered_wheel_pinion_thick_multiplier=2, pendulum_fixing=pendulum_fixing, lanterns=[0],
#                 pinion_extensions=pinion_extensions, stack_away_from_powered_wheel=True)

rod_size=1.2
module = WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(rod_size)
module = 1.2
pinion_type=PinionType.PLASTIC
train.generate_arbors_dicts([
    {
        #great wheel
        "module": 1.3,
        "wheel_thick" : 8,
        # "pinion_type": PinionType.LANTERN,
        "style": gear_style,
        "pinion_at_front": True
    },
    {
        #centre wheel
        "module": module,
        "wheel_thick" : 4,
        "pinion_thick": 12,
        "pinion_type": pinion_type,
        "style": gear_style,
        "pinion_at_front": True
    },
    {
        #second wheel
        "module": module,
        "wheel_thick" : 4,
        "pinion_thick": 10,
        "pinion_type": pinion_type,
        "style": gear_style,
        "pinion_extension": 18
    },
{
        # third wheel
        "module": module,
        "wheel_thick" : 4,
        "pinion_thick": 10,
        "pinion_type": pinion_type,
        "style": gear_style,
        "pinion_at_front": False,
    },
    {
        # escape wheel
        "module": module,
        "wheel_thick" : 4,
        "pinion_thick": 10,
        "pinion_type": pinion_type,
        "style": gear_style,
        "pinion_extension": 8,
        "pinion_at_front": False,
    }
])

train.print_info(weight_kg=0.500)

dial_d=160
dial_width = 27#dial_d*0.125
moon_radius=10


pendulum = Pendulum(bob_d=60, bob_thick=12, hand_avoider_inner_d=100)
# pendulum = FancyPendulum(bob_d=40)
pendulum_fixing = KnifeEdgePendulumBits()

# dial = Dial(outside_d=dial_d, bottom_fixing=True, top_fixing=False, style=DialStyle.LINES_INDUSTRIAL,
#                   seconds_style=DialStyle.LINES_ARC, pillar_style=pillar_style, raised_detail=True, dial_width=dial_width)
dial = Dial(outside_d=dial_d, bottom_fixing=True, top_fixing=False, romain_numerals_style=RomanNumeralStyle.SIMPLE_SQUARE, style=DialStyle.ROMAN_NUMERALS,
                        outer_edge_style=DialStyle.CONCENTRIC_CIRCLES,
                  seconds_style=DialStyle.LINES_ARC, pillar_style=pillar_style, raised_detail=True, dial_width=dial_width)
# plaque = Plaque(text_lines=["W40#0 {:.1f}cm L.Wallin".format(train.pendulum_length_m * 100), "2025 PLA Test"])
dial = None
plaque = None
gear_train_layout=GearLayout2D.get_compact_layout(train, start_on_right=False)#, support_second_hand=False)

motion_works = MotionWorks(extra_height=0, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True)
motion_works.calculate_size(arbor_distance=30)

motion_works_angle_deg = 90

# plates = ChildFriendlySimpleClockPlates(going_train=train, motion_works=motion_works, pendulum=pendulum, gear_train_layout=gear_train_layout, plate_thick=8,
#                            back_plate_thick=10, pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS,back_plate_from_wall=30, fixing_screws=MachineScrew(8, countersunk=True),
#                            dial=dial, pendulum_at_front=False, name=clock_name,chain_through_pillar_required=False, heavy=False, allow_bottom_pillar_height_reduction=True)

# plates = RoundClockPlates(train, motion_works, name="Wall 49", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=9,
#                                 motion_works_angle_deg=motion_works_angle_deg, leg_height=0, fully_round=True, style=PlateStyle.RAISED_EDGING, pillar_style=pillar_style,
#                                 second_hand=False, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=True,
#                                 gear_train_layout=gear_train_layout, back_plate_from_wall=27, fewer_arms=True)#, default_arbor_d=6)

plates = RectangularWallClockPlates(train, motion_works, name="Wall 49", dial=dial, plate_thick=8, layer_thick=0.2, pendulum_sticks_out=20,
                                motion_works_angle_deg=motion_works_angle_deg, style=PlateStyle.RAISED_EDGING, pillar_style=pillar_style,
                                second_hand=False, standoff_pillars_separate=True, plaque=plaque, split_detailed_plate=True,
                                gear_train_layout=gear_train_layout, back_plate_from_wall=40, pendulum_fixing=pendulum_fixing)


# pulley = LightweightPulley(diameter=plates.get_diameter_for_pulley(), rope_diameter=2, use_steel_rod=False, style=gear_style)

# hands = Hands(style=HandStyle.INDUSTRIAL, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
#                     length=dial.get_hand_length()+dial_width/4, thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True, second_hand_centred=second_hand_centred)#, secondLength=dial.second_hand_mini_dial_d*0.45, seconds_hand_thick=1.5)

hands = Hands(style=HandStyle.SIMPLE_ROUND, minute_fixing="square", minute_fixing_d1=motion_works.get_minute_hand_square_size(), hourfixing_d=motion_works.get_hour_hand_hole_d(),
                    length=200, thick=motion_works.minute_hand_slot_height, outline=1, outline_same_as_body=False, chunky=True, second_hand_centred=second_hand_centred)#, secondLength=dial.second_hand_mini_dial_d*0.45, seconds_hand_thick=1.5)
#dial.get_hand_length()+dial_width/4


assembly = Assembly(plates, name=clock_name, hands=hands, time_seconds=30, pendulum=pendulum, pulley=None)

if not outputSTL:
    assembly.show_clock(show_object, with_rods=True, plate_colours=[Colour.BROWN, Colour.BLACK, Colour.BLACK],
                        dial_colours=[Colour.WHITE, Colour.BLACK], bob_colours=[Colour.BRIGHT_ORANGE],
                        # gear_colours=[Colour.BRIGHT_ORANGE, Colour.LIME_GREEN],
                        motion_works_colours=[Colour.BRIGHT_ORANGE, Colour.BRIGHT_ORANGE, Colour.LIME_GREEN],
                        pulley_colour=Colour.LIME_GREEN, plaque_colours=[Colour.WHITE, Colour.BLACK], with_key=True,
                        # hand_colours=[Colour.GOLD]
                        )

if outputSTL:
    assembly.get_BOM().export(clock_out_dir)