from clocks import clock

'''
Experiment to see how large I could make a clock if I used wood for the plates
'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_12"
clockOutDir="out"
gearStyle=clock.GearStyle.FLOWER

drop =1.5
lift =3
lock=1.5
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, tooth_tip_angle=5, tooth_base_angle=4)

# lift=4
# drop=2
# lock=2
# escapement = clock.Escapement(drop=drop, lift=lift, teeth=30, lock=lock, toothTipAngle=5, toothBaseAngle=4)

train = clock.GoingTrain(pendulum_period=1, wheels=2, escapement=escapement, max_weight_drop=1200, use_pulley=True, chain_at_back=False, chain_wheels=1, runtime_hours=7.25 * 24)

moduleReduction=1

train.calculate_ratios(max_wheel_teeth=100000, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction, loud=True)
# train.setChainWheelRatio([93, 10])

train.gen_cord_wheels(ratchet_thick=4, rod_metric_thread=4, cord_thick=1.5, cord_coil_thick=14, style=gearStyle, use_key=True, prefered_diameter=25)
#override default until it calculates an ideally sized wheel
train.calculate_powered_wheel_ratios(wheel_max=100)
#3.5 should be enough, but plan is to bump it up to 4 if it isn't
train.print_info(weight_kg=3.5)
exit()
pendulumSticksOut=30

train.gen_gears(module_size=0.9, module_reduction=moduleReduction, thick=2.4, thickness_reduction=0.9, chain_wheel_thick=4, useNyloc=False, pinion_thick_multiplier=3, style=gearStyle, powered_wheel_module_increase=1, chain_wheel_pinion_thick_multiplier=2)#, chainModuleIncrease=1.1)

train.get_arbour_with_conventional_naming(0).print_screw_length()

motionWorks = clock.MotionWorks(extra_height=pendulumSticksOut + 30, style=gearStyle, thick=2, compensate_loose_arbour=True)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0, hand_avoider_inner_d=50, bob_d=60, bob_thick=10, useNylocForAnchor=False, hand_avoider_height=100)



dial = clock.Dial(120)

#back plate of 15 thick is only just enough for the 3.5kg weight in a shell! it won't be enough for 4kg
plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=8, back_plate_thick=15, pendulum_sticks_out=pendulumSticksOut, name="Wall 12", style=ClockPlateStyle.VERTICAL, motion_works_above=True, heavy=True, extra_heavy=True, usingPulley=True)


hands = clock.Hands(style=clock.HandStyle.SPADE, minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=100, thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False, second_length=25)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)

# pulley = clock.Pulley(diameter=train.poweredWheel.diameter, bearing=clock.getBearingInfo(4))
pulley = clock.BearingPulley(diameter=26, bearing=clock.get_bearing_info(4), screwMetricSize=2, screwsCountersunk=False)
#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands, time_mins=0, time_seconds=30, pulley = pulley, showPendulum=True, pendulum=pendulum)#weights=[clock.Weight(height=245,diameter=55)]

# show_object(plates.getPlate(back=True))
show_object(assembly.get_clock())

if outputSTL:
    #
    #
    train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    dial.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    pulley.output_STLs(clockName, clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)

    # clock.outputSTLMultithreaded([train, motionWorks,pendulum,dial,plates,hands,pulley,assembly], clockName, clockOutDir)
