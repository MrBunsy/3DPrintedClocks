import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
from math import sin, cos, pi, floor
import numpy as np
import os

'''
Long term plan: this will be a library of useful classes to generate all the components and bits of clock plates
But another script will generate specific clock plates and arbours
'''

if 'show_object' not in globals():
    def show_object(*args, **kwargs):
        pass




class Gear:
    @staticmethod
    def cutHACStyle(gear,armThick, rimRadius):
        # vaguely styled after some HAC gears I've got, with nice arcing shapes cut out
        armAngle = armThick / rimRadius
        # cadquery complains it can't make a radiusArc with a radius < rimRadius*0.85. this is clearly bollocks as the sagittaArc works.
        innerRadius = rimRadius * 0.7
        # TODO might want to adjust this based on size of pinion attached to this wheel
        innerSagitta = rimRadius * 0.325

        arms = 5
        for i in range(arms):
            startAngle = i * math.pi * 2 / arms
            endAngle = (i + 1) * math.pi * 2 / arms - armAngle

            startPos = (math.cos(startAngle) * rimRadius, math.sin(startAngle) * rimRadius)
            endPos = (math.cos(endAngle) * rimRadius, math.sin(endAngle) * rimRadius)

            gear = gear.faces(">Z").workplane()
            gear = gear.moveTo(startPos[0], startPos[1]).radiusArc(endPos, -rimRadius).sagittaArc(startPos, -innerSagitta).close().cutThruAll()
            # .radiusArc(startPos,-innerRadius)\
            # .close().cutThruAll()
        return gear

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

    def getMaxRadius(self):
        return self.pitch_diameter/2 + self.addendum_factor*self.module

    def get3D(self, holeD=0, thick=0, style="HAC"):
        gear = self.get2D()

        if thick == 0:
            thick = round(self.pitch_diameter*0.05)
        gear = gear.extrude(thick)

        if holeD > 0:
            gear = gear.faces(">Z").workplane().circle(holeD/2).cutThruAll()

        if self.iswheel:
            if style == "HAC":

                rimThick = holeD
                rimRadius = self.pitch_diameter/2 - self.dedendum_factor*self.module - rimThick

                armThick = rimThick
                Gear.cutHACStyle(gear, armThick, rimRadius)



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
            # print("teeth: {}, angle: {}".format(t,tooth_angle*(t*2 + 1)))
            
            toothStartAngle = (tooth_angle + gap_angle)*t + gap_angle
            toothTipAngle = (tooth_angle + gap_angle)*t + gap_angle + tooth_angle/2
            toothEndAngle = (tooth_angle + gap_angle)*(t + 1)
            
            midBottomPos = ( math.cos(toothStartAngle)*inner_radius, math.sin(toothStartAngle)*inner_radius )
            addendum_startPos = ( math.cos(toothStartAngle)*pitch_radius, math.sin(toothStartAngle)*pitch_radius )
            tipPos = ( math.cos(toothTipAngle)*outer_radius, math.sin(toothTipAngle)*outer_radius )
            addendum_endPos = (math.cos(toothEndAngle) * pitch_radius, math.sin(toothEndAngle) * pitch_radius)
            endBottomPos = (math.cos(toothEndAngle) * inner_radius, math.sin(toothEndAngle) * inner_radius)

            # print(midBottomPos)

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
    '''
    Wheels drive pinions, and wheels and pinions are made to mesh together

    Each arbour will have the wheel of one pair and a pinion of a different pair - which need not have the same size module
    '''

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


