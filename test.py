from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.clock import *
from clocks.utility import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

# ratchet = Ratchet()
# # frictionCord = CordWheel( diameter=25, capDiameter=50, ratchet=ratchet,useFriction=True, cordThick=4)
#
# # show_object(frictionCord.getAssembled())
#
#
# # cordwheel = CordWheel( diameter=25, capDiameter=50, ratchet=ratchet, useKey=True, cordThick=2)
#
# cordwheel = CordWheel( diameter=17, capDiameter=50, ratchet=ratchet,cordThick=1)
#
#
# show_object(cordwheel.getAssembled())
# show_object(cordwheel.getKey(withKnob=False))


#
# escapement = Escapement()
#
# show_object(escapement.getAnchor2D())


# chainWheel = ChainWheel()
# ratchet = Ratchet()
# chainWheel.setRatchet(ratchet)
#
# show_object(chainWheel.getAssembled())


# motionWorks=MotionWorks(compensateLooseArbour=True, compact= True)
# show_object(motionWorks.getAssembled())

# ballWheel = BallWheel(ballsAtOnce=15)
#
# print(ballWheel.getPower(rotationsPerHour=1))

#
# print(ballWheel.getTorque())
#
#
# clock6torque = (26/1000) * 1.5 * GRAVITY / 10.3
#
# print("clock 6 torque:{:.3f}".format(clock6torque))
# print("for one ball an hour: {:.2f}".format(clock6torque*12))
# print("for one ball per half hour: {:.2f}".format(clock6torque*6))


# pulley = BearingPulley(diameter=30, vShaped=True)
#
# show_object(pulley.getAssembled())

# bob = LightweightPulley(30)
#
# # show_object(bob.get_wheel())
# show_object(bob.getAssembled())

# weight = Weight(height=130, diameter=50)
# weight.printInfo()

# ratchet = Ratchet(powerAntiClockwise=True,thick=4,innerRadius=21,totalD=70)

#actual rope distance apart: 31.3mm

# ropeWheel = RopeWheel(diameter=20, ratchet_thick=2, screw=MachineScrew(2, countersunk=False), wallThick=2.2)
# show_object(ropeWheel.getAssembled())
#
# chainWheel = ChainWheel(ratchet_thick=3, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075,screwThreadLength=8)
#
# show_object(chainWheel.getAssembled().translate((50,0,0)))

# ropeWheel.outputSTLs("test","out")


# pendulum = Pendulum(Escapement(), 200, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=50, bobD=70, bobThick=10, useNylocForAnchor=False, handAvoiderHeight=100)
#
# # show_object(pendulum.getBob(hollow=True))
# # show_object(pendulum.getPendulumForRod())
#
# show_object(pendulum.getHandAvoider())

# motionWorks = MotionWorks(minuteHandHolderHeight=30 )
#
# hands = Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False, outline=1.2)
#
# show_object(hands.getHand(hour=False))


# motionWorks = MotionWorks(minuteHandHolderHeight=30+30,style=GearStyle.ARCS, thick=2, compensateLooseArbour=True)
# hands = Hands(style=HandStyle.CIRCLES, chunky=True, minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=140, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=25)
#
# show_object(hands.getHand(hour=True).translate((40,0)))
# show_object(hands.getHand(minute=True))
# show_object(hands.getHand(second=True).translate((-40,0)))


# show_object(getHandDemo(assembled=True, chunky=True))
# show_object(getGearDemo())


# show_object(getSpanner())

# weight = Weight(height=150, diameter=35, wallThick=1.8)
# weight.printInfo()
#
# show_object(weight.getLid())
#
# weight.outputSTLs("temp", "out")


# weight = Weight()
# show_object(weight.getWeight())

# screw = MachineScrew()
#
# show_object(screw.getCutter(20, facingUp=False))


# weightShell = WeightShell(50,200)
#
# show_object(weightShell.getShell())
#
# weightShell.outputSTLs("test","out")

# snail = Snail()
# trigger = StrikeTrigger()
# motionWorks=MotionWorks(compensateLooseArbour=True, strikeTrigger=trigger, snail=snail, module=1.2)
# show_object(motionWorks.getAssembled())
# show_object(motionWorks.getHourHolder())

# a = Line((0,0), 0)
#
# print(a.get_perpendicular_direction(False))



# show_object(grasshopper.generate_geometry())

#
# rack = Rack()
# show_object(rack.getRack())

# pulley = Pulley(diameter=27.5, bearing=getBearingInfo(4), screwMetricSize=2, screwsCountersunk=False)
#
# # show_object(pulley.getHalf(False))
# # show_object(pulley.getHalf(True).translate((50,0,0)))
# # show_object(pulley.getHookHalf().translate((0,50,0)))
# show_object(pulley.getAssembled())
#
#
# print(pulley.getTotalThick())

# #clock 12
# wheelPinionPair = WheelPinionPair(wheelTeeth=87, pinionTeeth=9, module=1.0495300312000941)
# # # ratchet = Ratchet(power_clockwise=False,thick=4,innerRadius=13,totalD=52)
# cordWheel = CordWheel(diameter=25, rodMetricSize=4, useKey=True, cordThick=1.5, thick=14)
# # #
# poweredArbour = Arbour(wheel=wheelPinionPair.wheel, wheelThick=4, ratchetInset=False, arbourD=4, poweredWheel=cordWheel, style=GearStyle.SIMPLE5)
# poweredArbour.setArbourExtensionInfo(rearSide=7,maxR=10,frontSide=123)
# # # show_object(poweredArbour.getShape(forPrinting=True).add(poweredArbour.getExtraRatchet().rotate((0,0,0),(1,0,0),180)))
# #
# show_object(poweredArbour.getAssembled())

