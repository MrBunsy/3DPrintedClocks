from clocks.power import *
from clocks.escapements import *
from clocks.striking import *

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

# ballWheel = BallWheel(ballsAtOnce=12)
#
# print(ballWheel.getTorque())
#
#
# clock6torque = (26/1000) * 1.5 * GRAVITY / 10.3
#
# print("clock 6 torque:{:.3f}".format(clock6torque))
# print("for one ball an hour: {:.2f}".format(clock6torque*12))
# print("for one ball per half hour: {:.2f}".format(clock6torque*6))


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

#the gear wheel from clock 10
wheelPinionPair = WheelPinionPair(wheelTeeth=93, pinionTeeth=9, module=1)
ratchet = Ratchet(powerAntiClockwise=True,thick=4,innerRadius=13,totalD=52)
cordWheel = CordWheel(ratchet=ratchet,diameter=21,capDiameter=52)

poweredArbour = Arbour(wheel=wheelPinionPair.wheel, wheelThick=4, ratchet=ratchet, ratchetInset=True, arbourD=4, chainWheel=cordWheel, style=GearStyle.SIMPLE5)
poweredArbour.setArbourExtensionInfo(wheelSide=7,maxR=10,pinionSide=123)
show_object(poweredArbour.getShape(forPrinting=True).add(poweredArbour.getExtraRatchet().rotate((0,0,0),(1,0,0),180)))

poweredArbour.printScrewLength()

# show_object(poweredArbour.getExtraRatchet())