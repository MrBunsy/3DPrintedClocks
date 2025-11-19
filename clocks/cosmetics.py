'''
Copyright Luke Wallin 2023

This source describes Open Hardware and is licensed under the CERN-OHL-S v2.

You may redistribute and modify this source and make products using it under
the terms of the CERN-OHL-S v2 or any later version (https://ohwr.org/cern_ohl_s_v2.txt).

This source is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY,
INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A
PARTICULAR PURPOSE. Please see the CERN-OHL-S v2 for applicable conditions.

Source location: https://github.com/MrBunsy/3DPrintedClocks

As per CERN-OHL-S v2 section 4, should you produce hardware based on this
source, You must where practicable maintain the Source Location visible
on the external case of the clock or other products you make using this
source.
'''
from .utility import *
from .leaves import *
import cadquery as cq
import os
from cadquery import exporters

'''
measuring a printout of tony the clock
'''
tony_the_clock={
    "diameter":140,
    "dial_edge_width":11,
    "dial_marker_length":10,
    "dial_marker_width":5,
    "minute_hand_length":51,
    "hand_width":3,
    "arrow_width":11,
    "arrow_length":10,
    "hand_base_r":11/2,
    "eye_diameter":19.5,
    "pupil_diameter":6.5,
    "eye_spacing":38,
    "eyes_from_top":48,
    "eyebrow_width":18,
    "eyebrow_thick":2,
    "eyebrow_sagitta":4,
    "eyebrow_above_eye":6,
    "mouth_width":26,
    "mouth_below_centre":25,
    "bow_tie_width":40,
    "bow_tie_centre_thick":6,
    "bow_tie_centre_width":7.5,
    "bow_tie_height":22,
    "bow_tie_end_thick":5
}

class BowTie:
    def __init__(self, width=50, thick=1, bob_nut_width=-1, bob_nut_height=-1):
        '''
        Loosely styled after tony the clock (not adhering rigidly as I want it to fit on the pendulum bob)
        designed so the bob nut fits in the middle
        '''
        self.width = width
        self.thick = thick
        self.height = self.get_tony_dimension("bow_tie_height")

        self.centre_width = self.get_tony_dimension("bow_tie_centre_width")
        self.centre_height = self.get_tony_dimension("bow_tie_centre_thick")

        if self.centre_height < bob_nut_height:
            self.centre_height = bob_nut_height
        if self.centre_width < bob_nut_width:
            self.centre_width = bob_nut_width

        #for a bow tie on teh pendulum bob
        self.cut_hole = bob_nut_width > 0 and bob_nut_height >0

        self.bob_nut_width =bob_nut_width
        self.bob_nut_height =bob_nut_height


        self.colour_line_thick = self.centre_height/3



    def get_tony_dimension(self, name):
        '''
        Get a dimension for tony the clock, scaled to the current size of the bow tie
        '''
        return self.width * tony_the_clock[name] / tony_the_clock["bow_tie_width"]

    def get_outline(self):

        peaks = 3.5
        points = []

        x_scale = self.width * 0.02
        x_offset = self.width / 2
        y_scale = -self.height / (math.pi * peaks * 2)
        y_offset = self.height/2

        arc_angle = math.atan((self.height/2)/(self.width/2))*2

        num_points = 100

        #sine wave along a circular arc
        for t in np.linspace(0, math.pi * peaks * 2, num=num_points):
            angle = -(arc_angle / (math.pi * peaks * 2)) * t + arc_angle/2
            points.append(polar(angle,(math.sin(t) * x_scale + x_offset)))

        #undecided if I want this join to be smooth or not
        curve_angle_from_90 = math.atan2(points[1][1]-points[0][1], points[1][0] - points[0][0])#-degToRad(10)

        bow = cq.Workplane("XY").moveTo(0, self.centre_height/2).lineTo(self.centre_width/2, self.centre_height/2).spline([points[0]], includeCurrent=True,tangents=[None,polar(curve_angle_from_90,1)])\
            .spline(listOfXYTuple=points).\
            spline(listOfXYTuple=[(self.centre_width/2, -self.centre_height/2)], includeCurrent=True, tangents=[polar(math.pi-curve_angle_from_90,1), None]).lineTo(0, -self.centre_height/2).mirrorY().extrude(self.thick)
        #lineTo(self.width/2, -self.height/2)
        if self.cut_hole:
            bow = bow.faces(">Z").workplane().rect(self.bob_nut_width, self.bob_nut_height).cutThruAll()

        return bow

    def get_red(self):
        ring_thick = self.get_tony_dimension("bow_tie_end_thick")

        red = cq.Workplane("XY").circle(self.width).circle(self.width/2 - ring_thick/6).extrude(self.thick)
        red = red.union(cq.Workplane("XY").circle(self.width/2 - ring_thick/3).circle(self.width/2 - ring_thick/2).extrude(self.thick))

        r = self.centre_height*2
        red = red.union(cq.Workplane("XY").rect(self.centre_width + ring_thick, self.centre_height*2).extrude(self.thick).
                        cut(cq.Workplane("XY").pushPoints([(-self.centre_width/2 - r - ring_thick/6, 0), (self.centre_width/2 + r + ring_thick/6, 0)]).circle(r).extrude(self.thick)))

        return red.intersect(self.get_outline())

    def get_yellow(self):
        return self.get_outline().cut(self.get_red())

