import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
import sys

if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass


def chain_plate():
    '''
    I cut the chain holes in the wrong place for Frankencuckoo, so now there needs to be something in place to stop the weights falling furtehr than they should
    so this is just a simple new plate to put over the top
    :return:
    '''

    width= 80
    length=40
    thick = 2
    #two centre chains are 1.4cm apart, end two chains are 5.3cm
    chain1=14/2
    chain2=53/2

    chain_d = 8



    return (cq.Workplane("front").box(width, length, thick).pushPoints([(-chain2, 0), (-chain1, 0),(chain1, 0), (chain2, 0)])
    .circle(chain_d/2).cutThruAll())


rod_width = 10
rod_thick = 3.5

def pendulum_rod(max_length=170, hook_type="normal", fixing="simple"):
    '''

    :param length: aprox lenght from tip of rod to bob
    :param max_length: max length bob could be adjusted down
    :param hook_type: how the rod fixes to the pendulum leader ("normal" or "toy")
    :param fixing: How the bob fixes to the rod. Simple is slide-friction fit, thread is an attempt at a mantle-style pendulum adjustment
    :return:
    '''

    normal_hook_width = 5.5
    hook_gap=1.5

    hook_thick = 2
    hook_height=10

    rod = cq.Workplane("XY").tag("base")

    #lieing on its side, x is therefore thickness, z is width and y is height
    #top centre of rod is at 0,0 fixing is +ve y, rest of rod is -ve y

    if fixing == "simple":
        #just a rectangular length
        rod = rod.workplaneFromTagged("base").move(0,-max_length/2).box(rod_thick,max_length,rod_width)
        rod = rod.faces(">X").workplane().transformed(offset=(0,0,-rod_thick)).move(-max_length,rod_width/2).lineTo(-max_length-rod_width/2,0).lineTo(-max_length,-rod_width/2).close().extrude(rod_thick)

    if hook_type == "normal":
        # rod = rod.faces(">Y").workplane().rect(hook_thick,normal_hook_width).extrude(hook_height)
        # rod = rod.faces(">Y").workplane().transformed(offset=cq.Vector(0,0,-hook_thick/2),rotate=cq.Vector(0,130,0)).rect(hook_thick, normal_hook_width).extrude(hook_height/2)

        hook_top_thick = hook_thick * 2 + hook_gap
        rod = rod.workplaneFromTagged("base").transformed(offset=(hook_gap/2,0,(rod_width-normal_hook_width)/2-rod_width/2)).tag("hook_base").moveTo(0,hook_height/2).rect(hook_thick,hook_height).extrude(normal_hook_width)

        rod = rod.workplaneFromTagged("hook_base").moveTo(-hook_top_thick/2+hook_thick/2,hook_height).circle(radius=hook_top_thick/2).extrude(normal_hook_width)

        rod = rod.workplaneFromTagged("hook_base").moveTo(-hook_top_thick / 2 + hook_thick / 2, hook_height-hook_top_thick/4).rect(hook_top_thick,hook_top_thick/2).extrude(normal_hook_width)

        rod = rod.workplaneFromTagged("hook_base").moveTo(-hook_top_thick/2+hook_thick/2,hook_height).circle(radius=hook_gap/2).cutThruAll()
        rod = rod.workplaneFromTagged("hook_base").moveTo(-hook_top_thick / 2 + hook_thick / 2, hook_height - hook_top_thick / 4).rect(hook_gap, hook_top_thick / 2).cutThruAll()
    elif hook_type == "toy":
        hanger_depth = 4
        hanger_width = 2
        hanger_length = 20

        extra_length = hanger_length*2.25

        rod = rod.workplaneFromTagged("base").move(0, extra_length / 2).box(rod_thick, extra_length, rod_width)
        rod = rod.faces(">X").workplane().move(extra_length / 2,0).rect(extra_length, rod_width).extrude(hanger_depth-rod_thick+2)

        cutter = cq.Workplane("ZY").rect(hanger_width,hanger_length*2).extrude(-hanger_depth/2-10)
        cutter = cutter.faces("<X").workplane().move(hanger_length/2).rect(hanger_length,hanger_width).extrude(10)
        # return cutter
        rod = rod.cut(cutter.translate([0,extra_length/2,0]))

    return rod


