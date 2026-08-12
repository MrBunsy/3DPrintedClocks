import math

import os

from clocks.utility import *
from clocks.geometry import *
from cadquery import exporters
outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

class Fan:
    def __init__(self, size=120, screw_distance=105):
        self.size = size
        self.screw_distance = screw_distance

class Ducting:

    def __init__(self, diameter=100, wall_thick=5, screw=None, fan=None):
        self.diameter = diameter
        self.wall_thick = wall_thick
        self.screw = screw
        if self.screw is None:
            self.screw = CountersunkWoodScrew.get_wood_screw(4)
        self.fan = fan
        if self.fan is None:
            self.fan = Fan()
        # seen some listed on screwfix as 98mm wide
        self.ducting_radius_wiggle = 1

        self.fillet_r = 2

        # hacky, need them either clockwise or anticlockwise for the template to be easy to make
        self.fan_screw_positions = [
            (self.fan.screw_distance/2, self.fan.screw_distance/2),
            (self.fan.screw_distance / 2, -self.fan.screw_distance / 2),
            (-self.fan.screw_distance / 2, -self.fan.screw_distance / 2),
            (-self.fan.screw_distance / 2, self.fan.screw_distance / 2),
        ]
        # for x in [-1, 1]:
        #     for y in [1, -1]:
        #         self.fan_screw_positions += [(x*self.fan.screw_distance/2, y*self.fan.screw_distance/2)]


    def get_fan_fixing_template(self):
        # template = cq.Workplane("XY").rect(self.fan.size, self.fan.size).pushPoints(self.fan_screw_positions+[(0,0)]).circle(self.screw.get_rod_cutter_r()).extrude(2)
        # template = template.edges("|Z").fillet(5)
        #
        # #cut out some bits
        # thickness = 10
        # for i in range(len(self.fan_screw_positions)-3):
        #     points = [
        #         self.fan_screw_positions[i % len(self.fan_screw_positions)],
        #         self.fan_screw_positions[(i+1) % len(self.fan_screw_positions)],
        #         (0,0)
        #         ]
        #
        #     centre = get_average_of_points(points)
        #
        #
        #
        #     newpoints = []
        #     for point in points:
        #         line = Line(point, anotherPoint=centre)
        #         newpoints.append(np_to_set(np.add(point, np.multiply(line.dir, thickness))))
        #
        #     template = template.faces(">Z").workplane().moveTo(newpoints[0][0], newpoints[0][1])
        #     for point in newpoints[1:]:
        #         template = template.lineTo(point[0], point[1])
        #     template = template.close().extrude(10)
        #     # return template

        thickness = 10

        template = get_stroke_line(self.fan_screw_positions, thickness,2)
        for i in range(len(self.fan_screw_positions)):
            points = [
                self.fan_screw_positions[i % len(self.fan_screw_positions)],
                self.fan_screw_positions[(i+1) % len(self.fan_screw_positions)],
                (0,0)
                ]
            template = template.union(get_stroke_line(points, thickness,2))

        template = template.faces(">Z").workplane().pushPoints(self.fan_screw_positions+[(0,0)]).circle(self.screw.get_rod_cutter_r()).cutThruAll()

        return template

    def get_fan_fixing(self):
        fixing = self.get_flat_surface_fixing(base_wide=self.fan.size, screw_distance= self.fan.screw_distance)

        return fixing
    def get_flat_surface_fixing(self, base_wide=-1, screw_distance=-1):

        #maybe make wider?


        outer_radius = self.diameter/2 - self.ducting_radius_wiggle

        width = outer_radius*2 + self.fillet_r*2

        if base_wide > 0:
            width = base_wide
        tall = 50
        fixing = cq.Workplane("XY").rect(width, width).extrude(self.wall_thick).edges("|Z").fillet(self.fillet_r).edges(">Z").fillet(self.fillet_r)
        fixing = fixing.cut(cq.Workplane("XY").circle(outer_radius - self.wall_thick).extrude(self.wall_thick))

        # screw_from_corner = self.screw.head_diameter*1.5
        # r = math.sqrt(2*(width/2)**2) - screw_from_corner
        #
        # for i in range(4):
        #     angle = math.pi/4 + i*math.pi/2
        #     pos = polar(angle, r)
        #     fixing = fixing.cut(self.screw.get_cutter().rotate((0,0,0),(0,1,0),180).translate((0,0,self.wall_thick)).translate(pos))
        if screw_distance < 0:
            screw_distance = width - self.screw.get_head_diameter()*2.5
        screw_positions = []

        for x in [-1, 1]:
            for y in [-1, 1]:
                screw_positions += [(x*screw_distance/2, y*screw_distance/2)]

        for pos in screw_positions:
            fixing = fixing.cut(self.screw.get_cutter().rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, self.wall_thick)).translate(pos))

        fixing = fixing.union(cq.Workplane("XY").circle(outer_radius).circle(outer_radius - self.wall_thick).extrude(tall + self.wall_thick).edges(">Z").fillet(self.fillet_r))


        return fixing

