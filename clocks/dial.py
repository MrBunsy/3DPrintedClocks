import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math

from .pillars import *
from .types import *
from .utility import *
from .cuckoo_bits import roman_numerals
import numpy as np
import os
from .cosmetics import tony_the_clock
from .gearing import *

class MoonPhaseComplication2D:
    def __init__(self, motion_works):
        '''
        UNFINISHED
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

    I think this may work out easier than the 2D as there's less gearing required (...but still lots of gearing)

    Plan:

    One gear from the hour holder on the motion works, which will drive a bevel gear to a rod going up through the top holder for the dial

    then a grey/black sphere for the moon - possibly with a hemisphere cup around the back half (moon spoon!)
    module of 0.9 on first experiment
    '''
    def __init__(self, pinion_teeth_on_hour_wheel=16, module=0.9, gear_thick=2.4, gear_style=GearStyle.ARCS, moon_radius=30, first_gear_angle_deg=180,
                 on_left=True, bevel_module=-1, moon_inside_dial = False, bevel_angle_from_hands_deg=90, moon_from_hands=40):
        self.lunar_month_hours = 29.53059 * 24.0
        self.ratio = 12 / self.lunar_month_hours
        self.module = module
        self.gear_style = gear_style
        self.on_left = on_left
        #if false, sticks off the top of the clock
        self.moon_inside_dial = moon_inside_dial

        '''
        bevel angle work is only partly finished - the gear layout works but the moon holder doesn't
        I'm not sure I'm going to use it as it doesn't actually make assembling the complication on a small clock any easier
        '''
        #angle the rod off directly upright? can be useful for fitting moon inside a dial
        #this is the angle from the motion works to the bevel gear (but note that if on_left is false, this is flipped sides)
        self.bevel_angle_from_hands_deg = bevel_angle_from_hands_deg
        self.bevel_angle_from_hands = deg_to_rad(bevel_angle_from_hands_deg)
        #if bevel_angle_from_hands_deg is not 90, use to calculate position of the bevel gear. in mm
        self.moon_from_hands = moon_from_hands

        self.moon_radius = moon_radius
        self.first_gear_angle = deg_to_rad(first_gear_angle_deg)

        '''
        TODO - each one will need carefully controlled thickness
        the pinion on the hour hand just needs to be chunky enough to allow for non perfect alignment
        the pinion on the first abour needs to be long enough that the *next* arbour can be as close to the plate as possible
        if the second arbour (with the first bevel gear) is close to the plate then the vertical arbor with the moon can be relatvely close to the plate
        '''
        self.gear_thick = gear_thick
        self.hour_hand_pinion_thick = 8
        self.pinion_thick = gear_thick*2
        #extra long to get back to near the plate
        self.first_pinion_thick = 15

        # bevel_min = 15
        # bevel_max = 30
        # wheel_min = 60
        # wheel_max = 100
        # pinion_min = 9
        # pinion_max = 15
        bevel_min = 20
        bevel_max = 30
        wheel_min = 40
        wheel_max = 70
        pinion_min = 12
        pinion_max = 20

        self.arbor_d = 3
        self.screws = MachineScrew(self.arbor_d, countersunk=True)
        self.arbor_loose_d = self.arbor_d + LOOSE_FIT_ON_ROD_MOTION_WORKS
        self.lone_bevel_min_height = 15

        self.bevel_module = bevel_module
        if self.bevel_module < 0:
            self.bevel_module = self.module

        '''
        wheel driven by a pinion from the hour holder
        this wheel is on an arbour with a bevel gear
        final bevel gear is on the rod that goes up to the moon
        
        ...or an extra arbor too? then the hour holder can have a real pinion rather than a one-tooth thingie, and we can push the bevel gear as close to the front of the frame as possible
        '''

        # if we start with this number of teeth on the pinion then it might fit without making the module size too big
        #could consider a single pin as a 1-tooth pinion
        #18 was the minimum at module 1
        self.pinion_teeth_on_hour_wheel = pinion_teeth_on_hour_wheel#self.motion_works.get_cannon_pinion_teeth() + 3
        # for pinion_on_hour_wheel in range(pinion_min, pinion_max):
        # print("{:.1f}% calculating moon complication gears".format(100 * (pinion_on_hour_wheel - pinion_min) / (pinion_max - pinion_min)))
        options = []
        #I should probably do this like I do in the main time train calculator, this is messy
        total_combos = (wheel_max - wheel_min) * (pinion_max -pinion_min)* (pinion_max -pinion_min) * (wheel_max - wheel_min)  * (wheel_max - wheel_min) * (bevel_max - bevel_min)*(bevel_max - bevel_min)
        combo = 0
        if False:
            for w0 in range(wheel_min, wheel_max):
                for p1 in range(pinion_min, pinion_max):
                    for w1 in range(wheel_min, wheel_max):
                        for p2 in range(pinion_min, pinion_max):
                            for w2 in range(wheel_min, wheel_max):
                                for bevel_pinion in range(bevel_min, bevel_max):
                                    for bevel_wheel in range(bevel_min, bevel_max):
                                        if combo % round(total_combos/100) == 0:
                                            print("{}%".format(round(100*combo/total_combos)))
                                        combo +=1
                                        ratio = (pinion_teeth_on_hour_wheel / w0) * (p1 / w1) * (p2 / w2) * (bevel_pinion / bevel_wheel)
                                        error = abs(1/ratio - 1/self.ratio)
                                        if error < 0.01 and w1 > w0 and w2 > w1:#0.0000002
                                            # print(self.ratio, pinion_on_hour_wheel, w0, bevel0, bevel1, ratio, 1 / ratio, self.lunar_month_hours / 12)
                                            option = {
                                                "ratio": ratio,
                                                "1/ratio": 1/ratio,
                                                "w0": w0,
                                                "p1": p1,
                                                "w1": w1,
                                                "p2": p2,
                                                "w2": w2,
                                                "bevel_pinion": bevel_pinion,
                                                "bevel_wheel": bevel_wheel,
                                                "weighting": w1 - w0,
                                                "error": abs(1/ratio - 1/self.ratio)
                                            }
                                            options.append(option)
            print(options)
            # options.sort(key=lambda x: -x["weighting"])
            options.sort(key=lambda x: x["error"])

        else:
            # options = [{'ratio': 0.01693159320277965, '1/ratio': 59.06118745138707, 'w0': 59, 'p1': 15, 'w1': 65, 'p2': 19, 'w2': 66, 'bevel_pinion': 29, 'bevel_wheel': 27, 'weighting': 6, 'error': 7.451387070034343e-06}]
            options = [{'ratio': 0.016931599773883546, '1/ratio': 59.06116452991454, 'w0': 55, 'p1': 18, 'w1': 58, 'p2': 13, 'w2': 61, 'bevel_pinion': 22, 'bevel_wheel': 25, 'weighting': 3, 'error': 1.5470085457991445e-05}]
        #pinions driving wheels here
        self.train = [(self.pinion_teeth_on_hour_wheel, options[0]["w0"]), (options[0]["p1"], options[0]["w1"]), (options[0]["p2"], options[0]["w2"]), (options[0]["bevel_wheel"], options[0]["bevel_pinion"])]
        self.bevel_pair = WheelPinionBeveledPair(options[0]["bevel_wheel"], options[0]["bevel_pinion"], module=self.bevel_module)

        #want second wheel to be larger so there's space for the bevel, can do this by meddling with tooth count but I'd rather keep the ratio accuracy and meddle size with module size
        size_ratio_target = 1.05
        tooth_ratio = options[0]["w1"]/options[0]["w0"]
        module_ratio = size_ratio_target/tooth_ratio
        second_module = self.module * module_ratio
        print("second module",second_module)

        #TODO faff about with module sizes to make sure this all fits and the bevel is big enough to be reliable
        self.pairs = [WheelPinionPair(self.train[0][1], self.train[0][0], self.module), WheelPinionPair(self.train[1][1], self.train[1][0], self.module),
                      WheelPinionPair(self.train[2][1], self.train[2][0], self.module), self.bevel_pair]

        # print(options)
        print(options[0], self.lunar_month_hours / 12)

        #placeholders
        self.cannon_pinion_max_r = 10
        self.plate_to_top_of_hour_holder_wheel = 15

    def set_motion_works_sizes(self, motion_works):

        self.cannon_pinion_max_r = motion_works.get_cannon_pinion_max_r()
        self.plate_to_top_of_hour_holder_wheel = motion_works.get_cannon_pinion_base_thick() + motion_works.thick + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - motion_works.inset_at_base
        self.first_pinion_thick = self.plate_to_top_of_hour_holder_wheel + self.hour_hand_pinion_thick/2 - self.gear_thick/2 - WASHER_THICK_M3

    def get_pinion_for_motion_works_shape(self):
        '''
        get the Gear that should be part of the hour holder
        '''
        return self.pairs[0].pinion.get3D(thick=self.hour_hand_pinion_thick)

    def get_pinion_for_motion_works_max_radius(self):
        return self.pairs[0].pinion.get_max_radius()

    def get_arbor_shape(self, index, for_printing=True):
        '''
        not adapting the Arbour class to do all this as there's just not the need - there's only going to be one sensible solution for the moon complication once it's finished

        (arbor -1 is the hour holder)
        arbor 0 is off to one side - standard arbor except driven backwards (pinion drives the wheel)
        arbor 2 has the first bevel gear
        arbor 3 is just the last bevel gear
        '''
        if index < 2:
            pinion_length = self.first_pinion_thick if index == 0 else self.pinion_thick
            #TODO pinion should be long enough to reach all the way to the plate so the next arbor can be as close as possible and thus the moon not stick out too much
            arbor_object = Arbor(arbor_d= self.arbor_loose_d, wheel=self.pairs[index].wheel, wheel_thick=self.gear_thick, pinion=self.pairs[index + 1].pinion, pinion_thick=self.pinion_thick,
                          pinion_extension=pinion_length - self.pinion_thick, pinion_at_front=False, clockwise_from_pinion_side=True, style=self.gear_style, end_cap_thick=0)
            arbor = arbor_object.get_shape()
            if index == 0:
                #cut away a bit to improve fitting ext to motion works (woopsee printing clock 32)
                pinion_r = arbor_object.get_pinion_max_radius()
                cut_to_r = pinion_r*0.7
                cutter_high = pinion_length - self.pinion_thick*1.25
                cutter = cq.Workplane("XY").circle(pinion_r*1.5).circle(cut_to_r).extrude(cutter_high).translate((0,0,self.gear_thick))
                #trim off the top so this is printable at 45deg
                cutter = cutter.cut(cq.Solid.makeCone(radius1=pinion_r, radius2=0,height=pinion_r*1.5,pnt=(0,0,cutter_high + self.gear_thick), dir=(0,0,-1)))
                arbor = arbor.cut(cutter)

            if not for_printing and index == 0:
                arbor = arbor.rotate((0,0,0),(1,0,0),180).translate((0,0,self.gear_thick + pinion_length))
            return arbor

        elif index == 2:
            #arbour with bevel#
            arbor = self.pairs[index].wheel.get3D(holeD=self.arbor_loose_d, thick=self.gear_thick, style = self.gear_style, innerRadiusForStyle=self.bevel_pair.get_pinion_max_radius())
            arbor = arbor.union(self.bevel_pair.pinion.cut(cq.Workplane("XY").circle(self.arbor_loose_d / 2).extrude(1000)).translate((0, 0, self.gear_thick)))

            return arbor
        elif index == 3:
            #lone bevel that sits at the bottom of the rod with the moon on the other end
            bevel = self.bevel_pair.wheel.union(cq.Workplane("XY").circle(self.arbor_d*1.6).extrude(self.lone_bevel_min_height))
            #hole to thread onto rod
            bevel = bevel.cut(cq.Workplane("XY").circle(self.arbor_d / 2).extrude(1000))
            #nyloc nut space
            bevel = bevel.cut(self.screws.get_nut_cutter(nyloc=True).translate((0, 0, self.lone_bevel_min_height - self.screws.get_nut_height(nyloc=True))))
            return bevel

        else:
            raise ValueError("Arbor {} not valid".format(index))

    def get_arbor_distances(self, pair_index):
        if pair_index < 3:
            return self.pairs[pair_index].centre_distance
        else:
            raise ValueError("Invalid pair ({}) to calculate distances".format(pair_index))


    def get_arbor_positions_relative_to_motion_works(self):
        '''
        returns [(x,y,z),] starting with the first arbor (not position of motion works)
        '''

        positions = []

        #directly above and as close to the motion works as possible
        motion_works_to_belvel0 = self.cannon_pinion_max_r + self.pairs[2].wheel.get_max_radius() + 3
        bevel0_pos = polar(self.bevel_angle_from_hands, motion_works_to_belvel0)#(0, motion_works_to_belvel0)
        # directly to the left of teh motion works
        arbor0_pos = polar(self.first_gear_angle, self.get_arbor_distances(0))#(-self.get_arbor_distances(0),0)

        #plan, first arbor at 90deg from the motion works, then fit the final arbor in
        #potentially fiddle the angle of the first arbor

        on_side = 1
        arbor0_to_arbor1 = self.get_arbor_distances(1)
        arbor1_to_bevel0 = self.get_arbor_distances(2)
        arbor0_to_bevel0_vector = np_to_set(np.subtract(bevel0_pos, arbor0_pos))

        arbor0_to_bevel0 = np.linalg.norm(arbor0_to_bevel0_vector)
        arbor0_to_bevel0_angle = math.atan2(arbor0_to_bevel0_vector[1], arbor0_to_bevel0_vector[0])

        b = arbor0_to_arbor1
        c = arbor1_to_bevel0
        a = arbor0_to_bevel0
        # cosine law
        angle = math.acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b))




        arbor1_pos = np_to_set(np.add(arbor0_pos, polar(angle + arbor0_to_bevel0_angle, arbor0_to_arbor1)))
        arbor1_to_bevel0_check = np.linalg.norm(np.subtract(bevel0_pos, arbor1_pos))

        print("arbor1_to_bevel0: {}, arbor1_to_bevel0_check:{}".format(arbor1_to_bevel0, arbor1_to_bevel0_check))

        #flip it all if needed (don't want to re-do the angle stuff)
        x = 1 if self.on_left else -1

        return [
            (x*arbor0_pos[0], arbor0_pos[1], WASHER_THICK_M3),
            (x*arbor1_pos[0], arbor1_pos[1], WASHER_THICK_M3),
            (x*bevel0_pos[0], bevel0_pos[1], WASHER_THICK_M3 + self.pinion_thick/2 +self.gear_thick/2)]

    def get_moon_half(self):
        moon = cq.Workplane("XY").add(cq.Solid.makeSphere(self.moon_radius))

        #hole for rod - we're clamping the moon in place like the motion works, so it can be rotated with friction from the split washer
        moon = moon.cut(cq.Workplane("XY").circle((self.arbor_d + LOOSE_FIT_ON_ROD)/2).extrude(self.moon_radius*2).rotate((0,0,0),(1,0,0),-90).translate((0,-self.moon_radius,0)))

        #TODO way to attach the two halves together? Inset little areas to hold glue like on the model trains?
        #panhead screws stick and out it slots on and rotates?

        hole_size = self.moon_radius*0.5
        if hole_size > 15:
            hole_size = 15
        #slight inset areas to provide grip and space for glue, crude but should work
        moon = moon.cut(cq.Workplane("XY").pushPoints([(self.moon_radius/2,0),(-self.moon_radius/2,0)]).rect(hole_size,hole_size).extrude(LAYER_THICK*2))

        return moon

    def get_relative_moon_z(self):
        #front of the last arbor, then the bevel
        return self.get_arbor_positions_relative_to_motion_works()[2][2] + self.gear_thick + self.bevel_pair.get_centre_of_wheel_to_back_of_pinion()

    def get_last_wheel_r(self):
        return self.pairs[-2].wheel.get_max_radius()

    def get_bevel_angle(self):
        '''
        angle from the centre of the last arbor to the moon
        '''
        if self.bevel_angle_from_hands_deg == 90:
            return math.pi/2

        positions = self.get_arbor_positions_relative_to_motion_works()
        last_arbor_pos = positions[2][:2]
        moon_centre_pos = (0, self.moon_from_hands)

        angle = math.atan2(moon_centre_pos[1] - last_arbor_pos[1], moon_centre_pos[0] - last_arbor_pos[0])

        return angle

    def get_assembled(self):
        model = cq.Workplane("XY")
        # positions = self.get_arbor_positions_relative_to_motion_works()
        # for i in range(3):
        #     model = model.add(self.get_arbor_shape(i, for_printing=False).translate((positions[i][0], positions[i][1], positions[i][2])))
        #
        # #would like the bevel at the top, keeping it further out the way of the motion works and closer to where it can be through a pipe/bearing (to reduce wobble)
        # #but with the extra gear it'd be spinning the wrong way!
        #
        # bevel_angle = math.pi + self.get_bevel_angle()# -math.pi/2 + (math.pi / 2 - self.bevel_angle_from_hands)
        #
        # bevel_relative_pos = polar(bevel_angle,self.bevel_pair.get_centre_of_pinion_to_back_of_wheel())
        # # if not self.on_left:
        # #     bevel_relative_pos = (-bevel_relative_pos[0], bevel_relative_pos[1])
        # bevel_pos = np_to_set(np.add(positions[2][:2], bevel_relative_pos))
        # model = model.add(self.get_arbor_shape(3).rotate((0,0,0),(1,0,0),-90).rotate((0,0,0), (0,0,1), rad_to_deg(bevel_angle + math.pi / 2)).translate(
        #     (bevel_pos[0], bevel_pos[1], self.get_relative_moon_z())
        # ))
        # # model = model.add(cq.Workplane("XY").circle(1).extrude(40).translate(
        # #     (bevel_pos[0], bevel_pos[1], self.get_relative_moon_z())
        # # ))
        parts = self.get_parts_in_situ()
        for part in parts:
            model = model.add(parts[part])

        return model

    def get_parts_in_situ(self):
        '''
        for rendering a preview with colours
        '''
        parts = {}
        positions = self.get_arbor_positions_relative_to_motion_works()
        for i in range(3):
            parts[f"arbor_{i}"]=self.get_arbor_shape(i, for_printing=False).translate((positions[i][0], positions[i][1], positions[i][2]))

        # would like the bevel at the top, keeping it further out the way of the motion works and closer to where it can be through a pipe/bearing (to reduce wobble)
        # but with the extra gear it'd be spinning the wrong way!
        # however at the bottom it works really well for the smaller moon phase inside the dial

        bevel_angle = math.pi + self.get_bevel_angle()  # -math.pi/2 + (math.pi / 2 - self.bevel_angle_from_hands)

        bevel_relative_pos = polar(bevel_angle, self.bevel_pair.get_centre_of_pinion_to_back_of_wheel())
        # if not self.on_left:
        #     bevel_relative_pos = (-bevel_relative_pos[0], bevel_relative_pos[1])
        bevel_pos = np_to_set(np.add(positions[2][:2], bevel_relative_pos))
        parts["arbor_3"] = self.get_arbor_shape(3).rotate((0, 0, 0), (1, 0, 0), -90).rotate((0, 0, 0), (0, 0, 1), rad_to_deg(bevel_angle + math.pi / 2)).translate(
            (bevel_pos[0], bevel_pos[1], self.get_relative_moon_z())
        )
        return parts

    def output_STLs(self, name="clock", path="../out", max_wide=250, max_long=210):

        for i in range(4):
            out = os.path.join(path, "{}_moon_arbor_{}.stl".format(name,i))
            print("Outputting ", out)
            exporters.export(self.get_arbor_shape(i), out)

        out = os.path.join(path, "{}_moon_half.stl".format(name))
        print("Outputting ", out)
        #worth bumping up the quality for this!
        exporters.export(self.get_moon_half(), out, tolerance=0.01, angularTolerance=0.01)

