import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
from math import sin, cos, pi, floor

if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass

#
# # define the generating function
# def hypocycloid(t, r1, r2):
#     return ((r1-r2)*cos(t)+r2*cos(r1/r2*t-t), (r1-r2)*sin(t)+r2*sin(-(r1/r2*t-t)))
#
# def epicycloid(t, r1, r2):
#     return ((r1+r2)*cos(t)-r2*cos(r1/r2*t+t), (r1+r2)*sin(t)-r2*sin(r1/r2*t+t))
#
# def gear(t, r1=4, r2=1):
#     if (-1)**(1+floor(t/2/pi*(r1/r2))) < 0:
#         return epicycloid(t, r1, r2)
#     else:
#         return hypocycloid(t, r1, r2)





class Gear:
    def __init__(self, isWheel, teeth, module, addendum_factor, addendum_radius_factor, dedendum_factor, toothFactor=math.pi/2):
        self.iswheel = isWheel
        self.teeth = teeth
        self.module=module
        self.addendum_factor=addendum_factor
        # # BS 978 via https://www.csparks.com/watchmaking/CycloidalGears/index.jxl
        # self.addendum_radius_factor=addendum_factor * 1.4
        self.addendum_radius_factor=addendum_radius_factor
        self.dedendum_factor=dedendum_factor

        self.toothFactor = toothFactor

        self.pitch_diameter = self.module * self.teeth
        # # via practical addendum factor
        # self.addendum_height = 0.95 * addendum_factor * module

    def get3D(self, holeD=0, thick=0, style="HAC"):
        gear = self.get2D()

        if thick == 0:
            thick = round(self.pitch_diameter*0.05)
        gear = gear.extrude(thick)

        if holeD > 0:
            gear = gear.faces(">Z").workplane().circle(holeD/2).cutThruAll()

        if self.iswheel:
            if style == "HAC":
                #vaguely styled after some HAC gears I've got, with nice arcing shapes cut out
                rimThick = holeD
                rimRadius = self.pitch_diameter/2 - self.dedendum_factor*self.module - rimThick

                armThick = rimThick
                armAngle=armThick/rimRadius
                #cadquery complains it can't make a radiusArc with a radius < rimRadius*0.85. this is clearly bollocks as the sagittaArc works.
                innerRadius = rimRadius*0.7
                innerSagitta= rimRadius*0.325


                arms = 5
                for i in range(arms):
                    startAngle = i*math.pi*2/arms
                    endAngle = (i+1)*math.pi*2/arms - armAngle

                    startPos = (math.cos(startAngle)*rimRadius, math.sin(startAngle)*rimRadius)
                    endPos = (math.cos(endAngle) * rimRadius, math.sin(endAngle) * rimRadius)

                    gear = gear.faces(">Z").workplane()
                    gear = gear.moveTo(startPos[0], startPos[1]).radiusArc(endPos,-rimRadius).sagittaArc(startPos,-innerSagitta).close().cutThruAll()
                        # .radiusArc(startPos,-innerRadius)\
                        # .close().cutThruAll()



        return gear

    def get2D(self):
        '''
        Return a 2D cadquery profile of a single gear

        note - might need somethign different for pinions?
        '''


        pitch_radius = self.pitch_diameter / 2
        addendum_radius = self.module * self.addendum_radius_factor
        # via practical addendum factor
        addendum_height = 0.95 * self.addendum_factor * self.module
        dedendum_height = self.dedendum_factor * self.module

        inner_radius = pitch_radius - dedendum_height
        outer_radius = pitch_radius + addendum_height

        tooth_angle = self.toothFactor / (self.teeth/2)
        gap_angle = (math.pi - self.toothFactor) / (self.teeth/2)

        gear = cq.Workplane("XY")

        gear = gear.moveTo(inner_radius, 0)

        for t in range(self.teeth):
            print("teeth: {}, angle: {}".format(t,tooth_angle*(t*2 + 1)))
            
            toothStartAngle = (tooth_angle + gap_angle)*t + gap_angle
            toothTipAngle = (tooth_angle + gap_angle)*t + gap_angle + tooth_angle/2
            toothEndAngle = (tooth_angle + gap_angle)*(t + 1)
            
            midBottomPos = ( math.cos(toothStartAngle)*inner_radius, math.sin(toothStartAngle)*inner_radius )
            addendum_startPos = ( math.cos(toothStartAngle)*pitch_radius, math.sin(toothStartAngle)*pitch_radius )
            tipPos = ( math.cos(toothTipAngle)*outer_radius, math.sin(toothTipAngle)*outer_radius )
            addendum_endPos = (math.cos(toothEndAngle) * pitch_radius, math.sin(toothEndAngle) * pitch_radius)
            endBottomPos = (math.cos(toothEndAngle) * inner_radius, math.sin(toothEndAngle) * inner_radius)

            print(midBottomPos)

            #the gap
            gear = gear.radiusArc(midBottomPos, -inner_radius)
            gear = gear.lineTo(addendum_startPos[0], addendum_startPos[1])
            gear = gear.radiusArc(tipPos, -addendum_radius)
            gear = gear.radiusArc(addendum_endPos, -addendum_radius)
            gear = gear.lineTo(endBottomPos[0], endBottomPos[1])

            # gear = gear.lineTo(midBottomPos[0], midBottomPos[1])
            # gear = gear.lineTo(addendum_startPos[0], addendum_startPos[1])
            # gear = gear.lineTo(tipPos[0], tipPos[1])
            # gear = gear.lineTo(addendum_endPos[0], addendum_endPos[1])
            # gear = gear.lineTo(endBottomPos[0], endBottomPos[1])

        # gear = cq.Workplane("XY").circle(pitch_radius)
        gear = gear.close()

        return gear

