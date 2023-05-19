'''
Copyright Luke Wallin 2023

This source describes Open Hardware and is licensed under the CERN-OHL-S v2.

You may redistribute and modify this source and make products using it under
the terms of the CERN-OHL-S v2 or any later version (https://ohwr.org/cern_ohl_s_v2.txt).

This source is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY,
INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A
PARTICULAR PURPOSE. Please see the CERN-OHL-S v2 for applicable conditions.

Source location: https://github.com/MrBunsy/3DPrintedClocks

As per CERN-OHL-S v2 section 4, should you produce hardware based on this
source, You must where practicable maintain the Source Location visible
on the external case of the clock or other products you make using this
source.
'''
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

def pendulum_rod(max_length=170, hook_type="normal", fixing="simple", normal_hook_width = 5.5):
    '''

    :param length: aprox lenght from tip of rod to bob
    :param max_length: max length bob could be adjusted down
    :param hook_type: how the rod fixes to the pendulum leader ("normal" or "toy")
    :param fixing: How the bob fixes to the rod. Simple is slide-friction fit, thread is an attempt at a mantle-style pendulum adjustment
    :return:
    '''


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

def toy_back(width=88,length=120, edge_thick=2.2,inner_width=82,hole_d=10):
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

def back(width=110, height=114.75, lip_thick=1.9,thick=7.5,hole_d=20,hole_y=45,gongholder_width=13,gongholder_height=29.8,gongholder_d=2):

    lip_length=2.25
    #gong stuff very specific for now
    gong_pos=[hole_d/2+gongholder_width/2,hole_y-height/2]
    gong_bit_width=0.8
    # back = cq.Workplane("XY").rect(width, height).extrude(thick).moveTo(0, -height / 2 + hole_y).circle(hole_d / 2). \
    #     moveTo(gong_pos[0], gong_pos[1]).move(-gongholder_width / 2, gongholder_height / 2).rect(gong_bit_width, 2).move(gongholder_width, 0). \
    #     rect(gong_bit_width, 2).move(0, -gongholder_height).rect(gong_bit_width, 1.8).move(-gongholder_width, 0).rect(gong_bit_width, 1.8)  # .cutThruAll()
    back = cq.Workplane("XY").rect(width,height).extrude(thick).moveTo(0,-height/2+hole_y).circle(hole_d/2).cutThruAll()
        # .\
    back= back.moveTo(gong_pos[0]-gongholder_width/2,gong_pos[1]+gongholder_height/2).rect(gong_bit_width,2).cutThruAll()#
    back = back.moveTo(gong_pos[0]+gongholder_width/2,gong_pos[1]+gongholder_height/2).rect(gong_bit_width,2).cutThruAll()
    back = back.moveTo(gong_pos[0]+gongholder_width/2,gong_pos[1]-gongholder_height/2).rect(gong_bit_width,1.8).cutThruAll()
    back = back.moveTo(gong_pos[0]-gongholder_width/2,gong_pos[1]-gongholder_height/2).rect(gong_bit_width,1.8).cutThruAll()#.cutThruAll()

    back = back.faces("<Y").workplane().move(0,lip_thick/2).rect(width,lip_thick).extrude(lip_length)

    return back


def roman_numerals(number, height, workplane=None, thick=0.4, invert=False):
    if workplane is None:
        workplane = cq.Workplane("XY")
    width = height * 0.1
    #I changed the width later.. bodge
    width_for_calcs = height*0.15
    end_tip_height = width_for_calcs * 0.5
    # the sticky out bits
    diamond_width = width_for_calcs * 2.5#2#1.75
    diamond_height = width_for_calcs * 1#0.75
    #instead of a point, end in a blunt bit this tall
    # diamond_thinnest = diamond_height*0.1
    v_top_width = width_for_calcs * 3#2.5
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

    if invert:
        workplane = workplane.rotate((0,0,0), (0,1,0),180).translate((0,0,thick))

    return workplane

def dial(diameter=62, hole_d=7, black=True):
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

