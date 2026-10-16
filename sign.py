import cadquery as cq

from clocks.utility import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


'''

This doesn't belong in clocks, but it's here until I get around to abstracting out some of the utility classes I've written for cadquery

'''
class Sign:

    def __init__(self, text, font=SANS_GILL_BOLD_FONT, font_height=50, corner_radius=15, padding=12, border_wide=10):
        self.text=text
        self.font_height = font_height
        self.corner_radius = corner_radius
        self.padding = padding
        self.border_wide = border_wide
        self.font = font

        self.base_thick=4

        self.detail_thick = 0.4

        text_shape = self.font.get_text(self.text, self.font_height, thick=self.detail_thick)
        bounding_box = text_shape.val().BoundingBox()
        actual_height = bounding_box.ylen / self.font_height
        new_height = self.font_height / actual_height
        self.text_shape = self.font.get_text(self.text, new_height, thick=self.detail_thick)

        self.text_bounding_box = self.text_shape.val().BoundingBox()

        self.outer_width = self.text_bounding_box.xlen + self.padding*2 + self.border_wide*2
        self.outer_height = self.text_bounding_box.ylen + self.padding * 2 + self.border_wide * 2

        self.screws = CountersunkWoodScrew.get_wood_screw(imperial_size=6)

    def rounded_rectangle(self, width, height, thick, corner_radius):
        rectangle = cq.Workplane("XY").rect(width, height).extrude(thick).edges("|Z").fillet(corner_radius)

        return rectangle

    def get_text(self):

        return self.text_shape

    # def get_border(self):
    #     pass
    #
    # def get_base(self):
    #     pass

    def get_border_and_base(self):
        sign = self.rounded_rectangle(self.outer_width, self.outer_height, self.base_thick + self.detail_thick, self.corner_radius)

        sign = sign.cut(self.get_background(self.detail_thick*2).translate((0,0,self.base_thick-self.detail_thick)))


        return sign

    def get_background(self, thick=-1):
        '''
        Just the two layers behind the text, so we can have just this bit a different colour
        '''
        if thick < 0:
            thick = self.detail_thick

        return  self.rounded_rectangle(self.outer_width - self.border_wide*2, self.outer_height - self.border_wide*2, thick, self.corner_radius - self.border_wide)


    def get_screw_cutter(self):
        x = self.outer_width/2 - self.border_wide - self.padding/2
        y = self.outer_height/2 - self.border_wide - self.padding/2
        positions = [
            (x, y),
            (-x, y),
            (-x, -y),
            (x, -y),
        ]

        screws = cq.Workplane("XY")

        for pos in positions:
            screws = screws.union(self.screws.get_cutter().rotate((0,0,0),(1,0,0),180).translate((0,0,self.base_thick)).translate(pos))

        return screws

    def get_parts_in_situ(self):
        parts = {}
        parts["base"] = sign.get_border_and_base().cut(self.get_screw_cutter())
        parts["background"] = sign.get_background().translate((0, 0, sign.base_thick - sign.detail_thick)).cut(self.get_screw_cutter())
        parts["text"] = sign.get_text().translate((0, 0, sign.base_thick))

        return parts

    def get_bom(self):
        bom = BillOfMaterials("Sign")
        parts = sign.get_parts_in_situ()

        for part in parts:
            bom.add_printed_part(BillOfMaterials.PrintedPart(part, parts[part]))

        return bom


sign = Sign("Billy's Room", font_height=30, corner_radius=10, padding=12, border_wide=8)

# show_object(sign.get_text())
# show_object(sign.rounded_rectangle(100,50,4,5))
# show_object(sign.get_border_and_base(), options={"color": "red"}, name="Sign")
# show_object(sign.get_background().translate((0,0,sign.base_thick-sign.detail_thick)), options={"color": "green"}, name="background")
# show_object(sign.get_text().translate((0,0,sign.base_thick)), options={"color": "red"}, name="text")


# show_object(sign.screws.get_cutter())
# show_object(sign.get_screw_cutter())


parts = sign.get_parts_in_situ()

show_object(parts["base"], options={"color": "red"}, name="Sign")
show_object(parts["background"], options={"color": "green"}, name="background")
show_object(parts["text"], options={"color": "red"}, name="text")
if outputSTL:
    sign.get_bom().export()