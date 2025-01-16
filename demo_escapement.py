from clocks import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

class AnchorDemo:
    '''
    Fix together with screws through the loose holes in the plate, with a nut on the front side to hold it tight
    half nut for the anchor, whole nut for the wheel to try and line them up nicely
    '''


    def __init__(self, escapement=None, diameter=120, anchor_thick=14, wheel_thick=8, screw=None, type=EscapementType.DEADBEAT, with_pendulum_rod=False):
        self.escapement = escapement
        self.screw = screw

        #25mm pan head screwed from front to hold escape wheel, 40mm countersunk screwed from back with dome nut to hold anchor
        self.plate_thick = 8
        self.arbor_long = 14.5
        self.pendulum_rod_thick = 4
        self.pendulum_sticks_out = 10
        self.with_pendulum_rod = with_pendulum_rod
        #extend anchor to minimum of arbor_long? - using this to fiddle exact screw lengths
        self.extend_anchor = False


        if self.screw is None:
            self.screw = MachineScrew(3, countersunk=True)

        if self.escapement is None:
            #exagerating lock slightly, as printing the anchor with a 0.6 nozzle rounds the corners a bit too much
            self.escapement = AnchorEscapement.get_with_optimal_pallets(diameter=diameter, anchor_thick=anchor_thick, wheel_thick=wheel_thick, type=type, lock_deg=4)

        #make sure it pritns with the right dimensions with a 0.6mm nozzle
        self.escapement.tooth_tip_width=1.5
        self.escapement.arbor_d=self.screw.metric_thread
        self.plate_wide = max(self.escapement.diameter * 0.1, self.screw.get_head_diameter() + 1)
        self.square_wide = self.plate_wide*0.8

        self.pendulum_rod_long = self.escapement.anchor_centre_distance + self.escapement.diameter * 0.75
        self.pendulum_rod_base_thick = 1


    def get_anchor(self):



        anchor = self.escapement.get_anchor()

        if self.extend_anchor:
            if self.with_pendulum_rod:
                arbor_long = self.arbor_long + self.pendulum_sticks_out - self.pendulum_rod_thick + self.pendulum_rod_base_thick
            else:
                arbor_long = self.arbor_long
            anchor = anchor.union(self.get_arbor_beefer_upper(arbor_long))

        if self.with_pendulum_rod:
            #square bit to hold pendulum rod
            square = cq.Workplane("XY").rect(self.square_wide, self.square_wide).circle(self.screw.metric_thread/2).extrude(self.arbor_long+self.pendulum_sticks_out)
            square = square.intersect(self.get_arbor_beefer_upper(self.arbor_long+self.pendulum_sticks_out))
            anchor = anchor.union(square)

        return anchor

    def get_pendulum_rod(self):



        rod=cq.Workplane("XY").rect(self.plate_wide, self.pendulum_rod_long).extrude(self.pendulum_rod_thick).translate((0, self.escapement.anchor_centre_distance - self.pendulum_rod_long / 2 + self.plate_wide / 2))
        rod = rod.union(cq.Workplane("XY").circle(self.plate_wide*0.75).extrude(self.pendulum_rod_thick).translate((0,self.escapement.anchor_centre_distance)))
        rod = rod.edges("|Z").fillet(3)

        rod = rod.faces(">Z").workplane().moveTo(0, self.escapement.anchor_centre_distance).circle(self.screw.metric_thread/2).cutThruAll()
        rod = rod.cut(cq.Workplane("XY").moveTo(0, self.escapement.anchor_centre_distance).rect(self.square_wide+0.2, self.square_wide+0.2).extrude(self.pendulum_rod_thick - self.pendulum_rod_base_thick))

        return rod
    def get_arbor_beefer_upper(self, long = -1):
        if long < 0:
            long = self.arbor_long
        return cq.Workplane("XY").circle(self.plate_wide/2).circle(self.screw.metric_thread/2).extrude(long)

    def get_escape_wheel(self):
        wheel = self.escapement.get_wheel().faces(">Z").workplane().circle(self.screw.metric_thread/2).cutThruAll()

        wheel = Gear.cutStyle(wheel, innerRadius=self.screw.metric_thread+8, outerRadius=self.escapement.get_wheel_inner_r(), style=GearStyle.ROUNDED_ARMS5)

        wheel = wheel.translate((0,0,self.arbor_long - self.escapement.wheel_thick)).union(self.get_arbor_beefer_upper())


        return wheel

    def get_plate(self):

        extra_length = 40
        width = self.plate_wide

        total_length = self.escapement.anchor_centre_distance + width/2 + extra_length

        plate = cq.Workplane("XY").rect(width, total_length).extrude(self.plate_thick).translate((0, total_length/2 - width/2))

        plate = plate.edges("|Z").fillet(width/3)
        screwed_from_back = [False, True]

        for i,pos in enumerate([(0,0), (0,self.escapement.anchor_centre_distance)]):
            if screwed_from_back[i]:
                plate = plate.cut(self.screw.get_cutter(loose=True).translate(pos))
            else:
                plate = plate.faces(">Z").moveTo(pos[0], pos[1]).circle(self.screw.get_rod_cutter_r(loose=True)).cutThruAll()
                plate = plate.cut(self.screw.get_nut_cutter().translate(pos))


        for pos in [(0,total_length-width), (0, self.escapement.diameter/2 + width/2)]:
            plate = plate.cut(self.screw.get_cutter(loose=True).rotate((0,0,0),(1,0,0),180).translate((0,0,self.plate_thick)).translate(pos))

        return plate

    def get_anchor_thick(self):
        if self.extend_anchor:
            return max(self.arbor_long, self.escapement.anchor_thick)
        else:
            return self.escapement.anchor_thick

    def get_assembled(self):
        anchor_z_offset = self.screw.get_nut_height(half=False)*2
        escape_z_offset = self.screw.get_nut_height(half=True)
        # anchor_half_nut = False
        # escape_half_nut = True
        assembly = self.get_anchor().translate((0,self.escapement.anchor_centre_distance, anchor_z_offset))
        assembly = assembly.add(self.get_escape_wheel().translate((0,0, escape_z_offset)))

        assembly = assembly.translate((0,0,self.plate_thick)).add(self.get_plate())
        if self.with_pendulum_rod:
            assembly = assembly.add(self.get_pendulum_rod().translate((0,0,self.plate_thick + anchor_z_offset+ self.arbor_long+self.pendulum_sticks_out - self.pendulum_rod_thick + self.pendulum_rod_base_thick)))

        base_of_pendulum_rod = anchor_z_offset + self.arbor_long+self.pendulum_sticks_out - self.pendulum_rod_thick + self.pendulum_rod_base_thick
        top_of_escape_wheel_arbor = escape_z_offset + self.arbor_long
        print(f"top of escape wheel arbor: {top_of_escape_wheel_arbor} base of pendulum rod: {base_of_pendulum_rod}, gap: {base_of_pendulum_rod - top_of_escape_wheel_arbor}")
        #countersunk from bottom with dome nut on top:
        dome_nut_removes = 3
        # print(f"length of screw for escape wheel = {top_of_escape_wheel_arbor + dome_nut_removes + self.plate_thick}")
        if self.with_pendulum_rod:
            anchor_screw_length = self.plate_thick + anchor_z_offset + self.arbor_long + self.pendulum_sticks_out + self.pendulum_rod_base_thick + dome_nut_removes
        else:
            anchor_screw_length = self.plate_thick + anchor_z_offset + self.get_anchor_thick() + dome_nut_removes
        escape_screw_length = top_of_escape_wheel_arbor  + self.plate_thick
        print(f"length of screw for anchor = {anchor_screw_length}")
        #pan head from top with nut in the bottom of the plate and front of plate
        print(f"length of screw for escape wheel = {escape_screw_length}")
        # print(f"length of screw for anchor = {self.plate_thick + self.screw.get_nut_height(half=True) + self.arbor_long + self.pendulum_sticks_out + self.pendulum_rod_base_thick }")

        assembly.add(cq.Workplane("XY").moveTo(0, self.escapement.anchor_centre_distance).circle(self.screw.metric_thread*0.4).extrude(anchor_screw_length))
        assembly.add(cq.Workplane("XY").moveTo(0, 0).circle(self.screw.metric_thread * 0.4).extrude(escape_screw_length))

        return assembly

    def output_STLs(self, path="out/"):
        name= "escapement_demo"
        export_STL(self.get_anchor(), "anchor", name, path, tolerance=0.01)
        export_STL(self.get_escape_wheel(), "escape_wheel", name,  path)
        export_STL(self.get_plate(), "plate", name, path)
        if self.with_pendulum_rod:
            export_STL(self.get_pendulum_rod(), "pendulum_rod", name, path)


demo = AnchorDemo(type=EscapementType.RECOIL)

# show_object(get_gear_demo(just_style=GearStyle.DIAMONDS))
show_object(demo.get_assembled())
if outputSTL:
    demo.output_STLs()
# show_object(getGearDemo())
# # show_object(getHandDemo(assembled=True, chunky=True).translate((0,400,0)))
# show_hand_demo(show_object, outline=1, length=200*0.45)