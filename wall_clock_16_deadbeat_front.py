import clocks.clock as clock

'''
first attempt at a grasshopper. Plan:

Escapment on teh front of the clock (new)
pendulum on the back (new)
hyugens maintaining power using a loop of chain (new)

one day, but since we're using pulleys aiming for a drop of 1.5m

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_16_grasshopper"
clockOutDir="out"
gearStyle = clock.GearStyle.FLOWER


drop =1.5
lift =3
lock=1.5
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4, forceDiameter=True, diameter=100)

train=clock.GoingTrain(pendulum_period=1.25, fourth_wheel=False, escapement=escapement, maxWeightDrop=1200, usePulley=True,
                       chainAtBack=False, chainWheels=0, hours=28, huygensMaintainingPower=True)

train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)

# 61 links/ft 1-day regula chain. copied from clock 04
train.genChainWheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8, holeD=3)

#pendulum is on the back
pendulumSticksOut=20


#trying to reduce plate size as much as possible - works, but means I don't think I have anywhere to attach an extra front plate
# train.genGears(module_size=1,moduleReduction=1.4, thick=3, chainWheelThick=4, useNyloc=False, style=gearStyle, pinionThickMultiplier=2.5, chainWheelPinionThickMultiplier=2.5)
#just big enough module size that the escape wheel can be on the front and not clash with the hands arbour
train.genGears(module_size=1,moduleReduction=0.875, thick=3, chainWheelThick=4, useNyloc=False, style=gearStyle, pinionThickMultiplier=2, chainWheelPinionThickMultiplier=2)

train.printInfo(weight_kg=0.75)

motionWorks = clock.MotionWorks(minuteHandHolderHeight=40, style=gearStyle, compact=True, thick=2)

pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=100, bobD=80, bobThick=10, useNylocForAnchor=False)



dial = clock.Dial(120)


plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=6, pendulumSticksOut=pendulumSticksOut, name="wall clock 16", style="vertical", pendulumAtFront=False,
                                 backPlateFromWall=40, escapementOnFront=True)
pulley = clock.LightweightPulley(diameter=plates.get_diameter_for_pulley())
print("Pulley thick = {}mm".format(pulley.get_total_thickness()))

hands = clock.Hands(style=clock.HandStyle.SPADE, chunky=True, secondLength=25, minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(),
                    length=120, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
assembly = clock.Assembly(plates, hands=hands, timeHours=12, pulley=pulley)

assembly.printInfo()



weight = clock.Weight(height=130, diameter=35)
weight.printInfo()

show_object(assembly.getClock())

if outputSTL:
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    dial.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    weight.outputSTLs(clockName, clockOutDir)
    # bigweight.outputSTLs(clockName+"_big", clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)
    pulley.outputSTLs(clockName, clockOutDir)
