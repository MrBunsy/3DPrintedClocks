import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
from .types import *
from .utility import *
from .cuckoo_bits import roman_numerals
import numpy as np
import os
from .cosmetics import tony_the_clock

class MoonPhaseComplication2D:
    def __init__(self, motion_works):
        '''
        Simple 2D 29.5 day cycle moon phase complication

        Plan:
        single pin on the BACK of the hour holder gear, and a 158 (29.5*4) toothed gear with two pictures of the moon
        The dial will have an addition section near the top which is a semicricle with two semicircles on either side. As the disc with two moons rotates
        the moon will pass the first semicircle until it's a full moon in the centre then then slowly go behind the second semicircle

        A small sprung arm will hold the gear in place so it can only move when the pin on the hour wheel goes past a tooth every 12 hours


        lunar year says wiki is 354.36707 so 29.5306 days so a ratio from the hour wheel of 59.06
        29.53059 days

        alternative idea:
        just gear it down and have another friction fitting for the moon disc
        '''
        self.lunar_month_hours = 29.53059 * 24.0

        #we want to rotate once every two lunar months (as have two moons on the dial) and we're geared off the hour hand (12 hours)
        #ratio should be aprox 1/118
        self.ratio = 12 / (self.lunar_month_hours * 2)
        self.motion_works = motion_works

        #don't think I can do this in one wheel without using the conventional pins mechanism
        self.wheel_count = 2

        pinion_min=9
        pinion_max = 20
        wheel_min=80
        wheel_max = 160

        '''
        Gear train  is "backwards" with pinions driving wheels because we're gearing down:
        
        hour wheel, with a new pinion attached -> arbour 0 (driven by pinion 0) -> wheel 1 with the 
        
        
        '''

        # hour_wheel_teeth = self.motion_works.get_hour_wheel_teeth()
        #if we start with this number of teeth on the pinion then it might fit without making the module size too big
        pinion_on_hour_wheel = self.motion_works.get_cannon_pinion_teeth() + 3
        # for pinion_on_hour_wheel in range(pinion_min, pinion_max):
        # print("{:.1f}% calculating moon complication gears".format(100 * (pinion_on_hour_wheel - pinion_min) / (pinion_max - pinion_min)))
        for w0 in range(wheel_min, wheel_max):
            for p0 in range(pinion_min, pinion_max):
                for w1 in range(wheel_min, wheel_max):
                    ratio = (pinion_on_hour_wheel/ w0) * (p0 / w1)
                    if abs(ratio - self.ratio) < 0.000001:
                        print( self.ratio, pinion_on_hour_wheel, w0, p0, w1, ratio, 1/ratio, self.lunar_month_hours*2/12)

class MoonPhaseComplication3D:
    '''
    A moon phase complication with a spherical moon!

    I think this may work out easier than the 2D as there's less gearing required

    Plan:

    One gear from the hour holder on the motion works, which will drive a bevel gear to a rod going up through the top holder for the dial

    then a grey/black sphere for the moon - possibly with a hemisphere cup around the back half
    '''
    def __init__(self, motion_works):
        self.motion_works = motion_works
        self.lunar_month_hours = 29.53059 * 24.0
        self.ratio = 12 / self.lunar_month_hours

        bevel_min = 9
        bevel_max = 120
        wheel_min = 30
        wheel_max = 160

        '''
        wheel driven by a pinion from the hour holder
        this wheel is on an arbour with a bevel gear
        final bevel gear is on the rod that goes up to the moon
        '''

        # if we start with this number of teeth on the pinion then it might fit without making the module size too big
        #could consider a single pin as a 1-tooth pinion
        pinion_on_hour_wheel = 1#self.motion_works.get_cannon_pinion_teeth() + 3
        # for pinion_on_hour_wheel in range(pinion_min, pinion_max):
        # print("{:.1f}% calculating moon complication gears".format(100 * (pinion_on_hour_wheel - pinion_min) / (pinion_max - pinion_min)))
        options = []
        for w0 in range(wheel_min, wheel_max):
            for bevel0 in range(bevel_min, bevel_max):
                for bevel1 in range(wheel_min, wheel_max):
                    ratio = (pinion_on_hour_wheel / w0) * (bevel0 / bevel1)
                    if abs(ratio - self.ratio) < 0.000001:#0.0000002
                        print(self.ratio, pinion_on_hour_wheel, w0, bevel0, bevel1, ratio, 1 / ratio, self.lunar_month_hours / 12)
                        option = {
                            "ratio": ratio,
                            "1/ratio": 1/ratio,
                            "w0": w0,
                            "bevel0": bevel0,
                            "bevel1": bevel1,
                            "weighting": bevel0 + bevel1# - w0
                        }
                        options.append(option)

        options.sort(key=lambda x: x["weighting"])
        print(options[0], self.lunar_month_hours / 12)

