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
import math

from .geometry import get_stroke_line
from .utility import *
import cadquery as cq
import os
from cadquery import exporters
from enum import Enum
from .gearing import GearStyle,Gear
from .cosmetics import tony_the_clock
from .types import HandType, HandStyle

def spade_hand(hand_width, length, thick):

    # for the bottom of the spade, not the usual baseR
    spadeBaseR = length * 0.05 * 2

    spadeTopLength = length * 0.4
    spadeTipWidth = hand_width * 0.5
    tipLength = length * 0.1

    # if second:
    #     spadeTipWidth*=0.9

    # length = length - tipLength - spadeTopLength

    armLength = length - tipLength - spadeTopLength

    midPoint = (spadeBaseR * 0.75, armLength + spadeTopLength * 0.3)
    tipBase = (spadeTipWidth / 2, armLength + spadeTopLength)
    tipEndSide = (spadeTipWidth / 2, armLength + spadeTopLength + tipLength)
    tip = (0, armLength + spadeTopLength + tipLength + spadeTipWidth / 2)

    hand = cq.Workplane("XY").moveTo(0, armLength / 2).rect(hand_width, armLength).extrude(thick)

    hand = hand.union(cq.Workplane("XY").moveTo(0, armLength - spadeBaseR).radiusArc((spadeBaseR, armLength),
                                                                                        -spadeBaseR) \
        .tangentArcPoint(midPoint, relative=False) \
        .tangentArcPoint(tipBase, relative=False).tangentArcPoint(tipEndSide, relative=False).tangentArcPoint(tip,
                                                                                                              relative=False) \
        .mirrorY().extrude(thick))

    return hand


class HandGenerator:
    def __init__(self, base_r, length, thick, second_base_r=-1, second_thick=-1):
        #radius of circle at base of hand
        self.base_r = base_r
        #total length of minute hand regardless of base_r
        self.length = length
        self.thick = thick
        #none of the below is actually used (yet? can't make up my mind)
        self.second_base_r = second_base_r
        if self.second_base_r < 0:
            self.second_base_r = self.base_r
        self.second_thick = second_thick
        if self.second_thick < 0:
            self.second_thick = self.thick

    def get_colours(self):
        return [None]

    def get_colours_which_need_base_r(self):
        return [None]

    def hour_hand(self, colour = None, thick_override=-1):
        raise NotImplemented()

    def minute_hand(self, colour = None, thick_override=-1):
        raise NotImplemented()

    def second_hand(self, total_length=30, base_r=6, thick=3, colour = None, balanced=False, fixing_thick=-1):
        raise NotImplemented()

# class CombinedGenerator(HandGenerator):
#     def __init__(self, base_r, length, thick, second_base_r=-1, second_thick=-1, hour_generator=None, minute_generator=None, seconds_generator=None):
#         '''
#         Conform to the hand generator interface, but support a mix-and-match
#         '''

class KnobHands(HandGenerator):
    '''
    Mohsin asked, it amuses me so I'm going to try!

    I'd like to have the balls literally dangling off the end, I think just a screw and nyloc nut should be enough for that
    '''
    def __init__(self, base_r, length, thick):
        super().__init__(base_r, length, thick)

    def get_knob(self, length, width):
        knob = cq.Workplane("XY")

        knob = knob.moveTo(width/2, 0).radiusArc((-width/2,0), width/2)

        return knob

class FancyWatchHands(HandGenerator):
    def __init__(self, base_r, total_length, thick, outline=1, detail_thick=0.4):
        super().__init__(base_r, total_length, thick)

        self.base_r = self.length * 0.15
        #originally was thinking of using the outline provided to the hands, but now we'll override it with whatever is best and expect these hands to have been provided
        #with an outline of 0
        self.outline = outline
        self.outline = self.length*0.02
        self.detail_thick = detail_thick

        self.main_hand_black = True

    def hour_hand(self, colour=None, thick_override=-1):
        hand = cq.Workplane("XY").tag("base")

        '''
        copied and tweaked from brequet hands
        '''
        length = self.length*0.6

        thick = self.thick
        if thick_override > 0:
            thick = thick_override

        hand_width = self.length * 0.09
        tip_width = self.length * 0.02  # *0.0125
        circle_r = self.length * 0.125

        circle_y = length * 0.65
        # #point where teh arm starts to bend towards the tip
        bend_point_y = circle_y + circle_r - hand_width / 2

        fudge = 0.0001
        hand = hand.workplaneFromTagged("base").moveTo(0, bend_point_y / 2).rect(hand_width, bend_point_y).extrude(thick)
        # some sizes are complaining the radius isn't long enough to complete the arc, so bodge it a bit
        # the little tiny straight bit before the rounded end fixes the shell so we can add outlines. *shrug*
        hand = (hand.workplaneFromTagged("base").moveTo(-hand_width / 2, bend_point_y).lineTo(-tip_width / 2, length).line(0, fudge)
        .radiusArc((tip_width / 2, length + fudge), tip_width / 2 + 0.01).line(0, -fudge).lineTo(hand_width / 2, bend_point_y).close()
        .extrude(thick))

        # brequet hand without hole in the circle - when colour is None this is used to calcualte the outline
        hand = hand.workplaneFromTagged("base").moveTo(0, circle_y).circle(circle_r).extrude(thick)
        hand = hand.workplaneFromTagged("base").circle(radius=self.base_r).extrude(thick)

        if colour == None:
            return hand

        prong_thick = self.outline

        three_prongs = cq.Workplane("XY").tag("base")

        for i in range(3):

            angle = math.pi/2 + (i+0.5)*math.pi*2/3

            centre = polar(angle, circle_r/2)
            three_prongs = three_prongs.union(cq.Workplane("XY").rect(prong_thick, circle_r).extrude(self.detail_thick)
                                              .rotate((0,0,0), (0,0,1), rad_to_deg(angle + math.pi / 2)).translate(centre))

        three_prongs = three_prongs.union(cq.Workplane("XY").circle(circle_r).circle(circle_r - self.outline).extrude(self.detail_thick))

        three_prongs = three_prongs.translate((0, circle_y))





        # doing outline manually here as this is the only hand of the three that needs it and it's neater and esasier than bodging the combinations of outline and black detail on all the other hands
        black_outline = self.hour_hand(colour=None, thick_override=self.outline * 4).shell(-self.outline).translate((0,0,-self.outline)).intersect(cq.Workplane("XY").rect(self.length * 4, self.length * 4).extrude(self.detail_thick))
        black_detail = three_prongs.union(black_outline)
        # black_detail = three_prongs

        white_detail = hand.intersect(cq.Workplane("XY").rect(self.length * 4, self.length * 4).extrude(self.detail_thick)).cut(black_detail)

        if colour == "white":
            if self.main_hand_black:
                return white_detail
            return hand.cut(black_detail)

        if colour == "black":
            if self.main_hand_black:
                return hand.cut(white_detail)
            return black_detail


        # hand = hand.faces(">Z").moveTo(0, circle_y).circle(circle_r - hand_width).cutThruAll()




        return hand

    def minute_hand(self, colour=None, thick_override=-1):

        base_r = self.base_r*0.8

        thick = self.thick
        if thick_override > 0:
            thick = thick_override
        hand = cq.Workplane("XY").tag("base")
        '''
        copied and tweaked from SYRINGE
        '''
        syringe_width = self.length * 0.1

        syringe_length = self.length * 0.5

        syringe_startY = (self.length - syringe_length) / 2

        base_wide = syringe_width * 0.25

        tip_r = self.length * 0.01

        hand = hand.workplaneFromTagged("base").moveTo(0, 0).lineTo(-base_wide / 2, 0)

        hand = hand.lineTo(-syringe_width / 2, syringe_startY).line(0, syringe_length) \
            .lineTo(-tip_r, self.length - tip_r).line(0,0.00001).radiusArc((0, self.length), tip_r).mirrorY().extrude(thick)

        white_rectangle = cq.Workplane("XY").rect(syringe_width - self.outline*3, syringe_length).extrude(self.detail_thick).translate((0,syringe_startY + syringe_length/2))

        hand = hand.workplaneFromTagged("base").circle(radius=base_r).extrude(thick)

        detail_without_rectangle = hand.intersect(cq.Workplane("XY").rect(self.length * 4, self.length * 4).extrude(self.detail_thick)).cut(white_rectangle)
        #.cut(cq.Workplane("XY").circle(base_r - self.outline).extrude(self.thick))



        if colour == "black":
            if self.main_hand_black:
                return hand.cut(white_rectangle)
            return detail_without_rectangle
        if colour == "white":
            if self.main_hand_black:
                return white_rectangle
            return hand.cut(detail_without_rectangle)

        return hand

    def second_hand(self, total_length=30, base_r=6, thick=3, colour = None, balanced=False, fixing_thick=-1):



        if balanced:
            #centred second hand
            total_length = self.length*1.05
            base_r = self.base_r*0.7

        if fixing_thick < 0:
            fixing_thick = thick * 3

        width = 1.5
        back_width = 2

        hand = cq.Workplane("XY").tag("base").moveTo(0,total_length/2).rect(width, total_length).extrude(thick)
        hand = hand.workplaneFromTagged("base").circle(base_r).extrude(fixing_thick)

        #these look fairly accurate to the hands I'm modelling, but can't easily be balanced
        # front_circle_y = total_length*0.6
        # back_circle_y = -total_length*0.3
        # front_circle_r = self.length*0.075
        # back_circle_r = self.length*0.05

        front_circle_y = total_length * 0.6
        back_circle_y = -total_length * 0.4
        front_circle_r = self.length * 0.06
        back_circle_r = self.length * 0.06

        #volume x centre distance
        front_moment = total_length * width * thick * total_length*0.5 + math.pi*(front_circle_r**2)*thick * front_circle_y

        back_arm_moment = -back_circle_y*0.5 * -back_circle_y*back_width*thick
        back_circle_area_times_distance = math.pi*(back_circle_r**2) * -back_circle_y

        back_circle_thick = (front_moment - back_arm_moment) / back_circle_area_times_distance


        hand = hand.workplaneFromTagged("base").moveTo(0, front_circle_y).circle(front_circle_r).extrude(thick)

        hand = hand.workplaneFromTagged("base").moveTo(0, back_circle_y/2).rect(back_width, -back_circle_y).extrude(thick)
        hand = hand.workplaneFromTagged("base").moveTo(0, back_circle_y).circle(back_circle_r).extrude(back_circle_thick)


        white_circle = cq.Workplane("XY").moveTo(0,front_circle_y).circle(front_circle_r - self.outline).extrude(self.detail_thick)

        if colour == "white":
            return white_circle
        if colour == "black":
            hand = hand.cut(white_circle)#.intersect(cq.Workplane("XY").rect(self.length * 4, self.length * 4).extrude(self.detail_thick)).cut(white_rectangle)

        return hand

    def get_colours(self):
        return ["white", "black"]

    def get_colours_which_need_base_r(self):
        return []
