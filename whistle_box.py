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