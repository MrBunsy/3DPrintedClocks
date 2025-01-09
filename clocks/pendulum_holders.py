from .geometry import *
from .types import *

from .utility import *
import cadquery as cq

class FrictionFitPendulumBits:
    '''
    Pendulum holder that attaches to a threaded rod by friction, can be manually adjusted to set in beat
    Do not use for new designs - was a pain to set the beat and easy to knock out of beat
    '''

    def __init__(self, arbor_d=3):
        self.pendulumTopThick = 15
        self.arbor_d = arbor_d

    def get_pendulum_holder(self, holeD=3, for_printing=True):
        '''
        Will allow a threaded rod for the pendulum to be attached to threaded rod for the arbour
        '''

        pendulum = cq.Workplane("XY")

        width = 12  # holeD*4
        height = 22  # 26#holeD*6

        # I've noticed that the pendulum doesn't always hang vertical, so give more room for the rod than the minimum so it can hang forwards relative to the holder
        extraRodSpace = 1

        # (0,0,0) is the rod from the anchor, the rod is along the z axis

        # hole that the pendulum (threaded rod with nyloc nut on the end) rests in
        holeStartY = -get_nut_containing_diameter(self.arbor_d) * 0.5 - 0.4  # -5#-8#-height*0.2
        holeHeight = get_nut_height(self.arbor_d, nyloc=True) + get_nut_height(self.arbor_d) + 1

        nutD = get_nut_containing_diameter(holeD)

        wall_thick = (width - (nutD + 1)) / 2

        pendulum = pendulum.moveTo(-width / 2, 0).radiusArc((width / 2, 0), width / 2).line(0, -height).radiusArc((-width / 2, -height), width / 2).close().extrude(self.pendulumTopThick)

        pendulum = pendulum.faces(">Z").workplane().circle(holeD / 2).cutThruAll()

        # nut to hold to anchor rod
        nutThick = get_nut_height(holeD, nyloc=True)
        nutSpace = cq.Workplane("XY").polygon(6, nutD).extrude(nutThick).translate((0, 0, self.pendulumTopThick - nutThick))
        pendulum = pendulum.cut(nutSpace)

        # pendulum = pendulum.faces(">Z").moveTo(0,-height*3/4).rect(width-wall_thick*2,height/2).cutThruAll()
        space = cq.Workplane("XY").moveTo(0, holeStartY - holeHeight / 2).rect(width - wall_thick * 2, holeHeight).extrude(self.pendulumTopThick).translate((0, 0, LAYER_THICK * 3))
        pendulum = pendulum.cut(space)

        extraSpaceForRod = 0.1
        extraSpaceForNut = 0.2
        #
        rod = cq.Workplane("XZ").tag("base").moveTo(0, self.pendulumTopThick / 2 - extraRodSpace).circle(self.arbor_d / 2 + extraSpaceForRod / 2).extrude(100)
        # add slot for rod to come in and out
        rod = rod.workplaneFromTagged("base").moveTo(0, self.pendulumTopThick - extraRodSpace).rect(self.arbor_d + extraSpaceForRod, self.pendulumTopThick).extrude(100)

        rod = rod.translate((0, holeStartY, 0))

        pendulum = pendulum.cut(rod)

        nutSpace2 = cq.Workplane("XZ").moveTo(0, self.pendulumTopThick / 2).polygon(6, nutD + extraSpaceForNut).extrude(nutThick).translate((0, holeStartY - holeHeight, 0))
        pendulum = pendulum.cut(nutSpace2)

        if not for_printing:
            pendulum = pendulum.mirror().translate((0, 0, self.pendulumTopThick))

        return pendulum


