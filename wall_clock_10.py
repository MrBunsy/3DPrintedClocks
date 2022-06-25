from clocks import clock

'''
Repeat of the eight day cord driven clock, attempting to reduce plate distance, reduce friction and increase strength
First attempt at using a pulley on the weight to reduce height needed
'''
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

clockName="wall_clock_10"
clockOutDir="out"
gearStyle=clock.GearStyle.SIMPLE5

# drop =1.5
# lift =3
# lock=1.5
lift=4
drop=2
lock=2
escapement = clock.Escapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

train = clock.GoingTrain(pendulum_period=2,fourth_wheel=False,escapement=escapement , maxChainDrop=1750, chainAtBack=False,chainWheels=1, hours=180, max_chain_wheel_d=21)

train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1)
# train.calculateRatios()
# train.setRatios([[60, 14], [63, 12], [64, 12]])
# train.setRatios([[64, 12], [63, 12], [60, 14]])
# train.setRatios([[81, 12], [80, 9]])
# train.setRatios([[108, 10], [80, 9]])
# train.setChainWheelRatio([74, 11])

train.setChainWheelRatio([93, 10])

#chain size seems about right, trying reducing tolerance
#the 1.2mm 47links/ft regula chain
# train.genChainWheels(ratchetThick=5, wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075)#, wire_thick=0.85, width=3.6, inside_length=6.65-0.85*2, tolerance=0.1)

#with drop of 1675
#thickness of 17 works well for using 25mm countersunk screws to hold it together, not being too much space between plates and a not-awful gear ratio
#thickness of 12 was just shy of using 20mm countersunk (I forgot I also shrunk the cap thickness) trying 13.5
#Trying 10mm over drop of 1750mm
train.genCordWheels(ratchetThick=4, rodMetricThread=4, cordThick=2, cordCoilThick=10, style=gearStyle, useKey=True)
'''
with drop of 1.8m and max d of 28:
pendulum length: 0.9939608115313336m period: 2s
escapement time: 60s teeth: 30
[102, 10]
layers of cord: 3, cord per hour: 1.2cm to 0.9cm
runtime: 179.6hours. Chain wheel multiplier: 10.2

with 1675mm and 26mm diameter:
[103, 10]
layers of cord: 3, cord per hour: 1.1cm to 0.9cm
runtime: 180.0hours. Chain wheel multiplier: 10.3

'''
train.setChainWheelRatio([93, 10])
# train.calculateChainWheelRatios()

train.printInfo()

pendulumSticksOut=20

train.genGears(module_size=1,moduleReduction=0.875,  thick=2, thicknessReduction=0.9, chainWheelThick=4, useNyloc=False, pinionThickMultiplier=3, style=gearStyle,chainModuleIncrease=1, chainWheelPinionThickMultiplier=2,ratchetInset=True)#, chainModuleIncrease=1.1)

train.getArbourWithConventionalNaming(0).printScrewLength()

motionWorks = clock.MotionWorks(minuteHandHolderHeight=pendulumSticksOut+30,style=gearStyle, thick=2, compensateLooseArbour=True)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=120, bobD=80, bobThick=10, useNylocForAnchor=False)



dial = clock.Dial(120)

plates = clock.ClockPlates(train, motionWorks, pendulum, plateThick=8, backPlateThick=10, pendulumSticksOut=pendulumSticksOut, name="Wall 10", style="vertical", motionWorksAbove=True, heavy=True, extraHeavy=True, usingPulley=True)


hands = clock.Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=25)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)

# pulley = clock.Pulley(diameter=train.poweredWheel.diameter, bearing=clock.getBearingInfo(4))
pulley = clock.Pulley(diameter=26, bearing=clock.getBearingInfo(4), screwMetricSize=2, screwsCountersunk=False)
#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands, timeMins=0, timeSeconds=30, pulley = pulley)


show_object(assembly.getClock())

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
