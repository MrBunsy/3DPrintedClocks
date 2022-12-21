import random
import os
import clocks.clock as clock
from cadquery import exporters

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

# random.seed(6)
random.seed(7)

clockName="wall_clock_17_xmas"
clockOutDir="out"
gearStyle = clock.GearStyle.SNOWFLAKE
pendulumFixing=clock.PendulumFixing.DIRECT_ARBOUR

#pre-calculated good values for a 9.75 escaping arc
escapement = clock.GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361, xmas=True)

#TODO fix chain at back, there's some work to do in the arbours (and maybe plates)
train=clock.GoingTrain(pendulum_period=2, fourth_wheel=False, escapement=escapement, maxWeightDrop=1200, usePulley=True,
                       chainAtBack=False, chainWheels=0, hours=28, huygensMaintainingPower=True)

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
train.genGears(module_size=1.1,moduleReduction=1.1, thick=3, chainWheelThick=4, useNyloc=False, style=gearStyle, pinionThickMultiplier=2, chainWheelPinionThickMultiplier=2, pendulumFixing=pendulumFixing)
train.printInfo(weight_kg=0.5)

motionWorks = clock.MotionWorks(extra_height=40, style=gearStyle, compact=True, thick=2)

pendulum = clock.Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=100, bobD=80, bobThick=10, useNylocForAnchor=False)

#need thicker plates to holder the bigger bearings for the direct arbour pendulum fixing
plates = clock.SimpleClockPlates(train, motionWorks, pendulum, plateThick=8, pendulumSticksOut=pendulumSticksOut, name="clk 17", style="vertical", pendulumAtFront=False,
                                 backPlateFromWall=40, escapementOnFront=True, pendulumFixing=pendulumFixing, pendulumFixingBearing = clock.getBearingInfo(10))
pulley = clock.LightweightPulley(diameter=plates.get_diameter_for_pulley())
print("Pulley thick = {}mm".format(pulley.get_total_thickness()))

pulley_no_pipe = clock.LightweightPulley(diameter=plates.get_diameter_for_pulley(), use_steel_rod=False)

hands = clock.Hands(style=clock.HandStyle.XMAS_TREE, chunky=True, secondLength=25, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
                    length=120, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=True)
assembly = clock.Assembly(plates, hands=hands, pulley=pulley)

assembly.printInfo()


weight_shell = clock.WeightShell(diameter=38, height=120, twoParts=False, solidBottom=True)

show_object(assembly.getClock())

leaf_thick=1
pud = clock.ChristmasPudding(thick=leaf_thick, diameter=pendulum.bobR*2, cut_rect_width=pendulum.gapWidth+0.1, cut_rect_height=pendulum.gapHeight+0.1)

pretty_bob = clock.ItemWithCosmetics(pendulum.getBob(hollow=True), name="bob_pud", background_colour="brown", cosmetics=pud.get_cosmetics(), colour_thick_overrides={"green":leaf_thick})

wreath = clock.Wreath(diameter=pendulum.handAvoiderInnerD, thick=leaf_thick)
cosmetics={"green": wreath.get_leaves(),
           "red": wreath.get_berries()}

pretty_hand_avoider = clock.ItemWithCosmetics(shape = pendulum.getHandAvoider(), name="hand_avoider", background_colour="brown", cosmetics=cosmetics, colour_thick_overrides={"green":leaf_thick})

if outputSTL:

    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    weight_shell.outputSTLs(clockName, clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)
    pulley.outputSTLs(clockName, clockOutDir)
    pulley_no_pipe.outputSTLs(clockName+"_no_pipe", clockOutDir)

    pretty_bob.output_STLs(clockName, clockOutDir)
    pretty_hand_avoider.output_STLs(clockName, clockOutDir)

    out = os.path.join(clockOutDir, "anchor_white.stl")
    print("Outputting ", out)
    exporters.export(escapement.star_inset.rotate((0, 0, 0), (1, 0, 0), 180).translate((0,0,escapement.getAnchorThick())), out)

    for i in ["_a", "_b", "_c"]:
        train.outputSTLs(clockName+i, clockOutDir)