class GoingTrain:
    gravity = 9.81
    def __init__(self, pendulum_period=1, fourth_wheel=False, escapement_teeth=30, min_pinion_teeth=10, max_wheel_teeth=100):
        '''
        Grand plan: auto generate gear ratios.
        Naming convention seems to be powered (spring/weight) wheel is first wheel, then minute hand wheel is second, etc, until the escapement
        However, all the 8-day clocks I've got have an intermediate wheel between spring powered wheel and minute hand wheel
        And only the little tiny balance wheel clocks have a "fourth" wheel.
        Regula 1-day cuckoos have the minute hand driven directly from the chain wheel, but then also drive the wheels up the escapment from the chain wheel, effectively making the chain
        wheel part of the gearing from the escapement to the minute wheel

        So, the plan: generate gear ratios from escapement to the minute hand, then make a wild guess about how much weight is needed and the ratio from the weight and
         where it should enter the escapment->minute hand chain

         so sod the usual naming convention until otherwise. Minute hand wheel is gonig to be zero, +ve is towards escapment and -ve is towards the powered wheel
         I suspect regula are onto something, so I may end up just stealing their idea

        '''

        #in seconds
        self.pendulum_period = pendulum_period
        #in metres
        self.pendulum_length = self.gravity * pendulum_period * pendulum_period / (4 * math.pi * math.pi)



        #calculate ratios from minute hand to escapement
        #the last wheel is the escapement
        self.wheels = 4 if fourth_wheel else 3

        self.escapement_time = pendulum_period * escapement_teeth
        self.escapement_teeth = escapement_teeth


        self.min_pinion_teeth=min_pinion_teeth
        self.max_wheel_teeth=max_wheel_teeth
        self.trains=[]

    def genTrain(self):

        desired_minute_time = 60*60
        #[ {time:float, wheels:[[wheelteeth,piniontheeth],]} ]
        options = []

        pinion_min=self.min_pinion_teeth
        pinion_max=20
        wheel_min=30
        wheel_max=self.max_wheel_teeth

        #TODO prefer non-integer combos.
        '''
        https://needhamia.com/clock-repair-101-making-sense-of-the-time-gears/
        “With an ‘integer ratio’, the same pairs of teeth (gear/pinion) always mesh on each revolution.
         With a non-integer ratio, each pass puts a different pair of teeth in mesh. (Some fractional 
         ratios are also called a ‘hunting ratio’ because a given tooth ‘hunts’ [walks around] the other gear.)”
         
         "So it seems clock designers prefer non-whole-number gear ratios to even out the wear of the gears’ teeth. "
         
         seems reasonable to me
        '''
        allGearPairCombos = []

        for p in range(pinion_min,pinion_max):
            for w in range(wheel_min, wheel_max):
                allGearPairCombos.append([w,p])

        #[ [[w,p],[w,p],[w,p]] ,  ]
        allTrains = []

        allTrainsLength = 1
        for i in range(self.wheels):
            allTrainsLength*=len(allGearPairCombos)

        # for i in range(allTrainsLength):
        #

        # for i in range(wheels):
        #     #clone
        #     # trains = allTrains[:]
        #     if i == 0:
        #         for j in range(len(allGearPairCombos)):
        #             allTrains.append([])
        #             allTrains[j].append(allGearPairCombos[j])
        #     else:
        #         currentLength = len(allTrains)
        #         for j in range(currentLength):
        #             for k in range(len):

        # def getComboBranch(allGearPairCombos, train, depth=0):
        #     if depth == 0:
        #         return getComboBranch(allGearPairCombos, allGearPairCombos[:], depth+1)
        #     if depth == self.wheels:


        #assuming no fourth wheel for now

        #this can be made generic for self.wheels, but I can't think of it right now. A stack or recursion will do the job
        #one fewer pairs than wheels
        if self.wheels == 3:
            for pair_0 in range(len(allGearPairCombos)):
                for pair_1 in range(len(allGearPairCombos)):
                        allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1]])
        elif self.wheels == 4:
            for pair_0 in range(len(allGearPairCombos)):
                for pair_1 in range(len(allGearPairCombos)):
                    for pair_2 in range(len(allGearPairCombos)):
                        allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1], allGearPairCombos[pair_2]])

        allTimes=[]
        for c in range(len(allTrains)):
            totalRatio = 1
            intRatio = False
            totalTeeth = 0
            #trying for small wheels and big pinions
            totalWheelTeeth = 0
            totalPinionTeeth = 0
            for p in range(len(allTrains[c])):
                ratio = allTrains[c][p][0] / allTrains[c][p][1]
                if ratio == round(ratio):
                    intRatio=True
                totalRatio*=ratio
                totalTeeth +=  allTrains[c][p][0] + allTrains[c][p][1]
                totalWheelTeeth += allTrains[c][p][0]
                totalPinionTeeth += allTrains[c][p][1]
            totalTime = totalRatio*self.escapement_time
            error = 60*60-totalTime

            train = {"time":totalTime, "train":allTrains[c], "error": abs(error), "ratio": totalRatio, "teeth": totalWheelTeeth/100-totalPinionTeeth/10 }
            if abs(error) < 1 and not intRatio:
                allTimes.append(train)

        allTimes.sort(key = lambda x: x["error"]+x["teeth"])
        # print(allTimes)

        self.trains = allTimes
    def printInfo(self):
        print(self.trains[0])
        print("pendulum length: {}m".format(self.pendulum_length))
        print("escapement time: {}s".format(self.escapement_time))

    def genGears(self, module_size=1.5, holeD=3):
        #TODO how many hours and how many gears between chain wheel and minute wheel (0+)?
        arbours = []
        thick = holeD*2
        style="HAC"
        pairs = [WheelPinionPair(wheel[0],wheel[1],module_size) for wheel in self.trains[0]["train"]]

        escapement = Escapement(self.escapement_teeth,module_size*100)

        for i in range(self.wheels):

            if i == 0:
                #minute wheel
                #TODO add chain wheel or chain wheel train pinion
                arbours.append(pairs[i].wheel.get3D(holeD=holeD,thick=thick, style=style))
            elif i < self.wheels-1:

                #intermediate wheels
                arbours.append(getArbour(pairs[i].wheel,pairs[i-1].pinion, holeD=holeD, thick=thick, style=style))
            else:
                #last pinion + escape wheel
                arbours.append(getArbour(escapement, pairs[i-1].pinion, holeD=holeD, thick=thick, style=style))

        self.arbours = arbours

    def outputSTLs(self, name="clock", path="../out"):
        for i,wheel in enumerate(self.arbours):
            out = os.path.join(path,"{}_wheel_{}.stl".format(name,i))
            print("Outputting ",out)
            exporters.export(wheel, out)

