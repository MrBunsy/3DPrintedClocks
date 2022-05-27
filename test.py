from clocks.power import *
from clocks.escapements import *

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

ratchet = Ratchet()
# frictionCord = CordWheel( diameter=25, capDiameter=50, ratchet=ratchet,useFriction=True, cordThick=4)

# show_object(frictionCord.getAssembled())


# cordwheel = CordWheel( diameter=25, capDiameter=50, ratchet=ratchet, useKey=True, cordThick=2)

cordwheel = CordWheel( diameter=17, capDiameter=50, ratchet=ratchet,cordThick=1)


show_object(cordwheel.getAssembled())
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


# motionWorks=MotionWorks()
#
# show_object(motionWorks.getAssembled())