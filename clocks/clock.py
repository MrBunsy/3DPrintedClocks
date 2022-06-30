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
    gravity = 9.81
    def __init__(self, pendulum_period=1, fourth_wheel=False, escapement_teeth=30, chainWheels=0, hours=30,chainAtBack=True, maxChainDrop=1800, max_chain_wheel_d=23, escapement=None, escapeWheelPinionAtFront=None):
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
        self.pendulum_length = self.gravity * pendulum_period * pendulum_period / (4 * math.pi * math.pi)

        self.chainAtBack = chainAtBack
        #to ensure the anchor isn't pressed up against the back (or front) plate
        if escapeWheelPinionAtFront is None:
            self.escapeWheelPinionAtFront = chainAtBack
        else:
            self.escapeWheelPinionAtFront=escapeWheelPinionAtFront

        #if zero, the minute hand is directly driven by the chain, otherwise, how many gears from minute hand to chain wheel
        self.chainWheels = chainWheels
        self.hours = hours
        self.max_chain_wheel_d = max_chain_wheel_d
        self.maxChainDrop = maxChainDrop

        #calculate ratios from minute hand to escapement
        #the last wheel is the escapement
        self.wheels = 4 if fourth_wheel else 3

        #maybe make this overridable in genGears?
        self.anchorThick = 12

        self.escapement=escapement
        if escapement is None:
            self.escapement = Escapement(teeth=escapement_teeth)
        #
        self.escapement_time = pendulum_period * self.escapement.teeth
        # self.escapement_teeth = escapement_teeth
        # self.escapement_lift = 4
        # self.escapement_drop = 2
        # self.escapement_lock = 2
        # self.escapement_type = "deadbeat"

        # self.min_pinion_teeth=min_pinion_teeth
        # self.max_wheel_teeth=max_wheel_teeth
        # self.pinion_max_teeth = pinion_max_teeth
        # self.wheel_min_teeth = wheel_min_teeth
        self.trains=[]

    # def setEscapementDetails(self, lift = None, drop = None, lock=None, type=None):
    #     if lift is not None:
    #         self.lift = lift
    #     if drop is not None:
    #         self.drop = drop
    #     if lock is not None:
    #         self.lock = lock
    #     if type is not None:
    #         self.type = type

    def calculateRatios(self,moduleReduction=0.85, min_pinion_teeth=10, max_wheel_teeth=100, pinion_max_teeth = 20, wheel_min_teeth = 50, max_error=0.1, loud=False):
        '''
        Returns and stores a list of possible gear ratios, sorted in order of "best" to worst
        module recution used to caculate smallest possible wheels - assumes each wheel has a smaller module than the last
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
        print(allTimes)

        self.trains = allTimes

        if len(allTimes) == 0:
            raise RuntimeError("Unable to calculate valid going train")

        return allTimes

    def setRatios(self, gearPinionPairs):
        #keep in the format of the autoformat
        time={'train': gearPinionPairs}

        self.trains = [time]

    def calculateChainWheelRatios(self):
        if self.chainWheels == 0:
            '''
            nothing to do
            '''
        elif self.chainWheels == 1:
            chainWheelCircumference = self.max_chain_wheel_d * math.pi

            # get the actual circumference (calculated from the length of chain segments)
            if self.usingChain:
                chainWheelCircumference = self.chainWheel.circumference
            else:
                chainWheelCircumference = self.cordWheel.diameter*math.pi

            turns = self.poweredWheel.getTurnsForDrop(self.maxChainDrop)

            # find the ratio we need from the chain wheel to the minute wheel
            turnsPerHour = turns / self.hours

            desiredRatio = 1 / turnsPerHour

            print("Chain wheel turns per hour", turnsPerHour)
            print("Chain wheel ratio to minute wheel", desiredRatio)

            allGearPairCombos = []

            pinion_min = 10
            pinion_max = 20
            wheel_min = 20
            wheel_max = 120

            for p in range(pinion_min, pinion_max):
                for w in range(wheel_min, wheel_max):
                    allGearPairCombos.append([w, p])
            print("ChainWheel: allGearPairCombos", len(allGearPairCombos))

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

            print(allRatios)

            self.chainWheelRatio = allRatios[0]["pair"]
        else:
            raise ValueError("Unsupported number of chain wheels")

    def setChainWheelRatio(self, pinionPair):
        self.chainWheelRatio = pinionPair

    def isWeightOnTheRight(self):
        '''
        returns true if the weight dangles from the right side of the chain wheel (as seen from the front)
        '''

        clockwise = self.ratchet.isClockwise()
        chainAtFront = not self.chainAtBack

        #XNOR
        clockwiseFromFront = not (clockwise != chainAtFront)

        return clockwiseFromFront

    def genPowerWheelRatchet(self, ratchetThick=7.5):
        '''
        The ratchet and bits shared between chain and cord wheels
        '''
        if self.chainWheels == 0:
            self.chainWheelCircumference = self.maxChainDrop/self.hours
            self.max_chain_wheel_d = self.chainWheelCircumference/math.pi

        elif self.chainWheels == 1:
            self.chainWheelCircumference = self.max_chain_wheel_d * math.pi
            #use provided max_chain_wheel_d and calculate the rest

        # true for no chainwheels
        anticlockwise = self.chainAtBack

        for i in range(self.chainWheels):
            anticlockwise = not anticlockwise

        self.poweredWheelAnticlockwise = anticlockwise

    def genChainWheels(self, ratchetThick=7.5, holeD=3.3, wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15,screwThreadLength=10):
        '''
        HoleD of 3.5 is nice and loose, but I think it's contributing to making the chain wheel wonky - the weight is pulling it over a bit
        Trying 3.3, wondering if I'm going to want to go back to the idea of a brass tube in the middle

        Generate the gear ratios for the wheels between chain and minute wheel
        again, I'd like to make this generic but the solution isn't immediately obvious and it would take
        longer to make it generic than just make it work
        '''

        self.genPowerWheelRatchet()


        self.chainWheel = ChainWheel(max_circumference=self.chainWheelCircumference, wire_thick=wire_thick, inside_length=inside_length, width=width, holeD=holeD, tolerance=tolerance, screwThreadLength=screwThreadLength)
        self.poweredWheel=self.chainWheel


        self.ratchet = Ratchet(totalD=self.max_chain_wheel_d * 2, innerRadius=self.chainWheel.outerDiameter / 2, thick=ratchetThick, powerAntiClockwise=self.poweredWheelAnticlockwise)

        self.chainWheel.setRatchet(self.ratchet)

        self.usingChain=True

    def genCordWheels(self,ratchetThick=7.5, rodMetricThread=3, cordCoilThick=10, useKey=False, cordThick=2, style="HAC", useFriction=False ):

        self.genPowerWheelRatchet()
        #slight hack, make this a little bit bigger as this works better with the standard 1 day clock (leaves enough space for the m3 screw heads)
        #21.2 comes from a mistake on clock 07, but a happy mistake as it was a good size. keeping this for now
        #increasing since I'm now using the key would cord wheels and not sure I'll be going back to the other type any time soon
        ratchetD = max(self.max_chain_wheel_d, 26)
        # ratchetD = 21.22065907891938
        self.ratchet = Ratchet(totalD=ratchetD * 2, thick=ratchetThick, powerAntiClockwise=self.poweredWheelAnticlockwise)

        self.cordWheel = CordWheel(self.max_chain_wheel_d, self.ratchet.outsideDiameter,self.ratchet,rodMetricSize=rodMetricThread, thick=cordCoilThick, useKey=useKey, cordThick=cordThick, style=style, useFriction=useFriction)
        self.poweredWheel = self.cordWheel
        self.usingChain=False

    def setTrain(self, train):
        '''
        Set a single train as the preferred train to generate everythign else
        '''
        self.trains = [train]

    def printInfo(self):
        print(self.trains[0])

        print("pendulum length: {}m period: {}s".format(self.pendulum_length, self.pendulum_period))
        print("escapement time: {}s teeth: {}".format(self.escapement_time, self.escapement.teeth))
        # print("cicumference: {}, run time of:{:.1f}hours".format(self.circumference, self.getRunTime()))
        chainRatio = 1
        if self.chainWheels > 0:
            print(self.chainWheelRatio)
            chainRatio = self.chainWheelRatio[0]/self.chainWheelRatio[1]

        runtime = self.poweredWheel.getRunTime(chainRatio,self.maxChainDrop)

        print("runtime: {:.1f}hours over {:.1f}m. Chain wheel multiplier: {:.1f}".format(runtime, self.maxChainDrop/1000, chainRatio))


    def genGears(self, module_size=1.5, holeD=3, moduleReduction=0.5, thick=6, chainWheelThick=-1, escapeWheelThick=-1, escapeWheelMaxD=-1, useNyloc=True, chainModuleIncrease=None, pinionThickMultiplier = 2.5, style="HAC", chainWheelPinionThickMultiplier=2, ratchetInset=False, thicknessReduction=1):
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
        ratchetOuterR = self.ratchet.outsideDiameter/2
        space = firstWheelR - ratchetOuterR
        if secondWheelR < space - 3:
            #the second wheel can actually fit on the same side as the ratchet
            chainWheelImaginaryPinionAtFront = not chainWheelImaginaryPinionAtFront

        #using != as XOR, so if an odd number of wheels, it's the same as chainAtBack. If it's an even number of wheels, it's the opposite
        # escapeWheelPinionAtFront =  chainWheelImaginaryPinionAtFront != ((self.wheels + self.chainWheels) % 2 == 0)
        escapeWheelPinionAtFront = self.escapeWheelPinionAtFront

        #only true if an odd number of wheels (note this IS wheels, not with chainwheels, as the minute wheel is always clockwise)
        escapeWheelClockwise = self.wheels %2 == 1

        escapeWheelClockwiseFromPinionSide = escapeWheelPinionAtFront == escapeWheelClockwise

        pinionAtFront = chainWheelImaginaryPinionAtFront

        print("Escape wheel pinion at front: {}, clockwise (from front) {}, clockwise from pinion side: {} ".format(escapeWheelPinionAtFront, escapeWheelClockwise, escapeWheelClockwiseFromPinionSide))
        #escapment is now provided or configured in the constructor
        # self.escapement = Escapement(teeth=self.escapement_teeth, diameter=escapeWheelDiameter, type=self.escapement_type, lift=self.escapement_lift, lock=self.escapement_lock, drop=self.escapement_drop, anchorTeeth=None, clockwiseFromPinionSide=escapeWheelClockwiseFromPinionSide)
        self.escapement.setDiameter(escapeWheelDiameter)
        self.escapement.clockwiseFromPinionSide=escapeWheelClockwiseFromPinionSide
        self.escapement.escapeWheelClockwise=escapeWheelClockwise
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
            self.chainWheelArbours=[Arbour(chainWheel=self.poweredWheel, wheel = self.chainWheelPair.wheel, wheelThick=chainWheelThick, ratchet=self.ratchet, arbourD=self.poweredWheel.rodMetricSize, distanceToNextArbour=self.chainWheelPair.centre_distance, style=style, ratchetInset=ratchetInset)]
            pinionAtFront = not pinionAtFront

        for i in range(self.wheels):

            if i == 0:
                #minute wheel
                if self.chainWheels == 0:
                    #the minute wheel also has the chain with ratchet
                    arbour = Arbour(chainWheel=self.poweredWheel, wheel = pairs[i].wheel, wheelThick=chainWheelThick, ratchet=self.ratchet, arbourD=holeD, distanceToNextArbour=pairs[i].centre_distance, style=style, pinionAtFront=not self.chainAtBack, ratchetInset=ratchetInset)
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
                #Trying this to ensure that the anchor doesn't end up against the back plate (or front plate)
                pinionAtFront = self.escapeWheelPinionAtFront

                #last pinion + escape wheel, the escapment itself knows which way the wheel will turn
                arbours.append(Arbour(escapement=self.escapement, pinion=pairs[i - 1].pinion, arbourD=holeD, wheelThick=escapeWheelThick, pinionThick=arbours[-1].wheelThick * pinionThickMultiplier, endCapThick=self.gearPinionEndCapLength,
                                      distanceToNextArbour=self.escapement.anchor_centre_distance, style=style, pinionAtFront=pinionAtFront))

            pinionAtFront = not pinionAtFront

        #anchor is the last arbour
        arbours.append(Arbour(escapement=self.escapement, wheelThick=self.anchorThick, arbourD=holeD))

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

        if self.usingChain:
            self.chainWheel.outputSTLs(name, path)
        else:
            self.cordWheel.outputSTLs(name, path)

        # for i,arbour in enumerate(self.chainWheelArbours):
        #     out = os.path.join(path, "{}_chain_wheel_{}.stl".format(name, i))
        #     print("Outputting ", out)
        #     exporters.export(arbour.getShape(), out)


        out = os.path.join(path, "{}_escapement_test_rig.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.escapement.getTestRig(), out)


class ClockPlates:
    '''
    This took a while to settle - clocks before v4 will be unlikely to work anymore.
    '''
    def __init__(self, goingTrain, motionWorks, pendulum, style="vertical", arbourD=3,pendulumAtTop=True, fixingScrewsD=3, plateThick=5, backPlateThick=None, pendulumSticksOut=20, name="", dial=None, heavy=False, extraHeavy=False, motionWorksAbove=False, usingPulley=False):
        '''
        Idea: provide the train and the angles desired between the arbours, try and generate the rest
        No idea if it will work nicely!
        '''

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

        self.fixingScrewsD = fixingScrewsD

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
        #maximum dimention of the bearing
        # self.bearingOuterD=bearingOuterD
        #how chunky to make the bearing holders
        self.bearingWallThick = 4
        #how much space we need to support the bearing (and how much space to leave for the arbour + screw0
        # self.bearingHolderLip=bearingHolderLip
        # self.bearingHeight = bearingHeight
        self.screwheadHeight = getScrewHeadHeight(self.fixingScrewsD)
        self.pendulumAtTop = pendulumAtTop
        self.pendulumSticksOut = pendulumSticksOut

        # how much space to leave around the edge of the gears for safety
        self.gearGap = 3

        #TODO make some sort of object to hold all this info we keep passing around?
        self.anchorThick=self.pendulum.anchorThick



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
                print("angle on arc: {}deg".format(radToDeg(angleOnArc)))
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
        self.wobble = 1
        #height of the centre of the wheel that will drive the next pinion
        drivingZ = 0
        for i in range(-self.goingTrain.chainWheels, self.goingTrain.wheels +1):
            print(str(i))
            if  i == -self.goingTrain.chainWheels:
                #the wheel with chain wheel ratchet
                #assuming this is at the very back of the clock
                #note - this is true when chain *is* at the back, when the chain is at the front the bearingPositions will be relative, not absolute
                pos = [0, 0, 0]
                self.bearingPositions.append(pos)
                #note - this is the chain wheel, which has the wheel at the back, but only pretends to have the pinion at the back for calculating the direction of the rest of the train
                drivingZ = self.goingTrain.getArbour(i).getWheelCentreZ()
                self.arbourThicknesses.append(self.goingTrain.getArbour(i).getTotalThickness())
                print("pinionAtFront: {} wheel {} drivingZ: {}".format(self.goingTrain.getArbour(i).pinionAtFront, i, drivingZ), pos)
            else:
                r = self.goingTrain.getArbour(i - 1).distanceToNextArbour
                print("r", r)
                #all the other going wheels up to and including the escape wheel
                if i == self.goingTrain.wheels:
                    # the anchor
                    baseZ = drivingZ - self.anchorThick / 2
                    self.arbourThicknesses.append(self.anchorThick)
                    print("is anchor")
                else:
                    #any of the other wheels
                    # pinionAtBack = not pinionAtBack
                    print("drivingZ at start:{} pinionToWheel: {} pinionCentreZ: {}".format(drivingZ, self.goingTrain.getArbour(i).getPinionToWheelZ(), self.goingTrain.getArbour(i).getPinionCentreZ()))
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
                if i < self.goingTrain.wheels:
                    print("pinionAtFront: {} wheel {} r: {} angle: {}".format( self.goingTrain.getArbour(i).pinionAtFront, i, r, angle), pos)
                print("baseZ: ",baseZ, "drivingZ ", drivingZ)

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
        self.plateDistance=max(topZs) + self.wobble

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
                maxR = arbour.distanceToNextArbour - self.goingTrain.getArbourWithConventionalNaming(i+1).getMaxRadius() - self.gearGap
            else:
                maxR = 0
            arbour.setArbourExtensionInfo(rearSide=bearingPos[2],maxR=maxR, frontSide=self.plateDistance-self.wobble-bearingPos[2] - arbour.getTotalThickness())



        #NOTE - can't change this here as it was used in calculating the plate distance. Need to push this up to the user to set
        # if poweredWheelBracingR > 5:
        #     #could do more logic here all the way to completely embedding the ratchet inside the wheel?
        #     poweredWheel.ratchetInsetness=0.5


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
        if self.goingTrain.usingChain:
            self.chainHoleD = self.goingTrain.chainWheel.chain_width + 2
        else:
            self.chainHoleD = self.goingTrain.cordWheel.cordThick*3

        self.weightOnRightSide = self.goingTrain.isWeightOnTheRight()

        #absolute z position
        self.embeddedNutHeight = self.plateThick + self.plateDistance - 20


    def getPlate(self, back=True, getText=False):
        if self.style in ["round", "vertical"]:
            return self.getSimplePlate(back, getText)

    def getPlateThick(self, back=True):
        if back:
            return self.backPlateThick
        return self.plateThick

    def getSimplePlate(self, back=True, getText=False):
        '''
        Two plates that are almost idential, with pillars at the very top and bottom to hold them together.
        Designed to be flat up against the wall, with everything offset to avoid the wall and picture rail

        styles: round or vertical
        round minimises total height by placing the gear train in a circle, so more complicated clocks can still fit on the print bed
        vertical just has everything directly above each other.

        The screwhole is placed directly above the weight to make the clock easier to hang straight

        '''
        bearingInfo = getBearingInfo(self.arbourD)
        #width of thin bit
        holderWide =  bearingInfo.bearingOuterD + self.bearingWallThick*2

        if self.extraHeavy:
            holderWide*=1.2

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

        minDistanceForChainHoles = (self.goingTrain.poweredWheel.diameter + self.chainHoleD * 2.5) / 2

        bottomPillarR= minDistanceForChainHoles

        if self.heavy:
            bottomPillarR = self.plateDistance/2


        if bottomPillarR < minDistanceForChainHoles:
            bottomPillarR = minDistanceForChainHoles
        topPillarR = holderWide/2









        if self.style == "round":
            screwHoleY = chainWheelR*1.4
        elif self.style == "vertical":
            if self.extraHeavy:
                #just above chain wheel (see if this helps reduce the plate flexing)
                screwHoleY = self.bearingPositions[0][1] + (self.bearingPositions[1][1] - self.bearingPositions[0][1]) * 0.6
            else:
                #just below escape wheel
                screwHoleY = self.bearingPositions[-3][1] + (self.bearingPositions[-2][1] - self.bearingPositions[-3][1])*0.6

        weightX = 0

        weightOnSide = 1 if self.weightOnRightSide else -1
        if self.heavy and not self.usingPulley:
            # line up the hole with the big heavy weight
            weightX = weightOnSide*self.goingTrain.poweredWheel.diameter/2

        #hole for hanging on the wall
        screwHolePos = (weightX , screwHoleY)

        anchorSpace = bearingInfo.bearingOuterD / 2 + self.gearGap

        #find the Y position of the bottom of the top pillar
        topY = self.bearingPositions[0][1]
        if self.style == "round":
            #find the highest point on the going train
            #TODO for potentially large gears this might be lower if they're spaced right
            for i in range(len(self.bearingPositions)-1):
                y = self.bearingPositions[i][1] + self.goingTrain.getArbourWithConventionalNaming(i).getMaxRadius() + self.gearGap
                if y > topY:
                    topY = y
        else:

            topY = self.bearingPositions[-1][1] + anchorSpace

        bottomPillarPos = [self.bearingPositions[0][0], self.bearingPositions[0][1] - chainWheelR - bottomPillarR]
        topPillarPos = [self.bearingPositions[0][0], topY + topPillarR]
        #where the extra-wide bit of the plate stops
        topOfBottomBitPos = self.bearingPositions[0]

        if self.heavy and self.usingPulley and back:
            #instead of an extra circle around the screwhole, make the plate wider extend all the way up
            #because the screwhole will be central when heavy and using a pulley
            topOfBottomBitPos = screwHolePos


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
        plate = plate.workplaneFromTagged("base").moveTo(topOfPlate[0] - topPillarR, topOfPlate[1]) \
            .lineTo(topPillarPos[0] - topPillarR, topPillarPos[1]).radiusArc((topPillarPos[0] + topPillarR, topPillarPos[1]), topPillarR) \
            .lineTo(topOfPlate[0] + topPillarR, topOfPlate[1]).close().extrude(self.getPlateThick(back))


        plate = plate.tag("top")
        # #for the screwhole
        # screwHeadD = 9
        # screwBodyD = 6
        # slotLength = 7

        if back:
            #extra bit around the screwhole
            #r = self.goingTrain.chainWheel.diameter*1.25
            # plate = plate.workplaneFromTagged("base").moveTo(screwHolePos[0], screwHolePos[1]-7-11/2).circle(holderWide*0.75).extrude(self.plateThick)
            backThick = max(self.getPlateThick(back)-5, 4)

            extraSupport = True

            if self.usingPulley and self.heavy:
                #the back plate is wide enough to accomodate
                extraSupport = False

            plate = self.addScrewHole(plate, screwHolePos, backThick=backThick, screwHeadD=11, addExtraSupport=extraSupport)
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
                plate = plate.workplaneFromTagged("top").moveTo(bottomPillarPos[0], bottomPillarPos[1]).circle(bottomPillarR * 0.9999).extrude(self.plateDistance)

            if self.extraHeavy:
                #beef up the top pillar
                # if anchorSpace > topPillarR:
                #     spaceR = anchorSpace
                #     pillarBottomZ = self.bearingPositions[-1][1] - math.sqrt(anchorSpace**2 - topPillarR ** 2)
                # else:
                #     spaceR = topPillarR
                #     pillarBottomZ = topPillarPos[1] - topPillarR*2
                #
                # plate = plate.workplaneFromTagged("top").moveTo(topPillarPos[0] - topPillarR, topPillarPos[1]).radiusArc((topPillarPos[0] + topPillarR, topPillarPos[1]), topPillarR).lineTo(topPillarPos[0] + topPillarR, pillarBottomZ).\
                #     radiusArc((topPillarPos[0] - topPillarR, pillarBottomZ),-spaceR).close().extrude(self.plateDistance)
                sagitta = topPillarR*0.25
                plate = plate.workplaneFromTagged("top").moveTo(topPillarPos[0] - topPillarR, topPillarPos[1]).radiusArc((topPillarPos[0] + topPillarR, topPillarPos[1]), topPillarR).lineTo(topPillarPos[0] + topPillarR, topPillarPos[1]-topPillarR - sagitta).\
                    sagittaArc((topPillarPos[0] - topPillarR, topPillarPos[1]-topPillarR-sagitta), -sagitta).close().extrude(self.plateDistance)
                #line(-topPillarR*2,0)
            else:
                plate = plate.workplaneFromTagged("top").moveTo(topPillarPos[0], topPillarPos[1]).circle(topPillarR*0.9999).extrude(self.plateDistance)

            textMultiMaterial = cq.Workplane("XY")
            textSize = topPillarR * 0.9
            textY = (self.bearingPositions[0][1] + fixingPositions[2][1])/2
            plate, textMultiMaterial = self.addText(plate, textMultiMaterial, "{} {:.1f}".format(self.name, self.goingTrain.pendulum_length * 100), (-textSize*0.5, textY), textSize)

            plate, textMultiMaterial = self.addText(plate, textMultiMaterial, "{}".format(datetime.date.today().strftime('%Y-%m-%d')), (textSize*0.5, textY), textSize)

            if getText:
                return textMultiMaterial

        plate = self.punchBearingHoles(plate, back)


        if back:



            chainHoles = self.getChainHoles(absoluteZ=True, bottomPillarPos=bottomPillarPos, bottomPillarR=bottomPillarR)



            plate = plate.cut(chainHoles)
        else:
           plate = self.frontAdditionsToPlate(plate)

        fixingScrewD = 3

        #screws to fix the plates together
        # if back:
        plate = plate.faces(">Z").workplane().pushPoints(fixingPositions).circle(fixingScrewD / 2).cutThruAll()
        # else:
        #can't get the countersinking to work
        #     plate = plate.workplaneFromTagged("top").pushPoints(fixingPositions).cskHole(diameter=fixingScrewD, cskAngle=90, cskDiameter=getScrewHeadDiameter(fixingScrewD), depth=None)#.cutThruAll()


        if back:
            for fixingPos in fixingPositions:
                #embedded nuts!
                plate = plate.cut(getHoleWithHole(fixingScrewD,getNutContainingDiameter(fixingScrewD,NUT_WIGGLE_ROOM), getNutHeight(fixingScrewD)*1.4, sides=6).translate((fixingPos[0], fixingPos[1], self.embeddedNutHeight)))

        return plate

    def getChainHoles(self, absoluteZ=False, bottomPillarPos=None, bottomPillarR=10):
        '''
        if absolute Z is false, these are positioned above the base plateThick
        this assumes an awful lot, it's likely to be a bit fragile

        bottomPillarPos needed for screw for pulley cord
        '''
        if self.goingTrain.usingChain:
            chainZ = self.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness() - WASHER_THICK - (self.goingTrain.chainWheel.getHeight() - self.goingTrain.chainWheel.ratchet.thick) / 2 + self.wobble/2
            leftZ = chainZ
            rightZ = chainZ
        else:
            if self.goingTrain.cordWheel.useFriction:
                #basically a chain wheel that uses friction instead of chain links
                chainZ = self.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness() - WASHER_THICK - self.goingTrain.cordWheel.pulley.getTotalThick()/2 + self.wobble / 2
                leftZ = chainZ
                rightZ = chainZ
            elif self.goingTrain.cordWheel.useKey and not self.goingTrain.cordWheel.useGear:
                #cord wheel with a key (probably for an eight day)
                #need one elongated hole for the cord
                chainZTop = self.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness() - WASHER_THICK - self.goingTrain.cordWheel.capThick + self.wobble / 2
                chainZBottom = self.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness() - WASHER_THICK - self.goingTrain.cordWheel.capThick - self.goingTrain.cordWheel.thick + self.wobble / 2

                if absoluteZ:
                    chainZTop += self.getPlateThick(back=True)
                    chainZBottom += self.getPlateThick(back=True)

                side = 1 if self.weightOnRightSide else -1
                chainX=side* (self.goingTrain.poweredWheel.diameter / 2 + self.chainHoleD*0.25 )

                chainHole = cq.Workplane("XZ").moveTo(chainX - self.chainHoleD/2, chainZTop-self.chainHoleD/2).radiusArc((chainX +self.chainHoleD/2, chainZTop-self.chainHoleD/2), self.chainHoleD/2)\
                    .lineTo(chainX + self.chainHoleD/2, chainZBottom + self.chainHoleD/2).radiusArc((chainX - self.chainHoleD/2, chainZBottom + self.chainHoleD/2), self.chainHoleD/2).close()\
                    .extrude(1000)

                if self.usingPulley:
                    pulleyX = -chainX
                    #might want it as far back as possible?
                    pulleyZ = chainZBottom + self.chainHoleD/2#(chainZTop + chainZBottom)/2
                    #and one hole for the cord to be tied
                    pulleyHole = cq.Workplane("XZ").moveTo(pulleyX, pulleyZ).circle(self.chainHoleD/2).extrude(1000)

                    #original plan was a screw in from the side, but I think this won't be particularly strong as it's in line with the layers
                    #so instead, put a screw in from the front

                    #this screw will provide something for the cord to be tied round
                    pulleyScrewHole = cq.Workplane("XY").moveTo(pulleyX,bottomPillarPos[1]).circle(self.fixingScrewsD/2).extrude(10000)
                    coneHeight = getScrewHeadHeight(self.fixingScrewsD, countersunk=True) + COUNTERSUNK_HEAD_WIGGLE
                    topR = getScrewHeadDiameter(self.fixingScrewsD, countersunk=True) / 2 + COUNTERSUNK_HEAD_WIGGLE
                    topZ=self.plateDistance
                    if absoluteZ:
                        topZ+=self.getPlateThick(back=True)
                    pulleyScrewHole = pulleyScrewHole.add(cq.Solid.makeCone(radius2=topR, radius1=self.fixingScrewsD / 2,height=coneHeight).translate((pulleyX, bottomPillarPos[1], topZ-coneHeight)))

                    #
                    # pulleyScrewHole = cq.Workplane("YZ").moveTo(bottomPillarPos[1], pulleyZ).circle(self.fixingScrewsD / 2).extrude(bottomPillarR)
                    # if False:
                    #
                    #     #I like the idea of this for not having a screw sticking out the side, however it leaves very little material to hold the weight
                    #
                    #     coneHeight = getScrewHeadHeight(self.fixingScrewsD, countersunk=True) + COUNTERSUNK_HEAD_WIGGLE
                    #     topR = getScrewHeadDiameter(self.fixingScrewsD, countersunk=True) / 2 + COUNTERSUNK_HEAD_WIGGLE
                    #     countersink = cq.Workplane("XY").add(cq.Solid.makeCone(radius2=topR, radius1=self.fixingScrewsD / 2,height=coneHeight)).rotate((0,0,0),(0,1,0),90).translate((bottomPillarR-coneHeight,bottomPillarPos[1],pulleyZ))
                    #     pulleyHole = pulleyHole.add(countersink)



                    chainHole = chainHole.add(pulleyHole).add(pulleyScrewHole)

                return chainHole
            else:
                #TODO make these elongated too - probably doesn't matter that much as it's only ever going to be a 1 day light weight
                #assuming a two-section cord wheel, one side coils up as the weight coils down
                #cord, leaving enough space for the washer as well (which is hackily included in getTotalThickness()
                bottomZ = self.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness() - WASHER_THICK - self.goingTrain.cordWheel.thick*1.5 - self.goingTrain.cordWheel.capThick*2 + self.wobble / 2
                topZ = bottomZ +  self.goingTrain.cordWheel.thick + self.goingTrain.cordWheel.capThick

                if self.weightOnRightSide:
                    rightZ = bottomZ
                    leftZ = topZ
                else:
                    rightZ = topZ
                    leftZ = bottomZ

        if absoluteZ:
            leftZ += self.getPlateThick(back=True)
            rightZ += self.getPlateThick(back=True)

        chainHoles = cq.Workplane("XZ").pushPoints([(self.goingTrain.poweredWheel.diameter / 2, rightZ), (-self.goingTrain.poweredWheel.diameter / 2, leftZ)]).circle(self.chainHoleD / 2).extrude(1000)

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
            punch = getHoleWithHole(bearingInfo.innerD + bearingInfo.bearingHolderLip*2,bearingInfo.bearingOuterD, bearingInfo.bearingHeight).faces(">Z").workplane().circle(bearingInfo.innerD/2 + bearingInfo.bearingHolderLip).extrude(height - bearingInfo.bearingHeight)

        return punch

    def punchBearingHoles(self, plate, back):
        for i, pos in enumerate(self.bearingPositions):
            bearingInfo = getBearingInfo(self.goingTrain.getArbourWithConventionalNaming(i).getRodD())
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

        if self.pendulumSticksOut > 0:
            #trying this WITHOUT the support
            extraBearingHolder = self.getBearingHolder(self.pendulumSticksOut, False).translate((self.bearingPositions[len(self.bearingPositions) - 1][0], self.bearingPositions[len(self.bearingPositions) - 1][1], plateThick))
            plate = plate.add(extraBearingHolder)

        plate = plate.faces(">Z").workplane().moveTo(self.bearingPositions[self.goingTrain.chainWheels][0] + self.motionWorksRelativePos[0], self.bearingPositions[self.goingTrain.chainWheels][1] + self.motionWorksRelativePos[1]).circle(
            self.fixingScrewsD / 2).cutThruAll()

        nutDeep = getNutHeight(self.fixingScrewsD, halfHeight=True)
        screwheadHeight = getScrewHeadHeight(self.fixingScrewsD)
        #ideally want a nut embedded on the top, but that can leave the plate a bit thin here

        nutZ = max(screwheadHeight + 3, plateThick - nutDeep)
        nutSpace = cq.Workplane("XY").polygon(6, getNutContainingDiameter(self.fixingScrewsD)).extrude(nutDeep).translate(
            (self.bearingPositions[self.goingTrain.chainWheels][0] + self.motionWorksRelativePos[0], self.bearingPositions[self.goingTrain.chainWheels][1] + self.motionWorksRelativePos[1], nutZ))

        plate = plate.cut(nutSpace)

        screwheadSpace =  getHoleWithHole(self.fixingScrewsD, getScrewHeadDiameter(self.fixingScrewsD)+0.5, screwheadHeight).translate((self.bearingPositions[self.goingTrain.chainWheels][0] + self.motionWorksRelativePos[0], self.bearingPositions[self.goingTrain.chainWheels][1] + self.motionWorksRelativePos[1], 0))

        plate = plate.cut(screwheadSpace)

        if self.dial is not None:
            dialFixings = self.dial.getFixingDistance()
            minuteY = self.bearingPositions[self.goingTrain.chainWheels][1]
            plate = plate.faces(">Z").workplane().pushPoints([(0, minuteY + dialFixings / 2), (0, minuteY - dialFixings / 2)]).circle(self.dial.fixingD / 2).cutThruAll()

        # need an extra chunky hole for the big bearing that the key slots through
        if not self.goingTrain.usingChain and self.goingTrain.cordWheel.useKey and not self.goingTrain.cordWheel.useGear:
            cordWheel = self.goingTrain.cordWheel
            # cordBearingHole = cq.Workplane("XY").circle(cordWheel.bearingOuterD/2).extrude(cordWheel.bearingHeight)
            cordBearingHole = getHoleWithHole(cordWheel.bearingInnerD + cordWheel.bearingLip * 2, cordWheel.bearingOuterD, cordWheel.bearingHeight)
            cordBearingHole = cordBearingHole.faces(">Z").workplane().circle(cordWheel.bearingInnerD/2 + cordWheel.bearingLip).extrude(plateThick)

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
    def __init__(self, plates, hands=None, dial=None, timeMins=10, timeHours=10, timeSeconds=0, pulley=None):
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

    def getClock(self):
        bottomPlate = self.plates.getPlate(True)
        topPlate  = self.plates.getPlate(False)

        clock = bottomPlate.add(topPlate.translate((0,0,self.plates.plateDistance + self.plates.getPlateThick(back=True))))

        #the wheels
        for a in range(self.goingTrain.wheels + self.goingTrain.chainWheels + 1):
            arbour = self.goingTrain.getArbourWithConventionalNaming(a)
            clock = clock.add(arbour.getAssembled().translate(self.plates.bearingPositions[a]).translate((0,0,self.plates.getPlateThick(back=True) + self.plates.wobble/2)))



        # anchorAngle = math.atan2(self.plates.bearingPositions[-1][1] - self.plates.bearingPositions[-2][1], self.plates.bearingPositions[-1][0] - self.plates.bearingPositions[-2][0]) - math.pi/2
        #
        # #the anchor is upside down for better printing, so flip it back
        # anchor = self.pendulum.anchor#.mirror("YZ", (0,0,0))
        # #and rotate it into position
        # anchor = anchor.rotate((0,0,0),(0,0,1), radToDeg(anchorAngle)).translate(self.plates.bearingPositions[-1]).translate((0,0,self.plates.getPlateThick(back=True) + self.plates.wobble/2))
        # clock = clock.add(anchor)

        #where the nylock nut and spring washer would be
        motionWorksZOffset = 3

        time_min = self.timeMins
        time_hour = self.timeHours


        minuteAngle = - 360 * (time_min / 60)
        hourAngle = - 360 * (time_hour + time_min / 60) / 12
        secondAngle = -360 * (self.timeSeconds / 60)

        motionWorksModel = self.motionWorks.getAssembled(motionWorksRelativePos=self.plates.motionWorksRelativePos,minuteAngle=minuteAngle)

        clock = clock.add(motionWorksModel.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1], self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance + motionWorksZOffset)))



        #hands on the motion work, showing the time
        #mirror them so the outline is visible (consistent with second hand)
        minuteHand = self.hands.getHand(hour=False).mirror().translate((0,0,self.hands.thick)).rotate((0,0,0),(0,0,1), minuteAngle)
        hourHand = self.hands.getHand(hour=True).mirror().translate((0,0,self.hands.thick)).rotate((0, 0, 0), (0, 0, 1), hourAngle)


        clock = clock.add(minuteHand.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1], self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance + motionWorksZOffset + self.motionWorks.minuteHolderTotalHeight - self.hands.thick)))

        clock = clock.add(hourHand.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1],
                                                self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance + motionWorksZOffset + self.motionWorks.minuteHolderTotalHeight - self.hands.thick*3)))

        if self.goingTrain.escapement_time == 60:
            #second hand!! yay
            secondHand = self.hands.getHand(second=True).mirror().translate((0,0,self.hands.thick)).rotate((0, 0, 0), (0, 0, 1), secondAngle)
            clock = clock.add(secondHand.translate((self.plates.bearingPositions[-2][0], self.plates.bearingPositions[-2][1], self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance+self.hands.secondFixing_thick )))


        pendulumRodExtraZ = 2

        pendulumRodFixing = self.pendulum.getPendulumForRod().mirror().translate((0,0,self.pendulum.pendulumTopThick))

        clock = clock.add(pendulumRodFixing.translate((self.plates.bearingPositions[-1][0], self.plates.bearingPositions[-1][1], self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance + self.plates.pendulumSticksOut + pendulumRodExtraZ)))

        minuteToPendulum = (self.plates.bearingPositions[-1][0] - self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[-1][1] - self.plates.bearingPositions[self.goingTrain.chainWheels][1])

        if abs(minuteToPendulum[0]) < 50:
            #assume we need the ring to go around the hands
            ring = self.pendulum.getHandAvoider()
            handAvoiderExtraZ = (self.pendulum.pendulumTopThick - self.pendulum.handAvoiderThick)/2
            #ring is over the minute wheel/hands
            clock = clock.add(ring.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1],self.plates.getPlateThick(back=True) + self.plates.getPlateThick(back=False) + self.plates.plateDistance + self.plates.pendulumSticksOut + pendulumRodExtraZ + handAvoiderExtraZ)))

        if self.pulley is not None:
            #HACK HACK HACK, just copy pasted from teh chainHoles in plates, assumes cord wheel with key
            chainZ = self.plates.getPlateThick(back=True) + self.plates.bearingPositions[0][2] + self.goingTrain.getArbour(-self.goingTrain.chainWheels).getTotalThickness() - WASHER_THICK - self.goingTrain.cordWheel.capThick - self.goingTrain.cordWheel.thick + self.plates.wobble / 2
            print("chain Z", chainZ)
            clock = clock.add(self.pulley.getAssembled().rotate((0,0,0),(0,0,1),90).translate((0,self.plates.bearingPositions[0][1] - 120, chainZ - self.pulley.getTotalThick()/2)))

        #TODO pendulum bob and nut?

        #TODO weight?

        return clock

    def outputSTLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.getClock(), out)

# if 'show_object' not in globals():
#     def show_object(*args, **kwargs):
#         pass
#
# ballWheel = BallWheel()
# torque = ballWheel.getTorque()
# print("torque", torque, torque/0.037)

#trial for 48 tooth wheel
# drop = 1.5
# lift = 2
# lock = 1.5
# teeth = 48
# diameter = 65  # 64.44433859295404#61.454842805344896
# toothTipAngle = 4
# toothBaseAngle = 3
# escapement = Escapement(drop=drop, lift=lift, type="deadbeat", diameter=diameter, teeth=teeth, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=toothTipAngle, toothBaseAngle=toothBaseAngle)

# drop =1.5
# lift =3
# lock=1.5
# escapement = Escapement(drop=drop, lift=lift, type="deadbeat",teeth=40, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=5, toothBaseAngle=4)

# animateEscapement(escapement, frames=100, period=1.5,overswing_deg=4)












# getRadiusForPointsOnACircle([10,20,15], math.pi)
#
#
# dial = Dial(120)
#
# show_object(dial.getDial())
#
# weight = Weight()
#
# show_object(weight.getHook())
#
# show_object(weight.getRing().translate((20,0,0)))
#
# show_object(weight.getWeight())
#
# weight.printInfo()
#
# print("Weight max: {:.2f}kg".format(weight.getMaxWeight()))
# show_object(weight.getLid(forCutting=True))
#
# train=GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=30, maxChainDrop=2100, chainAtBack=False)
# train.calculateRatios()
# train.printInfo()
# train.genChainWheels()
# # show_object(train.chainWheelWithRatchet)
# # show_object(train.chainWheelHalf.translate((0,30,0)))
# train.genGears(module_size=1.2,moduleReduction=0.85, ratchetThick=4)
# # show_object(train.ratchet.getInnerWheel())
# # show_object(train.arbours[0])
#
# motionWorks = MotionWorks(minuteHandHolderHeight=30)
#
# pendulum = Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=8)
#
#
# # show_object(pendulum.getPendulumForRod())
# # show_object(pendulum.getHandAvoider())
# # show_object(pendulum.getBob())
# show_object(pendulum.getBobNut())
#
#
# plates = ClockPlates(train, motionWorks, pendulum,plateThick=10)
# #
# backplate = plates.getPlate(True)
# frontplate = plates.getPlate(False)
# show_object(backplate)
# show_object(frontplate.translate((100,0,0)))

# holepunch = getHoleWithHole(3,10,4)
# show_object(holepunch)
# shape = cq.Workplane("XY").circle(10).extrude(20)
# shape = shape.cut(holepunch)
#
# show_object(shape)

# escapement = Escapement(teeth=30, diameter=60)
# pendulum = Pendulum(escapement, 0.388, anchorHoleD=3, anchorThick=8, nutMetricSize=3, crutchLength=0, bobD=60, bobThick=10)
# show_object(pendulum.getPendulumForRod())
# # show_object(pendulum.getBob())

# # show_object(escapement.getAnchor3D())
# show_object(escapement.getAnchorArbour(holeD=3, crutchLength=0, nutMetricSize=3))
#
# # hands = Hands(style="simple", minuteFixing="square", minuteFixing_d1=5, hourfixing_d=5, length=100, outline=1, outlineSameAsBody=False)
# hands = Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=5, hourfixing_d=5, length=100, thick=4, outline=1, outlineSameAsBody=False)
# #
# # show_object(hands.getHand(outline=False))
# show_object(hands.getHandNut())
# hands.outputSTLs(clockName, clockOutDir)

##### =========== escapement testing ======================
#drop of 1 and lift of 3 has good pallet angles with 42 teeth
# drop =1.5
# lift =2
# lock=1.5
# teeth = 48
# diameter = 65# 64.44433859295404#61.454842805344896
# toothTipAngle = 4
# toothBaseAngle = 3
# escapement = Escapement(drop=drop, lift=lift, type="deadbeat",diameter=diameter, teeth=teeth, lock=lock, anchorTeeth=None, toothHeightFraction=0.2, toothTipAngle=toothTipAngle, toothBaseAngle=toothBaseAngle)
# # # escapement = Escapement(teeth=30, diameter=61.454842805344896, lift=4, lock=2, drop=2, anchorTeeth=None,
# # #                              clockwiseFromPinionSide=False, type="deadbeat")
# ##
# svgOpt = opt={"showAxes":False,
# "projectionDir": (0, 0, 1),
# "width": 1280,
# "height": 720,
# }
#
# toothAngle = 360/teeth
# toothAtEndOfExitPallet = radToDeg(math.pi/2 +escapement.anchorAngle/2) - (toothAngle/2 - drop)/2
# wheel_angle = toothAtEndOfExitPallet#-3.8  -4.1  -2 #- radToDeg(escapement.toothAngle - escapement.drop)/2#-3.3 - drop - 3.5 -
# anchor_angle = lift/2+lock/2#lift/2 + lock/2
#
# frames = 100
# for frame in range(frames):
#     wholeObject = escapement.getAnchor2D().rotate((0,escapement.anchor_centre_distance,0),(0,escapement.anchor_centre_distance,1), anchor_angle).add(escapement.getWheel2D().rotateAboutCenter((0,0,1), wheel_angle))
#     exporters.export(wholeObject, "out/test_{:02d}.svg".format(frame), opt=svgOpt)
#     # svgString = exporters.getSVG(exporters.toCompound(wholeObject), opts=svgOpt)
#     # print(svgString)
#     # show_object(wholeObject)




# toothAngle = 360/teeth
# toothAtEndOfExitPallet = radToDeg(math.pi/2 +escapement.anchorAngle/2) - (toothAngle/2 - drop)/2
# wheel_angle = toothAtEndOfExitPallet#-3.8  -4.1  -2 #- radToDeg(escapement.toothAngle - escapement.drop)/2#-3.3 - drop - 3.5 -
# anchor_angle = lift/2+lock/2#lift/2 + lock/2
#
# wholeObject = escapement.getAnchor2D().rotate((0,escapement.anchor_centre_distance,0),(0,escapement.anchor_centre_distance,1), anchor_angle).add(escapement.getWheel2D().rotateAboutCenter((0,0,1), wheel_angle))
#
# show_object(wholeObject)
#
# svgOpt = opt={"showAxes":False,
# "projectionDir": (0, 0, 1),
# "width": 1280,
# "height": 720,
# }
#
# exporters.export(wholeObject, "out/test.svg", opt=svgOpt)

# show_object(escapement.getAnchor2D().rotate((0,escapement.anchor_centre_distance,0),(0,escapement.anchor_centre_distance,1), anchor_angle))
# show_object(escapement.getWheel2D().rotateAboutCenter((0,0,1), wheel_angle))

# anchor = escapement.getAnchorArbour(holeD=3, anchorThick=10, clockwise=False, arbourLength=0, crutchLength=0, crutchBoltD=3, pendulumThick=3, nutMetricSize=3)
# # show_object(escapement.getAnchor3D())
# show_object(anchor)
# exporters.export(anchor, "../out/anchor_test.stl")
# #
# #

# ### ============FULL CLOCK ============
# # # train=clock.GoingTrain(pendulum_period=1.5,fourth_wheel=False,escapement_teeth=40, maxChainDrop=2100)
# train=GoingTrain(pendulum_period=2,fourth_wheel=False,escapement_teeth=30, maxChainDrop=1800, chainAtBack=False)#,chainWheels=1, hours=180)
# train.calculateRatios()
# # train.setRatios([[64, 12], [63, 12], [60, 14]])
# # train.setChainWheelRatio([74, 11])
# # train.genChainWheels(ratchetThick=5)
# pendulumSticksOut=25
# # train.genChainWheels(ratchetThick=5, wire_thick=1.2,width=4.5, inside_length=8.75-1.2*2, tolerance=0.075)#, wire_thick=0.85, width=3.6, inside_length=6.65-0.85*2, tolerance=0.1)
# train.genCordWheels(ratchetThick=5, cordThick=2, cordCoilThick=11)
# train.genGears(module_size=1,moduleReduction=0.875, thick=3, chainWheelThick=6, useNyloc=False)
# motionWorks = MotionWorks(minuteHandHolderHeight=30)
# #trying using same bearings and having the pendulum rigidly fixed to the anchor's arbour
# pendulum = Pendulum(train.escapement, train.pendulum_length, anchorHoleD=3, anchorThick=12, nutMetricSize=3, crutchLength=0, useNylocForAnchor=False)
#
#
# #printed the base in 10, seems much chunkier than needed at the current width. Adjusting to 8 for the front plate
# plates = ClockPlates(train, motionWorks, pendulum, plateThick=8, pendulumSticksOut=pendulumSticksOut, name="Wall 05", style="vertical")#, heavy=True)
#
# plate = plates.getPlate(True)
# #
# show_object(plate)
#
# show_object(plates.getPlate(False).translate((0,0,plates.plateDistance + plates.plateThick)))
# #
# # hands = Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=3, hourfixing_d=5, length=100, thick=4, outline=0, outlineSameAsBody=False)
# hands = Hands(style="simple_rounded", minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, thick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
# assembly = Assembly(plates, hands=hands)
#
# show_object(assembly.getClock())
# # #

# # anchorAngle = math.atan2(plates.bearingPositions[-1][1] - plates.bearingPositions[-2][1], plates.bearingPositions[-1][0] - plates.bearingPositions[-2][0]) - math.pi / 2
# # # anchorAngle=0
# # anchor = pendulum.anchor.rotate((0,0,0),(0, 0, 1), radToDeg(anchorAngle))#.translate(plates.bearingPositions[-1]).translate((0, 0, plates.plateThick + plates.wobble / 2))
# # show_object(anchor)
#
# # exporters.export(plate, "../out/platetest.stl")
# #
# # hands = Hands(minuteFixing="square", minuteFixing_d1=motionWorks.minuteHandHolderSize+0.2, hourfixing_d=motionWorks.getHourHandHoleD(), length=100, ratchetThick=motionWorks.minuteHandSlotHeight, outline=1, outlineSameAsBody=False)
#
# #
# #
# # show_object(plates.goingTrain.getArbour(0).getShape(False).translate((0,200,0)))

# ============ hands ==================
#
# hands = Hands(style="simple_rounded",minuteFixing="square", minuteFixing_d1=3, hourfixing_d=5, length=80, thick=4, outline=1, outlineSameAsBody=False)
# show_object(hands.getHand(True,True))
# show_object(hands.getHand(True,False).translate((50,0,0)))
# show_object(hands.getHand(hour=False,second=True).translate((-50,0,0)))

#
# shell = WeightShell(45,220, twoParts=True, holeD=5)
#
# show_object(shell.getShell())
#
# show_object(shell.getShell(False).translate((100,0,0)))
#
# ratchet = Ratchet()
# # cordWheel = CordWheel(23,50, ratchet=ratchet, useGear=True, style="circles")
# cordWheel = CordWheel(23,50, ratchet=ratchet, style="circles", useKey=True)
# #
# #
# #
#
# # pulley = Pulley(diameter=30, vShaped=False)
# #
# # show_object(pulley.getHalf())
#
# # show_object(cordWheel.getSegment())
# # show_object(cordWheel.getAssembled())
# # show_object(cordWheel.getCap(top=True))
# # show_object(cordWheel.getCap())
#
# show_object(cordWheel.getKey())
#
# show_object(cordWheel.getKeyKnob().translate((50,0,0)))
#
#

# show_object(cordWheel.getClickWheelForCord(ratchet))
# show_object(cordWheel.getCap().translate((0,0,ratchet.thick)))
# show_object(cordWheel.getSegment(False).mirror().translate((0,0,cordWheel.thick)).translate((0,0,ratchet.thick + cordWheel.capThick)))
# show_object(cordWheel.getSegment(True).mirror().translate((0,0,cordWheel.thick)).translate((0,0,ratchet.thick + cordWheel.capThick + cordWheel.thick)))

