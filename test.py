from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.clock import *
from clocks.utility import *
from clocks.leaves import HollyLeaf, Wreath, HollySprig
from clocks.cosmetics import *
from clocks.geometry import *
from clocks.cuckoo_bits import roman_numerals, CuckooWhistle
from clocks.viewer import *

from clocks.cq_gears import BevelGear, BevelGearPair, CrownGearPair

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

# ratchet = Ratchet()
# # frictionCord = CordWheel( diameter=25, capDiameter=50, ratchet=ratchet,useFriction=True, cordThick=4)
#
# # show_object(frictionCord.getAssembled())
#
#
# # cordwheel = CordWheel( diameter=25, capDiameter=50, ratchet=ratchet, useKey=True, cordThick=2)
#
# cordwheel = CordWheel( diameter=17, capDiameter=50, ratchet=ratchet,cordThick=1)
#
#
# show_object(cordwheel.getAssembled())
# show_object(cordwheel.getKey(withKnob=False))


#
# escapement = Escapement()
#
# show_object(escapement.getAnchor2D())


# chainWheel = ChainWheel()
# ratchet = Ratchet()
# chainWheel.setRatchet(ratchet)
#
# show_object(chainWheel.getAssembled())

# chainWheel = PocketChainWheel2(max_diameter=35, chain=CHAIN_PRODUCTS_1_4MM_CHAIN, ratchet_thick=4, ratchetOuterD=50)
#
# # show_object(chainWheel.get_pocket_cutter())
# # show_object(chainWheel.get_whole_wheel())
# # show_object(chainWheel.getAssembled())
# # show_object(chainWheel.get_top_half())
# show_object(chainWheel.get_bottom_half())

# show_object(chainWheel.get_between_pocket_cutter())

# show_object(chainWheel.getAssembled())

#
# motionWorks=MotionWorks(compensateLooseArbour=True, compact= True, bearing=getBearingInfo(3))
# motionWorks.calculateGears(arbourDistance=30)
# show_object(motionWorks.getAssembled())

# ballWheel = BallWheel(ballsAtOnce=15)
# #
# print(ballWheel.getPower(rotationsPerHour=0.5))

#
# print(ballWheel.getTorque())
#
#
# clock6torque = (26/1000) * 1.5 * GRAVITY / 10.3
#
# print("clock 6 torque:{:.3f}".format(clock6torque))
# print("for one ball an hour: {:.2f}".format(clock6torque*12))
# print("for one ball per half hour: {:.2f}".format(clock6torque*6))


# pulley = BearingPulley(diameter=30, vShaped=True)
#
# show_object(pulley.getAssembled())

# bob = LightweightPulley(30)
#
# # show_object(bob.get_wheel())
# show_object(bob.getAssembled())

# weight = Weight(height=130, diameter=50)
# weight.printInfo()

# ratchet = Ratchet(powerAntiClockwise=True,thick=4,innerRadius=21,totalD=70)

#actual rope distance apart: 31.3mm

# ropeWheel = RopeWheel(diameter=20, ratchet_thick=2, screw=MachineScrew(2, countersunk=False), wallThick=2.2)
# show_object(ropeWheel.getAssembled())
#
# chainWheel = ChainWheel(ratchet_thick=3, wire_thick=0.85, width=3.6, inside_length=6.65 - 0.85 * 2, tolerance=0.075,screwThreadLength=8)
#
# show_object(chainWheel.getAssembled().translate((50,0,0)))

# ropeWheel.outputSTLs("test","out")


# pendulum = Pendulum(Escapement(), 200, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=50, bobD=70, bobThick=10, useNylocForAnchor=False, handAvoiderHeight=100)
#
# # show_object(pendulum.getBob(hollow=True))
# # show_object(pendulum.getPendulumForRod())
#
# show_object(pendulum.getHandAvoider())