class WindowVent:

    def __init__(self, wood_thick=5, fixing_screws=None, above_window_sticks_out=7):
        '''
        plan is that the duct fixing can be screwed to a sheet of plywood, which can slot into some fixings attached to the window frame
        two corner bits at the bottom and maybe some sort of latch on the top
        '''

        self.wood_thick = wood_thick
        self.holder_thick = wood_thick
        self.corner_wide = 50
        self.handle_length = 50
        self.handle_wide = 25
        self.knob_long = 30
        self.fixing_screws = fixing_screws
        if self.fixing_screws is None:
            self.fixing_screws = MachineScrew(3, countersunk=True)

        self.above_window_sticks_out = above_window_sticks_out

        self.handle_holder_thick=6
        # self.holder_length = self.handle_wide * 2

    def get_corner_holder(self, left=True):

        #from the side, where the plywood would be slotting in
        holder = (cq.Workplane("XY").lineTo(self.holder_thick*2,0)
                  .lineTo(self.holder_thick*2, self.holder_thick*2)
                  .lineTo(self.holder_thick, self.holder_thick).lineTo(0, self.holder_thick).close().extrude(self.corner_wide))

        face = "<Z" if left else ">Z"

        #holder = holder.faces(face).workplane().moveTo(self.holder_thick,-self.corner_wide/2).rect(self.holder_thick*2, self.corner_wide).extrude(self.holder_thick)

        z = -self.holder_thick if left else self.corner_wide

        end = cq.Workplane("XY").moveTo(self.holder_thick,self.corner_wide/2).rect(self.holder_thick*2, self.corner_wide).extrude(self.holder_thick).translate((0,0,z))
        # return end

        holder = holder.union(end)

        return holder

    def get_handle(self, foldupable=False):
        '''
        foldupable: if true then this can rotate upwards inline with the holder
        '''

        ends = [(0,0), (0,self.handle_length)]

        handle = get_stroke_line(ends, wide=self.handle_wide, thick= self.holder_thick)

        # handle = handle.faces(">Z").pushPoints(ends).circle(self.fixing_screws.get_rod_cutter_r(loose=True)).cutThruAll()
        #loose on one end so the handle can rotate, but fixed on the other end as the knob will be the loose bit
        handle = handle.faces(">Z").workplane().moveTo(ends[0][0], ends[0][1]).circle(self.fixing_screws.get_rod_cutter_r(loose=True)).cutThruAll()

        #decided against knob
        # handle = handle.cut(self.fixing_screws.get_cutter(for_tap_die=True).translate(ends[1]))

        #sticky out bit that will press tightly against the wood

        sticky_out_thick = self.above_window_sticks_out + self.handle_holder_thick - self.wood_thick
        if foldupable:
            sticky_out_thick = self.handle_holder_thick

        handle = handle.faces(">Z").workplane().moveTo(ends[1][0], ends[1][1]).circle(self.handle_wide/2).extrude(sticky_out_thick)


        return handle

    def get_pad(self):
        '''
        for handle that is foldupable, need to make the wood thicker
        '''
        pad = get_stroke_line([(0,0), (0,self.handle_length)], wide=self.handle_wide, thick = self.above_window_sticks_out - self.wood_thick)

        return pad

    def get_knob(self):
        '''
        don't think I need a knob after all, just the handle should be enough, like the bits that hold drop-down tables on trains in place
        '''
        knob = cq.Workplane("XY").circle(self.handle_wide/2).circle(self.fixing_screws.get_rod_cutter_r(loose=True)).extrude(self.knob_long)

        #knob is loose, no need for embedding nyloc nut! that can go on the end
        # knob = knob.cut(self.fixing_screws.get_nut_cutter(nyloc=True).translate((0,0,self.knob_long - self.fixing_screws.get_nut_height(nyloc=True))))
        return knob
    def get_handle_holder(self):
        '''
        bit above the window sticks out a bit, the plywood isn't very thick, so I'm not sure how to do this yet

        IDEA - make the handle thicker on the end, can then keep the pivot as thick as needed
        '''

        # length = self.handle_wide*2
        #the two radii at ends of handle and holder cancel out, so this is just short enough that the handle can rotate 360deg if foldupable
        length = self.handle_length - 2

        holder = get_stroke_line([(-length/2, 0), (length/2, 0)], wide=self.handle_wide, thick = self.handle_holder_thick)

        holder = holder.cut(self.fixing_screws.get_cutter(self_tapping=True))

        return holder

