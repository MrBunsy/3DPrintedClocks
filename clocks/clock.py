import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
from math import sin, cos, pi, floor

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
    def __init__(self, pendulum_period=1, intermediate_wheel=False,fourth_wheel=False, escapement_teeth=30):
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

        escapement_time = pendulum_period * escapement_teeth
        desired_minute_time = 60*60
        #[ {time:float, wheels:[[wheelteeth,piniontheeth],]} ]
        options = []

        pinion_min=8
        pinion_max=20
        wheel_min=30
        wheel_max=100

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
            totalTime = totalRatio*escapement_time
            error = 60*60-totalTime

            train = {"time":totalTime, "train":allTrains[c], "error": abs(error), "ratio": totalRatio, "teeth": totalWheelTeeth-totalPinionTeeth }
            if abs(error) < 1 and not intRatio:
                allTimes.append(train)

        allTimes.sort(key = lambda x: x["error"]+x["teeth"])

        print(allTimes)

def degToRad(deg):
    return math.pi*deg/180

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



    def getAnchor2D(self):

        anchor = cq.Workplane("XY")

        # angle that encompases the teeth the anchor encompases
        wheelAngle = math.pi * 2 * self.anchorTeeth / self.teeth

        entryPalletAngle=degToRad(6)

        # arbitary, just needs to be long enough to contain recoil and lift
        entryPalletLength = self.toothHeight


        #height from centre of escape wheel to anchor pivot
        anchor_centre_distance = self.radius/math.cos(wheelAngle/2)

        #distance from anchor pivot to the nominal point the anchor meets the escape wheel
        x = math.sqrt(math.pow(anchor_centre_distance,2) - math.pow(self.radius,2))

        entryPoint = (math.cos(math.pi/2+wheelAngle/2)*self.radius, math.sin(+math.pi/2+wheelAngle/2)*self.radius)

        # entrySideDiameter = anchor_centre_distance - entryPoint[1]

        #how far the entry pallet extends into the escape wheel (along the angle of entryPalletAngle)
        liftExtension = x * math.sin(self.halfLift)/math.sin(math.pi - self.halfLift - entryPalletAngle - wheelAngle/2)

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
        anchor = anchor.moveTo(entryPalletTip[0], entryPalletTip[1])

        anchorTopThickBase = (anchor_centre_distance - self.radius)*0.6
        anchorTopThickMid = (anchor_centre_distance - self.radius)*0.1
        anchorTopThickTop = (anchor_centre_distance - self.radius) * 0.75



        endOfEntryPalletAngle = degToRad(15) # math.pi + wheelAngle/2 +
        endOfExitPalletAngle = degToRad(25)

        h = anchor_centre_distance - anchorTopThickBase - entryPalletTip[1]

        innerLeft = (entryPalletTip[0] - h*math.tan(endOfEntryPalletAngle), entryPoint[1] + h)
        innerRight = (exitPalletTip[0], innerLeft[1])


        h2 = anchor_centre_distance - anchorTopThickMid - exitPalletTip[1]
        farRight = (exitPalletTip[0] + h2*math.tan(endOfExitPalletAngle), exitPalletTip[1] + h2)
        farLeft = (-farRight[0], farRight[1])

        top = (0, anchor_centre_distance + anchorTopThickTop)


        anchor = anchor.lineTo(innerLeft[0], innerLeft[1]).lineTo(innerRight[0], innerRight[1]).lineTo(exitPalletTip[0], exitPalletTip[1])

        anchor = anchor.lineTo(farRight[0], farRight[1]).lineTo(top[0], top[1]).lineTo(farLeft[0], farLeft[1])

        # anchor = anchor.tangentArcPoint(entryPalletEnd, relative=False)
        # anchor = anchor.sagittaArc(entryPalletEnd, (farLeft[0] - entryPalletEnd[0])*1.75)
           #.lineTo(entryPalletEnd[0], entryPalletEnd[1])

        anchor = anchor.moveTo(entryPalletTip[0], entryPalletTip[1]).lineTo(entryPalletEnd[0],entryPalletEnd[1]).tangentArcPoint(farLeft,relative=False)

        anchor = anchor.close()

        return anchor

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
        gear = Gear.cutHACStyle(gear, armThick, rimRadius)

        gear = gear.faces(">Z").workplane().circle(holeD/2).cutThruAll()

        return gear

escapement = Escapement()
escapeWheel = escapement.getWheel3D()
#
show_object(escapeWheel)
# exporters.export(escapeWheel, "../out/escapeWheel.stl")

anchor = escapement.getAnchor2D()

show_object(anchor)
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
# # pair = WheelPinionPair(36, 8, moduleSize)
# # pair2 = WheelPinionPair(50, 9,moduleSize)
# # pair3 = WheelPinionPair(48, 10,moduleSize)
# # pair = WheelPinionPair(48, 10, moduleSize)
# # pair2 = WheelPinionPair(55, 10,moduleSize)
# # pair3 = WheelPinionPair(50, 11,moduleSize)
#
# pair = WheelPinionPair(81, 8, moduleSize)
# pair2 = WheelPinionPair(80, 9, moduleSize)
# # pair3 = WheelPinionPair(50, 11,moduleSize)
#
# # wheel=pair.getWheel()
#
# thick = 5
# arbourD=5
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