def pendulum_bob_fixing():
    '''
    Bit that can glue onto the back of a pretty pendulum bob and be used to adjust its height on the pendulum rod
    :return:
    '''

    width = rod_width*1.6
    length = rod_width*2*1.25
    thick = rod_thick*3
    back_thick = 2

    rod_thick_hole = rod_thick+1

    #1.5 was too small for thick wire - but maybe paperclip would be fine?
    wire_hole_d = 1.5

    fixing = cq.Workplane("XY").tag("base")

    fixing = fixing.rect(width,length).extrude(thick)

    wire_z = (thick - (back_thick + rod_thick_hole)) / 2

    fixing = fixing.faces(">Y").workplane().moveTo(0,thick - (back_thick + rod_thick_hole/2)).rect(rod_width+1,rod_thick_hole).cutThruAll()

    fixing = fixing.faces(">Y").workplane().moveTo(0, wire_z).circle(radius=wire_hole_d/2).cutThruAll()

    # fixing = fixing.faces(">X").workplane().moveTo(0,1.7).circle(radius=wire_hole_d / 2).cutThruAll()



    #why is 0,0 suddenly in the corner?
    # fixing = fixing.faces(">X").workplane().moveTo(0, (thick - rod_thick)/4).rect(wire_hole_d,wire_hole_d).cutThruAll()
    fixing = fixing.faces(">X").workplane().moveTo(0.01, wire_z).circle(wire_hole_d*0.6).cutThruAll()
    fixing = fixing.faces(">X").workplane().moveTo(-length,wire_z).circle(wire_hole_d * 0.6).cutThruAll()

    slot = cq.Workplane("XY").box(100,width*0.8,thick)
    # return slot

    fixing = fixing.cut(slot)

    # fixing = cq.selectors.SubtractSelector(fixing,slot)

    return fixing

def cuckoo_back(width=88,length=120, edge_thick=2.2,inner_width=82,hole_d=10):
    '''
    A back for the toy cuckoo , could be adapted easily for a back to a proper cuckoo
    :param width:
    :param length:
    :param edge_thick:
    :param inner_width:
    :param hole_d:
    :return:
    '''

    back = cq.Workplane("XY").rect(width,length).extrude(edge_thick)
    # extra thick
    # back = back.faces(">Z").workplane().rect(inner_width,length).extrude(edge_thick)

    #hole to hang on wall
    back = back.faces(">Z").workplane().moveTo(0,width/2-hole_d).circle(hole_d/2).cutThruAll()

    return back

