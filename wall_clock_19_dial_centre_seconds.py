import math

from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.clock import *
from clocks.utility import *
from clocks.leaves import HollyLeaf, Wreath, HollySprig
from clocks.cosmetics import *

'''
Based on wall clock 07. Shortest pendulum that can provide a seconds hand. 30 hour runtime, but chain driven

'''
outputSTL=False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


clockName="wall_clock_19b"
clockOutDir="out"
gearStyle = GearStyle.HONEYCOMB_SMALL
pendulumFixing=PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS


drop =1.5
lift =3
lock=1.5
escapement = AnchorEscapement(drop=drop, lift=lift, teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4, anchorThick=10)
moduleReduction=0.875

#minute wheel ratio so we can use a pinion of 10 teeth to turn the standard motion works arbour and keep the cannon pinion rotating once an hour
train=GoingTrain(pendulum_period=1.5, fourth_wheel=False, escapement=escapement, maxWeightDrop=1200, chainAtBack=False, chainWheels=0, hours=30,
                       usePulley=True, huygensMaintainingPower=True, escapeWheelPinionAtFront=True)#, minuteWheelRatio=10/12)

#lie about module reduction, we don't want smallest possible clock, we want a clock where the 2nd arbour isn't too close to the motion works arbour
train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, moduleReduction=1)

# train.genCordWheels(ratchetThick=5, cordThick=1, cordCoilThick=11, style=gearStyle)
# 61 links/ft 1-day regula chain. copied from clock 04
train.genChainWheels(ratchetThick=4, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075, screwThreadLength=8)
# train.genRopeWheels(ratchetThick=4, ropeThick=2.2, use_steel_tube=False)

pendulumSticksOut=25
# was attemptign to get the second arbour to line up with where I want the arbour for the motion works - but I think this is actually impossible
# to do without the gears overlapping
# ratio_of_teeth = sum(train.trains[0]["train"][0]) / sum(train.trains[0]["train"][1])
#
# first_module_size = 1.25
#
# module_sizes = [first_module_size, first_module_size * ratio_of_teeth]
module_sizes = None

train.genGears(module_size=1.25, moduleReduction=moduleReduction, thick=2, chainWheelThick=3, useNyloc=False, style=gearStyle, pinionThickMultiplier=3, chainWheelPinionThickMultiplier=3,
               pendulumFixing=pendulumFixing, module_sizes=module_sizes)
# train.printInfo(weight_kg=0.75-0.15)
train.printInfo(weight_kg=1-0.25)

#reprinting these after the work to reduce module size back to 1, hoping it removes the jam problem
motionWorks = MotionWorks(extra_height=20, style=gearStyle, bearing=getBearingInfo(3), module=1, compensateLooseArbour=False, compact=True, thick=1.8, pinionThick=8)

pendulum = Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=90, bobD=70, bobThick=10, useNylocForAnchor=False)


dial_diameter = 175


plates = SimpleClockPlates(train, motionWorks, pendulum, plateThick=7, pendulumSticksOut=pendulumSticksOut, name="clock 19",
                           style="vertical", backPlateFromWall=40, pendulumFixing=pendulumFixing, pendulumAtFront=False, centred_second_hand=True, chainThroughPillarRequired=True,
                           dial_diameter=dial_diameter, pillars_separate=True)
pulley_no_pipe = LightweightPulley(diameter=plates.get_diameter_for_pulley(), use_steel_rod=False)

hands = Hands(style=HandStyle.SIMPLE_ROUND, secondLength=40, minuteFixing="circle", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(),
                    hourfixing_d=motionWorks.getHourHandHoleD(), length=plates.dial_diameter/2 - 10, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False,
                    second_hand_centred=True, secondFixing_d=get_diameter_for_die_cutting(3), outline_on_seconds=1, seconds_hand_thick=2.5)

assembly = Assembly(plates, hands=hands, timeSeconds=15, pulley=pulley_no_pipe)

assembly.printInfo()

# weight = Weight(height=130, diameter=35)
# weight.printInfo()

# bigweight = Weight(height=125, diameter=45)
# bigweight.printInfo()
# show_object(train.getArbourWithConventionalNaming(0).getAssembled())
# show_object(train.getArbourWithConventionalNaming(0).poweredWheel.getAssembled())

show_object(assembly.getClock())

if outputSTL:
    train.outputSTLs(clockName,clockOutDir)
    motionWorks.outputSTLs(clockName,clockOutDir)
    pendulum.outputSTLs(clockName, clockOutDir)
    plates.outputSTLs(clockName, clockOutDir)
    hands.outputSTLs(clockName, clockOutDir)
    # weight.outputSTLs(clockName, clockOutDir)
    # bigweight.outputSTLs(clockName+"_big", clockOutDir)
    pulley_no_pipe.outputSTLs(clockName + "_no_pipe", clockOutDir)
    assembly.outputSTLs(clockName, clockOutDir)
