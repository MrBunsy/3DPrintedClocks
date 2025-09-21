from clocks import *


outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


# going_train = GoingTrain
# from wall clock 32 just for playing around
# train.set_ratios([[65, 14], [60, 13], [56, 10]])

going_train_ratios = [[65, 14], [60, 13], [56, 10]]
for ratio in going_train_ratios:
    print(ratio[0]/ratio[1])

gear_style = GearStyle.BENT_ARMS5

total_ratio = 1
for pair in going_train_ratios:
    total_ratio*= pair[0]/pair[1]

print(f"total ratio: {total_ratio}")

fly = Fly(length=22+10, end_space=0)

# show_object(fly.get_assembled())

# fan = CentrifugalFan()
#
power = SpringBarrel(style=gear_style, ratchet_screws=MachineScrew(2, grub=True), pawl_angle=math.pi*1.1475, click_angle=-math.pi*0.1475,
                     ratchet_pawl_screwed_from_front=True, key_bearing=PlainBushing(12))
#
# power = SpringBarrel(pawl_angle=-math.pi * 0.8125, ratchet_screws=MachineScrew(2, grub=True), click_angle=-math.pi * 0.2125, base_thick=6,
#                      style=gear_style, wall_thick=8, ratchet_thick=8, spring=SMITHS_EIGHT_DAY_MAINSPRING, key_bearing=BEARING_10x15x4, lid_bearing=BEARING_10x15x4_FLANGED,
#                      barrel_bearing=BEARING_10x15x4, ratchet_pawl_screwed_from_front=True)


train = SlideWhistleTrain(powered_wheel=power, fly=fly)
#
# train.calculate_ratios(loud=True)
#calculated originally
# train.set_ratios([[61, 10], [64, 10]], [[80, 12], [63, 13], [52, 14]])

'''
"The Finest Bird Song of 1890":
https://www.youtube.com/watch?v=tPKFT_t2rL0  

JBakes Machines:
https://www.youtube.com/watch?v=Q-cf2TJ0fR0
https://www.youtube.com/watch?v=iIES3-L0Oxw

things to note: the ratio from cam to bellows pump on "The Finest Bird Song of 1890" is about 25 (judging by counting the rotations on the video and looking at a spot on the barrel to see when it rotated)
Both "The Finest Bird Song of 1890" and JBlakes have the cams directly on the spring barrel. JBlake looks like he's using a much less powerful spring. Can't see inside the antique mechanism.
JBlake uses a cam to pump the bellows, from the same cam wheel. I think. TODO count his ratio between cam and fan

JBlake train aprox:

92:12, 60:7(?), 80:9(?)

~571 from cam to fly


so, new plan: need ~25 from cam to bellows wheel and ~500 from cam to fly.
Undecided on how much to gear down the spring. Maybe try first without an intermediate wheel? i think the real mainspring I'm plannin to use is more powerful
'''

train.set_ratios([[61, 10], [64, 10], [81, 10], [71, 10], [61, 10]], [20,51])
#plan: 2:1 ratio from the intermediate wheel to drive the cam, so the cam is going twice as fast as the intermediate wheel. that will give a ratio of ~25 from cam to bellows wheel
#maybe remove the last arbor as well? then tweak to try and get ~500 from cam to fly (or intermediate to fly? unsure)

#Power ratio: 39.04 cam to fly: 350.811
# train.set_ratios([[61, 10], [64, 10]], [[71, 10], [64, 10], [64, 10]])

train.generate_arbors_dicts([
    {
        #spring barrel
        "module":WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.5),
        "style":GearStyle.BENT_ARMS5
    },
    {
        #intermediate wheel
        "module": WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1.2),
        "pinion_type": PinionType.THIN_LANTERN
    },
    {
        #cam wheel
        "module":0.9,
        "pinion_type": PinionType.THIN_LANTERN,
        "pinion_faces_forwards": True
    },
    {
        #bellows wheel
        "module":0.9,
        #this makes the whole thing bigger but not by much and makes a lot more room for the fan
        "pinion_faces_forwards": True
    },
    {
        #warning wheel
        "module":0.9,
        "pinion_faces_forwards": False,
        "pinion_extension": 24+10

    },
    {
        #fly
        "pinion_faces_forwards": True
    }
])

#
# train.generate_arbors(modules=[WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)], thicknesses=[5, 3], lanterns=[0])
#
plates = SlideWhistlePlates(going_train=train, pillar_style=PillarStyle.SIMPLE_HEX)
print(plates.bearing_positions)
# print(train.trains)

# for arbor in plates.get_arbors_in_situ():
#     show_object(arbor)

# show_object(plates.get_assembled())

assembly = WhistleAssembly(plates)
assembly.show_whistle(show_object)

# show_object(plates.going_train.powered_wheel.get_ratchet_gear_for_arbor())

# show_object(plates.get_spring_ratchet_screws_cutter())
# show_object(plates.get_fixing_screws_cutter())
# print([a.get_type() for a in train.arbors])

# show_object(plates.get_plate())
# show_object(fan.get_assembled())