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
Repeat of the eight day cord driven clock (clock 06), attempting to reduce plate distance, reduce friction and increase strength
First attempt at using a pulley on the weight to reduce height needed

This is working, but I had to re-do the cord wheel to increase drop rate and thicken the top cap. The ratio and diameter are overridden so I could reprint just that wheel.
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
escapement = clock.AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

train = clock.GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, max_weight_drop=1200, chain_at_back=False, chain_wheels=1, hours=180, use_pulley=True)

moduleReduction=0.875

train.calculate_ratios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, module_reduction=moduleReduction)
# train.calculateRatios()
# train.setRatios([[60, 14], [63, 12], [64, 12]])
# train.setRatios([[64, 12], [63, 12], [60, 14]])
# train.setRatios([[81, 12], [80, 9]])
# train.setRatios([[108, 10], [80, 9]])
# train.setChainWheelRatio([74, 11])

train.set_chain_wheel_ratio([93, 10])

#chain size seems about right, trying reducing tolerance
#the 1.2mm 47links/ft regula chain
# train.genChainWheels(ratchetThick=5, wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075)#, wire_thick=0.85, width=3.6, inside_length=6.65-0.85*2, tolerance=0.1)

#1mm cord retrofit, planning to print just a ring to retrofit the retrofit
train.gen_cord_wheels(ratchetThick=3.5, rodMetricThread=4, cordThick=1, cordCoilThick=8, style=gearStyle, useKey=True, preferedDiameter=39)

#2mm cord retrofit, note this has a very wide range of power so doesn't work reliably towards the end of the week with 3.5kg
#train.genCordWheels(ratchetThick=3.5, rodMetricThread=4, cordThick=2, cordCoilThick=8, style=gearStyle, useKey=True, preferedDiameter=32)

'''
layers of cord: 5, cord per hour: 1.7cm to 1.1cm min diameter: 32.0mm
runtime: 171.9hours using 2.4m of cord/chain for a weight drop of 1200. Chain wheel multiplier: 9.3 ([93, 10])
With a weight of 4.25kg, this results in an average power usage of 80.9μW
Generate gears to get screw information
Cordwheel power varies from 66.5μW to 97.8μW
Ratchet needs M2 (CS) screws of length 7.5mm
Plate distance 28.8
cord hole from wall = 35.3mm

With a weight of 3.5kg, this results in an average power usage of 66.6μW
Generate gears to get screw information
Cordwheel power varies from 54.8μW to 80.5μW

With a weight of 4kg, this results in an average power usage of 76.1μW
Generate gears to get screw information
Cordwheel power varies from 62.6μW to 92.1μW
'''
train.set_chain_wheel_ratio([93, 10])
# train.calculateChainWheelRatios()

train.print_info(weight_kg=3.5)
train.print_info(weight_kg=4)
train.print_info(weight_kg=4.25)

pendulumSticksOut=20

train.gen_gears(module_size=1, moduleReduction=moduleReduction, thick=2, thicknessReduction=0.9, chainWheelThick=4, useNyloc=False, pinionThickMultiplier=3, style=gearStyle, chainModuleIncrease=1, chainWheelPinionThickMultiplier=2)#,ratchetInset=True)#, chainModuleIncrease=1.1)

train.get_arbour_with_conventional_naming(0).print_screw_length()

motionWorks = clock.MotionWorks(extra_height=pendulumSticksOut + 30, style=gearStyle, thick=2, compensateLooseArbour=True)


#trying a thicker anchor and glue rather than nyloc
pendulum = clock.Pendulum(bobD=80, bobThick=10)



dial = clock.Dial(120)

#rear plate super thick mainly just to ensure there's enough space for the weight to not bump into the wall!
plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plate_thick=8, back_plate_thick=15, pendulum_sticks_out=pendulumSticksOut, name="Wall 10", style=clock.ClockPlateStyle.VERTICAL, motion_works_above=True, heavy=True, extra_heavy=True)


hands = clock.Hands(style=clock.HandStyle.SWORD, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=110, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=25)
# hands = clock.Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=60, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False)

# pulley = clock.Pulley(diameter=train.poweredWheel.diameter, bearing=clock.getBearingInfo(4))
pulley = clock.BearingPulley(diameter=26, bearing=clock.get_bearing_info(4))
#no weight for this clock, as it's going to probably be too heavy to make myself.

assembly = clock.Assembly(plates, hands=hands, timeMins=0, timeSeconds=30, pulley = pulley)
assembly.printInfo()
# show_object(plates.getPlate(back=True))
# show_object(assembly.getClock())

assembly.show_clock(show_object, plate_colour=clock.Colour.DARKGREY, motion_works_colours=[clock.Colour.GREEN,clock.Colour.GREEN,clock.Colour.YELLOW])

# show_object(assembly.goingTrain.getArbourWithConventionalNaming(0).get_assembled())
# show_object(assembly.goingTrain.getArbourWithConventionalNaming(0).getShape())
# show_object(assembly.goingTrain.getArbourWithConventionalNaming(0).getExtraRatchet())
# show_object(assembly.goingTrain.getArbourWithConventionalNaming(0).poweredWheel.get_assembled())

# assembly.goingTrain.getArbourWithConventionalNaming(0).poweredWheel.printScrewLength()

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
