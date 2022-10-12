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


clockName="wall_clock_14_grasshopper"
clockOutDir="out"
gearStyle = clock.GearStyle.HONEYCOMB


#pre-calculated good values for a 9.75 escaping arc
escapement = clock.GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361)

train=clock.GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, maxWeightDrop=1500, usePulley=True, chainAtBack=False, chainWheels=0, hours=28)

#, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4
# train.setEscapementDetails(drop=1.5, lift=3, lock=1.5)

train.calculateRatios(max_wheel_teeth=50, min_pinion_teeth=9, wheel_min_teeth=30, pinion_max_teeth=30, max_error=0.1)

# train.genCordWheels(ratchetThick=5, cordThick=1, cordCoilThick=11, style=gearStyle)
# 61 links/ft 1-day regula chain. copied from clock 04
train.genChainWheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8)


#25 should comfortably stick out in front of the motion works
pendulumSticksOut=25

train.genGears(module_size=1.25,moduleReduction=0.875, thick=3, chainWheelThick=4, useNyloc=False, style=gearStyle, pinionThickMultiplier=4, chainWheelPinionThickMultiplier=4)
train.printInfo(weight_kg=0.425)

motionWorks = clock.MotionWorks(minuteHandHolderHeight=pendulumSticksOut+30, style=gearStyle)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=75, bobD=70, bobThick=10, useNylocForAnchor=False)



dial = clock.Dial(120)


plates = clock.ClockPlates(train, motionWorks, pendulum, plateThick=6, pendulumSticksOut=pendulumSticksOut, name="Granny", style="vertical")


hands = clock.Hands(style=clock.HandStyle.CUCKOO, secondLength=40, minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)


#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands)

assembly.printInfo()

weight = clock.Weight(height=130, diameter=35)
weight.printInfo()

# bigweight = clock.Weight(height=125, diameter=45)
# bigweight.printInfo()
# show_object(train.getArbourWithConventionalNaming(0).getAssembled())
# show_object(train.getArbourWithConventionalNaming(0).poweredWheel.getAssembled())

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
