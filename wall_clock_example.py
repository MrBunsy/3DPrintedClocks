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
import clocks as clock

'''
Experiment to see if I have enough power to get a month runtime on a clock

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_25b"
clockOutDir="out"
gear_style=clock.GearStyle.BENT_ARMS5
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

#1.5deg of lock results in a slight recoil as the teeth land on the pallet rather than the inner edge (as first printed). Going back to 2deg
#closer inspection shows that actually the anchor is slightly too far away. Is the front anchor holder at an angle?
#might be worth instead filing the "feet" of it flat or slightly at an angle to get the anchor and escape wheel closer together
escapement = clock.AnchorEscapement.get_with_optimal_pallets(teeth=30, drop_deg=2.75, lock_deg=1.5, diameter=45, force_diameter=True, anchor_thick=10)

train = clock.GoingTrain(pendulum_period=2.0, wheels=3, escapement=escapement, max_weight_drop=1500, use_pulley=True, chain_at_back=False,
                         powered_wheels=2, runtime_hours=32 * 24, support_second_hand=False)#, huygensMaintainingPower=True)

moduleReduction=0.9

train.calculate_ratios(max_wheel_teeth=120, min_pinion_teeth=12, wheel_min_teeth=70, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction, loud=True, favour_smallest=True)


#TODO one screw goes straight through the hole used to tie the cord! printed clock is assembled with just three screws
#also reduced ratchet diameter slightly after initial print as the pawl looks like it can bump into the next pinion
train.gen_cord_wheels(ratchet_thick=8, rod_metric_thread=4, cord_thick=2, cord_coil_thick=14, style=gear_style, use_key=True, prefered_diameter=35, loose_on_rod=False, prefer_small=True,
                      min_wheel_teeth=70, traditional_ratchet=True, cap_diameter=65, ratchet_diameter=33)

train.calculate_powered_wheel_ratios(pinion_min=10, pinion_max=12, wheel_min=50, wheel_max=120)

pendulumSticksOut=10
backPlateFromWall=30

powered_modules = [clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5), clock.WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2)]

lanterns=[0, 1]
pinion_extensions = {0:2, 1:2}
#want to make second powered wheel have chunkier rod, but really struggling to get the rest of the train to fit without a crazy small module.
#let's see if m3 is enough
rod_diameters = [4,3,3,3,3,3]

train.gen_gears(module_size=0.675, module_reduction=moduleReduction, thick=2.4, thickness_reduction=0.9, powered_wheel_thicks=[8,5], pinion_thick_extra=5, style=gear_style,
                powered_wheel_pinion_thick_multiplier=1.5, pendulum_fixing=pendulumFixing, stack_away_from_powered_wheel=True,
                powered_wheel_module_sizes=powered_modules, lanterns=lanterns, pinion_extensions=pinion_extensions, rod_diameters=rod_diameters, escapement_split=True)
train.print_info(weight_kg=6)

motionWorks = clock.MotionWorks(extra_height=10, style=gear_style, thick=3, compensate_loose_arbour=False, compact=True, reduced_jamming=True, cannon_pinion_to_hour_holder_gap_size=0.75)
motionWorks.calculate_size(arbor_distance=30)

pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=100, bob_thick=15)
#toying with making dial wider if I reprint
dial = clock.Dial(outside_d=192.5+10, dial_width=192.5/10 + 5, style=clock.DialStyle.LINES_INDUSTRIAL, pillar_style=clock.PillarStyle.BARLEY_TWIST, top_fixing=False)

plaque = clock.Plaque(text_lines=["W25#0 {:.1f}cm".format(train.pendulum_length_m * 100), "L.Wallin 2024"])

#anchor_distance_fudge_mm judged by eye tinkering with a modelled escapement to get it to behave like the real one
#I think that the escape wheel is being angled downwards as the back of the arbor is pressed upwards, and it's hinging aroudn the front plate.
#this likely affects most clocks with the escapement on the front and a compact gear layout
plates = clock.RoundClockPlates(train, motionWorks, second_hand=False, style=clock.PlateStyle.RAISED_EDGING, pillar_style=clock.PillarStyle.BARLEY_TWIST, fully_round=True,
                                leg_height=0, plaque=plaque, dial=dial, motion_works_angle_deg=180+30, escapement_on_front=True, name="Clock 25", split_detailed_plate=True,
                                plate_thick=10, anchor_distance_fudge_mm=-0.5, off_centre_escape_wheel=False)

hands = clock.Hands(style=clock.HandStyle.INDUSTRIAL, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motionWorks.minute_hand_slot_height, outline=0, outline_same_as_body=False, chunky=True, second_length=20, seconds_hand_thick=1.5)

#TODO pullet capable of holding two weights, I think two cheap weights in fancy shells looks better and works out a similar price to one large cheap (ugly) weight

pulley = clock.BearingPulley(diameter=plates.get_diameter_for_pulley(), bearing=clock.get_bearing_info(4), wheel_screws=clock.MachineScrew(2, countersunk=True, length=8),
                             style=gear_style)
# print("pulley needs screws {} {}mm and {} {}mm".format(pulley.screws, pulley.get_total_thick(), pulley.hook_screws, pulley.get_hook_total_thick()))


assembly = clock.Assembly(plates, hands=hands, time_seconds=30, pulley = pulley, pendulum=pendulum, name=clockName)#, timeHours=12, timeMins=0)#weights=[clock.Weight(height=245,diameter=55)]

if not outputSTL:
    # show_object(pulley.get_assembled())
    assembly.show_clock(show_object, motion_works_colours=[clock.Colour.BRASS],
                    bob_colours=[clock.Colour.PURPLE], plate_colours=[clock.Colour.DARKBLUE, clock.Colour.BRASS, clock.Colour.BRASS, clock.Colour.BRASS],
                    hand_colours=[clock.Colour.RED], with_rods=True)

# show_object(plates.getDrillTemplate(6))

if outputSTL:
    assembly.get_BOM().export()
    #
    #
    # train.output_STLs(clockName,clockOutDir)
    # plaque.output_STLs(clockName, clockOutDir)
    # motionWorks.output_STLs(clockName,clockOutDir)
    # pendulum.output_STLs(clockName, clockOutDir)
    # plates.output_STLs(clockName, clockOutDir)
    # hands.output_STLs(clockName, clockOutDir)
    # pulley.output_STLs(clockName, clockOutDir)
    # assembly.output_STLs(clockName, clockOutDir)


    # clock.outputSTLMultithreaded([train, motionWorks,pendulum,dial,plates,hands,pulley,assembly], clockName, clockOutDir)