def degToRad(deg):
    return math.pi*deg/180

def polar(angle, radius):
    return (math.cos(angle) * radius, math.sin(angle) * radius)

def getArbour(wheel,pinion, holeD=0, thick=0, style="HAC"):
    base = wheel.get3D(thick=thick, holeD=holeD,style=style)

    top = pinion.get3D(thick=thick*3, holeD=holeD,style=style).translate([0,0,thick])

    arbour = base.add(top)

    arbour = arbour.faces(">Z").workplane().circle(pinion.getMaxRadius()).extrude(thick*0.5).circle(holeD/2).cutThruAll()
    return arbour

class Escapement:
    def __init__(self, teeth=42, diameter=100, anchorTeeth=None, recoil=True, lift=15, drop=2, run=2):
        '''
        Roughly following Mark Headrick's Clock and Watch Escapement Mechanics.
        if recoil, generate a recoil escapement, if false, deadbeat.
        Also from reading of The Modern Clock

        Choosing recoil as it's supposedly more reliable (even if less accurate) and should have less wear on the teeth, since
        most of the side of the tooth is in contact, rather than just the tip

        Deadbeat aim: teeth should be an even number that is not a multiple of 4 (aiming for x.5 number of teeth between the pallets - don't know if this is needed or not)
        for recoil, I don't think it matters, just any half number of teeth might do

        lift is the angle of pendulum swing, in degrees

        drop is the rotation of the escape wheel between the teeth engaging the pallets - this is lost energy
        from the weight/spring. However it seems to be required in a real clock. I *think* this is why some clocks are louder than others

        run is how much the anchor continues to move towards the centre of the escape wheel after locking (or in the recoil, how much it recoils) in degrees
        '''

        self.lift_deg = lift
        self.halfLift = 0.5*degToRad(lift)

        self.drop_deg= drop
        self.drop = degToRad(drop)

        self.run_deg = run
        self.run = degToRad(run)

        self.teeth = teeth
        self.diameter=diameter
        # self.anchourDiameter=anchourDiameter

        self.innerDiameter = diameter * 0.8

        self.radius = self.diameter/2

        self.innerRadius = self.innerDiameter/2

        self.toothHeight = self.diameter/2 - self.innerRadius

        self.recoil = recoil

        if anchorTeeth is None:
            if recoil:
                self.anchorTeeth = floor(self.teeth/6)+0.5
            else:
                self.anchorTeeth = floor(self.teeth/4)+0.5
        else:
            self.anchorTeeth = anchorTeeth

        # angle that encompases the teeth the anchor encompases
        self.wheelAngle = math.pi * 2 * self.anchorTeeth / self.teeth

        # height from centre of escape wheel to anchor pivot
        anchor_centre_distance = self.radius / math.cos(self.wheelAngle / 2)

        self.anchor_centre_distance = anchor_centre_distance

        self.anchorTopThickBase = (self.anchor_centre_distance - self.radius) * 0.6
        self.anchorTopThickMid = (self.anchor_centre_distance - self.radius) * 0.1
        self.anchorTopThickTop = (self.anchor_centre_distance - self.radius) * 0.75

    def getAnchor2D(self):

        anchor = cq.Workplane("XY")



        entryPalletAngle=degToRad(6)

        # arbitary, just needs to be long enough to contain recoil and lift
        entryPalletLength = self.toothHeight*0.5




        #distance from anchor pivot to the nominal point the anchor meets the escape wheel
        x = math.sqrt(math.pow(self.anchor_centre_distance,2) - math.pow(self.radius,2))

        entryPoint = (math.cos(math.pi/2+self.wheelAngle/2)*self.radius, math.sin(+math.pi/2+self.wheelAngle/2)*self.radius)

        # entrySideDiameter = anchor_centre_distance - entryPoint[1]

        #how far the entry pallet extends into the escape wheel (along the angle of entryPalletAngle)
        liftExtension = x * math.sin(self.halfLift)/math.sin(math.pi - self.halfLift - entryPalletAngle - self.wheelAngle/2)

        # #crude aprox
        # liftExtension2 = math.sin(self.halfLift)*x
        #
        # print(liftExtension)
        # print(liftExtension2)

        # liftExtension = 100

        entryPalletTip = (entryPoint[0] + math.cos(entryPalletAngle)*liftExtension, entryPoint[1] - math.sin(entryPalletAngle)*liftExtension)

        entryPalletEnd = (entryPalletTip[0] - math.cos(entryPalletAngle)* entryPalletLength, entryPalletTip[1] + math.sin(entryPalletAngle) * entryPalletLength)

        exitPalletTip = ( -entryPoint[0], entryPoint[1])

        # anchor = anchor.moveTo(entryPoint[0], entryPoint[1])
        # anchor = anchor.moveTo(entryPalletTip[0], entryPalletTip[1])





        endOfEntryPalletAngle = degToRad(35) # math.pi + wheelAngle/2 +
        endOfExitPalletAngle = degToRad(35)

        h = self.anchor_centre_distance - self.anchorTopThickBase - entryPalletTip[1]

        innerLeft = (entryPalletTip[0] - h*math.tan(endOfEntryPalletAngle), entryPoint[1] + h)
        innerRight = (exitPalletTip[0], innerLeft[1])


        h2 = self.anchor_centre_distance - self.anchorTopThickMid - exitPalletTip[1]
        farRight = (exitPalletTip[0] + h2*math.tan(endOfExitPalletAngle), exitPalletTip[1] + h2)
        farLeft = (-(exitPalletTip[0] + h2*math.tan(endOfExitPalletAngle)), exitPalletTip[1] + h2)

        top = (0, self.anchor_centre_distance + self.anchorTopThickTop)


        # anchor = anchor.lineTo(innerLeft[0], innerLeft[1]).lineTo(innerRight[0], innerRight[1]).lineTo(exitPalletTip[0], exitPalletTip[1])
        #
        # anchor = anchor.lineTo(farRight[0], farRight[1]).lineTo(top[0], top[1]).lineTo(farLeft[0], farLeft[1])

        # anchor = anchor.tangentArcPoint(entryPalletEnd, relative=False)
        # anchor = anchor.sagittaArc(entryPalletEnd, (farLeft[0] - entryPalletEnd[0])*1.75)
           #.lineTo(entryPalletEnd[0], entryPalletEnd[1])

        anchor = anchor.moveTo(entryPalletTip[0], entryPalletTip[1]).lineTo(entryPalletEnd[0],entryPalletEnd[1]).tangentArcPoint(farLeft,relative=False)

        anchor = anchor.lineTo(top[0], top[1]).lineTo(farRight[0], farRight[1]).lineTo(exitPalletTip[0], exitPalletTip[1]).lineTo(innerRight[0], innerRight[1])

        anchor = anchor.lineTo(innerLeft[0], innerLeft[1])

        anchor = anchor.close()

        return anchor

    def getAnchor3D(self, thick=15, holeD=2, clockwise=True):

        anchor = self.getAnchor2D()



        anchor = anchor.extrude(thick)

        if not clockwise:
            anchor = anchor.mirror("YZ", (0,0,0))

        anchor = anchor.faces(">Z").workplane().moveTo(0,self.anchor_centre_distance).circle(holeD/2).cutThruAll()

        return anchor

    def getAnchorArbour(self, holeD=3, anchorThick=10, clockwise=True, length=0, crutchHeight=50, crutchDepth=30):
        '''
        Going to try making the anchor and the pendulum one piece - not bothering with the crutch.
        I'm hoping that it'll be large enoguh to be relatively sturdy. We'll find out!

        length for how long to extend the 3d printed bit of the arbour - I'm still toying with the idea of using this to help keep things in place
        '''

        #get the anchor the other way around so we can build on top of it, and centre it on the pivot
        arbour = self.getAnchor3D(anchorThick, holeD, not clockwise).translate([0,-self.anchor_centre_distance,0])

        #clearly soemthing's wrong in the maths so anchorTopThickBase isn't being used as I'd hoped
        #bodgetime
        arbourRadius = min(self.anchorTopThickBase*0.85, self.anchorTopThickTop)

        if length > 0:
            arbour = arbour.faces(">Z").workplane().circle(arbourRadius).circle(holeD/2).extrude(length-anchorThick)

        return arbour

    def getWheel2D(self):


        dA = -math.pi*2/self.teeth

        if self.recoil:
            #based on the angle of the tooth being 20deg, but I want to calculate everyting in angles from the cetnre of the wheel
            #lazily assume arc along edge of inner wheel is a straight line
            toothAngle = math.pi*20/180
            toothTipAngle = 0
            toothBaseAngle = -math.atan(math.tan(toothAngle)*self.toothHeight/self.innerRadius)
        else:
            #done entirely by eye rather than working out the maths to adapt the book's geometry.
            toothTipAngle = -math.pi*0.05
            toothBaseAngle = -math.pi*0.03

        wheel = cq.Workplane("XY").lineTo(self.innerRadius, 0)

        for i in range(self.teeth):
            angle = dA*i
            tipPos = (math.cos(angle+toothTipAngle)*self.diameter/2, math.sin(angle+toothTipAngle)*self.diameter/2)
            nextbasePos = (math.cos(angle+dA) * self.innerRadius, math.sin(angle + dA) * self.innerRadius)
            endPos = (math.cos(angle+toothBaseAngle) * self.innerRadius, math.sin(angle + toothBaseAngle) * self.innerRadius)
            print(tipPos)
            # wheel = wheel.lineTo(0,tipPos[1])
            wheel = wheel.lineTo(tipPos[0], tipPos[1]).lineTo(endPos[0],endPos[1]).radiusArc(nextbasePos,self.innerDiameter)

        wheel = wheel.close()

        return wheel

    def getWheel3D(self, thick=5, holeD=5, style="HAC"):
        gear = self.getWheel2D().extrude(thick)

        rimThick = holeD
        rimRadius = self.innerRadius - rimThick

        armThick = rimThick
        if style == "HAC":
            gear = Gear.cutHACStyle(gear, armThick, rimRadius)

        gear = gear.faces(">Z").workplane().circle(holeD/2).cutThruAll()

        return gear
    #hack to masquerade as a Gear
    def get3D(self, thick=5, holeD=5, style="HAC"):
        return self.getWheel3D(thick=thick, holeD=holeD, style=style)
    # def getWithPinion(self, pinion, clockwise=True, thick=5, holeD=5, style="HAC"):
    #     base = self.getWheel3D(thick=thick,holeD=holeD, style=style)
    #
    #     top = pinion.get3D(thick=thick * 3, holeD=holeD, style=style).translate([0, 0, thick])
    #
    #     wheel = base.add(top)

        # # face = ">Z" if clockwise else "<Z"
        # #cut hole through both
        # wheel = wheel.faces(">Z").workplane().circle(pinion.getMaxRadius()).extrude(thick * 0.5).circle(holeD / 2).cutThruAll()


