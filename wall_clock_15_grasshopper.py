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
import clocks.clock as clock

'''
second attempt at a grasshopper. Same as teh first attempt (clock 14) but with space to fit hands on properly and less drooping of the escape wheel and frame
A regenerated clock 14 will benefit from the improvements to the plates, but this rejigged the gear train so there's more space

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_15_grasshopper_retrofit"
clockOutDir="out"
gearStyle = clock.GearStyle.HONEYCOMB

pendulumFixing=clock.PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS

need_space = clock.SimpleClockPlates.get_lone_anchor_bearing_holder_thick() + clock.WASHER_THICK_M3

#pre-calculated good values for a 9.75 escaping arc
#also -1 from frame_thick because I've reduced front_anchor_from_plate by one
escapement = clock.GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361, frame_thick=10 - need_space+1, composer_min_distance=need_space)#clock.GrasshopperEscapement.get_harrison_compliant_grasshopper(frame_thick=10-need_space)#(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361)

#TODO fix chain at back, there's some work to do in the arbours (and maybe plates)
train=clock.GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, maxWeightDrop=1200, usePulley=True,
                       chainAtBack=False, chainWheels=0, hours=28, huygensMaintainingPower=True)

train.calculateRatios(max_wheel_teeth=100, min_pinion_teeth=15, wheel_min_teeth=30, pinion_max_teeth=30, max_error=0.1)

# Trying the thinner 47 LPF regula chain
# train.genChainWheels(ratchetThick=4,  wire_thick=1.05,width=4.4, inside_length=8.4-1.05*2, tolerance=0.075, screwThreadLength=8)

#for the first draft let's stick to a chain I know works, and hope that we're not over its weight limit
# 61 links/ft 1-day regula chain. copied from clock 04
train.genChainWheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8, holeD=3)

#pendulum is on the back
pendulumSticksOut=20


#trying to reduce plate size as much as possible - works, but means I don't think I have anywhere to attach an extra front plate
# train.genGears(module_size=1,moduleReduction=1.4, thick=3, chainWheelThick=4, useNyloc=False, style=gearStyle, pinionThickMultiplier=2.5, chainWheelPinionThickMultiplier=2.5)
#just big enough module size that the escape wheel can be on the front and not clash with the hands arbour
train.genGears(module_size=1.1,moduleReduction=1.1, thick=3, chainWheelThick=4, useNyloc=False, style=gearStyle, pinionThickMultiplier=2, chainWheelPinionThickMultiplier=2,pendulumFixing=pendulumFixing)
train.printInfo(weight_kg=1)

motionWorks = clock.MotionWorks(extra_height=40, style=gearStyle, compact=True, thick=2)

pendulum = clock.Pendulum(bobD=80, bobThick=10)

plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=6, pendulumSticksOut=pendulumSticksOut, name="wall clock 15",style=clock.ClockPlateStyle.VERTICAL, pendulumAtFront=False,
                                 backPlateFromWall=40, escapementOnFront=True,pendulumFixing=pendulumFixing, direct_arbour_d=6)
pulley = clock.LightweightPulley(diameter=plates.get_diameter_for_pulley())
print("Pulley thick = {}mm".format(pulley.get_total_thickness()))

hands = clock.Hands(style=clock.HandStyle.SPADE, chunky=True, secondLength=25, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
                    length=120, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
assembly = clock.Assembly(plates, hands=hands, timeHours=12, pulley=pulley)

assembly.printInfo()



weight = clock.Weight(height=130, diameter=50)
weight.printInfo()

# show_object(assembly.getClock())
assembly.show_clock(show_object)

if outputSTL:
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    weight.outputSTLs(clockName, clockOutDir)
    # bigweight.outputSTLs(clockName+"_big", clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)
    pulley.outputSTLs(clockName, clockOutDir)
