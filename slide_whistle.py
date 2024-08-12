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

# print(train.trains)

show_object(fan.get_assembled())