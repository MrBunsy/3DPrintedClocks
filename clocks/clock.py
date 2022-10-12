from .utility import *
from .power import *
from .gearing import *
from .hands import *
from .escapements import *
import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
from math import sin, cos, pi, floor
import numpy as np
import os
import datetime




'''
Long term plan: this will be a library of useful classes to generate all the components and bits of clock plates
But another script will generate specific clock plates and arbours (note - the GoingTrain class has become a bit of a jack of all trades generating most of the arbours)

Note: naming conventions I can find for clock gears seem to assume you always have the same number of gears between the chain and the minute hand
this is blatantly false (I can see this just looking at the various clocks I have) so I'm adopting a different naming convention:

The minute hand arbour is arbour 0.
In the direction of the escapement is +=ve
in the direction of the chain/spring wheel is -ve

NOTE - although I thought it would be useful to always have the minute wheel as 0, it has actually proven to be more of a bother
A lot of operations require looping through all the bearings, and it would have been much easier to stick with the convention
It's probably too late now to refactor, but worth thinking about for the future 


So for a very simple clock where the minute arbour is also the chain wheel, there could be only three arbours: 0, 1 and 2 (the escape wheel itself)

This way I can add more gears in either direction without confusing things too much.

The gears that drive the hour hand are the motion work. The cannon pinion is attached to the minute hand arbour, this drives the minute wheel.
The minute wheel is on a mini arbour with the hour pinion, which drives the hour wheel. The hour wheel is on the hour shaft.
The hour shaft fits over the minute arbour (on the clock face side) and the hour hand is friction fitted onto the hour shaft

Current plan: the cannon pinion will be loose over the minute arbour, and have a little shaft for the minute hand.
A nyloc nut underneath it and a normal nut on top of the minute hand will provide friction from the minute arbour to the motion work.
I think this is similar to older cuckoos I've seen. It will result in a visible nut, but a more simple time train. Will try it
for the first clock and decide if I want to switch to something else later. 
'''



