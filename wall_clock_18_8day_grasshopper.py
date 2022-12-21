import random
import os
import clocks.clock as clock
from cadquery import exporters

'''
Experimental eight day grasshopper

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass



clockName="wall_clock_18"
clockOutDir="out"
gearStyle = clock.GearStyle.FLOWER
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOUR

#pre-calculated good values for a 9.75 escaping arc
escapement = clock.GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361)

#TODO fix chain at back, there's some work to do in the arbours (and maybe plates)
train=clock.GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, maxWeightDrop=1250, usePulley=True,
                       chainAtBack=False, chainWheels=1, hours=24*7+6, huygensMaintainingPower=True)

train.calculateRatios(max_wheel_teeth=100, min_pinion_teeth=15, wheel_min_teeth=30, pinion_max_teeth=30, max_error=0.1)

# Trying the thinner 47 LPF regula chain
# train.genChainWheels(ratchetThick=4,  wire_thick=1.05,width=4.4, inside_length=8.4-1.05*2, tolerance=0.075, screwThreadLength=8)

#for the first draft let's stick to a chain I know works, and hope that we're not over its weight limit
# 61 links/ft 1-day regula chain. copied from clock 04
train.genChainWheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8, holeD=3)
# train.genChainWheels(ratchetThick=4,wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075, screwThreadLength=8, holeD=3)


#pendulum is on the back
pendulumSticksOut=20


#trying to reduce plate size as much as possible - works, but means I don't think I have anywhere to attach an extra front plate
# train.genGears(module_size=1,moduleReduction=1.4, thick=3, chainWheelThick=4, useNyloc=False, style=gearStyle, pinionThickMultiplier=2.5, chainWheelPinionThickMultiplier=2.5)
#just big enough module size that the escape wheel can be on the front and not clash with the hands arbour
train.genGears(module_size=1,moduleReduction=1.1, thick=2.4, chainWheelThick=5, useNyloc=False, style=gearStyle, pinionThickMultiplier=2, chainWheelPinionThickMultiplier=2, pendulumFixing=pendulumFixing)
train.printInfo(weight_kg=3)

motionWorks = clock.MotionWorks(extra_height=40, style=gearStyle, compact=True, thick=2)

pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=100, bobD=80, bobThick=10, useNylocForAnchor=False)

#need thicker plates to holder the bigger bearings for the direct arbour pendulum fixing
plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=8, pendulumSticksOut=pendulumSticksOut, name="clk 17", style="vertical", pendulumAtFront=False,
                                 backPlateFromWall=40, escapementOnFront=True, pendulumFixing=pendulumFixing)
pulley = clock.LightweightPulley(diameter=plates.get_diameter_for_pulley())
print("Pulley thick = {}mm".format(pulley.get_total_thickness()))

hands = clock.Hands(style=clock.HandStyle.BREGUET, chunky=True, secondLength=25, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
                    length=120, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=True)
assembly = clock.Assembly(plates, hands=hands, pulley=pulley)

assembly.printInfo()


weight_shell = clock.WeightShell(diameter=38, height=120, twoParts=False, solidBottom=True)

show_object(assembly.getClock())

if outputSTL:

    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    weight_shell.outputSTLs(clockName, clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)
    pulley.outputSTLs(clockName, clockOutDir)
