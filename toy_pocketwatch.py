from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.plates import *
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
    def __init__(self, diameter=50, thick=10, hands=HandStyle.SPADE, dial=DialStyle.ARABIC_NUMBERS):
        self.detail_thick = LAYER_THICK * 2

        self.diameter=diameter
        self.thick = thick

        self.dial_diameter = self.diameter*0.8

        self.hand_thick = self.detail_thick


        self.dial = Dial(outside_d=self.dial_diameter, style=dial, detail_thick = self.detail_thick)
        self.dial.configure_dimensions(support_length=0, support_d=0, outside_d=self.dial_diameter)
        self.dial.dial_width = self.dial_diameter * 0.15

        self.hands = Hands(style=hands, length=self.dial.get_hand_length(), outline=0, thick=self.hand_thick)

        self.hands_shape = self.gen_hands()
        self.dial_detail_shape = self.gen_dial_detail().cut(self.hands_shape)
        self.dial_shape = self.gen_dial().cut(self.dial_detail_shape).cut(self.hands_shape)
        self.body_shape = self.gen_body().cut(self.dial_shape).cut(self.dial_detail_shape).cut(self.hands_shape)

    def get_dial_detail(self):
        return self.dial_detail_shape

    def gen_dial_detail(self):
        return self.dial.get_main_dial_detail().rotate((0,0,0),(0,1,0),180).translate((0,0, self.thick))

    def get_dial(self):
        return self.dial_shape

    def gen_dial(self):
        return cq.Workplane("XY").circle(self.dial_diameter/2).extrude(self.detail_thick).translate((0,0, self.thick - self.detail_thick))

    def get_hands(self):
        return self.hands_shape

    def gen_hands(self):
        hands = self.hands.get_assembled(time_minute=10, time_hour=10, flatten=True, include_seconds=False).translate((0,0,self.thick))
        hands = hands.union(cq.Workplane("XY").circle(self.hands.length * 0.05 * 2*1.4).extrude(self.hand_thick).translate((0,0,self.thick-self.hand_thick)))

        return hands

    def get_body(self):
        return self.body_shape

    def gen_body(self):
        body = cq.Workplane("XY").circle(self.diameter/2).extrude(self.thick)

        #looks great, not sure it'll print wel
        # body = body.fillet(self.thick/3)
        body = body.fillet(self.thick / 4)

        hole_d = 3

        crown_base_wide = self.diameter*0.15
        crown_top_wide = crown_base_wide*1.5
        crown_tall = crown_top_wide*0.8
        crown_taper = crown_tall*0.25

        crown = cq.Workplane("XY").moveTo(-crown_base_wide/2, 0).lineTo(-crown_base_wide/2, self.diameter/2).lineTo(-crown_top_wide/2, self.diameter/2 + crown_taper)\
            .line(0, crown_tall-crown_taper).radiusArc((crown_top_wide/2,self.diameter/2 + crown_tall), self.diameter/2).line(0, -(crown_tall - crown_taper)).lineTo(crown_base_wide/2, self.diameter/2).lineTo(crown_base_wide/2, 0)\
            .close().extrude(self.thick)

        # crown = crown.cut(cq.Workplane("YZ").moveTo(self.diameter/2 + crown_taper + (crown_tall - crown_taper)/2, self.thick/2).circle(hole_d/2).)
        crown = crown.faces(">X").workplane().moveTo(self.diameter/2 + crown_taper + (crown_tall - crown_taper)/2, self.thick/2).circle(hole_d/2).cutThruAll()

        body = body.union(crown)

        return body

    def output_STLs(self, name="toy_pocketwatch", path="out"):
        out = os.path.join(path, "{}_body.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_body(), out, tolerance=0.01, angularTolerance=0.05)

        out = os.path.join(path, "{}_hands.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_hands(), out)

        out = os.path.join(path, "{}_dial.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_dial(), out)

        out = os.path.join(path, "{}_dial_detail.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_dial_detail(), out)

pocketwatch = ToyPocketwatch()

show_object(pocketwatch.get_dial(), options={"color":Colour.WHITE}, name="Dial")
show_object(pocketwatch.get_dial_detail(), options={"color":Colour.BLACK}, name="Numbers")
show_object(pocketwatch.get_hands(), options={"color":Colour.BLACK}, name="Hands")
show_object(pocketwatch.get_body(), options={"color":Colour.BRASS}, name="Body")

if outputSTL:
    pocketwatch.output_STLs()