class GoingTrain:

    def __init__(self, pendulum_period=-1, pendulum_length=-1, wheels=3, fourth_wheel=None, escapement_teeth=30, chainWheels=0, hours=30, chainAtBack=True, maxWeightDrop=1800, escapement=None, escapeWheelPinionAtFront=None, usePulley=False):
        '''

        pendulum_period: desired period for the pendulum (full swing, there and back) in seconds
        fourth_wheel: if True there will be four wheels from minute hand to the escape wheel
        escapement_teeth: number of teeth on the escape wheel DEPRECATED, provide entire escapement instead
        chainWheels: if 0 the minute wheel is also the chain wheel, if >0, this many gears between the minute wheel and chain wheel (say for 8 day clocks)
        hours: intended hours to run for (dictates diameter of chain wheel)
        chainAtBack: Where the chain and ratchet mechanism should go relative to the minute wheel
        maxChainDrop: maximum length of chain drop to meet hours required, in mm
        max_chain_wheel_d: Desired diameter of the chain wheel, only used if chainWheels > 0. If chainWheels is 0 there is no flexibility here
        escapement: Escapement object. If not provided, falls back to defaults with esacpement_teeth

        escapeWheelPinionAtFront:  bool, override default

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

         This is intended to be agnostic to how the gears are laid out - the options are manually provided for which ways round the gear and scape wheel should face

        '''

        #in seconds
        self.pendulum_period = pendulum_period
        #in metres
        self.pendulum_length = pendulum_length

        self.arbours = []

        if pendulum_length < 0 and pendulum_period > 0:
            #calulate length from period
            self.pendulum_length = getPendulumLength(pendulum_period)
        elif pendulum_period < 0 and pendulum_length > 0:
            self.pendulum_period = getPendulumPeriod(pendulum_length)
        else:
            raise ValueError("Must provide either pendulum length or perioud, not neither or both")

        #note - this has become assumed in many places and will require work to the plates and layout of gears to undo
        self.chainAtBack = chainAtBack
        #likewise, this has been assumed, but I'm trying to undo those assumptions to use this
        self.penulumAtFront = True
        #to ensure the anchor isn't pressed up against the back (or front) plate
        if escapeWheelPinionAtFront is None:
            self.escapeWheelPinionAtFront = chainAtBack
        else:
            self.escapeWheelPinionAtFront=escapeWheelPinionAtFront

        self.powered_by = PowerType.NOT_CONFIGURED

        #if zero, the minute hand is directly driven by the chain, otherwise, how many gears from minute hand to chain wheel
        self.chainWheels = chainWheels
        #to calculate sizes of the powered wheels and ratios later
        self.hours = hours
        self.maxWeightDrop = maxWeightDrop
        self.usePulley=usePulley

        if fourth_wheel is not None:
            #old deprecated interface
            self.wheels = 4 if fourth_wheel else 3
        else:
            self.wheels = wheels

        #calculate ratios from minute hand to escapement
        #the last wheel is the escapement

        self.escapement=escapement
        if escapement is None:
            self.escapement = AnchorEscapement(teeth=escapement_teeth)
        #
        self.escapement_time = self.pendulum_period * self.escapement.teeth

        self.trains=[]

    def getCordUsage(self):
        '''
        how much rope or cord will actually be used, as opposed to how far the weight will drop
        '''
        if self.usePulley:
            return 2*self.maxWeightDrop
        return self.maxWeightDrop

    def calculateRatios(self,moduleReduction=0.85, min_pinion_teeth=10, max_wheel_teeth=100, pinion_max_teeth = 20, wheel_min_teeth = 50, max_error=0.1, loud=False):
        '''
        Returns and stores a list of possible gear ratios, sorted in order of "best" to worst
        module reduction used to calculate smallest possible wheels - assumes each wheel has a smaller module than the last
        '''

        desired_minute_time = 60*60
        #[ {time:float, wheels:[[wheelteeth,piniontheeth],]} ]
        options = []

        pinion_min=min_pinion_teeth
        pinion_max=pinion_max_teeth
        wheel_min=wheel_min_teeth
        wheel_max=max_wheel_teeth

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
        if loud:
            print("allGearPairCombos", len(allGearPairCombos))
        #[ [[w,p],[w,p],[w,p]] ,  ]
        allTrains = []

        allTrainsLength = 1
        for i in range(self.wheels):
            allTrainsLength*=len(allGearPairCombos)

        #this can be made generic for self.wheels, but I can't think of it right now. A stack or recursion will do the job
        #one fewer pairs than wheels
        allcomboCount=len(allGearPairCombos)
        if self.wheels == 2:
            for pair_0 in range(allcomboCount):
                allTrains.append([allGearPairCombos[pair_0]])
        if self.wheels == 3:
            for pair_0 in range(allcomboCount):
                for pair_1 in range(allcomboCount):
                        allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1]])
        elif self.wheels == 4:
            for pair_0 in range(allcomboCount):
                if loud and pair_0 % 10 == 0:
                    print("{:.1f}% of calculating trains".format(100*pair_0/allcomboCount))
                for pair_1 in range(allcomboCount):
                    for pair_2 in range(allcomboCount):
                        allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1], allGearPairCombos[pair_2]])
        if loud:
            print("allTrains", len(allTrains))
        allTimes=[]
        totalTrains = len(allTrains)
        for c in range(totalTrains):
            if loud and c % 100 == 0:
                print("{:.1f}% of combos".format(100*c/totalTrains))
            totalRatio = 1
            intRatio = False
            totalTeeth = 0
            #trying for small wheels and big pinions
            totalWheelTeeth = 0
            totalPinionTeeth = 0
            weighting = 0
            lastSize=0
            fits=True
            for p in range(len(allTrains[c])):
                ratio = allTrains[c][p][0] / allTrains[c][p][1]
                if ratio == round(ratio):
                    intRatio=True
                    break
                totalRatio*=ratio
                totalTeeth +=  allTrains[c][p][0] + allTrains[c][p][1]
                totalWheelTeeth += allTrains[c][p][0]
                totalPinionTeeth += allTrains[c][p][1]
                #module * number of wheel teeth - proportional to diameter
                size =  math.pow(moduleReduction, p)*allTrains[c][p][0]
                weighting += size
                if p > 0 and size > lastSize*0.9:
                    #this wheel is unlikely to physically fit
                    fits=False
                    break
                lastSize = size
            totalTime = totalRatio*self.escapement_time
            error = 60*60-totalTime

            train = {"time":totalTime, "train":allTrains[c], "error": abs(error), "ratio": totalRatio, "teeth": totalWheelTeeth, "weighting": weighting }
            if fits and  abs(error) < max_error and not intRatio:
                allTimes.append(train)

        allTimes.sort(key = lambda x: x["weighting"])
        # print(allTimes)

        self.trains = allTimes

        if len(allTimes) == 0:
            raise RuntimeError("Unable to calculate valid going train")

        return allTimes

    def setRatios(self, gearPinionPairs):
        '''
        Instead of calculating the gear train from scratch, use a predetermined one. Useful when using 4 wheels as those take a very long time to calculate
        '''
        #keep in the format of the autoformat
        time={'train': gearPinionPairs}

        self.trains = [time]

    def calculatePoweredWheelRatios(self, pinion_min = 10, pinion_max = 20, wheel_min = 20, wheel_max = 120):
        '''
        Calcualte the ratio of the chain wheel based on the desired runtime and chain drop
        TODO currently this tries to choose the largest wheel possible so it can fit. ideally we want the smallest wheel that fits to reduce plate size
        '''
        if self.chainWheels == 0:
            '''
            nothing to do, the diameter is calculted in calculatePoweredWheelInfo
            '''
        elif self.chainWheels == 1:

            turns = self.poweredWheel.getTurnsForDrop(self.getCordUsage())

            # find the ratio we need from the chain wheel to the minute wheel
            turnsPerHour = turns / self.hours

            desiredRatio = 1 / turnsPerHour

            # print("Chain wheel turns per hour", turnsPerHour)
            # print("Chain wheel ratio to minute wheel", desiredRatio)

            allGearPairCombos = []



            for p in range(pinion_min, pinion_max):
                for w in range(wheel_min, wheel_max):
                    allGearPairCombos.append([w, p])
            # print("ChainWheel: allGearPairCombos", len(allGearPairCombos))

            allRatios = []
            for i in range(len(allGearPairCombos)):
                ratio = allGearPairCombos[i][0] / allGearPairCombos[i][1]
                if round(ratio) == ratio:
                    # integer ratio
                    continue
                totalTeeth = 0
                # trying for small wheels and big pinions
                totalWheelTeeth = allGearPairCombos[i][0]
                totalPinionTeeth = allGearPairCombos[i][1]

                error = desiredRatio - ratio
                # want a fairly large wheel so it can actually fit next to the minute wheel (which is always going to be pretty big)
                train = {"ratio": ratio, "pair": allGearPairCombos[i], "error": abs(error), "teeth": totalWheelTeeth / 1000}
                if abs(error) < 0.1:
                    allRatios.append(train)

            allRatios.sort(key=lambda x: x["error"] - x["teeth"])  #

            # print(allRatios)

            self.chainWheelRatio = allRatios[0]["pair"]
        else:
            raise ValueError("Unsupported number of chain wheels")

    def setChainWheelRatio(self, pinionPair):
        '''
        Note, shouldn't need to use this anymore, and I think it's overriden when generating powered wheels anyway!
        '''
        self.chainWheelRatio = pinionPair

    def isWeightOnTheRight(self):
        '''
        returns true if the weight dangles from the right side of the chain wheel (as seen from the front)
        '''

        clockwise = self.poweredWheel.ratchet.isClockwise()
        chainAtFront = not self.chainAtBack

        #XNOR
        clockwiseFromFront = not (clockwise != chainAtFront)

        return clockwiseFromFront

    def calculatePoweredWheelInfo(self, default_powered_wheel_diameter=20):
        '''
        Calculate best diameter and direction of ratchet
        '''
        if self.chainWheels == 0:
            #no choice but to set diameter to what fits with the drop and hours
            self.powered_wheel_circumference = self.getCordUsage() / self.hours
            self.powered_wheel_diameter = self.powered_wheel_circumference / math.pi

        elif self.chainWheels == 1:
            #set the diameter to the minimum so the chain wheel gear ratio is as low as possible (TODO - do we always want this?)

            self.powered_wheel_diameter = default_powered_wheel_diameter

            self.powered_wheel_circumference = self.powered_wheel_diameter * math.pi

        # true for no chainwheels
        anticlockwise = self.chainAtBack

        for i in range(self.chainWheels):
            anticlockwise = not anticlockwise

        self.powered_wheel_clockwise = not anticlockwise

    def genChainWheels(self, ratchetThick=7.5, holeD=3.4, wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15,screwThreadLength=10):
        '''
        HoleD of 3.5 is nice and loose, but I think it's contributing to making the chain wheel wonky - the weight is pulling it over a bit
        Trying 3.3, wondering if I'm going to want to go back to the idea of a brass tube in the middle
        Gone back to 3.4 now that the arbour extension is part of the wheel, should be more stable and I don't want problems with the hands turning backwards when winding!
        don't want it to be too loose so it doesn't butt up against the front plate.
        TODO - provide metric thread and do this inside the chain wheel

        Generate the gear ratios for the wheels between chain and minute wheel
        again, I'd like to make this generic but the solution isn't immediately obvious and it would take
        longer to make it generic than just make it work
        '''

        self.calculatePoweredWheelInfo(ChainWheel.getMinDiameter())


        self.poweredWheel = ChainWheel(ratchet_thick=ratchetThick, power_clockwise=self.powered_wheel_clockwise, max_circumference=self.powered_wheel_circumference, wire_thick=wire_thick, inside_length=inside_length, width=width, holeD=holeD, tolerance=tolerance, screwThreadLength=screwThreadLength)

        self.calculatePoweredWheelRatios()

    def genCordWheels(self,ratchetThick=7.5, rodMetricThread=3, cordCoilThick=10, useKey=False, cordThick=2, style="HAC", preferedDiameter=-1, looseOnRod=True):
        '''
        If preferred diameter is provided, use that rather than the min diameter
        '''
        diameter = preferedDiameter
        if diameter < 0:
            diameter = CordWheel.getMinDiameter()

        self.calculatePoweredWheelInfo(diameter)
        self.poweredWheel = CordWheel(self.powered_wheel_diameter, ratchet_thick=ratchetThick, power_clockwise=self.powered_wheel_clockwise,rodMetricSize=rodMetricThread, thick=cordCoilThick, useKey=useKey, cordThick=cordThick, style=style, looseOnRod=looseOnRod)
        self.calculatePoweredWheelRatios()

    def genRopeWheels(self, ratchetThick = 3, rodMetricSize=3, wheelScrews=None, ropeThick=2.2, wallThick=2):

        self.calculatePoweredWheelInfo(RopeWheel.getMinDiameter())

        self.poweredWheel = RopeWheel(diameter=self.powered_wheel_diameter,ratchet_thick=ratchetThick, rodMetricSize=rodMetricSize, screw=wheelScrews, ropeThick=ropeThick, power_clockwise=self.powered_wheel_clockwise, wallThick=wallThick)

        self.calculatePoweredWheelRatios()


    def setTrain(self, train):
        '''
        Set a single train as the preferred train to generate everythign else
        '''
        self.trains = [train]


    def printInfo(self, weight_kg=0.35):
        print(self.trains[0])

        print("pendulum length: {}m period: {}s".format(self.pendulum_length, self.pendulum_period))
        print("escapement time: {}s teeth: {}".format(self.escapement_time, self.escapement.teeth))
        # print("cicumference: {}, run time of:{:.1f}hours".format(self.circumference, self.getRunTime()))
        chainRatio = 1
        chainRatios=[1]
        if self.chainWheels > 0:
            print(self.chainWheelRatio)
            #how many turns per turn of the minute wheel
            chainRatio = self.chainWheelRatio[0]/self.chainWheelRatio[1]
            #the wheel/pinion tooth count
            chainRatios=self.chainWheelRatio

        runtime_hours = self.poweredWheel.getRunTime(chainRatio, self.getCordUsage())

        drop_m = self.maxWeightDrop/1000
        power = weight_kg * GRAVITY * drop_m / (runtime_hours*60*60)
        power_uW = power * math.pow(10, 6)

        print("runtime: {:.1f}hours using {:.1f}m of cord/chain for a weight drop of {}. Chain wheel multiplier: {:.1f} ({})".format(runtime_hours, self.getCordUsage() / 1000,self.maxWeightDrop, chainRatio, chainRatios))
        print("With a weight of {}kg, this results in an average power usage of {:.1f}μW".format(weight_kg, power_uW))

        if len(self.arbours) > 0:
            self.getArbourWithConventionalNaming(0).printScrewLength()
            self.getArbourWithConventionalNaming(0).poweredWheel.printScrewLength()
        else:
            print("Generate gears to get screw information")

        if self.poweredWheel.type == PowerType.CORD:
            #because there are potentially multiple layers of cord on a cordwheel, power lever can vary enough for the clock to be viable when wound and not halfway through its run time!
            #seen this on clock 10!

            (rotations, layers, cordPerRotationPerLayer, cordPerLayer) = self.poweredWheel.getCordTurningInfo(self.maxWeightDrop*(2 if self.usePulley else 1))
            #cord per rotation divided by chainRatio, gives speed in mm per hour, we want in m/s to calculate power
            effective_weight = weight_kg / (2 if self.usePulley else 1)
            min_weight_speed = (cordPerRotationPerLayer[0] / chainRatio) /(60*60*1000)
            min_power = effective_weight * GRAVITY * min_weight_speed* math.pow(10, 6)
            max_weight_speed = (cordPerRotationPerLayer[-1] / chainRatio) / (60 * 60 * 1000)
            max_power = effective_weight * GRAVITY * max_weight_speed* math.pow(10, 6)
            print("Cordwheel power varies from {:.1f}μW to {:.1f}μW".format(min_power, max_power))

    def genGears(self, module_size=1.5, holeD=3, moduleReduction=0.5, thick=6, chainWheelThick=-1, escapeWheelThick=-1, escapeWheelMaxD=-1, useNyloc=False,
                 chainModuleIncrease=None, pinionThickMultiplier = 2.5, style="HAC", chainWheelPinionThickMultiplier=2, ratchetInset=False, thicknessReduction=1,
                 ratchetScrews=None, pendulumFixing=PendulumFixing.FRICTION_ROD):
        '''
        escapeWheelMaxD - if <0 (default) escape wheel will be as big as can fit
        if > 1 escape wheel will be as big as can fit, or escapeWheelMaxD big, if that is smaller
        if > 0 and < 1, escape wheel will be this fraction of the previous wheel



        '''
        arbours = []
        # ratchetThick = holeD*2
        #thickness of just the wheel
        self.gearWheelThick=thick
        #thickness of arbour assembly
        #wheel + pinion (3*wheel) + pinion top (0.5*wheel)

        if chainWheelThick < 0:
            chainWheelThick = thick

        if escapeWheelThick < 0:
            escapeWheelThick = thick * (thicknessReduction**(self.wheels-1))

        # self.gearPinionLength=thick*3
        # self.chainGearPinionLength = chainWheelThick*2.5


        self.gearPinionEndCapLength=thick*0.25
        # self.gearTotalThick = self.gearWheelThick + self.gearPinionLength + self.gearPinionEndCapLength
        # self.chainGearTotalThick

        # module_sizes = [module_size * math.pow(moduleReduction, i) for i in range(self.wheels)]

        #the module of each wheel is slightly smaller than the preceeding wheel
        pairs = [WheelPinionPair(wheel[0],wheel[1],module_size* math.pow(moduleReduction, i)) for i,wheel in enumerate(self.trains[0]["train"])]




        # print(module_sizes)
        #make the escape wheel as large as possible, by default
        escapeWheelDiameter = (pairs[len(pairs)-1].centre_distance - pairs[len(pairs)-1].pinion.getMaxRadius() - 3)*2

        #we might choose to override this
        if escapeWheelMaxD > 1 and escapeWheelDiameter > escapeWheelMaxD:
            escapeWheelDiameter = escapeWheelMaxD
        elif escapeWheelMaxD >0 and escapeWheelMaxD < 1:
            #treat as fraction of previous wheel
            escapeWheelDiameter = pairs[len(pairs) - 1].wheel.getMaxRadius() * 2 * escapeWheelMaxD

        # chain wheel imaginary pinion (in relation to deciding which way the next wheel faces) is opposite to where teh chain is
        chainWheelImaginaryPinionAtFront = self.chainAtBack

        #TODO - does this work when chain wheels are involved?
        secondWheelR = pairs[1].wheel.getMaxRadius()
        firstWheelR = pairs[0].wheel.getMaxRadius() + pairs[0].pinion.getMaxRadius()
        ratchetOuterR = self.poweredWheel.ratchet.outsideDiameter/2
        space = firstWheelR - ratchetOuterR
        if secondWheelR < space - 3:
            #the second wheel can actually fit on the same side as the ratchet
            chainWheelImaginaryPinionAtFront = not chainWheelImaginaryPinionAtFront

        #this is a bit messy. leaving it alone for now, but basically we manually choose which way to have the escape wheel but by default it's at front (if the chain is also at the front)
        escapeWheelPinionAtFront = self.escapeWheelPinionAtFront

        #only true if an odd number of wheels (note this IS wheels, not with chainwheels, as the minute wheel is always clockwise)
        escapeWheelClockwise = self.wheels %2 == 1

        escapeWheelClockwiseFromPinionSide = escapeWheelPinionAtFront == escapeWheelClockwise

        pinionAtFront = chainWheelImaginaryPinionAtFront

        # print("Escape wheel pinion at front: {}, clockwise (from front) {}, clockwise from pinion side: {} ".format(escapeWheelPinionAtFront, escapeWheelClockwise, escapeWheelClockwiseFromPinionSide))
        #escapment is now provided or configured in the constructor
        # self.escapement = Escapement(teeth=self.escapement_teeth, diameter=escapeWheelDiameter, type=self.escapement_type, lift=self.escapement_lift, lock=self.escapement_lock, drop=self.escapement_drop, anchorTeeth=None, clockwiseFromPinionSide=escapeWheelClockwiseFromPinionSide)
        # self.escapement.setDiameter(escapeWheelDiameter)
        # self.escapement.clockwiseFromPinionSide=escapeWheelClockwiseFromPinionSide
        # self.escapement.escapeWheelClockwise=escapeWheelClockwise
        self.escapement.setGearTrainInfo(escapeWheelDiameter, escapeWheelClockwiseFromPinionSide, escapeWheelClockwise)
        self.chainWheelArbours=[]
        if self.chainWheels > 0:
            # assuming one chain wheel for now
            if chainModuleIncrease is None:
                chainModuleIncrease = (1 / moduleReduction)

            chainModule = module_size * chainModuleIncrease
            chainDistance = chainModule * (self.chainWheelRatio[0] + self.chainWheelRatio[1]) / 2

            minuteWheelSpace = pairs[0].wheel.getMaxRadius() + holeD*2

            #check if the chain wheel will fit next to the minute wheel
            if chainDistance < minuteWheelSpace:
                # calculate module for the chain wheel based on teh space available
                chainModule = 2 * minuteWheelSpace / (self.chainWheelRatio[0] + self.chainWheelRatio[1])
            self.chainWheelPair = WheelPinionPair(self.chainWheelRatio[0], self.chainWheelRatio[1], chainModule)
            #only supporting one at the moment, but open to more in the future if needed
            self.chainWheelPairs=[self.chainWheelPair]
            self.chainWheelArbours=[Arbour(poweredWheel=self.poweredWheel, wheel = self.chainWheelPair.wheel, wheelThick=chainWheelThick, arbourD=self.poweredWheel.rodMetricSize, distanceToNextArbour=self.chainWheelPair.centre_distance, style=style, ratchetInset=ratchetInset, ratchetScrews=ratchetScrews)]
            pinionAtFront = not pinionAtFront

        for i in range(self.wheels):

            if i == 0:
                #minute wheel
                if self.chainWheels == 0:
                    #the minute wheel also has the chain with ratchet
                    arbour = Arbour(poweredWheel=self.poweredWheel, wheel = pairs[i].wheel, wheelThick=chainWheelThick, arbourD=holeD, distanceToNextArbour=pairs[i].centre_distance, style=style, pinionAtFront=not self.chainAtBack, ratchetInset=ratchetInset, ratchetScrews=ratchetScrews)
                else:
                    #just a normal gear
                    if self.chainWheels == 1:
                        pinionThick = self.chainWheelArbours[-1].wheelThick * chainWheelPinionThickMultiplier
                    else:
                        pinionThick = self.chainWheelArbours[-1].wheelThick * pinionThickMultiplier
                    arbour = Arbour(wheel = pairs[i].wheel, pinion=self.chainWheelPair.pinion, arbourD=holeD, wheelThick=thick, pinionThick=pinionThick, endCapThick=self.gearPinionEndCapLength, distanceToNextArbour= pairs[i].centre_distance, style=style, pinionAtFront=pinionAtFront)

                if useNyloc:
                    #regardless of chains, we need a nyloc nut to fix the wheel to the rod
                    arbour.setNutSpace(holeD)

                arbours.append(arbour)

            elif i < self.wheels-1:
                pinionThick = arbours[-1].wheelThick * pinionThickMultiplier

                if self.chainWheels == 0 and i == 1:
                    #this pinion is for the chain wheel
                    pinionThick = arbours[-1].wheelThick * chainWheelPinionThickMultiplier

                #intermediate wheels
                #no need to worry about front and back as they can just be turned around
                arbours.append(Arbour(wheel=pairs[i].wheel, pinion=pairs[i-1].pinion, arbourD=holeD, wheelThick=thick*(thicknessReduction**i), pinionThick=pinionThick, endCapThick=self.gearPinionEndCapLength,
                                distanceToNextArbour=pairs[i].centre_distance, style=style, pinionAtFront=pinionAtFront))
            else:
                #Using the manual override to try and ensure that the anchor doesn't end up against the back plate (or front plate)
                #automating would require knowing how far apart the plates are, which we don't at this point, so just do it manually
                pinionAtFront = self.escapeWheelPinionAtFront

                #last pinion + escape wheel, the escapment itself knows which way the wheel will turn
                #escape wheel has its thickness controlled by the escapement, but we control the arbour diameter
                arbours.append(Arbour(escapement=self.escapement, pinion=pairs[i - 1].pinion, arbourD=holeD, pinionThick=arbours[-1].wheelThick * pinionThickMultiplier, endCapThick=self.gearPinionEndCapLength,
                                      distanceToNextArbour=self.escapement.getDistanceBeteenArbours(), style=style, pinionAtFront=pinionAtFront))

            pinionAtFront = not pinionAtFront

        #anchor is the last arbour
        #"pinion" is the direction of the extended arbour for fixing to pendulum
        #this doesn't need arbourD or thickness as this is controlled by the escapement
        arbours.append(Arbour(escapement=self.escapement, pinionAtFront=self.penulumAtFront, pendulumFixing=pendulumFixing))

        self.wheelPinionPairs = pairs
        self.arbours = arbours




        # self.chainWheelArbours = []
        # if self.chainWheels > 0:
        #     self.chainWheelArbours=[getWheelWithRatchet(self.ratchet,self.chainWheelPair.wheel,holeD=holeD, thick=chainWheelThick, style=style)]

    def getArbourWithConventionalNaming(self, i):
        '''
        Use the traditional naming of the chain wheel being zero
        '''
        return self.getArbour(i - self.chainWheels)

    def getArbour(self, i):
        '''
        +ve is in direction of the anchor
        0 is minute wheel
        -ve is in direction of power ( so last chain wheel is -1, first chain wheel is -chainWheels)
        '''

        if i >= 0:
            return self.arbours[i]
        else:
            return self.chainWheelArbours[self.chainWheels+i]


    # def getMinuteWheelPinionPair(self):
    #     return self.wheelPinionPairs[0]

    def outputSTLs(self, name="clock", path="../out"):
        #wheels, chainwheels
        for i in range(self.wheels+self.chainWheels+1):
            arbour = self.getArbourWithConventionalNaming(i)
            out = os.path.join(path,"{}_wheel_{}.stl".format(name,i))
            print("Outputting ",out)
            exporters.export(arbour.getShape(), out)
            extras = arbour.getExtras()
            for extraName in extras:
                out = os.path.join(path, "{}_wheel_{}_{}.stl".format(name, i, extraName))
                print("Outputting ", out)
                exporters.export(extras[extraName], out)

        self.poweredWheel.outputSTLs(name, path)


        # for i,arbour in enumerate(self.chainWheelArbours):
        #     out = os.path.join(path, "{}_chain_wheel_{}.stl".format(name, i))
        #     print("Outputting ", out)
        #     exporters.export(arbour.getShape(), out)


        # out = os.path.join(path, "{}_escapement_test_rig.stl".format(name))
        # print("Outputting ", out)
        # exporters.export(self.escapement.getTestRig(), out)

        # out = os.path.join(path, "{}_anchor_spanner.stl".format(name))
        # print("Outputting ", out)
        # exporters.export(getSpanner(thick=self.arbours[-1].spannerBitThick,size=self.arbours[-1].getAnchorSpannerSize()), out)