class WindowVentImproved():
    def __init__(self, wood_thick=5, seal_effective_thick=2):
        '''
        The previous one required fixing things to the inside of the window. This didn't work very well.
        New idea - have something that fixes to the plywood and hooks onto the bottom of the window and then a rotating bit at top which can hook in there too!
        This should be much more secure and reliable.

        Might even work with using some sort of seal around the edge to make it properly air-tight, then this could be reused with an air condition in future
        '''
        self.wood_thick = wood_thick
        #how much space to allow the seal once its squished slightly in place
        self.seal_effective_thick = seal_effective_thick
        self.fixing_screws = MachineScrew(3, type=MachineScrewType.COUNTERSUNK)

        self.hook_thick = 15

        self.window_frame_thick = 15
        self.window_frame_angled_length=9
        self.window_frame_rubber_seal_thick_unsquished = 5
        self.window_frame_rubber_seal_thick_squished = 3
        self.window_frame_inner_deep = 23

        self.hook_squisher_taper_length = 20

        self.knob_thick = 10


    def get_bottom_hook(self, short=False):

        #(0,0) will be the top tip of the bottom ledge. left is the window and outside and right is the inside

        #turns out there's some bits on the inside of the window frame, I think to help align the window. to avoid screwing another hole, I'm making
        # a shorter hook to go over that bit

        length = self.hook_squisher_taper_length
        extra_bottom_gap = 5

        if short:
            length = 12.5
            extra_bottom_gap=0


        hook = (cq.Workplane("XY").moveTo(self.window_frame_thick, 0)
                .lineTo(-self.window_frame_rubber_seal_thick_squished, 0)
                #angling a bit more, not sure how easy it will be to slot into window
                .lineTo(-self.window_frame_rubber_seal_thick_unsquished-extra_bottom_gap,-length)
                .lineTo(-self.window_frame_rubber_seal_thick_unsquished-self.hook_thick, -length)
                .lineTo(-self.window_frame_rubber_seal_thick_unsquished-self.hook_thick, self.hook_thick*2)
                .lineTo(self.window_frame_thick, self.hook_thick*2).close().extrude(self.hook_thick))

        # hook = hook.edges().chamfer(1,1)
        hook = hook.edges("|Z").chamfer(1)

        screw = self.fixing_screws.get_cutter().rotate((0,0,0),(0,1,0),90)
        screwcutter = screw.translate((-self.window_frame_rubber_seal_thick_unsquished-self.hook_thick,self.hook_thick/2, self.hook_thick/2)).add(screw.translate((-self.window_frame_rubber_seal_thick_unsquished-self.hook_thick,self.hook_thick*1.5, self.hook_thick/2)))

        hook = hook.cut(screwcutter)

        return hook

    def get_top_hook(self):
        ''' (0,0) will be the bottom tip of the top ledge. left is the window and outside and right is the inside

        plan is this hook will rotate into the top of the window slot. There will be a knob on the inside of the wood. Will rely on glue/self-tapping to keep
        the hook firmly attached to the screw

        TODO get hold of some hex head set screws (and a slot for the nut) then I can be sure the hook will rotate with teh screw

        '''

        top_hook_thick = 8

        hook = (cq.Workplane("XY").moveTo(self.window_frame_thick, 0)
                .lineTo(-self.window_frame_rubber_seal_thick_squished, 0)
                .lineTo(-self.window_frame_rubber_seal_thick_squished - top_hook_thick, 0)
                # .lineTo(-self.window_frame_rubber_seal_thick_squished - top_hook_thick, -self.hook_squisher_taper_length)
                .lineTo(-self.window_frame_rubber_seal_thick_squished - top_hook_thick, self.hook_thick)
                .lineTo(self.window_frame_thick, self.hook_thick).close().extrude(self.hook_thick))
        hook = hook.edges("|Z").chamfer(1)
        #TODO proper radius for the squisher bit (or would a wedge shape be better?)
        #making longer than needed so the filleted ends will be inside the top or chopped off by the containing cylinder
        half_cylinder = (cq.Workplane("XZ").moveTo(-self.window_frame_rubber_seal_thick_squished - top_hook_thick, 0)
                          .lineTo(-self.window_frame_rubber_seal_thick_unsquished, 0)
                          # .radiusArc((-self.window_frame_rubber_seal_thick_squished , self.hook_thick), -self.hook_thick)
                          .lineTo(-self.window_frame_rubber_seal_thick_squished, self.hook_thick*0.3)
                         .lineTo(-self.window_frame_rubber_seal_thick_squished, self.hook_thick * 0.7)
                         .lineTo(-self.window_frame_rubber_seal_thick_unsquished,  self.hook_thick)
                          .lineTo(-self.window_frame_rubber_seal_thick_squished - top_hook_thick, self.hook_thick).close().extrude(self.hook_squisher_taper_length*1.5))

        half_cylinder = half_cylinder.edges(">X").fillet(1.5)
        # return half_cylinder

        containing_cylinder = cq.Workplane("YZ").moveTo(0, self.hook_thick/2).circle(self.hook_squisher_taper_length).extrude(100).translate((-self.window_frame_rubber_seal_thick_squished - top_hook_thick,0))
        # return containing_cylinder
        hook = hook.union(half_cylinder.translate((0,self.hook_squisher_taper_length*0.25)))

        hook = hook.intersect(containing_cylinder)

        screw = self.fixing_screws.get_cutter(self_tapping=True).rotate((0, 0, 0), (0, 1, 0), 90)
        screwcutter = screw.translate((-self.window_frame_rubber_seal_thick_squished - top_hook_thick, self.hook_thick / 2, self.hook_thick / 2))

        hook = hook.cut(screwcutter)

        return hook

    def get_top_knob(self):

        radius = 20

        knob = cq.Workplane("XY").circle(radius).extrude(self.knob_thick)

        knibs = 20
        knib_r = radius/20

        for knib in range(knibs):
            angle = knib*math.pi*2/knibs
            knob = knob.union(cq.Workplane("XY").circle(knib_r).extrude(self.knob_thick).translate(polar(angle, radius - knib_r*0.2)))

        #not working
        # knob = knob.edges(">Z").chamfer(0.1)
        # knob = knob.edges(">Z").fillet(0.1)
        
        chamfer = 0.8
        manual_chamfer_cone = cq.Solid.makeCone(radius + knib_r*chamfer, radius2=radius - knib_r*chamfer, height=knib_r*chamfer*2)
        manual_chamfer = cq.Workplane("XY").circle(radius + knib_r*chamfer).extrude(self.knob_thick - knib_r*chamfer*1.5).union(manual_chamfer_cone.translate((0,0,self.knob_thick - knib_r*chamfer*1.5)))
        # return manual_chamfer
        knob = knob.intersect(manual_chamfer)

        knob = knob.cut(self.fixing_screws.get_cutter(self_tapping=True, ignore_head=True))
        knob = knob.cut(self.fixing_screws.get_nut_cutter(with_bridging=True))

        return knob