# motionWorks = MotionWorks(minuteHandHolderHeight=30 )
#
# hands = Hands(style="cuckoo", minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outlineSameAsBody=False, outline=1.2)
#
# show_object(hands.getHand(hour=False))


# motionWorks = MotionWorks(minuteHandHolderHeight=30+30,style=GearStyle.ARCS, thick=2, compensateLooseArbour=True)
# hands = Hands(style=HandStyle.CIRCLES, chunky=True, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(), length=140, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False, secondLength=25)
#
# show_object(hands.getHand(hour=True).translate((40,0)))
# show_object(hands.getHand(minute=True))
# show_object(hands.getHand(second=True).translate((-40,0)))


# show_object(getHandDemo(assembled=True, chunky=True, justStyle=HandStyle.MOON, outline=1, length=85))
# show_object(getGearDemo(justStyle=GearStyle.DIAMONDS))


# fillet_test = cq.Workplane("XY").rect(50,20).extrude(10).edges(">Z").fillet(2)
#
# show_object(fillet_test)


# pulley = BearingPulley(diameter=29, bearing=getBearingInfo(4))
#
# show_object(pulley.getHalf())

# show_object(Gear.cutStyle(cq.Workplane("XY").circle(100).extrude(3), 100,20, style=GearStyle.DIAMONDS))




# show_object(Gear.cutCurvesStyle(cq.Workplane("XY").circle(120).extrude(5), 100, 20, clockwise=True))

# show_object(getSpanner())

# weight = Weight(height=150, diameter=35, wallThick=1.8)
# weight.printInfo()
#
# show_object(weight.getLid())
#
# weight.outputSTLs("temp", "out")


# weight = Weight()
# show_object(weight.getWeight())

# screw = MachineScrew()
#
# show_object(screw.getCutter(20, facingUp=False))


# weightShell = WeightShell(50,200)
#
# show_object(weightShell.getShell())
#
# weightShell.outputSTLs("test","out")

# snail = Snail()
# trigger = StrikeTrigger()
# motionWorks=MotionWorks(compensateLooseArbour=True, strikeTrigger=trigger, snail=snail, module=1.2)
# show_object(motionWorks.getAssembled())
# show_object(motionWorks.getHourHolder())

# a = Line((0,0), 0)
#
# print(a.get_perpendicular_direction(False))



# show_object(grasshopper.generate_geometry())

#
# rack = Rack()
# show_object(rack.getRack())

# pulley = Pulley(diameter=27.5, bearing=getBearingInfo(4), screwMetricSize=2, screwsCountersunk=False)
#
# # show_object(pulley.getHalf(False))
# # show_object(pulley.getHalf(True).translate((50,0,0)))
# # show_object(pulley.getHookHalf().translate((0,50,0)))
# show_object(pulley.getAssembled())
#
#
# print(pulley.getTotalThick())

# #clock 12
# wheelPinionPair = WheelPinionPair(wheelTeeth=87, pinionTeeth=9, module=1.0495300312000941)
# # # ratchet = Ratchet(power_clockwise=False,thick=4,innerRadius=13,totalD=52)
# cordWheel = CordWheel(diameter=25, rodMetricSize=4, useKey=True, cordThick=1.5, thick=14)
# # #
# poweredArbour = Arbour(wheel=wheelPinionPair.wheel, wheelThick=4, arbourD=4, poweredWheel=cordWheel, style=GearStyle.SIMPLE5)
# poweredArbour.setArbourExtensionInfo(rearSide=7,maxR=10,frontSide=123)
# # # show_object(poweredArbour.getShape(forPrinting=True).add(poweredArbour.getExtraRatchet().rotate((0,0,0),(1,0,0),180)))
# #
# show_object(poweredArbour.getAssembled())

# show_object(poweredArbour.poweredWheel.getCap(top=True))
# show_object(poweredArbour.poweredWheel.getSegment(front=False))


# poweredArbour.printScrewLength()

