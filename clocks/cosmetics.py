from .utility import *
from .leaves import *
import cadquery as cq
import os
from cadquery import exporters


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
            total_shape = total_shape.add(cosmetic)
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

    def output_STLs(self, name="clock", path="../out"):
        '''

        '''

        for colour in self.final_shapes:

            out = os.path.join(path, "{}_{}_{}.stl".format(name, self.name, colour))
            print("Outputting ", out)
            exporters.export(self.final_shapes[colour], out)

class ChristmasPudding:
    '''
    Centred at (0,0)
    '''
    def __init__(self, diameter=100, thick=5):
        self.diameter = diameter
        self.sprig = HollySprig(thick=thick)
        self.thick = thick

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


    def gen_icing(self):
        points = []

        peaks= 3

        x_scale = self.diameter/(math.pi * peaks * 2)
        x_offset = - self.diameter/2
        y_scale = self.diameter*0.075


        for t in np.linspace(0, math.pi * peaks * 2, num=100):
            points.append((t * x_scale + x_offset, math.sin(t)* y_scale))

        icing = cq.Workplane("XY").spline(listOfXYTuple=points).radiusArc((-self.diameter/2,0),-self.diameter/2).close().extrude(self.thick)

        return icing

    def gen_currents(self):
        currents = cq.Workplane("XY")

        current_diameter = self.diameter*0.03
        current_length= current_diameter

        for current in range(random.randrange(10,20)):
            pos = (random.uniform(-0.5,0.5)*self.diameter, random.uniform(-0.5,0)*self.diameter)
            if distanceBetweenTwoPoints((0,0),pos) > self.diameter/2 - current_diameter:
                #outside the pud
                continue
            current_angle = random.random()*math.pi*2
            current_end_pos = np.add(pos, polar(current_angle, current_length*random.uniform(0.8,1.2)))

            current = cq.Workplane("XY").sketch().arc((pos[0], pos[1]), current_diameter*random.uniform(0.4,0.6), 0., 360.).arc(npToSet(current_end_pos), current_diameter*random.uniform(0.4,0.6), 0., 360.)\
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