class CuckooWhistle:
    '''
    Very much based on teh whistle built in this thread https://mb.nawcc.org/threads/how-to-diy-a-wooden-whistle.97498/

    Thought - could also make one of those train whistles just for fun

    This was one of the first clock-related bits I wrote and is designed for a cuckoo clock, it's not very re-usable as a general purpose whistle (yet)

    '''
    def __init__(self, total_length=65):
        self.total_length=total_length
        self.whistle_top_length=20
        self.body_length = self.total_length - self.whistle_top_length

        self.whistle_wall_thick=3
        self.wall_thick = 3
        self.pipe_width=22
        #taken by generating a trend line from all the commercial sizes of bellows I could find.
        #completely over the top I expect
        self.bellow_length=0.25*total_length + 25
        self.bellow_width = 0.1*total_length + 25
        self.hole_d = 8

        self.bellow_offset=5
        self.bellowTopThick = 9.5
        self.bellowBottomThick = 3.5
        self.bellow_fabric_extra=7
        self.highPitchedShorter=10

        print("bellow width: {} length: {}".format(self.bellow_width,self.bellow_length))

        #TODO - the bellows need to be slightly from the edge, otherwise they'll get caught on teh side of the case!
        #offsetting the hole in the bellow base should be fine

        #TODO measure how much shorter the main chamber needs to be for the second whistle and then both can be printed

    def getBellowBase(self):
        thick = self.bellowBottomThick

        base = cq.Workplane("XY").line(self.bellow_width,0).line(0,self.bellow_length).line(-self.bellow_width,0).close().extrude(thick)
        #hole for the whistle
        base = base.faces(">Z").workplane().moveTo(self.pipe_width/2 - self.bellow_offset,self.pipe_width/2).circle(self.hole_d/2).cutThruAll()
        return base

    def getBellowTop(self):
        thick = self.bellowTopThick
        coin_d = 23
        coin_thick = 3.2

        top = cq.Workplane("XY").tag("base").line(self.bellow_width, 0).line(0, self.bellow_length).line(-self.bellow_width, 0).close().extrude(thick)

        gap = (self.bellow_width-coin_d)/2

        top = top.faces(">Z").workplane().moveTo(self.bellow_width/2, gap+coin_d/2).circle(coin_d/2).cutThruAll()

        top = top.workplaneFromTagged("base").line(self.bellow_width, 0).line(0, self.bellow_length).line(-self.bellow_width, 0).close().extrude(thick-coin_thick)

        return top

    def getWholeWhistle(self, withBase=True, highPitched=False):
        '''

        :param withBase: if False the base of the whistle is oen-ended
        :param highPitched: If True, the whistle chamber is smaller
        :return:
        '''
        whistle = self.getWhistleTop()
        # body
        whistle = whistle.faces(">X").workplane().moveTo(0,-self.pipe_width/2+self.whistle_wall_thick).rect(self.pipe_width,self.pipe_width).rect(self.pipe_width-self.wall_thick*2,self.pipe_width-self.wall_thick*2).extrude(self.body_length)

        if withBase:
            whistle = whistle.faces(">X").workplane()

            if highPitched:
                whistle = whistle.transformed(offset=[0,0,-self.highPitchedShorter])

            whistle = whistle.moveTo(0,-self.pipe_width/2+self.whistle_wall_thick).rect(self.pipe_width,self.pipe_width).extrude(self.whistle_wall_thick)

        # text = "Low (2nd)"
        # if highPitched:
        #     text = "High (1st)"

        #TODO - rotate text for left whistle?
        text = "Left (2nd)"
        if highPitched:
            text = "Right (1st)"
        textoffset = self.highPitchedShorter if highPitched else self.wall_thick/2

        #.moveTo(self.highPitchedShorter, self.wall_thick/2).move(-self.total_length/2,-self.pipe_width/2)
        whistle = whistle.faces("<Y").workplane().transformed(offset=[textoffset-self.total_length/2,self.wall_thick*1.5-self.pipe_width/2]).text(txt=text, fontsize=self.pipe_width*0.6,distance=0.2,cut=False,combine=True)
        # whistle = cq.Workplane("XY").text(txt=text, fontsize=self.pipe_width*0.6,distance=0.2)
        return whistle

    def getBody(self):
        pipe = cq.Workplane("XY").rect(self.pipe_width, self.pipe_width).extrude(self.total_length - self.whistle_top_length)
        pipe = pipe.faces(">Z").workplane().rect(self.pipe_width - self.wall_thick * 2, self.pipe_width - self.wall_thick * 2).cutThruAll()

        #in a pair of old wooden whistles, the differnce in sizes appears to be: 16x21 inner size, height of 4mm

        return pipe

    def getWhistleTop(self):
        wedge_depth=3
        hole_d=self.hole_d
        #0.025"
        wedge_end_thick = 0.6
        #~0.03" the bit that focuses the air onto the wedge
        #0.8 was too big - needs lots of airflow to whistle
        #0.2 is too small - needs a lot of weight to make a noise
        #0.6 works but I think the whistle is too short
        #0.4 sounds promising but needs testing in a clock
        airgap = 0.4#0.4
        #first internal chamber - before the wedge
        chamber_height=3
        exit_gap = 2.3
        #building the whistle on its side, hoping the wedge shape can be printed side-on
        #I drew this side-on so x is the height of the whistle and y is the width of the whistle.

        #just to make the following bit less verbose
        w = self.whistle_top_length
        h=self.pipe_width
        wall = self.whistle_wall_thick

        top=cq.Workplane("XY").rect(w, h).extrude(wall)
        #the wedge
        top = top.faces(">Z").workplane().tag("whistle").moveTo(w/2,h/2).lineTo(-w/2+wall*2+chamber_height+exit_gap,h/2-wedge_depth+wedge_end_thick).\
            line(0,-wedge_end_thick).lineTo(w/2,h/2-wedge_depth).close().extrude(h-wall*2)
        #top cap
        top = top.workplaneFromTagged("whistle").moveTo(-w/2+wall/2,0).rect(wall,h).extrude(h-wall*2)
        #hole in top cap
        #this seems to place us at wall height
        top = top.faces("<X").workplane().moveTo(0,(self.pipe_width-wall*2)/2).circle(hole_d/2).cutThruAll()
        #bit that forces the air over the wedge
        top = top.workplaneFromTagged("whistle").moveTo(-w / 2 + wall, h/2).line(wall+chamber_height,0).line(0,-wedge_depth).line(-(wall+chamber_height),0).close().extrude(h-wall*2)
        #top chamber and other wall
        top = top.workplaneFromTagged("whistle").moveTo(w/2,-h/2).line(-w+wall,0).line(0,wall).line(chamber_height,0).lineTo(-w/2+wall+chamber_height,h/2-wedge_depth-airgap).line(wall,0).lineTo(-w/2+wall*2+chamber_height,-h/2+wall).\
            lineTo(w/2,-h/2+wall).close().extrude(h-wall*2)

        # and the final wall (comment this out to see inside the whistle)
        top = top.faces(">Z").workplane().tag("pretweak").rect(w, h).extrude(wall)
        fudge = 0.5

        #add a ledge so it's easier to line up the bellows
        top = top.faces("<X").workplane().move(0,self.wall_thick-self.pipe_width/2).move(-self.pipe_width/2+self.bellow_offset/2-fudge/2,0).rect(self.bellow_offset-0.5,self.pipe_width).extrude(0.2)

        # top = top.workplaneFromTagged("pretweak")


        return top

    def getBellowsTemplate(self):

        #to improve - make height tiny bit shorter than width of the square in the middle
        #make top and bottom overlap exactly same size as the bellow thickenss to make lining up for gluing easier
        #consider how much extra to allow for overlap on the hinge - do I want rounded?

        #tip of the triangle
        # angle = math.asin((self.bellow_width/2)/self.bellow_length)
        # extra_y = self.bellow_fabric_extra*math.cos(angle)
        # extra_top_x = self.bellow_fabric_extra*math.sin(angle)
        tip_x = math.sqrt(math.pow(self.bellow_length,2) - math.pow(self.bellow_width/2,2)) + self.bellow_width/2
        print("x :{}".format(tip_x))
        # #could work this out properly...
        # extra_x = self.bellow_fabric_extra*3

        # template = cq.Workplane("XY").moveTo(-self.bellow_width/2-extra_top_x,self.bellow_width/2 + extra_y).line(self.bellow_width+extra_top_x*2,0).lineTo(tip_x)

        template = cq.Workplane("XY").moveTo(-self.bellow_width / 2, self.bellow_width / 2 + self.bellow_fabric_extra).line(self.bellow_width, 0).lineTo(tip_x + self.bellow_width * 0.33, 0).\
            lineTo(self.bellow_width / 2, -self.bellow_width / 2 - self.bellow_fabric_extra).line(-self.bellow_width, 0).lineTo(-tip_x - self.bellow_width * 0.4, 0).close().moveTo(0, 0).rect(self.bellow_width, self.bellow_width).extrude(1)

        # template = cq.Workplane("XY").moveTo(-self.bellow_width / 2, self.bellow_width / 2 + self.bellow_fabric_extra).line(self.bellow_width,0).lineTo(tip_x+self.bellow_width*0.33,self.bellow_fabric_extra*0.75).tangentArcPoint([tip_x+self.bellow_width*0.33,-self.bellow_fabric_extra*0.75],relative=False).\
        #     lineTo(self.bellow_width/2,-self.bellow_width/2-self.bellow_fabric_extra).line(-self.bellow_width,0).lineTo(-tip_x-self.bellow_width*0.4,0).close().moveTo(0,0).rect(self.bellow_width,self.bellow_width).extrude(1)

        return template