class ChainWheel:

    # def anglePerLink(self, radius):
    #     return math.atan(((self.chain_thick + self.chain_inside_length)/2) / (radius + self.chain_thick/2))

    # def getRadiusFromAnglePerLink(self, angle):
    #     return ( (self.chain_thick + self.chain_inside_length)/2 ) / math.tan(angle/2) - self.chain_thick/2

    def __init__(self, max_circumference=75, wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15):
        '''
        0.2 tolerance worked but could be tighter
        Going for a pocket-chain-wheel as this should be easiest to print in two parts

        default chain is for the spare hubert hurr chain I've got and probably don't need (wire_thick=1.25, inside_length=6.8, width=5)
        '''

        self.chain_width = width
        self.chain_thick = wire_thick
        self.chain_inside_length = inside_length

        # max_circumference = math.pi * max_diameter
        self.tolerance = tolerance
        link_length = inside_length*2 - tolerance
        leftover = max_circumference %  link_length

        #this is a circumference that fits exactly an even number of chain segments
        self.circumference = (max_circumference - leftover)

        #shouldn't need rounding
        self.pockets = int(self.circumference / link_length)

        n = self.pockets*2
        #https://en.wikipedia.org/wiki/Apothem "it is the line drawn from the center of the polygon that is perpendicular to one of its sides"
        apothem = ( self.chain_inside_length/2 - self.tolerance ) * math.tan((math.pi * (n - 2)) / (2*n))

        #diameter of the inner bit
        #a pocket is for two link segments
        # angle_per_single_link = math.pi*2/(self.pockets*2)

        self.diameter = (apothem - self.chain_thick/2)*2#self.getRadiusFromAnglePerLink(angle_per_single_link) * 2

        self.radius = self.diameter/2

        print("cicumference: {}, run time of:{:.1f}hours".format(self.circumference,self.getRunTime()))
        self.outerDiameter = self.diameter + width * 0.75
        self.outerRadius = self.outerDiameter/2




        self.wall_thick = width*0.4
        self.pocket_wall_thick = inside_length - wire_thick*4



        self.inner_width = width*1.2

        self.hole_distance = self.diameter*0.25

    def getRunTime(self,minuteRatio=1,chainLength=2000):
        #minute hand rotates once per hour, so this answer will be in hours
        return chainLength/((self.pockets*self.chain_inside_length*2)/minuteRatio)

    def getHalf(self, holeD=3.5 ,screwD=3):
        '''
        I'm hoping to be able to keep both halves identical - so long as there's space for the m3 screws and the m3 pivot then this should remain possible
        '''

        halfWheel = cq.Workplane("XY")

        halfWheel = halfWheel.circle(self.outerDiameter/2).extrude(self.wall_thick).faces(">Z").workplane().tag("inside")



        # width = self.chain_width*1.2

        #the U shape when looking at a slice through the pocket
        topGap = self.chain_thick*2.5
        midGap = self.chain_thick*2
        bottomGap = self.chain_thick*1.25

        h1 = (self.inner_width - midGap)/2
        h2 = (self.inner_width - bottomGap)/2
        h3 = self.inner_width/2

        bottomGapHeight = self.chain_width*0.5

        halfWheel = halfWheel.circle(self.diameter/2).extrude(h1).faces(">Z").workplane().circle(self.diameter/2).\
            workplane(offset=h2-h1).tag("inside2").circle(self.diameter/2-bottomGapHeight).loft(combine=True). \
            faces(">Z").workplane().circle(self.diameter/2-bottomGapHeight).extrude(bottomGap/2)

        dA = math.pi * 2 / self.pockets
        pocketA = self.pocket_wall_thick/self.outerRadius
        #angle the pocket ends inwards slightly
        pocketA_end_diff = pocketA*0.2

        for i in range(self.pockets):
            #the offset is a lazy way to ensure both halves can be identical, with the screw holes vertical
            angle = i*dA - pocketA/2


            halfWheel = halfWheel.workplaneFromTagged("inside")
            # .rotateAboutCenter(axisEndPoint=(0,0,1),angleDegrees=dA)
            # wp2 = halfWheel.transformed(offset=(0,0,self.inner_width/2)).moveTo(0, self.diameter/2).rect(self.chain_thick,self.chain_thick)
            # halfWheel = halfWheel.moveTo(0, self.diameter / 2).rect(self.chain_thick * 2, self.chain_thick * 2). \
            #     workplane(offset=self.inner_width / 2).moveTo(0, self.diameter / 2).rect(self.chain_thick, self.chain_thick).loft(combine=True)

            # radiusArc((math.cos(angle+pocketA)*self.outerRadius, math.sin(angle+pocketA)*self.outerRadius), -self.outerRadius).close().extrude(h1)

            #yay more weird cadquery bugs, can't have it with the full radius but 0.9999 is fine :/
            halfWheel = halfWheel.moveTo(0,0).lineTo(math.cos(angle)*self.radius, math.sin(angle)*self.radius).\
                lineTo(math.cos(angle+pocketA_end_diff) * self.outerRadius, math.sin(angle+pocketA_end_diff) * self.outerRadius).\
                radiusArc((math.cos(angle + pocketA - pocketA_end_diff) * self.outerRadius, math.sin(angle + pocketA- pocketA_end_diff) * self.outerRadius), -self.outerRadius*0.99999999).\
                lineTo(math.cos(angle+pocketA) * self.radius, math.sin(angle+pocketA) * self.radius).close().extrude(h1)
                # lineTo(math.cos(angle+pocketA)*self.outerRadius, math.sin(angle+pocketA)*self.outerRadius).close().extrude(h1)

        halfWheel = halfWheel.faces(">Z").workplane().circle(holeD/2).cutThruAll()
        halfWheel = halfWheel.faces(">Z").workplane().moveTo(0,self.hole_distance).circle(screwD / 2).cutThruAll()
        halfWheel = halfWheel.faces(">Z").workplane().moveTo(0,-self.hole_distance).circle(screwD / 2).cutThruAll()

        return halfWheel

