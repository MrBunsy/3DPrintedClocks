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
import math
from .utility import *

class Rack:
    '''
    designed to be paired with a snail

    Copying Smiths - the pin that rests on the snail is part way along the arm
    '''

    def __init__(self, snail=None, hinge_to_snail=50, fixingScrew=None):

        self.snail = snail

        if self.snail is None:
            self.snail = Snail()

        if fixingScrew is None:
            fixingScrew = MachineScrew(3)
        self.fixingScrew = fixingScrew

        #distance from the hinge of the rack to the centre of the snail
        self.hinge_to_snail = hinge_to_snail
        #specifically, where the gathering pallet pin will be when closest to the hinge
        self.hinge_to_rack = self.hinge_to_snail + self.snail.maxR*1.5

        # since 1 o'clock is maxR, we always need to add one more
        self.snail_per_strike = (self.snail.maxR - self.snail.minR) / 11

        self.angle_per_strike = self.snail_per_strike / self.hinge_to_snail

        self.tip_thick = 1

        self.arm_wide = 2.4
        self.arm_thick = 2.4

        self.hinge_thick = 15

        #have more ratchet than needed, in case the rack ever falls down beside the snail
        self.max_strikes = 13

        self.ratchet_angle = math.pi/4

        '''
        relative to the arm, so if this is zero the bottom of the rack is at the end of the arm, if this is one the top of the rack is at the end of teh arm
        
        0:
        <
        <
        <
        <----------------O
        
        1:
        <----------------O
        <
        <
        <
        <
        
        since I'm not quite sure which is going to be needed yet, this is going to stay flexible
        
        '''
        self.rack_starts_at=0


    def getSprungSnailTip(self):
        '''
        Get the bit that will rest on the snail - this is a separate piece so it can be sprung and thus cope with hands being wound backwards or the strike not being powered

        can this be printed as part of the rack?
        Yes I think it can - if it can jut be a thin vertical bit, it'll bend easily left and right, but notvertically - but will this result in an inconsistent drop?
        I'm wondering if I can just make this bit sacraficial? Or if it's strong enough, then the clock will stop if the strike doesn't work?
        '''

    def getRack(self):
        '''
        This has a spring-like bit that branches off near the hinge, and passes under a small bridge. this should allow the hands to be turned backwards
        or the time to run without the strike, without causing any damage. This is broadly copying the smiths design
        '''



        rack = cq.Workplane("XY").tag("base")

        rack = rack.moveTo(self.hinge_to_rack/2,0).rect(self.hinge_to_rack, self.arm_wide).extrude(self.arm_thick)

        rack = rack.workplaneFromTagged("base").circle(self.fixingScrew.metric_thread*2).extrude(self.hinge_thick)

        rack = rack.faces(">Z").workplane().circle(self.fixingScrew.metric_thread+LOOSE_FIT_ON_ROD).cutThruAll()

        start_angle = 0 - self.rack_starts_at * self.max_strikes * self.angle_per_strike

        for strike in range(self.max_strikes):
            angle = start_angle + self.angle_per_strike * strike
            next_angle = angle + self.angle_per_strike



        return rack