class ColletFixingPendulumWithBeatSetting:
    '''
    The PendulumFixing.DIRECT_ARBOR has a pendulum holder that slots onto a square (or rounded square) rod.
    This works really well, but there's no way to set the beat other than bending the pendulum rod.
    So - this is an attempt to copy a mechanism I've seen on old clocks on ebay:

    We'll use a collet like the direct arbor fixing, but this won't hold the pendulum directly. it will hold a pivot point for the pendulum holder
    and a horizontal threaded rod. the pendulum holder will pivot on the aforementioned pivot point and have the threaded rod passing through half way down
    this will enable the threaded rod to be twisted to adjust the alignment left and right a bit

    slightly improved idea: have the rod fixed and a hole in the centre of the pendulum holder with a single thumb-nut. This makes it lighter and less bulky

    then at the bottom of the pendulum holder there will be a mechanism like the existing one that the top of the pendulum slots into


    default to 14.5 thick because it's easy to buy 14mm countersunk m3 screws but for some reason hard to buy 15mm
    so then I can use a 14mm screw without it sticking out the end or looking like it's too short
    '''

    def __init__(self, collet_size, fixing_screws=None, pendulum_fixing_extra_space=0.2, pendulum_holder_thick=14.5, length=35, collet_screws=None):
        self.collet_size = collet_size
        self.fixing_screws = fixing_screws
        if self.fixing_screws is None:
            self.fixing_screws = MachineScrew(3, countersunk=True)
        self.pendulum_fixing_extra_space = pendulum_fixing_extra_space

        self.collet_screws = collet_screws
        if self.collet_screws is None:
            self.collet_screws = MachineScrew(2, countersunk=False)

        self.arm_width = collet_size * 1.5
        if self.arm_width < 12:
            self.arm_width = 12
        self.collet_radius = collet_size
        if self.collet_radius < self.arm_width / 2:
            self.collet_radius = self.arm_width / 2
        self.length = length
        self.width = length * 0.55
        self.pendulum_holder_thick = pendulum_holder_thick
        self.threadholder_arm_width = self.arm_width * 0.75

        nearest_screw = get_nearest_machine_screw_length(self.get_thread_screw_length(), self.fixing_screws, prefer_longer=True)
        extra_width = nearest_screw - self.get_thread_screw_length()
        print(f"Making pendulum holder {extra_width} wider to better fit available machine screws")
        self.width += extra_width

        self.hinge_distance = self.collet_radius + self.arm_width / 2 + 1  # self.arm_width*1.5
        self.hinge_point = (0, - self.hinge_distance)

        # where the arcs will branch out from
        self.arm_end_point = (0, -self.length + self.width / 2 + self.threadholder_arm_width / 2)

        # plus extra because we'll be at an angle
        self.nut_hole_height = self.fixing_screws.get_nut_containing_diameter(thumb=True) + 3

        self.top_of_pendulum_holder_hole_y = -self.length - self.nut_hole_height / 2 - 1.5

        print("beat setter needs {} of length {:.1f}".format(self.fixing_screws, self.get_thread_screw_length()))

    def get_BOM(self):
        adjusting_screw_length = get_nearest_machine_screw_length(self.get_thread_screw_length(), self.fixing_screws)
        fixing_screw_length = get_nearest_machine_screw_length(self.pendulum_holder_thick, self.fixing_screws)
        bom = BillOfMaterials("Pendulum Holder")
        bom.add_item(BillOfMaterials.Item(f"{self.fixing_screws} {adjusting_screw_length:.0f}mm", object=self.fixing_screws))
        bom.add_item(BillOfMaterials.Item(f"{self.fixing_screws} {fixing_screw_length:.0f}mm", object=self.fixing_screws))
        bom.add_item(BillOfMaterials.Item(f"M{self.fixing_screws} Thumb nut ({self.fixing_screws.get_nut_height(thumb=True):.1f}mm thick)", object=self.fixing_screws))
        bom.add_item(BillOfMaterials.Item(f"M{self.fixing_screws} Crinkle washer"))
        bom.add_item(BillOfMaterials.Item(f"M{self.fixing_screws} Nut"))
        bom.add_item(BillOfMaterials.Item(f"M{self.collet_screws} 5mm", self.collet_screws))# think 5mm did the job?
        bom.add_item(BillOfMaterials.Item(f"M{self.collet_screws} half nut"))

        return bom

    def get_thread_cutter(self):
        thick = self.pendulum_holder_thick
        thread_cutter = self.fixing_screws.get_cutter(sideways=True).rotate((0, 0, 0), (0, 1, 0), 90).translate((-self.width / 2 - self.threadholder_arm_width, -self.length, thick / 4))
        thread_cutter = thread_cutter.union(self.fixing_screws.get_nut_cutter().rotate((0, 0, 0), (0, 0, 1), 360 / 12).rotate((0, 0, 0), (0, 1, 0), -90).translate((-self.width / 2, -self.length, thick / 4)))
        return thread_cutter

    def get_thread_screw_length(self):
        return self.width + self.threadholder_arm_width * 2

    def get_collet(self):
        '''
        centred on centre of rod that goes through the collet
        '''
        half_thick = self.pendulum_holder_thick / 2
        thick = self.pendulum_holder_thick

        end_thick = self.arm_width * 0.4
        fillet_r = self.arm_width * 0.25

        # arm from collet to arm_end_point
        collet = get_stroke_line([(0, 0), self.arm_end_point], wide=self.arm_width, thick=half_thick, style=StrokeStyle.SQUARE).translate((0, 0, half_thick))

        # collet
        collet = collet.union(cq.Workplane("XY").circle(self.collet_radius).extrude(thick))

        curve_outer_r = self.width / 2 + self.threadholder_arm_width
        # curve centred on hinge_pos

        # arms that curve down to the threaded rod holders
        arms = cq.Workplane("XY").moveTo(0, -self.length).circle(curve_outer_r).circle(curve_outer_r - self.threadholder_arm_width).extrude(half_thick).translate((0, 0, half_thick)).cut(
            cq.Workplane("XY").moveTo(0, -self.length - curve_outer_r).rect(curve_outer_r * 2, curve_outer_r * 2).extrude(thick))
        for x_dir in [-1, 1]:
            x = x_dir * (self.width / 2 + self.threadholder_arm_width / 2)
            # arms = arms.union(get_stroke_line([(x, self.hinge_point[1]), (x, -self.length - self.fixing_screws.get_nut_containing_diameter()/2)], wide=self.threadholder_arm_width, thick=thick))#arms.union(cq.Workplane.moveTo(x*self.width/2+self.threadholder_arm_width/2,-(self.length + self.)))
            arms = arms.union(cq.Workplane("XY").moveTo(x, -self.length).circle(self.threadholder_arm_width / 2).extrude(thick))
        collet = collet.union(arms)
        #
        # #sideways arm for the adjustment
        # arm = cq.Workplane("XY").moveTo(0, -self.length).rect(self.width, self.arm_width).extrude(thick).translate((0,0, thick))#.edges("|Z").fillet(fillet_r))
        #
        # for x in [-1, 1]:
        #     edges=">X" if x > 0 else "<X"
        #     arm = arm.union(cq.Workplane("XY").moveTo(x*(self.width/2 + end_thick/2),-self.length).rect(end_thick, self.arm_width).extrude(self.pendulum_holder_thick).edges("|Z and {}".format(edges)).fillet(fillet_r))
        #
        # collet = collet.union(arm)

        # cut hinge point screw hole
        # collet = collet.cut(self.fixing_screws.get_cutter(with_bridging=True, for_tap_die=True).rotate((0, 0, 0), (1, 0, 0), 180).translate((self.hinge_point[0], self.hinge_point[1], self.pendulum_holder_thick)))
        # was considering using a pan head with the head outside, so this is as strong as possible, but then it can struggle to fit when the back_plate_from_wall isn't large enough
        # might put countersunk head in teh pendulum holder arm instead
        collet = collet.cut(cq.Workplane("XY").circle(self.fixing_screws.get_rod_cutter_r(for_tap_die=True)).extrude(thick).rotate((0, 0, 0), (1, 0, 0), 180).translate((self.hinge_point[0], self.hinge_point[1], self.pendulum_holder_thick)))
        # cut out square bit that slots over arbour
        collet = collet.cut(cq.Workplane("XY").rect(self.collet_size, self.collet_size).extrude(thick))

        # return thread_cutter
        collet = collet.cut(self.get_thread_cutter())

        # screw and nut to tightly fix to the anchor rod, will probably have to use pan head as cutting space for countersunk leaves the gap a bit thin
        # used to come in from the bottom, but that makes assembly tricky, so going to come in from the side
        screw_length = self.arm_width / 2 - self.collet_size / 2 + 2
        # just a tiny bit makes it easier to put in
        extra_deep = 0.25
        nut_thick = self.collet_screws.get_nut_height(half=True) + extra_deep
        # collet = collet.cut(self.collet_screws.get_cutter(length=screw_length, head_space_length=10).rotate((0, 0, 0), (1, 0, 0), -90).translate((0, -self.collet_size/2 - screw_length, self.pendulum_holder_thick/4)))
        # collet = collet.cut(self.collet_screws.get_nut_cutter(half=True).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, -self.collet_size / 2, self.pendulum_holder_thick/4)))
        collet = collet.cut(self.collet_screws.get_cutter(length=screw_length, head_space_length=10).rotate((0, 0, 0), (0, 1, 0), 90).translate((-self.collet_size / 2 - screw_length, 0, self.pendulum_holder_thick / 4)))
        collet = collet.cut(self.collet_screws.get_nut_cutter(height=nut_thick).rotate((0, 0, 0), (0, 1, 0), -90).translate((-self.collet_size / 2, 0, self.pendulum_holder_thick / 4)))

        return collet

    def get_pendulum_holder(self, for_printing=True):

        # plus extra because we'll be at an angle
        # nut_hole_height = self.fixing_screws.get_nut_containing_diameter(thumb=True) + 3
        # 0.5 for space to squash a crinkle washer to add friction that will hopefully prevent this turning by itself
        #-0.74 because it turned out taht thumb=true was being ignored! this adjusts for that
        nut_hole_centre_width = self.fixing_screws.get_nut_height(thumb=True) + 0.9 - 0.74  # +1 worked, but think there was a tiny bit of slack +0.8 worked but was really tough to get the washer in
        nut_hole_centre_height = self.fixing_screws.metric_thread
        nut_hole_width = self.arm_width * 0.5

        half_thick = self.pendulum_holder_thick / 2

        # bit longer to give pendulum holder more length and therefore less wobble
        bottom = (self.hinge_point[0], self.hinge_point[1] - self.length - 15)

        holder = get_stroke_line([self.hinge_point, bottom], wide=self.arm_width, thick=self.pendulum_holder_thick)

        nut_hole_height = self.nut_hole_height

        end_of_half_thick = self.top_of_pendulum_holder_hole_y + 1.5

        holder = holder.cut(cq.Workplane("XY").moveTo(0, end_of_half_thick / 2).rect(self.arm_width * 2, abs(end_of_half_thick)).extrude(half_thick).translate((0, 0, half_thick)))

        # holder = holder.cut(cq.Workplane("XY").circle(self.arm_width/2 + 0.25).extrude(self.pendulum_holder_thick/2).translate((self.hinge_point[0], self.hinge_point[1], half_thick/2)))
        # hinge point hole for screw
        # holder = holder.cut(cq.Workplane("XY").moveTo(self.hinge_point[0], self.hinge_point[1]).circle(self.fixing_screws.get_rod_cutter_r()).extrude(self.pendulum_holder_thick))
        holder = holder.cut(self.fixing_screws.get_cutter(with_bridging=True, loose=True).translate(self.hinge_point))

        # hole for thumb nut
        hole_cutter = (cq.Workplane("XY").moveTo(-nut_hole_centre_width / 2, nut_hole_centre_height / 2).lineTo(-nut_hole_width / 2, nut_hole_height / 2).lineTo(nut_hole_width / 2, nut_hole_height / 2)
                       .lineTo(nut_hole_centre_width / 2, nut_hole_centre_height / 2).lineTo(nut_hole_centre_width / 2, -nut_hole_centre_height / 2).lineTo(nut_hole_width / 2, -nut_hole_height / 2)
                       .lineTo(-nut_hole_width / 2, -nut_hole_height / 2).lineTo(-nut_hole_centre_width / 2, -nut_hole_centre_height / 2).close().extrude(self.pendulum_holder_thick))
        holder = holder.cut(hole_cutter.translate((0, -self.length)))

        # place to hang pendulum
        # holder = holder.union()
        z = self.pendulum_holder_thick / 2
        # cut out of the bottom so we can place right up against the back plate if needed
        # trying extra 0.2 nut space as the bridging makes it hard to get the pendulum in with the default of 0.2
        # 0.4 works, but feels sliiightly too loose
        # 0.3 works but is still a bit tight, not sure end-users would be able to easily put pendulum in, going back to 0.4 but with reduced space for rod
        # tryin reducing sideways space too, default was 0.1
        holder = holder.cut(get_pendulum_holder_cutter(z=z, extra_nut_space=0.4, extra_space_for_rod=0.0).translate((0, self.top_of_pendulum_holder_hole_y)).rotate((0, 0, z), (0, 1, z), 180))

        thumb_nut_d = self.fixing_screws.get_nut_containing_diameter(thumb=True)

        # TODO cut away top of hexagon from top and bottom so the nut is accessible
        # or maybe just make the holder half the thickness, then I can reduce the size of teh collet part too? back to two sticky-outy arms

        # elongated hole for the threaded rod, elongated because this twists sideways
        hole_wide = self.fixing_screws.get_rod_cutter_r(loose=True, sideways=True) * 2 + 0.5
        # get_stroke_line([(0, -nut_hole_centre_height/2), (0, nut_hole_centre_height/2)], wide=self.fixing_screws.get_rod_cutter_r(loose=True, sideways=True)*2 + 0.5, thick=self.width*3)
        threaded_hole_cutter = (cq.Workplane("XY").rect(hole_wide, nut_hole_centre_height * 2.5).extrude(self.width * 3)
                                .rotate((0, 0, half_thick / 2), (0, 1, half_thick / 2), 90).translate((-self.width, -self.length, 0)))
        holder = holder.cut(threaded_hole_cutter)

        # holder = holder.rotate((0,-self.hinge_distance,0),(0,-self.hinge_distance,1),12)

        return holder

    def get_assembled(self):
        assembly = self.get_collet()
        assembly = assembly.add(self.get_pendulum_holder(for_printing=False))

        return assembly


