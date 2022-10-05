import clocks.clock as clock

'''
Simple one day clock with shortest pendulum I can manage and first test of the ropewheel

Attempting to reduce plate distance and size of the one day clock

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_11"
clockOutDir="out"
gearStyle=clock.GearStyle.CARTWHEEL

# drop =1
# lift =2.5
# lock=1.5
# escapement = clock.Escapement(drop=drop, lift=lift, teeth=48, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

drop =1.5
lift =3
lock=1.5
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

train=clock.GoingTrain(pendulum_period=1, fourth_wheel=False, escapement=escapement, maxWeightDrop=2000, chainAtBack=False, chainWheels=0, hours=30)

#note, going below a module of 0.85 makes the pinions are bit hard to print - can do it, but I think it's worth sticking with 0.85 as an absolute minimum with a 0.4mm nozzle
moduleReduction=0.9
train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1,moduleReduction=moduleReduction)


# train.genCordWheels(ratchetThick=2.2, cordThick=1, cordCoilThick=6, style=gearStyle)
# train.genChainWheels(ratchetThick=2.5, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075,screwThreadLength=8)
train.genRopeWheels()

train.printInfo()

pendulumSticksOut=8

#module size of 0.85 looks printable without stringing!
train.genGears(module_size=0.85,moduleReduction=moduleReduction, thick=2, thicknessReduction=0.9, chainWheelThick=2, useNyloc=False, ratchetInset=True, pinionThickMultiplier=3, chainWheelPinionThickMultiplier=3, style=gearStyle, ratchetScrews=clock.MachineScrew(2,countersunk=True))

train.getArbourWithConventionalNaming(0).printScrewLength()
motionWorks = clock.MotionWorks(minuteHandHolderHeight=pendulumSticksOut+30, style=gearStyle)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=75, bobD=70, bobThick=10, useNylocForAnchor=False)



dial = clock.Dial(120)


plates = clock.ClockPlates(train, motionWorks, pendulum, plateThick=6, pendulumSticksOut=pendulumSticksOut, name="Wall 11", style="vertical")


# hands = clock.Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=17)

hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False, outline=0.9)

#wall thick of 1.8 appears to work, but feels a bit more brittle than I'd like
weight = clock.Weight(height=150, diameter=35, wallThick=2.25)
weight.printInfo()

counterweight = clock.Weight(height=100, diameter=18, wallThick=1.35, bolt=clock.MachineScrew(2))
counterweight.printInfo()


assembly = clock.Assembly(plates, hands=hands, showPendulum=True, weights=[weight, counterweight])



show_object(assembly.getClock())

if outputSTL:
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    dial.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    weight.outputSTLs(clockName, clockOutDir)
    counterweight.outputSTLs(clockName+"_counter", clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)
