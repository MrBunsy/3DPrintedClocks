from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.plates import *
from clocks.utility import *
from clocks.leaves import HollyLeaf, Wreath, HollySprig
from clocks.cosmetics import *
from clocks.geometry import *
from clocks.cuckoo_bits import roman_numerals, CuckooWhistle
# from clocks.viewer import *

from clocks.cq_gears import BevelGear, BevelGearPair, CrownGearPair

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


# pendulum = Pendulum(bob_d=120, bob_text=["Paul","34"], font=[SANS_GILL_FONT, FANCY_WATCH_FONT])

pendulum = Pendulum()
#
show_object(pendulum.get_bob_assembled())
#
# holder = ColletFixingPendulumWithBeatSetting(6)
#
# show_object(holder.get_assembled())

# pendulum = FancyPendulum(bob_d=40)#, lid_fixing_screws=MachineScrew(2, countersunk=True, length=10))
#
# # show_object(pendulum.get_bob_assembled(hollow=True))
# #
# show_object(pendulum.get_bob())
# #
# show_object(pendulum.get_bob_lid())
