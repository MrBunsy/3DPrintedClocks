from clocks import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


leaf_thick=1
mistletoe_sprig = MistletoeSprig(thick=leaf_thick, leaf_length=30, branch_length=30)

mistletoe = ItemWithCosmetics(cq.Workplane("XY").circle(3).extrude(leaf_thick), "Mistletoe Sprig","lightgreen",  mistletoe_sprig.get_cosmetics())

mistletoe.show(show_object)