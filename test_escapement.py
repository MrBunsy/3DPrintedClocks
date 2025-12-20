from clocks.power import *
from clocks.escapements import *
from clocks.striking import *
from clocks.plates import *
from clocks.utility import *
from clocks.leaves import HollyLeaf, Wreath, HollySprig
from clocks.cosmetics import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass


# escapement = GrasshopperEscapement.get_harrison_compliant_grasshopper()#BrocotEscapment()
# show_object(escapement.get_assembled())

diameter = 55
#
escapement = BrocotEscapment(use_rubies=True, diameter=diameter, style=AnchorStyle.FANCY_BROCOT)
# teeth=30
# anchor_teeth = math.floor(teeth / 3) + 0.5
#
# escapement = AnchorEscapement(anchor_teeth=anchor_teeth, diameter=diameter)
#
# show_object(escapement.get_anchor_2d().rotate((0,escapement.anchor_centre_distance,0),(0,escapement.anchor_centre_distance,1),-(escapement.lift_deg/2+escapement.lock_deg/2)))
# show_object(escapement.get_anchor().translate((0,escapement.anchor_centre_distance)))
# show_object(escapement.get_wheel().translate((0,0,10)))
# show_object(escapement.get_assembled())
# show_object(escapement2.get_assembled())
#
# show_object(cq.Workplane("XY").circle(escapement.radius))


# show_object(cq.Workplane("XY").circle(escapement.diameter/2))

# escapement = AnchorEscapement(diameter=diameter)

# drop =4
# lift =3
# lock=1.25
# pendulum_period=2.0
# teeth = 20
# toothspan = floor(teeth / 4) + 0.5
# escapement = BrocotEscapment(drop=drop, lift=lift, teeth=teeth, lock=lock, diameter=55, anchor_teeth=toothspan)

lift=3
drop=3
lock=2
tooth_tip_angle=3
tooth_base_angle=3

# drop =3
# lift =3
# lock= 2
drop =2.5
lift =2
lock= 0
tooth_tip_angle = 5
tooth_base_angle = 4

lift=3
drop=2
lock=2
# drop =2.5
# lift =2
# lock= 2

# drop =1.5
# lift =2.5
# lock=1.5

lift=3
drop=3
lock=2
# drop =2.5
# lift =2
# lock= 2
teeth = 30


drop =1.5
lift =2.75
lock=1.5
teeth=40

teeth=30
drop=2.75
#
# escapement2 = AnchorEscapement.get_with_optimal_pallets(teeth, drop)
# # escapement = AnchorEscapement.get_with_45deg_pallets(teeth=30, drop_deg=2.75, lock_deg=1.5, diameter=45, force_diameter=True, anchor_thick=10)
# # escapement = AnchorEscapement(drop=drop, lift=lift, teeth=teeth, lock=lock, tooth_tip_angle=tooth_tip_angle,
# # escapement = AnchorEscapement.get_with_45deg_pallets(teeth=30, drop_deg=2, lock_deg=1.5, force_diameter=False, anchor_thick=10)
# # escapement = AnchorEscapement.get_with_optimal_pallets(30, drop_deg=1.75, diameter=60)
# escapement = AnchorEscapement.get_with_optimal_pallets(60, drop_deg=1.75, diameter=60, anchor_teeth=9.5)
# #                                     tooth_base_angle=tooth_base_angle, style=AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2, type=EscapementType.DEADBEAT)
#
# print("wheel angle ",rad_to_deg(escapement.wheel_angle))
#
# drop = escapement.drop_deg
# lift = escapement.lift_deg#+0.5
# escapement = AnchorEscapement.get_with_optimal_pallets(60, drop_deg=1.75, diameter=60, anchor_teeth=9.5)
# #but we want to reconfigure the diameter and tooth size
# big_escapement = AnchorEscapement(60, diameter=132, drop=escapement.drop_deg, lift=escapement.lift_deg, anchor_teeth=9.5, style=AnchorStyle.CURVED_MATCHING_WHEEL,
#                                         tooth_height_fraction=0.1, tooth_tip_angle=5/2, tooth_base_angle=4/2, force_diameter=True, wheel_thick=2)
# #old anchor distance
# anchor_centre_distance = big_escapement.anchor_centre_distance
#
# #trying with normal tooth span and retrofitting
#
# teeth = 60
# anchor_teeth = math.floor(teeth / 4) + 0.5
# wheel_angle = math.pi * 2 * anchor_teeth / teeth
# radius  = anchor_centre_distance * math.cos(wheel_angle / 2)
#
# tooth_height_fraction=0.15
# angle_divisor = (0.2/tooth_height_fraction)
# big_escapement = AnchorEscapement(teeth, diameter=radius*2, drop=escapement.drop_deg, lift=escapement.lift_deg, anchor_teeth=anchor_teeth, style=AnchorStyle.STRAIGHT,
#                                         tooth_height_fraction=tooth_height_fraction, tooth_tip_angle=2, tooth_base_angle=1.5, force_diameter=True,
#                                         wheel_thick=2, run=5, lock=1)
#
# anchor_angle_deg =0#1#-2.5
# wheel_angle_deg = -1.2#0.7#1.8#-0.6#-5.25#-1.7