class BaroqueHands(HandGenerator):
    def __init__(self, base_r, total_length, thick, line_width):
        super().__init__(base_r, total_length, thick)
        self.total_length =total_length
        self.line_width = line_width
        self.hour_total_length = 0.7*self.total_length

        self.hour_hand_cache = None
        self.minute_hand_cache = None
        self.second_hand_cache = None

    def get_bar(self):
        bar_width = self.total_length * 0.1
        # hand = hand.union(cq.Workplane("XY").rect(bar_width, line_width).extrude(thick).translate((0, bar_y)))
        # bar with slightly rounded ends
        bar = cq.Workplane("XY").moveTo(bar_width / 2, self.line_width / 2).radiusArc((bar_width / 2, -self.line_width / 2), self.line_width).\
                          lineTo(-bar_width / 2, -self.line_width / 2).radiusArc((-bar_width / 2, self.line_width / 2), self.line_width).close().extrude(self.thick)
        return bar
    def hour_hand(self, colour=None, thick_override=-1):
        '''
        doing this outside the main hands class as it could get complicated and for the baroque hands there's little in common between the hour and minute hands
        '''

        if self.hour_hand_cache is not None:
            return self.hour_hand_cache

        total_length = self.hour_total_length
        #plan is to make the bulk of the hand always start just after the base circle
        length = total_length-self.base_r
        hand =  cq.Workplane("XY").tag("base").circle(self.base_r).extrude(self.thick)
        #overlap should be 1.5 line thick

        # line_width = thick#length*0.05
        centre_circles_r = length*0.125
        centre_circle_position = (centre_circles_r + self.line_width*0.25, self.base_r + length*0.55)
        centre_circle_positions = [(centre_circle_position[0]*-1, centre_circle_position[1]),centre_circle_position]

        #the two circles side by side
        for circle_pos in centre_circle_positions:
            hand = hand.union(cq.Workplane("XY").circle(centre_circles_r + self.line_width/2).circle(centre_circles_r-self.line_width/2).extrude(self.thick).translate(circle_pos))

        #the two arcs below these circles
        #outer radius
        arc_top_y = centre_circle_position[1] - centre_circles_r + self.line_width/2
        #we won't keep the bottom bit, we'll chop off line_width's worth of height
        arc_bottom_y = self.base_r + length*0.07
        arc_height = arc_top_y - arc_bottom_y
        arc_y = (arc_bottom_y + arc_top_y)/2
        arc_sag = centre_circle_position[0]+self.line_width/4
        #https://en.wikipedia.org/wiki/Sagitta_(geometry)
        arc_outer_r = arc_sag/2 + arc_height**2/(8*arc_sag)
        for x in [-1,1]:
            arc = cq.Workplane("XY").circle(arc_outer_r).circle(arc_outer_r-self.line_width).extrude(self.thick).translate(((arc_outer_r-self.line_width/4)*x,arc_y))
            arc = arc.intersect(cq.Workplane("XY").rect(arc_sag, arc_height-self.line_width).extrude(self.thick).translate((x*(arc_sag/2-self.line_width/8), arc_y + self.line_width)))
            hand = hand.union(arc)

            hand = hand.union(cq.Workplane("XY").circle(self.line_width*1.25).extrude(self.thick).translate((centre_circle_position[0]*x,centre_circle_position[1] - centre_circles_r)))

        #edge of gap between the bottom ends of teh arcs (another sagitta)
        #bottom of the intersection rectangle from above
        y = arc_y + self.line_width - (arc_height-self.line_width)/2
        #length of sagitta
        l = (arc_y - y )*2
        edge_of_inner_triangle_x = arc_outer_r - math.sqrt(arc_outer_r**2 - (l/2)**2) - self.line_width*0.25
        # x = (2*arc_outer_r + math.sqrt(4*arc_outer_r**2 - 4*(arc_height-line_width)**4))/2
        # print(x)

        base_circle_r = edge_of_inner_triangle_x + self.line_width  # arc_bottom_y+line_width - bar_y + line_width/2

        #horizontal bar near the base circle
        bar_y = arc_bottom_y+self.line_width*1.5 - base_circle_r#base_r + (arc_bottom_y+line_width - base_r)/2# + line_width/2
        # bar_width = self.total_length*0.15
        # hand = hand.union(cq.Workplane("XY").rect(bar_width, line_width).extrude(thick).translate((0, bar_y)))
        #bar with slightly rounded ends
        hand = hand.union(self.get_bar().translate((0, bar_y)))
        # for x in [-1, 1]:
        #     hand = hand.union(cq.Workplane("XY").circle(line_width/2).extrude(thick).translate((x*bar_width/2, bar_y)))


        #semicircle above the bar, inner radius of this circle is calcualted to be in the right place above
        hand = hand.union(cq.Workplane("XY").circle(base_circle_r).circle(edge_of_inner_triangle_x).extrude(self.thick).intersect(cq.Workplane("XY").rect(base_circle_r*2, base_circle_r).extrude(self.thick).translate((0,-base_circle_r/2))).translate((0,(bar_y + base_circle_r))))

        #link up the bar to the base circle
        hand = hand.union(cq.Workplane("XY").rect(self.line_width*1.5,bar_y).extrude(self.thick).translate((0,bar_y/2)))


        #above the centre circles, width of gap in the middle
        gap_width = (centre_circle_position[0]*0.9 - self.line_width)*2 * 0.6
        gap_circle_r = gap_width/4 + self.line_width/8
        gap_circles_y = centre_circle_position[1] + length*0.225
        top_of_circles_y =centre_circle_position[1] + centre_circles_r
        # height = self.total_length - top_of_circles_y


        for x in [-1, 1]:
            hand = hand.union(cq.Workplane("XY").circle(gap_circle_r).extrude(self.thick).translate((x*gap_width/4, gap_circles_y)))



            top_line = cq.Workplane("XY").moveTo((gap_width + self.line_width)*x, top_of_circles_y).spline([((gap_width/2 + self.line_width)*x, gap_circles_y ), (x*self.line_width/2, total_length)], includeCurrent=True, tangents=[(0,1), (0,1)])\
                .line(-self.line_width*x,0).spline([((gap_width/2)*x, gap_circles_y ), ((gap_width)*x, top_of_circles_y)], includeCurrent=True, tangents=[(0,-1), (0,-1)]).close().extrude(self.thick)
            # return top_line
            hand = hand.union(top_line)


        #tip:
        hand = hand.union(cq.Workplane("XY").circle(self.line_width/2).extrude(self.thick).translate((0,total_length)))
        self.hour_hand_cache = hand
        return hand

    def minute_hand(self, colour=None, thick_override=-1):
        if self.minute_hand_cache is not None:
            return self.minute_hand_cache
        hand =  cq.Workplane("XY").tag("base").circle(self.base_r).extrude(self.thick)

        length = self.total_length - self.base_r

        #series of semicircles from top of base circle upwards
        semicircles=[]

        circles_top_y = self.base_r + length*0.6
        arrow_y = self.total_length - (self.total_length - circles_top_y)*0.6
        y = self.base_r + self.line_width
        bar_y = y
        semicircle_count = 4
        semicircle_r = (circles_top_y -y)/(semicircle_count*2)
        x_offset = semicircle_r*0.5
        x = 1
        bar_width = self.total_length * 0.15
        bar = self.get_bar()
        # link up the bar to the base circle
        hand = hand.union(cq.Workplane("XY").rect(self.line_width * 1.5, bar_y).extrude(self.thick).translate((0, bar_y / 2)))
        hand = hand.union(bar.translate((0,bar_y)))

        for i in range(semicircle_count):
            semicircle = cq.Workplane("XY").circle(semicircle_r + self.line_width/2).circle(semicircle_r-self.line_width/2).extrude(self.thick)
            semicircle = semicircle.intersect(cq.Workplane("XY").rect(semicircle_r+self.line_width/2, semicircle_r*2 + self.line_width).extrude(self.thick).translate((x*(semicircle_r + self.line_width/2)/2, 0)))
            for nobble_y in [-1,1]:
                semicircle = semicircle.union(cq.Workplane("XY").circle(self.line_width/4).extrude(self.thick).translate((0,nobble_y*(semicircle_r + self.line_width/4))))
                semicircle = semicircle.union(cq.Workplane("XY").circle(self.line_width / 4).extrude(self.thick).translate((0, nobble_y*(semicircle_r - self.line_width / 4))))

            semicircle = semicircle.translate((-x*x_offset,y + semicircle_r))
            hand = hand.union(semicircle)
            y += semicircle_r*2
            x*=-1

        #link top of circles up to arrow with a bendy line
        top_bend = cq.Workplane("XY").moveTo(-semicircle_r+x_offset-self.line_width/2, circles_top_y-semicircle_r).spline([(-self.line_width/2, arrow_y)], includeCurrent=True, tangents=[(0.2,1), (-0.2,1)]).\
            line(self.line_width,0).spline([(-semicircle_r+x_offset+self.line_width/2, circles_top_y-semicircle_r)], includeCurrent=True, tangents=[(0.2,-1), (-0.2,-1)]).close().extrude(self.thick)
        #chop out any bit that slight comes inside teh circle
        top_bend = top_bend.cut(cq.Workplane("XY").circle(semicircle_r - self.line_width/2).extrude(self.thick).translate((x_offset,circles_top_y-semicircle_r)))
        hand = hand.union(top_bend)

        #line to tip
        hand = hand.union(cq.Workplane("XY").moveTo(-self.line_width/2, arrow_y).lineTo(-self.line_width/2, self.total_length).radiusArc((self.line_width/2, self.total_length), self.line_width/2)
                          .lineTo(self.line_width/2, arrow_y).close().extrude(self.thick))

        #arrow
        arrow_wide = self.line_width*4
        arrow_long = self.line_width*5
        arrow_y_offset = arrow_long*0.3
        arrow = cq.Workplane("XY").moveTo(-arrow_wide/2, -arrow_long/2).radiusArc((arrow_wide/2, -arrow_long/2),arrow_wide)\
            .radiusArc((self.line_width/2, arrow_long/2), arrow_long*1.5).line(-self.line_width,0).radiusArc((-arrow_wide/2, -arrow_long/2), arrow_long*1.5).close().extrude(self.thick).translate((0,arrow_y + arrow_y_offset))

        hand = hand.union(arrow)
        self.minute_hand_cache = hand
        return hand

    def second_hand(self, total_length=30, base_r=6, thick=3, colour=None, balanced=False, fixing_thick=1.6):
        #TODO use fixing_thick
        if self.second_hand_cache is not None:
            return self.second_hand_cache
        line_width=1.2
        # line_width=1.6
        hand = cq.Workplane("XY").tag("base").circle(base_r).extrude(thick)

        length = total_length - base_r

        curve_centre_r = length*0.2
        points_wide = length*0.5

        points_y = base_r + length*0.6
        narrow_start_y = base_r + length*0.3
        narrow_centre_y = base_r + length*0.35
        narrow_end_y =base_r + length*0.4

        #bottom right curve
        pointer = cq.Workplane("XY").moveTo(0, base_r- line_width/2).radiusArc((curve_centre_r/2 + line_width/2, base_r + curve_centre_r/2), -curve_centre_r/2 - line_width/2)
        #curve out to the pointy bit
        pointer = pointer.spline([(line_width/2, narrow_centre_y), (points_wide/2, points_y)], includeCurrent=True, tangents=[(0,1), (1,0.5)])
        #curve back to the tip
        pointer = pointer.spline([(line_width/2, total_length-line_width)], includeCurrent=True, tangents=[(-1, 0.5),(0, 1)]).lineTo(0,total_length)#.radiusArc((0,total_length), -line_width)
        pointer = pointer.mirrorY().extrude(thick)

        first_cutter = cq.Workplane("XY").moveTo(0, base_r+ line_width/2).radiusArc((curve_centre_r/2 - line_width/2, base_r + curve_centre_r/2), -curve_centre_r/2 + line_width/2)
        first_cutter = first_cutter.spline([(0, narrow_centre_y - line_width)], includeCurrent=True, tangents=[(0,1), (0,1)])
        first_cutter = first_cutter.mirrorY().extrude(thick)
        pointer = pointer.cut(first_cutter)

        star_base_y = narrow_centre_y + line_width*1.25
        star_top_y = points_y + (points_y - star_base_y)
        star_wide = points_wide - line_width*2.5

        # second_cutter = cq.Workplane("XY").moveTo(0,star_base_y).lineTo(points_wide/2 - line_width, points_y).lineTo(0, star_top_y).mirrorY().extrude(thick)
        second_cutter = cq.Workplane("XY").spline([(0, star_base_y), (star_wide/2, points_y)], tangents=[(0.5,1),(1,0.5)])\
            .spline([(0, star_top_y)], includeCurrent=True, tangents=[(-1,0.5),(-0.5,1)]).mirrorY().extrude(thick)
        # return second_cutter.add(first_cutter)
        # return second_cutter
        pointer = pointer.cut(second_cutter)

        # return first_cutter
        # pointer = cq.Workplane("XY").moveTo(0, base_r-line_width/2).spline([(line_width/2, narrow_start_y),(line_width/2, narrow_end_y),(points_wide/2, points_y)], tangents=[(1,0),None, None ,(1,0)] ,includeCurrent=True)
        hand = hand.union(pointer)
        # return pointer
        #swirly bit out the back
        semicircle_r = length*0.6/4

        x=-1
        x_offset=0
        y = -(base_r - line_width/2)
        for i in range(2):
            semicircle = cq.Workplane("XY").circle(semicircle_r + line_width/2).circle(semicircle_r-line_width/2).extrude(thick)
            semicircle = semicircle.intersect(cq.Workplane("XY").rect(semicircle_r+line_width/2, semicircle_r*2 + line_width).extrude(self.thick).translate((x*(semicircle_r + line_width/2)/2, 0)))
            # for nobble_y in [-1,1]:
            #     semicircle = semicircle.union(cq.Workplane("XY").circle(line_width/4).extrude(thick).translate((0,nobble_y*(semicircle_r + line_width/4))))
            #     semicircle = semicircle.union(cq.Workplane("XY").circle(line_width / 4).extrude(thick).translate((0, nobble_y*(semicircle_r - line_width / 4))))

            semicircle = semicircle.translate((-x*x_offset,y - semicircle_r))
            hand = hand.union(semicircle)
            y -= semicircle_r*2
            x*=-1

        #blob at end
        hand = hand.union(cq.Workplane("XY").circle(line_width).extrude(thick).translate((0,y + line_width/2)))

        # return base_swirl_line
        # swirl = cq.Workplane("YZ").moveTo(0, thick/2).rect(line_width,thick).loft(base_swirl_line)
        # return swirl
        # hand = hand.union(swirl)
        self.second_hand_cache = hand
        return hand