# show_object(poweredArbour.getExtraRatchet())

# pair = WheelPinionPair(80,10, module=1)
# #
# arbour = Arbour(arbourD=3, wheel=pair.wheel, pinion=pair.pinion, wheelThick=2, pinionThick=6, style=GearStyle.HONEYCOMB, pinionExtension=5, endCapThick=1)
# #
# show_object(arbour.getShape())
#
# # show_object(getGearDemo(justStyle=GearStyle.HONEYCOMB_SMALL))
# show_object(getGearDemo(justStyle=GearStyle.HONEYCOMB))
# show_object(getGearDemo(justStyle=GearStyle.SPOKES))
# show_object(getGearDemo())
# show_object(getGearDemo(justStyle=GearStyle.FLOWER))
# show_object(getGearDemo(justStyle=GearStyle.ARCS))

#
# # grasshopper = GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.423922627615948, ax_deg=90.28)
# grasshopper = GrasshopperEscapement.get_harrison_compliant_grasshopper()
# '''
# Balanced escaping arc of 9.7500deg with d of 12.40705997 and ax of 90.26021004
# Diameter of 130.34328818 results in mean torque arm of 9.9396
# '''
# # # grasshopper = GrasshopperEscapement(acceptableError=0.00001)
# # grasshopper = GrasshopperEscapement(acceptableError=0.001, teeth=60, tooth_span=9.5, pendulum_length_m=getPendulumLength(1), mean_torque_arm_length=10, loud_checks=True, skip_failed_checks=True, ax_deg=89)
# # # grasshopper = GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361)
# grasshopper = GrasshopperEscapement(escaping_arc_deg=9.75, d= 12.40705997, ax_deg=90.26021004, diameter=130.34329361, xmas=True)
# #
# # # # # # show_object(grasshopper.diagrams[-1])
# # # # # # grasshopper.checkGeometry(loud=True)
# # # # #
# show_object(grasshopper.getAnchor())
# # # # show_object(grasshopper.getEscapementWheel())
# show_object(grasshopper.getAssembled(style=GearStyle.CURVES))
#
# if outputSTL:
#     grasshopper.outputSTLs("grasshopper", "out")


# shell = WeightShell(diameter=38, height=120, twoParts=False)
#
# show_object(shell.getShell())

if False:
    gear_random = random.seed(4)

    flakes = 9
    combinedFlake = cq.Workplane("XY")
    space = 150 / 2
    for flake in range(flakes):

        r = space
        innerRadius = 10
        if flake > 2:
            r = 50
        if flake > 5:
            r = 30
            innerRadius = 15


        shape = Gear.cutStyle(cq.Workplane("XY").circle(r).extrude(3), outerRadius=r, innerRadius=innerRadius, style=GearStyle.SNOWFLAKE)
        shape = shape.translate(((flake%3)*space*2.5,(floor(flake/3))*space*2.5))
        combinedFlake = combinedFlake.add(shape)
    show_object(combinedFlake)


# holder = cq.Workplane("XY").rect(20,20).extrude(20)
#
# holder = holder.cut(Pendulum.get_pendulum_holder_cutter().translate((0,5,0)))
#
# show_object(holder)
#
# motionWorks = MotionWorks(extra_height=0, style=GearStyle.SIMPLE5, compact=True, thick=3, module=2, bearing=getBearingInfo(3), compensateLooseArbour=False)
# hands = Hands(style=HandStyle.SIMPLE_ROUND, chunky=True, secondLength=40, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
#                     length=150, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=True)
#
# show_object(hands.getHand())
# # #
# # # hands = Hands(style=HandStyle.SIMPLE_ROUND, chunky=True, secondLength=40, minuteFixing="circle", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
# # #                      length=120, thick=motionWorks.minuteHandSlotHeight, outline=1, second_hand_centred=True)
# # #
# # show_object(motionWorks.getAssembled())
# #
# # # show_object(motionWorks.getCannonPinion())
# # # show_object(motionWorks.getHourHolder())
# #
# show_object(hands.getHand())
#
# show_object(hands.getAssembled())
#
# if outputSTL:
#     motionWorks.outputSTLs(name="test", path="out")

