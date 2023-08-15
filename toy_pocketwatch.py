from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.clock import *
from clocks.utility import *
from clocks.leaves import HollyLeaf, Wreath, HollySprig
from clocks.cosmetics import *
from clocks.geometry import *
from clocks.cuckoo_bits import roman_numerals, CuckooWhistle
from clocks.viewer import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

class ToyPocketwatch:
    def __init__(self, diameter=50, thick=10, hands=HandStyle.SPADE, dial=DialStyle.SIMPLE_ARABIC):
        self.detail_thick = LAYER_THICK * 2

        self.diameter=diameter
        self.thick = thick

        self.dial_diameter = self.diameter*0.8

        self.hand_thick = 0.4


        self.dial = Dial(outside_d=self.dial_diameter, style=dial, detail_thick = self.detail_thick)
        self.dial.configure_dimensions(support_length=0, support_d=0, outside_d=self.dial_diameter)

        self.hands = Hands(style=hands, length=self.dial.get_hand_length(), outline=0, thick=self.hand_thick)



    def get_dial_detail(self):
        return self.dial.get_main_dial_detail().rotate((0,0,0),(0,1,0),180).translate((0,0, self.thick))

    def get_dial(self):
        return cq.Workplane("XY").circle(self.dial_diameter/2).extrude(self.detail_thick).translate((0,0, self.thick - self.detail_thick)).cut(self.get_dial_detail())

    def get_hands(self):
        hands = self.hands.getAssembled(time_minute=10, time_hour=10, flatten=True, include_seconds=False).translate((0,0,self.thick+self.hand_thick))
        hands = hands.union(cq.Workplane("XY").circle(self.hands.length * 0.05 * 2*1.4).extrude(self.hand_thick).translate((0,0,self.thick)))

        return hands

    def get_body(self):
        body = cq.Workplane("XY").circle(self.diameter/2).extrude(self.thick)

        body = body.fillet(self.thick/3)
        body = body.cut(self.get_dial())
        body = body.cut(self.get_dial_detail())
        body = body.cut(self.get_hands())

        return body

pocketwatch = ToyPocketwatch()

show_object(pocketwatch.get_dial(), options={"color":Colour.WHITE}, name="Dial")
show_object(pocketwatch.get_dial_detail(), options={"color":Colour.BLACK}, name="Numbers")
show_object(pocketwatch.get_hands(), options={"color":Colour.BLACK}, name="Hands")
show_object(pocketwatch.get_body(), options={"color":Colour.BRASS}, name="Body")