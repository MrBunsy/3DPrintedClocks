from clocks import *

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

pair_ratios = [[82,10],[71,10]]

pairs = [WheelPinionPair(wheelTeeth=p[0], pinionTeeth=p[1]) for p in pair_ratios]

arbor = Arbor(rod_diameter=4, wheel=pairs[1].wheel, pinion=pairs[0].pinion, style=GearStyle.ROUNDED_ARMS5,
              distance_to_next_arbor=pairs[1].centre_distance, type=ArborType.WHEEL_AND_PINION, pinion_extension=0,
              pinion_thick=6, wheel_thick=2)

single_gear = arbor.get_shape(hole_d=3)

def exportomatic(shape, name):
    BillOfMaterials.PrintedPart(name, shape, svg_options=BillOfMaterials.SVG_OPTS_FRONT_PROJECTION_800).export_SVG("out/pretty_pictures")

# model = BillOfMaterials.PrintedPart(f"single_gear", single_gear, svg_options=BillOfMaterials.SVG_OPTS_FRONT_PROJECTION_800)
#
# model.export_SVG("out/pretty_pictures")

exportomatic(single_gear, "single_gear")

