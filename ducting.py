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

    def __init__(self, wood_thick=5, fixing_screws=None, above_window_sticks_out=4):
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

    def get_handle(self):

        ends = [(0,0), (0,self.handle_length)]

        handle = get_stroke_line(ends, wide=self.handle_wide, thick= self.holder_thick)

        # handle = handle.faces(">Z").pushPoints(ends).circle(self.fixing_screws.get_rod_cutter_r(loose=True)).cutThruAll()
        #loose on one end so the handle can rotate, but fixed on the other end as the knob will be the loose bit
        handle = handle.faces(">Z").workplane().moveTo(ends[0][0], ends[0][1]).circle(self.fixing_screws.get_rod_cutter_r(loose=True)).cutThruAll()

        #decided against knob
        # handle = handle.cut(self.fixing_screws.get_cutter(for_tap_die=True).translate(ends[1]))


        return handle
    def get_knob(self):
        '''
        don't think I need a knob after all, just the handle should be enough, like the bits that hold drop-down tables on trains in place
        '''
        knob = cq.Workplane("XY").circle(self.handle_wide/2).circle(self.fixing_screws.get_rod_cutter_r(loose=True)).extrude(self.knob_long)

        #knob is loose, no need for embedding nyloc nut! that can go on the end
        # knob = knob.cut(self.fixing_screws.get_nut_cutter(nyloc=True).translate((0,0,self.knob_long - self.fixing_screws.get_nut_height(nyloc=True))))
        return knob
    def get_handle_pivot(self):
        '''
        bit above the window sticks out a bit, the plywood isn't very thick, so I'm not sure how to do this yet

        IDEA - make the handle thicker on the end, can then keep the pivot as thick as needed
        '''


ducting = Ducting(screw=MachineScrew(4, countersunk=True))

# show_object(ducting.get_fan_fixing())
# show_object(ducting.get_flat_surface_fixing().translate((120,120,0)))
# show_object(ducting.get_fan_fixing_template().translate((-120,-120,0)))

windowVent = WindowVent()

show_object(windowVent.get_handle())
# show_object(windowVent.get_knob().translate((0, windowVent.handle_length, windowVent.holder_thick)))

if outputSTL:
    path = "out"
    name="duct_fixing"
    out = os.path.join(path, "{}.stl".format(name))
    print("Outputting ", out)
    exporters.export(ducting.get_flat_surface_fixing(), out)

    name = "duct_fan_fixing"
    out = os.path.join(path, "{}.stl".format(name))
    print("Outputting ", out)
    exporters.export(ducting.get_fan_fixing(), out)

    name = "duct_fan_fixing_template"
    out = os.path.join(path, "{}.stl".format(name))
    print("Outputting ", out)
    exporters.export(ducting.get_fan_fixing_template(), out)

    name = "window_fixing_left"
    out = os.path.join(path, "{}.stl".format(name))
    print("Outputting ", out)
    exporters.export(windowVent.get_corner_holder(left=True), out)

    name = "window_fixing_right"
    out = os.path.join(path, "{}.stl".format(name))
    print("Outputting ", out)
    exporters.export(windowVent.get_corner_holder(left=False), out)