class ItemWithCosmetics:
    def __init__(self, shape, name, background_colour,cosmetics, offset = None, colour_thick=LAYER_THICK*2, colour_thick_overrides=None):
        '''
        Take a shape of a useful part of the clock and add the cosmetics to the front for printing with the single extruder multi material technique
        shape is a caqdquery 3d shape
        name for outputted STLs
        background_colour (can be same as something in cosmetics) for what colour anything beyond colour_thick from the print bed should be
        cosmetics expects dict of { 'colour name': shape}
        offset if they should be translated by offset before adding to the main shape
        colour_thick how thick the layers which vary in colour should be

        '''
        self.shape = shape
        self.name = name
        self.background_colour = background_colour
        self.colour_thick = colour_thick
        if offset is None:
            offset = (0,0)
        self.offset = offset
        #dict of colour names to shapes
        self.cosmetics = cosmetics
        self.colour_thick_overrides = colour_thick_overrides
        if self.colour_thick_overrides is None:
            self.colour_thick_overrides = {}

        self.generate_shapes()

    def generate_shapes(self):
        total_shape = self.shape
        self.final_shapes = {}
        for colour in self.cosmetics:
            cosmetic = self.cosmetics[colour].translate(self.offset)
            total_shape = total_shape.union(cosmetic)
            thick = self.colour_thick
            if colour in self.colour_thick_overrides:
                thick = self.colour_thick_overrides[colour]
            thin = cosmetic.intersect(cq.Workplane("XY").rect(1000000, 1000000).extrude(thick))
            self.final_shapes[colour] = thin

        colours = self.cosmetics.keys()
        if self.background_colour not in self.final_shapes:
            # the background colour is not included in the thin shapes on the front
            background_shape = total_shape
            for colour in self.final_shapes:
                background_shape = background_shape.cut(self.final_shapes[colour])

            self.final_shapes[self.background_colour] = background_shape
        else:
            background_shape = total_shape
            for colour in self.final_shapes:
                if colour != self.background_colour:
                    background_shape = background_shape.cut(self.final_shapes[colour])
            self.final_shapes[self.background_colour] = background_shape

    def get_models(self):
        return [self.final_shapes[colour] for colour in self.final_shapes]

    def get_models_by_colour(self):
        return self.final_shapes

    def get_model(self):
        complete_model = cq.Workplane("XY")
        for model in self.get_models():
            complete_model = complete_model.add(model)

        return complete_model

    def show(self, show_object, translation_lambda = None):
        if translation_lambda is None:
            translation_lambda = lambda c : c
        shapes = self.get_models_by_colour()
        for colour in shapes:
            show_object(translation_lambda(shapes[colour]), options={"color": Colour.colour_tidier(colour)}, name=f"Cosmetic {self.name}: {colour}")

    def output_STLs(self, name="clock", path="../out"):
        '''

        '''

        for colour in self.final_shapes:

            out = os.path.join(path, "{}_{}_{}.stl".format(name, self.name, colour))
            print("Outputting ", out)
            exporters.export(self.final_shapes[colour], out)

    def get_BOM(self):
        bom = BillOfMaterials(self.name, "A multicolour part")



        for colour in self.final_shapes:
            bom.add_printed_part(BillOfMaterials.PrintedPart(colour, self.final_shapes[colour]))

        return bom