#
# hands = Hands(style=HandStyle.BREGUET, chunky=True, secondLength=40, minuteFixing="square", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(), hourfixing_d=motionWorks.getHourHandHoleD(),
#                     length=120, thick=motionWorks.minuteHandSlotHeight, outline=1)
# #
# show_object(hands.getHand(hour=True,second=False, colour="brown"))
# show_object(hands.getHand(hour=True,second=False, colour="green"))
# show_object(hands.getHand(hour=True,second=False, colour="red"))
# show_object(hands.getHand(hour=True, second=False, generate_outline=True))
#
#
# #
# show_object(hands.getHand(hour=False,second=False, colour="brown").translate((50,0,0)))
# show_object(hands.getHand(hour=False,second=False, colour="green").translate((50,0,0)))
# show_object(hands.getHand(hour=False,second=False, colour="red").translate((50,0,0)))
# show_object(hands.getHand(hour=False, second=False, generate_outline=True).translate((50,0,0)))

# show_object(hands.getHand(hour=True,second=False))#.rotate((0,0,0),(0,0,1),90))
#
# show_object(hands.getHand(hour=False,second=True, generate_outline=True).translate((-50,0,0)))
# show_object(hands.getHand(hour=False).translate((50,0,0)))
#
# show_object(hands.getAssembled())
#
# # holly_leaf = HollyLeaf()
# #
# # show_object(holly_leaf.get_2d())
# random.seed(1)
# # wreath = Wreath(diameter=120, thick=1.6)
# #
# # # show_object(wreath.get_wreath())
# #
# # pend = Pendulum(escapement=None, length=1000, handAvoiderInnerD=120, bobD=80, bobThick=10)
# pend = Pendulum(None, 1000, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=100, bobD=80, bobThick=10, useNylocForAnchor=False)

#
# cosmetics={"green": wreath.get_leaves(),
#            "red": wreath.get_berries()}
#
# pretty_hand_avoider = ItemWithCosmetics(shape = pend.getHandAvoider(), name="hand_avoider", background_colour="brown", cosmetics=cosmetics, colour_thick_overrides={"green":1.6})
#
# for shape in pretty_hand_avoider.get_models():
#     show_object(shape)
#
# if outputSTL:
#     pretty_hand_avoider.output_STLs(name="test", path="out")
#
# holly_sprig = HollySprig()
#
# show_object(holly_sprig.get_leaves())
# show_object(holly_sprig.get_berries())
# pendulum = pend
# leaf_thick = 1.6
# pud = ChristmasPudding(thick=leaf_thick, diameter=pend.bobR*2, cut_rect_width=pendulum.gapWidth, cut_rect_height=pendulum.gapHeight)
# cosmetics = pud.get_cosmetics()
#
# for colour in cosmetics:
#     show_object(cosmetics[colour])
# bob = pend.getBob(hollow=True)
# pretty_bob = ItemWithCosmetics(bob, name="bob", background_colour="brown", cosmetics=pud.get_cosmetics(), colour_thick_overrides={"green":leaf_thick})
#
# if outputSTL:
#     pretty_bob.output_STLs(name="test", path="out")

# points = []
#
# x_scale = 1
# y_scale = 1
#
# for t in np.linspace(0, math.pi*4, num=50):
#     points.append((t*x_scale, math.sin(t*y_scale)))
#
# print(points)
#
# show_object(cq.Workplane("XY").spline(listOfXYTuple=points))

# show_object(cq.Workplane("XY").circle(10).extrude(10))



# show_object(cq.Workplane("XY").circle(10).add(cq.Workplane("XY").text("A", fontsize=10, distance=0.1)))


