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
from clocks import clock

'''
Loosely styled on a rolex

TODO ensure key is right length and isn't recessed into front plate - I think current logic assumes it's inside the dial
also optimise placement of pawl on the ratchet so I can increase the diameter of the ratchet gear wheel and keep lots of the gear style cut

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        # print(args)
        # if args[0] is None:
        #     raise ValueError("invalid object to show")
        pass

clockName="wall_clock_28"
clockOutDir="out"
gearStyle=clock.GearStyle.DIAMONDS
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS

#for period 1.5
# drop =1.5
# lift =3
# lock=1.5
# escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)
# escapement = clock.GrasshopperEscapement(acceptableError=0.001, teeth=60, tooth_span=9.5, pendulum_length_m=clock.getPendulumLength(1.5), mean_torque_arm_length=10, loud_checks=True, skip_failed_checks=True, ax_deg=89)
lift=4
drop=2
lock=2
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4,
                                    style=clock.AnchorStyle.CURVED_MATCHING_WHEEL, wheelThick=2)
train = clock.GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, max_weight_drop=1000, use_pulley=True, chain_at_back=False, chain_wheels=1, runtime_hours=7.5 * 24)#, huygensMaintainingPower=True)

moduleReduction=0.85

train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction)

train.gen_cord_wheels(ratchet_thick=6, rod_metric_thread=4, cord_thick=1, cord_coil_thick=16, style=gearStyle, use_key=True, prefered_diameter=25,
                      loose_on_rod=False, prefer_small=True, traditional_ratchet=True)#, ratchet_diameter=29 + 27.5)

train.set_chain_wheel_ratio([67, 11])

pendulumSticksOut=20

train.gen_gears(module_size=1, module_reduction=moduleReduction, thick=2.4, thickness_reduction=0.9, chain_wheel_thick=6, pinion_thick_multiplier=3, style=gearStyle,
                powered_wheel_module_increase=1, chain_wheel_pinion_thick_multiplier=2, pendulum_fixing=pendulumFixing)
train.print_info(weight_kg=2)

train.get_arbour_with_conventional_naming(0).print_screw_length()


#extra height so that any future dial matches up with the dial height currently printed from the old (wrong) calculations,
# but if I re-printed the motion works, the hands would be properly in front of the dial (currently hour hand is in-line with dial)
motionWorks = clock.MotionWorks(extra_height=10, style=gearStyle, thick=3, compensate_loose_arbour=False, compact=True, module=1.2, bearing=clock.get_bearing_info(3), minute_hand_thick=2)
motionWorks.calculate_size(35)

pendulum = clock.Pendulum(hand_avoider_inner_d=100, bob_d=80, bob_thick=10)#, handAvoiderHeight=100)

dial_diameter=205
dial = clock.Dial(dial_diameter, clock.DialStyle.FANCY_WATCH_NUMBERS, font="Eurostile Extended #2", font_scale=1.5, font_path="../fonts/Eurostile_Extended_2_Bold.otf",
                  outer_edge_style=clock.DialStyle.LINES_ARC, inner_edge_style=None, dial_width=dial_diameter/6, seconds_style=clock.DialStyle.CONCENTRIC_CIRCLES,
                  bottom_fixing=False, top_fixing=True)
                  # font="Gill Sans Medium", font_scale=0.8, font_path="../fonts/GillSans/Gill Sans Medium.otf",
                  # outer_edge_style=clock.DialStyle.CONCENTRIC_CIRCLES, inner_edge_style=clock.DialStyle.RING, bottom_fixing=True, top_fixing=True)

# dial = clock.Dial(outside_d=180, bottom_fixing=False, top_fixing=True)
plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=9, back_plate_thick=11, pendulum_sticks_out=pendulumSticksOut, name="Wall 28", style=clock.ClockPlateStyle.VERTICAL,
                                 motion_works_above=False, heavy=True, extra_heavy=False, pendulum_fixing=pendulumFixing, pendulum_at_front=False,
                                 back_plate_from_wall=pendulumSticksOut * 2, fixing_screws=clock.MachineScrew(metric_thread=4, countersunk=True),
                                 chain_through_pillar_required=True, dial=dial, centred_second_hand=True, pillars_separate=True, motion_works_angle_deg=-1, top_pillar_holds_dial=True)


hands = clock.Hands(style=clock.HandStyle.FANCY_WATCH, minute_fixing="circle", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(),
                    length=dial.get_hand_length(), thick=motionWorks.minute_hand_slot_height, outline=1.5, outline_same_as_body=False, second_hand_centred=True, chunky=True, outline_on_seconds=0.4,
                    second_length=dial.get_hand_length(clock.HandType.SECOND))

pulley = clock.BearingPulley(diameter=train.powered_wheel.diameter, bearing=clock.get_bearing_info(4), wheel_screws=clock.MachineScrew(2, countersunk=True, length=8))

print("pulley needs screws {} {}mm and {} {}mm".format(pulley.screws, pulley.getTotalThick(), pulley.hook_screws, pulley.getHookTotalThick()))

assembly = clock.Assembly(plates, hands=hands, timeSeconds=30, pulley = pulley, pendulum=pendulum)#weights=[clock.Weight(height=245,diameter=55)]
assembly.get_arbour_rod_lengths()
# show_object(plates.getPlate(back=True))
# show_object(assembly.getClock(with_rods=True, with_key=True))
# show_object(plates.get_winding_key(for_printing=False))

# motion_works_colours=[clock.Colour.GREEN,clock.Colour.GREEN,clock.Colour.YELLOW],
assembly.show_clock(show_object, dial_colours=[clock.Colour.WHITE, clock.Colour.BRASS],
                   motion_works_colours=[clock.Colour.BRASS],
                    hand_colours=[clock.Colour.WHITE, clock.Colour.BLACK, clock.Colour.RED], with_key=True)

# show_object(plates.getDrillTemplate(6))

if outputSTL:
    #
    #
    # train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    dial.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    pulley.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)

    # clock.outputSTLMultithreaded([train, motionWorks,pendulum,dial,plates,hands,pulley,assembly], clockName, clockOutDir)