class Snail:
    '''
    Part of the rack and snail, should be attached to the hour holder
    default values work well with default motion works
    '''
    def __init__(self, maxDiameter=40, minDiameter=12, thick=8, wallThick=0):
        self.maxR=maxDiameter/2
        self.minR=minDiameter/2
        self.thick = thick
        #making it not completely solid so it looks better and prints faster
        #note - this worked fine, but actually it *needs* to be solid so if the rack isn't raised it doesn't get stuck on the inside
        #unless I come up with a different mechanism for that
        self.wallThick = wallThick
        # self.gapDistance=minDiameter*0.05


    def get2D(self):
        snail = cq.Workplane("XY")

        hours = 12
        dA = -math.pi*2/hours
        dR = (self.maxR - self.minR)/hours

        start = polar(0, self.minR)

        snail = snail.moveTo(start[0], start[1])

        for hour in range(hours):
            angle = dA * hour
            r = self.minR + dR * hour

            start = polar(angle, r)
            end = polar(angle + dA, r)
            if hour != 0:
                #lineTo(start[0], start[1]).lineTo(end[0], end[1])
                snail = snail.lineTo(start[0], start[1])

            snail=snail.radiusArc(end,r)

        snail = snail.close()




        return snail

    def get3D(self, extraThick=0):
        #TODO consider a ramp so the rack can slide over the 1 o'clock ledge if it's not been raised for any reason?
        #that mechanism hasn't been designed yet
        snail = self.get2D().extrude(self.thick + extraThick)

        if self.wallThick > 0:
            shellThick = self.thick-self.wallThick*2

            #get a flat bit that we can use to chop away the inside
            shell = snail.shell(-self.wallThick).translate((0, 0, -self.wallThick)).intersect(cq.Workplane("XY").rect(self.maxR*8, self.maxR*8).extrude(shellThick))

            cutter = snail.cut(shell).cut(shell.translate((0,0,shellThick)))

            snail = snail.cut(cutter)

        return snail

class StrikeTrigger:
    '''
    Would like a better name - this is the bit that raises a lever to trigger the hourly and half hourly strikes.
    Should be attached to the minute wheel
    '''
    def __init__(self, minR=10, hourR=20, halfHourR=15):
        self.minR=minR
        self.hourR=hourR
        self.halfHourR=halfHourR

    def get2D(self):
        #was attempting to make a gradient that lifted at a steady rate, but given up

        # halfHourGradient = (self.halfHourR - self.minR)/math.pi
        #
        # def triggerCurve(angle, minR, gradient):
        #     return polar(angle, minR + gradient*(angle % math.pi))
        #
        # def triggerCurveWhole(angle, minR, hourR, halfHourR):
        #     halfHourGradient = (halfHourR - minR) / math.pi
        #     hourGradient = (hourR - minR)/math.pi
        #
        #     if angle < math.pi:
        #         return polar(angle, minR + halfHourGradient *angle)
        #     else:
        #         return polar(angle, minR + hourGradient * (angle - math.pi) + math.pi)
        #
        # # trigger = cq.Workplane("XY").moveTo(self.minR,0).parametricCurve(lambda a: triggerCurve(a, self.minR, halfHourGradient), start=0, stop = math.pi*2 )
        # trigger = cq.Workplane("XY").moveTo(self.minR,0).parametricCurve(lambda a: triggerCurveWhole(a, self.minR, self.hourR, self.halfHourR), start=0, stop = math.pi*2 )
        # # trigger = trigger.lineTo(-self.minR, 0)
        trigger = cq.Workplane("XY").moveTo(self.minR, 0).radiusArc((0,self.minR),-self.minR).tangentArcPoint((-self.halfHourR,0),relative=False).\
            lineTo(-self.minR,0).radiusArc((0,-self.minR),-self.minR).tangentArcPoint((self.hourR,0),relative=False).close()

        # .rotate((0,0,0),(0,0,1),90)
        #hour is currently at 0deg (+ve x)
        return trigger

# class Rack:
#     def __init__(self, radius=60, snail=None, holeR=3.5):
#         self.radius=radius
#         self.hourNotchSize=3
#         self.holeR=holeR
#         if snail is not None:
#             self.hourNotchSize = (snail.maxDiameter - snail.minDiameter)/11
#
#     def get2D(self):
#         rack = cq.Workplane("XY")
#
#
#         return rack