# cq.Sketch.importDXF("test.dxf")

# show_object(cq.Workplane("XY").sketch().importDXF(filename="test.dxf").finalize().extrude(10))

# thick=2
# text = cq.Workplane("XY").text("bob", 20, LAYER_THICK, cut=False, halign='center', valign='center', kind="bold").rotate((0,0,0), (0,0,1),90).translate((0,0,thick))
# show_object(text)

# path = "out"
# name="test_train"
# out = os.path.join(path, "{}.stl".format(name))
# print("Outputting ", out)
# exporters.export(arbour.getShape(), out)

# screw = MachineScrew(metric_thread=3, length=20)
#
# show_object(screw.get_nut_for_die_cutting())
#
# show_object(screw.get_screw_for_thread_cutting().translate((0,20,0)))
#
#
# if outputSTL:
#     path = "out"
#     name = "test"
#     out = os.path.join(path, "{}_nut.stl".format(name))
#     print("Outputting ", out)
#     exporters.export(screw.get_nut_for_die_cutting(), out)
#
#     out = os.path.join(path, "{}_screw.stl".format(name))
#     print("Outputting ", out)
#     exporters.export(screw.get_screw_for_thread_cutting(), out)

# r1 = 50
# r2 = 30
# d = 60
# # show_object(cq.Sketch().circle(r1).push([cq.Location(cq.Vector(0,d))]).circle(r2).hull())
# # .located(cq.Location(cq.Vector(0,d)))
#
# show_object(cq.Workplane("XY").sketch()
#     .arc((0,0),1.,0.,360.)
#     .arc((1,10),0.5,0.,360.)
#     # .segment((0.,2),(-1,3.))
#     .hull().finalize().extrude(5))
if False:
    dial = Dial(outside_d=200, style=DialStyle.TONY_THE_CLOCK)
    # #
    # show_object(dial.get_assembled(),options={"color":"blue"})
    show_object(dial.get_dial().rotate((0,0,0),(0,1,0),180),options={"color":"blue"})
    show_object(dial.get_tony_face_detail(),options={"color":"black"})
    show_object(dial.get_all_detail(),options={"color":"yellow"})
    show_object(dial.get_extras()["outer_ring"].rotate((0,0,0),(0,1,0),180).translate((0,0,dial.thick)),options={"color":"black"})
    #.rotate((0,0,0),(0,1,0),180)
    show_object(getHandDemo(justStyle=HandStyle.ARROWS, length=200*0.45-10, chunky=True,outline=0, assembled=True, include_seconds=False, time_hour=3, time_min=41).translate((0,0,dial.get_hand_space_z())),options = { "color" : "red"})
    eye,pupil = dial.get_eye()

    for x in [-1, 1]:
        show_object(eye.translate((x * dial.get_tony_dimension("eye_spacing") / 2, dial.outside_d / 2 - dial.get_tony_dimension("eyes_from_top"), -dial.thick - dial.eye_pivot_z)),options={"color":"white"} )
        show_object(pupil.translate((x * dial.get_tony_dimension("eye_spacing") / 2, dial.outside_d / 2 - dial.get_tony_dimension("eyes_from_top"), -dial.thick - dial.eye_pivot_z)), options={"color": "black"})

if False:
    #testing the slots for holding an eyeball
    dial = Dial(outside_d=200, style=DialStyle.TONY_THE_CLOCK)
    test_eye_hole = dial.get_dial().union(dial.get_tony_face_detail()).intersect(cq.Workplane("XY").moveTo(dial.eye_distance_apart/2, dial.eye_y).circle(dial.eye_hole_d*0.75+7).extrude(50))
    show_object(test_eye_hole)
    path="out"
    name="test_eye_hole"
    out = os.path.join(path, "{}.stl".format(name))
    print("Outputting ", out)
    exporters.export(test_eye_hole, out)