# if __name__ == "__main__":
#
#     # plate = chain_plate()
# rod = pendulum_rod()
rod_thin_hook = pendulum_rod(normal_hook_width=4.5)
#     # toyrod = pendulum_rod(max_length=150,hook_type="toy")
#     # fixing = pendulum_bob_fixing()
# whistleObj = Whistle()
# whistle=whistleObj.getWholeWhistle()
# whistle_top=whistleObj.getWhistleTop()
# whistle_full_low = whistleObj.getWholeWhistle(True,False)
# whistle_full_high = whistleObj.getWholeWhistle(True,True)
# bellow_base = whistleObj.getBellowBase()
# bellow_top = whistleObj.getBellowTop()
# bellow_template = whistleObj.getBellowsTemplate()

# backObj = back()

musical_back = back(width=109, height=109.75, lip_thick=2,thick=5,hole_d=20,hole_y=45,gongholder_width=12.8,gongholder_height=30)
show_object(musical_back)
# show_object(backObj)

# whistle_top=whistle.getWhistleTop()
#     # toyback = cuckoo_back()
#     # toy_dial = dial()
#     # toy_dial_brown=dial(black=False)
#
#     # num = roman_numerals("VIIIX",10,cq.Workplane("XY"))
#
#     # show_object(plate)
# show_object(rod)
# show_object(rod_thin_hook)
#     # show_object(toyrod)
#     # show_object(fixing)
#     # show_object(whistle.getBody())
#     show_object(whistle_top)
#     # show_object(whistle)
# show_object(whistle_full_high)
# show_object(whistle_full_low)
# show_object(bellow_template)
#     # show_object(bellow_base)
#     # show_object(bellow_top)
#     # show_object(toyback)
#     # show_object(toy_dial[0])
#     # show_object(toy_dial[1])
#     # if len(toy_dial) > 2:
#     #     show_object(toy_dial[2])
#     # show_object(num)
#
#     # exporters.export(plate, "out/cuckoo_chain_plate.stl", tolerance=0.001, angularTolerance=0.01)
#     # exporters.export(rod, "out/cuckoo_pendulum_rod.stl", tolerance=0.001, angularTolerance=0.01)
#     # exporters.export(toyrod, "out/cuckoo_toy_pendulum_rod.stl", tolerance=0.001, angularTolerance=0.01)
#     # exporters.export(fixing, "out/cuckoo_pendulum_fixing.stl", tolerance=0.001, angularTolerance=0.01)
#     # exporters.export(toyback, "out/cuckoo_toy_back.stl", tolerance=0.001, angularTolerance=0.01)
#     # exporters.export(toy_dial, "out/cuckoo_toy_dial.stl", tolerance=0.001, angularTolerance=0.01)
#     # exporters.export(toy_dial[0], "out/cuckoo_toy_dial_brown.stl")#, tolerance=0.001, angularTolerance=0.01)
#     # exporters.export(toy_dial_brown[0], "out/cuckoo_toy_dial_allbrown_brown.stl")#, tolerance=0.001, angularTolerance=0.01)
#     # exporters.export(toy_dial[1], "out/cuckoo_toy_dial_white.stl")#, tolerance=0.001, angularTolerance=0.01)
#     # if len(toy_dial) > 2:
#     #     exporters.export(toy_dial[2], "out/cuckoo_toy_dial_black.stl")  # , tolerance=0.001, angularTolerance=0.01)
#
#     # exporters.export(whistle_top, "out/whistle_top.stl")
#     exporters.export(whistle, "out/whistle.stl")
#     exporters.export(whistle_top, "out/whistle_top.stl")
# exporters.export(whistle_full_low, "../out/whistle_full_low.stl")
# exporters.export(whistle_full_high, "../out/whistle_full_high.stl")
# exporters.export(bellow_template, "../out/bellows_template.stl")
#     exporters.export(bellow_base, "out/bellow_base.stl")
#     exporters.export(bellow_top, "out/bellow_top.stl")

# exporters.export(backObj, "../out/back.stl")
exporters.export(musical_back, "../out/musical_back.stl")
# exporters.export(rod_thin_hook, "../out/cuckoo_pendulum_rod_thin_hook.stl")