class AirconWindowFixing:
    #diameter inside lip is 121
    #lip thick of 1mm was the right measurement, but it didn't fit without a lot of filing and it's still a tight squeeze
    def __init__(self, inner_diameter=122, lip_thick=0.5, lip_deep=3.5, screw_pos_radius=140/2):
        self.inner_diameter =inner_diameter
        self.lip_thick = lip_thick

        self.depth = 10

        self.lip_deep = lip_deep

        self.wall_thick=2.4
        self.rim_wide = (screw_pos_radius - (inner_diameter/2 + self.wall_thick))*2
        self.rim_thick = 2.4

        self.screw_pos_radius = screw_pos_radius

        self.screws = 4
        self.screwhole_d = 3

    def get_fixing(self):
        fixing = cq.Workplane("XY").circle(self.inner_diameter/2 + self.wall_thick + self.rim_wide).circle(self.inner_diameter/2).extrude(self.rim_thick)

        fixing = fixing.union(cq.Workplane("XY").circle(self.inner_diameter/2 + self.wall_thick).circle(self.inner_diameter/2).extrude(self.depth))

        circle = cq.Workplane("XY").circle(self.inner_diameter/2)
        lip = cq.Workplane("XZ").moveTo(self.inner_diameter/2, self.lip_deep).lineTo(self.inner_diameter/2 - self.lip_thick, self.lip_deep + self.lip_thick).line(0, self.lip_thick/3).line(self.lip_thick, self.lip_thick/3).close().sweep(
            circle)


        fixing = fixing.union(lip)

        for screw in range(self.screws):
            angle = screw * math.pi*2/self.screws
            fixing = fixing.cut(cq.Workplane("XY").circle(self.screwhole_d/2).extrude(self.rim_thick).translate(polar(angle,self.screw_pos_radius)))


        return fixing

