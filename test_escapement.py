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
# escapement2 = BrocotEscapment(use_rubies=True, diameter=diameter)
# teeth=30
# anchor_teeth = math.floor(teeth / 3) + 0.5
#
# escapement = AnchorEscapement(anchor_teeth=anchor_teeth, diameter=diameter)
#
# # show_object(escapement.get_anchor_2d().rotate((0,escapement.anchor_centre_distance,0),(0,escapement.anchor_centre_distance,1),-(escapement.lift_deg/2+escapement.lock_deg/2)))
# # show_object(escapement.get_anchor())
# # show_object(escapement.get_wheel_2d())
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
# escapement = AnchorEscapement.get_with_45deg_pallets(teeth, drop)
# escapement = AnchorEscapement.get_with_45deg_pallets(teeth=30, drop_deg=2.75, lock_deg=1.5, diameter=45, force_diameter=True, anchor_thick=10)
# escapement = AnchorEscapement(drop=drop, lift=lift, teeth=teeth, lock=lock, tooth_tip_angle=tooth_tip_angle,
# escapement = AnchorEscapement.get_with_45deg_pallets(teeth=30, drop_deg=2, lock_deg=1.5, force_diameter=False, anchor_thick=10)
# escapement = AnchorEscapement.get_with_optimal_pallets(30, drop_deg=1.75, diameter=60)
escapement = AnchorEscapement.get_with_optimal_pallets(60, drop_deg=1.75, diameter=60, anchor_teeth=9.5)
#                                     tooth_base_angle=tooth_base_angle, style=AnchorStyle.CURVED_MATCHING_WHEEL, wheel_thick=2, type=EscapementType.DEADBEAT)

print("wheel angle ",rad_to_deg(escapement.wheel_angle))

drop = escapement.drop_deg
lift = escapement.lift_deg#+0.5
big_escapement = AnchorEscapement(60, diameter=120, drop=drop, lift=lift, anchor_teeth=9.5, style=AnchorStyle.CURVED_MATCHING_WHEEL, tooth_height_fraction=0.1,
                                  tooth_tip_angle=5/2, tooth_base_angle=4/2)

anchor_angle_deg = 0#-2.5
wheel_angle_deg = 0#-5.25#-1.7

# anchor_angle_deg = 0
# wheel_angle_deg = -1.25

# show_object(escapement.get_assembled(anchor_angle_deg=anchor_angle_deg, wheel_angle_deg=wheel_angle_deg, distance_fudge_mm=0.5))
show_object(big_escapement.get_assembled(anchor_angle_deg=anchor_angle_deg, wheel_angle_deg=wheel_angle_deg, distance_fudge_mm=0.5))

show_object(cq.Workplane("XY").circle(escapement.radius))
#40 teeth distance 73.6593180385267
print("distance", escapement.anchor_centre_distance)