class WheelPinionPair:
    errorLimit=0.000001
    def __init__(self, wheelTeeth, pinionTeeth, module=1.5):
        '''

        :param teeth:
        :param radius:
        '''
        # self.wheelTeeth = wheelTeeth
        # self.pinionTeeth=pinionTeeth
        self.module=module
        self.thick = module

        self.gear_ratio = wheelTeeth/pinionTeeth

        self.pinion_pitch_radius = self.module * pinionTeeth / 2
        self.wheel_pitch_radius = self.module * wheelTeeth / 2

        self.centre_distance = self.pinion_pitch_radius + self.wheel_pitch_radius

        # self.Diameter_generating_circle = self.pinion_pitch_radius



        wheel_addendum_factor = self.calcWheelAddendumFactor(pinionTeeth)
        # BS 978 via https://www.csparks.com/watchmaking/CycloidalGears/index.jxl says addendum radius factor is 1.4*addendum factor
        wheel_addendum_radius_factor=wheel_addendum_factor*1.4
        #TODO consider custom slop, this is from http://hessmer.org/gears/CycloidalGearBuilder.html
        wheel_dedendum_factor = math.pi/2
        self.wheel = Gear(True, wheelTeeth, module, wheel_addendum_factor, wheel_addendum_radius_factor, wheel_dedendum_factor)

        #based on the practical wheel addendum factor
        pinion_dedendum_factor = wheel_addendum_factor*0.95 + 0.4
        pinion_tooth_factor = 1.25
        if pinionTeeth <= 10:
            pinion_tooth_factor = 1.05
        #https://www.csparks.com/watchmaking/CycloidalGears/index.jxl
        if pinionTeeth == 6 or pinionTeeth == 7:
            pinion_addendum_factor=0.855
            pinion_addendum_radius_factor = 1.05
        elif pinionTeeth == 8 or pinionTeeth == 9:
            pinion_addendum_factor = 0.67
            pinion_addendum_radius_factor = 0.7
        else:
            pinion_addendum_factor = 0.625
            pinion_addendum_radius_factor = 0.625


        self.pinion=Gear(False, pinionTeeth, module, pinion_addendum_factor, pinion_addendum_radius_factor, pinion_dedendum_factor, pinion_tooth_factor)

    def calcWheelAddendumFactor(self,pinionTeeth):
        #http://hessmer.org/gears/CycloidalGearBuilder.html MIT licence
        beta = 0.0
        theta = 1.0
        thetaNew = 0.0
        R = self.gear_ratio
        while (abs(thetaNew - theta) > self.errorLimit):
            theta = thetaNew
            beta = math.atan2(math.sin(theta), (1.0 + 2 * R - math.cos(theta)))
            thetaNew = math.pi/pinionTeeth + 2 * R * beta

        theta = thetaNew

        k = 1.0 + 2 * R

        #addendum factor af
        addendumFactor = pinionTeeth / 4.0 * (1.0 - k + math.sqrt( 1.0 + k * k - 2.0 * k * math.cos(theta)) )
        return addendumFactor


    # def getWheel(self):
    #     addendum_factor = self.calcAddendumFactor()
    #     # wheel = gear2D(self.wheelTeeth, self.module, addendum_factor).extrude(self.thick)
    #
    #     #TODO holes and stuff
    #
    #     return wheel

pair = WheelPinionPair(30, 8,3)
# wheel=pair.getWheel()

thick = 5
arbourD=5

wheel = pair.wheel.get3D(thick=thick, holeD=arbourD)
#mirror and rotate a bit so the teeth line up and look nice
pinion = pair.pinion.get3D(thick=thick, holeD=arbourD).rotateAboutCenter([0,1,0],180).rotateAboutCenter([0,0,1],180/pair.pinion.teeth).translate([pair.centre_distance,0,0])
#.rotateAboutCenter([0,0,1],-360/pair.pinion.teeth)

show_object(wheel)
show_object(pinion)
# show_object(cq.Workplane("XY").circle(10).extrude(20))

exporters.export(wheel, "../out/wheel.stl")