from clocks import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass

class AnchorDemo:
    def __init__(self, escapement=None, diameter=120, anchor_thick=8, wheel_thick=8, screw=None, type=EscapementType.DEADBEAT):
        self.escapement = escapement
        self.screw = screw

        #should nicely fit a 30mm screw with dome nut tightly on the end
        self.plate_thick = 8
        self.arbor_long = 18

        if self.screw is None:
            self.screw = MachineScrew(3, countersunk=True)

        if self.escapement is None:
            self.escapement = AnchorEscapement.get_with_45deg_pallets(diameter=diameter, anchor_thick=anchor_thick, wheel_thick=wheel_thick, type=type)

        self.escapement.arbor_d=self.screw.metric_thread

    def get_anchor(self):
        return self.escapement.get_anchor().union(self.get_arbor_beefer_upper())

    def get_arbor_beefer_upper(self):
        return cq.Workplane("XY").circle(self.screw.metric_thread*2).circle(self.screw.metric_thread/2).extrude(self.arbor_long)

    def get_escape_wheel(self):
        wheel = self.escapement.get_wheel().faces(">Z").workplane().circle(self.screw.metric_thread/2).cutThruAll()

        wheel = Gear.cutStyle(wheel, innerRadius=self.screw.metric_thread+8, outerRadius=self.escapement.get_wheel_inner_r(), style=GearStyle.ROUNDED_ARMS5)

        wheel = wheel.union(self.get_arbor_beefer_upper())


        return wheel

    def get_plate(self):

        extra_length = 40
        width = max(self.escapement.diameter*0.1, self.screw.get_head_diameter()+1)
        total_length = self.escapement.anchor_centre_distance + width/2 + extra_length

        plate = cq.Workplane("XY").rect(width, total_length).extrude(self.plate_thick).translate((0, total_length/2 - width/2))

        plate = plate.edges("|Z").fillet(width/3)

        for pos in [(0,0), (0,self.escapement.anchor_centre_distance)]:
            plate = plate.cut(self.screw.get_cutter(for_tap_die=True).translate(pos))

        for pos in [(0,total_length-width), (0, self.escapement.diameter/2 + width/2)]:
            plate = plate.cut(self.screw.get_cutter(for_tap_die=True).rotate((0,0,0),(1,0,0),180).translate((0,0,self.plate_thick)).translate(pos))

        return plate


    def get_assembled(self):
        assembly = self.get_anchor().translate((0,self.escapement.anchor_centre_distance)).add(self.get_escape_wheel())

        assembly = assembly.translate((0,0,self.plate_thick)).add(self.get_plate())

        return assembly

    def output_STLs(self, path="out/"):
        name= "escapement_demo"
        export_STL(self.get_anchor(), "anchor", name, path, tolerance=0.01)
        export_STL(self.get_escape_wheel(), "escape_wheel", name,  path)
        export_STL(self.get_plate(), "plate", name, path)


demo = AnchorDemo(type=EscapementType.DEADBEAT)

# show_object(get_gear_demo(just_style=GearStyle.DIAMONDS))
show_object(demo.get_assembled())
if outputSTL:
    demo.output_STLs()
# show_object(getGearDemo())
# # show_object(getHandDemo(assembled=True, chunky=True).translate((0,400,0)))
# show_hand_demo(show_object, outline=1, length=200*0.45)