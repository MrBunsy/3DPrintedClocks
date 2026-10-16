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

number_plate_dimensions = {
    "width": 520,
    "height":111,
    "font_height":79,
    "fillet_radius": (111-79)/4
}

def get_plate(width=59, text="MW17 BWZ", thick=3):
    ratio = width/number_plate_dimensions["width"]
    height = number_plate_dimensions["height"]*ratio
    font_height = number_plate_dimensions["font_height"]*ratio

    fillet_r = number_plate_dimensions["fillet_radius"]*ratio
    plate = cq.Workplane("XY").rect(width, height).extrude(thick).edges("|Z").fillet(fillet_r)
    text_shape = NUMBER_PLATE_FONT.get_text(text, font_height, thick=0.4)
    bounding_box = text_shape.val().BoundingBox()
    actual_height = bounding_box.ylen/font_height
    new_height = font_height/actual_height
    text_shape = NUMBER_PLATE_FONT.get_text(text, new_height, thick=0.4)
    bounding_box = text_shape.val().BoundingBox()


    return {"plate": plate,
            "text": text_shape.translate((0,0,thick))}


show_object(get_plate()["plate"], options={"color": "yellow" }, name="Plate Backing")
show_object(get_plate()["text"], options={"color": "black" }, name="Plate Text")