# anchor_angle_deg = 0
# wheel_angle_deg = -1.25
#
# model = big_escapement.get_assembled(anchor_angle_deg=anchor_angle_deg, wheel_angle_deg=wheel_angle_deg, distance_fudge_mm=0.5)
#
# # show_object(escapement2.get_assembled(anchor_angle_deg=anchor_angle_deg, wheel_angle_deg=wheel_angle_deg, distance_fudge_mm=0.5))
# show_object(model)
#
# # show_object(Gear.cutStyle(big_escapement.get_wheel(2), outer_radius=big_escapement.get_wheel_inner_r(), inner_radius=6, style = GearStyle.DIAMONDS, clockwise_from_pinion_side=True, lightweight=True))
#
# # show_object(cq.Workplane("XY").circle(escapement.radius))
# #40 teeth distance 73.6593180385267
# print("distance", escapement.anchor_centre_distance)
# #(-1.75, 1.1, 5)
#
# #"projectionDir": (-1, 0, 0), "xDirection": (0,0,1)
# exportSVG(model, "out/test_model.svg", opts={"width":400, "height":400, "projectionDir": (1, -1, 1), "xDirection": (-1, -1, 0), "yDirection": (0, 0, 1), "showHidden": False})


# anchor = AnchorEscapement.get_with_optimal_pallets(diameter=40)
# silent = SilentAnchorEscapement(diameter=40)
# anchor = AnchorEscapement.get_with_optimal_pallets(teeth=30, drop_deg=2,diameter=40)
# silent = SilentPinPalletAnchorEscapement(diameter=47.75,pin_diameter=1.4 , teeth=anchor.teeth, drop=anchor.drop_deg, lock=anchor.lock_deg, lift=anchor.lift_deg, run=anchor.run_deg)
escapement_info = AnchorEscapement.get_with_optimal_pallets(20, drop_deg=3)#1.75
# escapement = SilentAnchorEscapement(teeth=escapement.teeth, drop=escapement.drop, lift=escapement.lift,l)
escapement = SilentPinPalletAnchorEscapement(teeth=escapement_info.teeth, drop=escapement_info.drop_deg, lift=escapement_info.lift_deg, run=escapement_info.run_deg, lock=escapement_info.lock_deg,
                                             pin_diameter=1.0, pin_external_length=1.5*2 + 3 + 1, diameter=45)
# show_object(silent.get_wheel())
# show_object(silent.get_anchor())
# show_object(escapement.get_assembled(anchor_angle_deg=2, wheel_angle_deg=1))
show_object(escapement.get_assembled())
show_object(cq.Workplane("XY").circle(escapement.wheel_max_r))
show_object(cq.Workplane("XY").circle(0.5).extrude(100).translate(escapement.fixing_screw_pos).translate(escapement.anchor_centre))

# show_object(get_stroke_line([(0,100),(0,0)], wide=20, thick=10))