class ChristmasPudding:
    '''
    Centred at (0,0)
    Note that the brown pudding appears to produce a malformed STL when a rectangle is cut in the centre. It still slices okay
    '''
    def __init__(self, diameter=100, thick=5, cut_rect_width=-1, cut_rect_height=-1):
        self.diameter = diameter
        self.sprig = HollySprig(thick=thick)
        self.thick = thick
        #as this is intended for the bob, cut a hole for the bob nut
        self.cut_rect_width =cut_rect_width
        self.cut_rect_height =cut_rect_height

        self.sprig_offset = (0, self.diameter*0.4)
        self.leaves = self.sprig.get_leaves().translate(self.sprig_offset)
        self.berries = self.sprig.get_berries().translate(self.sprig_offset)

        self.icing = self.gen_icing()





        self.currents = self.gen_currents()
        self.currents = self.currents.cut(self.icing)

        self.pud = cq.Workplane("XY").circle(self.diameter / 2).extrude(self.thick).cut(self.berries).cut(self.leaves)

        self.currents = self.currents.intersect(self.pud)

        self.pud = self.pud.cut(self.icing).cut(self.currents)
        self.icing = self.icing.cut(self.leaves).cut(self.berries)

        if self.cut_rect_height > 0 and self.cut_rect_width > 0:
            rect_hole = cq.Workplane("XY").rect(self.cut_rect_width, self.cut_rect_height).extrude(self.thick)
            self.currents = self.currents.cut(rect_hole)
            self.pud = self.pud.cut(rect_hole)
            self.icing = self.icing.cut(rect_hole)



    def gen_icing(self):
        points = []

        peaks= 3.5

        x_scale = self.diameter/(math.pi * peaks * 2)
        x_offset = - self.diameter/2
        y_scale = self.diameter*0.05
        y_offset = 0

        if self.cut_rect_height > 0 and self.cut_rect_width > 0:
            #tiny offset so we don't touch the rect with the edge of a curve, trying to track down the cause of a malformed STL when cutting a rect
            y_offset = self.cut_rect_height/2 + y_scale + 0.6


        for t in np.linspace(0, math.pi * peaks * 2, num=100):
            points.append((t * x_scale + x_offset, math.sin(t)* y_scale + y_offset))

        ##.radiusArc((-self.diameter/2,0),-self.diameter/2)
        icing = cq.Workplane("XY").spline(listOfXYTuple=points).line(0,self.diameter).line(-self.diameter,0).close().extrude(self.thick)
        icing = icing.intersect( cq.Workplane("XY").circle(self.diameter/2).extrude(self.thick))

        return icing

    def gen_currents(self):
        #I think I want to make this slightly less random so they're more evenly distributed
        currents = cq.Workplane("XY")

        current_diameter = self.diameter*0.03
        current_length= current_diameter

        for current in range(random.randrange(10,20)):
            pos = (random.uniform(-0.5,0.5)*self.diameter, random.uniform(-0.5,0)*self.diameter)
            if get_distance_between_two_points((0, 0), pos) > self.diameter/2 - current_diameter:
                #outside the pud
                continue
            current_angle = random.random()*math.pi*2
            current_end_pos = np.add(pos, polar(current_angle, current_length*random.uniform(0.8,1.2)))

            current = cq.Workplane("XY").sketch().arc((pos[0], pos[1]), current_diameter*random.uniform(0.4,0.6), 0., 360.).arc(np_to_set(current_end_pos), current_diameter * random.uniform(0.4, 0.6), 0., 360.)\
                .hull().finalize().extrude(self.thick)
            currents = currents.add(current)


        return currents

    def get_cosmetics(self):
        cosmetics = {}

        cosmetics["brown"] = self.pud
        cosmetics["black"] = self.currents
        cosmetics["white"] = self.icing
        cosmetics["green"] = self.leaves
        cosmetics["red"] = self.berries


        return cosmetics


def get_star(star_thick=3, star_size = 75):


    star_arm_wide = star_size * 0.2
    secondary_star_arm_length = star_size * 0.3
    secondary_star_arm_wide = star_arm_wide*0.9

    star = cq.Workplane("XY").tag("base").moveTo(-star_size/2,0).lineTo(0, star_arm_wide/2).lineTo(star_size/2, 0).lineTo(0, -star_arm_wide/2).close().extrude(star_thick)
    star = star.workplaneFromTagged("base").moveTo(-star_arm_wide / 2, 0).lineTo(0, star_size / 2).lineTo(star_arm_wide / 2, 0).lineTo(0, -star_size/2).close().extrude(star_thick)

    secondary_top_left = polar(math.pi*3/4,secondary_star_arm_length)
    secondary_top = (0, secondary_star_arm_wide/2)
    star = star.workplaneFromTagged("base").moveTo(secondary_top_left[0], secondary_top_left[1]).lineTo(secondary_top[0], secondary_top[1]).lineTo(-secondary_top_left[0], -secondary_top_left[1])\
        .lineTo(-secondary_top[0], -secondary_top[1]).close().extrude(star_thick)

    star = star.workplaneFromTagged("base").moveTo(-secondary_top_left[0], secondary_top_left[1]).lineTo(-secondary_top[0], secondary_top[1]).lineTo(secondary_top_left[0], -secondary_top_left[1]) \
        .lineTo(secondary_top[0], -secondary_top[1]).close().extrude(star_thick)

    return star