# dial = Dial(outside_d=200, style=DialStyle.TONY_THE_CLOCK)
# show_object(dial.get_wire_to_arbor_fixer())

if False:
    lift=4
    drop=2
    lock=2
    escapement = AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4, style=AnchorStyle.CURVED_MATCHING_WHEEL)
    pendulum = Pendulum(escapement, 0.225, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0,handAvoiderInnerD=100,
                              bobD=60, bobThick=10, useNylocForAnchor=False)
    bow_tie = BowTie(width=200*tony_the_clock["bow_tie_width"]/tony_the_clock["diameter"], bob_nut_width=pendulum.gapWidth, bob_nut_height=pendulum.gapHeight)

    # show_object(bow.get_outline())
    # show_object(bow.get_red(),options={"color":"red"} )
    # show_object(bow.get_yellow(),options={"color":"yellow"} )

    cosmetics={"red": bow_tie.get_red(),
               "yellow": bow_tie.get_yellow()}

    pretty_bob = ItemWithCosmetics(shape = pendulum.getBob(), name="bow_tie_bob", background_colour="black", cosmetics=cosmetics)

    show_object(pretty_bob.get_models())

dial = Dial(200, DialStyle.SIMPLE_ARABIC)

show_object(dial.get_dial())

# text = cq.Workplane("XY").moveTo(0, 0).text("Testing", 10, LAYER_THICK, kind="bold")
#
# # cadquery.BoundBox()
# print(text.val().BoundingBox().center)
#
# show_object(text.rotate((0, 0, 0), (0, 1, 0), 180).translate((0,0,LAYER_THICK)))
# show_object(cq.Workplane("XY").rect(10,10).extrude(10).cut(cq.Solid.makeCone(radius1=0, radius2=50, height=50)))

# show_object(eye,options={"color":"white"} )
# show_object(pupil,options={"color":"black"} )

# leaf = MistletoeLeaf()
#
# show_object(leaf.get_2d())

# twig = MistletoeLeafPair(seed=2)
# twig = MistletoeLeafPair()
# show_object(twig.get_branch())
# show_object(twig.get_leaves())

# AnchorEscapement.get_with_45deg_pallets(teeth=30)
# springArbour = SpringArbour(power_clockwise=True)
#
# show_object(springArbour.getArbour())
# path="out"
# name="spring_arbour_test"
# out = os.path.join(path, "{}.stl".format(name))
# print("Outputting ", out)
# exporters.export(springArbour.getArbour(), out)

#, bearing=getBearingInfo(3)
# motionWorks = MotionWorks(extra_height=20, style=GearStyle.CURVES, module=1, compensateLooseArbour=False, compact=True, inset_at_base=TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT)
# motionWorks.calculateGears(35)
# # #
# # hands = Hands(style=HandStyle.BREGUET, secondLength=40, minuteFixing="circle", minuteFixing_d1=motionWorks.getMinuteHandSquareSize(),
# #                     hourfixing_d=motionWorks.getHourHandHoleD(), length=77.5, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False,
# #                     second_hand_centred=True, secondFixing_d=get_diameter_for_die_cutting(3), chunky=True)
# # #
# # #
# # # show_object(hands.getAssembled())
# show_object(motionWorks.getAssembled())
# show_object(hands.getHand(hour=False, minute=False, second=True))


# def shape_func(t):
#
#     angle = t*math.pi*2
#     knobs = 5
#     distance = math.pi*2*knobs
#     print(t)
#     return polar(angle,10+math.sin(t*distance)*3)
#
# show_object(cq.Workplane('XY').parametricCurve(lambda t: shape_func(t)))

# show_object(get_smooth_knob_2d(10,20,7))

# lift=4
# drop=2
# lock=2
#
# y = 0
# for style in AnchorStyle:
#     escapement = AnchorEscapement(drop=drop, lift=lift, teeth=30, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4, style=style)
#     show_object(escapement.getAnchor().translate((0,y)))
#     y+=50


