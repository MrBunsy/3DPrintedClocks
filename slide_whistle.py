from clocks import *


outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

fan = CentrifugalFan()

power = SpringBarrel()

train = SlideWhistleTrain(power, fan)

train.calculate_ratios(loud=True)

train.generate_arbors(modules=[WheelPinionPair.module_size_for_lantern_pinion_trundle_diameter(1)], thicknesses=[5, 3])

# print(train.trains)

# print([a.get_type() for a in train.arbors])

show_object(fan.get_assembled())