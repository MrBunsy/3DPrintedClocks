from .utility import *
import cadquery as cq
import os
from cadquery import exporters


class ItemWithCosmetics:
    def __init__(self, shape, name, background_colour,cosmetics, offset = None, colour_thick=LAYER_THICK*2):
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

        self.generate_shapes()

    def generate_shapes(self):
        total_shape = self.shape
        self.final_shapes = {}
        for colour in self.cosmetics:
            cosmetic = self.cosmetics[colour].translate(self.offset)
            total_shape = total_shape.add(cosmetic)
            thin = cosmetic.intersect(cq.Workplane("XY").rect(1000000, 1000000).extrude(self.colour_thick))
            self.final_shapes[colour] = thin

        colours = self.cosmetics.keys()
        if self.background_colour not in self.final_shapes:
            # the background colour is not included in the thin shapes on the front
            background_shape = total_shape
            for colour in self.final_shapes:
                background_shape = background_shape.cut(self.final_shapes[colour])

            self.final_shapes[self.background_colour] = background_shape
        else:
            raise NotImplementedError("TODO: background colour part of one of the cosmetics")

    def get_models(self):
        return [self.final_shapes[colour] for colour in self.final_shapes]

    def output_STLs(self, name="clock", path="../out"):
        '''

        '''

        for colour in self.final_shapes:

            out = os.path.join(path, "{}_{}_{}.stl".format(name, self.name, colour))
            print("Outputting ", out)
            exporters.export(self.final_shapes[colour], out)