# line = get_stroke_line([(0,0), (20,20), (0,50)], 5, 2)
#
# show_object(line)

# baroque_hands = BaroqueHands(base_r=23/2, total_length=100, thick=3, line_width=2.4)
# #
# # show_object(baroque_hands.hour_hand())
# # show_object(baroque_hands.minute_hand().translate((30,0,0)))
# show_object(baroque_hands.second_hand())

# show_object(getHandDemo(justStyle=HandStyle.BAROQUE, outline=0, assembled=True))


# gear_demo = getGearDemo(justStyle=GearStyle.MOONS)
# show_object(gear_demo)

# show_object(Gear.crescent_moon_2D(20,0.125*7.5))

# exporters.export(gear_demo, "out/test.svg", opt={"width":480,"height":1024, "showAxes":False, "strokeWidth":0.2, "showHidden":False})

# show_object(getHandDemo())

# testfillet = cq.Workplane("XY").rect(100,100).extrude(10).edges(">Z").fillet(1)
# show_object(testfillet)

if False:
    moon = MoonPhaseComplication3D(pinion_teeth_on_hour_wheel=18, module=1, gear_style=GearStyle.CIRCLES)
    motionWorks = MotionWorks(extra_height=10, style=GearStyle.CIRCLES, thick=3, compensateLooseArbour=False, compact=True, moon_complication=moon)#, inset_at_base=MotionWorks.STANDARD_INSET_DEPTH)
    moon.set_motion_works_sizes(motionWorks)
    # show_object(motionWorks.getAssembled().translate((0,0,TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - motionWorks.inset_at_base)))
    # show_object(moon.get_assembled())
    #
    show_object(moon.get_moon_half())


    #
    # # print(1/moon.ratio)
    # face_width = 6
    # bevels = BevelGearPair(module=1, gear_teeth=23, pinion_teeth=29, face_width=face_width, pressure_angle=20)
    # #
    # print(radToDeg(bevels.axis_angle), face_width*math.sin(bevels.axis_angle))
    #
    # beveled_pair = WheelPinionBeveledPair(wheel_teeth=23, pinion_teeth=29, module=1)
    #
    # show_object(beveled_pair.get_assembled())

    # show_object(bevels.assemble())
    # testbevel = cq.Workplane("XY").add(bevels.gear.build()).intersect(cq.Workplane("XY").rect(100,100).extrude(face_width*math.sin(bevels.axis_angle/2)).translate((0,0,0)))
    #
    # testbevel = testbevel.cut(cq.Workplane("XY").circle(3.2/2).extrude(10))
    #
    # testbevel_pinion = cq.Workplane("XY").add(bevels.pinion.build()).intersect(cq.Workplane("XY").rect(100,100).extrude(face_width*math.sin(bevels.axis_angle/2)))
    # testbevel_pinion = testbevel_pinion.cut(cq.Workplane("XY").circle(3.2/2).extrude(10))
    #
    # show_object(testbevel)
    # show_object(testbevel_pinion.rotate((0,0,0),(1,0,0),90).translate((0,bevels.pinion.cone_h,bevels.gear.cone_h)))
    # # show_object(bevels.gear.build())
    # # show_object(bevels.pinion.build())
    #
    # holder_wide = 10
    # holder_thick = 5
    # holder_long = bevels.pinion.cone_h + WASHER_THICK_M3
    #
    # holder_tall = bevels.gear.cone_h + holder_thick + WASHER_THICK_M3
    #
    #
    # # testbevel_holder = cq.Workplane("XY").moveTo(0,holder_long/2 - holder_wide/2).rect(holder_wide, holder_long).extrude(holder_thick).faces(">Z").workplane().circle(3/2).cutThruAll()
    #
    # testbevel_holder = cq.Workplane("XY").circle(holder_wide/2).extrude(holder_thick)
    # testbevel_holder = testbevel_holder.union(get_stroke_line([(0,0), (0,holder_long + holder_thick)],wide = holder_wide,thick = holder_thick, style=StrokeStyle.SQUARE))
    #
    # testbevel_holder = testbevel_holder.union(cq.Workplane("XY").moveTo(0,bevels.pinion.cone_h + WASHER_THICK_M3 + holder_thick/2).rect(holder_wide, holder_thick).extrude(holder_tall))
    # testbevel_holder = testbevel_holder.union(cq.Workplane("XY").circle(holder_wide/2).extrude(holder_thick).rotate((0,0,0),(1,0,0),-90).translate((0,holder_long,holder_tall)))
    #
    # testbevel_holder = testbevel_holder.cut(cq.Workplane("XY").circle(3/2).extrude(holder_thick))
    # testbevel_holder = testbevel_holder.cut(cq.Workplane("XY").circle(3/2).extrude(holder_thick).rotate((0,0,0),(1,0,0),-90).translate((0,holder_long,holder_tall)))
    #
    # show_object(testbevel_holder.translate((0,0,-holder_thick-WASHER_THICK_M3)))

    # exporters.export(testbevel, "out/test_bevel.stl")
    # exporters.export(testbevel_pinion, "out/test_bevel_pinion.stl")
    # exporters.export(testbevel_holder, "out/test_bevel_holder.stl")
