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

fly = Fly()

show_object(fly.get_assembled())

# fan = CentrifugalFan()
#
# power = SpringBarrel()
#
# train = SlideWhistleTrain(power, fan)
#
# train.calculate_ratios(loud=True)
#
# train.generate_arbors(modules=[WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)], thicknesses=[5, 3], lanterns=[0])
#
# plates = SlideWhistlePlates(going_train=train)
# print(plates.bearing_positions)
# # print(train.trains)
#
# for arbor in plates.get_arbors_in_situ():
#     show_object(arbor)

# print([a.get_type() for a in train.arbors])

# show_object(fan.get_assembled())