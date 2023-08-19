### ============FULL CLOCK ============
# # train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
train=GoingTrain(pendulum_period=1,fourth_wheel=True,escapement_teeth=30, maxChainDrop=1800, chainAtBack=False,chainWheels=0)#, hours=180)
# train.calculateRatios()
train.set_ratios([[64, 12], [63, 12], [60, 14]])
# train.setChainWheelRatio([74, 11])
# train.genChainWheels(ratchetThick=5)
pendulumSticksOut=25
train.gen_chain_wheels(ratchetThick=5, wire_thick=1.2, width=4.5, inside_length=8.75 - 1.2 * 2, tolerance=0.075)#, wire_thick=0.85, width=3.6, inside_length=6.65-0.85*2, tolerance=0.1)
train.gen_gears(module_size=1, moduleReduction=0.875, thick=3, chainWheelThick=6, useNyloc=False)
motionWorks = MotionWorks(minuteHandHolderHeight=30)
#trying using same bearings and having the pendulum rigidly fixed to the anchor's arbour
pendulum = Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0, useNylocForAnchor=False)


#printed the base in 10, seems much chunkier than needed at the current width. Adjusting to 8 for the front plate
plates = ClockPlates(train, motionWorks, pendulum, plateThick=8, pendulumSticksOut=pendulumSticksOut, name="Wall 05", style="round")

# plate = plates.getPlate(True)
# #
# show_object(plate)
#
# show_object(plates.getPlate(False).translate((0,0,plates.plateDistance + plates.plateThick)))
#
# hands = Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=3, hourfixing_d=5, length=100, thick=4, outline=0, outlineSameAsBody=False)
hands = Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
assembly = Assembly(plates, hands=hands)

show_object(assembly.get_clock())
# #