# show_object(poweredArbour.poweredWheel.getCap(top=True))
# show_object(poweredArbour.poweredWheel.getSegment(front=False))


# poweredArbour.printScrewLength()

# show_object(poweredArbour.getExtraRatchet())

# pair = WheelPinionPair(80,10, module=1)
#
# arbour = Arbour(arbourD=3, wheel=pair.wheel, pinion=pair.pinion, wheelThick=2, pinionThick=6, style=GearStyle.HONEYCOMB)
#
# # show_object(arbour.getShape())
#
# # show_object(getGearDemo(justStyle=GearStyle.HONEYCOMB_SMALL))
# show_object(getGearDemo(justStyle=GearStyle.HONEYCOMB))
# show_object(getGearDemo(justStyle=GearStyle.SPOKES))
# show_object(getGearDemo())
# show_object(getGearDemo(justStyle=GearStyle.FLOWER))
# show_object(getGearDemo(justStyle=GearStyle.ARCS))

#
# # grasshopper = GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.423922627615948, ax_deg=90.28)
# '''
# Balanced escaping arc of 9.7500deg with d of 12.40705997 and ax of 90.26021004
# Diameter of 130.34328818 results in mean torque arm of 9.9396
# '''
# # # grasshopper = GrasshopperEscapement(acceptableError=0.00001)
# # grasshopper = GrasshopperEscapement(acceptableError=0.001, teeth=60, tooth_span=9.5, pendulum_length_m=getPendulumLength(1), mean_torque_arm_length=10, loud_checks=True, skip_failed_checks=True, ax_deg=89)
# # # grasshopper = GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361)
# grasshopper = GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361, xmas=True)
# #
# # # # # # show_object(grasshopper.diagrams[-1])
# # # # # # grasshopper.checkGeometry(loud=True)
# # # # #
# show_object(grasshopper.getAnchor())
# # # # show_object(grasshopper.getEscapementWheel())
# show_object(grasshopper.getAssembled(style=GearStyle.FLOWER))
#
# if outputSTL:
#     grasshopper.outputSTLs("grasshopper", "out")


# shell = WeightShell(diameter=38, height=120, twoParts=False)
#
# show_object(shell.getShell())

if False:
    gear_random = random.seed(4)

    flakes = 9
    combinedFlake = cq.Workplane("XY")
    space = 150 / 2
    for flake in range(flakes):

        r = space
        innerRadius = 10
        if flake > 2:
            r = 50
        if flake > 5:
            r = 30
            innerRadius = 15


        shape = Gear.cutStyle(cq.Workplane("XY").circle(r).extrude(3), outerRadius=r, innerRadius=innerRadius, style=GearStyle.SNOWFLAKE)
        shape = shape.translate(((flake%3)*space*2.5,(floor(flake/3))*space*2.5))
        combinedFlake = combinedFlake.add(shape)
    show_object(combinedFlake)


# holder = cq.Workplane("XY").rect(20,20).extrude(20)
#
# holder = holder.cut(Pendulum.get_pendulum_holder_cutter().translate((0,5,0)))
#
# show_object(holder)
#
motionWorks = MotionWorks(minuteHandHolderHeight=40, style=GearStyle.HONEYCOMB, compact=True, thick=2, module=0.8)
hands = Hands(style=HandStyle.XMAS_TREE, chunky=True, secondLength=40, minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(),
                    length=150, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=True)
#
show_object(hands.getHand(hour=True,second=False, colour="brown"))
show_object(hands.getHand(hour=True,second=False, colour="green"))
# show_object(hands.getHand(hour=True,second=False, colour="red"))
show_object(hands.getHand(hour=True, second=False, generate_outline=True))
# # show_object(hands.getHand(hour=True,second=False).rotate((0,0,0),(0,0,1),90))
#
# show_object(hands.getHand(hour=False,second=True, outline=True).translate((50,0,0)))
# show_object(hands.getHand(hour=False).translate((50,0,0)))

# show_object(cq.Workplane("XY").circle(10).add(cq.Workplane("XY").text("A", fontsize=10, distance=0.1)))


# path = "out"
# name="test_train"
# out = os.path.join(path, "{}.stl".format(name))
# print("Outputting ", out)
# exporters.export(arbour.getShape(), out)

# r1 = 50
# r2 = 30
# d = 60
# # show_object(cq.Sketch().circle(r1).push([cq.Location(cq.Vector(0,d))]).circle(r2).hull())
# # .located(cq.Location(cq.Vector(0,d)))
#
# show_object(cq.Workplane("XY").sketch()
#     .arc((0,0),1.,0.,360.)
#     .arc((1,10),0.5,0.,360.)
#     # .segment((0.,2),(-1,3.))
#     .hull().finalize().extrude(5))
# dial = Dial(outsideD=200)
#
# show_object(dial.getDial())


# springArbour = SpringArbour(power_clockwise=True)
#
# show_object(springArbour.getArbour())
# path="out"
# name="spring_arbour_test"
# out = os.path.join(path, "{}.stl".format(name))
# print("Outputting ", out)
# exporters.export(springArbour.getArbour(), out)