class SimpleClockPlates:
    '''
    This took a while to settle - clocks before v4 will be unlikely to work anymore.

    Given that the simple plate is the only working implementation, would it make more sense to turn this class into the SimpleClockPlates?

    Any future plates are likely to be be very different in terms out laying out gears, and anything that is needed can always be spun out

    '''
    def __init__(self, goingTrain, motionWorks, pendulum, style="vertical", arbourD=3,pendulumAtTop=True, plateThick=5, backPlateThick=None,
                 pendulumSticksOut=20, name="", dial=None, heavy=False, extraHeavy=False, motionWorksAbove=False, usingPulley=False, pendulumFixing = PendulumFixing.FRICTION_ROD,
                 pendulumFixingBearing=None, pendulumAtFront=True, backPlateFromWall=0, fixingScrews=None):
        '''
        Idea: provide the train and the angles desired between the arbours, try and generate the rest
        No idea if it will work nicely!
        '''

        #how the pendulum is fixed to the anchor arbour.
        self.pendulumFixing = pendulumFixing
        self.pendulumAtFront = pendulumAtFront

        #only used for the direct arbour pendulum
        self.pendulumFixingBearing = pendulumFixingBearing
        if self.pendulumFixingBearing is None:
            #default to the 10mm bearing
            self.pendulumFixingBearing = getBearingInfo(10)

        anglesFromMinute = None
        anglesFromChain = None

        #"round" or "vertical"
        self.style=style
        #to print on the back
        self.name = name
        #to get fixing positions
        self.dial = dial

        self.motionWorksAbove=motionWorksAbove

        #is the weight heavy enough that we want to chagne the plate design?
        #will result in wider plates up to the chain wheel
        self.heavy = heavy
        #beef up the pillars as well
        self.extraHeavy = extraHeavy

        #is the weight danging from a pulley? (will affect screwhole and give space to tie other end of cord)
        self.usingPulley = usingPulley

        #just for the first prototype
        self.anchorHasNormalBushing=True
        self.motionWorks = motionWorks
        self.goingTrain = goingTrain
        self.pendulum=pendulum
        #up to and including the anchor
        self.anglesFromMinute = anglesFromMinute
        self.anglesFromChain=anglesFromChain
        self.plateThick=plateThick
        self.backPlateThick = backPlateThick
        if self.backPlateThick is None:
            self.backPlateThick = self.plateThick
        #default for anchor, overriden by most arbours
        self.arbourD=arbourD
        #how chunky to make the bearing holders
        self.bearingWallThick = 4

        self.pendulumAtTop = pendulumAtTop
        #how far away from the relevant plate (front if pendulumAtFront) the pendulum should be
        self.pendulumSticksOut = pendulumSticksOut
        #if this is 0 then pendulumAtFront is going to be needed
        self.backPlateFromWall = backPlateFromWall
        self.fixingScrews = fixingScrews
        if self.fixingScrews is None:
            self.fixingScrews = MachineScrew(metric_thread=3, countersunk=True, length=25)

        # how much space to leave around the edge of the gears for safety
        self.gearGap = 3
        self.smallGearGap = 2

        # self.holderInnerD=self.bearingOuterD - self.bearingHolderLip*2
        #if angles are not given, assume clock is entirely vertical

        if anglesFromMinute is None:
            #assume simple pendulum at top
            angle = math.pi/2 if self.pendulumAtTop else math.pi / 2

            #one extra for the anchor
            self.anglesFromMinute = [angle for i in range(self.goingTrain.wheels + 1)]
        if anglesFromChain is None:
            angle = math.pi / 2 if self.pendulumAtTop else -math.pi / 2

            self.anglesFromChain = [angle for i in range(self.goingTrain.chainWheels)]

        if self.style=="round":

            # TODO decide if we want the train to go in different directions based on which side the weight is
            side = -1 if self.goingTrain.isWeightOnTheRight() else 1
            arbours = [self.goingTrain.getArbourWithConventionalNaming(arbour) for arbour in range(self.goingTrain.wheels + self.goingTrain.chainWheels)]
            distances = [arbour.distanceToNextArbour for arbour in arbours]
            maxRs = [arbour.getMaxRadius() for arbour in arbours]
            arcAngleDeg = 270

            foundSolution=False
            while(not foundSolution and arcAngleDeg > 180):
                arcRadius = getRadiusForPointsOnAnArc(distances, degToRad(arcAngleDeg))

                # minDistance = max(distances)

                if arcRadius > max(maxRs):
                    #if none of the gears cross the centre, they should all fit
                    #pretty sure there are other situations where they all fit
                    #and it might be possible for this to be true and they still don't all fit
                    #but a bit of playing around and it looks true enough
                    foundSolution=True
                    self.compactRadius = arcRadius
                else:
                    arcAngleDeg-=1
            if not foundSolution:
                raise ValueError("Unable to calculate radius for gear ring, try a vertical clock instead")

            angleOnArc = -math.pi/2
            lastPos = polar(angleOnArc, arcRadius)

            for i in range(-self.goingTrain.chainWheels, self.goingTrain.wheels):
                '''
                Calculate angle of the isololese triangle with the distance at the base and radius as the other two sides
                then work around the arc to get the positions
                then calculate the relative angles so the logic for finding bearing locations still works
                bit over complicated
                '''
                # print("angle on arc: {}deg".format(radToDeg(angleOnArc)))
                nextAngleOnArc = angleOnArc + 2*math.asin(distances[i+self.goingTrain.chainWheels]/(2*arcRadius))*side
                nextPos = polar(nextAngleOnArc, arcRadius)

                relativeAngle = math.atan2(nextPos[1] - lastPos[1], nextPos[0] - lastPos[0])
                if i < 0 :
                    self.anglesFromChain[i + self.goingTrain.chainWheels] = relativeAngle
                else:
                    self.anglesFromMinute[i] = relativeAngle
                lastPos = nextPos
                angleOnArc = nextAngleOnArc


        #[[x,y,z],]
        #for everything, arbours and anchor
        self.bearingPositions=[]
        #TODO consider putting the anchor on a bushing
        # self.bushingPositions=[]
        self.arbourThicknesses=[]
        #how much the arbours can wobble back and forth. aka End-shake.
        #2mm seemed a bit much
        self.endshake = 1
        #height of the centre of the wheel that will drive the next pinion
        drivingZ = 0
        for i in range(-self.goingTrain.chainWheels, self.goingTrain.wheels +1):
            # print(str(i))
            if  i == -self.goingTrain.chainWheels:
                #the wheel with chain wheel ratchet
                #assuming this is at the very back of the clock
                #note - this is true when chain *is* at the back, when the chain is at the front the bearingPositions will be relative, not absolute
                pos = [0, 0, 0]
                self.bearingPositions.append(pos)
                #note - this is the chain wheel, which has the wheel at the back, but only pretends to have the pinion at the back for calculating the direction of the rest of the train
                drivingZ = self.goingTrain.getArbour(i).getWheelCentreZ()
                self.arbourThicknesses.append(self.goingTrain.getArbour(i).getTotalThickness())
                # print("pinionAtFront: {} wheel {} drivingZ: {}".format(self.goingTrain.getArbour(i).pinionAtFront, i, drivingZ), pos)
            else:
                r = self.goingTrain.getArbour(i - 1).distanceToNextArbour
                # print("r", r)
                #all the other going wheels up to and including the escape wheel
                if i == self.goingTrain.wheels:
                    # the anchor
                    escapement = self.goingTrain.getArbour(i).escapement
                    baseZ = drivingZ - self.goingTrain.getArbour(i-1).wheelThick/2 + escapement.getWheelBaseToAnchorBaseZ()
                    self.arbourThicknesses.append(escapement.getAnchorThick())
                    # print("is anchor")
                else:
                    #any of the other wheels
                    # pinionAtBack = not pinionAtBack
                    # print("drivingZ at start:{} pinionToWheel: {} pinionCentreZ: {}".format(drivingZ, self.goingTrain.getArbour(i).getPinionToWheelZ(), self.goingTrain.getArbour(i).getPinionCentreZ()))
                    pinionToWheel = self.goingTrain.getArbour(i).getPinionToWheelZ()
                    pinionZ = self.goingTrain.getArbour(i).getPinionCentreZ()
                    baseZ = drivingZ - pinionZ

                    drivingZ = drivingZ + pinionToWheel


                    self.arbourThicknesses.append(self.goingTrain.getArbour(i).getTotalThickness())

                if i <= 0:
                    angle = self.anglesFromChain[i - 1 + self.goingTrain.chainWheels]
                else:
                    angle = self.anglesFromMinute[i - 1]
                v = polar(angle, r)
                # v = [v[0], v[1], baseZ]
                lastPos = self.bearingPositions[-1]
                # pos = list(np.add(self.bearingPositions[i-1],v))
                pos = [lastPos[0] + v[0], lastPos[1] + v[1], baseZ]
                # if i < self.goingTrain.wheels:
                #     print("pinionAtFront: {} wheel {} r: {} angle: {}".format( self.goingTrain.getArbour(i).pinionAtFront, i, r, angle), pos)
                # print("baseZ: ",baseZ, "drivingZ ", drivingZ)

                self.bearingPositions.append(pos)


        # print(self.bearingPositions)

        topZs = [self.arbourThicknesses[i] + self.bearingPositions[i][2] for i in range(len(self.bearingPositions))]

        bottomZs = [self.bearingPositions[i][2] for i in range(len(self.bearingPositions))]

        bottomZ = min(bottomZs)
        if bottomZ < 0:
            #positions are relative (chain at front), so readjust everything
            topZs = [z-bottomZ for z in topZs]
            # bottomZs = [z - bottomZ for z in bottomZs]
            for i in range(len(self.bearingPositions)):
                self.bearingPositions[i][2] -= bottomZ

        if self.bearingPositions[-1][2] == 0:
            #the anchor would be directly up against the plate
            self.bearingPositions[-1][2] = WASHER_THICK#self.anchorThick*0.25

        # print(self.bearingPositions)
        self.plateDistance=max(topZs) + self.endshake

        print("Plate distance", self.plateDistance)

        #configure stuff for the arbours, now we know their absolute positions
        # poweredWheel=self.goingTrain.getArbourWithConventionalNaming(0)
        # poweredWheelBracingR = poweredWheel.distanceToNextArbour - self.goingTrain.getArbourWithConventionalNaming(1).getMaxRadius() - self.gearGap
        #
        # #no need for it to be massive
        # poweredWheelBracingR = min(10,poweredWheelBracingR)
        # poweredWheel.setArbourExtensionInfo(rearSide=self.bearingPositions[0][2], maxR=poweredWheelBracingR)

        for i,bearingPos in enumerate(self.bearingPositions):
            arbour = self.goingTrain.getArbourWithConventionalNaming(i)
            if i < self.goingTrain.wheels + self.goingTrain.chainWheels - 2:
                maxR = arbour.distanceToNextArbour - self.goingTrain.getArbourWithConventionalNaming(i+1).getMaxRadius() - self.smallGearGap
            else:
                maxR = 0
            arbour.setPlateInfo(rearSideExtension=bearingPos[2], maxR=maxR, frontSideExtension=self.plateDistance - self.endshake - bearingPos[2] - arbour.getTotalThickness(),
                                frontPlateThick=self.getPlateThick(back=False), pendulumSticksOut=self.pendulumSticksOut, backPlateThick=self.getPlateThick(back=True), endshake=self.endshake,
                                pendulumFixingBearing=self.pendulumFixingBearing)

        motionWorksDistance = self.motionWorks.getArbourDistance()
        #get position of motion works relative to the minute wheel
        if style == "round":
            #place the motion works on the same circle as the rest of the bearings
            angle =  2*math.asin(motionWorksDistance/(2*self.compactRadius))
            compactCentre = (0, self.compactRadius)
            minuteAngle = math.atan2(self.bearingPositions[self.goingTrain.chainWheels][1] - compactCentre[1], self.bearingPositions[self.goingTrain.chainWheels][0] - compactCentre[0])
            motionWorksPos = polar(minuteAngle - angle, self.compactRadius)
            motionWorksPos=(motionWorksPos[0] + compactCentre[0], motionWorksPos[1] + compactCentre[1])
            self.motionWorksRelativePos = (motionWorksPos[0] - self.bearingPositions[self.goingTrain.chainWheels][0], motionWorksPos[1] - self.bearingPositions[self.goingTrain.chainWheels][1])
        else:
            #motion works is directly below the minute rod
            self.motionWorksRelativePos = [0, motionWorksDistance * (1 if self.motionWorksAbove else -1)]

        self.chainHoleD = self.goingTrain.poweredWheel.getChainHoleD()

        self.weightOnRightSide = self.goingTrain.isWeightOnTheRight()

        #absolute z position
        self.embeddedNutHeight = self.getPlateThick(back=True) + self.plateDistance  + self.getPlateThick(back=False) - (self.fixingScrews.length - 10)


    def getPlateThick(self, back=True):
        if back:
            return self.backPlateThick
        return self.plateThick

    def getScrewHolePositions(self):
        '''
        returns [(x,y, supported),]
        for where the holes to fix the clock to the wall will be

        This logic is a bit of a mess, it was pulled out of the tangle in clock plates and could do with tidying up
        '''
        bottomScrewHoleY = self.bearingPositions[0][1] + (self.bearingPositions[1][1] - self.bearingPositions[0][1]) * 0.6

        extraSupport = True
        if self.usingPulley and self.heavy:
            # the back plate is wide enough to accomodate
            extraSupport = False

        weightX = 0
        weightOnSide = 1 if self.weightOnRightSide else -1
        if self.heavy and not self.usingPulley:
            # line up the hole with the big heavy weight
            weightX = weightOnSide * self.goingTrain.poweredWheel.diameter / 2

        if self.style == "round":
            #screwHoleY = chainWheelR * 1.4
            raise NotImplemented("Haven't fixed this for round clocks")

        elif self.style == "vertical":
            if self.extraHeavy:

                # below anchor
                topScrewHoleY = self.bearingPositions[-2][1] + (self.bearingPositions[-1][1] - self.bearingPositions[-2][1]) * 0.6
                return [(weightX, bottomScrewHoleY, extraSupport), (weightX, topScrewHoleY, True)]
            else:
                # just below anchor
                screwHoleY = self.bearingPositions[-2][1] + (self.bearingPositions[-1][1] - self.bearingPositions[-2][1]) * 0.6

                return [(weightX, screwHoleY, extraSupport)]

    def getDrillTemplate(self,drillHoleD=7):

        screwHoles = self.getScrewHolePositions()

        if len(screwHoles) <= 1:
            raise ValueError("Can't make template without at least two screwholes")

        ys = [hole[1] for hole in screwHoles]
        xs = [hole[0] for hole in screwHoles]
        maxY = max(ys)
        minY = min(ys)
        minX = min(xs)
        maxX = max(xs)

        minWidth = maxX - minX
        minHeight = maxY - minY

        border = drillHoleD*2
        thick = 3

        template = cq.Workplane("XY").moveTo(minX + minWidth/2, minY + minHeight/2).rect(minWidth + border*2, minHeight + border*2).extrude(thick)

        for hole in screwHoles:
            template = template.faces(">Z").workplane().moveTo(hole[0], hole[1]).circle(drillHoleD/2).cutThruAll()

        return template

    def getPillarInfo(self):
        '''
        return (topPillarPos, topPillarR, bottomPillarPos, bottomPillarR, holderWide)
        '''
        bearingInfo = getBearingInfo(self.arbourD)
        # width of thin bit
        holderWide = bearingInfo.bearingOuterD + self.bearingWallThick * 2

        if self.extraHeavy:
            holderWide *= 1.2

        chainWheelR = self.goingTrain.getArbour(-self.goingTrain.chainWheels).getMaxRadius() + self.gearGap

        # original thinking was to make it the equivilant of a 45deg shelf bracket, but this is massive once cord wheels are used
        # so instead, make it just big enough to contain the holes for the chains/cord

        furthestX = max([abs(holePos[0][0]) for holePos in self.goingTrain.poweredWheel.getChainPositionsFromTop()])

        # juuust wide enough for the small bits on the edge of the bottom pillar to print cleanly
        minDistanceForChainHoles = (furthestX * 2 + self.chainHoleD + 5) / 2

        bottomPillarR = minDistanceForChainHoles

        if self.heavy:
            bottomPillarR = self.plateDistance / 2

        if bottomPillarR < minDistanceForChainHoles:
            bottomPillarR = minDistanceForChainHoles
        topPillarR = holderWide / 2

        anchorSpace = bearingInfo.bearingOuterD / 2 + self.gearGap

        # find the Y position of the bottom of the top pillar
        topY = self.bearingPositions[0][1]
        if self.style == "round":
            # find the highest point on the going train
            # TODO for potentially large gears this might be lower if they're spaced right
            for i in range(len(self.bearingPositions) - 1):
                y = self.bearingPositions[i][1] + self.goingTrain.getArbourWithConventionalNaming(i).getMaxRadius() + self.gearGap
                if y > topY:
                    topY = y
        else:

            topY = self.bearingPositions[-1][1] + anchorSpace

        bottomPillarPos = [self.bearingPositions[0][0], self.bearingPositions[0][1] - chainWheelR - bottomPillarR]
        topPillarPos = [self.bearingPositions[0][0], topY + topPillarR]


        return (topPillarPos, topPillarR, bottomPillarPos, bottomPillarR, holderWide)

    def getWallStandoff(self, top=True):
        '''
        If the back plate isn't directly up against the wall, we need two more peices that attach to the top and bottom pillars on the back
        if the pendulum is at the back (likely given there's not much other reason to not be against the wall) the bottom peice will need
        a large gap or the hand-avoider
        '''

    def getPlate(self, back=True, getText=False):
        '''
        Two plates that are almost idential, with pillars at the very top and bottom to hold them together.
        Designed to be flat up against the wall, with everything offset to avoid the wall and picture rail

        styles: round or vertical
        round minimises total height by placing the gear train in a circle, so more complicated clocks can still fit on the print bed
        vertical just has everything directly above each other.

        The screwhole is placed directly above the weight to make the clock easier to hang straight

        '''
        topPillarPos, topPillarR, bottomPillarPos, bottomPillarR, holderWide = self.getPillarInfo()

        chainWheelR = self.goingTrain.getArbour(-self.goingTrain.chainWheels).getMaxRadius() + self.gearGap

        plate = cq.Workplane("XY").tag("base")
        if self.style=="round":
            radius = self.compactRadius + holderWide / 2
            #the ring that holds the gears
            plate = plate.moveTo(self.bearingPositions[0][0], self.bearingPositions[0][1] + self.compactRadius).circle(radius).circle(radius - holderWide).extrude(self.getPlateThick(back))
        elif self.style == "vertical":
            #rectangle that just spans from the top bearing to the bottom pillar (so we can vary the width of the bottom section later)
            plate = plate.moveTo(self.bearingPositions[0][0]-holderWide/2, self.bearingPositions[0][1] - chainWheelR).line(holderWide,0).\
                lineTo(self.bearingPositions[-1][0]+holderWide/2, self.bearingPositions[-1][1]).line(-holderWide,0).close().extrude(self.getPlateThick(back))

        #original thinking was to make it the equivilant of a 45deg shelf bracket, but this is massive once cord wheels are used
        #so instead, make it just big enough to contain the holes for the chains/cord

        plate = plate.tag("top")

        topOfBottomBitPos = self.bearingPositions[0]

        screwHolePositions = self.getScrewHolePositions()

        bottomScrewHoleY = min([hole[1] for hole in screwHolePositions])

        if self.heavy and self.usingPulley and back:
            #instead of an extra circle around the screwhole, make the plate wider extend all the way up
            #because the screwhole will be central when heavy and using a pulley
            topOfBottomBitPos = (0, bottomScrewHoleY)


        fixingPositions = [(topPillarPos[0] -topPillarR / 2, topPillarPos[1]), (topPillarPos[0] + topPillarR / 2, topPillarPos[1]), (bottomPillarPos[0], bottomPillarPos[1] + bottomPillarR * 0.5), (bottomPillarPos[0], bottomPillarPos[1] - bottomPillarR * 0.5)]


        #supports all the combinations of round/vertical and chainwheels or not
        topRound = self.style == "vertical"
        narrow = self.goingTrain.chainWheels == 0
        bottomBitWide = holderWide if narrow else bottomPillarR*2

        #link the bottom pillar to the rest of the plate
        plate = plate.workplaneFromTagged("base").moveTo(topOfBottomBitPos[0] - bottomBitWide/2, topOfBottomBitPos[1])
        if topRound:
            # do want the wide bit nicely rounded
            plate = plate.radiusArc((topOfBottomBitPos[0] + bottomBitWide/2, topOfBottomBitPos[1]), bottomBitWide/2)
        else:
            # square top
            plate = plate.line(bottomBitWide, 0)

        #just square, will pop a round bit on after
        plate = plate.lineTo(bottomPillarPos[0] + bottomBitWide/2, bottomPillarPos[1]).line(-bottomBitWide,0)

        plate = plate.close().extrude(self.getPlateThick(back))

        plate = plate.workplaneFromTagged("base").moveTo(bottomPillarPos[0], bottomPillarPos[1]).circle(bottomPillarR).extrude(self.getPlateThick(back))




        if self.style == "round":
            #centre of the top of the ring
            topOfPlate = (self.bearingPositions[0][0], self.bearingPositions[0][1] + self.compactRadius * 2)
        elif self.style == "vertical":
            #topmost bearing
            topOfPlate = self.bearingPositions[-1]

        # link the top pillar to the rest of the plate
        if back:
            #the pillar will fill the rest in (and cadquery has some bugs with putting circles perfectly on top of circles)
            plate = plate.workplaneFromTagged("base").moveTo(topOfPlate[0] - topPillarR, topOfPlate[1]) \
                .lineTo(topPillarPos[0] - topPillarR, topPillarPos[1]).line(topPillarR*2,0) \
                .lineTo(topOfPlate[0] + topPillarR, topOfPlate[1]).close().extrude(self.getPlateThick(back))
        else:
            plate = plate.workplaneFromTagged("base").moveTo(topOfPlate[0] - topPillarR, topOfPlate[1]) \
                .lineTo(topPillarPos[0] - topPillarR, topPillarPos[1]).radiusArc((topPillarPos[0] + topPillarR, topPillarPos[1]), topPillarR) \
                .lineTo(topOfPlate[0] + topPillarR, topOfPlate[1]).close().extrude(self.getPlateThick(back))


        plate = plate.tag("top")
        # #for the screwhole
        # screwHeadD = 9
        # screwBodyD = 6
        # slotLength = 7

        if back:

            backThick = max(self.getPlateThick(back)-5, 4)

            screwHeadD = 11
            if self.backPlateFromWall == 0:
                for screwPos in screwHolePositions:
                    plate = self.addScrewHole(plate, (screwPos[0], screwPos[1]), backThick=backThick, screwHeadD=screwHeadD, addExtraSupport=screwPos[2])

            #the pillars

            if self.extraHeavy:
                '''
                beef up the bottom pillar
                bottomPillarR^2 + x^2 = chainWheelR^2
                x = sqrt(chainWheelR^2 - bottomPilarR^2)

                '''
                pillarTopZ = self.bearingPositions[0][1] - math.sqrt(chainWheelR ** 2 - bottomPillarR ** 2)
                try:
                    plate = plate.workplaneFromTagged("top").moveTo(bottomPillarPos[0] - bottomPillarR, bottomPillarPos[1]).radiusArc((bottomPillarPos[0] + bottomPillarR, bottomPillarPos[1]), -bottomPillarR). \
                        lineTo(bottomPillarPos[0] + bottomPillarR, pillarTopZ).radiusArc((bottomPillarPos[0] - bottomPillarR, pillarTopZ), chainWheelR).close().extrude(self.plateDistance)
                except:
                    plate = plate.workplaneFromTagged("top").moveTo(bottomPillarPos[0] - bottomPillarR, bottomPillarPos[1]).radiusArc((bottomPillarPos[0] + bottomPillarR, bottomPillarPos[1]), -bottomPillarR*1.000001). \
                        lineTo(bottomPillarPos[0] + bottomPillarR, pillarTopZ).radiusArc((bottomPillarPos[0] - bottomPillarR, pillarTopZ), chainWheelR).close().extrude(self.plateDistance)
                # plate = plate.workplaneFromTagged("base").moveTo(bottomPillarPos[0] - bottomPillarR, bottomPillarPos[1]).lineTo(bottomPillarPos[0] + bottomPillarR, bottomPillarPos[1]). \
                #     lineTo(bottomPillarPos[0] + bottomPillarR, pillarTopZ).lineTo(bottomPillarPos[0] - bottomPillarR, -chainWheelR * 10).close().extrude(self.getPlateThick(back))
            else:
                try:
                    plate = plate.workplaneFromTagged("top").moveTo(bottomPillarPos[0], bottomPillarPos[1]).circle(bottomPillarR).extrude(self.plateDistance)
                except:
                    plate = plate.workplaneFromTagged("base").moveTo(bottomPillarPos[0], bottomPillarPos[1]).circle(bottomPillarR+0.01).extrude(self.plateDistance+self.getPlateThick(back=True))

            if self.extraHeavy:
                sagitta = topPillarR*0.25
                plate = plate.workplaneFromTagged("base").moveTo(topPillarPos[0] - topPillarR, topPillarPos[1]).radiusArc((topPillarPos[0] + topPillarR, topPillarPos[1]), topPillarR).lineTo(topPillarPos[0] + topPillarR, topPillarPos[1]-topPillarR - sagitta).\
                    sagittaArc((topPillarPos[0] - topPillarR, topPillarPos[1]-topPillarR-sagitta), -sagitta).close().extrude(self.plateDistance+self.getPlateThick(back=True))
            else:
                # try:
                #     plate = plate.workplaneFromTagged("top").moveTo(topPillarPos[0], topPillarPos[1]).circle(topPillarR).extrude(self.plateDistance)
                # except:
                plate = plate.workplaneFromTagged("base").moveTo(topPillarPos[0], topPillarPos[1]).circle(topPillarR).extrude(self.plateDistance+self.getPlateThick(back=True))

            textMultiMaterial = cq.Workplane("XY")
            textSize = topPillarR * 0.9
            textY = (self.bearingPositions[0][1] + fixingPositions[2][1])/2
            plate, textMultiMaterial = self.addText(plate, textMultiMaterial, "{} {:.1f}".format(self.name, self.goingTrain.pendulum_length * 100), (-textSize*0.4, textY), textSize)

            plate, textMultiMaterial = self.addText(plate, textMultiMaterial, "{}".format(datetime.date.today().strftime('%Y-%m-%d')), (textSize*0.6, textY), textSize)

            if getText:
                return textMultiMaterial

        plate = self.punchBearingHoles(plate, back)


        if back:
            chainHoles = self.getChainHoles(bottomPillarPos=bottomPillarPos, bottomPillarR=bottomPillarR)
            plate = plate.cut(chainHoles.translate((0, 0, self.getPlateThick(back=True) + self.endshake / 2)))
        else:
           plate = self.frontAdditionsToPlate(plate)

        fixingScrewD = 3

        #screws to fix the plates together
        # plate = plate.faces(">Z").workplane().pushPoints(fixingPositions).circle(fixingScrewD / 2).cutThruAll()



        for fixingPos in fixingPositions:

            if back:
                #embedded nuts!
                #extra thick layer because plates are huge and usually printed with 0.3 layer height
                plate = plate.cut(getHoleWithHole(fixingScrewD,getNutContainingDiameter(fixingScrewD,NUT_WIGGLE_ROOM), getNutHeight(fixingScrewD)*1.4, sides=6, layerThick=LAYER_THICK_EXTRATHICK).translate((fixingPos[0], fixingPos[1], self.embeddedNutHeight)))

                plate = plate.cut(self.fixingScrews.getCutter(length=10000).rotate((0,0,0),(1,0,0), 180).translate(fixingPos).translate((0, 0, self.getPlateThick(back=True) + self.plateDistance + self.getPlateThick(back=False))))
            else:
                #front
                plate = plate.cut(self.fixingScrews.getCutter(length=10000).rotate((0,0,0),(1,0,0), 180).translate(fixingPos).translate((0,0,self.getPlateThick(back=False))))

        return plate

    def getChainHoles(self, bottomPillarPos, bottomPillarR):
        '''
        These chain holes are relative to the front of the back plate - they do NOT take plate thickness or wobble into account

        bottomPillarPos needed for screw for pulley cord
        '''

        holePositions = self.goingTrain.poweredWheel.getChainPositionsFromTop()
        topZ = self.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness()

        chainHoles = cq.Workplane("XZ")

        for holePosition in holePositions:
            if len(holePosition) > 1:
                #elongated hole

                chainZTop = topZ + holePosition[0][1] + self.endshake / 2
                chainZBottom = topZ + holePosition[1][1] - self.endshake / 2
                #assuming we're only ever elongated along the z axis
                chainX = holePosition[0][0]

                # chainHole = cq.Workplane("XZ").moveTo(chainX - self.chainHoleD / 2, chainZTop - self.chainHoleD / 2).radiusArc((chainX + self.chainHoleD / 2, chainZTop - self.chainHoleD / 2), self.chainHoleD / 2) \
                #     .lineTo(chainX + self.chainHoleD / 2, chainZBottom + self.chainHoleD / 2).radiusArc((chainX - self.chainHoleD / 2, chainZBottom + self.chainHoleD / 2), self.chainHoleD / 2).close() \
                #     .extrude(1000)
                chainHole = cq.Workplane("XZ").moveTo(chainX, (chainZTop + chainZBottom)/2).rect(self.chainHoleD, abs(chainZTop - chainZBottom) ).extrude(1000)
                chainHoles.add(chainHole)
            else:
                chainHole = cq.Workplane("XZ").moveTo(holePosition[0][0], holePosition[0][1] + topZ).circle(self.chainHoleD / 2).extrude(1000)
                chainHoles.add(chainHole)

        if self.usingPulley:
            chainX = holePositions[0][0][0]
            chainZTop = topZ + holePositions[0][0][1]
            pulleyX = -chainX
            # might want it as far back as possible?
            # for now, as far FORWARDS as possible, because the 4kg weight is really wide!
            pulleyZ = chainZTop - self.chainHoleD / 2  # chainZBottom + self.chainHoleD/2#(chainZTop + chainZBottom)/2
            # and one hole for the cord to be tied
            pulleyHole = cq.Workplane("XZ").moveTo(pulleyX, pulleyZ).circle(self.chainHoleD / 2).extrude(1000)
            chainHoles.add(pulleyHole)
            # print("chainZ min:", chainZBottom, "chainZ max:", chainZTop)

            # original plan was a screw in from the side, but I think this won't be particularly strong as it's in line with the layers
            # so instead, put a screw in from the front
            pulleyY =  bottomPillarPos[1]+bottomPillarR/2
            # this screw will provide something for the cord to be tied round
            pulleyScrewHole = cq.Workplane("XY").moveTo(pulleyX, pulleyY).circle(self.fixingScrewsD / 2).extrude(10000)
            coneHeight = getScrewHeadHeight(self.fixingScrewsD, countersunk=True) + COUNTERSUNK_HEAD_WIGGLE
            topR = getScrewHeadDiameter(self.fixingScrewsD, countersunk=True) / 2 + COUNTERSUNK_HEAD_WIGGLE
            topZ = self.plateDistance
            pulleyScrewHole = pulleyScrewHole.add(cq.Solid.makeCone(radius2=topR, radius1=self.fixingScrewsD / 2, height=coneHeight).translate((pulleyX, pulleyY, topZ - coneHeight)))
            chainHoles.add(pulleyScrewHole)
        return chainHoles

    def getBearingHolder(self, height, addSupport=True, bearingInfo=None):
        #height from base (outside) of plate, so this is inclusive of base thickness, not in addition to
        if bearingInfo is None:
            bearingInfo = getBearingInfo(self.arbourD)
        wallThick = self.bearingWallThick
        diameter = bearingInfo.bearingOuterD + wallThick*2
        holder = cq.Workplane("XY").circle(diameter/2).circle(bearingInfo.innerD/2 + bearingInfo.bearingHolderLip).extrude(height - bearingInfo.bearingHeight)


        holder = holder.faces(">Z").workplane().circle(diameter/2).circle(bearingInfo.bearingOuterD/2).extrude(bearingInfo.bearingHeight)
        # extra support?
        if addSupport:
            support = cq.Workplane("YZ").moveTo(-bearingInfo.bearingOuterD/2,0).lineTo(-height-bearingInfo.bearingOuterD/2,0).lineTo(-bearingInfo.bearingOuterD/2,height).close().extrude(wallThick).translate([-wallThick/2,0,0])
            holder = holder.add(support)

        return holder

    def getBearingPunch(self, bearingOnTop=True, bearingInfo=None, back=True):
        '''
        A shape that can be cut out of a clock plate to hold a bearing
        '''
        if bearingInfo is None:
            bearingInfo = getBearingInfo(self.arbourD)

        height = self.getPlateThick(back)

        if bearingOnTop:
            punch = cq.Workplane("XY").circle(bearingInfo.innerD/2 + bearingInfo.bearingHolderLip).extrude(height - bearingInfo.bearingHeight)
            punch = punch.faces(">Z").workplane().circle(bearingInfo.bearingOuterD/2).extrude(bearingInfo.bearingHeight)
        else:
            punch = getHoleWithHole(bearingInfo.innerD + bearingInfo.bearingHolderLip*2,bearingInfo.bearingOuterD, bearingInfo.bearingHeight, layerThick=LAYER_THICK_EXTRATHICK).faces(">Z").workplane().circle(bearingInfo.innerD/2 + bearingInfo.bearingHolderLip).extrude(height - bearingInfo.bearingHeight)

        return punch

    def punchBearingHoles(self, plate, back):
        for i, pos in enumerate(self.bearingPositions):
            bearingInfo = getBearingInfo(self.goingTrain.getArbourWithConventionalNaming(i).getRodD())

            if self.pendulumFixing == PendulumFixing.DIRECT_ARBOUR and back == False and i == len(self.bearingPositions)-1:
                #this is the front (TODO configurable) bearing for the anchor and the pendulum is using a direct arbour (which extends through a large bearing in the front plate)
                bearingInfo = self.pendulumFixingBearing


            plate = plate.cut(self.getBearingPunch(back, bearingInfo=bearingInfo, back=back).translate((pos[0], pos[1], 0)))
        return plate

    def addScrewHole(self, plate, screwholePos, screwHeadD = 9, screwBodyD = 6, slotLength = 7, backThick = -1, addExtraSupport=False):
        '''
        screwholePos is the position the clock will hang from
        this is an upside-down-lollypop shape

        if backThick is default, this cuts through the whole plate
        if not, backthick is the thickness of the plastic around the screw


          /-\   circle of screwBodyD diameter (centre of the circle is the screwholePos)
          |  |  screwbodyD wide
          |  |  distance between teh two circle centres is screwholeHeight
        /     \
        |     |  circle of screwHeadD diameter
        \_____/
        '''

        if addExtraSupport:
            #a circle around the big hole to strengthen the plate
            #assumes plate has been tagged
            extraSupportSize = screwHeadD*1.25
            supportCentre=[screwholePos[0], screwholePos[1]- slotLength]

            if self.heavy:
                extraSupportSize*=1.5
                supportCentre[1] += slotLength / 2
                #bodge if the screwhole is off to one side
                if screwholePos[0] != 0:
                    #this can be a bit finnickity - I think if something lines up exactly wrong with the bearing holes?
                    supportCentre[0] += (-1 if screwholePos[0] > 0 else 1) * extraSupportSize*0.5
            #
            plate = plate.workplaneFromTagged("base").moveTo(supportCentre[0], supportCentre[1] ).circle(extraSupportSize).extrude(self.getPlateThick(back=True))

        #big hole
        plate = plate.faces(">Z").workplane().tag("top").moveTo(screwholePos[0], screwholePos[1] - slotLength).circle(screwHeadD / 2).cutThruAll()
        #slot
        plate = plate.workplaneFromTagged("top").moveTo(screwholePos[0], screwholePos[1] - slotLength/2).rect(screwBodyD, slotLength).cutThruAll()
        # small hole
        plate = plate.workplaneFromTagged("top").moveTo(screwholePos[0], screwholePos[1]).circle(screwBodyD / 2).cutThruAll()

        if backThick > 0:
            extraY = screwBodyD*0.5
            cutter = cq.Workplane("XY").moveTo(screwholePos[0], screwholePos[1] + extraY).circle(screwHeadD/2).extrude(self.getPlateThick(back=True) - backThick).translate((0,0,backThick))
            cutter = cutter.add(cq.Workplane("XY").moveTo(screwholePos[0], screwholePos[1] - slotLength / 2 + extraY/2).rect(screwHeadD, slotLength+extraY).extrude(self.getPlateThick(back=True) - backThick).translate((0, 0, backThick)))
            plate = plate.cut(cutter)

        return plate

    def addText(self,plate, multimaterial, text, pos, textSize):
        # textSize =  width*0.25
        # textYOffset = width*0.025
        y = pos[1]
        textYOffset = 0  + pos[0]# width*0.1
        text = cq.Workplane("XY").moveTo(0, 0).text(text, textSize, LAYER_THICK, cut=False, halign='center', valign='center', kind="bold").rotateAboutCenter((0, 0, 1), 90).rotateAboutCenter((1, 0, 0), 180).translate((textYOffset, y, 0))

        return plate.cut(text), multimaterial.add(text)

    def frontAdditionsToPlate(self, plate):
        '''
        stuff shared between all plate designs
        '''
        plateThick = self.getPlateThick(back=False)
        # FRONT

        # note - works fine with the pendulum on the same rod as teh anchor, but I'm not sure about the long term use of ball bearings for just rocking back and forth
        # suspensionBaseThick=0.5
        # suspensionPoint = self.pendulum.getSuspension(False,suspensionBaseThick ).translate((self.bearingPositions[len(self.bearingPositions)-1][0], self.bearingPositions[len(self.bearingPositions)-1][1], plateThick-suspensionBaseThick))
        #         #
        #         # plate = plate.add(suspensionPoint)
        # new plan: just put the pendulum on the same rod as the anchor, and use nyloc nuts to keep both firmly on the rod.
        # no idea if it'll work without the rod bending!

        if self.pendulumAtFront and self.pendulumSticksOut > 0 and self.pendulumFixing == PendulumFixing.FRICTION_ROD:
            #a cylinder that sticks out the front and holds a bearing on the end
            extraBearingHolder = self.getBearingHolder(self.pendulumSticksOut, False).translate((self.bearingPositions[len(self.bearingPositions) - 1][0], self.bearingPositions[len(self.bearingPositions) - 1][1], plateThick))
            plate = plate.add(extraBearingHolder)




        motionWorksPos = (self.bearingPositions[self.goingTrain.chainWheels][0] + self.motionWorksRelativePos[0], self.bearingPositions[self.goingTrain.chainWheels][1] + self.motionWorksRelativePos[1])

        #hole for screw to hold motion works arbour
        plate = plate.cut(self.fixingScrews.getCutter().translate(motionWorksPos))

        #embedded nut on the front so we can tighten this screw in
        nutDeep =  self.fixingScrews.getNutHeight(half=True)
        nutSpace = self.fixingScrews.getNutCutter(half=True).translate(motionWorksPos).translate((0,0,self.getPlateThick(back=False) - nutDeep))

        plate = plate.cut(nutSpace)

        if self.dial is not None:
            dialFixings = self.dial.getFixingDistance()
            minuteY = self.bearingPositions[self.goingTrain.chainWheels][1]
            plate = plate.faces(">Z").workplane().pushPoints([(0, minuteY + dialFixings / 2), (0, minuteY - dialFixings / 2)]).circle(self.dial.fixingD / 2).cutThruAll()

        # need an extra chunky hole for the big bearing that the key slots through
        if self.goingTrain.poweredWheel.type == PowerType.CORD and self.goingTrain.poweredWheel.useKey:
            cordWheel = self.goingTrain.poweredWheel
            # cordBearingHole = cq.Workplane("XY").circle(cordWheel.bearingOuterD/2).extrude(cordWheel.bearingHeight)
            cordBearingHole = getHoleWithHole(cordWheel.bearing.innerD + cordWheel.bearing.bearingHolderLip * 2, cordWheel.bearing.bearingOuterD, cordWheel.bearing.bearingHeight ,layerThick=LAYER_THICK_EXTRATHICK)
            cordBearingHole = cordBearingHole.faces(">Z").workplane().circle(cordWheel.bearing.innerD/2 + cordWheel.bearing.bearingHolderLip).extrude(plateThick)

            plate = plate.cut(cordBearingHole.translate((self.bearingPositions[0][0], self.bearingPositions[0][1],0)))

        return plate

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_front_plate.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getPlate(False), out)

        out = os.path.join(path, "{}_back_plate_platecolour.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getPlate(True), out)
        out = os.path.join(path, "{}_back_plate_textcolour.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getPlate(True, True), out)

        if len(self.getScrewHolePositions()) > 1:
            #need a template to help drill the screwholes!
            out = os.path.join(path, "{}_drill_template_7mm.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.getDrillTemplate(7), out)

        # for arbour in range(self.goingTrain.wheels + self.goingTrain.chainWheels + 1):
        #     for top in [True, False]:
        #         extensionShape=self.getArbourExtension(arbour, top=top)
        #         if extensionShape is not None:
        #             out = os.path.join(path, "{}_arbour_{}_{}_extension.stl".format(name, arbour, "top" if top else "bottom"))
        #             print("Outputting ", out)
        #             exporters.export(extensionShape, out)



class Dial:
    '''
    WIP
    '''
    def __init__(self, outsideD, hollow=True, style="simple", fixingD=3, supportLength=0):
        self.outsideD=outsideD
        self.hollow = hollow
        self.style = style
        self.fixingD=fixingD
        self.supportLength=supportLength
        self.thick = 3

    def getFixingDistance(self):
        return self.outsideD - self.fixingD*4

    def getDial(self):
        r = self.outsideD / 2

        bigLineThick=3
        smallLineThick=1

        bigAngle = math.asin((bigLineThick/2)/r)*2
        smallAngle = math.asin((smallLineThick / 2) / r) * 2

        lineThick = LAYER_THICK*2

        innerR = r*0.8

        dial = cq.Workplane("XY").circle(r).circle(innerR).extrude(self.thick)

        dial = dial.faces(">Z").workplane().tag("top")

        lines = 60

        dA = math.pi*2/lines

        fromEdge = self.outsideD*0.01

        lineInnerR = innerR + fromEdge
        lineOuterR = r - fromEdge

        for i in range(lines):
            big = i % 5 == 0
            # big=True
            lineAngle = bigAngle if big else smallAngle
            angle = math.pi/2 - i*dA

            # if not big:
            #     continue

            bottomLeft=polar(angle - lineAngle/2, lineInnerR)
            bottomRight=polar(angle + lineAngle/2, lineInnerR)
            topRight=polar(angle + lineAngle/2, lineOuterR)
            topLeft=polar(angle - lineAngle / 2, lineOuterR)
            #keep forgetting cq does not line shapes that line up perfectly, so have a 0.001 bodge... again
            dial = dial.workplaneFromTagged("top").moveTo(bottomLeft[0], bottomLeft[1]).radiusArc(bottomRight, 0.001-innerR).lineTo(topRight[0], topRight[1]).radiusArc(topLeft, r-0.001).close().extrude(lineThick)
            # dial = dial.workplaneFromTagged("top").moveTo(bottomLeft[0], bottomLeft[1]).lineTo(bottomRight[0], bottomRight[1]).lineTo(topRight[0], topRight[1]).lineTo(topLeft[0], topLeft[1]).close().extrude(lineThick)

        return dial

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}_dial.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getDial(), out)

class Assembly:
    '''
    Produce a fully (or near fully) assembled clock
    likely to be fragile as it will need to delve into the detail of basically everything

    currently assumes pendulum and chain wheels are at front - doesn't listen to their values
    '''
    def __init__(self, plates, hands=None, dial=None, timeMins=10, timeHours=10, timeSeconds=0, pulley=None, showPendulum=False, weights=None):
        self.plates = plates
        self.hands = hands
        self.dial=dial
        self.goingTrain = plates.goingTrain
        self.arbourCount = self.goingTrain.chainWheels + self.goingTrain.wheels
        self.pendulum = self.plates.pendulum
        self.motionWorks = self.plates.motionWorks
        self.timeMins = timeMins
        self.timeHours = timeHours
        self.timeSeconds = timeSeconds
        self.pulley=pulley
        self.showPendulum=showPendulum
        #weights is a list of weights, first in the list is the main weight and second is the counterweight (if needed)
        self.weights=weights
        if self.weights is None:
            self.weights = []

    def printInfo(self):

        for holeInfo in self.goingTrain.poweredWheel.getChainPositionsFromTop():
            #TODO improve this a bit for cordwheels which have a slot rather than just a hole
            z = self.plates.bearingPositions[0][2] + self.plates.getPlateThick(back=True) + self.goingTrain.poweredWheel.getHeight() + self.plates.endshake/2 + holeInfo[0][1]
            print("{} hole from wall = {}mm".format(self.goingTrain.poweredWheel.type.value, z))

    def getClock(self):
        bottomPlate = self.plates.getPlate(True)
        topPlate  = self.plates.getPlate(False)

        clock = bottomPlate.add(topPlate.translate((0,0,self.plates.plateDistance + self.plates.getPlateThick(back=True))))

        #the wheels
        for a in range(self.goingTrain.wheels + self.goingTrain.chainWheels + 1):
            arbour = self.goingTrain.getArbourWithConventionalNaming(a)
            clock = clock.add(arbour.getAssembled().translate(self.plates.bearingPositions[a]).translate((0,0,self.plates.getPlateThick(back=True) + self.plates.endshake/2)))



        # anchorAngle = math.atan2(self.plates.bearingPositions[-1][1] - self.plates.bearingPositions[-2][1], self.plates.bearingPositions[-1][0] - self.plates.bearingPositions[-2][0]) - math.pi/2
        #
        # #the anchor is upside down for better printing, so flip it back
        # anchor = self.pendulum.anchor#.mirror("YZ", (0,0,0))
        # #and rotate it into position
        # anchor = anchor.rotate((0,0,0),(0,0,1), radToDeg(anchorAngle)).translate(self.plates.bearingPositions[-1]).translate((0,0,self.plates.getPlateThick(back=True) + self.plates.wobble/2))
        # clock = clock.add(anchor)

        #where the nylock nut and spring washer would be (6mm = two half size m3 nuts and a spring washer + some slack)
        motionWorksZOffset = 6

        time_min = self.timeMins
        time_hour = self.timeHours


        minuteAngle = - 360 * (time_min / 60)
        hourAngle = - 360 * (time_hour + time_min / 60) / 12
        secondAngle = -360 * (self.timeSeconds / 60)

        motionWorksModel = self.motionWorks.getAssembled(motionWorksRelativePos=self.plates.motionWorksRelativePos,minuteAngle=minuteAngle)

        clock = clock.add(motionWorksModel.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1], self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance + motionWorksZOffset)))



        #hands on the motion work, showing the time
        #mirror them so the outline is visible (consistent with second hand)
        minuteHand = self.hands.getHand(minute=True).mirror().translate((0,0,self.hands.thick)).rotate((0,0,0),(0,0,1), minuteAngle)
        hourHand = self.hands.getHand(hour=True).mirror().translate((0,0,self.hands.thick)).rotate((0, 0, 0), (0, 0, 1), hourAngle)


        minuteHandZ = self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance + motionWorksZOffset\
                      + self.motionWorks.minuteHolderTotalHeight - self.hands.thick

        clock = clock.add(minuteHand.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1], minuteHandZ)))

        clock = clock.add(hourHand.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1],
                                              minuteHandZ - self.motionWorks.hourHandSlotHeight - self.motionWorks.space)))

        if self.goingTrain.escapement_time == 60:
            #second hand!! yay
            secondHand = self.hands.getHand(second=True).mirror().translate((0,0,self.hands.thick)).rotate((0, 0, 0), (0, 0, 1), secondAngle)
            clock = clock.add(secondHand.translate((self.plates.bearingPositions[-2][0], self.plates.bearingPositions[-2][1], self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance+self.hands.secondFixing_thick )))


        pendulumRodExtraZ = 2

        pendulumRodFixing = self.pendulum.getPendulumForRod().mirror().translate((0,0,self.pendulum.pendulumTopThick))

        pendulumHolderBaseZ = self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance + self.plates.pendulumSticksOut + pendulumRodExtraZ



        clock = clock.add(pendulumRodFixing.translate((self.plates.bearingPositions[-1][0], self.plates.bearingPositions[-1][1], pendulumHolderBaseZ)))

        pendulumRodCentreZ = pendulumHolderBaseZ + self.pendulum.pendulumTopThick / 2
        pendulumBobBaseZ = pendulumRodCentreZ - self.pendulum.bobThick / 2
        pendulumBobCentreY = self.plates.bearingPositions[-1][1] - self.goingTrain.pendulum_length * 1000

        if self.showPendulum:


            clock = clock.add(self.pendulum.getBob(hollow=False).rotate((0,0,self.pendulum.bobThick / 2),(0,1,self.pendulum.bobThick / 2),180).translate((self.plates.bearingPositions[-1][0], pendulumBobCentreY, pendulumBobBaseZ)))

            clock = clock.add(self.pendulum.getBobNut().translate((0,0,-self.pendulum.bobNutThick/2)).rotate((0,0,0), (1,0,0),90).translate((self.plates.bearingPositions[-1][0], pendulumBobCentreY, pendulumBobBaseZ + self.pendulum.bobThick/2)))


        if len(self.weights) > 0:
            for i, weight in enumerate(self.weights):
                #line them up so I can see if they'll bump into each other
                weightTopY = pendulumBobCentreY

                holePositions = self.goingTrain.poweredWheel.getChainPositionsFromTop()

                #side the main weight is on
                side = 1 if self.goingTrain.isWeightOnTheRight() else -1

                if i == 1:
                    #counterweight
                    side*=-1

                #in X,Y,Z
                weightPos = None

                for holeInfo in holePositions:
                    if (holeInfo[0][0] > 0) == (side > 0):
                        #hole for the weight
                        weightPos = (holeInfo[0][0], weightTopY - weight.height, self.plates.bearingPositions[0][2] + self.plates.getPlateThick(back=True) + self.goingTrain.poweredWheel.getHeight() + holeInfo[0][1])

                if weightPos is not None:
                    weightShape = weight.getWeight().rotate((0,0,0), (1,0,0),-90)

                    clock = clock.add(weightShape.translate(weightPos))



        minuteToPendulum = (self.plates.bearingPositions[-1][0] - self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[-1][1] - self.plates.bearingPositions[self.goingTrain.chainWheels][1])

        if abs(minuteToPendulum[0]) < 50:
            #centre around the hands by default
            ringY = self.plates.bearingPositions[self.goingTrain.chainWheels][1]
            if self.goingTrain.poweredWheel.type == PowerType.CORD and self.goingTrain.poweredWheel.useKey:
                #centre between the hands and the winding key
                ringY =  (self.plates.bearingPositions[self.goingTrain.chainWheels][1] + self.plates.bearingPositions[0][1])/2

            ring = self.pendulum.getHandAvoider()
            handAvoiderExtraZ = (self.pendulum.pendulumTopThick - self.pendulum.handAvoiderThick)/2
            #ring is over the minute wheel/hands
            clock = clock.add(ring.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], ringY, self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance + self.plates.pendulumSticksOut + pendulumRodExtraZ + handAvoiderExtraZ)))

        if self.pulley is not None:
            #HACK HACK HACK, just copy pasted from teh chainHoles in plates, assumes cord wheel with key
            chainZ = self.plates.getPlateThick(back=True) + self.plates.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness() - WASHER_THICK - self.goingTrain.poweredWheel.capThick - self.goingTrain.poweredWheel.thick + self.plates.endshake / 2
            # print("chain Z", chainZ)
            clock = clock.add(self.pulley.getAssembled().rotate((0,0,0),(0,0,1),90).translate((0,self.plates.bearingPositions[0][1] - 120, chainZ - self.pulley.getTotalThick()/2)))

        #TODO pendulum bob and nut?

        #TODO weight?

        return clock

    def getSpanner(self, size, length=180):
        '''

        '''

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getClock(), out)