def roman_numerals(number, height, workplane, thick=0.4):
    width = height * 0.1
    #I changed the width later.. bodge
    width_for_calcs = height*0.15
    end_tip_height = width_for_calcs * 0.5
    # the sticky out bits
    diamond_width = width_for_calcs * 2.5#2#1.75
    diamond_height = width_for_calcs * 1#0.75
    #instead of a point, end in a blunt bit this tall
    # diamond_thinnest = diamond_height*0.1
    v_top_width = width_for_calcs * 2.5
    thin_width = width * 0.75
    thick_width = width*1.1
    widths={}
    widths["I"] = width_for_calcs*1.35# + diamond_width*0.175#0.2
    widths["V"] = (v_top_width-width_for_calcs + diamond_width)*0.8
    widths["X"] = widths["V"]

    def add_diamond(workplane,pos):
        return workplane.moveTo(pos[0],pos[1]).move(0,-diamond_height/2).line(diamond_width/2,diamond_height/2).line(-diamond_width/2,diamond_height/2).line(-diamond_width/2,-diamond_height/2).close().extrude(thick)
    def make_i(workplane):


        i = workplane.tag("numeral_base")
        i = i.moveTo(0,-height/2).line(width/2,end_tip_height).line(0,height-end_tip_height*2).line(-width/2,end_tip_height).line(-width/2,-end_tip_height).line(0,-(height-end_tip_height*2)).close().extrude(thick)
        for j in range(3):
            i = add_diamond(i.workplaneFromTagged("numeral_base"),(0,j*(height/2-end_tip_height)-height/2+end_tip_height))
        return i


    def make_v(workplane):
        v = workplane.tag("numeral_base")


        #left stroke
        v = v.moveTo(0,-height/2).line(thick_width/2,end_tip_height).lineTo(-v_top_width/2+thick_width,height/2-end_tip_height).line(-width/2,end_tip_height).line(-width/2,-end_tip_height).lineTo(-width/2,-height/2+end_tip_height).close().extrude(thick)
        #right stroke
        v = v.workplaneFromTagged("numeral_base").moveTo(width/2,-height/2+end_tip_height).lineTo(v_top_width/2,height/2-end_tip_height).line(-width/2,end_tip_height).line(-width/2,-end_tip_height).lineTo(v_top_width/2-thin_width,height/2-end_tip_height).lineTo(width/2-thin_width,-height/2+end_tip_height).close().extrude(thick)

        #diamonds
        diamond_positions=[
            #(0,-height/2+end_tip_height),
                           (-v_top_width/2+width/2,height/2-end_tip_height),
                           (v_top_width/2-width/2,height/2-end_tip_height),
                           ((-v_top_width/2+width/2)*0.75,0),
                           (-(-v_top_width/2+width/2)*0.75,0)]
        for pos in diamond_positions:
            v = add_diamond(v.workplaneFromTagged("numeral_base"), pos)
        bottom_diamond_half_width = v_top_width/2-width/2+diamond_width/2
        v = v.workplaneFromTagged("numeral_base").moveTo(0,-height/2+end_tip_height-diamond_height/2).line(bottom_diamond_half_width,diamond_height/2).line(-bottom_diamond_half_width,diamond_height/2)\
        .line(-diamond_width/2,-diamond_height/2).line(diamond_width/2,-diamond_height/2).close().extrude(thick)

        return v

    def make_x(workplane):
        x = workplane.tag("numeral_base")
        # thick stroke
        x = x.moveTo(v_top_width/2-width/2, -height / 2).line(width / 2, end_tip_height).lineTo(-v_top_width / 2 + width, height / 2 - end_tip_height).line(-width / 2, end_tip_height).line(-width / 2, -end_tip_height).\
            lineTo(v_top_width/2-width,-height / 2 + end_tip_height).close().extrude(thick)
        # thin stroke
        x = x.workplaneFromTagged("numeral_base").moveTo(-v_top_width/2+thin_width, -height / 2 + end_tip_height).lineTo(v_top_width / 2, height / 2 - end_tip_height).line(-width / 2, end_tip_height).line(-width / 2, -end_tip_height).\
            lineTo(v_top_width / 2 - thin_width, height / 2 - end_tip_height).lineTo(-v_top_width/2, -height / 2 + end_tip_height).line(width/2,-end_tip_height).line(width/2,end_tip_height).close().extrude(thick)

        diamond_positions=[(0,0), (v_top_width/2-width/2,height/2-end_tip_height)
                           , ((v_top_width/2-width/2),-(height/2-end_tip_height))
                           , (-(v_top_width/2-width/2),(height/2-end_tip_height))
                           , (-(v_top_width/2-width/2),-(height/2-end_tip_height))]
        for pos in diamond_positions:
            x = add_diamond(x.workplaneFromTagged("numeral_base"), pos)

        return x

    makes = {}
    makes["I"]=make_i
    makes["V"]=make_v
    makes["X"]=make_x

    total_width=0
    for char in number:
        total_width+=widths[char]
    for char in number:
        thiswidth=widths[char]
        workplane = makes[char](workplane.transformed(offset=(thiswidth/2,0))).translate((-thiswidth/2,0))
    return workplane