class FancyClockHands(HandGenerator):
    def __init__(self, base_r, length, thick):
        super().__init__(base_r, length, thick)
        self.diamond_width = self.length*0.15
        self.diamond_thick = self.diamond_width*0.4
        self.basic_width = self.length*0.04

        self.tip_r = self.basic_width*0.25
        self.rear_length = self.length*0.3

        self.hour_length = self.length * 0.7

    def diamond(self):
        #little  horizontal stretched diamond which appears in multiple places
        fillet_r = self.diamond_thick*0.05
        return cq.Workplane("XY").sketch().polygon([(-self.diamond_width/2,0), (0, self.diamond_thick/2), (self.diamond_width/2, 0), (0, -self.diamond_thick/2)]).finalize().extrude(self.thick).edges("|Z").fillet(fillet_r)
        # return cq.Workplane("XY").polyline([(-self.diamond_width/2,0), (0, self.diamond_thick/2), (self.diamond_width/2, 0), (0, -self.diamond_thick/2)]).close().extrude(self.thick)

    def rear_extension(self):
        diamond_distance = -self.base_r - self.diamond_thick
        rear_hand = get_stroke_line([(0,0), (0, diamond_distance)], wide=self.basic_width, thick=self.thick)



        rear_curve_base = diamond_distance - self.diamond_thick * 0.25
        rear_curve_centre_width = self.basic_width * 0.8
        rear_curve_centre = (-self.rear_length + self.tip_r + rear_curve_base) / 2
        rear_curve = (cq.Workplane("XY").moveTo(0, rear_curve_base).spline([(0, rear_curve_base), (-rear_curve_centre_width / 2, rear_curve_centre), (-self.tip_r, -self.rear_length + self.tip_r)], tangents=[(-1, 0), (0, -1)])
                      .radiusArc((0, -self.rear_length), -self.tip_r).mirrorY().extrude(self.thick))

        rear_hand = rear_hand.union(rear_curve)
        rear_hand = rear_hand.union(self.diamond().translate((0, diamond_distance)))

        return rear_hand
    def minute_hand(self, colour = None, thick_override=-1):
        hand = cq.Workplane("XY").tag("base")

        diamond_distances = [self.base_r + self.diamond_thick, self.length * 0.45]

        #first bar from centre to first diamond
        hand = hand.union(get_stroke_line([(0,0), (0, diamond_distances[0])], wide=self.basic_width, thick=self.thick))

        curve_base = diamond_distances[0] + self.diamond_thick*0.25
        curve_centre_width = self.basic_width*1.2
        curve_length = diamond_distances[1] - curve_base
        curve_centre = curve_base + curve_length/2
        #curvey bit after first diamond
        curvey_bit = (cq.Workplane("XY").spline([(0,curve_base), (-curve_centre_width/2, curve_centre), (-self.basic_width/2, diamond_distances[1])], [(-1,0.2),(0.075,1), (0,1)]).lineTo(0, diamond_distances[1])
                      .close().mirrorY().extrude(self.thick))
        hand = hand.union(curvey_bit)
        #.spline([(0, self.length)], tangents=[None, (1,0)], includeCurrent=True)
        end_bit = (cq.Workplane("XY").moveTo(0, diamond_distances[1]).lineTo(-self.basic_width/2, diamond_distances[1]).lineTo(-self.tip_r, self.length-self.tip_r)
                   .tangentArcPoint((0,self.length), relative=False).lineTo(0, diamond_distances[1]).close().mirrorY().extrude(self.thick))


        hand = hand.union(end_bit)

        #and backwards


        #.tangentArcPoint((0,-self.rear_length), relative=False)



        hand = hand.union(self.rear_extension())

        for distance in diamond_distances:
            hand = hand.union(self.diamond().translate((0, distance)))

        return hand

    def hour_hand(self, colour = None, thick_override=-1):
        hand = cq.Workplane("XY").tag("base")

        diamond_distances = [self.base_r + self.diamond_thick/2, self.hour_length*0.45]

        # first bar from centre to first diamond
        hand = hand.union(get_stroke_line([(0, 0), (0, diamond_distances[0])], wide=self.basic_width, thick=self.thick))

        curve_base = diamond_distances[0] + self.diamond_thick * 0.25
        curve_centre_width = self.basic_width * 1.4
        curve_length = diamond_distances[1] - curve_base
        curve_centre = curve_base + curve_length / 2
        # curvey bit after first diamond
        curvey_bit = (cq.Workplane("XY").spline([(0, curve_base), (-curve_centre_width / 2, curve_centre), (-self.basic_width / 2, diamond_distances[1])],
                                                [(-1, 0), None, (0, 1)]).lineTo(0, diamond_distances[1])
                      .close().mirrorY().extrude(self.thick))
        hand = hand.union(curvey_bit)

        apple_wall_thick = self.basic_width
        circle_positions = [(-self.hour_length * 0.1, diamond_distances[1] + self.hour_length*0.15), (-self.hour_length * 0.1, diamond_distances[1] + self.hour_length*0.2)]

        circle_distance = circle_positions[1][1] - circle_positions[0][1]
        circle_radii = [self.hour_length*0.06, self.hour_length*0.09]

        second_circle_cutter_pos = np_to_set(np.add(circle_positions[1], polar(math.pi*3/4, apple_wall_thick*1.1)))

        apple_bit = cq.Workplane("XY").moveTo(circle_positions[0][0], circle_positions[0][1]).circle(circle_radii[0] + apple_wall_thick).mirrorY().extrude(self.thick)

        apple_bit = apple_bit.union(cq.Workplane("XY").moveTo(circle_positions[1][0], circle_positions[1][1]).circle(circle_radii[1] + apple_wall_thick).mirrorY().extrude(self.thick))

        apple_cutter = cq.Workplane("XY").moveTo(second_circle_cutter_pos[0], second_circle_cutter_pos[1]).circle(circle_radii[1]).mirrorY().extrude(self.thick)
        apple_cutter = apple_cutter.union(cq.Workplane("XY").moveTo(circle_positions[0][0], circle_positions[0][1]).circle(circle_radii[0]).mirrorY().extrude(self.thick))

        apple_bit = apple_bit.cut(apple_cutter)

        #sticky out bits on the "apple"
        start_angle = math.pi + math.pi*0.25
        start_pos = np_to_set(np.add(polar(start_angle, circle_radii[0] + apple_wall_thick), circle_positions[0]))
        start_angle90 = start_angle - math.pi/2
        start_dir = polar(start_angle90)

        #doesn't want to slice nicely otherwise
        tiny_tip_r = 0.2
        tip_pos0 = (-self.hour_length*0.35, diamond_distances[1] + self.diamond_thick/2)
        tip_pos0b = (-self.hour_length * 0.35 - tiny_tip_r*2, diamond_distances[1] + self.diamond_thick / 2)

        inner_pos0 = (-self.hour_length*0.25, circle_positions[0][1] + circle_radii[0]*0.1)
        tip_pos1 = (-self.hour_length*0.3, circle_positions[0][1] + circle_radii[0])



        inner_pos1 = np_to_set(np.add(polar(math.pi + math.pi*0.25, circle_radii[1]+apple_wall_thick*0.1), circle_positions[1]))

        #.spline([tip_pos0, inner_pos0], tangents=[(-0.1,1), (1,1)])
        sticky_out = (cq.Workplane("XY").spline([start_pos, tip_pos0], tangents=[start_dir, (-0.1,-1)]).radiusArc(tip_pos0b,tiny_tip_r).spline([tip_pos0b, inner_pos0], tangents=[(-0.2,1), (1,0.5)])
                      .spline([tip_pos1], includeCurrent=True, tangents=[(-1,0), (-1,0.25)]).spline([inner_pos1], includeCurrent=True, tangents=[(1,0.2), (1,0)]).close().mirrorY().extrude(self.thick))

        apple_bit = apple_bit.union(sticky_out)

        start_pos = (second_circle_cutter_pos[0], second_circle_cutter_pos[1] + circle_radii[1])

        end_circle_cutter_avoider_pos = np_to_set(np.add(second_circle_cutter_pos, polar(math.pi*0.4, circle_radii[1]+apple_wall_thick*0.1)))

        end_sticky_out = (cq.Workplane("XY").moveTo(start_pos[0], start_pos[1]).lineTo(start_pos[0], start_pos[1] + apple_wall_thick*0.25)
                          .spline([(0, start_pos[1]-apple_wall_thick)], includeCurrent=True, tangents=[(1,0), (0,-1)])
                          .lineTo(end_circle_cutter_avoider_pos[0], end_circle_cutter_avoider_pos[1]).close().mirrorY().extrude(self.thick))
        # apple_bit = apple_bit.union(end_sticky_out)

        # apple_bit = apple_bit.union(cq.Workplane("XY").circle(0.5).extrude(10).translate(start_pos))
        hand = hand.union(apple_bit)

        apple_end_distance = circle_positions[1][1] + circle_radii[1]

        hand = hand.union(get_stroke_line([(0, diamond_distances[1]), (0, apple_end_distance)], wide=self.basic_width, thick=self.thick))

        end_bit = (cq.Workplane("XY").spline([(-self.basic_width/2, apple_end_distance), (-self.tip_r, self.hour_length - self.tip_r), (0, self.hour_length)], tangents=[(-0.2,1), (0.3,0.8), (1,0)]).lineTo(0, apple_end_distance)
                   .close().mirrorY().extrude(self.thick))

        hand = hand.union(end_bit)

        hand = hand.union(self.rear_extension())


        for distance in diamond_distances:
            hand = hand.union(self.diamond().translate((0, distance)))
        return hand

    def second_hand(self, total_length=30, base_r=6, thick=3, colour=None, balanced=False, fixing_thick=-1):
        hand = cq.Workplane("XY").tag("base")

        return hand