class Ratchet:

    '''
    Plan is to do this slightly backwards - so the 'clicks' are attached to the chain wheel and the teeth are on the
    gear-wheel.

    This means that they can be printed as only two parts with minimal screws to keep everything together
    '''

    def __init__(self, totalD=50, thick=5, powerClockwise=True):
        # , chain_hole_distance=10, chain_hole_d = 3):
        # #distance of the screw holes on the chain wheel, so the ratchet wheel can be securely attached
        # self.chain_hole_distance = chain_hole_distance
        # self.chain_hole_d = chain_hole_d
        self.outsideDiameter=totalD

        self.outer_thick = self.outsideDiameter*0.1


        self.clickInnerDiameter = self.outsideDiameter * 0.5
        self.clickInnerRadius = self.clickInnerDiameter / 2

        self.clockwise = 1 if powerClockwise else -1

        self.toothLength = self.outsideDiameter*0.025
        self.toothAngle = degToRad(2)* self.clockwise

        self.toothRadius = self.outsideDiameter / 2 - self.outer_thick
        self.toothTipR = self.toothRadius - self.toothLength

        self.clicks = 8
        #ratchetTeet must be a multiple of clicks
        self.ratchetTeeth = self.clicks*1


        self.thick = thick

    def getInnerWheel(self):
        '''
        Contains the ratchet clicks, hoping that PETG will be strong and springy enough, if not I'll have to go for screws as pivots and some spring wire (stainless steel wire might work?)
        Intended to be larger than the chain wheel so it can be printed as part of teh same object
        '''
        wheel = cq.Workplane("XY")

        thick = 1.25

        innerClickR = self.clickInnerRadius

        #arc aprox thick
        clickArcAngle = self.clockwise * thick/innerClickR
        clickOffsetAngle = -(math.pi*2/self.clicks)*1 * self.clockwise

        dA = -math.pi*2 / self.clicks * self.clockwise

        start = polar(clickOffsetAngle, innerClickR)
        wheel = wheel.moveTo(start[0], start[1])

        outerR = self.toothRadius
        innerR = self.toothRadius-thick


        for i in range(self.clicks):
            toothAngle = dA * i
            clickStartAngle = dA * i + clickOffsetAngle
            clickEndAngle = clickStartAngle - clickArcAngle
            clickNextStartAngle = clickStartAngle + dA

            clickTip = polar(toothAngle, self.toothRadius)
            toothInner = polar(toothAngle-self.toothAngle, self.toothTipR)
            tipToInner = np.subtract(toothInner, clickTip)
            clickInner = tuple(np.add(clickTip, np.multiply(tipToInner, thick/np.linalg.norm(tipToInner))))

            clickStart = polar(clickStartAngle, innerClickR)
            clickEnd = polar(clickEndAngle, innerClickR)
            nextClickStart = polar(clickNextStartAngle, innerClickR)

            wheel = wheel.radiusArc(clickInner, -innerR).lineTo(clickTip[0], clickTip[1]).radiusArc(clickEnd, outerR).radiusArc(nextClickStart, innerClickR)


        wheel = wheel.close().extrude(self.thick)

        return wheel

    def getOuterWheel(self):
        '''
        contains the ratchet teeth, designed so it can be printed as part of the same object as a gear wheel
        '''
        wheel = cq.Workplane("XY").circle(self.outsideDiameter/2)#.circle(self.outsideDiameter/2-self.outer_thick)

        dA = math.pi * 2 / self.ratchetTeeth * self.clockwise


        wheel = wheel.moveTo(self.toothRadius,0)

        for i in range(self.ratchetTeeth):
            angle = dA * i

            wheel = wheel.lineTo(math.cos(angle - self.toothAngle) * self.toothTipR, math.sin(angle - self.toothAngle) * self.toothTipR)
            # wheel = wheel.radiusArc(polar(angle - self.toothAngle, self.toothTipR), self.toothTipR)
            # wheel = wheel.lineTo(math.cos(angle + dA) * self.toothRadius, math.sin(angle + dA) * self.toothRadius)
            wheel = wheel.radiusArc(polar(angle+dA, self.toothRadius), -self.toothRadius)

        wheel = wheel.close().extrude(self.thick)


        return wheel