class Whistle:
    '''

    Taken from CuckooWhistle and improved here - the old class was one of the first caquery bits I'd written and I'd like to overhaul it

    The whistle and chamber are one part, then teh bellows is in two parts which must have the tyvek attached and then glued to the top of the whistle
    I could include the base of the bellows in the whistle, but I think that would make the bellows hard to glue the tyvek

    Very much based on teh whistle built in this thread https://mb.nawcc.org/threads/how-to-diy-a-wooden-whistle.97498/

    NOTE: massively benefits from being printed in PLA. I think the slight lack of sharpness in PETG is enough for it to sound significantly worse

    '''
    def __init__(self, chamber_length=45, harmonics=1, text=None, extra_body_length=0, total_length = -1, bellows_at_back=False, nozzle_size=0.4, mouthpiece=False, open_end=False):
        '''
        chamber_length - length of internal chamber
        harmonics - 1 or 2 for how many internal chambers (2 for train whistle, 1 for cuckoo)
        extra_body_length - add extra length to the body so a pair of whistles matches in size

        total_length = if provided, override chamber length to set total whistle length
        '''
        self.whistle_top_length = 20
        self.extra_body_length = 0

        self.bellows_at_back = bellows_at_back

        self.top_wall_thick = 3
        self.chamber_wall_thick = 3

        #affects the size of thin edges so they will print as close as possible to the desired dimensions
        #scrap that, it'll take 4 hours to print with a 0.25 nozzle. It's only going to support 0.4 nozzles for now. Might be useful for printing only the top peice
        #NOT YET USED
        #note, i tried using this to adjust the sharpness of points and then print with 0.25 on the mk4. However the whistle simply didn't work!
        #going back to hardcoded 0.4 for everything
        self.nozzle_size = nozzle_size

        self.mouthpiece = mouthpiece

        self.open_end = open_end


        #extra wall thick for the base of the whistle
        self.total_length=chamber_length + self.whistle_top_length + extra_body_length
        if not self.open_end:
            self.total_length += self.chamber_wall_thick

        if total_length > 0:
            self.total_length = total_length
            chamber_length = total_length - self.whistle_top_length - extra_body_length
            if not self.open_end:
                chamber_length -= self.chamber_wall_thick

        #how many chambers to add? Plan is for two for a train whistle
        self.harmonics = harmonics

        self.chamber_length = chamber_length



        self.chamber_outside_width=22
        #taken by generating a trend line from all the commercial sizes of bellows I could find.
        #completely over the top I expect
        self.bellow_length=0.25*self.total_length + 25
        self.bellow_width = 0.1*self.total_length + 25
        self.hole_d = 8

        #bellow offset from the side so that this whistle can be attached to the wall of a clock case without getting caught
        self.bellow_offset=5
        self.bellow_top_thick = 9.5
        self.bellow_bottom_thick = 3.5
        self.bellow_fabric_extra=7

        self.top_chamber_height = 3

        self.divider_thick=1

        #old £1 coin for the weight on the top of the bellows
        self.weight_d = 23
        self.weight_thick = 3.2
        self.text = text

        print("bellow width: {} length: {}".format(self.bellow_width,self.bellow_length))

        #TODO measure how much shorter the main chamber needs to be for the second whistle and then both can be printed

    def get_bellow_bottom(self):
        '''
        bellow top and bottom is in the +ve quadrant with the bottom left corner at 0,0
        '''
        thick = self.bellow_bottom_thick

        base = cq.Workplane("XY").line(self.bellow_width,0).line(0,self.bellow_length).line(-self.bellow_width,0).close().extrude(thick)
        #hole for the whistle
        base = base.faces(">Z").workplane().moveTo(self.chamber_outside_width / 2 - self.bellow_offset, self.chamber_outside_width / 2).circle(self.hole_d / 2).cutThruAll()
        return base

    def get_bellow_top(self):
        thick = self.bellow_top_thick


        top = cq.Workplane("XY").tag("base").line(self.bellow_width, 0).line(0, self.bellow_length).line(-self.bellow_width, 0).close().extrude(thick)

        gap = (self.bellow_width-self.weight_d)/2

        top = top.faces(">Z").workplane().moveTo(self.bellow_width/2, gap+self.weight_d/2).circle(self.weight_d/2).cutThruAll()

        top = top.workplaneFromTagged("base").line(self.bellow_width, 0).line(0, self.bellow_length).line(-self.bellow_width, 0).close().extrude(thick-self.weight_thick)

        return top

    def get_mouthpiece(self):

        mouthpiece = cq.Workplane("XY")


        return mouthpiece

    def get_whole_whistle(self):
        '''

        :param with_base: if False the base of the whistle is oen-ended
        :param high_pitched: If True, the whistle chamber is smaller
        :return:
        '''
        top = self.get_whistle_top()
        # body
        whistle = top.union(self.get_chamber())


        if self.text is not None:
            textspace = TextSpace(x=self.total_length/2 - self.whistle_top_length, y=0, width = self.chamber_outside_width, height=self.total_length, text=self.text,
                                  horizontal=True, inverted=False, font="Gill Sans Medium", font_path="../fonts/GillSans/Gill Sans Medium.otf" )

            #.moveTo(self.highPitchedShorter, self.wall_thick/2).move(-self.total_length/2,-self.pipe_width/2)
            whistle = whistle.union(textspace.get_text_shape().rotate((0,-self.chamber_outside_width/2,0),(-1,-self.chamber_outside_width/2,0),-90))
            # whistle = cq.Workplane("XY").text(txt=text, fontsize=self.pipe_width*0.6,distance=0.2)


        # whistle = whistle.chamfer()

        return whistle

    def get_chamber(self):
        chamber = (cq.Workplane("XY").rect(self.chamber_outside_width, self.chamber_outside_width)
                   .rect(self.chamber_outside_width - self.top_wall_thick * 2, self.chamber_outside_width - self.top_wall_thick * 2).extrude(self.total_length - self.whistle_top_length))

        chamber = chamber.rotate((0,0,0),(0,1,0),90).translate((0,0,self.chamber_outside_width/2))


        if not self.open_end:
            #base extends off the bottom of the whistle
            base = cq.Workplane("XY").rect(self.chamber_wall_thick, self.chamber_outside_width).extrude(self.chamber_outside_width).translate((self.chamber_length + self.chamber_wall_thick/2,0))

            chamber = chamber.union(base)


        #in a pair of old wooden whistles, the differnce in sizes appears to be: 16x21 inner size, height of 4mm

        if self.harmonics == 2:
            #TODO worth making generic for any number of harmonics? am I ever going to want more than 2?

            whistle_top_thick = (self.top_wall_thick * 2 + self.top_chamber_height)

            #plus some extra for fudge factor so the slicer connects the divider with the whistle bits
            # inner_chamber_length = self.total_length - whistle_top_thick# + 1
            # if not self.open_end:
            #     inner_chamber_length -= self.chamber_wall_thick
            inner_chamber_width = self.chamber_outside_width - self.top_wall_thick * 2 + 1


            chamber_top_x =  -self.whistle_top_length  + whistle_top_thick
            chamber_base_x =  self.chamber_length

            whistle_overlap = 0.5
            inner_chamber_length = chamber_base_x - chamber_top_x

            #-0.5 so that the slicer combines it with the top part of the whistle
            divider = cq.Workplane("XY").rect(inner_chamber_length + whistle_overlap*2, inner_chamber_width).extrude(self.divider_thick).translate(
                (inner_chamber_length/2 - self.whistle_top_length  + whistle_top_thick, 0, self.chamber_outside_width / 2 - self.divider_thick / 2))

            #TODO review that this is in the right place
            filler = cq.Workplane("XY").rect(inner_chamber_length/2, inner_chamber_width).extrude(inner_chamber_width/2).translate(
                ((chamber_top_x + chamber_base_x)/2 + inner_chamber_length/4, 0, self.top_wall_thick))

            divider = divider.union(filler)

            chamber = chamber.union(divider)

        return chamber

    def get_whistle_top(self):
        wedge_depth=3
        hole_d=self.hole_d
        #0.025" (aprox 0.6mm)
        #later comments suggest thinner is louder, so although 0.6 worked fine I'm going to try smaller
        #was just 0.4, but with a smaller nozzle I think I can go thinner
        #tried 0.25 with 0.25 nozzle - didn't work!
        wedge_end_thick =0.4
        #~0.03" the bit that focuses the air onto the wedge
        #0.8 was too big - needs lots of airflow to whistle
        #0.2 is too small - needs a lot of weight to make a noise
        #0.6 works but I think the whistle is too short
        #0.4 sounds promising but needs testing in a clock
        airgap = 0.4#0.4
        #first internal chamber - before the wedge
        top_chamber_height=self.top_chamber_height
        #I think I measured this from a real whistle, it seems to work, so leaving it be
        exit_gap = 2.3
        #building the whistle on its side, hoping the wedge shape can be printed side-on
        #I drew this side-on so x is the height of the whistle and y is the width of the whistle.
        # tried 0.25 with 0.25 nozzle - didn't work!
        airgap_wedge_tip_width=0.4
        airgap_wedge_end_width= self.chamber_wall_thick * 0.3

        #just to make the following bit less verbose
        w = self.whistle_top_length
        h=self.chamber_outside_width
        wall = self.chamber_wall_thick

        top=cq.Workplane("XY").rect(w, h).extrude(wall)
        #the wedge
        top = top.faces(">Z").workplane().tag("whistle").moveTo(w/2,h/2).lineTo(-w/2+wall*2+top_chamber_height+exit_gap,h/2-wedge_depth+wedge_end_thick).\
            line(0,-wedge_end_thick).lineTo(w/2,h/2-wedge_depth).close().extrude(h-wall*2)
        #top cap
        top = top.workplaneFromTagged("whistle").moveTo(-w/2+wall/2,0).rect(wall,h).extrude(h-wall*2)
        if not self.bellows_at_back:
            #hole in top cap
            #this seems to place us at wall height
            top = top.faces("<X").workplane().moveTo(0, (self.chamber_outside_width - wall * 2) / 2).circle(hole_d / 2).cutThruAll()
        #bit that forces the air over the wedge
        top = top.workplaneFromTagged("whistle").moveTo(-w / 2 + wall, h/2).line(wall+top_chamber_height,0).line(0,-wedge_depth).line(-(wall+top_chamber_height),0).close().extrude(h-wall*2)
        #top chamber and other wall
        top = (top.workplaneFromTagged("whistle").moveTo(w/2,-h/2).line(-w+wall,0).line(0,wall).line(top_chamber_height,0).lineTo(-w/2+wall+top_chamber_height,h/2-wedge_depth-airgap - airgap_wedge_end_width)
               .line(wall - airgap_wedge_tip_width,airgap_wedge_end_width).line(airgap_wedge_tip_width,0).lineTo(-w/2+wall*2+top_chamber_height,-h/2+wall).lineTo(w/2,-h/2+wall).close().extrude(h-wall*2))

        # and the final wall (comment this out to see inside the whistle)
        top = top.faces(">Z").workplane().tag("pretweak").rect(w, h).extrude(wall)
        fudge = 0.5

        if self.bellows_at_back:
            #cut a square hole in the back (since there's not enough space for the circle)
            #this turns out to be approximately the same size as the chamber. Since I copied the dimensions from a real whistle this seems like have been by (not my) design
            area = math.pi * (hole_d / 2) ** 2
            hole_width = self.chamber_outside_width - self.top_wall_thick * 2
            hole_height = area / hole_width
            top = top.cut(cq.Workplane("XY").rect(hole_height, hole_width).extrude(10000).rotate((0,0,0),(1,0,0),90).translate((-self.whistle_top_length/2 + self.top_wall_thick + hole_height/2,0,self.chamber_outside_width/2)))
        else:
            if not self.mouthpiece:
                #add a ledge so it's easier to line up the bellows
                top = top.faces("<X").workplane().move(0, self.top_wall_thick - self.chamber_outside_width / 2).move(-self.chamber_outside_width / 2 + self.bellow_offset / 2 - fudge / 2, 0).rect(self.bellow_offset - 0.5, self.chamber_outside_width).extrude(0.2)

        if self.mouthpiece:
            bigger_hole = (cq.Workplane("XY").rect(self.top_wall_thick*2, self.chamber_outside_width - self.top_wall_thick*2).extrude(self.chamber_outside_width - self.top_wall_thick*2)
                           .translate((-self.whistle_top_length/2, 0, self.top_wall_thick)))
            top = top.cut(bigger_hole)

            mouthpiece_length = self.chamber_outside_width*1.5
            mouthpiece_wall_thick = 2
            #
            area = math.pi * (hole_d / 2) ** 2
            hole_width = self.chamber_outside_width - mouthpiece_wall_thick* 2
            mouthpiece_hole_wide = area / hole_width
            mouthpiece_thick = mouthpiece_hole_wide + mouthpiece_wall_thick*2


            # mouthpiece = (cq.Workplane("XY").moveTo(-self.whistle_top_length/2,-self.chamber_outside_width/2).line(-mouthpiece_length,0).radiusArc((-self.whistle_top_length/2 - mouthpiece_length,mouthpiece_thick-self.chamber_outside_width/2),mouthpiece_thick/2)
            #               .radiusArc((-self.whistle_top_length/2,self.chamber_outside_width/2), -mouthpiece_length*1.5).close().extrude(self.chamber_outside_width))

            mouthpiece = (cq.Workplane("XY").moveTo(-self.whistle_top_length / 2, -self.chamber_outside_width / 2).line(-mouthpiece_length, 0).radiusArc(
                (-self.whistle_top_length / 2 - mouthpiece_length, mouthpiece_thick - self.chamber_outside_width / 2), mouthpiece_thick / 2)
                          .spline([(-self.whistle_top_length / 2, self.chamber_outside_width / 2)], includeCurrent=True, tangents=[(1,0),(1,0)]).close().extrude(self.chamber_outside_width))

            # mouthpiece_hole = (cq.Workplane("XY").moveTo(-self.whistle_top_length/2,-self.chamber_outside_width/2 + mouthpiece_wall_thick).line(-mouthpiece_length - mouthpiece_thick,0).line(0,mouthpiece_hole_wide)
            #               .line(mouthpiece_thick,0).radiusArc((-self.whistle_top_length/2,self.chamber_outside_width/2 - mouthpiece_wall_thick-0.5), -mouthpiece_length*1.5 - mouthpiece_wall_thick).close().extrude(self.chamber_outside_width - mouthpiece_wall_thick*2).
            #                    translate((0,0,mouthpiece_wall_thick)))
            mouthpiece_hole = (cq.Workplane("XY").moveTo(-self.whistle_top_length / 2, -self.chamber_outside_width / 2 + self.top_wall_thick).lineTo(-mouthpiece_length-self.whistle_top_length / 2 - mouthpiece_thick, mouthpiece_wall_thick-self.chamber_outside_width/2).line(0, mouthpiece_hole_wide)
                               .line(mouthpiece_thick, 0)
                               .spline([(-self.whistle_top_length / 2, self.chamber_outside_width / 2 - self.top_wall_thick)], includeCurrent=True, tangents=[(1,0),(1,0)]).close()
                               .extrude(self.chamber_outside_width - mouthpiece_wall_thick * 2).translate((0, 0, mouthpiece_wall_thick)))

            top = top.union(mouthpiece.cut(mouthpiece_hole))

        top = top.translate((-self.whistle_top_length/2,0,0))
        return top

    def get_bellows_template(self):

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