def getHandDemo(justStyle=None, length = 120, perRow=3, assembled=False, time_min=10, time_hour=10, time_sec=0, chunky=False):
    demo = cq.Workplane("XY")

    motionWorks = MotionWorks(minuteHandHolderHeight=30 + 30, style=GearStyle.ARCS, thick=2, compensateLooseArbour=True)

    space = length

    if assembled:
        space = length*2

    for i,style in enumerate(HandStyle):

        if justStyle is not None and style != justStyle:
            continue

        hands = Hands(style=style, chunky=chunky, minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize + 0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=length, thick=motionWorks.minuteHandSlotHeight, outline=1,
                      outlineSameAsBody=False, secondLength=25)

        x = space*(i%perRow)

        y = (space)*math.floor(i/perRow)

        secondsHand = None
        try:
            secondsHand =hands.getHand(second=True)
        except:
            print("Unable to generate second hand for {}".format(style.value))

        if assembled:
            #showing a time
            minuteAngle = - 360 * (time_min / 60)
            hourAngle = - 360 * (time_hour + time_min / 60) / 12
            secondAngle = -360 * (time_sec / 60)

            # hands on the motion work, showing the time
            # mirror them so the outline is visible (consistent with second hand)
            minuteHand = hands.getHand(minute=True).rotate((0, 0, 0), (0, 0, 1), minuteAngle)
            hourHand = hands.getHand(hour=True).rotate((0, 0, 0), (0, 0, 1), hourAngle)

            demo = demo.add(minuteHand.translate((x, y, hands.thick)))
            demo = demo.add(hourHand.translate((x, y, 0)))

            if secondsHand is not None:
                demo = demo.add(secondsHand.translate((x, y + length * 0.3)))

        else:
            demo = demo.add(hands.getHand(hour=True).translate((x, y)))
            demo = demo.add(hands.getHand(minute=True).translate((x+length*0.3, y)))
            if secondsHand is not None:
                demo = demo.add(secondsHand.translate((x - length * 0.3, y)))


    return demo