def getChainWheelWithRatchet(ratchet, chainwheel, holeD=3.5 ,screwD=3):
    '''
    slightly OO encapsulation breaking. oh well.
    '''
    chain = chainwheel.getHalf(holeD=holeD, screwD=screwD).translate((0, 0, ratchet.thick))

    clickwheel = ratchet.getInnerWheel()


    # "the size of the circle the polygon is inscribed into"
    nutDiameter=6.2
    #TODO if we do this, make the nut tops bridgable
    # clickwheel = clickwheel.faces(">Z").workplane().circle(holeD/2).moveTo(0,chainwheel.hole_distance).polygon(6,nutDiameter).moveTo(0,-chainwheel.hole_distance).polygon(6,nutDiameter).cutThruAll()
    #be lazy for now and just screw into it
    clickwheel = clickwheel.faces(">Z").workplane().circle(holeD / 2).moveTo(0, chainwheel.hole_distance).circle(screwD/2).moveTo(0, -chainwheel.hole_distance).circle(screwD/2).cutThruAll()

    # combined = combined.faces("<Z").workplane()



    combined = clickwheel.add(chain)

    return combined

def getWheelWithRatchet(ratchet, gear, holeD=3, thick=5, style="HAC"):
    gearWheel = gear.get3D(holeD=holeD, thick=thick, style=style)

    ratchetWheel = ratchet.getOuterWheel().translate((0,0,thick))

    return gearWheel.add(ratchetWheel)