class Plaque:

    def __init__(self, text_lines, width=-1, height=-1, border=False, raised=True, screws = None, thick=0.6, screw_count = 4, font=None, text_thick = 0.3):
        #expect list of strings
        self.text_lines = text_lines
        self.width = width
        self.height = height
        self.border = border
        self.raised = raised
        self.screws = screws
        self.thick = thick
        self.font = font
        if self.font is None:
            self.font = SANS_GILL_BOLD_FONT

        self.text_thick = text_thick

        self.screw_count = screw_count

        if self.screws is None:
            self.screws = MachineScrew(2, countersunk=False, length=6)#

        self.fillet_r = self.screws.get_head_diameter()/2

    def get_screw_positions(self):
        if self.screws.countersunk:
            from_edge = self.screws.get_head_diameter()
        else:
            from_edge = self.screws.get_head_diameter() / 2
        screw_positions = [(-self.width / 2 + from_edge, self.height / 2 - from_edge), (self.width / 2 - from_edge, -self.height / 2 + from_edge)]

        if self.screw_count == 4:
            screw_positions += [(-self.width / 2 + from_edge, -self.height / 2 + from_edge), (self.width / 2 - from_edge, self.height / 2 - from_edge)]
        return screw_positions

    def set_dimensions(self, max_width, max_height):
        '''
        will use the provided height and reduce width if possible
        '''
        self.height = max_height
        self.width = max_width

        text_spaces = self.get_text_spaces()
        max_width = max([text_space.get_text_width() for text_space in text_spaces])

        if self.width > max_width + self.fillet_r * 4:
            self.width = max_width + self.fillet_r * 4

        #TODO reduce height if possible?

    def get_plaque(self):
        plaque = cq.Workplane("XY").rect(self.width, self.height).extrude(self.thick).edges("|Z").fillet(self.fillet_r)

        for pos in self.get_screw_positions():
            plaque = plaque.cut(self.screws.get_cutter(loose=True).rotate((0,0,0), (1,0,0),180).translate((0,0,self.thick)).translate(pos))

        return plaque

    def get_text_spaces(self):
        available_height = self.height - self.fillet_r * 2
        available_width = self.width - self.fillet_r * 4

        text_space_height = 0.9 * available_height / 3

        text_spaces = []
        for y in range(len(self.text_lines)):
            text_space = TextSpace(x=0, y=available_height / 2 - available_height * (0.5 + y) / len(self.text_lines), width=available_width,
                                   height=text_space_height, horizontal=True, font=self.font, inverted=False)
            text_space.set_text(self.text_lines[y])
            text_spaces.append(text_space)

        max_text_size = min([text_space.get_text_max_size() for text_space in text_spaces])

        for space in text_spaces:
            space.set_size(max_text_size)

        return text_spaces

    def get_text(self):

        text_spaces = self.get_text_spaces()


        text = cq.Workplane("XY")

        for text_space in text_spaces:
            text = text.add(text_space.get_text_shape())

        z = self.thick - self.text_thick
        if self.raised:
            z = self.thick
        text = text.translate((0,0,z))

        return text

    def get_assembled(self):
        return self.get_plaque().add(self.get_text())

    def get_BOM(self):
        bom = BillOfMaterials("Plaque", assembly_instructions="Screw to the back of the back plate")
        bom.add_model(self.get_assembled())
        bom.add_printed_parts(self.get_printed_parts())
        bom.add_item(BillOfMaterials.Item(f"{self.screws} {self.screws.length:.0f}mm", purpose="Plaque fixing screws", quantity=len(self.get_screw_positions())))
        return bom

    def get_printed_parts(self):
        return [
            BillOfMaterials.PrintedPart("base", self.get_plaque(), printing_instructions="Print with text as multicolour print"),
            BillOfMaterials.PrintedPart("text", self.get_text(), printing_instructions="Print with base as multicolour print")
        ]

    def output_STLs(self, name="clock", path="../out"):
        export_STL(self.get_plaque(), "plaque_base", clock_name=name, path=path)
        export_STL(self.get_text(), "plaque_text", clock_name=name, path=path)
