from clocks.utility import *
#20mm
# ball_weight_kg = 32.63/1000
#10mm
# ball_weight_kg = 4.08/1000
#15mm
ball_weight_kg = 13.77/1000

#marbles: 20g, 16g, 12g, 11g for 20-15mm diameters
ball_weight_kg = 16/1000
time_s=15
height_raised_m=1/100

runtime_s = 30*60*60

ball_total_raised_m = height_raised_m * (runtime_s / time_s)
print("ball total raised height: {}m".format(ball_total_raised_m))

weight_kg = 1.5
drop_m=1

power = weight_kg * GRAVITY * drop_m / runtime_s
power_needed = ball_weight_kg * GRAVITY * ball_total_raised_m / (runtime_s)
power_needed_uW = power_needed * math.pow(10, 6)
print("power needed = {}uW. Power provided = {}uW".format(power_needed_uW, power * math.pow(10,6)))