#
# ratchet = Ratchet()
#
# ratchetWheel = ratchet.getInnerWheel()
# clickWheel = ratchet.getOuterWheel()
#
# show_object(ratchetWheel)
# show_object(clickWheel)
#
# exporters.export(ratchetWheel, "../out/ratchetWheel.stl")
# exporters.export(clickWheel, "../out/clickWheel.stl")

# chainWithRatchet = getChainWheelWithRatchet(Ratchet(), ChainWheel())
#
# show_object(chainWithRatchet)
# exporters.export(chainWithRatchet, "../out/chainWithRatchet.stl")
#
# ratchet = Ratchet()
#
# click = ratchet.getInnerWheel()
# ratchetWheel = ratchet.getOuterWheel()
#
# show_object(click)
# show_object(ratchetWheel)
# exporters.export(click, "../out/clickWheel.stl")
# exporters.export(ratchetWheel, "../out/ratchetWheel.stl")
#
# wheelWithRatchet = getWheelWithRatchet(ratchet,WheelPinionPair(90, 8, 1.5).wheel)
# show_object(ratchet.getOuterWheel())
# # show_object(wheelWithRatchet)
# exporters.export(wheelWithRatchet, "../out/wheelWithRatchet.stl")
#
# chainWheel = ChainWheel()
#
# halfWheel = chainWheel.getHalf()
#
# # show_object(halfWheel)
#
# exporters.export(halfWheel, "../out/chainWheel.stl")

