from clocks.utility import *
#20mm
# ball_weight_kg = 32.63/1000
#10mm
# ball_weight_kg = 4.08/1000
#15mm
ball_weight_kg = 13.77/1000

#marbles: 20g, 16g, 12g, 11g for 20-15mm diameters
#4.0788g for the 10mm chrome steel balls https://simplybearings.co.uk/shop/p35940/10mm-Diameter-Grade-100-Hardened-52100-Chrome-Steel-Ball-Bearings/product_info.html
ball_weight_kg = 4.1/1000#20/1000#16/1000
time_s=12
height_raised_m=1/100

runtime_s = 24*8*60*60

ball_total_raised_m = height_raised_m * (runtime_s / time_s)
print("ball total raised height: {}m".format(ball_total_raised_m))

weight_kg = 2
drop_m=1

#usual 2kg weight over a metre is ~30uW. Let's assume that an eight day spring is (at minimum) the same.
#so I think we'll need two spring barrels for 30 hours.

power = 2*weight_kg * GRAVITY * drop_m / runtime_s
power_needed = ball_weight_kg * GRAVITY * ball_total_raised_m / (runtime_s)
power_needed_uW = power_needed * math.pow(10, 6)
print("power needed = {}uW. Power provided = {}uW".format(power_needed_uW, power * math.pow(10,6)))