class SuspensionSpringPendulumBits:
    '''
    Crutch and pendulum holder for a suspension spring, contained here to avoid making ArborForPlate far too large

    UNFINISHED
    '''

    def __init__(self, crutch_length=40, square_side_length=6, crutch_thick=7.5, collet_screws=None, crutch_screw=None, printed_suspension=True):

        self.collet_screws = collet_screws

        # experiment: try a 3D printed suspension spring
        self.printed_suspension = printed_suspension

        if self.collet_screws is None:
            self.collet_screws = MachineScrew(2, countersunk=True)

        self.crutch_screw = crutch_screw
        if self.crutch_screw is None:
            self.crutch_screw = MachineScrew(3, countersunk=True)

        self.crutch_length = crutch_length
        # size of the square that will slot onto the anchor arbor
        self.square_side_length = square_side_length
        self.crutch_thick = crutch_thick

        self.radius = self.square_side_length * 0.5 / math.sqrt(2) + 4
        self.crutch_wide = 10

    def get_crutch(self):
        crutch = cq.Workplane("XY").circle(self.radius).extrude(self.crutch_thick)
        # means to hold screw that will hold this in place
        crutch = crutch.cut(self.collet_screws.get_cutter(length=self.radius, head_space_length=5).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, self.radius, self.crutch_thick / 2)))
        # rotating so bridging shouldn't be needed to print
        crutch = crutch.cut(self.collet_screws.get_nut_cutter(half=True).rotate((0, 0, 0), (0, 0, 1), 360 / 12).rotate((0, 0, 0), (1, 0, 0), -90).translate((0, self.square_side_length / 2, self.crutch_thick / 2)))

        # arm down to the screw that will link with the pendulum
        crutch = crutch.union(cq.Workplane("XY").moveTo(0, -self.crutch_length / 2).rect(self.crutch_wide, self.crutch_length).extrude(self.crutch_thick))
        crutch = crutch.union(cq.Workplane("XY").moveTo(0, -self.crutch_length).circle(self.crutch_wide / 2).extrude(self.crutch_thick))

        # screw to link with pendulum
        crutch = crutch.cut(self.crutch_screw.get_cutter(with_bridging=True).translate((0, -self.crutch_length)))

        crutch = crutch.faces(">Z").workplane().rect(self.square_side_length, self.square_side_length).cutThruAll()

        return crutch

    def get_pendulum_holder(self):
        holder = cq.Workplane("XY")

        return holder