#
# mistletoe = MistletoeSprig() #MistletoeLeafPair()
#
# # show_object(mistletoe.get_branch())
# show_object(mistletoe.get_leaves(),options = { "color" : "green"})
# show_object(mistletoe.get_berries(),options = { "color" : "white"})
# # sprig = cq.Assembly(name='mistletoe')
# sprig.add(mistletoe.get_leaves(), name='leaves', loc=cq.Location(),color='green')
# sprig.add(mistletoe.get_berries(), name='berries', loc=cq.Location(),color='white')
#
# show_object(sprig)

# whistle = CuckooWhistle()
#
# # show_object(whistle.getWholeWhistle())
# show_object(whistle.getWhistleTop())

# show_object(Gear.cutStyle(cq.Workplane("XY").circle(120).extrude(5),outerRadius=100, innerRadius=30,style=GearStyle.CIRCLES_HOLLOW))

# show_object(roman_numerals("VII",30,cq.Workplane("XY"),0.4))



# x=0
# for i in range(60,70,2):
#     # innerR:29.5 outerR:34.2383298577297, petals:24
#     innerR = 29.5
#     outerR = 100 - i
#
#
#     circle = cq.Workplane("XY").circle(outerR+5).extrude(3)
#
#     show_object(Gear.cutFlowerStyle2(circle,  outerRadius=outerR, innerRadius=innerR).translate((x,0,0)))
#     x += outerR*2 + 5

# show_object(get_stroke_semicircle((-50,0), 20, math.pi/2, math.pi, 3,2))

# suspension_bits = SuspensionSpringPendulumBits()
#
# show_object(suspension_bits.get_crutch())

# show_object(cq.Solid.makeSphere(10))

# viewer = ViewGenerator()
#
# viewer.display(cq.Workplane("XY").rect(10,10).extrude(10))
# viewer.save_screenshot("out/screenshottest.png")


# rolling_ball = RollingBallEscapement()
#
# tray = rolling_ball.get_track_assembled()
#
# show_object(tray)
# out = "tray.stl"
# print("Outputting ", out)
# exporters.export(rolling_ball.get_track(), out)

# pair = WheelPinionPair(wheelTeeth=55,pinionTeeth= 22, module=0.891)
#
# show_object(pair.get_model(offset_angle_deg=-0.3))


# ratchet = TraditionalRatchet(50, power_clockwise=True)
#
# show_object(ratchet.get_gear())
# show_object(ratchet.get_pawl())