class SmithsPocketWatchHands(HandGenerator):

    def __init__(self, base_r, length, thick, second_base_r=-1, second_thick=-1):
        super().__init__(base_r, length, thick, second_base_r, second_thick)


    def hour_hand(self, colour=None, thick_override=-1):
        hand = cq.Workplane("XY").tag("base").circle(self.base_r).extrude(self.thick)

        hand = hand.union(spade_hand())

        return hand

class Hands:
    '''
    this class generates most of the hands entirely internally - but can now use a "hand generator" class like BaroqueHands.
    This class provides  hour_hand(), minute_hand() and second_hand(length, base_r, thick)

    This helps prevent this class grow and grow.

    The main benefit of this class is the shared features: cutting fixings and adding outlines.

    TODO (long term aspiration) tidy up so this Hands class is more explicitly just teh shared features and the hand styles are all in generators
    '''


    def show_hands(self, show_object, hand_colours=None, position=None, second_hand_pos=None, hour_hand_slot_height=6,
                   time_hours=10, time_minutes=10, time_seconds=0, show_second_hand=True, hand_colours_overrides=None):

        if hand_colours is None:
            #main hand, outline, second hand if different
            hand_colours = ["white", "black"]
            if self.second_hand_centred:
                hand_colours += ["red"]
        if hand_colours_overrides is None:
            #for hands with named colours, allow overriding for the preview
            hand_colours_overrides = {}
        if position is None:
            position = (0,0,0)
        if second_hand_pos is None:
            if self.second_hand_centred:
                second_hand_pos = (0,0,0)
            else:
                second_hand_pos = (position[0], position[1] + self.length * 0.75, 0)

        hands = self.get_in_situ(time_minute=time_minutes, time_hour=time_hours, time_seconds=time_seconds, gap_size=hour_hand_slot_height - self.thick, second_gap_size=CENTRED_SECOND_HAND_BOTTOM_FIXING_HEIGHT)

        for type in HandType:
            for colour in hands[type]:
                show_colour = colour
                description = "{} {} Hand{}".format(self.style.value.capitalize(), type.value.capitalize(), " " + colour.capitalize() if colour is not None else "")
                if show_colour is None:
                    show_colour = hand_colours[0]
                    if type == HandType.SECOND:
                        show_colour = hand_colours[2 % len(hand_colours)]
                if show_colour == "outline":
                    show_colour = hand_colours[1 % len(hand_colours)]
                if show_colour in hand_colours_overrides:
                    show_colour = hand_colours_overrides[show_colour]
                show_colour = Colour.colour_tidier(show_colour)

                if type != HandType.SECOND:
                    show_object(hands[type][colour].translate(position), options={"color": show_colour}, name=description)
                elif show_second_hand:
                    # second hand!! yay
                    secondHand = hands[type][colour].translate(second_hand_pos)
                    show_object(secondHand, options={"color": show_colour}, name=description)


    def __init__(self, style=HandStyle.SIMPLE, minute_fixing="rectangle", hourFixing="circle", second_fixing="rod", minute_fixing_d1=1.5, minute_fixing_d2=2.5,
                 hourfixing_d=3, second_fixing_d=3, length=25, second_length=30, thick=1.6, fixing_offset_deg=0, outline=0, outline_same_as_body=True,
                 chunky = False, second_hand_centred=False, outline_on_seconds=-1, seconds_hand_thick=-1, second_style_override=None, hour_style_override=None, outline_colour=None,
                 second_fixing_thick=-1, outline_thick=LAYER_THICK * 2, include_seconds_hand = False):
        '''
        chunky applies to some styles that can be made more or less chunky - idea is that some defaults might look good with a dial, but look a bit odd without a dial

        This is a bit of a mess, but the hand shapes are mostly generated in getBasicHandShape, with a few styles having their own classes to do the heavy work - I could probably consider combining these back
        now I've done some tidy up.

        There is a caching system for hand shapes, but it only helps with generating outlines and doesn't help with multicolour hands yet

        '''
        self.thick=thick
        #something with shells or outline doesn't behave how I'd expect with thin and narrow hands, ends up with a layer inside the hand for the outline
        #recommend using thicker seconds hands if using an outline
        self.second_thick= seconds_hand_thick
        self.include_seconds_hand = include_seconds_hand
        if self.second_thick < 0:
            self.second_thick = self.thick
        #usually I print multicolour stuff with two layers, but given it's entirely perimeter I think it will look okay with just one
        #one layer does work pretty well, but the elephant's foot is sometimes obvious and it's hard to keep the first layer of white perfect. So switching back to two
        self.outline_thick = outline_thick
        #how much to rotate the minute fixing by
        self.fixing_offset_deg=fixing_offset_deg
        self.length = length
        self.style=style
        self.second_style_override = second_style_override
        self.hour_style_override = hour_style_override

        #some hands have a class that generates the hand - TODO: should all hands extend from this class and do that? This is getting very messy
        self.generator = None

        #for multicolour hands, should the outline be combined with one of the details?
        #WORK IN PROGRESS
        self.outline_colour = outline_colour

        #if true, this second hand is centred through the motion works, and is longer and thinner than the minute hand.
        #not supported for all styles
        #TODO is this needed? is secondLength not enough?
        self.second_hand_centred = second_hand_centred
        self.seconds_hand_through_hole = second_hand_centred

        #the second hand doesn't have the rod go all the way through - how thick should the bit that stops on the end of the rod be?
        self.second_rod_end_thick = self.second_thick / 2

        #try to make the second hand counterbalanced
        self.second_hand_balanced = second_hand_centred

        self.chunky = chunky

        #backwards compat, support old strings
        if isinstance(self.style, str):
            for handStyle in HandStyle:
                if self.style == handStyle.value:
                    self.style = handStyle

        self.minute_fixing=minute_fixing
        self.minute_fixing_d1 = minute_fixing_d1
        self.minute_fixing_d2 = minute_fixing_d2
        #"rod"
        self.second_fixing=second_fixing
        self.second_fixing_d = second_fixing_d
        #NOTE - total thickness of centre of second hand (assumes second_fixing_thick > second_thick )
        self.second_fixing_thick = second_fixing_thick
        if self.second_fixing_thick < 0:
            self.second_fixing_thick = self.thick
        self.second_length= second_length
        if self.second_length == 0:
            raise ValueError("Cannot have second hand of length zero")
        #Add a different coloured outline that is this many mm ratchetThick
        self.outline = outline
        self.outline_on_seconds = outline_on_seconds
        if outline_on_seconds < 0:
            #default to same as the other hands, but can be override. Note that if the outline fails to generate (can struggle on some complicated shapes when small) outline will be ignored
            self.outline_on_seconds = self.outline
        #if true the outline will be part of the same STL as the main body, if false, it'll just be a small sliver
        self.outline_same_as_body = outline_same_as_body

        if self.minute_fixing == "square":
            self.minute_fixing_d2 = self.minute_fixing_d1
            self.minute_fixing= "rectangle"

        self.hour_fixing=hourFixing
        self.hour_fixing_d = hourfixing_d

        self.configure_length(length)
        # was attempting to use a cache, but so many edge cases that I've given up
        self.hand_shapes = {}
        self.outline_shapes = {}
        for hand_type in HandType:
            self.hand_shapes[hand_type] = None
            self.outline_shapes[hand_type] = None

    def configure_motion_works(self, motion_works):
        #configure fixings and thicknesses from the motion works
        self.minute_fixing = motion_works.get_minute_hand_fixing_shape()
        self.minute_fixing_d1 = motion_works.get_minute_hand_square_size()
        self.hour_fixing_d = motion_works.get_hour_hand_hole_d()

        self.thick = motion_works.minute_hand_slot_height

        if self.minute_fixing == "square":
            self.minute_fixing_d2 = self.minute_fixing_d1
            self.minute_fixing= "rectangle"

    def configure_length(self, length, second_length=-1):
        self.length = length
        if second_length > 0:
            self.second_length = second_length
        if self.style == HandStyle.BAROQUE:
            line_width = max(self.length * 0.03, 2.4)
            #TODO tidy up the base_r calculations do this here again (commented out below)
            self.generator = BaroqueHands(base_r=self.hour_fixing_d * 0.75, total_length=self.length, thick=self.thick, line_width=line_width)

        if self.style == HandStyle.FANCY_WATCH:
            #TODO base_r properly?
            self.generator = FancyWatchHands(base_r=self.length*0.1, thick = self.thick, total_length= self.length, outline= self.outline, detail_thick=self.outline_thick)
        if self.style == HandStyle.FANCY_FRENCH:
            self.generator = FancyClockHands(base_r=self.length*0.1, thick = self.thick, length= self.length)



    def cut_fixing(self, hand, hand_type):
        if hand_type == HandType.SECOND and self.second_fixing == "rod":
            #second hand, assuming threaded onto a threaded rod, hole doesn't extend all the way through unless centred seconds hand
            # hand = hand.moveTo(0, 0).circle(self.secondFixing_d / 2).cutThruAll()

            z_offset =self.second_rod_end_thick
            if self.seconds_hand_through_hole:
                z_offset = 0

            '''
            note - the original idea was I cut a thread in the hole on the second hand and it was fixed firmly to the rod, with a standoff from the bearing
            (so it only touched the centre part which rotated with the hand)
            however, over time the second hand became loose and so I ended up clamping it between two nuts. Therefore I'm now going to design it around being
            clamped between two nuts and abandon the standoff
            '''
            # bearing_standoff_thick = 0
            # #mega hacky, review if I ever want to try a 2mm arbour for the escape wheel
            # # bearing = get_bearing_info(3)
            # bearing = None
            #
            # if bearing is not None:
            #     bearing_standoff_thick =  LAYER_THICK*2

            hand = hand.cut(cq.Workplane("XY").moveTo(0,0).circle(self.second_fixing_d / 2).extrude(self.second_fixing_thick - z_offset).translate((0, 0, z_offset)))
            # try:
            # hand = hand.add(cq.Workplane("XY").moveTo(0,0).circle(self.secondFixing_d).circle(self.secondFixing_d / 2).extrude(self.secondFixing_thick - bearing_standoff_thick).translate((0,0,self.secondThick)))
            # if bearing is not None:
            #     hand = hand.add(cq.Workplane("XY").moveTo(0, 0).circle(bearing.inner_safe_d / 2).circle(self.secondFixing_d / 2).extrude(bearing_standoff_thick).translate((0, 0, self.secondThick + self.secondFixing_thick - bearing_standoff_thick)))
            # # except:
            #     hand = hand.workplaneFromTagged("base").moveTo(0, 0).circle(self.secondFixing_d * 0.99).circle(self.secondFixing_d / 2).extrude(self.secondFixing_thick + self.thick)
            return hand


        if hand_type == HandType.MINUTE and self.minute_fixing == "rectangle":
            # TODO fixing_offset
            cutter = cq.Workplane("XY").rect(self.minute_fixing_d1, self.minute_fixing_d2).extrude(self.thick).rotate((0, 0, 0), (0, 0, 1), self.fixing_offset_deg)
            hand = hand.cut(cutter)
        elif hand_type == HandType.MINUTE and self.minute_fixing == "circle":
            hand = hand.moveTo(0, 0).circle(self.minute_fixing_d1 / 2).cutThruAll()
        elif hand_type == HandType.HOUR and self.hour_fixing == "circle":
            #hour hand, assuming circular friction fit
            hand = hand.moveTo(0, 0).circle(self.hour_fixing_d / 2).cutThruAll()
        else:
            #major TODO would be a collet for the minute hand
            raise ValueError("Combination not supported yet")

        return hand
   
    def out_line_is_subtractive(self):
        '''
        If the outline is a negative shell from the outline provided by hand, return true
        if the outline is a positive shell, return false (for hands with thin bits where there isn't enough width)
        '''
        #sword is a bit too pointy, so trying to soften it
        #xmas tree just looks bettery
        #spade and cuckoo only work this way
        if self.style in [HandStyle.CUCKOO, HandStyle.SPADE, HandStyle.XMAS_TREE, HandStyle.SWORD]:#, HandStyle.BREGUET
            return False

        return True

    def get_extra_colours(self):
        #first colour is default
        if self.style == HandStyle.XMAS_TREE:
            #green leaves, red tinsel, brown trunk
            return ["brown", "green", "red", "gold"]

        if self.generator is not None:
            return self.generator.get_colours()

        return [None]

    def get_basic_hand_shape(self, hour=False, minute=False, second=False, colour=None, thick=-1):
        '''
        Get the hand shape without fixing or outline
        '''
        style = self.style
        if self.hour_style_override is not None and hour:
            style = self.hour_style_override
        if self.second_style_override is not None and second:
            style = self.second_style_override
        min_base_r=0
        if minute or hour:
            min_base_r = max(self.minute_fixing_d1, self.minute_fixing_d2, self.hour_fixing_d) * 0.75

        if second:
            min_base_r = self.second_fixing_d * 0.7

        need_base_r = True
        base_r = self.length * 0.12
        length = self.length
        if thick < 0:
            thick = self.thick

        # width = self.length * 0.3
        if hour:
            length = self.length * 0.8
            # if self.style == "simple":
            #     width = width * 1.2
            # if self.style == "square":
            #     width = width * 1.75
        if second:
            thick = self.second_thick
            if self.second_hand_centred:
                # length = self.length
                base_r = self.second_fixing_d * 2
                # hack until I design better seconds hands
                # style = HandStyle.SIMPLE_ROUND
            else:
                length = self.second_length
                base_r = self.second_length * 0.15



        ignoreOutline = False

        hand = cq.Workplane("XY").tag("base")

        # if colour is None and len(self.getExtraColours()) > 0:
        #     colour = self.getExtraColours()[0]

        # if colour is not None:
        #     ignoreOutline = True

        if self.generator is not None:
            if second:
                hand = self.generator.second_hand(total_length=self.second_length, base_r=base_r, thick=self.second_thick, colour=colour, balanced=self.second_hand_balanced, fixing_thick=self.second_fixing_thick)
            elif hour:
                base_r = self.generator.base_r
                hand = self.generator.hour_hand(colour=colour, thick_override=thick)
            else:
                base_r = self.generator.base_r
                hand = self.generator.minute_hand(colour=colour, thick_override=thick)
            if colour not in self.generator.get_colours_which_need_base_r():
                need_base_r = False

        if style == HandStyle.SIMPLE:

            width = self.length * 0.1
            if second:
                width = self.length * 0.05
                # don't let it be smaller than the rounded end!
                base_r = max(base_r, self.length * 0.1 / 2)

            hand = hand.workplaneFromTagged("base").moveTo(0, length / 2).rect(width, length).extrude(thick)

        if style == HandStyle.INDUSTRIAL:

            behind_centre = self.length*0.3

            #square but with a point on the end
            width = self.length * 0.1
            if second:
                width = self.length * 0.075
            if hour:
                width*=1.5


            # base_r = width/2
            need_base_r = False
            tip_length = width/2
            body_length = length - tip_length

            hand = (hand.workplaneFromTagged("base").moveTo(-width/2, -behind_centre).lineTo(-width/2, body_length).lineTo(0, length).lineTo(width/2, body_length).lineTo(width/2, -behind_centre)
                    .close().extrude(thick))

        elif style == HandStyle.SIMPLE_ROUND:
            width = self.length * 0.1
            if second:
                width = self.length * 0.05
                # don't let it be smaller than the rounded end!
                base_r = max(base_r, self.length * 0.1 / 2)

            hand = hand.workplaneFromTagged("base").moveTo(width / 2, 0).line(0, length).radiusArc((-width / 2, length), -width / 2).line(0, -length).close().extrude(thick)

            if second and self.second_hand_balanced:
                area = length * width
                # proportional to moment, assuming uniform thickness and ignoring the curved end and outline
                moment = length / 2 * area
                counterweight_r = width * 2.5
                counterweight_distance = moment / (math.pi * (counterweight_r ** 2))

                hand = hand.workplaneFromTagged("base").moveTo(0, -counterweight_distance / 2).rect(width, counterweight_distance).extrude(thick)
                hand = hand.workplaneFromTagged("base").moveTo(0, -counterweight_distance).circle(counterweight_r).extrude(thick)

        elif style == HandStyle.SIMPLE_POINTED:
            #copypasted and tweaked from SIMPLE_ROUNDED
            width = self.length * 0.1
            point_length = width*2/3
            body_length = length - point_length

            rounded_second_hand = True
            if second:
                centre_width = self.length * 0.12
                tip_width = self.length*0.01 + self.outline*2.5
                # don't let it be smaller than the end!
                base_r = max(base_r, self.length * 0.1 / 2)
                if rounded_second_hand:
                    body_length = length - tip_width/2

            if minute or hour:
                #overriding this is getting super hacky... oh well
                min_base_r = max(self.minute_fixing_d1, self.minute_fixing_d2, self.hour_fixing_d) * 0.5 + 2.5

            hand = hand.workplaneFromTagged("base").moveTo(width / 2, 0).line(0, body_length).lineTo(0, length).lineTo(-width/2, body_length).line(0, -body_length).close().extrude(thick)

            def moment_of_trapezium(length, centre_width, tip_width, chunks=10):
                moment = 0
                chunk_length = length/chunks
                width_per_length = (tip_width - centre_width) / length
                for i in range(chunks):
                    distance = chunk_length * i + chunk_length/2
                    start_width = centre_width + width_per_length * i * chunk_length
                    end_width = centre_width + width_per_length * (i + 1) * chunk_length
                    area = chunk_length * (start_width + end_width)/2
                    moment += distance * area
                return moment

            if second and self.second_hand_balanced:
                # approx
                need_base_r = False
                moment = moment_of_trapezium(length, centre_width, tip_width)
                # TODO we have end width as a function of length, by keeping this triangularish, we know what moment we need to get
                # so we should be able to just calculate the length of the thicker side easily enough
                width_per_length = (centre_width - tip_width) / length

                def counterweight_moment(back_length):
                    back_width = centre_width + back_length * width_per_length
                    moment = moment_of_trapezium(back_length, centre_width, tip_width=back_width)
                    if rounded_second_hand:
                        r = back_width/2
                        moment += (back_length + r/2) * math.pi * (r**2) / 2
                    return moment

                min_length = 0.1
                max_length = length
                test_length = min_length
                counterweight_moment_test = counterweight_moment(test_length)
                error = counterweight_moment_test - moment
                last_error = 1000
                # TODO write a generic binary search solver, this is just copied from BREGUET
                for i in range(100):
                    # print("counterweight difference: {}, test_r:{}".format(error, test_r))

                    if error < 0:
                        # r too small
                        min_length = test_length
                    if error > 0:
                        # too big
                        max_length = test_length
                    if error == 0 or abs(error - last_error) < 0.001:
                        print("best counterweight difference: {}, test_r:{} i {}".format(error, test_length, i))
                        back_length = test_length
                        break

                    last_error = error
                    test_length = (min_length + max_length) / 2
                    counterweight_moment_test = counterweight_moment(test_length)
                    error = counterweight_moment_test - moment


                # back_length_a = (-0.5 * centre_width + math.sqrt(0.25 * centre_width ** 2 + width_per_length * moment)) / (width_per_length / 2)
                # back_length_b = (-0.5 * centre_width - math.sqrt(0.25 * centre_width ** 2 + width_per_length * moment)) / (width_per_length / 2)
                # back_length = max(back_length_a, back_length_b)

                back_width = centre_width + back_length * width_per_length
                if rounded_second_hand:
                    #shell seems to struggle with an inward tapered not-quite-rectangle with a semicircle on the end
                    #so make the rounded bit attach to a rectangle, even a tiny length of one
                    '''
                    fails:
                      /\
                     /  \
                     (___)
                    succeeds:
                        /\
                       /  \
                       |   |
                       (___)
                    '''
                    shell_bodge = 0.01
                    hand = (cq.Workplane("XY").tag("base").moveTo(-back_width / 2, shell_bodge-back_length).line(0,-shell_bodge)
                    .radiusArc((back_width / 2, shell_bodge-back_length-shell_bodge), -back_width/2).line(0,shell_bodge).lineTo(tip_width / 2, body_length-shell_bodge).line(0,shell_bodge)
                    .radiusArc((-tip_width/2, body_length), -tip_width/2).line(0, -shell_bodge).close().extrude(thick))
                else:
                    hand = cq.Workplane("XY").tag("base").moveTo(-back_width/2, -back_length).lineTo(back_width/2, -back_length).lineTo(tip_width/2, body_length).lineTo(0, length).lineTo(-tip_width/2, body_length).close().extrude(thick)
        elif style == HandStyle.ARROWS:
            '''
            Deliberately styled to look like the hands for Tony the Clock
            '''
            base_r = self.length * tony_the_clock["hand_base_r"]/tony_the_clock["minute_hand_length"]
            arrow_base_wide = self.length * tony_the_clock["arrow_width"]/tony_the_clock["minute_hand_length"]
            arrow_length = self.length * tony_the_clock["arrow_length"]/tony_the_clock["minute_hand_length"]
            width = self.length * tony_the_clock["hand_width"]/tony_the_clock["minute_hand_length"]
            fillet = arrow_base_wide*0.1

            hand = hand.workplaneFromTagged("base").moveTo(0, (length - arrow_length)/2).rect(width, length-arrow_length).extrude(thick)
            hand = hand.union(cq.Workplane("XY").moveTo(arrow_base_wide/2, length - arrow_length).lineTo(0, length).lineTo(-arrow_base_wide/2, length - arrow_length).close().extrude(thick).edges("|Z").fillet(fillet))


        elif style == HandStyle.SQUARE:

            if not second:
                base_r = self.length * 0.08

            hand_width = base_r * 2
            hand = hand.workplaneFromTagged("base").moveTo(0, length / 2 - base_r).rect(hand_width, length).extrude(thick)
        elif style == HandStyle.XMAS_TREE:
            trunkWidth = self.length * 0.075
            leafyWidth = length * 0.5
            trunkEnd = length * 0.4
            useTinsel = True
            if minute:
                leafyWidth *= 0.6
            if hour:
                trunkEnd *= 0.9

            # same as the spades
            base_r = self.length * 0.075

            leaves = cq.Workplane("XY").tag("base")
            tinsel = cq.Workplane("XY").tag("base")
            baubles = cq.Workplane("XY").tag("base")
            bauble_r = self.length * 0.03
            tinsel_thick = length * 0.02

            hand = hand.workplaneFromTagged("base").moveTo(0, trunkEnd / 2).rect(trunkWidth, trunkEnd).extrude(thick)

            # rate of change of leaf width with respect to height from the start of the leaf bit
            dLeaf = 0.5 * leafyWidth / (length - trunkEnd)

            spikes = 4
            spikeHeight = (length - trunkEnd) / spikes
            sag = spikeHeight * 0.2
            ys = [trunkEnd + spikeHeight * spike for spike in range(spikes + 1)]
            tinselHeight = spikeHeight * 0.3

            for spike in range(spikes):
                width = leafyWidth - dLeaf * spikeHeight * spike
                left = (-width / 2, ys[spike])
                right = (width / 2, ys[spike])
                topLeft = (-width / 4, ys[spike + 1])
                topRight = (width / 4, ys[spike + 1])
                tinselTopLeft = (left[0], left[1] + tinselHeight)
                tinselTopRight = (right[0], right[1] + tinselHeight)
                if spike == spikes - 1:
                    topLeft = topRight = (0, length)
                leaves = leaves.workplaneFromTagged("base").moveTo(topLeft[0], topLeft[1]).sagittaArc(endPoint=left, sag=sag / 2).sagittaArc(endPoint=right, sag=-sag). \
                    sagittaArc(endPoint=topRight, sag=sag / 2).close().extrude(thick)
                # tinsel = tinsel.workplaneFromTagged("base").moveTo(tinselTopLeft[0], tinselTopLeft[1]).lineTo(left[0], left[1]).sagittaArc(endPoint=right, sag=-sag). \
                #     lineTo(tinselTopRight[0], tinselTopRight[1]).sagittaArc(endPoint=tinselTopLeft, sag=sag).close().extrude(thick)

            tinsel_circle_centres = [(leafyWidth * 0.6, length), (-leafyWidth * 0.6, length * 1.2), (leafyWidth * 0.6, length * 1.4)]

            for circle_centre in tinsel_circle_centres:
                circle_r = length - trunkEnd
                tinsel = tinsel.workplaneFromTagged("base").moveTo(circle_centre[0], circle_centre[1]).circle(circle_r).circle(circle_r - tinsel_thick).extrude(thick)

            bauble_positions = [(leafyWidth * 0.1, length * 0.5), (-leafyWidth * 0.1, length * 0.75)]

            for pos in bauble_positions:
                baubles = baubles.workplaneFromTagged("base").moveTo(pos[0], pos[1]).circle(bauble_r).extrude(thick)
                baubles = baubles.workplaneFromTagged("base").moveTo(pos[0], pos[1] + base_r * 0.3).rect(bauble_r * 0.3, bauble_r).extrude(thick)

            #
            tinsel = tinsel.intersect(leaves)
            if useTinsel:
                leaves = leaves.cut(tinsel)
                # baubles = baubles.cut(tinsel)
                tinsel = tinsel.cut(baubles)

            leaves = leaves.cut(baubles)

            if colour is None:
                hand = hand.union(leaves)
                hand = hand.union(baubles)
                if useTinsel:
                    hand = hand.union(tinsel)
            elif colour == "brown":
                hand = hand.cut(leaves)
                if useTinsel:
                    hand = hand.cut(tinsel)
            elif colour == "green":
                hand = leaves
                need_base_r = False
            elif colour == "red":
                hand = tinsel
                need_base_r = False
            elif colour == "gold":
                hand = baubles
                need_base_r = False



        elif style == HandStyle.SYRINGE:

            syringe_width = self.length * 0.1
            if hour:
                syringe_width = self.length * 0.15

            if second:
                syringe_width = length * 0.2

            syringe_length = length * 0.7

            syringe_startY = (length - syringe_length) / 2

            syringe_end_length = syringe_width / 2

            base_wide = syringe_width * 0.25

            tip_wide = 3  # syringe_width*0.1
            base_r = base_r * 0.6
            if second:
                tip_wide = 1
                syringe_width = base_r * 2

            if second:
                hand = hand.workplaneFromTagged("base").moveTo(0, 0).lineTo(-syringe_width / 2, 0)
            else:
                hand = hand.workplaneFromTagged("base").moveTo(0, 0).lineTo(-base_wide / 2, 0)

            hand = hand.lineTo(-syringe_width / 2, syringe_startY).line(0, syringe_length - syringe_end_length) \
                .lineTo(-tip_wide / 2, syringe_startY + syringe_length).lineTo(-tip_wide / 2, length).lineTo(0, length + tip_wide / 2).mirrorY().extrude(thick)
        elif style == HandStyle.CIRCLES:

            tip_r = self.length * 0.05
            base_r = self.length * 0.2
            border = self.length * 0.045
            if second:
                base_r = length * 0.2
                tip_r = length * 0.05
                border = length * 0.045

            r_rate = (tip_r - base_r) / length

            overlap = border
            r = base_r
            y = 0  # -(base_r-overlap)

            while y < length:

                r = base_r + y * r_rate
                if y > 0:
                    y += r - overlap / 2
                hand = hand.workplaneFromTagged("base").moveTo(0, y).circle(r)
                if not second and y > base_r:
                    hand = hand.circle(r - border)
                hand = hand.extrude(thick)
                y += r - overlap / 2
            if not second:
                # is this too much? # TODO line up cutter with hand!
                hand = Gear.cutStyle(hand, base_r * 0.9, self.hour_fixing_d * 0.7, style=GearStyle.CIRCLES)
            base_r = self.hour_fixing_d * 0.6

            # circle on the other side (I'm sure there's a way to set up initial y to do this properly)
            # actually makes it quite hard to read the time!
            # y=-(base_r-overlap/2)
            # r = base_r + y * r_rate
            # y -= r - overlap / 2
            # hand = hand.workplaneFromTagged("base").moveTo(0, y).circle(r)
            # if not second:
            #     hand = hand.circle(r - border)
            # hand = hand.extrude(thick)

        elif style == HandStyle.SWORD:

            base_r = base_r * 0.6
            need_base_r = False

            base_width = base_r * 2.5
            rear_length = length * 0.3

            if rear_length < base_r * 2:
                rear_length = base_r * 2

            hand = hand.workplaneFromTagged("base").moveTo(-base_width / 2, 0).lineTo(0, length).lineTo(base_width / 2, 0).lineTo(0, -rear_length).close().extrude(thick)

        elif style == HandStyle.MOON:
            #similar to brequet but with two circles forming a moon-like shape

            #copypasted from BREGUET below
            hand_width = self.length * 0.06
            tip_width = self.length * 0.02

            circle_r = self.length * 0.125
            if hour:
                circle_r*=1.05
            circle_y = length * 0.65
            # #point where teh arm starts to bend towards the tip
            bend_point_y = circle_y
            # if self.chunky:
            #     hand_width = self.length * 0.06
            #     tip_width = self.length * 0.02  # *0.0125
            #     circle_r = self.length * 0.1
            #     base_r = circle_r
            # else:
            base_r = self.length * 0.075

            moon_thickness = hand_width*0.75
            inner_moon_r = circle_r * 0.6

            hand = hand.workplaneFromTagged("base").moveTo(0, bend_point_y / 2).rect(hand_width, bend_point_y).extrude(thick)
            # some sizes are complaining the radius isn't long enough to complete the arc, so bodge it a bit
            hand = hand.workplaneFromTagged("base").moveTo(-hand_width / 2, bend_point_y).lineTo(-tip_width / 2, length).radiusArc((tip_width / 2, length), tip_width / 2 + 0.01).lineTo(hand_width / 2, bend_point_y).close().extrude(thick)
            if second:
                # this is out the back, extend the main body of the arm
                hand = hand.workplaneFromTagged("base").moveTo(0, circle_y / 2).rect(hand_width, abs(circle_y)).extrude(thick)
                # hand = hand.workplaneFromTagged("base").moveTo(0,0).circle(base_r).extrude(thick)

            hand = hand.workplaneFromTagged("base").moveTo(0, circle_y).circle(circle_r).extrude(thick)
            hand = hand.faces(">Z").moveTo(0, circle_y).circle(circle_r - moon_thickness).cutThruAll()

            hand = hand.union(cq.Workplane("XY").moveTo(0,circle_y - (circle_r - inner_moon_r)).circle(inner_moon_r).circle(inner_moon_r - moon_thickness).extrude(thick))

        elif style == HandStyle.BREGUET:

            hand_width = self.length * 0.04
            tip_width = self.length * 0.01

            circle_r = self.length * 0.08
            circle_y = length * 0.75
            # #point where teh arm starts to bend towards the tip
            bend_point_y = circle_y + circle_r - hand_width/2

            if self.chunky:
                hand_width = self.length * 0.06
                tip_width = self.length * 0.02  # *0.0125
                circle_r = self.length * 0.1
                base_r = circle_r
            else:
                base_r = self.length * 0.075

            if hour:
                hand_width *= 1.16
                circle_r = self.length * 0.125
                circle_y = length * 0.65
                bend_point_y = circle_y + circle_r - hand_width/2
            if second:
                if self.second_hand_centred:
                    base_r = self.length * 0.05 # 0.04
                    hand_width = self.length * 0.055
                    # tipWidth = self.length * 0.015
                    circle_y = - self.length * 0.3
                    circle_y = - self.length * 0.5
                    bend_point_y = self.length * 0.75

                    '''
                    Given a chosen circleY (distance for the hollow circle from the axle), find a radius which should result in a balanced second hand
                    this could be done analytically, but it was quicker to write a binary search than do the algebra
                    '''

                    other_side_area = bend_point_y * hand_width + (length - bend_point_y) * (hand_width + tip_width) / 2
                    # accurately(ish) counterbalance the second hand (treats tip as trapezium)
                    # this is currently adjusting size of circle based on my chosen length, but would it look better if I instead calculated length to keep size of circle same as one of the other hands?
                    # but both circles on hour and minute hand are difference sizes, so I'll leave it like this

                    moment = (bend_point_y ** 2) * hand_width / 2 + ((length - bend_point_y) * (tip_width + hand_width) / 2) * (length - (length - bend_point_y) / 2)

                    def counterweight_moment(circle_r, distance):
                        return distance * (math.pi * circle_r ** 2 - math.pi * (circle_r - hand_width) ** 2) + (hand_width * (distance - circle_r) ** 2) / 2

                    min_r = hand_width * 2.1
                    max_r = abs(circle_y)
                    test_r = min_r
                    counterweight_moment_test = counterweight_moment(test_r, abs(circle_y))
                    error = counterweight_moment_test - moment
                    last_error = 1000
                    # TODO write a generic binary search solver, this is just a variant over the one used a few times in escapements
                    for i in range(100):
                        # print("counterweight difference: {}, test_r:{}".format(error, test_r))

                        if error < 0:
                            # r too small
                            min_r = test_r
                        if error > 0:
                            # too big
                            max_r = test_r
                        if error == 0 or abs(error - last_error) < 0.001:
                            print("best counterweight difference: {}, test_r:{} i {}".format(error, test_r, i))
                            circle_r = test_r
                            break

                        last_error = error
                        test_r = (min_r + max_r) / 2
                        counterweight_moment_test = counterweight_moment(test_r, abs(circle_y))
                        error = counterweight_moment_test - moment
                    # possible_circle_rs = [r for r in range(handWidth*2.5,abs(circleY),0.1)]
                    #
                    # for

                    # THIS IS WRONG - I'm only comparing area here, not moments! oops
                    # circleR = (other_side_area - abs(circleY) * handWidth + math.pi * handWidth**2)/((2*math.pi - 1)*handWidth)



                else:
                    hand_width = self.length * 0.03
                    circle_r = self.length * 0.04
                    circle_y = - self.length * 0.04 * 2.5
                    base_r = circle_r
                    bend_point_y = abs(circle_y)
                # ignoreOutline=True

            fudge=0.0001
            hand = hand.workplaneFromTagged("base").moveTo(0, bend_point_y / 2).rect(hand_width, bend_point_y).extrude(thick)
            # some sizes are complaining the radius isn't long enough to complete the arc, so bodge it a bit
            #the little tiny straight bit before the rounded end fixes the shell so we can add outlines. *shrug*
            hand = hand.workplaneFromTagged("base").moveTo(-hand_width / 2, bend_point_y).lineTo(-tip_width / 2, length).line(0,fudge).radiusArc((tip_width / 2, length+fudge), tip_width / 2 + 0.01).line(0,-fudge).lineTo(hand_width / 2, bend_point_y).close().extrude(thick)
            if second:
                # this is out the back, extend the main body of the arm
                hand = hand.workplaneFromTagged("base").moveTo(0, circle_y / 2).rect(hand_width, abs(circle_y)).extrude(thick)
                # hand = hand.workplaneFromTagged("base").moveTo(0,0).circle(base_r).extrude(thick)

            hand = hand.workplaneFromTagged("base").moveTo(0, circle_y).circle(circle_r).extrude(thick)
            hand = hand.faces(">Z").moveTo(0, circle_y).circle(circle_r - hand_width).cutThruAll()



        elif style == HandStyle.SPADE:
            base_r = self.length * 0.075
            hand_width = self.length * 0.05
            if second:
                hand_width = self.length * 0.025
                base_r = self.length * 0.02

            # for the bottom of the spade, not the usual baseR
            spadeBaseR = length * 0.05 * 2

            if hour:
                spadeBaseR *= 1.4

            spadeTopLength = length * 0.4
            spadeTipWidth = hand_width * 0.5
            tipLength = length * 0.1

            # if second:
            #     spadeTipWidth*=0.9

            # length = length - tipLength - spadeTopLength

            armLength = length - tipLength - spadeTopLength

            midPoint = (spadeBaseR * 0.75, armLength + spadeTopLength * 0.3)
            tipBase = (spadeTipWidth / 2, armLength + spadeTopLength)
            tipEndSide = (spadeTipWidth / 2, armLength + spadeTopLength + tipLength)
            tip = (0, armLength + spadeTopLength + tipLength + spadeTipWidth / 2)

            hand = hand.workplaneFromTagged("base").moveTo(0, armLength / 2).rect(hand_width, armLength).extrude(thick)

            hand = hand.workplaneFromTagged("base").moveTo(0, armLength - spadeBaseR).radiusArc((spadeBaseR, armLength), -spadeBaseR) \
                .tangentArcPoint(midPoint, relative=False) \
                .tangentArcPoint(tipBase, relative=False).tangentArcPoint(tipEndSide, relative=False).tangentArcPoint(tip, relative=False) \
                .mirrorY().extrude(thick)

        elif style == HandStyle.CUCKOO:

            end_d = self.length * 0.3 * 0.1
            centrehole_y = length * 0.6
            width = self.length * 0.3
            if second:
                width = length * 0.3
                end_d = length * 0.3 * 0.1
                ignoreOutline = True
                base_r = self.second_length * 0.12
            centrehole_r = width * 0.15

            # hand = hand.workplaneFromTagged("base").moveTo(width * 0.4, 0).threePointArc((end_d *0.75, length/2),(end_d / 2, length)).radiusArc(
            #    (-end_d / 2, length), -end_d / 2).threePointArc((-end_d *0.75, length/2),(-width * 0.4, 0)).close().extrude(ratchetThick)

            # hand = hand.workplaneFromTagged("base").moveTo(width * 0.25, length*0.3).lineTo(end_d / 2, length).radiusArc(
            #     (-end_d / 2, length), -end_d / 2).lineTo(-width * 0.25, length*0.3).close().extrude(ratchetThick)
            hand = hand.workplaneFromTagged("base").moveTo(width * 0.2, length * 0.3).lineTo(end_d / 2, length).threePointArc((0, length + end_d / 2), (-end_d / 2, length)).lineTo(-width * 0.2, length * 0.3).close().extrude(thick)

            # extra round bits towards the end of the hand
            little_sticky_out_dist = width * 0.3
            little_sticky_out_d = width * 0.35
            little_sticky_out_y = centrehole_y - centrehole_r * 0.4
            little_sticky_out_d2 = width * 0.125
            little_sticky_out_dist2 = width * 0.2
            stickyoutblobs = hand.workplaneFromTagged("base")
            # the two smaller blobs, justcircles
            for angle_d in [45]:
                angle = math.pi * angle_d / 180
                # just circle, works but needs more
                stickyoutblobs = stickyoutblobs.moveTo(0 + math.cos(angle) * little_sticky_out_dist2, centrehole_y + little_sticky_out_d2 * 0.25 + math.sin(angle) * little_sticky_out_dist2).circle(little_sticky_out_d2)
                # hand =  hand.workplaneFromTagged("base").moveTo(0+math.cos(angle+math.pi/2)*little_sticky_out_d/2,centrehole_y+math.sin(angle+math.pi/2)*little_sticky_out_d/2).lineTo()
                # hand = hand.workplaneFromTagged("base").moveTo(0, centrehole_y).rot
            hand = stickyoutblobs.mirrorY().extrude(thick)

            # hand = hand.workplaneFromTagged("base").moveTo(0, centrehole_y-centrehole_r).spline([(little_sticky_out_dist*1.6,centrehole_y-little_sticky_out_d*0.6),(little_sticky_out_dist*1.6,centrehole_y+little_sticky_out_d*0.2),(0,centrehole_y)],includeCurrent=True)\
            #     .mirrorY().extrude(ratchetThick)
            hand = hand.workplaneFromTagged("base").moveTo(0, little_sticky_out_y - little_sticky_out_d / 2 + little_sticky_out_d * 0.1).lineTo(little_sticky_out_dist, little_sticky_out_y - little_sticky_out_d / 2).threePointArc(
                (little_sticky_out_dist + little_sticky_out_d / 2, little_sticky_out_y), (little_sticky_out_dist, little_sticky_out_y + little_sticky_out_d / 2)).line(-little_sticky_out_dist, 0) \
                .mirrorY().extrude(thick)

            petalend = (width * 0.6, length * 0.45)

            # petal-like bits near the centre of the hand
            hand = hand.workplaneFromTagged("base").lineTo(width * 0.1, 0).spline([(petalend[0] * 0.3, petalend[1] * 0.1), (petalend[0] * 0.7, petalend[1] * 0.4), (petalend[0] * 0.6, petalend[1] * 0.75), petalend], includeCurrent=True) \
                .line(0, length * 0.005).spline([(petalend[0] * 0.5, petalend[1] * 0.95), (0, petalend[1] * 0.8)], includeCurrent=True).mirrorY()
            # return hand
            hand = hand.extrude(thick)

            # sticky out bottom bit for hour hand
            if hour:
                hand = hand.workplaneFromTagged("base").lineTo(width * 0.4, 0).lineTo(0, -width * 0.9).mirrorY().extrude(thick)
                # return hand
            # cut bits out
            # roudn bit in centre of knobbly bit
            hand = hand.moveTo(0, centrehole_y).circle(centrehole_r).cutThruAll()
            heartbase = base_r + length * 0.025  # length*0.175

            hearttop = length * 0.425
            heartheight = hearttop - heartbase
            heartwidth = length * 0.27 * 0.3  # width*0.3
            # heart shape (definitely not a dick)
            # hand = hand.moveTo(0, heartbase).spline([(heartwidth*0.6,heartbase*0.9),(heartwidth*0.8,heartbase+heartheight*0.15),(heartwidth*0.6,heartbase+heartheight*0.4),(heartwidth*0.3,heartbase + heartheight/2)],includeCurrent=True).lineTo(heartwidth*0.5,heartbase + heartheight*0.75).lineTo(0,hearttop).mirrorY().cutThruAll()
            hand = hand.moveTo(0, heartbase).spline(
                [(heartwidth * 0.6, heartbase * 0.9), (heartwidth * 0.8, heartbase + heartheight * 0.15),
                 (heartwidth * 0.6, heartbase + heartheight * 0.4), (heartwidth * 0.3, heartbase + heartheight / 2)],
                includeCurrent=True).lineTo(heartwidth * 0.5, heartbase + heartheight * 0.75).lineTo(0,
                                                                                                     hearttop).mirrorY()  # .cutThruAll()
            # return hand.extrude(ratchetThick*2)
            try:
                hand = hand.cutThruAll()
            except:
                print("Unable to cut detail in cuckoo hand")

        if base_r < min_base_r:
            base_r = min_base_r

        if need_base_r:
            hand = hand.workplaneFromTagged("base").circle(radius=base_r).extrude(thick)

            if second and self.second_fixing == "rod":
                try:
                    hand = hand.union(cq.Workplane("XY").moveTo(0, 0).circle(self.second_fixing_d).circle(self.second_fixing_d / 2).extrude(self.second_fixing_thick).translate((0, 0, self.second_thick)))
                except:
                    hand = hand.workplaneFromTagged("base").moveTo(0, 0).circle(self.second_fixing_d * 0.99).circle(self.second_fixing_d / 2).extrude(self.second_fixing_thick + self.thick)


        return hand


    def get_hand(self, hand_type=HandType.MINUTE, generate_outline=False, colour=None):
        '''
        #either hour, minute or second hand (for now?)
        if provide a colour, return the layer for just that colour (for novelty hands with lots of colours)

        if generate_outline is true this is just the shape of the hand used to generate an outline - this skips cutting a hole for the fixing
        '''

        thick = self.thick

        if generate_outline and self.thick < self.outline*2:
            #if twice the outline can't fit inside the thickness, shell won't work. so create a hand that's extra thick purely for the shell generation
            #then we can use the outline from that on the normal thickness hand
            thick = self.outline*2.5

        hand = self.get_basic_hand_shape(hand_type == HandType.HOUR, hand_type == HandType.MINUTE, hand_type == HandType.SECOND, colour=colour, thick=thick)

        if hand is None:
            #should only happen if multicolour hands don't have all colours on all hands
            return None


        #doen't work, I think this can get a bit recursive. Need to re-think.
        # if self.outline_colour is not None and self.outline_colour == colour:
        #     colour_detail = self.getHand(hand_type=hand_type, generate_outline=True)
        #     if colour_detail is not None:
        #         hand = hand.union(colour_detail)

        # if generate_outline and self.outline_shapes[hand_type] is not None:
        #     #the outline is cached
        #     return self.outline_shapes[hand_type]
        #
        #
        # hand = None
        # #draw a circle for the base of the hand
        # if self.hand_shapes[hand_type] is not None and False:
        #     #fetch out the cache (disabling cache for now - doesn't work with colours)
        #     hand = self.hand_shapes[hand_type]
        # else:
        #     hand = self.getBasicHandShape(hand_type == HandType.HOUR, hand_type == HandType.MINUTE, hand_type == HandType.SECOND, colour)
        #     #cache the basic shape as it's re-used in generating the outline
        #     self.hand_shapes[hand_type] = hand
        # # if second:
        #     hand = hand.workplaneFromTagged("base").moveTo(0, 0).circle(self.secondFixing_d).extrude(self.secondFixing_thick + thick)

        #cut the fixing AFTERWARDS so we don't accidentally try and make a shell around the hand fixing if outline is not subtractive

        thick = self.thick
        outline_wide = self.outline
        if hand_type == HandType.SECOND:
            outline_wide = self.outline_on_seconds
            thick = self.second_thick

        if outline_wide > 0:# and not ignoreOutline:
            if self.out_line_is_subtractive():
                #the outline cuts into the hand shape

                if generate_outline:
                    #we are generating the outline - hand is currently the default hand shape

                    #use a negative shell to get a thick line just inside the edge of the hand

                    #this doesn't work for fancier shapes - I think it can't cope if there isn't space to extrude the shell without it overlapping itself?
                    #works fine for simple hands, not for cuckoo hands
                    try:
                        shell = hand.shell(-outline_wide).translate((0,0,-outline_wide))
                    except Exception as e:
                        print("Unable to give outline to {} {} hand: ".format(hand_type.value, self.style.value), type(e), e)
                        return None
                    # hand_minus_shell = hand.cut(shell)
                    # return shell
                    slab_thick = self.outline_thick

                    bigSlab = cq.Workplane("XY").rect(self.length*3, self.length*3).extrude(slab_thick)

                    outline = shell.intersect(bigSlab)

                    if self.outline_same_as_body:
                        thin_not_outline = hand.intersect(bigSlab).cut(outline)
                        outline_with_back_of_hand = hand.cut(thin_not_outline)
                        try:
                            outline_with_back_of_hand = self.cut_fixing(outline_with_back_of_hand, hand_type)
                        except:
                            pass
                        self.outline_shapes[hand_type] = outline_with_back_of_hand
                        return outline_with_back_of_hand
                    else:
                        self.outline_shapes[hand_type] = outline
                        return outline
                else:
                    outlineShape = self.get_hand(hand_type, generate_outline=True)
                    #chop out the outline from the shape
                    if outlineShape is not None:
                        hand = hand.cut(outlineShape)
            else:#positive shell - outline is outside the shape
                #for things we can't use a negative shell on, we'll make the whole hand a bit bigger
                if generate_outline:
                    shell = hand.shell(outline_wide)
                    slabThick = self.outline_thick
                    if self.outline_same_as_body:
                        slabThick = thick
                    bigSlab = cq.Workplane("XY").rect(self.length * 3, self.length * 3).extrude(slabThick)

                    outline = shell.intersect(bigSlab)

                    if self.outline_same_as_body:
                        #add the hand, minus a thin layer on the front
                        outline = outline.union(hand.cut(cq.Workplane("XY").rect(self.length * 3, self.length * 3).extrude(self.outline_thick)))
                        outline = self.cut_fixing(outline, hand_type)
                        self.outline_shapes[hand_type] = outline
                        return outline
                    self.outline_shapes[hand_type] = outline
                    return outline
                else:
                    #this is the hand, minus the outline
                    if self.outline_same_as_body:
                        bigSlab = cq.Workplane("XY").rect(self.length * 3, self.length * 3).extrude(thick)
                        hand = hand.intersect(bigSlab)
                    else:
                        try:
                            outlineShape = self.get_hand(hand_type, generate_outline=True)
                            # chop out the outline from the shape

                            #make the whole hand bigger by the outline amount
                            shell = hand.shell(outline_wide)#.intersect(cq.Workplane("XY").rect(self.length * 3, self.length * 3).extrude(thick-self.outlineThick).translate((0,0,self.outlineThick)))

                            bigSlab = cq.Workplane("XY").rect(self.length * 3, self.length * 3).extrude(thick)

                            hand = hand.union(shell.intersect(bigSlab))
                            if outlineShape is not None:
                                hand = hand.cut(outlineShape)


                        except:
                            print("Unable to add external outline to hand: {} {}".format(hand_type.value, self.style.value))
                        hand = self.cut_fixing(hand, hand_type)
                        return hand

        if not generate_outline:
            try:
                hand = self.cut_fixing(hand, hand_type)
            except:
                pass

        return hand

    def get_in_situ(self,time_minute=10, time_hour=10, time_seconds=0, gap_size=0, second_gap_size=CENTRED_SECOND_HAND_BOTTOM_FIXING_HEIGHT):
        '''
        get individual hands in the right position for assembling a model
        '''

        minuteAngle = - 360 * (time_minute / 60)
        hourAngle = - 360 * (time_hour + time_minute / 60) / 12
        secondAngle = -360 * (time_seconds / 60)

        hands = {HandType.MINUTE: {},
                 HandType.HOUR: {},
                 HandType.SECOND: {}
                 }


        for colour in self.get_extra_colours():
            #None means the main hand colour
            for type in HandType:
                hand = self.get_hand(hand_type=type, colour=colour)
                if hand is not None:
                    hands[type][colour] = hand

        if self.outline > 0:
            for type in HandType:
                try:
                    hand = self.get_hand(hand_type=type, generate_outline=True)
                    if hand is not None:
                        hands[type]["outline"] = hand
                except:
                    pass

        #rotate and translate into position
        for colour in hands[HandType.MINUTE]:
            hands[HandType.MINUTE][colour] = hands[HandType.MINUTE][colour].rotate((0,0,0),(0,1,0),180).translate((0, 0, self.thick * 2 + gap_size)).rotate((0, 0, 0), (0, 0, 1), minuteAngle)
        for colour in hands[HandType.HOUR]:
            hands[HandType.HOUR][colour] = hands[HandType.HOUR][colour].rotate((0,0,0),(0,1,0),180).translate((0, 0, self.thick)).rotate((0, 0, 0), (0, 0, 1), hourAngle)
        for colour in hands[HandType.SECOND]:
            #relative position of second hand is irrelevant because Hands object doesn't know where to put it, so it's only valid for centred second hand
            #self.second_thick
            hands[HandType.SECOND][colour] = hands[HandType.SECOND][colour].rotate((0,0,0),(0,1,0),180).translate((0, 0, self.second_fixing_thick)).rotate((0, 0, 0), (0, 0, 1), secondAngle)

            if self.second_hand_centred:
                hands[HandType.SECOND][colour] = hands[HandType.SECOND][colour].translate((0, 0, self.thick * 2 + gap_size + second_gap_size))
            # else:
            #     hands[HandType.SECOND][colour] = hands[HandType.SECOND][colour].translate((0, self.length * 0.5, 0))

        return hands

    def get_assembled(self, time_minute=10, time_hour=10, time_seconds=0, gap_size=0, include_seconds=True, flatten=False):
        '''
        get minute and hour hands assembled centred around 0,0
        gap_size is how much gap between top of hour hand and bottom of minute hand
        '''

        minuteAngle = - 360 * (time_minute / 60)
        hourAngle = - 360 * (time_hour + time_minute / 60) / 12
        secondAngle = -360 * (time_seconds / 60)

        minuteHand = cq.Workplane("XY")
        hourHand = cq.Workplane("XY")
        secondHand = cq.Workplane("XY")

        for colour in self.get_extra_colours():
            minuteHand = minuteHand.add(self.get_hand(hand_type=HandType.MINUTE, colour=colour))
            hourHand = hourHand.add(self.get_hand(hand_type=HandType.HOUR, colour=colour))
            secondHand = secondHand.add(self.get_hand(hand_type=HandType.SECOND, colour = colour))

        if self.outline > 0:
            minuteHand = minuteHand.add(self.get_hand(hand_type=HandType.MINUTE, generate_outline=True))
            hourHand = hourHand.add(self.get_hand(hand_type=HandType.HOUR, generate_outline=True))
            try:
                secondHand = secondHand.add(self.get_hand(hand_type=HandType.SECOND, generate_outline=True))
            except:
                pass

        minuteHand = minuteHand.mirror().translate((0, 0, 0 if flatten else self.thick*2 + gap_size)).rotate((0, 0, 0), (0, 0, 1), minuteAngle)
        hourHand = hourHand.mirror().translate((0, 0, 0 if flatten else self.thick)).rotate((0, 0, 0), (0, 0, 1), hourAngle)
        secondHand = secondHand.mirror().translate((0, 0, 0 if flatten else self.second_thick)).rotate((0, 0, 0), (0, 0, 1), secondAngle)

        if self.second_hand_centred:
            secondHand = secondHand.translate((0,0,self.thick*3))
        else:
            secondHand = secondHand.translate((0, self.length * 0.5, 0))

        #add, not union, so we keep the detail visible
        all = minuteHand.add(hourHand)

        if include_seconds:
            all = all.add(secondHand)

        return all

    def get_BOM(self):
        bom = BillOfMaterials("Hands", assembly_instructions="Most hands are multicolour prints with multiple STLs per hand")
        #could split this further into different hands as subcomponents, but I don't think there's any actual advantage other than pretty previews
        bom.add_model(self.get_assembled(include_seconds=self.include_seconds_hand))

        bom.add_printed_parts(self.get_printed_parts())

        return bom

    def get_printed_parts(self):
        parts = []
        colours = self.get_extra_colours()

        for colour in colours:
            colour_string = "_" + colour if colour is not None else ""

            parts.append(BillOfMaterials.PrintedPart(f"hand_hour{colour_string}", self.get_hand(hand_type=HandType.HOUR, colour=colour)))
            parts.append(BillOfMaterials.PrintedPart(f"hand_minute{colour_string}", self.get_hand(hand_type=HandType.MINUTE, colour=colour)))
            if self.include_seconds_hand:
                parts.append(BillOfMaterials.PrintedPart(f"hand_second{colour_string}", self.get_hand(hand_type=HandType.SECOND, colour=colour)))

        if self.outline > 0:
            parts.append(BillOfMaterials.PrintedPart("hand_hour_outline", self.get_hand(hand_type=HandType.HOUR, generate_outline=True)))
            parts.append(BillOfMaterials.PrintedPart("hand_minute_outline", self.get_hand(hand_type=HandType.MINUTE, generate_outline=True)))
            if self.include_seconds_hand:
                secondoutline = self.get_hand(hand_type=HandType.SECOND, generate_outline=True)
                if secondoutline is not None:
                    parts.append(BillOfMaterials.PrintedPart("hand_second_outline", secondoutline))
        return parts

    def output_STLs(self, name="clock", path="../out"):

        colours = self.get_extra_colours()

        for colour in colours:
            colour_string = "_"+colour if colour is not None else ""
            out = os.path.join(path, "{}_hand_hour{}.stl".format(name, colour_string))
            print("Outputting ", out)
            exporters.export(self.get_hand(hand_type=HandType.HOUR, colour=colour), out)

            out = os.path.join(path, "{}_hand_minute{}.stl".format(name, colour_string))
            print("Outputting ", out)
            exporters.export(self.get_hand(hand_type=HandType.MINUTE, colour=colour), out)

            out = os.path.join(path, "{}_hand_second{}.stl".format(name, colour_string))
            print("Outputting ", out)
            exporters.export(self.get_hand(hand_type=HandType.SECOND, colour=colour), out)

        if self.outline > 0:
            out = os.path.join(path, "{}_hand_hour_outline.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_hand(hand_type=HandType.HOUR, generate_outline=True), out)

            out = os.path.join(path, "{}_hand_minute_outline.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_hand(hand_type=HandType.MINUTE, generate_outline=True), out)
            try:
                secondoutline = self.get_hand(hand_type=HandType.SECOND, generate_outline=True)
                if secondoutline is not None:
                    out = os.path.join(path, "{}_hand_second_outline.stl".format(name))
                    print("Outputting ", out)
                    exporters.export(secondoutline, out)
            except:
                print("Unable to export second hand outline")