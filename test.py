from clocks.power import *


if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

ratchet = Ratchet()
# frictionCord = CordWheel( diameter=25, capDiameter=50, ratchet=ratchet,useFriction=True, cordThick=4)

# show_object(frictionCord.getAssembled())


cordwheel = CordWheel( diameter=25, capDiameter=50, ratchet=ratchet, useKey=True, cordThick=2)


# show_object(cordwheel.getAssembled())
show_object(cordwheel.getKey(withKnob=False))