from clocks import clock

'''
Tony the Clock from Don't Hug Me I'm Scared

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="tony"
clockOutDir="out"
gearStyle=clock.GearStyle.ARCS
pendulumFixing=clock.PendulumFixing.SUSPENSION_SPRING

#for period 1.5
# drop =1.5
# lift =3
# lock=1.5
lift=4
drop=2
lock=2
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL)
# lift=4
# drop=2
# lock=2
# escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

train = clock.GoingTrain(pendulum_length=0.20, fourth_wheel=True, escapement=escapement, maxWeightDrop=1800, usePulley=False, chainAtBack=False, chainWheels=1, hours=7.5*24)#, huygensMaintainingPower=True)

moduleReduction=1#0.85

# train.calculateRatios(max_wheel_teeth=80, min_pinion_teeth=9, wheel_min_teeth=55, pinion_max_teeth=20, max_error=0.1, moduleReduction=moduleReduction, loud=True)
train.setRatios( [[76, 10], [66, 14], [56, 15]])
'''
power wheel ratios [{'ratio': 7.7272727272727275, 'pair': [85, 11], 'error': 0.04742606790799542, 'teeth': 85}, {'ratio': 7.818181818181818, 'pair': [86, 11], 'error': 0.04348302300109541, 'teeth': 86}, {'ratio': 7.75, 'pair': [93, 12], 'error': 0.024698795180722932, 'teeth': 93}, {'ratio': 7.833333333333333, 'pair': [94, 12], 'error': 0.058634538152610105, 'teeth': 94}, {'ratio': 7.769230769230769, 'pair': [101, 13], 'error': 0.00546802594995377, 'teeth': 101}, {'ratio': 7.6923076923076925, 'pair': [100, 13], 'error': 0.08239110287303042, 'teeth': 100}, {'ratio': 7.846153846153846, 'pair': [102, 13], 'error': 0.07145505097312288, 'teeth': 102}, {'ratio': 7.785714285714286, 'pair': [109, 14], 'error': 0.011015490533562655, 'teeth': 109}, {'ratio': 7.714285714285714, 'pair': [108, 14], 'error': 0.06041308089500852, 'teeth': 108}, {'ratio': 7.857142857142857, 'pair': [110, 14], 'error': 0.08244406196213383, 'teeth': 110}, {'ratio': 7.8, 'pair': [117, 15], 'error': 0.02530120481927689, 'teeth': 117}, {'ratio': 7.733333333333333, 'pair': [116, 15], 'error': 0.04136546184738954, 'teeth': 116}, {'ratio': 7.75, 'pair': [124, 16], 'error': 0.024698795180722932, 'teeth': 124}, {'ratio': 7.866666666666666, 'pair': [118, 15], 'error': 0.09196787148594332, 'teeth': 118}, {'ratio': 7.8125, 'pair': [125, 16], 'error': 0.03780120481927707, 'teeth': 125}, {'ratio': 7.6875, 'pair': [123, 16], 'error': 0.08719879518072293, 'teeth': 123}, {'ratio': 7.764705882352941, 'pair': [132, 17], 'error': 0.009992912827781808, 'teeth': 132}, {'ratio': 7.705882352941177, 'pair': [131, 17], 'error': 0.0688164422395463, 'teeth': 131}, {'ratio': 7.823529411764706, 'pair': [133, 17], 'error': 0.04883061658398269, 'teeth': 133}, {'ratio': 7.777777777777778, 'pair': [140, 18], 'error': 0.003078982597054747, 'teeth': 140}, {'ratio': 7.722222222222222, 'pair': [139, 18], 'error': 0.05247657295850061, 'teeth': 139}, {'ratio': 7.833333333333333, 'pair': [141, 18], 'error': 0.058634538152610105, 'teeth': 141}, {'ratio': 7.7894736842105265, 'pair': [148, 19], 'error': 0.014774889029803617, 'teeth': 148}, {'ratio': 7.7368421052631575, 'pair': [147, 19], 'error': 0.03785668991756541, 'teeth': 147}, {'ratio': 7.684210526315789, 'pair': [146, 19], 'error': 0.09048826886493355, 'teeth': 146}, {'ratio': 7.842105263157895, 'pair': [149, 19], 'error': 0.06740646797717176, 'teeth': 149}]
{'time': 3600.0445681246924, 'train': [[76, 10], [66, 14], [56, 15]], 'error': 0.04456812469243232, 'ratio': 133.76, 'teeth': 198, 'weighting': 198.0}
'''

#think this is promising for good compromise of size
# train.genCordWheels(ratchetThick=4, rodMetricThread=4, cordThick=1, cordCoilThick=14, style=gearStyle, useKey=True, preferedDiameter=29, looseOnRod=False, prefer_small=True)
train.genChainWheels2(clock.COUSINS_1_5MM_CHAIN, ratchetThick=4, arbourD=4, looseOnRod=False, prefer_small=True, preferedDiameter=30, fixing_screws=clock.MachineScrew(3, countersunk=True))

pendulumSticksOut=20

train.genGears(module_size=0.9, moduleReduction=moduleReduction, thick=2.4, thicknessReduction=0.9, chainWheelThick=4, pinionThickMultiplier=3, style=gearStyle,
               chainModuleIncrease=1, chainWheelPinionThickMultiplier=2, pendulumFixing=pendulumFixing, stack_away_from_powered_wheel=True)
train.printInfo(weight_kg=3)
train.getArbourWithConventionalNaming(0).printScrewLength()

#although I can make really compact motion works now for the dial to be close, this results in a key that looks too short, so extending just so the key might be more stable
motionWorks = clock.MotionWorks(extra_height=10, style=gearStyle, thick=3, compensateLooseArbour=True, compact=True, inset_at_base=clock.MotionWorks.STANDARD_INSET_DEPTH)
motionWorks.calculateGears(arbourDistance=30)

pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=100,
                          bobD=60, bobThick=10, useNylocForAnchor=False)

dial = clock.Dial(outside_d=200, bottom_fixing=True, top_fixing=True, style=clock.DialStyle.TONY_THE_CLOCK)

plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=9, backPlateThick=11, pendulumSticksOut=pendulumSticksOut, name="Tony", style=clock.ClockPlateStyle.COMPACT,
                                 motionWorksAbove=False, heavy=True, extraHeavy=False, pendulumFixing=pendulumFixing, pendulumAtFront=False,
                                 backPlateFromWall=pendulumSticksOut*2, fixingScrews=clock.MachineScrew(metric_thread=4, countersunk=True),
                                 chainThroughPillarRequired=False, pillars_separate=True, dial=dial)


# hands = clock.Hands(style=clock.HandStyle.SPADE, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
#                     length=plates.dial_diameter*0.45, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=plates.second_hand_mini_dial_d*0.45)
hands = clock.Hands(style=clock.HandStyle.ARROWS,  minuteFixing="square",  minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
                    length=dial.outside_d*0.45, thick=motionWorks.minuteHandSlotHeight, outline=0, outlineSameAsBody=False, chunky=True)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)

pulley = clock.BearingPulley(diameter=train.poweredWheel.diameter, bearing=clock.getBearingInfo(4), wheel_screws=clock.MachineScrew(2, countersunk=True, length=8))
print("pulley needs screws {} {}mm and {} {}mm".format(pulley.screws, pulley.getTotalThick(), pulley.hook_screws, pulley.getHookTotalThick()))


assembly = clock.Assembly(plates, hands=hands, timeSeconds=30, pulley = pulley)#weights=[clock.Weight(height=245,diameter=55)]

# show_object(plates.getPlate(back=True))
show_object(assembly.getClock(with_key=False, with_pendulum=True))

# show_object(plates.getDrillTemplate(6))

if outputSTL:
    #
    #
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    pulley.outputSTLs(clockName, clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)

    # clock.outputSTLMultithreaded([train, motionWorks,pendulum,dial,plates,hands,pulley,assembly], clockName, clockOutDir)