class Dial:
    '''
    should really be created by the plates class

    using filament switching to change colours so the supports can be printed to the back of the dial
    '''
    def __init__(self, outside_d, style=DialStyle.LINES_ARC, seconds_style=None, fixing_screws=None,thick=2, top_fixing=True, bottom_fixing=False, hand_hole_d=18,
                 detail_thick=LAYER_THICK * 2, extras_thick=LAYER_THICK*2):
        '''
        Just style and fixing info, dimensions are set in configure_dimensions
        '''
        self.style = style
        self.seconds_style = seconds_style
        if self.seconds_style is None:
            self.seconds_style = self.style
        self.fixing_screws = fixing_screws
        if self.fixing_screws is None:
            self.fixing_screws = MachineScrew(metric_thread=3, countersunk=True, length=25)
        self.thick = thick
        #is there a pillar at the top?
        self.top_fixing = top_fixing
        #is there a pillar at the bottom?
        self.bottom_fixing = bottom_fixing
        #for a style which isn't just a ring, how big a hole for the hands to fit through?
        self.hand_hole_d = hand_hole_d
        self.detail_thick = detail_thick
        #bit of a bodge, for tony the detail is in yellow so I need it thicker (my yellow is really translucent)
        self.extras_thick = extras_thick

        #something for debugging
        self.configure_dimensions(support_length=30, support_d=15, outside_d=outside_d)

        #overrides for the default fixing screw and pillar positions
        self.fixing_positions = []

    def get_hand_space_z(self):
        #how much space between the front of the dial and the hands should there be?
        if self.style == DialStyle.TONY_THE_CLOCK:
            return 3 + self.eye_radius - self.eye_pivot_z - self.thick

        return 3

    def configure_dimensions(self, support_length, support_d, outside_d=-1, second_hand_mini_dial_d=0, second_hand_relative_pos=None):
        '''
        since the dimensions aren't known until the plates have been calculated, the main constructor is for storing the style and this actually sets the size
        Bit of a bodge, but the obvious alternative is to pass all the dial settings into clocks plates (or a new class for dial config?)
        '''
        self.support_length = support_length

        self.support_d = support_d
        if outside_d > 0:
            self.outside_d = outside_d
            # else leave the default
            self.dial_width = self.outside_d * 0.1
        # if >0, add a mini dial for the second hand
        self.second_hand_mini_dial_d = second_hand_mini_dial_d
        # when the second hand is here relative to the centre of the main hands
        self.second_hand_relative_pos = second_hand_relative_pos
        if self.support_d > self.dial_width:
            self.dial_width = self.support_d

        self.inner_r = self.outside_d/2 - self.dial_width
        if self.style == DialStyle.TONY_THE_CLOCK:
            self.inner_r = self.hand_hole_d/2
            self.dial_width = self.outside_d/2 - self.inner_r

        self.seconds_dial_width = self.dial_width * 0.3  # self.second_hand_mini_dial_d * 0.4

        self.dial_detail_from_edges = self.outside_d * 0.01
        self.seconds_dial_detail_from_edges = self.dial_detail_from_edges * 0.75

        if self.style == DialStyle.TONY_THE_CLOCK:
            self.outer_ring_thick=2
            #the dial will drop into the outer ring, from the back
            self.outer_ring_overlap = self.get_tony_dimension("dial_edge_width")*0.25

            #eye stuff is all tony specific so far, but hoping to make it generic in the future. Eye clocks for everyone!

            self.eye_hole_d = self.get_tony_dimension("eye_diameter")
            #how far from the back of the dial the pivot point for the eye should be
            self.eye_pivot_z = 5
            #how much more sphere to make behind the pivot?
            self.eye_extend_beyond_pivot = 5
            #minus one so it's not rubbing on the dial
            self.eye_radius = math.sqrt((self.eye_hole_d/2 - 1)**2 + self.eye_pivot_z**2)
            #from centre of eye, where should we switch to black to make a pupil with the right diameter?
            self.pupil_z = math.sqrt(self.eye_radius**2 - (self.get_tony_dimension("pupil_diameter")/2)**2)
            print("eye diameter", self.eye_radius*2)
            self.eye_rod_d = 2 + 0.2
            self.eye_screw = MachineScrew(2)
            self.eye_distance_apart = self.get_tony_dimension("eye_spacing")
            self.eye_y = self.outside_d / 2 - self.get_tony_dimension("eyes_from_top")
            self.eye_bendy_wire_d = 1.5

    def is_full_dial(self):
        '''
        false if the dial is just a ring,
        true if it's full - and so we can place the fixings fairly freely
        '''
        return self.style in [DialStyle.TONY_THE_CLOCK]

    def override_fixing_positions(self, fixing_positions):
        '''
        expects list of lists:
        [
            [(fixing_x, fixing_y), (fixing_x, fixing_y)]
        ]
        For some dials we might want more choice over where to put the fixings (eg Tony, which is fully filled in)
        '''
        self.fixing_positions = fixing_positions

    def get_fixing_positions(self):
        '''
        returns list of lists:
        [
            [(fixing_x, fixing_y), (fixing_x, fixing_y)]
        ]
        each sub-list is for an individual fixing pillar, where we might want vertical or horizontal sets of screws or just one screw
        '''

        fixing_positions = self.fixing_positions
        if len(self.fixing_positions) == 0:
            #generate them now, otherwise use ones that have been provided by override_fixing_positions
            if self.top_fixing:
                fixing_positions.append([(-self.support_d / 4, self.outside_d / 2 - self.dial_width / 2), (self.support_d / 4, self.outside_d / 2 - self.dial_width / 2)])

            if self.bottom_fixing:
                fixing_positions.append([(-self.support_d / 4, -(self.outside_d / 2 - self.dial_width / 2)), (self.support_d / 4, -(self.outside_d / 2 - self.dial_width / 2))])

        return fixing_positions


    def get_circles_detail(self,outer_r, dial_width, from_edge, thick_fives=False):
        '''
        In the style of two concentric circles with lines along the radii between them
        '''
        line_width = LINE_WIDTH*2
        inner_circle_r = outer_r - dial_width + from_edge + line_width/2
        outer_circle_r = outer_r - from_edge - line_width/2

        lines = 60
        dA = math.pi * 2 / lines

        detail = cq.Workplane("XY").tag("base")
        detail = detail.add(cq.Workplane("XY").circle(outer_circle_r + line_width / 2).circle(outer_circle_r - line_width / 2).extrude(self.detail_thick))
        detail = detail.add(cq.Workplane("XY").circle(inner_circle_r + line_width / 2).circle(inner_circle_r - line_width / 2).extrude(self.detail_thick))


        for i in range(lines):
            big = i % 5 == 0 and thick_fives
            this_line_width = line_width*2 if big else line_width
            angle = math.pi / 2 - i * dA

            detail = detail.add(cq.Workplane("XY").rect(this_line_width,outer_circle_r - inner_circle_r).extrude(self.detail_thick).translate((0, (outer_circle_r + inner_circle_r) / 2)).rotate((0, 0, 0), (0, 0, 1), radToDeg(angle)))

        return detail

    def get_roman_numerals_detail(self, outer_r, dial_width, from_edge, with_lines=True):

        outer_ring_width = from_edge*2

        centre_r = outer_r - dial_width/2
        numeral_r = centre_r - outer_ring_width/2
        numbers = ["XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
        detail = cq.Workplane("XY")
        numeral_height = dial_width - 2*from_edge - outer_ring_width

        for i,number in enumerate(numbers):
            angle = math.pi/2 + i*math.pi*2/12
            pos = polar(angle, numeral_r)
            detail = detail.add(roman_numerals(number, numeral_height, thick=self.detail_thick, invert=True).rotate((0, 0, 0), (0, 0, 1), radToDeg(angle - math.pi / 2)).translate(pos))

        # detail = detail.add(self.get_lines_detail(outer_r, dial_width=from_edge, from_edge=0))
        detail = detail.add(self.get_circles_detail(outer_r, dial_width=outer_ring_width, from_edge=0, thick_fives=False))

        return detail

    def get_lines_detail(self, outer_r, dial_width, from_edge, thick_fives=True):
        '''
        In the style of standalone lines for each minute, with the five minutes thicker

        get the bits to be printed in a different colour
        '''
        # r = self.outside_d / 2
        # from_edge = self.outside_d * 0.01
        # line_inner_r = self.inner_r + from_edge
        r = outer_r
        line_inner_r = outer_r - dial_width + from_edge
        line_outer_r = r - from_edge

        lines = 60

        dA = math.pi * 2 / lines



        big_line_thick = 3
        small_line_thick = 1
        #the angle the line spreads out over
        big_angle = math.asin((big_line_thick / 2) / r) * 2
        small_angle = math.asin((small_line_thick / 2) / r) * 2

        detail = cq.Workplane("XY").tag("base")

        for i in range(lines):
            big = i % 5 == 0 and thick_fives
            line_angle = big_angle if big else small_angle
            angle = math.pi / 2 - i * dA

            bottom_left = polar(angle - line_angle / 2, line_inner_r)
            bottom_right = polar(angle + line_angle / 2, line_inner_r)
            top_right = polar(angle + line_angle / 2, line_outer_r)
            top_left = polar(angle - line_angle / 2, line_outer_r)
            detail = detail.workplaneFromTagged("base").moveTo(bottom_left[0], bottom_left[1]).radiusArc(bottom_right, line_inner_r).lineTo(top_right[0], top_right[1]).radiusArc(top_left, line_outer_r).close().extrude(self.detail_thick)

        return detail

    def get_quad_marks(self, outer_r, mark_length, mark_width, from_edge):
        '''
        Marks only at 12, 3, 6 and 9 o'clock
        '''
        marks = cq.Workplane("XY")

        for i in range(4):
            angle = i*360/4
            #12 o'clock, then rotate into place
            marks = marks.add(cq.Workplane("XY").rect(mark_width, mark_length).extrude(self.detail_thick).translate((0, outer_r - from_edge - mark_length / 2)).rotate((0, 0, 0), (0, 0, 1), angle))

        return marks

    def get_main_dial_detail(self):
        '''
        detailing for the big dial
        '''
        if self.style == DialStyle.LINES_ARC:
            return self.get_lines_detail(self.outside_d / 2, self.dial_width, self.dial_detail_from_edges)
        elif self.style == DialStyle.CONCENTRIC_CIRCLES:
            return self.get_circles_detail(self.outside_d / 2, self.dial_width, self.dial_detail_from_edges)
        elif self.style == DialStyle.ROMAN:
            return self.get_roman_numerals_detail(self.outside_d/2, self.dial_width, self.dial_detail_from_edges)
        elif self.style == DialStyle.TONY_THE_CLOCK:
            #extend the marks so they go underneath the black ring to allow for some slop attaching the ring
            extra = 2
            return self.get_quad_marks(self.outside_d/2, self.outside_d * tony_the_clock["dial_marker_length"]/tony_the_clock["diameter"] + extra,
                                       self.outside_d * tony_the_clock["dial_marker_width"]/tony_the_clock["diameter"], self.outside_d * tony_the_clock["dial_edge_width"]/tony_the_clock["diameter"] - extra)
        raise ValueError("Unsupported dial type")

    def get_seconds_dial_detail(self):
        dial = None
        if self.seconds_style == DialStyle.LINES_ARC:
            dial = self.get_lines_detail(outer_r=self.second_hand_mini_dial_d / 2, dial_width=self.seconds_dial_width, from_edge=self.seconds_dial_detail_from_edges, thick_fives=False)
        elif self.seconds_style == DialStyle.CONCENTRIC_CIRCLES:
            dial = self.get_circles_detail(self.second_hand_mini_dial_d / 2, self.seconds_dial_width, self.seconds_dial_detail_from_edges, thick_fives=False)

        if dial is not None:
            dial = dial.translate(self.second_hand_relative_pos)

        return dial

    def get_tony_dimension(self, name):
        '''
        Get a dimension for tony the clock, scaled to the current size of the dial
        '''
        return self.outside_d * tony_the_clock[name] / tony_the_clock["diameter"]

    def get_tony_face_detail(self):
        '''
        eyebrows and mouth
        '''
        sagitta = self.get_tony_dimension("eyebrow_sagitta")
        width = self.get_tony_dimension("eyebrow_width")
        thick = self.get_tony_dimension("eyebrow_thick")
        eye_distance =self.get_tony_dimension("eye_spacing")

        r = sagitta/2 + (width**2)/(8*sagitta)

        detail = cq.Workplane("XY")

        for x in [-1,1]:
            #going from r to r+thick so we can put little circles at either end (on the sides rather than underneath)
            eyebrow = cq.Workplane("XY").circle(r).circle(r-thick).extrude(self.extras_thick).intersect(cq.Workplane("XY").moveTo(0, r - (sagitta) / 2).rect(width, sagitta).extrude(self.extras_thick))

            #circles at end of eyebrows
            # eyebrow = eyebrow.union(cq.Workplane("XY").circle(thick/2).extrude(self.line_thick).intersect(cq.Workplane("XY").moveTo(-thick/4,0).rect(thick, thick).extrude(self.line_thick)))

            eyebrow = eyebrow.edges("|Z").fillet(thick*0.499)

            eyebrow = eyebrow.translate((0, -(r - sagitta)))
            eyebrow = eyebrow.translate((x*eye_distance/2, self.outside_d/2 - self.get_tony_dimension("eyes_from_top") + self.get_tony_dimension("eye_diameter")/2 + self.get_tony_dimension("eyebrow_above_eye")))
            detail = detail.add(eyebrow)


        mouth = cq.Workplane("XY").moveTo(0, -self.get_tony_dimension("mouth_below_centre")-thick/2).rect(self.get_tony_dimension("mouth_width"),thick).extrude(self.extras_thick)

        mouth = mouth.edges("|Z").fillet(thick*0.499)

        detail = detail.add(mouth)

        return detail

    def get_dial(self):
        r = self.outside_d / 2

        if self.style == DialStyle.TONY_THE_CLOCK:
            #the dial slots into the outer ring, with some wiggle room, to be glued in place
            r-= self.outer_ring_overlap + 0.5

        dial = cq.Workplane("XY").circle(r).circle(self.inner_r).extrude(self.thick)




        self.inner_r = self.outside_d / 2 - self.dial_width


        if self.support_length > 0:
            support = cq.Workplane("XY").circle(self.support_d/2).extrude(self.support_length)
            # if self.top_fixing:
            #     dial = dial.union(support.translate((0,r - self.dial_width/2, self.thick)))
            # if self.bottom_fixing:
            #     dial = dial.union(support.translate((0, -(r - self.dial_width / 2), self.thick)))

            for fixing_pos_set in self.get_fixing_positions():
                support_pos = (sum([x for x, y in fixing_pos_set]) / len(fixing_pos_set), sum([y for x, y in fixing_pos_set])/len(fixing_pos_set), self.thick)
                dial = dial.union(support.translate(support_pos))
                for fixing_pos in fixing_pos_set:
                    # centre = (sum([x for x,y in fixing_pos_set])/2, sum([y for x,y in fixing_pos_set]))
                    dial = dial.cut(cq.Workplane("XY").circle(self.fixing_screws.metric_thread/2).extrude(self.support_length).translate((fixing_pos[0], fixing_pos[1], self.thick)))

        if self.second_hand_mini_dial_d > 0:
            dial = dial.union(cq.Workplane("XY").circle(self.second_hand_mini_dial_d/2).circle(self.second_hand_mini_dial_d/2-self.seconds_dial_width).extrude(self.thick).translate(self.second_hand_relative_pos))
            seconds_detail = self.get_seconds_dial_detail()
            if seconds_detail is not None:
                dial = dial.cut(seconds_detail)

        #cut main detail after potential seconds dial in case of some overlap
        dial = dial.cut(self.get_main_dial_detail())

        if self.style == DialStyle.TONY_THE_CLOCK:
            # cut holes for eyes
            dial = self.add_eyes(dial)
            dial = dial.cut(self.get_tony_face_detail())

        return dial

    def add_eyes(self, dial):
        '''
        cut out hole and add pivot holders for a pair of eyes
        Trying to be generic enough to be reused for more than just tony
        '''
        eye_pivot_holder_wide = 5
        eye_pivot_holder_thick = 8
        eye_pivot_space = 5
        eye_pivot_rod_d = 2
        #1.8 perfectly for slotting the rod in!
        #1.7 gap, 0.3 extra r and eye_pivot_holder_wide 6 snapped immediately
        #trying same extra r but making it thinner so it might be more flexible (or just weaker? really need to print soemthing at 90deg and attach it)
        rod_gap = 1.8
        #0.5 was very loose
        rod_loose_extra_r = 0.3
        eye_pivot_hole_deep = eye_pivot_rod_d

        for x in [-1, 1]:
            dial = dial.cut(cq.Workplane("XY").circle(self.eye_hole_d / 2).extrude(self.thick).translate((x * self.eye_distance_apart / 2, self.eye_y)))
            #bottom pivot holder - sticky out bit with a cone hole
            pivot_top_of_base = self.eye_y - self.eye_hole_d/2 - eye_pivot_space
            bottom_pivot_holder = cq.Workplane("XY").moveTo(x * self.eye_distance_apart/2,  pivot_top_of_base - eye_pivot_holder_thick/2 ).rect(eye_pivot_holder_wide, eye_pivot_holder_thick).extrude(self.eye_pivot_z + eye_pivot_holder_thick/2)
            bottom_pivot_holder = bottom_pivot_holder.cut(cq.Workplane("XY").add(cq.Solid.makeCone(radius1=0, radius2=eye_pivot_rod_d, height=eye_pivot_hole_deep).rotate((0,0,0), (1,0,0),-90).
                                    translate((x * self.eye_distance_apart/2,pivot_top_of_base - eye_pivot_hole_deep,self.eye_pivot_z))))
            dial = dial.union(bottom_pivot_holder.translate((0,0,self.thick)))
            #top pivot holder is a sticky out bit with a hole through the middle
            top_holder_y_centre = self.eye_y  + self.eye_hole_d/2 + eye_pivot_space + eye_pivot_holder_thick/2
            top_pivot_holder = cq.Workplane("XY").moveTo(x * self.eye_distance_apart/2, top_holder_y_centre ).rect(eye_pivot_holder_wide, eye_pivot_holder_thick).extrude(self.eye_pivot_z + eye_pivot_holder_thick/2)
            top_pivot_holder = top_pivot_holder.cut(cq.Workplane("XY").circle(eye_pivot_rod_d/2+rod_loose_extra_r).extrude(10000).rotate((0,0,0), (1,0,0),-90).translate((x * self.eye_distance_apart/2, pivot_top_of_base, self.eye_pivot_z)))
            #cut a slot so the rod can be pushed in - experimental!
            top_pivot_holder = top_pivot_holder.cut(cq.Workplane("XY").rect(rod_gap,eye_pivot_holder_thick).extrude(eye_pivot_holder_thick).translate((x * self.eye_distance_apart/2, top_holder_y_centre, self.eye_pivot_z )))

            dial = dial.union(top_pivot_holder.translate((0,0,self.thick)))

        return dial

    def get_assembled(self):
        '''
        for fancy dials with extras, get with them all together for the model
        opposite way around to the rest of the dial - facing UPWARDS (in the +ve z direction)
        '''

        dial = self.get_dial().rotate((0,0,0),(0,1,0),180)
        extras = self.get_extras()

        if self.style == DialStyle.TONY_THE_CLOCK:
            dial = dial.add(extras["outer_ring"].rotate((0,0,0),(0,1,0),180).translate((0,0,self.thick)))
            eye = extras["eye_white"].add(extras["eye_black"])
            for x in [-1,1]:
                dial = dial.add(eye.translate((x*self.get_tony_dimension("eye_spacing")/2, self.outside_d/2 - self.get_tony_dimension("eyes_from_top"), -self.thick - self.eye_pivot_z)))

        return dial

    def get_all_detail(self):
        '''
        all detail printed in the same colour
        '''
        detail = self.get_main_dial_detail()
        if self.second_hand_mini_dial_d > 0:
            detail = detail.add(self.get_seconds_dial_detail())

        return detail

    def get_eye(self):
        '''
        returns (white,black)

        Plan:
        I can use the drill and some patience to cut pointed ends onto brass rod, so I will mount the eyes vertically like model railway wheels - with two cone intends on either end
        Since it's hard to get the exact length my non-lathe technique I will have the bottom pocket fixed and the top on on the end of a machine screw
        so it'll need a bit of vertical space but will allow me to make it fully adjustable.

        Unsure best way to put the rod through the eye - superglue? Will I then want to make the bottom adjustable as well to make up for it not being in the right place?

        Or can I get away with just the pinpoint on the bottom and being loose in a hole for the top? Might be worth trying this first

        Do I want the whole eye-holding mechanism detachable from the dial?

        screw in the back of the eye - with print in place nut - to hold the eye on the rod and provide something to fix to out the back?

        This should be relatively generic so it can be re-used for more silly eye clocks

        '''
        eye = cq.Workplane("XY").sphere(radius=self.eye_radius)

        #cut off the back so it's printable
        eye = eye.cut(cq.Workplane("XY").rect(self.eye_radius*2,self.eye_radius*2).extrude(self.eye_radius).translate((0,0,-self.eye_radius-self.eye_extend_beyond_pivot)))


        #cut off the top for the multicolour pupil
        pupil = eye.intersect(cq.Workplane("XY").rect(self.eye_radius * 2, self.eye_radius * 2).extrude(self.eye_radius).translate((0, 0, self.pupil_z)))
        eye = eye.cut(cq.Workplane("XY").rect(self.eye_radius * 2, self.eye_radius * 2).extrude(self.eye_radius).translate((0, 0, self.pupil_z)))

        #hole for the pivot rod
        eye = eye.cut(cq.Workplane("XY").circle(self.eye_rod_d/2).extrude(self.eye_radius*4).translate((0,0,-self.eye_radius*2)).rotate((0,0,0),(1,0,0),90))

        #screw on the back to hold eye tight to rod and provide fixing for wire (maybe)
        #didn't need this, the rod is a good tight friction fit
        # eye = eye.cut(cq.Workplane("XY").circle(self.eye_screw.metric_thread/2).extrude(self.eye_extend_beyond_pivot).translate((0,0, -self.eye_extend_beyond_pivot)))
        # nut_hole_depth = self.eye_screw.getNutHeight(half=True)+1
        # eye = eye.cut(self.eye_screw.getNutCutter(height=nut_hole_depth, withBridging=True).translate((0,0,-self.eye_extend_beyond_pivot + 1)))

        wire_hole_depth = self.eye_pivot_z + self.eye_extend_beyond_pivot
        eye = eye.cut(cq.Workplane("XY").circle(self.eye_bendy_wire_d/2).extrude(wire_hole_depth).translate((0,0,-wire_hole_depth)))

        return eye,pupil


    def get_extras(self):
        '''
        Any extra bits for fancy dials (like eyes) or extra colours of detail
        {"name":shape}
        '''
        extras = {}

        if self.style == DialStyle.TONY_THE_CLOCK:
            outer_ring = cq.Workplane("XY").circle(self.outside_d/2).circle(self.outside_d/2 - self.outside_d * tony_the_clock["dial_edge_width"]/tony_the_clock["diameter"]).extrude(self.outer_ring_thick)
            outer_ring = outer_ring.faces(">Z").workplane().circle(self.outside_d/2).circle(self.outside_d/2 - self.outer_ring_overlap).extrude(self.thick)
            extras["outer_ring"] = outer_ring
            extras["black"] = self.get_tony_face_detail()
            eye, pupil = self.get_eye()
            extras["eye_white"] = eye
            extras["eye_black"] = pupil
        return extras

    def get_halfs(self, shape):
        top_includer = cq.Workplane("XY").rect(self.outside_d, self.outside_d/2).extrude(self.thick + self.support_d).translate((0,self.outside_d/4))
        # actually rotate by two and a half minutes so we don't slice through anything too complicated
        top_includer = top_includer.rotate((0, 0, 0), (0, 0, 1), -2.5 * 360 / 60).union(top_includer.rotate((0, 0, 0), (0, 0, 1), 2.5 * 360 / 60))

        halves = [shape.intersect(top_includer), shape.cut(top_includer)]

        return halves


    def outputSTLs(self, name="clock", path="../out", max_wide=250, max_long=210):

        if self.outside_d < min(max_wide, max_long):
            out = os.path.join(path, "{}_dial.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_dial(), out)

            out = os.path.join(path, "{}_dial_detail.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_all_detail(), out)
        else:
            dials = self.get_halfs(self.get_dial())
            details = self.get_halfs(self.get_all_detail())
            for i in range(len(dials)):
                out = os.path.join(path, "{}_dial_half{}.stl".format(name, i))
                print("Outputting ", out)
                exporters.export(dials[i], out)

                out = os.path.join(path, "{}_dial_detail_half{}.stl".format(name, i))
                print("Outputting ", out)
                exporters.export(details[i], out)
        extras = self.get_extras()
        for extra in self.get_extras():
            out = os.path.join(path, "{}_dial_{}.stl".format(name, extra))
            print("Outputting ", out)
            exporters.export(extras[extra], out)
