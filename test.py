from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.clock import *

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


# motionWorks=MotionWorks(compensateLooseArbour=True)
#
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


# pulley = Pulley(diameter=30, vShaped=True)
#
# show_object(pulley.getAssembled())

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

# rack = Rack()
#
# show_object(rack.get2D())

# pulley = Pulley(diameter=27.5, bearing=getBearingInfo(4), screwMetricSize=2, screwsCountersunk=False)
#
# # show_object(pulley.getHalf(False))
# # show_object(pulley.getHalf(True).translate((50,0,0)))
# # show_object(pulley.getHookHalf().translate((0,50,0)))
# show_object(pulley.getAssembled())
#
#
# print(pulley.getTotalThick())

# #the gear wheel from clock 10
# wheelPinionPair = WheelPinionPair(wheelTeeth=93, pinionTeeth=9, module=1)
# # ratchet = Ratchet(power_clockwise=False,thick=4,innerRadius=13,totalD=52)
# cordWheel = CordWheel(diameter=25, rodMetricSize=4, useKey=True)
# #
# poweredArbour = Arbour(wheel=wheelPinionPair.wheel, wheelThick=4, ratchetInset=False, arbourD=6.1, poweredWheel=cordWheel, style=GearStyle.SIMPLE5)
# poweredArbour.setArbourExtensionInfo(rearSide=7,maxR=10,frontSide=123)
# # show_object(poweredArbour.getShape(forPrinting=True).add(poweredArbour.getExtraRatchet().rotate((0,0,0),(1,0,0),180)))
#
# show_object(poweredArbour.getAssembled())


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
#
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


springArbour = SpringArbour(power_clockwise=True)

show_object(springArbour.getArbour())
path="out"
name="spring_arbour_test"
out = os.path.join(path, "{}.stl".format(name))
print("Outputting ", out)
exporters.export(springArbour.getArbour(), out)