class RomanNumerals:
    '''
    The old roman_numerals function in cuckoo_bits works, but I'd like something more flexible and that can follow the curve of a dial
    '''
    def __init__(self, height, thick=LAYER_THICK*2, centre_radius=150 ,style=RomanNumeralStyle.SIMPLE_SQUARE):
        self.height = height
        self.thick = thick
        self.style = style
        # radius of the centre of the font, so the numerals will fit neatly on a dial
        # could consider making this optional, but it will make the logic a lot messier, so I'm giong to run with it always being there
        self.centre_radius = centre_radius

        #things based on the style
        self.width_I = self.height*0.2
        self.width_X = self.width_I*2
        self.width_V = self.width_I*2
        self.width_line_thick = self.width_I*0.6
        self.width_line_thin = self.width_I*0.2

        #avoiding the V being too pointy to print well, can be set to zero
        self.width_v_base = 0.2

        self.height_extra = height*1.5

        self.stroke_style = StrokeStyle.ROUND

        if self.style == RomanNumeralStyle.SIMPLE_SQUARE:
            self.stroke_style = StrokeStyle.SQUARE

    def get_inclusion_ring(self):
        '''
        all the font should be inside this ring
        make slightly smaller if we've got a line at the top and bottom because cadquery seems to get its pants in a twist otherwise
        '''

        line_width = self.width_line_thin/2

        return cq.Workplane("XY").circle(self.centre_radius + self.height/2 - line_width).circle(self.centre_radius - self.height/2 + line_width).extrude(self.thick)

    def get_lines(self, width = None, angle=None):
        if angle is None:
            angle = get_angle_of_chord(self.centre_radius, width)

        bottom_r = self.centre_radius - self.height/2 + self.width_line_thin / 2
        top_r = self.centre_radius + self.height/2 - self.width_line_thin/2

        bottom_left = polar(math.pi / 2 + angle / 2, bottom_r)
        bottom_right = polar(math.pi / 2 - angle / 2, bottom_r)
        top_left = polar(math.pi / 2 + angle / 2, top_r)
        top_right = polar(math.pi / 2 - angle / 2, top_r)

        lines = get_stroke_arc(bottom_right, bottom_left, bottom_r, wide=self.width_line_thin, thick=self.thick, style=self.stroke_style)
        lines = lines.union(get_stroke_arc(top_right, top_left, top_r, wide=self.width_line_thin, thick=self.thick, style=self.stroke_style))

        return lines

    '''
    internal individual characters are all drawn centred at (0, self.radius)
    '''
    def get_I(self):
        i = cq.Workplane("XY").moveTo(0, self.centre_radius).rect(self.width_line_thick, self.height_extra).extrude(self.thick)
        i = i.intersect(self.get_inclusion_ring())

        # i = i.union(self.get_lines(self.width_I))

        return i

    def get_V(self):

        triangle_width = self.width_V*0.9

        #the outside containing triangle
        top_left = (-triangle_width/2, self.centre_radius + self.height/2)
        top_right = (triangle_width/2, self.centre_radius + self.height/2)
        #fudging slightly because this is purely to help it print as an exact point won't be printed
        bottom_left = (-self.width_v_base/2, self.centre_radius - self.height/2)
        bottom_right = (self.width_v_base / 2, self.centre_radius - self.height / 2)

        left_line = Line(bottom_left, anotherPoint=top_left)
        right_line = Line(bottom_right, anotherPoint=top_right)

        top_left_extended = np_to_set(np.add(bottom_left, np.multiply(left_line.dir, self.height_extra)))
        top_right_extended = np_to_set(np.add(bottom_right, np.multiply(right_line.dir, self.height_extra)))

        inclusion_triangle = (cq.Workplane("XY").moveTo(top_left_extended[0], top_left_extended[1]).lineTo(top_right_extended[0], top_right_extended[1])
                              .lineTo(bottom_right[0], bottom_right[1]))
        if self.width_v_base > 0:
            inclusion_triangle = inclusion_triangle.lineTo(bottom_left[0], bottom_left[1])

        inclusion_triangle = inclusion_triangle.close().extrude(self.thick)

        v = get_stroke_line([bottom_left, top_left_extended], wide=self.width_line_thick*2, thick=self.thick)
        v = v.union(get_stroke_line([bottom_right, top_right_extended], wide=self.width_line_thin*2, thick=self.thick))
        v = v.intersect(inclusion_triangle).intersect(self.get_inclusion_ring())

        # v = v.union(self.get_lines(self.width_V))

        return v

    def get_X(self):
        '''

        '''

        centre = (0, self.centre_radius)

        lines_apart = self.width_X*0.5

        top_left = (-lines_apart / 2, self.centre_radius + self.height / 2)
        top_right = (lines_apart / 2, self.centre_radius + self.height / 2)
        bottom_left = (-lines_apart / 2, self.centre_radius - self.height / 2)
        bottom_right = (lines_apart / 2, self.centre_radius - self.height / 2)

        thick_line = Line(centre, anotherPoint=top_left)
        thin_line = Line(centre, anotherPoint=top_right)

        angle_thick_line = thick_line.get_angle()
        angle_thin_line = thin_line.get_angle()

        x = cq.Workplane("XY").moveTo(centre[0], centre[1]).rect(self.height_extra, self.width_line_thick).extrude(self.thick).rotate(centre, (centre[0], centre[1], 1), rad_to_deg(angle_thick_line))
        x = x.union(cq.Workplane("XY").moveTo(centre[0], centre[1]).rect(self.height_extra, self.width_line_thin).extrude(self.thick).rotate(centre, (centre[0], centre[1], 1), rad_to_deg(angle_thin_line)))

        x = x.intersect(self.get_inclusion_ring())

        # x = x.union(self.get_lines(self.width_X))

        return x

    def get_character(self, char):
        if char == "I":
            return self.get_I()
        elif char == "V":
            return self.get_V()
        elif char == "X":
            return self.get_X()

    def get_number(self, number_string, invert=False):
        '''
        Assumes number is a string made up of only I,X,V
        '''

        if self.style == RomanNumeralStyle.CUCKOO:
            return roman_numerals(number_string, self.height, thick=self.thick, invert=invert)

        widths = []
        for char in number_string:
            if char == "I":
                widths.append(self.width_I)
            elif char == "V":
                widths.append(self.width_V)
            elif char == "X":
                widths.append(self.width_X)

        angles = [get_angle_of_chord(self.centre_radius, width) for width in widths]
        total_angle = sum(angles)

        number_shape = cq.Workplane("XY")

        current_angle = total_angle/2 - angles[0]/2
        for i, char in enumerate(number_string):
            number_shape = number_shape.union(self.get_character(char).rotate((0,0,0), (0,0,1), rad_to_deg(current_angle)))
            current_angle -= angles[i]/2
            if i < len(number_string)-1:
                current_angle -= angles[i+1]/2

        number_shape = number_shape.union(self.get_lines(angle=total_angle))

        number_shape = number_shape.translate((0,-self.centre_radius))
        if invert:
            number_shape = number_shape.rotate((0,0,0), (0,1,0),180).translate((0,0,self.thick))

        return number_shape