def dial(diameter=60, hole_d=7, black=True):
    radius = diameter/2
    inner_radius= radius*0.575
    base_thick = 2
    edge_thick=2
    # dial = cq.Workplane("XY").circle(diameter/2).extrude(base_thick)
    # fontsize = diameter*0.13
    fontsize = ((radius - edge_thick) - inner_radius)*0.8
    #fontY = -radius + fontsize*0.9
    fontY = -((radius - edge_thick + inner_radius)/2 )
    fontThick = 0.4
    blackThick = 0.4
    # dial.faces(">Z").workplane().tag("numbers_base")
    thick_ridge1 = 0.3
    thick_ridge2=0.4

    circle = cq.Workplane("XY").circle(radius)
    dial = cq.Workplane("XZ").moveTo(hole_d/2,0).lineTo(radius,0).line(0,base_thick*0.5).line(-edge_thick*0.5,base_thick).tangentArcPoint((radius-edge_thick,base_thick),relative=False).\
        lineTo(inner_radius,base_thick).tangentArcPoint((-base_thick*0.25,base_thick*0.25),relative=True).tangentArcPoint((-base_thick*0.25,base_thick*0.25),relative=True).\
        line(-base_thick*0.5,0).tangentArcPoint((-base_thick*0.25,-base_thick*0.25),relative=True).tangentArcPoint((-base_thick*0.25,-base_thick*0.25),relative=True).\
        line(-base_thick*0.25,0).tangentArcPoint((-base_thick*0.25,base_thick*0.25),relative=True).tangentArcPoint((-base_thick*0.25,base_thick*0.25),relative=True).\
        line(-base_thick*0.4,0).tangentArcPoint((-base_thick * thick_ridge1, -base_thick * thick_ridge1), relative=True).tangentArcPoint((-base_thick * thick_ridge2, -base_thick * thick_ridge2), relative=True). \
        tangentArcPoint((-base_thick * thick_ridge2, base_thick * thick_ridge2), relative=True).tangentArcPoint((-base_thick * thick_ridge1, base_thick * thick_ridge1), relative=True). \
        line(-base_thick*0.5,0).tangentArcPoint((-base_thick * 0.25, -base_thick * 0.25), relative=True).tangentArcPoint((-base_thick * 0.25, -base_thick * 0.25), relative=True). \
        tangentArcPoint((-base_thick * 0.25, base_thick * 0.25), relative=True).tangentArcPoint((-base_thick * 0.25, base_thick * 0.25), relative=True). \
        line(-base_thick * 0.3, 0).tangentArcPoint((-base_thick * 0.125, -base_thick * 0.125), relative=True).tangentArcPoint((-base_thick * 0.125, -base_thick * 0.125), relative=True). \
        lineTo(hole_d/2,base_thick*1.25).lineTo(hole_d/2,0).close().sweep(circle)

    numberscqs = []
    numbers = ["XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
    for i,num in enumerate(numbers):
        angleRads = -i*(math.pi*2/12)-math.pi/2
        fontAngleDegs = 360*angleRads/(math.pi*2)+90

        numcq = roman_numerals(num, fontsize,cq.Workplane("XY"), fontThick).rotate((0,0,0),(0,0,1),fontAngleDegs).translate((math.cos(angleRads)*fontY,math.sin(angleRads)*fontY, base_thick))
        numberscqs.append(numcq)

    numberscq_base = numberscqs[0]
    for i in range(1,len(numberscqs)):
        numberscq_base = numberscq_base.add(numberscqs[i])



    out =  [dial, numberscq_base]

    if black:
        blackDisc = cq.Workplane("XY").transformed(offset=(0,0,base_thick-blackThick)).circle(radius-edge_thick).extrude(blackThick).circle(inner_radius).cutThruAll()
        out.append(blackDisc)
        dial = dial.cut(blackDisc)
        out[0] = dial

    return out

class Whistle():

    def __init__(self, total_length=70):
        self.total_length=total_length
        self.whistle_top_length=23
        self.wall_thick=2
        self.pipe_width=24

    def getBody(self):
        pipe = cq.Workplane("XY").rect(self.pipe_width, self.pipe_width).extrude(self.total_length - self.whistle_top_length)
        pipe = pipe.faces(">Z").workplane().rect(self.pipe_width - self.wall_thick * 2, self.pipe_width - self.wall_thick * 2).cutThruAll()

        return pipe

    def getWhistleTop(self):
        top=cq.Workplane("XY").rect(self.pipe_width, self.pipe_width).extrude(self.whistle_top_length)


# plate = chain_plate()
# rod = pendulum_rod()
# toyrod = pendulum_rod(max_length=150,hook_type="toy")
# fixing = pendulum_bob_fixing()
# whistle = Whistle()
# toyback = cuckoo_back()
toy_dial = dial()
toy_dial_brown=dial(black=False)

# num = roman_numerals("VIIIX",10,cq.Workplane("XY"))

# show_object(plate)
# show_object(rod)
# show_object(toyrod)
# show_object(fixing)
# show_object(whistle.getBody())
# show_object(toyback)
show_object(toy_dial[0])
show_object(toy_dial[1])
if len(toy_dial) > 2:
    show_object(toy_dial[2])
# show_object(num)

# exporters.export(plate, "out/cuckoo_chain_plate.stl", tolerance=0.001, angularTolerance=0.01)
# exporters.export(rod, "out/cuckoo_pendulum_rod.stl", tolerance=0.001, angularTolerance=0.01)
# exporters.export(toyrod, "out/cuckoo_toy_pendulum_rod.stl", tolerance=0.001, angularTolerance=0.01)
# exporters.export(fixing, "out/cuckoo_pendulum_fixing.stl", tolerance=0.001, angularTolerance=0.01)
# exporters.export(toyback, "out/cuckoo_toy_back.stl", tolerance=0.001, angularTolerance=0.01)
# exporters.export(toy_dial, "out/cuckoo_toy_dial.stl", tolerance=0.001, angularTolerance=0.01)
exporters.export(toy_dial[0], "out/cuckoo_toy_dial_brown.stl")#, tolerance=0.001, angularTolerance=0.01)
exporters.export(toy_dial_brown[0], "out/cuckoo_toy_dial_allbrown_brown.stl")#, tolerance=0.001, angularTolerance=0.01)
exporters.export(toy_dial[1], "out/cuckoo_toy_dial_white.stl")#, tolerance=0.001, angularTolerance=0.01)
if len(toy_dial) > 2:
    exporters.export(toy_dial[2], "out/cuckoo_toy_dial_black.stl")  # , tolerance=0.001, angularTolerance=0.01)