# ducting = Ducting(screw=MachineScrew(4, countersunk=True))

# show_object(ducting.get_fan_fixing())
# show_object(ducting.get_flat_surface_fixing().translate((120,120,0)))
# show_object(ducting.get_fan_fixing_template().translate((-120,-120,0)))

# windowVent = WindowVent()
#
# show_object(windowVent.get_handle(foldupable=True), options={"color": Colour.RED, "alpha":0.1}, name="handle")
# show_object(windowVent.get_pad())
# show_object(windowVent.get_handle_holder())
# show_object(windowVent.get_knob().translate((0, windowVent.handle_length, windowVent.holder_thick)))



# new_window_vent = WindowVentImproved()
#
# show_object(new_window_vent.get_bottom_hook(short=True))
# show_object(new_window_vent.get_top_hook().translate((0, 200)))
# show_object(new_window_vent.get_top_knob().rotate((0,0,0),(0,1,0),90).translate((new_window_vent.window_frame_thick+new_window_vent.wood_thick, 200+new_window_vent.hook_thick/2, new_window_vent.hook_thick/2)))

airconvent = AirconWindowFixing()

show_object(airconvent.get_fixing())

if outputSTL:
    path = "out"
    name="duct_fixing"
    export_STL(airconvent.get_fixing(), "aircon_vent", name, path, tolerance=0.01)
    # export_STL(new_window_vent.get_bottom_hook(),"bottom_hook", name, path)
    # export_STL(new_window_vent.get_bottom_hook(short=True), "bottom_hook_short", name, path)
    # export_STL(new_window_vent.get_top_hook(), "top_hook", name, path)
    # export_STL(new_window_vent.get_top_knob(), "top_knob", name, path)
    # out = os.path.join(path, "{}.stl".format(name))
    # print("Outputting ", out)
    # exporters.export(ducting.get_flat_surface_fixing(), out)
    #
    # name = "duct_fan_fixing"
    # out = os.path.join(path, "{}.stl".format(name))
    # print("Outputting ", out)
    # exporters.export(ducting.get_fan_fixing(), out)
    #
    # name = "duct_fan_fixing_template"
    # out = os.path.join(path, "{}.stl".format(name))
    # print("Outputting ", out)
    # exporters.export(ducting.get_fan_fixing_template(), out)
    #
    # name = "window_fixing_left"
    # out = os.path.join(path, "{}.stl".format(name))
    # print("Outputting ", out)
    # exporters.export(windowVent.get_corner_holder(left=True), out)
    #
    # name = "window_fixing_right"
    # out = os.path.join(path, "{}.stl".format(name))
    # print("Outputting ", out)
    # exporters.export(windowVent.get_corner_holder(left=False), out)
    #
    # name = "window_fixing_handle"
    # out = os.path.join(path, "{}.stl".format(name))
    # print("Outputting ", out)
    # exporters.export(windowVent.get_handle(), out)
    #
    # name = "window_fixing_handle_foldupable"
    # out = os.path.join(path, "{}.stl".format(name))
    # print("Outputting ", out)
    # exporters.export(windowVent.get_handle(foldupable=True), out)
    #
    # name = "window_fixing_pad"
    # out = os.path.join(path, "{}.stl".format(name))
    # print("Outputting ", out)
    # exporters.export(windowVent.get_pad(), out)
    #
    # name = "window_fixing_handle_holder"
    # out = os.path.join(path, "{}.stl".format(name))
    # print("Outputting ", out)
    # exporters.export(windowVent.get_handle_holder(), out)