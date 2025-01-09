import clocks as clock

'''
A spherical weight clock with short pendulum

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="ball_clock_09"
clockOutDir="out"



drop =1.5
lift =2
lock=1.5
teeth = 48
toothTipAngle = 4
toothBaseAngle = 3
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, tooth_tip_angle=toothTipAngle, tooth_base_angle=toothBaseAngle)

train=clock.GoingTrain(pendulum_period=0.75, fourth_wheel=True, escapement=escapement, max_weight_drop=1700, chain_at_back=False, powered_wheels=0, runtime_hours=30)
train.calculate_ratios(max_wheel_teeth=80, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, loud=True)
'''
{'time': 3600.0, 'train': [[60, 14], [63, 12], [64, 12]], 'error': 0.0, 'ratio': 120.0, 'teeth': 187, 'weighting': 159.79}
pendulum length: 0.13977573912159377m period: 0.75s
escapement time: 30.0s teeth: 40
'''

#both three and four wheel trains have valid solutions, I think four wheels will end up giving me most flexibility in terms of space

# train=clock.GoingTrain(pendulum_period=0.75,fourth_wheel=False,escapement=escapement, maxChainDrop=1700, chainAtBack=False,chainWheels=0, hours=30)
# train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=20, max_error=0.1,loud=True)
'''
{'time': 3600.0, 'train': [[108, 10], [100, 9]], 'error': 0.0, 'ratio': 120.0, 'teeth': 208, 'weighting': 193.0}
pendulum length: 0.13977573912159377m period: 0.75s
escapement time: 30.0s teeth: 40
'''

train.gen_cord_wheels(ratchet_thick=5, cord_thick=2, cord_coil_thick=11)

train.print_info()

pendulumSticksOut=8

train.gen_gears(module_size=1.25, module_reduction=0.875, thick=3, powered_wheel_thick=6, useNyloc=False)


motionWorks = clock.MotionWorks(extra_height=pendulumSticksOut + 30)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0, hand_avoider_inner_d=75, bob_d=70, bob_thick=10, useNylocForAnchor=False)



dial = clock.Dial(120)


plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=6, pendulum_sticks_out=pendulumSticksOut, name="Wall 07", gear_train_layout=clock.GearTrainLayout.VERTICAL)


hands = clock.Hands(style="simple_rounded", minute_fixing="square", minute_fixing_d1=motionWorks.get_minute_hand_square_size(), hourfixing_d=motionWorks.get_hour_hand_hole_d(), length=100, thick=motionWorks.minute_hand_slot_height, outline=1, outline_same_as_body=False)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)


#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands, pendulum=pendulum)

weight = clock.Weight(height=100, diameter=35)
weight.printInfo()

bigweight = clock.Weight(height=125, diameter=45)
bigweight.printInfo()

show_object(assembly.get_clock())

if outputSTL:
    train.output_STLs(clockName, clockOutDir)
    motionWorks.output_STLs(clockName,clockOutDir)
    pendulum.output_STLs(clockName, clockOutDir)
    dial.output_STLs(clockName, clockOutDir)
    plates.output_STLs(clockName, clockOutDir)
    hands.output_STLs(clockName, clockOutDir)
    weight.output_STLs(clockName, clockOutDir)
    bigweight.output_STLs(clockName+"_big", clockOutDir)
    assembly.output_STLs(clockName, clockOutDir)