def getGearDemo(module=1, justStyle=None):
    demo = cq.Workplane("XY")

    train = GoingTrain(pendulum_period=2, fourth_wheel=False, maxWeightDrop=1200, usePulley=True, chainAtBack=False, chainWheels=1, hours=7.5 * 24)

    moduleReduction = 0.9

    train.calculateRatios(max_wheel_teeth=130, min_pinion_teeth=9, wheel_min_teeth=60, pinion_max_teeth=15, max_error=0.1, moduleReduction=moduleReduction)
    # train.setChainWheelRatio([93, 10])

    train.genCordWheels(ratchetThick=4, rodMetricThread=4, cordThick=1.5, cordCoilThick=14, style=None, useKey=True, preferedDiameter=25)
    # override default until it calculates an ideally sized wheel
    train.calculatePoweredWheelRatios(wheel_max=100)

    train.genGears(module_size=module, moduleReduction=moduleReduction, thick=2.4, thicknessReduction=0.9, chainWheelThick=4, useNyloc=False, pinionThickMultiplier=3, style=None, chainModuleIncrease=1, chainWheelPinionThickMultiplier=2,
                   ratchetInset=False)

    motionWorks = MotionWorks(minuteHandHolderHeight=30 + 30, style=GearStyle.ARCS, thick=2, compensateLooseArbour=True)

    demoArboursNums = [0, 1, 3]

    #get a chain wheel, a normal wheel, an escape wheel and part of the motion works for a good spread of sizes and inner radii
    demoArbours = [train.getArbourWithConventionalNaming(i) for i in demoArboursNums]
    demoArbours.append(motionWorks.getMotionArbour())

    gap = 5
    space = max([arbour.getMaxRadius()*2 for arbour in demoArbours]) + gap

    x=0

    for i,style in enumerate(GearStyle):
        if justStyle is not None and style != justStyle:
            continue
        print(style.value)

        y=0
        for arbour in demoArbours:
            arbour.style = style
            y += arbour.getMaxRadius() + gap
            demo = demo.add(arbour.getShape().translate((x,y,0)))
            y += arbour.getMaxRadius()

        x += space

    return demo