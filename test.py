from clocks.cuckoo_bits import *

if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass


# plate = chain_plate()
# rod = pendulum_rod()
# toyrod = pendulum_rod(max_length=150,hook_type="toy")
# fixing = pendulum_bob_fixing()
whistleObj = Whistle()
# whistle = whistleObj.getWholeWhistle()
# whistle_top = whistleObj.getWhistleTop()
whistle_full = whistleObj.getWholeWhistle(False, True)
# bellow_base = whistleObj.getBellowBase()
# bellow_top = whistleObj.getBellowTop()
# whistle_top=whistle.getWhistleTop()
# toyback = cuckoo_back()
# toy_dial = dial()
# toy_dial_brown=dial(black=False)

# num = roman_numerals("VIIIX",10,cq.Workplane("XY"))

# show_object(plate)
# show_object(rod)
# show_object(toyrod)
# show_object(fixing)
# show_object(whistle.getBody())
# show_object(whistle_top)
# show_object(whistle)

show_object(whistle_full)
# show_object(bellow_base)
# show_object(bellow_top)
# show_object(toyback)
# show_object(toy_dial[0])
# show_object(toy_dial[1])
# if len(toy_dial) > 2:
#     show_object(toy_dial[2])
# show_object(num)