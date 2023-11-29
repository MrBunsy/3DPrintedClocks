from clocks.striking import *

outputSTL = False
if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


'''
Plan is a toy for a two year old, little square box, handle on one side (maybe a knob sticking out of a disc, whole disc sunk into a circle?)
idea: ratchet so it can only turn one way and a simple snail cam
bellows using springs to shut, rather than weights, so they will work whichever way up the box is held

Either cuckoo whistle (two notes) or train whistle (same whistle, but second bellows is larger so note is held for longer?)
'''


class WhistleBoxToy:
    '''
    Plan: pair of whistles at "bottom" of box, with the bellows on the side of the whistle to keep the total size down
    '''
    def __init__(self, size=80, built_in_whistles=True, train=True):
        self.outer_size = size
        self.wall_thick = 5
        self.inner_size = size - self.wall_thick
        #if printing the outer box in PLA then the whistles can be part of the box. The whistles don't work well in PETG
        self.built_in_whistles = built_in_whistles

        if train:
            #TODO different bellows sizes
            self.left_whistle = Whistle(harmonics=2, total_length=self.inner_size, bellows_at_back=True)
            self.right_whistle = Whistle(harmonics=2, total_length=self.inner_size, bellows_at_back=True)
        #TODO else cuckoo

    def get_box(self):
        box = (cq.Workplane("XY").rect(self.outer_size, self.outer_size).extrude(self.wall_thick).faces(">Z").workplane()
               .rect(self.outer_size, self.outer_size).rect(self.inner_size, self.inner_size).extrude(self.inner_size))

        #holes for whistle
        # holes = cq.Workplane("YZ").
        whistle_hole_x = self.inner_size/2 - self.left_whistle.whistle_top_length/2
        whistle_hole_y = self.wall_thick + self.left_whistle.chamber_outside_width/2
        hole_height = self.left_whistle.chamber_outside_width
        hole_width = self.left_whistle.whistle_top_length
        box = box.cut(cq.Workplane("YZ").moveTo(whistle_hole_x, whistle_hole_y).rect(hole_width,hole_height).extrude(self.outer_size*3).translate((-self.outer_size,0,0)))
        
        if self.built_in_whistles:
            box = box.union(self.left_whistle.get_whole_whistle().rotate((0,0,0),(0,0,1),-90)
                            .rotate((0,0,self.left_whistle.chamber_outside_width/2),(0,1,self.left_whistle.chamber_outside_width/2),180)
                            .translate((-self.inner_size/2 + self.left_whistle.chamber_outside_width/2, self.inner_size/2 - self.left_whistle.whistle_top_length/2, self.wall_thick)))

            box = box.union(self.right_whistle.get_whole_whistle().rotate((0, 0, 0), (0, 0, 1), -90)
                            .translate((self.inner_size / 2 - self.right_whistle.chamber_outside_width / 2, self.inner_size / 2 - self.right_whistle.whistle_top_length / 2, self.wall_thick)))
        
        return box


whistle = WhistleBoxToy()

# show_object(whistle.left_whistle.get_whistle_top())
show_object(whistle.get_box())