class DialPillar:
    def __init__(self, position, screws_absolute_positions, radius, length, embedded_nuts=False, screws=None):
        #pillar position relative to the centre of the dial
        self.position = position
        #list of sets [(x,y),]
        self.screws_absolute_positions = screws_absolute_positions
        self.radius = radius
        self.length = length
        self.embedded_nuts = embedded_nuts
        self.screws = screws
        if self.screws is None:
            self.screws = MachineScrew(3, countersunk=True)

    def get_screws_relative_positions(self):
        return [np_to_set(np.subtract(screwpos, self.position)) for screwpos in self.screws_absolute_positions]

    def get_pillar(self):
        relative_screws = self.get_screws_relative_positions()
        pillar = cq.Workplane("XY").circle(self.radius).extrude(self.length).faces(">Z").workplane().pushPoints().circle(self.screws.metric_thread/2).cutThruAll()

        if self.embedded_nuts:
            for screwpos in relative_screws:
                pillar = pillar.cut(self.screws.get_nut_cutter(height=self.screws.get_nut_height() + 1, with_bridging=True).translate(screwpos))

        return pillar

class Dial:
    '''
    should really be created by the plates class

    using filament switching to change colours so the supports can be printed to the back of the dial
    '''
    def __init__(self, outside_d, style=DialStyle.LINES_ARC, outer_edge_style=None, inner_edge_style=None, seconds_style=None, fixing_screws=None, thick=2, top_fixing=True,
                 bottom_fixing=False, hand_hole_d=18, detail_thick=LAYER_THICK * 2, extras_thick=LAYER_THICK*2, font=None, font_scale=1, font_path=None, hours_only=False,
                 minutes_only=False, seconds_only=False, dial_width=-1, romain_numerals_style=None, pillar_style = PillarStyle.SIMPLE, hand_space_z=2):
        '''
        Just style and fixing info, dimensions are set in configure_dimensions

        if just a style is provided, that's all that's used.
        Alternatively a style an inner and/or outer edge style can be provided. Intention: numbers with a ring around the outside.

        '''
        #used to be 3 before made configurable
        self.hand_space_z = hand_space_z
        self.style = style
        #pillars/supports terms used interchangably
        self.pillar_style = pillar_style
        self.outer_edge_style = outer_edge_style
        self.inner_edge_style = inner_edge_style
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

        #for clocks without all hands on the same dial, or without sub-seconds dial?
        #the default assumption is this dial has a minute and hour hand and a sub-seconds hand.
        #these settings override that
        self.hours_only = hours_only
        self.seconds_only = seconds_only
        self.minutes_only = minutes_only

        #if -1 this will be overriden in configure_dimensions to the default of 0.1*diameter
        self.dial_width = dial_width
        #backwards compatibiltiy with things that relied on teh minimum dial width being 15mm:
        hacky_default_support_d = 5
        if self.dial_width < 0:
            hacky_default_support_d = 15
        #usually called by Plates class, but do it here so something exists without plates
        self.configure_dimensions(support_length=30, support_d=hacky_default_support_d, outside_d=outside_d)

        #overrides for the default fixing screw and pillar positions DEPRECATED, switching to configuring whole pillars instead
        self.fixing_positions = []
        self.pillars = []
        self.romain_numerals_style = romain_numerals_style

        #TODO switch over to new Font class (although we use font_scale for roman numerals, so take that into consideration)
        #if this is a roman numeral we will first look for romain_numerals_style. If it is None, fall back on font
        #for any styles which use a font
        self.font = font
        #manual adjustment for size of font if my automatic attempt doesn't work
        self.font_scale = font_scale
        #manual location of font file for when cadquery can't seem to find it on the system
        self.font_path = font_path

        # a shape to be subtracted from the supports to avoid crashing into things, bit hacky, will be set by plates
        self.subtract_from_supports = None
        # also a bit hacky, plates might want to add somethign to this dial (like front anchor holder)
        self.add_to_back = None

    def get_hand_space_z(self):
        #how much space between the front of the dial and the hands should there be?
        if self.style == DialStyle.TONY_THE_CLOCK:
            return self.hand_space_z + self.eye_radius - self.eye_pivot_z - self.thick

        return self.hand_space_z

    def get_hand_length(self, hand=HandType.MINUTE):
        '''
        what length hands should go on this dial?
        '''
        if hand == HandType.SECOND:
            return self.second_hand_mini_dial_d*0.5 - self.seconds_dial_width/2

        if self.style == DialStyle.TONY_THE_CLOCK:
            return self.get_tony_dimension("minute_hand_length")
        elif self.style == DialStyle.FANCY_WATCH_NUMBERS:
            return self.outside_d/2 - self.get_edge_style_width(self.outer_edge_style, outer=True) - self.dial_detail_from_edges
        else:
            return self.outside_d/2 - self.dial_width/2

    def configure_dimensions(self, support_length, support_d, outside_d=-1, second_hand_relative_pos=None):
        '''
        since the dimensions aren't known until the plates have been calculated, the main constructor is for storing the style and this actually sets the size
        Bit of a bodge, but the obvious alternative is to pass all the dial settings into clocks plates (or a new class for dial config?)
        '''
        self.support_length = support_length# + 1 #why was the +1 here? was this left over from a retrofit?

        self.support_d = support_d
        if outside_d > 0:
            self.outside_d = outside_d
            if self.dial_width < 0:
                # else leave the default
                self.dial_width = self.outside_d * 0.1

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
        self.second_hand_mini_dial_d = 0

        if self.second_hand_relative_pos is not None:
            # add a mini dial for the second hand (NOTE assumes second hand is vertical)
            self.second_hand_mini_dial_d = ((self.outside_d/2 - self.dial_width + self.dial_detail_from_edges) - abs(self.second_hand_relative_pos[1]))*2

            if self.seconds_dial_width > self.second_hand_mini_dial_d/2:
                print("seconds dial too small for default seconds dial width")
                self.seconds_dial_width = self.second_hand_mini_dial_d*0.2

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
            #2.2 works for the m2 eye bolts
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

    def has_eyes(self):
        '''
        has eyes that rotate with the pendulum
        '''
        return self.style in [DialStyle.TONY_THE_CLOCK]

    def has_seconds_sub_dial(self):
        return self.second_hand_mini_dial_d > 0

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

    def get_dots_detail(self, outer_r, dial_width, thick_fives=True, only_fives=False):
        dots = 60
        if only_fives:
            dots = 12
        dA = math.pi * 2 / dots

        centre_radius = outer_r - dial_width/2

        max_dot_r = centre_radius * math.sin(dA/2)

        if max_dot_r > dial_width/2:
            max_dot_r = dial_width/2 - 0.7

        big_dot_r = max_dot_r
        small_dot_r = max_dot_r/2
        if big_dot_r < 4:
            small_dot_r = max_dot_r*0.66

        if only_fives:
            big_dot_r -= self.dial_detail_from_edges*2

        detail = cq.Workplane("XY")

        for d in range(dots):
            # if d % 5 != 0 and only_fives:
            #     continue

            big = (d % 5 == 0 and thick_fives) or only_fives
            r = big_dot_r if big else small_dot_r

            pos = polar(dA*d, centre_radius)

            detail = detail.add(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(r).extrude(self.detail_thick))

        return detail

    def get_concentric_circles_detail(self, outer_r, dial_width, from_edge, thick_fives=False):
        '''
        In the style of two concentric circles with lines along the radii between them
        '''
        line_width = LINE_WIDTH*2
        inner_circle_r = outer_r - dial_width + from_edge + line_width/2
        outer_circle_r = outer_r - from_edge - line_width/2

        lines = 60
        dA = math.pi * 2 / lines

        detail = cq.Workplane("XY").tag("base")
        detail = detail.union(cq.Workplane("XY").circle(outer_circle_r + line_width / 2).circle(outer_circle_r - line_width / 2).extrude(self.detail_thick))
        detail = detail.union(cq.Workplane("XY").circle(inner_circle_r + line_width / 2).circle(inner_circle_r - line_width / 2).extrude(self.detail_thick))


        for i in range(lines):
            big = i % 5 == 0 and thick_fives
            this_line_width = line_width*2 if big else line_width
            angle = math.pi / 2 - i * dA

            detail = detail.union(cq.Workplane("XY").rect(this_line_width,outer_circle_r - inner_circle_r).extrude(self.detail_thick).translate((0, (outer_circle_r + inner_circle_r) / 2)).rotate((0, 0, 0), (0, 0, 1), rad_to_deg(angle)))

        return detail

    def get_roman_numerals_detail(self, outer_r, dial_width, from_edge, with_lines=True):

        outer_ring_width = from_edge*2
        if not with_lines:
            outer_ring_width = 0

        centre_r = outer_r - dial_width/2
        numeral_r = centre_r - outer_ring_width/2
        numbers = ["XII", "I", "II", "III", "IIII", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
        detail = cq.Workplane("XY")
        numeral_height = (dial_width - 2*from_edge - outer_ring_width)*self.font_scale

        roman_numerals_font = None
        if self.romain_numerals_style is not None:
            roman_numerals_font = RomanNumerals(height=numeral_height, thick = self.detail_thick, centre_radius=numeral_r, style=self.romain_numerals_style)

        if self.font is not None:
            #if font, use that, otherwise use the old hand-written cuckoo numerals
            number_spaces = [TextSpace(x=0, y=0, width=numeral_height*2.5, height=numeral_height, horizontal=True, text=number, thick=self.detail_thick, font=self.font, font_path=self.font_path) for number in numbers]

            max_text_size = min([text_space.get_text_max_size() for text_space in number_spaces])

            for space in number_spaces:
                space.set_size(max_text_size)


        for i,number in enumerate(numbers):
            angle = math.pi/2 + i*math.pi*2/12
            pos = polar(angle, numeral_r)

            if roman_numerals_font is not None:
                # numeral_shape = roman_numerals(number, numeral_height, thick=self.detail_thick, invert=True)
                numeral_shape = roman_numerals_font.get_number(number, invert=True)
            else:
                numeral_shape = number_spaces[i].get_text_shape()

            detail = detail.add(numeral_shape.rotate((0, 0, 0), (0, 0, 1), rad_to_deg(angle - math.pi / 2)).translate(pos))
        if with_lines:
            # detail = detail.add(self.get_lines_detail(outer_r, dial_width=from_edge, from_edge=0))
            detail = detail.add(self.get_concentric_circles_detail(outer_r, dial_width=outer_ring_width, from_edge=0, thick_fives=False))

        return detail

    def get_lines_detail(self, outer_r, dial_width, from_edge, thick_indicators=False, long_indicators=False, total_lines=60, inner_ring=False, outer_ring=False, only=None,
                         big_thick=2, small_thick=1, long_line_length_fraction=-1.0, short_line_length_fraction=-1.0):
        '''
        Intended to be used on the congrieve rolling ball clock, where there are separate dials for the hours and seconds
        so if total lines is 48 the long indicator is for the half hours
        '''
        r = outer_r
        line_inner_r = outer_r - dial_width + from_edge
        line_outer_r = r - from_edge

        total_lines

        dA = math.pi * 2 / total_lines

        if only is None:
            only = [i for i in range(total_lines)]

        big_line_thick = big_thick
        small_line_thick = small_thick

        # short_line_length = line_outer_r - line_inner_r
        # #not sure waht I was originally going for with lines that are longer than the dial?
        # long_line_length = short_line_length * 2
        max_line_length = line_outer_r - line_inner_r
        if long_line_length_fraction < 0:
            long_line_length_fraction = 1
        long_line_length = max_line_length*long_line_length_fraction

        if short_line_length_fraction < 0:
            short_line_length_fraction=0.5
        short_line_length = max_line_length*short_line_length_fraction

        detail = cq.Workplane("XY").tag("base")

        #every fifth line usually, but if we're an hours dial (48 marks for each quarter hour) highlight the half hours
        indicators_on = 4 if total_lines == 48 else 5
        indicators_offset = 2 if total_lines == 48 else 0

        for i in range(total_lines):

            if i not in only:
                continue

            line_thick = small_line_thick
            if i % indicators_on == indicators_offset and thick_indicators:
                line_thick = big_line_thick

            centre_r = (line_inner_r + line_outer_r) / 2
            line_length = short_line_length
            if i % indicators_on == indicators_offset and long_indicators:
                line_length = long_line_length
            if inner_ring:
                centre_r = line_inner_r + line_length/2
            elif outer_ring:
                centre_r = line_outer_r - line_length/2
                #else leave in centre

            angle = math.pi / 2 - i * dA

            line = cq.Workplane("XY").moveTo(centre_r, 0).rect(line_length,line_thick).extrude(self.detail_thick)

            detail = detail.add(line.rotate((0,0,0), (0,0,1), rad_to_deg(angle)))

        return detail

    def get_arcs_detail(self, outer_r, dial_width, from_edge, thick_fives=True):
        '''
        In the style of standalone lines for each minute, with the five minutes thicker
        "arcs" because they're wider on the outside, for just straight lines use get_lines_detail

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

    def get_ring_detail(self, outer_r, width, detail_from_edges):
        return cq.Workplane("XY").circle(outer_r - detail_from_edges).circle(outer_r - (width - detail_from_edges*2)).extrude(self.detail_thick)

    def get_edge_style_width(self, edge_style=None, outer=True):
        if edge_style is None:
            return 0
        else:
            if edge_style is DialStyle.RING:
                return 0.8
            return self.dial_width*0.2
    def get_fancy_watch_numbers_detail(self, outer_r, width, detail_from_edges):
        numbers = self.get_numbers_detail(outer_r, width, detail_from_edges, only=["3", "6", "9"])

        arc = width*0.5
        angle = math.pi*2/30#arc / outer_r

        top_left = polar(math.pi/2 + angle/2, outer_r - detail_from_edges)
        top_right = polar( math.pi/2 - angle/2, outer_r - detail_from_edges)
        bottom = polar(math.pi/2, outer_r - width + detail_from_edges)

        top_triangle = cq.Workplane("XY").moveTo(bottom[0], bottom[1]).lineTo(top_left[0], top_left[1]).lineTo(top_right[0], top_right[1]).close().extrude(self.detail_thick)

        #short_line_length_fraction of 1 deliberately for this style
        lines = self.get_lines_detail(outer_r, width, detail_from_edges, total_lines=12, only=[1,2,4,5,7,8,10,11], small_thick=width*0.2, short_line_length_fraction=1)

        return numbers.add(top_triangle).add(lines)
    def get_style_for_dial(self, style, outer_r, width, detail_from_edges, inner_ring = False, outer_ring = False):

        total_markers = 60
        if self.hours_only:
            total_markers = 48

        if style == DialStyle.LINES_ARC:
            return self.get_arcs_detail(outer_r, width, detail_from_edges)
        elif style == DialStyle.LINES_RECT:
            return self.get_lines_detail(outer_r, width, detail_from_edges, total_lines=total_markers, thick_indicators=True, inner_ring=inner_ring, outer_ring = outer_ring)
        elif style == DialStyle.LINES_RECT_LONG_INDICATORS:
            return self.get_lines_detail(outer_r, width, detail_from_edges, total_lines=total_markers, long_indicators=True, inner_ring=inner_ring, outer_ring = outer_ring)
        elif style == DialStyle.CONCENTRIC_CIRCLES:
            return self.get_concentric_circles_detail(outer_r, width, detail_from_edges, thick_fives=True)
        elif style == DialStyle.ROMAN:
            return self.get_roman_numerals_detail(outer_r, width, detail_from_edges)
        elif style == DialStyle.DOTS:
            return self.get_dots_detail(outer_r, width)
        elif style == DialStyle.DOTS_MAJOR_ONLY:
            return self.get_dots_detail(outer_r, width, only_fives=True)
        elif style == DialStyle.ARABIC_NUMBERS:
            return self.get_numbers_detail(outer_r, width, detail_from_edges, minutes=self.minutes_only, seconds= self.seconds_only)
        elif style == DialStyle.FANCY_WATCH_NUMBERS:
            return self.get_fancy_watch_numbers_detail(outer_r, width, detail_from_edges)
        elif style == DialStyle.ROMAN_NUMERALS:
            return self.get_roman_numerals_detail(outer_r, width, detail_from_edges, with_lines=False)
        elif style == DialStyle.RING:
            return self.get_ring_detail(outer_r, width, detail_from_edges)
        elif style == DialStyle.LINES_INDUSTRIAL:
            return self.get_lines_detail(outer_r, width, detail_from_edges, thick_indicators=True, long_indicators=True, outer_ring=True,
                                         big_thick=width*0.25, small_thick=width*0.1, long_line_length_fraction=1, short_line_length_fraction=0.35)
        elif style == DialStyle.LINES_MAJOR_ONLY:
            # return self.get_lines_detail(outer_r, width, detail_from_edges, thick_indicators=True, long_indicators=True, outer_ring=outer_ring,
            #                              big_thick=width * 0.25, small_thick=0, long_line_length_fraction=1, short_line_length_fraction=0.35, only=[m for m in range(0,60,5)])
            return self.get_lines_detail(outer_r, width, detail_from_edges, total_lines=total_markers, thick_indicators=True, inner_ring=inner_ring, outer_ring=outer_ring, only=[m for m in range(0,60,5)])
        else:
            raise ValueError("Unsupported dial type")

    def get_main_dial_detail(self):
        '''
        detailing for the big dial
        '''

        if self.style == DialStyle.TONY_THE_CLOCK:
            if self.outer_edge_style is not None and self.inner_edge_style is not None:
                raise ValueError("Tony not supported with inner or outer edge styles")
            # extend the marks so they go underneath the black ring to allow for some slop attaching the ring
            extra = 2
            return self.get_quad_marks(self.outside_d / 2, self.outside_d * tony_the_clock["dial_marker_length"] / tony_the_clock["diameter"] + extra,
                                       self.outside_d * tony_the_clock["dial_marker_width"] / tony_the_clock["diameter"], self.outside_d * tony_the_clock["dial_edge_width"] / tony_the_clock["diameter"] - extra)

        main_style_outer_r = self.outside_d/2
        main_style_dial_width = self.dial_width
        main_style_detail_from_edges = self.dial_detail_from_edges

        outer_width = self.get_edge_style_width(self.outer_edge_style, outer=True)
        inner_width = self.get_edge_style_width(self.inner_edge_style, outer=False)

        main_style_outer_r -= outer_width
        main_style_dial_width -= outer_width

        main_style_dial_width -= inner_width

        if self.style is not None:
            main_style = self.get_style_for_dial(self.style, main_style_outer_r, main_style_dial_width, main_style_detail_from_edges)
        else:
            main_style = cq.Workplane("XY")

        dial = main_style

        if self.outer_edge_style is not None:
            dial = dial.union(self.get_style_for_dial(self.outer_edge_style, self.outside_d/2, outer_width, 0, outer_ring=True))
        if self.inner_edge_style is not None:
            dial = dial.union(self.get_style_for_dial(self.inner_edge_style, main_style_outer_r - main_style_dial_width, inner_width, 0, inner_ring=True))

        return dial

    def get_numbers_detail(self, outer_r, dial_width, dial_detail_from_edges, minutes=False, seconds=False, only = None):

        font = self.font
        if self.font is None:
            font = "Arial"



        numbers = [str(i) for i in range(1, 13)]
        if minutes or seconds:
            numbers = [str(i) for i in range(5, 65, 5)]

        if only is None:
            only = numbers
        centre_r = outer_r - dial_width/2
        number_height = (dial_width - dial_detail_from_edges*2)*self.font_scale
        number_spaces = [TextSpace(x=0, y=0, width=number_height, height=number_height, horizontal=True, text=numbers[i], thick=self.detail_thick, font=font, font_path=self.font_path) for i in range(12)]

        max_text_size = min([text_space.get_text_max_size() for text_space in number_spaces])

        for space in number_spaces:
            space.set_size(max_text_size)

        dial = cq.Workplane("XY")
        for i in range(12):
            if seconds and i not in [5,11]:
                continue

            if number_spaces[i].text not in only:
                continue

            angle = math.pi/2 + (i+1)*math.pi*2/12
            number_spaces[i].x, number_spaces[i].y = polar(angle, centre_r)
            # dial = dial.add(number_spaces[i].get_text_shape().rotate((0,0,0),(0,0,1), radToDeg(angle+math.pi/2)).translate(polar(angle, centre_r)))
            dial = dial.add(number_spaces[i].get_text_shape())



        return dial

    def get_seconds_dial_detail(self):
        dial = None
        outer_r = self.second_hand_mini_dial_d / 2
        from_edge = self.seconds_dial_detail_from_edges
        width = self.seconds_dial_width
        if self.seconds_style == DialStyle.LINES_ARC:
            dial = self.get_arcs_detail(outer_r=outer_r, dial_width=width, from_edge=self.seconds_dial_detail_from_edges, thick_fives=False)
        elif self.seconds_style == DialStyle.CONCENTRIC_CIRCLES:
            dial = self.get_concentric_circles_detail(self.second_hand_mini_dial_d / 2, self.seconds_dial_width, self.seconds_dial_detail_from_edges, thick_fives=False)
        else:
            dial = self.get_style_for_dial(style=self.seconds_style, outer_r=outer_r, width=width, detail_from_edges=from_edge)
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

            # if self.top_fixing:
            #     dial = dial.union(support.translate((0,r - self.dial_width/2, self.thick)))
            # if self.bottom_fixing:
            #     dial = dial.union(support.translate((0, -(r - self.dial_width / 2), self.thick)))

            for fixing_pos_set in self.get_fixing_positions():
                support_pos = (sum([x for x, y in fixing_pos_set]) / len(fixing_pos_set), sum([y for x, y in fixing_pos_set])/len(fixing_pos_set), self.thick)

                if self.pillar_style == PillarStyle.SIMPLE:
                    support = cq.Workplane("XY").circle(self.support_d / 2).extrude(self.support_length)
                else:
                    support = fancy_pillar(r=self.support_d / 2, length=self.support_length, clockwise=support_pos[0] < 0, style=self.pillar_style)

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

        if self.subtract_from_supports is not None:
            dial = dial.cut(self.subtract_from_supports)

        if self.add_to_back is not None:
            dial = dial.union(self.add_to_back)

        return dial

    def get_eye_positions(self):
        return [(-self.eye_distance_apart / 2, self.eye_y), ( self.eye_distance_apart / 2, self.eye_y)]

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
        #do want to try using new tiny m2 eye bolts instead of hot-glued bent wire!
        #offset from the centre so tehy don't hit the rod
        x_offset = self.eye_rod_d/2 + self.eye_screw.metric_thread/2 + 1
        #just self.eye_screw.metric_thread/2 radius was really a faff to get the screws in and tight enough not to need the nuts, so could leave it at that and remove nuts
        #or make it looser and keep nut
        eye = eye.cut(cq.Workplane("XY").moveTo(x_offset,0).circle(self.eye_screw.metric_thread/2).extrude(self.eye_extend_beyond_pivot + self.eye_radius*0.75).translate((0,0, -self.eye_extend_beyond_pivot)))
        # nut_hole_depth = self.eye_screw.getNutHeight(half=True)+1
        # eye = eye.cut(self.eye_screw.getNutCutter(height=nut_hole_depth, withBridging=True).translate((x_offset,0,self.eye_rod_d/2 + 1)))

        # wire_hole_depth = self.eye_pivot_z + self.eye_extend_beyond_pivot
        # eye = eye.cut(cq.Workplane("XY").circle(self.eye_bendy_wire_d/2).extrude(wire_hole_depth).translate((0,0,-wire_hole_depth)))

        return eye,pupil

    def get_wire_to_arbor_fixer_thick(self, rod_d=3):
        '''
        separate so it can be used in teh rod length calculations
        '''
        screw = MachineScrew(rod_d)
        return screw.get_nut_height(nyloc=True) * 2


    def get_wire_to_arbor_fixer(self, rod_d=3, for_printing=True):
        '''
        bit like the friction-fit pendulum holder, screws onto a rod and provides ability to glue a wire in

        Intended to drive the eyes from the pendulum
        '''

        screw = MachineScrew(rod_d)

        width = screw.get_nut_containing_diameter() + 4
        length = rod_d*5
        thick = self.get_wire_to_arbor_fixer_thick(rod_d)

        holder = cq.Workplane("XY").moveTo(0,(length-width)/2).rect(width,length-width).extrude(thick)
        holder = holder.union(cq.Workplane("XY").circle(width/2).extrude(thick))
        holder = holder.union(cq.Workplane("XY").moveTo(0,length-width).circle(width / 2).extrude(thick))

        holder = holder.faces(">Z").moveTo(0,length-width).circle(self.eye_bendy_wire_d/2).cutThruAll()
        holder = holder.faces(">Z").moveTo(0,0).circle(rod_d/2).cutThruAll()

        holder= holder.cut(screw.get_nut_cutter(nyloc=True).translate((0, 0, thick - screw.get_nut_height(nyloc=True))))

        if not for_printing:
            holder = holder.rotate((0,0,0),(1,0,0),180).translate((0,0,thick))

        return holder

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
            extras["eye_wire_to_arbor_fixer"] = self.get_wire_to_arbor_fixer()
        return extras

    def get_halfs(self, shape):
        top_includer = cq.Workplane("XY").rect(self.outside_d, self.outside_d/2).extrude(self.thick + self.support_d).translate((0,self.outside_d/4))
        # actually rotate by two and a half minutes so we don't slice through anything too complicated
        top_includer = top_includer.rotate((0, 0, 0), (0, 0, 1), -2.5 * 360 / 60).union(top_includer.rotate((0, 0, 0), (0, 0, 1), 2.5 * 360 / 60))

        halves = [shape.intersect(top_includer), shape.cut(top_includer)]

        return halves


    def output_STLs(self, name="clock", path="../out", max_wide=250, max_long=210):

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
