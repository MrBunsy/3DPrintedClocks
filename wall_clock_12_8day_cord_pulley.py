from clocks import clock

'''
Eight days, with pulley. 1.2m drop so it should have more power to play with than clock 10

Finishing this design after the success of clocks up to 19. This will take on the lessons from clock 10.

Changes from clock 10 planned:

 - Why not try a second hand without a visible hole?
 - go back to slightly thicker gears to increase robustness (I'm worried about long term life of the clock and seen the escape wheel teeth bend) and make up for friction with longer drop

 - Pendulum at back
 - Direct pendulum arbour - no means of adjusting beat beyond clock angle on the wall and bending pendulum (should make it harder to knock out of beat even if it's slightly harder to set up to begin)
 - dial

Originally decided to try out the new short pendulum since it worked well on clock 11, so I think I can get away with having the pendulum really close to the plates as it'll never reach the weight

Undecided about centred seconds hand.

TODO:

little bridge peice to mount part of motion works directly over third wheel arbour DONE
rounded square minute hand holder? - thinking of giving standalone cannon pinion pinion something to make it easy to grip
curved gear style - new mechanism to know hwich way is clockwise from the front DONE
second wall fixing DONE
front plate printed front-side on the textures sheet DONE
back plate text alignment to avoid wall standoff (bodged)

'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_12b"
clockOutDir="out"
gearStyle=clock.GearStyle.CURVES
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
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4, style=clock.AnchorStyle.CURVED_MATCHING_WHEEL)

train = clock.GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, maxWeightDrop=1400, usePulley=True, chainAtBack=False, chainWheels=1, hours=7.25*24)#, huygensMaintainingPower=True)

moduleReduction=0.85

train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, moduleReduction=moduleReduction)
# train.setChainWheelRatio([93, 10])

#original test
# train.genCordWheels(ratchetThick=4, rodMetricThread=4, cordThick=1, cordCoilThick=18, style=gearStyle, useKey=True, preferedDiameter=42.5, looseOnRod=False)
#think this is promising for good compromise of size
train.genCordWheels(ratchetThick=4, rodMetricThread=4, cordThick=1, cordCoilThick=14, style=gearStyle, useKey=True, preferedDiameter=29, looseOnRod=False, prefer_small=True)
#the 1.2mm 47links/ft regula chain
# train.genChainWheels(ratchetThick=5, wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075)

#override default until it calculates an ideally sized wheel
# train.calculatePoweredWheelRatios(wheel_max=100)

#for pulley
# train.genRopeWheels(ratchetThick = 4, arbour_d=4, ropeThick=2.2, wallThick=2, preferedDiameter=40,o_ring_diameter=2)
# train.genRopeWheels(ratchetThick = 4, arbour_d=4, ropeThick=2.2, wallThick=2, preferedDiameter=35,o_ring_diameter=2, prefer_small=True)



pendulumSticksOut=20

train.genGears(module_size=1, moduleReduction=moduleReduction, thick=2.4, thicknessReduction=0.9, chainWheelThick=4, pinionThickMultiplier=3, style=gearStyle,
               chainModuleIncrease=1, chainWheelPinionThickMultiplier=2, pendulumFixing=pendulumFixing)
train.printInfo(weight_kg=3.5)
train.getArbourWithConventionalNaming(0).printScrewLength()

cordwheel = train.getArbourWithConventionalNaming(0)

# show_object(cordwheel.poweredWheel.getAssembled())
# show_object(cordwheel.poweredWheel.getSegment(front=False))
#
motionWorks = clock.MotionWorks(extra_height=0, style=gearStyle, thick=3, compensateLooseArbour=False, bearing=clock.getBearingInfo(3), compact=True, module=1)

pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=100,
                          bobD=80, bobThick=10, useNylocForAnchor=False)#, handAvoiderHeight=100)

dial = clock.Dial(120)

# plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=9, backPlateThick=11, pendulumSticksOut=pendulumSticksOut, name="Wall 12", style="vertical",
#                                  motionWorksAbove=False, heavy=True, extraHeavy=True, pendulumFixing=pendulumFixing, pendulumAtFront=False,
#                                  backPlateFromWall=pendulumSticksOut*2, fixingScrews=clock.MachineScrew(metric_thread=3, countersunk=True, length=40),
#                                  chainThroughPillar=False, dial_diameter=250, second_hand_mini_dial_d=65)#, centred_second_hand=True

'''
Ideas:

side arms for the dial, then it can be smaller and not overlap with the key
use a rounded square shape for the minute hand, then the minute hand can be used to adjust the time.

or just stick with original plan of arm on top with rounded suqare for hand?
'''

plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=9, backPlateThick=11, pendulumSticksOut=pendulumSticksOut, name="Wall 12", style="vertical",
                                 motionWorksAbove=False, heavy=True, extraHeavy=True, pendulumFixing=pendulumFixing, pendulumAtFront=False,
                                 backPlateFromWall=pendulumSticksOut*2, fixingScrews=clock.MachineScrew(metric_thread=3, countersunk=True, length=40),
                                 chainThroughPillarRequired=True, dial_diameter=180, centred_second_hand=True, dial_bottom_fixing=False, dial_top_fixing=True, pillars_separate=True)


# hands = clock.Hands(style=clock.HandStyle.SPADE, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
#                     length=plates.dial_diameter*0.45, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=plates.second_hand_mini_dial_d*0.45)
hands = clock.Hands(style=clock.HandStyle.BREGUET,  minuteFixing="circle",  minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
                    length=plates.dial_diameter*0.45, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, second_hand_centred=True, chunky=True)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)

# # pulley = clock.Pulley(diameter=train.poweredWheel.diameter, bearing=clock.getBearingInfo(4))
pulley = clock.BearingPulley(diameter=train.poweredWheel.diameter, bearing=clock.getBearingInfo(4), wheel_screws=clock.MachineScrew(2, countersunk=True, length=8))
# #no weight for this clock, as it's going to probably be too heavy to make myself.
# pulley = None

print("pulley needs screws {} {}mm and {} {}mm".format(pulley.screws, pulley.getTotalThick(), pulley.hook_screws, pulley.getHookTotalThick()))

assembly = clock.Assembly(plates, hands=hands, timeSeconds=30, pulley = pulley, showPendulum=True)#weights=[clock.Weight(height=245,diameter=55)]
assembly.get_arbour_rod_lengths()
# show_object(plates.getPlate(back=True))
show_object(assembly.getClock(with_rods=True))

# show_object(plates.getDrillTemplate(6))

if outputSTL:
    #
    #
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    dial.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    pulley.outputSTLs(clockName, clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)

    # clock.outputSTLMultithreaded([train, motionWorks,pendulum,dial,plates,hands,pulley,assembly], clockName, clockOutDir)