# escapement = Escapement()
# escapeWheel = escapement.getWheel3D()
# #
# show_object(escapeWheel)
# # exporters.export(escapeWheel, "../out/escapeWheel.stl")
#
# anchor = escapement.getAnchor3D()
#
# show_object(anchor)
#
#
# # train = GoingTrain(fourth_wheel=False, pendulum_period=1, escapement_teeth=40)
# #
# # exit(0)
#
# #{'time': 3600.0, 'train': [[36, 8], [50, 9], [48, 10]], 'error': 0.0, 'ratio': 120.0, 'teeth': 161}
# #{'time': 3600.0, 'train': [[44, 8], [48, 10], [50, 11]], 'error': 0.0, 'ratio': 120.0, 'teeth': 171}
#
# #{'time': 3600.0, 'train': [[48, 10], [55, 10], [50, 11]], 'error': 0.0, 'ratio': 120.0, 'teeth': 184}
#
#
# # #{'time': 3600.0, 'train': [[20, 8], [54, 8], [64, 9]], 'error': 0.0}
# # #[{'time': 3600.0, 'train': [[90, 8], [96, 9]], 'error': 0.0, 'ratio': 120.0},
# # #printed wheel in green:
# # #pair = WheelPinionPair(30, 8,2)



#
# moduleSize = 1.5
#
# '''
# thoughts:
# module of 2 prints very well - I think I can go below this without any trouble.
# A module size of 1.5 produces ~12cm diameter wheels if I have no fourth wheel
# However, that then requires a rather more thin arbour because the pinions are so small
#
# I think I might have to have a fourth wheel and larger gears just so 3-5mm rod will be able to fit
# '''
#
# pair = WheelPinionPair(36, 8, moduleSize)
# pair2 = WheelPinionPair(50, 9,moduleSize)
# pair3 = WheelPinionPair(48, 10,moduleSize)
# pair = WheelPinionPair(48, 10, moduleSize)
# pair2 = WheelPinionPair(55, 10,moduleSize)
# pair3 = WheelPinionPair(50, 11,moduleSize)
#
# pair = WheelPinionPair(81, 8, moduleSize)
# pair2 = WheelPinionPair(80, 9, moduleSize)
# # pair3 = WheelPinionPair(50, 11,moduleSize)
#
# # wheel=pair.getWheel()
#
# thick = 5
# arbourD=3
# #
# # wheel = pair.wheel.get3D(thick=thick, holeD=arbourD)
# # #mirror and rotate a bit so the teeth line up and look nice
# # pinion = pair.pinion.get3D(thick=thick, holeD=arbourD).rotateAboutCenter([0,1,0],180).rotateAboutCenter([0,0,1],180/pair.pinion.teeth).translate([pair.centre_distance,0,0])
# # #.rotateAboutCenter([0,0,1],-360/pair.pinion.teeth)
# #
# # show_object(wheel)
# # show_object(pinion)
# # show_object(cq.Workplane("XY").circle(10).extrude(20))
#
# arbour = getArbour(pair2.wheel, pair.pinion, arbourD, thick)
# # arbour2 = getArbour(pair3.wheel, pair2.pinion, arbourD, thick)
#
# show_object(arbour)
#
# exporters.export(arbour, "../out/arbour.stl")

#
# escapment = Escapement()
#
# anchor = escapment.getAnchorArbour(clockwise=True)
#
# show_object(anchor)