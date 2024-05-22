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


# whistle = Whistle(text="Evie's Train", harmonics=2, mouthpiece=True, nozzle_size=0.25)
whistle = Whistle(nozzle_size=0.25)

# show_object(whistle.get_whistle_top())
# show_object(whistle.get_body())
show_object(whistle.get_whole_whistle())


export_STL(whistle.get_whole_whistle(), "whistle", "test", "out", tolerance=0.01)