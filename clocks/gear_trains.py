import numpy.linalg.linalg

from .utility import *
from .power import *
from .gearing import *
from .escapements import *
from .dial import *
import math
import numpy as np

'''
This file is for classes to generate gear trains. currently going a going train.

There's not much reason to do cadquery work here, this is mostly about calculating gear ratios and power wheels.
'''

class GoingTrain:
    '''
    This sets which direction the gears are facing and does some work about setting the size of the escape wheel, which is getting increasingly messy
    and makes some assumptions that are no longer true, now there's a variety of power sources and train layouts.

    I propose instead moving this logic over to the plates and therefore out of Arbor and into ArborForPlate.
    Maybe even going as far as this class not generating any actual geometry? just being ratios?

    TODO just provide a powered wheel to the constructor, like the escapement, and get rid of the myriad of gen_x_wheel methods.

    '''

    def __init__(self, pendulum_period=-1, pendulum_length_m=-1, wheels=3, fourth_wheel=None, escapement_teeth=30, chain_wheels=0, runtime_hours=30, chain_at_back=True, max_weight_drop=1800,
                 escapement=None, escape_wheel_pinion_at_front=None, use_pulley=False, huygens_maintaining_power=False, minute_wheel_ratio=1, support_second_hand=False, powered_wheel=None):
        '''

        pendulum_period: desired period for the pendulum (full swing, there and back) in seconds
        fourth_wheel: if True there will be four wheels from minute hand to the escape wheel
        escapement_teeth: number of teeth on the escape wheel DEPRECATED, provide entire escapement instead
        chain_wheels: if 0 the minute wheel is also the chain wheel, if >0, this many gears between the minute wheel and chain wheel (say for 8 day clocks)
        hours: intended hours to run for (dictates diameter of chain wheel)
        chain_at_back: Where the chain and ratchet mechanism should go relative to the minute wheel
        max_weight_drop: maximum length of chain drop to meet hours required, in mm
        max_chain_wheel_d: Desired diameter of the chain wheel, only used if chainWheels > 0. If chainWheels is 0 there is no flexibility here
        escapement: Escapement object. If not provided, falls back to defaults with esacpement_teeth
        use_pulley: if true, changes calculations for runtime
        escape_wheel_pinion_at_front:  bool, override default
        huygens_maintaining_power: bool, if true we're using a weight on a pulley with a single loop of chain/rope, going over a ratchet on the front of the clock and a counterweight on the other side from the main weight
        easiest to implement with a chain

        minute_wheel_ratio: usually 1 - so the minute wheel (chain wheel as well on a 1-day clock) rotates once an hour. If less than one, this "minute wheel" rotates less than once per hour.
        this makes sense (at the moment) only on a centred-second-hand clock where we have another set of wheels linking the "minute wheel" and the motion works

        support_second_hand: if the period and number of teeth on the escape wheel don't result in it rotating once a minute, try and get the next gear down the train to rotate once a minute

        powered_wheel: if provided, use this. if not use the deprecated gen_*wheels() methods

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

        # in seconds
        self.pendulum_period = pendulum_period
        # in metres
        self.pendulum_length_m = pendulum_length_m

        # was experimenting with having the minute wheel outside the powered wheel to escapement train - but I think it's a dead
        # end as it will end up with some slop if it's not in the train
        self.minute_wheel_ratio = minute_wheel_ratio

        self.support_second_hand = support_second_hand

        self.huygens_maintaining_power = huygens_maintaining_power
        self.arbors = []

        if pendulum_length_m < 0 and pendulum_period > 0:
            # calulate length from period
            self.pendulum_length_m = getPendulumLength(pendulum_period)
        elif pendulum_period < 0 and pendulum_length_m > 0:
            self.pendulum_period = getPendulumPeriod(pendulum_length_m)
        else:
            raise ValueError("Must provide either pendulum length or perioud, not neither or both")
        print("Pendulum length {}cm and period {}s".format(self.pendulum_length_m * 100, self.pendulum_period))
        # note - this has become assumed in many places and will require work to the plates and layout of gears to undo
        self.chain_at_back = chain_at_back
        # likewise, this has been assumed, but I'm trying to undo those assumptions to use this
        self.penulum_at_front = True
        # to ensure the anchor isn't pressed up against the back (or front) plate
        if escape_wheel_pinion_at_front is None:
            self.escape_wheel_pinion_at_front = chain_at_back
        else:
            self.escape_wheel_pinion_at_front = escape_wheel_pinion_at_front

        self.powered_wheel = powered_wheel

        if self.powered_wheel is not None:
            self.powered_by = self.powered_wheel.type
        else:
            self.powered_by = PowerType.NOT_CONFIGURED

        # if zero, the minute hand is directly driven by the chain, otherwise, how many gears from minute hand to chain wheel
        self.powered_wheels = chain_wheels
        # to calculate sizes of the powered wheels and ratios later
        self.runtime_hours = runtime_hours
        self.max_weight_drop = max_weight_drop
        self.use_pulley = use_pulley

        if fourth_wheel is not None:
            # old deprecated interface, use "wheels" instead
            self.wheels = 4 if fourth_wheel else 3
        else:
            self.wheels = wheels

        # calculate ratios from minute hand to escapement
        # the last wheel is the escapement

        self.escapement = escapement
        if escapement is None:
            self.escapement = AnchorEscapement(teeth=escapement_teeth)
        #
        self.escapement_time = self.pendulum_period * self.escapement.teeth

        self.trains = []

    def has_seconds_hand_on_escape_wheel(self):
        # not sure this should work with floating point, but it does...
        return self.escapement_time == 60

    def has_second_hand_on_last_wheel(self):

        last_pair = self.trains[0]["train"][-1]
        return self.escapement_time / (last_pair[1] / last_pair[0]) == 60

    def get_cord_usage(self):
        '''
        how much rope or cord will actually be used, as opposed to how far the weight will drop
        '''
        if self.use_pulley:
            return 2 * self.max_weight_drop
        return self.max_weight_drop

    '''
    TODO make this generic and re-usable, I've got similar logic over in calculating chain wheel ratios and motion works
    '''

    def calculate_ratios(self, module_reduction=0.85, min_pinion_teeth=10, max_wheel_teeth=100, pinion_max_teeth=20, wheel_min_teeth=50,
                         max_error=0.1, loud=False, penultimate_wheel_min_ratio=0, favour_smallest=True, allow_integer_ratio=False, constraint=None):
        '''
        Returns and stores a list of possible gear ratios, sorted in order of "best" to worst
        module reduction used to calculate smallest possible wheels - assumes each wheel has a smaller module than the last
        penultimate_wheel_min_ratio - check that the ratio of teeth on the last wheel is greater than the previous wheel's teeth * penultimate_wheel_min_ratio (mainly for trains
        where the second hand is on the penultimate wheel rather than the escape wheel - since we prioritise smaller trains we can end up with a teeny tiny escape wheel)

        now favours a low standard deviation of number of teeth on the wheels - this should stop situations where we get a giant first wheel and tiny final wheels (and tiny escape wheel)
        This is slow, but seems to work well
        '''

        pinion_min = min_pinion_teeth
        pinion_max = pinion_max_teeth
        wheel_min = wheel_min_teeth
        wheel_max = max_wheel_teeth

        '''
        https://needhamia.com/clock-repair-101-making-sense-of-the-time-gears/
        “With an ‘integer ratio’, the same pairs of teeth (gear/pinion) always mesh on each revolution.
         With a non-integer ratio, each pass puts a different pair of teeth in mesh. (Some fractional 
         ratios are also called a ‘hunting ratio’ because a given tooth ‘hunts’ [walks around] the other gear.)”

         "So it seems clock designers prefer non-whole-number gear ratios to even out the wear of the gears’ teeth. "

         seems reasonable to me
        '''
        all_gear_pair_combos = []
        all_seconds_wheel_combos = []

        target_time = 60 * 60 / self.minute_wheel_ratio

        for p in range(pinion_min, pinion_max):
            for w in range(wheel_min, wheel_max):
                all_gear_pair_combos.append([w, p])

        # use a much wider range
        if self.support_second_hand and not self.has_seconds_hand_on_escape_wheel():
            for p in range(pinion_min, pinion_max * 3):
                for w in range(pinion_max, wheel_max * 4):
                    # print(p, w, self.escapement_time / (p/w))
                    if self.escapement_time / (p / w) == 60:
                        all_seconds_wheel_combos.append([w, p])
        if loud:
            print("allGearPairCombos", len(all_gear_pair_combos))
        # [ [[w,p],[w,p],[w,p]] ,  ]
        all_trains = []

        print(all_seconds_wheel_combos)

        all_trains_length = 1
        for i in range(self.wheels):
            all_trains_length *= len(all_gear_pair_combos)
        allcombo_count = len(all_gear_pair_combos)

        def add_combos(pair_index=0, previous_pairs=None):
            if previous_pairs is None:
                previous_pairs = []
            # one fewer pair than wheels, and if we're the last pair then add the combos, else recurse
            final_pair = pair_index == self.wheels - 2
            valid_combos = all_gear_pair_combos
            if self.support_second_hand and not self.has_seconds_hand_on_escape_wheel() and final_pair:
                # using a different set of combinations that will force the penultimate wheel to rotate at 1 rpm
                valid_combos = all_seconds_wheel_combos
            for pair in range(len(valid_combos)):
                if loud and pair % 10 == 0 and pair_index == 0:
                    print("\r{:.1f}% of calculating train options".format(100 * pair / allcombo_count), end='')

                all_pairs = previous_pairs + [valid_combos[pair]]
                if final_pair:
                    all_trains.append(all_pairs)
                else:
                    add_combos(pair_index + 1, all_pairs)

        # recursively create an array of all gear trains to test - should work with any number of wheels >= 2
        add_combos()

        if loud:
            print("\nallTrains", len(all_trains))
        all_times = []
        total_trains = len(all_trains)
        for c in range(total_trains):
            if loud and c % 100 == 0:
                print("\r{:.1f}% of trains evaluated".format(100 * c / total_trains), end='')
            total_ratio = 1
            int_ratio = False
            total_teeth = 0
            # trying for small wheels and big pinions
            total_wheel_teeth = 0
            total_pinion_teeth = 0
            weighting = 0
            last_size = 0
            fits = True
            for p in range(len(all_trains[c])):
                ratio = all_trains[c][p][0] / all_trains[c][p][1]
                if ratio == round(ratio):
                    int_ratio = True
                    if not allow_integer_ratio:
                        break
                total_ratio *= ratio
                total_teeth += all_trains[c][p][0] + all_trains[c][p][1]
                total_wheel_teeth += all_trains[c][p][0]
                total_pinion_teeth += all_trains[c][p][1]
                # module * number of wheel teeth - proportional to diameter
                size = math.pow(module_reduction, p) * all_trains[c][p][0]
                if favour_smallest:
                    weighting += size
                else:
                    # still don't want to just choose largest by mistake
                    weighting += size * 0.3
                if p > 0 and size > last_size * 0.9:
                    # this wheel is unlikely to physically fit
                    fits = False
                    break
                last_size = size
            # favour evenly sized wheels
            wheel_tooth_counts = [pair[0] for pair in all_trains[c]]
            weighting += np.std(wheel_tooth_counts)
            if self.support_second_hand and not self.has_seconds_hand_on_escape_wheel():
                # want to check last wheel won't be too tiny (would rather add more teeth than increase the module size for asthetics)
                if all_trains[c][-1][0] < all_trains[c][-2][0] * penultimate_wheel_min_ratio:
                    # only continue if the penultimate wheel has more than half the number of teeth of the wheel before that
                    continue

            total_time = total_ratio * self.escapement_time
            error = target_time - total_time
            if int_ratio:
                # avoid if we can
                weighting += 100



            train = {"time": total_time, "train": all_trains[c], "error": abs(error), "ratio": total_ratio, "teeth": total_wheel_teeth, "weighting": weighting}



            if fits and abs(error) < max_error:  # and not int_ratio:

                if constraint is not None:
                    if not constraint(train):
                        continue
                    else:
                        print("constraint met", train)

                all_times.append(train)

        if loud:
            print("")

        all_times.sort(key=lambda x: x["error"])
        # print(allTimes)

        self.trains = all_times

        if len(all_times) == 0:
            raise RuntimeError("Unable to calculate valid going train")
        print(all_times[0])
        return all_times


    def set_ratios(self, gear_pinion_pairs):
        '''
        Instead of calculating the gear train from scratch, use a predetermined one. Useful when using 4 wheels as those take a very long time to calculate
        '''
        # keep in the format of the autoformat
        time = {'train': gear_pinion_pairs}

        self.trains = [time]

    def calculate_powered_wheel_ratios(self, pinion_min=10, pinion_max=20, wheel_min=20, wheel_max=160, prefer_small=False, inaccurate=False, big_pinion=False,
                                       prefer_large_second_wheel=True):
        '''
        Calcualte the ratio of the chain wheel based on the desired runtime and chain drop
        used to prefer largest wheel, now is hard coded to prefer smallest.

        experiment for springs, if inaccurate then allow a large variation of the final ratio if it helps keep the size down

        big_pinion if true prefer a larger first pinion (easier to print with multiple perimeters)


        prefer_large_second_wheel is usually true because this helps with spring barrels
        '''
        if self.powered_wheels == 0:
            '''
            nothing to do, the diameter is calculted in calculatePoweredWheelInfo
            '''
        else:
            # this should be made to scale down to 1 and then I can reduce the logic here

            max_error = 0.1
            if inaccurate:
                max_error = 1

            turns = self.powered_wheel.get_turns(cord_usage=self.get_cord_usage())

            # find the ratio we need from the chain wheel to the minute wheel
            turnsPerHour = turns / (self.runtime_hours * self.minute_wheel_ratio)

            desiredRatio = 1 / turnsPerHour

            # consider tweaking this in future
            moduleReduction = 1.1
            # copy-pasted from calculateRatios and tweaked
            allGearPairCombos = []

            for p in range(pinion_min, pinion_max):
                for w in range(wheel_min, wheel_max):
                    allGearPairCombos.append([w, p])
            # [ [[w,p],[w,p],[w,p]] ,  ]
            allTrains = []

            allTrainsLength = 1
            for i in range(self.powered_wheels):
                allTrainsLength *= len(allGearPairCombos)

            allcomboCount = len(allGearPairCombos)
            if self.powered_wheels == 1:
                for pair_0 in range(allcomboCount):
                    allTrains.append([allGearPairCombos[pair_0]])
            elif self.powered_wheels == 2:
                for pair_0 in range(allcomboCount):
                    for pair_1 in range(allcomboCount):
                        allTrains.append([allGearPairCombos[pair_0], allGearPairCombos[pair_1]])
            else:
                raise ValueError("Unsupported number of chain wheels")
            all_ratios = []
            totalTrains = len(allTrains)
            for c in range(totalTrains):
                totalRatio = 1
                intRatio = False
                totalTeeth = 0
                # trying for small wheels and big pinions
                totalWheelTeeth = 0
                totalPinionTeeth = 0
                weighting = 0
                lastSize = 0
                fits = True
                for p in range(len(allTrains[c])):
                    # loop through each wheel/pinion pair
                    ratio = allTrains[c][p][0] / allTrains[c][p][1]
                    if ratio == round(ratio):
                        intRatio = True
                        break
                    totalRatio *= ratio
                    totalTeeth += allTrains[c][p][0] + allTrains[c][p][1]
                    totalWheelTeeth += allTrains[c][p][0]
                    totalPinionTeeth += allTrains[c][p][1]
                    # module * number of wheel teeth - proportional to diameter
                    size = math.pow(moduleReduction, p) * allTrains[c][p][0]
                    # prefer smaller wheels
                    weighting += size
                    # allow more space between the wheels than with the normal wheels ebcause of the chunky bit out the back of the chain wheel
                    # if p > 0 and size > lastSize * 0.875:
                    # # if p > 0 and size > lastSize * 0.9:
                    #     # this wheel is unlikely to physically fit
                    #     fits = False
                    #     break
                    # TODO does it fit next to the minute wheel?
                    # if p > 0 and size > self.trains[0][0][0]
                    lastSize = size
                    # TODO is the first wheel big enough to take the powered wheel?

                error = desiredRatio - totalRatio
                # weighting = totalWheelTeeth
                if self.powered_wheels == 2:
                    # prefer similar sizes
                    # weighting+=abs(allTrains[c][0][0] - allTrains[c][1][0])*0.5

                    if prefer_large_second_wheel:
                        # prefer second wheel more teeth (but not so much that it makes it huge)
                        weighting += (allTrains[c][0][0] - allTrains[c][1][0]) * 0.5  # *0.5
                    else:
                        # similar sized if possible
                        weighting += abs(allTrains[c][0][0] - allTrains[c][1][0])
                    '''
                    Want large first pinion (for strength) and a smaller second wheel (so it will fit)
                    '''
                    # first_pinion_teeth = allTrains[c][0][1]
                    # weighting -= (first_pinion_teeth*8)# + allTrains[c][0][0] - allTrains[c][1][0]

                train = {"ratio": totalRatio, "train": allTrains[c], "error": abs(error), "ratio": totalRatio, "teeth": totalWheelTeeth, "weighting": weighting}
                if fits and abs(error) < max_error and not intRatio:
                    all_ratios.append(train)

            all_ratios.sort(key=lambda x: x["weighting"])
            # print(all_ratios[0])
            # if not prefer_small:
            #     all_ratios.sort(key=lambda x: x["error"] - x["teeth"] / 1000)
            # else:
            #     # aim for small wheels where possible
            #     all_ratios.sort(key=lambda x: x["error"] + x["teeth"] / 100)
            if len(all_ratios) == 0:
                raise ValueError("Unable to generate gear ratio for powered wheel")
            self.chain_wheel_ratios = all_ratios[0]["train"]
            print("chosen powered wheels: ", self.chain_wheel_ratios)
            print("")

    def set_chain_wheel_ratio(self, pinionPairs):
        '''
        Instead of autogenerating, manually configure ratios
        '''
        if type(pinionPairs[0]) == int:
            # backwards compatibility with old clocks that assumed only one chain wheel was supported
            self.chain_wheel_ratios = [pinionPairs]
        else:
            self.chain_wheel_ratios = pinionPairs

    def is_weight_on_the_right(self):
        '''
        returns true if the weight dangles from the right side of the chain wheel (as seen from the front)
        '''

        clockwise = self.powered_wheel.is_clockwise()
        chainAtFront = not self.chain_at_back

        # XNOR
        clockwiseFromFront = not (clockwise != chainAtFront)

        return clockwiseFromFront

    def calculate_powered_weight_wheel_info(self, default_powered_wheel_diameter=20):
        '''
        Calculate best diameter and direction of ratchet for weight driven wheels
        if powered wheel was already provided to going train and there is more than one powered wheel, default_powered_wheel_diameter is ignored
        '''




        if self.powered_wheels == 0:
            # no choice but to set diameter to what fits with the drop and hours
            self.powered_wheel_circumference = self.get_cord_usage() / (self.runtime_hours * self.minute_wheel_ratio)
            self.powered_wheel_diameter = self.powered_wheel_circumference / math.pi

        else:
            # set the diameter to the minimum so the chain wheel gear ratio is as low as possible (TODO - do we always want this?)
            if self.powered_wheel is not None:
                self.powered_wheel_diameter = self.powered_wheel.diameter
            else:
                self.powered_wheel_diameter = default_powered_wheel_diameter

            self.powered_wheel_circumference = self.powered_wheel_diameter * math.pi

        # true for no chainwheels
        anticlockwise = self.chain_at_back

        for i in range(self.powered_wheels):
            anticlockwise = not anticlockwise

        self.powered_wheel_clockwise = not anticlockwise

    def gen_chain_wheels2(self, chain, ratchetThick=7.5, arbourD=3, loose_on_rod=True, prefer_small=False, preferedDiameter=-1, fixing_screws=None, ratchetOuterThick=5):

        diameter = preferedDiameter
        if diameter < 0:
            diameter = PocketChainWheel2.get_min_diameter()
        self.calculate_powered_weight_wheel_info(diameter)

        if self.huygens_maintaining_power:
            # there is no ratchet with this setup
            ratchetThick = 0
            # TODO check holeD?

        self.powered_wheel = PocketChainWheel2(ratchet_thick=ratchetThick, arbor_d=arbourD, loose_on_rod=loose_on_rod,
                                               power_clockwise=self.powered_wheel_clockwise, chain=chain, max_diameter=self.powered_wheel_diameter, fixing_screws=fixing_screws, ratchetOuterThick=ratchetOuterThick)

        self.calculate_powered_wheel_ratios(prefer_small=prefer_small)

    def gen_chain_wheels(self, ratchetThick=7.5, holeD=3.4, wire_thick=1.25, inside_length=6.8, width=5, tolerance=0.15, screwThreadLength=10, prefer_small=False):
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

        self.calculate_powered_weight_wheel_info(PocketChainWheel.get_min_diameter())

        if self.huygens_maintaining_power:
            # there is no ratchet with this setup
            ratchetThick = 0
            # TODO check holeD?

        self.powered_wheel = PocketChainWheel(ratchet_thick=ratchetThick, power_clockwise=self.powered_wheel_clockwise, max_circumference=self.powered_wheel_circumference, wire_thick=wire_thick, inside_length=inside_length, width=width,
                                              holeD=holeD, tolerance=tolerance, screwThreadLength=screwThreadLength)

        self.calculate_powered_wheel_ratios(prefer_small=prefer_small)

    def gen_cord_wheels(self, ratchet_thick=7.5, rod_metric_thread=3, cord_coil_thick=10, use_key=False, cord_thick=2, style=GearStyle.ARCS, prefered_diameter=-1, loose_on_rod=True, prefer_small=False,
                        ratchet_diameter=-1, traditional_ratchet=True, min_wheel_teeth=20, cap_diameter=-1):
        '''
        If preferred diameter is provided, use that rather than the min diameter

        switching to defaulting to tradition ratchet as the old ratchet has proven not to hold up long term, I'm hoping the tradition ratchet with a long click will be better
        '''
        diameter = prefered_diameter
        if diameter < 0:
            diameter = CordWheel.get_min_diameter()

        if self.huygens_maintaining_power:
            raise ValueError("Cannot use cord wheel with huygens maintaining power")

        # if cap_diameter < 0:
        #     cap_diameter = ratchet_diameter

        self.calculate_powered_weight_wheel_info(diameter)
        self.powered_wheel = CordWheel(self.powered_wheel_diameter, ratchet_thick=ratchet_thick, power_clockwise=self.powered_wheel_clockwise,
                                       rod_metric_size=rod_metric_thread, thick=cord_coil_thick, use_key=use_key, cord_thick=cord_thick, style=style, loose_on_rod=loose_on_rod,
                                       cap_diameter=cap_diameter, traditional_ratchet=traditional_ratchet, ratchet_diameter=ratchet_diameter)
        self.calculate_powered_wheel_ratios(prefer_small=prefer_small, wheel_min=min_wheel_teeth, prefer_large_second_wheel=False)  # prefer_large_second_wheel=False,

    def gen_rope_wheels(self, ratchetThick=3, arbor_d=3, ropeThick=2.2, wallThick=1.2, preferedDiameter=-1, use_steel_tube=True, o_ring_diameter=2, prefer_small=False):

        diameter = preferedDiameter
        if diameter < 0:
            diameter = RopeWheel.get_min_diameter()

        self.calculate_powered_weight_wheel_info(diameter)

        if self.huygens_maintaining_power:
            # there is no ratchet with this setup
            ratchetThick = 0

        if use_steel_tube:
            hole_d = STEEL_TUBE_DIAMETER
        else:
            hole_d = arbor_d + LOOSE_FIT_ON_ROD

        self.powered_wheel = RopeWheel(diameter=self.powered_wheel_diameter, hole_d=hole_d, ratchet_thick=ratchetThick, arbor_d=arbor_d,
                                       rope_diameter=ropeThick, power_clockwise=self.powered_wheel_clockwise, wall_thick=wallThick, o_ring_diameter=o_ring_diameter, need_bearing_standoff=True)

        self.calculate_powered_wheel_ratios(prefer_small=prefer_small)

    def gen_spring_barrel(self, spring=None, key_bearing=None, pawl_angle=math.pi / 2, click_angle=-math.pi / 2, ratchet_at_back=True,
                          style=GearStyle.ARCS, chain_wheel_ratios=None, base_thick=8, fraction_of_max_turns=0.5, wheel_min_teeth=60, wall_thick=12, extra_barrel_height=2,
                          ratchet_thick=8):

        self.powered_wheel = SpringBarrel(spring=spring, key_bearing=key_bearing, clockwise=self.powered_wheels % 2 == 0,
                                          pawl_angle=pawl_angle, click_angle=click_angle, ratchet_at_back=ratchet_at_back, style=style, base_thick=base_thick,
                                          fraction_of_max_turns=fraction_of_max_turns, wall_thick=wall_thick, extra_barrel_height=extra_barrel_height, ratchet_thick=ratchet_thick)
        '''
        smiths: 66 teeth on barrel, 10 on next pinion
        76 teeth on next wheel, 13 on next pinion

        barrel rotates 4.35 times a week (168hours)
        '''
        if chain_wheel_ratios is None:
            self.calculate_powered_wheel_ratios(wheel_min=wheel_min_teeth, inaccurate=True)
        else:
            self.chain_wheel_ratios = chain_wheel_ratios

    def set_train(self, train):
        '''
        Set a single train as the preferred train to generate everythign else
        '''
        self.trains = [train]

    def print_info(self, weight_kg=0.35, for_runtime_hours=168):
        print(self.trains[0])

        print("pendulum length: {}m period: {}s".format(self.pendulum_length_m, self.pendulum_period))
        print("escapement time: {}s teeth: {}".format(self.escapement_time, self.escapement.teeth))
        if PowerType.is_weight(self.powered_wheel.type):
            print("Powered wheel diameter: {}".format(self.powered_wheel_diameter))
        # print("cicumference: {}, run time of:{:.1f}hours".format(self.circumference, self.get_run_time()))
        power_ratio = self.minute_wheel_ratio
        power_wheel_ratios = [1]
        if self.powered_wheels > 0:
            # TODO if - for some reason - the minuteWheelRatio isn't 1, this logic needs checking
            print(self.chain_wheel_ratios)
            # how many turns per turn of the minute wheel
            power_ratio = 1
            for pair in self.chain_wheel_ratios:
                power_ratio *= pair[0] / pair[1]
            # the wheel/pinion tooth count
            power_wheel_ratios = self.chain_wheel_ratios

        if self.powered_wheel.type == PowerType.SPRING_BARREL:
            max_barrel_turns = self.powered_wheel.get_max_barrel_turns()

            turns = for_runtime_hours / power_ratio

            rewinding_turns = self.powered_wheel.get_key_turns_to_rewind_barrel_turns(turns)
            print("Over a runtime of {:.1f}hours the spring barrel ({:.1f}mm diameter) will make {:.1f} full rotations which is {:.1f}% of the maximum number of turns ({:.1f}) and will take {:.1f} key turns to wind back up"
                  .format(for_runtime_hours, self.powered_wheel.barrel_diameter, turns, 100.0 * turns / max_barrel_turns, max_barrel_turns, rewinding_turns))
            return

        runtime_hours = self.powered_wheel.get_run_time(power_ratio, self.get_cord_usage())

        drop_m = self.max_weight_drop / 1000
        power = weight_kg * GRAVITY * drop_m / (runtime_hours * 60 * 60)
        power_uW = power * math.pow(10, 6)
        # for reference, the hubert hurr eight day cuckoo is aproximately 34uW
        print("runtime: {:.1f}hours using {:.1f}m of cord/chain for a weight drop of {}. Chain wheel multiplier: {:.1f} ({})".format(runtime_hours, self.get_cord_usage() / 1000, self.max_weight_drop, power_ratio, power_wheel_ratios))
        print("With a weight of {}kg, this results in an average power usage of {:.1f}uW".format(weight_kg, power_uW))

        if len(self.arbors) > 0:
            self.get_arbour_with_conventional_naming(0).print_screw_length()
            self.get_arbour_with_conventional_naming(0).powered_wheel.print_screw_length()
        else:
            print("Generate gears to get screw information")

        if self.powered_wheel.type == PowerType.CORD:
            # because there are potentially multiple layers of cord on a cordwheel, power lever can vary enough for the clock to be viable when wound and not halfway through its run time!
            # seen this on clock 10!

            (rotations, layers, cordPerRotationPerLayer, cordPerLayer) = self.powered_wheel.get_cord_turning_info(self.max_weight_drop * (2 if self.use_pulley else 1))
            # cord per rotation divided by chainRatio, gives speed in mm per hour, we want in m/s to calculate power
            effective_weight = weight_kg / (2 if self.use_pulley else 1)
            min_weight_speed = (cordPerRotationPerLayer[0] / power_ratio) / (60 * 60 * 1000)
            min_power = effective_weight * GRAVITY * min_weight_speed * math.pow(10, 6)
            max_weight_speed = (cordPerRotationPerLayer[-1] / power_ratio) / (60 * 60 * 1000)
            max_power = effective_weight * GRAVITY * max_weight_speed * math.pow(10, 6)
            print("Cordwheel power varies from {:.1f}uW to {:.1f}uW".format(min_power, max_power))

    def gen_gears(self, module_size=1.5, rod_diameters=None, module_reduction=0.5, thick=6, powered_wheel_thick=-1, escape_wheel_max_d=-1,
                  powered_wheel_module_increase=None, pinion_thick_multiplier=2.5, style="HAC", powered_wheel_pinion_thick_multiplier=2, thickness_reduction=1,
                  ratchet_screws=None, pendulum_fixing=PendulumFixing.FRICTION_ROD, module_sizes=None, stack_away_from_powered_wheel=False, pinion_extensions=None,
                  powered_wheel_module_sizes=None, lanterns=None, pinion_thick_extra=-1, override_powered_wheel_distance=-1, powered_wheel_thicks = None):
        '''
        What's provided to teh constructor and what's provided here is a bit scatty and needs tidying up. Might be worth breaking some backwards compatibility to do so
        Also this assumes a *lot* about the layout, which really should be in the control of the plates
        Might even be worth making it entirely user-configurable which way the gears stack as layouts get more complicated, rather than assume we can calculate the best


        escapeWheelMaxD - if <0 (default) escape wheel will be as big as can fit
        if > 1 escape wheel will be as big as can fit, or escapeWheelMaxD big, if that is smaller
        if > 0 and < 1, escape wheel will be this fraction of the previous wheel

        stack_away_from_powered_wheel - experimental, put each wheel in "front" of the previous, usually we interleave gears to minimise plate distance,
         but we might want to minimise height instead. Required for compact plates with 4 wheels

        chain_module_increase - increase module size from the minute wheel down to the chainwheel by this multiplier

        alernatively can specify chain wheel modules directly:
        powered_wheel_module_sizes = [powered_wheel_0_module, powered_wheel_1_module...]

        lanterns, array of WHEEL-pinion pair indexes, anything in this list is a lantern pinion (eg if [0] the first pinion is a lantern pinion)

        pinion_thick_extra: newer idea, override pinion_thick_multiplier and chain_wheel_pinion_thick_multiplier.
         Just add this value to the thickness of the previous wheel for each pinion thickness

         bodge: chain_wheel_pinion_thick_multiplier will override pinion_thick_extra if chain_wheel_pinion_thick_multiplier is positive


         pinion_extensions is indexed from the minute wheel
        '''

        if rod_diameters is None:
            rod_diameters = [3 for i in range(self.powered_wheels + self.wheels + 1)]

        if lanterns is None:
            lanterns = []

        # lantern_indexed = [l in lanterns for l in range(self.powered_wheels + self.wheels)]

        if powered_wheel_module_increase is None:
            powered_wheel_module_increase = (1 / module_reduction)

        if powered_wheel_module_sizes is None:
            powered_wheel_module_sizes = []
            for i in range(self.powered_wheels):
                powered_wheel_module_sizes.append(module_size * powered_wheel_module_increase ** (self.powered_wheels - i))

        if powered_wheel_thick < 0:
            powered_wheel_thick = thick

        if powered_wheel_thicks is None:
            powered_wheel_thicks = [powered_wheel_thick * thickness_reduction ** i for i in range(self.powered_wheels)]

        # can manually override the pinion extensions on a per arbor basis - used for some of the compact designs. Ideally I should automate this, but it feels like
        # a bit problem so solve so I'm offering the option to do it manually for now
        if pinion_extensions is None:
            pinion_extensions = {}

        self.pendulum_fixing = pendulum_fixing
        arbours = []
        # ratchetThick = holeD*2
        # thickness of just the wheel
        self.gear_wheel_thick = thick
        # thickness of arbour assembly
        # wheel + pinion (3*wheel) + pinion top (0.5*wheel)



        # self.gearPinionLength=thick*3
        # self.chainGearPinionLength = chainWheelThick*2.5

        # thought - should all this be part of the Gear or WheelAndPinion class?
        gear_pinion_end_cap_thick = max(thick * 0.25, 0.8)
        # on the assumption that we're using lantern pinions for strenght, make them chunky
        lantern_pinion_end_cap_thick = thick
        # self.gearTotalThick = self.gearWheelThick + self.gearPinionLength + self.gearPinionEndCapLength
        # self.chainGearTotalThick

        if module_sizes is None:
            module_sizes = [module_size * math.pow(module_reduction, i) for i in range(self.wheels)]

        print("module_sizes: {}".format(module_sizes))
        # the module of each wheel is slightly smaller than the preceeding wheel
        # pairs = [WheelPinionPair(wheel[0],wheel[1],module_sizes[i]) for i,wheel in enumerate(self.trains[0]["train"])]
        pairs = [WheelPinionPair(wheel[0], wheel[1], module_sizes[i], lantern=(i + self.powered_wheels) in lanterns) for i, wheel in enumerate(self.trains[0]["train"])]

        # print(module_sizes)
        # make the escape wheel as large as possible, by default
        escape_wheel_by_arbor_extension = (stack_away_from_powered_wheel or self.wheels == 3) and self.escape_wheel_pinion_at_front == self.chain_at_back
        if escape_wheel_by_arbor_extension or self.wheels-1 in pinion_extensions:
            #assume if a pinion extension has been added that the escape wheel doesn't clash with pinion.
            #this logic is awful and needs overhauling massively.
            # avoid previous arbour extension (BODGE - this has no knowledge of how thick that is)
            escape_wheel_diameter = (pairs[len(pairs) - 1].centre_distance - rod_diameters[-2] - 2) * 2
        else:
            # avoid previous pinion
            escape_wheel_diameter = (pairs[len(pairs) - 1].centre_distance - pairs[len(pairs) - 2].pinion.get_max_radius() - 2) * 2

        # we might choose to override this
        if escape_wheel_max_d > 1 and escape_wheel_diameter > escape_wheel_max_d:
            escape_wheel_diameter = escape_wheel_max_d
        elif escape_wheel_max_d > 0 and escape_wheel_max_d < 1:
            # treat as fraction of previous wheel
            escape_wheel_diameter = pairs[len(pairs) - 1].wheel.get_max_radius() * 2 * escape_wheel_max_d

        # little bit of a bodge
        self.escapement.set_diameter(escape_wheel_diameter)

        # chain wheel imaginary pinion (in relation to deciding which way the next wheel faces) is opposite to where teh chain is
        chain_wheel_imaginary_pinion_at_front = self.chain_at_back

        # this was an attempt to put the second wheel over the top of the powered wheel, if it fits, but now there are so many different setups I'm just disabling it
        second_wheel_r = pairs[1].wheel.get_max_radius()
        first_wheel_r = pairs[0].wheel.get_max_radius() + pairs[0].pinion.get_max_radius()
        powered_wheel_encasing_radius = self.powered_wheel.get_encasing_radius()  # .ratchet.outsideDiameter/2
        space = first_wheel_r - powered_wheel_encasing_radius
        # logic is flawed and doesn't work with multiple powered wheels (eg 8 day spring)
        if second_wheel_r < space - 3:
            # the second wheel can actually fit on the same side as the ratchet
            chain_wheel_imaginary_pinion_at_front = not chain_wheel_imaginary_pinion_at_front
            print("Space to fit minute wheel in front of chain wheel - should result in smaller plate distance. check to ensure it does not clash with power mechanism")

        # this is a bit messy. leaving it alone for now, but basically we manually choose which way to have the escape wheel but by default it's at front (if the chain is also at the front)
        escape_wheel_pinion_at_front = self.escape_wheel_pinion_at_front

        # only true if an odd number of wheels (note this IS wheels, not with chainwheels, as the minute wheel is always clockwise)
        escape_wheel_clockwise = self.wheels % 2 == 1

        escape_wheel_clockwise_from_pinion_side = escape_wheel_pinion_at_front == escape_wheel_clockwise

        pinion_at_front = chain_wheel_imaginary_pinion_at_front

        self.powered_wheel_arbors = []
        self.powered_wheel_pairs = []
        # chain_module_base = module_size
        chain_module_multiplier = 1
        # fits if we don't have any chain wheels, otherwise run the loop
        fits = self.powered_wheels == 0

        if override_powered_wheel_distance > 0 and self.powered_wheels == 1:
            # probably retrofitting a part
            print("overriding distance between powered wheel and second wheel")
            # fits=True
            # TODO this doesn't work, but I'm not sure what I've missed.
            chain_module = override_powered_wheel_distance / ((self.chain_wheel_ratios[0][0] + self.chain_wheel_ratios[0][1]) / 2)

            self.powered_wheel_pairs = [WheelPinionPair(self.chain_wheel_ratios[0][0], self.chain_wheel_ratios[0][1], chain_module, lantern=0 in lanterns)]
            print("chain module: ", chain_module)

        loop = 0
        has_lantern = False
        while not fits and loop < 100:
            loop += 1
            self.powered_wheel_pairs = []
            for i in range(self.powered_wheels):
                # TODO review this, should be able to just calculate needed module rather than use a loop? do i still need this at all?
                # chain_module = chain_module_base * powered_wheel_module_increase ** (self.powered_wheels - i)
                chain_module = powered_wheel_module_sizes[i] * chain_module_multiplier
                # chain_wheel_space = chainModule * (self.chainWheelRatios[i][0] + self.chainWheelRatios[i][1]) / 2

                # #check if the chain wheel will fit next to the minute wheel
                # if i == 0 and chain_wheel_space < minuteWheelSpace:
                #     # calculate module for the chain wheel based on teh space available
                #     chainModule = 2 * minuteWheelSpace / (self.chainWheelRatios[0] + self.chainWheelRatios[1])
                #     print("Chain wheel module increased to {} in order to fit next to minute wheel".format(chainModule))
                # self.chainWheelPair = WheelPinionPair(self.chainWheelRatios[0], self.chainWheelRatios[1], chainModule)
                # only supporting one at the moment, but open to more in the future if needed
                pair = WheelPinionPair(self.chain_wheel_ratios[i][0], self.chain_wheel_ratios[i][1], chain_module, lantern=i in lanterns)
                self.powered_wheel_pairs.append(pair)
                if i in lanterns:
                    has_lantern=True

            minute_wheel_space = pairs[0].wheel.get_max_radius()
            if self.powered_wheels == 1:
                minute_wheel_space += self.powered_wheel.get_rod_radius()
            else:
                minute_wheel_space += rod_diameters[1]

            last_chain_wheel_space = self.powered_wheel_pairs[-1].centre_distance
            # last_chain_wheel_space = self.powered_wheel_pairs[-1].wheel.get_max_radius()
            if not self.powered_wheel.loose_on_rod:
                # TODO properly work out space on rod behind pwoered wheel - should be calculated by the powered wheel
                # need space for the steel rod as the wheel itself is loose on the threaded rod
                minute_wheel_space += 1

            if last_chain_wheel_space < minute_wheel_space:
                # calculate module for the chain wheel based on teh space available
                chain_module_multiplier *= 1.01
                print("Chain wheel module multiplier to {} in order to fit next to minute wheel".format(chain_module_multiplier))
                if has_lantern:
                    raise RuntimeError("Trying to change module size for a lantern pinion, will likely not support available steel rods")
            else:
                fits = True

        power_at_front = not self.chain_at_back
        first_chainwheel_clockwise = self.powered_wheels % 2 == 0
        for i in range(self.powered_wheels):

            if i == 0:
                clockwise_from_powered_side = first_chainwheel_clockwise and power_at_front
                # the powered wheel
                self.powered_wheel_arbors.append(Arbor(powered_wheel=self.powered_wheel, wheel=self.powered_wheel_pairs[i].wheel, wheel_thick=powered_wheel_thicks[i], arbor_d=self.powered_wheel.arbor_d,
                                                       distance_to_next_arbour=self.powered_wheel_pairs[i].centre_distance, style=style, ratchet_screws=ratchet_screws,
                                                       use_ratchet=not self.huygens_maintaining_power, pinion_at_front=power_at_front, clockwise_from_pinion_side=clockwise_from_powered_side))
            else:
                # just a bog standard wheel and pinion TODO take into account direction of stacking?!? urgh, this will do for now
                clockwise_from_pinion_side = first_chainwheel_clockwise == (i % 2 == 0)
                pinion_thick = self.powered_wheel_arbors[i - 1].wheel_thick * powered_wheel_pinion_thick_multiplier
                if pinion_thick_extra > 0 and powered_wheel_pinion_thick_multiplier < 0:
                    pinion_thick = self.powered_wheel_arbors[i - 1].wheel_thick + pinion_thick_extra
                cap_thick = gear_pinion_end_cap_thick
                wheel_thick = powered_wheel_thicks[i]
                if self.powered_wheel_pairs[i - 1].pinion.lantern:
                    cap_thick = wheel_thick
                self.powered_wheel_arbors.append(Arbor(wheel=self.powered_wheel_pairs[i].wheel, wheel_thick=wheel_thick, arbor_d=rod_diameters[i], pinion=self.powered_wheel_pairs[i - 1].pinion,
                                                       pinion_thick=pinion_thick, end_cap_thick=cap_thick,
                                                       distance_to_next_arbour=self.powered_wheel_pairs[i].centre_distance, style=style, pinion_at_front=pinion_at_front,
                                                       clockwise_from_pinion_side=clockwise_from_pinion_side))
                if i == 1:
                    # negate flipping the direction of the pinion
                    pinion_at_front = not pinion_at_front
            pinion_at_front = not pinion_at_front

        for i in range(self.wheels):
            clockwise = i % 2 == 0
            clockwise_from_pinion_side = clockwise == pinion_at_front

            pinion_extension = 0
            if i in pinion_extensions:
                pinion_extension = pinion_extensions[i]

            if i == 0:
                # == minute wheel ==
                if self.powered_wheels == 0:
                    # the minute wheel also has the chain with ratchet
                    arbour = Arbor(powered_wheel=self.powered_wheel, wheel=pairs[i].wheel, wheel_thick=powered_wheel_thick, arbor_d=self.powered_wheel.arbor_d, distance_to_next_arbour=pairs[i].centre_distance,
                                   style=style, pinion_at_front=not self.chain_at_back, ratchet_screws=ratchet_screws, use_ratchet=not self.huygens_maintaining_power,
                                   clockwise_from_pinion_side=not self.chain_at_back)
                else:
                    # just a normal gear

                    if self.powered_wheels > 0:
                        pinion_thick = self.powered_wheel_arbors[-1].wheel_thick * powered_wheel_pinion_thick_multiplier
                    else:
                        pinion_thick = self.powered_wheel_arbors[-1].wheel_thick * pinion_thick_multiplier
                    if pinion_thick_extra > 0:
                        pinion_thick = self.powered_wheel_arbors[-1].wheel_thick + pinion_thick_extra
                    # occasionally useful on spring clocks to keep the minute wheel from bumping into the back part of a lantern wheel
                    # just make the pinino longer rather than actually add a pinion_extension
                    # pinion_thick += pinion_extension

                    cap_thick = lantern_pinion_end_cap_thick if self.powered_wheel_pairs[-1].pinion.lantern else gear_pinion_end_cap_thick
                    arbour = Arbor(wheel=pairs[i].wheel, pinion=self.powered_wheel_pairs[-1].pinion, arbor_d=rod_diameters[i + self.powered_wheels], wheel_thick=thick, pinion_thick=pinion_thick, end_cap_thick=cap_thick,
                                   distance_to_next_arbour=pairs[i].centre_distance, style=style, pinion_at_front=pinion_at_front, clockwise_from_pinion_side=clockwise_from_pinion_side, pinion_extension=pinion_extension)

                arbours.append(arbour)
                if stack_away_from_powered_wheel:
                    # only the minute wheel behind teh chain wheel
                    pinion_at_front = not pinion_at_front

            elif i < self.wheels - 1:
                ## == wheel-pinion pair ==
                pinion_thick = arbours[-1].wheel_thick * pinion_thick_multiplier
                if self.powered_wheels == 0 and i == 1:
                    # this pinion is for the chain wheel
                    pinion_thick = arbours[-1].wheel_thick * powered_wheel_pinion_thick_multiplier
                # if i == self.wheels-2 and self.has_second_hand_on_last_wheel() and stack_away_from_powered_wheel:
                #     #extend this pinion a bit to keep the giant pinion on the escape wheel from clashing
                #     #old bodge logic, use pinion_extensions instead now
                #     pinionExtension = pinion_thick*0.6

                if pinion_thick_extra > 0:
                    pinion_thick = arbours[-1].wheel_thick + pinion_thick_extra
                # intermediate wheels
                # no need to worry about front and back as they can just be turned around
                arbours.append(Arbor(wheel=pairs[i].wheel, pinion=pairs[i - 1].pinion, arbor_d=rod_diameters[i + self.powered_wheels], wheel_thick=thick * (thickness_reduction ** i),
                                     pinion_thick=pinion_thick, end_cap_thick=gear_pinion_end_cap_thick, pinion_extension=pinion_extension,
                                     distance_to_next_arbour=pairs[i].centre_distance, style=style, pinion_at_front=pinion_at_front, clockwise_from_pinion_side=clockwise_from_pinion_side))
            else:
                # == escape wheel ==
                # Using the manual override to try and ensure that the anchor doesn't end up against the back plate (or front plate)
                # automating would require knowing how far apart the plates are, which we don't at this point, so just do it manually
                pinion_at_front = self.escape_wheel_pinion_at_front
                pinion_thick = arbours[-1].wheel_thick * pinion_thick_multiplier

                if pinion_thick_extra > 0:
                    pinion_thick = arbours[-1].wheel_thick + pinion_thick_extra
                # last pinion + escape wheel, the escapment itself knows which way the wheel will turn
                # escape wheel has its thickness controlled by the escapement, but we control the arbour diameter
                arbours.append(Arbor(escapement=self.escapement, pinion=pairs[i - 1].pinion, arbor_d=rod_diameters[i + self.powered_wheels], pinion_thick=pinion_thick, end_cap_thick=gear_pinion_end_cap_thick,
                                     distance_to_next_arbour=self.escapement.get_distance_beteen_arbours(), style=style, pinion_at_front=pinion_at_front, clockwise_from_pinion_side=escape_wheel_clockwise_from_pinion_side,
                                     pinion_extension=pinion_extension))
            if not stack_away_from_powered_wheel:
                pinion_at_front = not pinion_at_front

        # anchor is the last arbour
        # "pinion" is the direction of the extended arbour for fixing to pendulum
        # this doesn't need arbourD or thickness as this is controlled by the escapement
        arbours.append(Arbor(escapement=self.escapement, pinion_at_front=self.penulum_at_front, clockwise_from_pinion_side=escape_wheel_clockwise, arbor_d=rod_diameters[self.powered_wheels + self.wheels]))

        self.wheelPinionPairs = pairs
        self.arbors = arbours

        # self.chainWheelArbours = []
        # if self.chainWheels > 0:
        #     self.chainWheelArbours=[getWheelWithRatchet(self.ratchet,self.chainWheelPair.wheel,holeD=holeD, thick=chainWheelThick, style=style)]

    def get_arbour_with_conventional_naming(self, i):
        '''
        Use the traditional naming of the chain wheel being zero
        if -ve, count from the anchor backwards (like array indexing in python, so -1 is the anchor, -2 is the escape wheel)
        '''
        if i < 0:
            i = i + len(self.arbors) + len(self.powered_wheel_arbors)
        return self.get_arbor(i - self.powered_wheels)

    def get_arbor(self, i):
        '''
        +ve is in direction of the anchor
        0 is minute wheel
        -ve is in direction of power ( so last chain wheel is -1, first chain wheel is -chainWheels)

        ended up switching to more conventional numbering with the powered wheel as zero - works more easily for looping through all arbors
        this is now deprecated and I don't think it's used anywhere anymore
        '''

        if i >= 0:
            return self.arbors[i]
        else:
            return self.powered_wheel_arbors[self.powered_wheels + i]

#
# def generic_gear_train_calculator(module_reduction=0.85, min_pinion_teeth=10, max_wheel_teeth=100, pinion_max_teeth=20, wheel_min_teeth=50,
#                      max_error=0.1, loud=False, penultimate_wheel_min_ratio=0, favour_smallest=True, allow_integer_ratio=False, constraint=None):
#     '''
#     Returns and stores a list of possible gear ratios, sorted in order of "best" to worst
#     module reduction used to calculate smallest possible wheels - assumes each wheel has a smaller module than the last
#     penultimate_wheel_min_ratio - check that the ratio of teeth on the last wheel is greater than the previous wheel's teeth * penultimate_wheel_min_ratio (mainly for trains
#     where the second hand is on the penultimate wheel rather than the escape wheel - since we prioritise smaller trains we can end up with a teeny tiny escape wheel)
#
#     now favours a low standard deviation of number of teeth on the wheels - this should stop situations where we get a giant first wheel and tiny final wheels (and tiny escape wheel)
#     This is slow, but seems to work well
#     '''
#
#     pinion_min = min_pinion_teeth
#     pinion_max = pinion_max_teeth
#     wheel_min = wheel_min_teeth
#     wheel_max = max_wheel_teeth
#
#     '''
#     https://needhamia.com/clock-repair-101-making-sense-of-the-time-gears/
#     “With an ‘integer ratio’, the same pairs of teeth (gear/pinion) always mesh on each revolution.
#      With a non-integer ratio, each pass puts a different pair of teeth in mesh. (Some fractional
#      ratios are also called a ‘hunting ratio’ because a given tooth ‘hunts’ [walks around] the other gear.)”
#
#      "So it seems clock designers prefer non-whole-number gear ratios to even out the wear of the gears’ teeth. "
#
#      seems reasonable to me
#     '''
#     all_gear_pair_combos = []
#     all_seconds_wheel_combos = []
#
#     target_time = 60 * 60 / self.minute_wheel_ratio
#
#     for p in range(pinion_min, pinion_max):
#         for w in range(wheel_min, wheel_max):
#             all_gear_pair_combos.append([w, p])
#
#     # use a much wider range
#     if self.support_second_hand and not self.has_seconds_hand_on_escape_wheel():
#         for p in range(pinion_min, pinion_max * 3):
#             for w in range(pinion_max, wheel_max * 4):
#                 # print(p, w, self.escapement_time / (p/w))
#                 if self.escapement_time / (p / w) == 60:
#                     all_seconds_wheel_combos.append([w, p])
#     if loud:
#         print("allGearPairCombos", len(all_gear_pair_combos))
#     # [ [[w,p],[w,p],[w,p]] ,  ]
#     all_trains = []
#
#     print(all_seconds_wheel_combos)
#
#     all_trains_length = 1
#     for i in range(self.wheels):
#         all_trains_length *= len(all_gear_pair_combos)
#     allcombo_count = len(all_gear_pair_combos)
#
#     def add_combos(pair_index=0, previous_pairs=None):
#         if previous_pairs is None:
#             previous_pairs = []
#         # one fewer pair than wheels, and if we're the last pair then add the combos, else recurse
#         final_pair = pair_index == self.wheels - 2
#         valid_combos = all_gear_pair_combos
#         if self.support_second_hand and not self.has_seconds_hand_on_escape_wheel() and final_pair:
#             # using a different set of combinations that will force the penultimate wheel to rotate at 1 rpm
#             valid_combos = all_seconds_wheel_combos
#         for pair in range(len(valid_combos)):
#             if loud and pair % 10 == 0 and pair_index == 0:
#                 print("\r{:.1f}% of calculating train options".format(100 * pair / allcombo_count), end='')
#
#             all_pairs = previous_pairs + [valid_combos[pair]]
#             if final_pair:
#                 all_trains.append(all_pairs)
#             else:
#                 add_combos(pair_index + 1, all_pairs)
#
#     # recursively create an array of all gear trains to test - should work with any number of wheels >= 2
#     add_combos()
#
#     if loud:
#         print("\nallTrains", len(all_trains))
#     all_times = []
#     total_trains = len(all_trains)
#     for c in range(total_trains):
#         if loud and c % 100 == 0:
#             print("\r{:.1f}% of trains evaluated".format(100 * c / total_trains), end='')
#         total_ratio = 1
#         int_ratio = False
#         total_teeth = 0
#         # trying for small wheels and big pinions
#         total_wheel_teeth = 0
#         total_pinion_teeth = 0
#         weighting = 0
#         last_size = 0
#         fits = True
#         for p in range(len(all_trains[c])):
#             ratio = all_trains[c][p][0] / all_trains[c][p][1]
#             if ratio == round(ratio):
#                 int_ratio = True
#                 if not allow_integer_ratio:
#                     break
#             total_ratio *= ratio
#             total_teeth += all_trains[c][p][0] + all_trains[c][p][1]
#             total_wheel_teeth += all_trains[c][p][0]
#             total_pinion_teeth += all_trains[c][p][1]
#             # module * number of wheel teeth - proportional to diameter
#             size = math.pow(module_reduction, p) * all_trains[c][p][0]
#             if favour_smallest:
#                 weighting += size
#             else:
#                 # still don't want to just choose largest by mistake
#                 weighting += size * 0.3
#             if p > 0 and size > last_size * 0.9:
#                 # this wheel is unlikely to physically fit
#                 fits = False
#                 break
#             last_size = size
#         # favour evenly sized wheels
#         wheel_tooth_counts = [pair[0] for pair in all_trains[c]]
#         weighting += np.std(wheel_tooth_counts)
#         if self.support_second_hand and not self.has_seconds_hand_on_escape_wheel():
#             # want to check last wheel won't be too tiny (would rather add more teeth than increase the module size for asthetics)
#             if all_trains[c][-1][0] < all_trains[c][-2][0] * penultimate_wheel_min_ratio:
#                 # only continue if the penultimate wheel has more than half the number of teeth of the wheel before that
#                 continue
#
#         total_time = total_ratio * self.escapement_time
#         error = target_time - total_time
#         if int_ratio:
#             # avoid if we can
#             weighting += 100
#
#
#
#         train = {"time": total_time, "train": all_trains[c], "error": abs(error), "ratio": total_ratio, "teeth": total_wheel_teeth, "weighting": weighting}
#
#
#
#         if fits and abs(error) < max_error:  # and not int_ratio:
#
#             if constraint is not None:
#                 if not constraint(train):
#                     continue
#                 else:
#                     print("constraint met", train)
#
#             all_times.append(train)
#
#     if loud:
#         print("")
#
#     all_times.sort(key=lambda x: x["error"])
#     # print(allTimes)
#
#     self.trains = all_times
#
#     if len(all_times) == 0:
#         raise RuntimeError("Unable to calculate valid going train")
#     print(all_times[0])
#     return all_times

class SlideWhistleTrain:
    '''
    Going to write this completely independantly of GoingTrain, but with the idea of re-writing GoingTrain later using this to test out neater ways to do it
    and maybe some sort of base class for calculating gear trains
    '''

    def __init__(self, powered_wheel, fan, wheels=3):
        # going to be a spring to develop this, but might eventually be any other source of power if it ends up in a clock
        #think it's much easier to just provide this in the constructor than the mess in goingtrain
        self.powered_wheel = powered_wheel
        self.fan = fan
        self.wheels = wheels
        self.trains = []

    def calculate_ratios(self, module_reduction=1, min_pinion_teeth=9, max_wheel_teeth=200, pinion_max_teeth=10, wheel_min_teeth=100,
                         max_error=10, loud=False, cam_rpm = 1, fan_rpm=250):
        all_gear_pair_combos = []

        for p in range(min_pinion_teeth, pinion_max_teeth):
            for w in range(wheel_min_teeth, max_wheel_teeth):
                all_gear_pair_combos.append([w, p])
        # [ [[w,p],[w,p],[w,p]] ,  ]
        all_trains = []
        all_trains_length = 1
        for i in range(self.wheels):
            all_trains_length *= len(all_gear_pair_combos)
        allcombo_count = len(all_gear_pair_combos)

        def add_combos(pair_index=0, previous_pairs=None):
            if previous_pairs is None:
                previous_pairs = []
            # one fewer pair than wheels, and if we're the last pair then add the combos, else recurse
            final_pair = pair_index == self.wheels - 2
            valid_combos = all_gear_pair_combos
            for pair in range(len(valid_combos)):
                if loud and pair % 10 == 0 and pair_index == 0:
                    print("\r{:.1f}% of calculating train options".format(100 * pair / allcombo_count), end='')

                all_pairs = previous_pairs + [valid_combos[pair]]
                if final_pair:
                    all_trains.append(all_pairs)
                else:
                    add_combos(pair_index + 1, all_pairs)

        # recursively create an array of all gear trains to test - should work with any number of wheels >= 2
        add_combos()

        desired_ratio = fan_rpm / cam_rpm

        all_times = []
        total_trains = len(all_trains)
        if loud:
            print("\nTotal trains:", total_trains)
        for c in range(total_trains):
            if loud and c % 100 == 0:
                print("\r{:.1f}% of trains evaluated".format(100 * c / total_trains), end='')
            total_ratio = 1
            total_teeth = 0
            # trying for small wheels and big pinions
            total_wheel_teeth = 0
            total_pinion_teeth = 0
            weighting = 0
            last_size = 0
            fits = True
            for p in range(len(all_trains[c])):
                ratio = all_trains[c][p][0] / all_trains[c][p][1]
                if ratio == round(ratio):
                    break
                total_ratio *= ratio
                total_teeth += all_trains[c][p][0] + all_trains[c][p][1]
                total_wheel_teeth += all_trains[c][p][0]
                total_pinion_teeth += all_trains[c][p][1]
                # module * number of wheel teeth - proportional to diameter
                size = math.pow(module_reduction, p) * all_trains[c][p][0]
                weighting += size

                if p > 0 and size > last_size * 0.9:
                    # this wheel is unlikely to physically fit
                    #TODO actually test this?
                    fits = False
                    break
                last_size = size
            # favour evenly sized wheels
            wheel_tooth_counts = [pair[0] for pair in all_trains[c]]
            weighting += np.std(wheel_tooth_counts)

            #favour smaller
            weighting += (sum(wheel_tooth_counts))*0.1

            error = abs(desired_ratio - total_ratio)

            # print(total_ratio)

            train = {"ratio": total_ratio, "train": all_trains[c], "error": abs(error), "ratio": total_ratio, "teeth": total_wheel_teeth, "weighting": weighting}



            if fits and abs(error) < max_error:  # and not int_ratio:


                all_times.append(train)

        if loud:
            print("")

        all_times.sort(key=lambda x: x["error"])

        self.trains = all_times

        if len(all_times) == 0:
            raise RuntimeError("Unable to calculate valid going train")
        print(all_times[0])

    @staticmethod
    def tidy_list(thelist, expected_length, default_value, default_reduction=0.9):
        '''
        Given a list of modules of thicknesses, tidy up, fill in the gaps, trim.
        replace -1s with expected values and fatten up list to full expected length
        '''
        if thelist is None:
            #none provided, calculate entirely default train
            thelist = [1*default_reduction**i for i in range(expected_length)]

        for i,module in enumerate(thelist):
            #check for any -1s and fill them in
            if module < 0:
                if i ==0:
                    thelist[i] = default_value
                else:
                    thelist[i] = thelist[i-1]*default_reduction


        if len(thelist) < expected_length:
            #only some provided, finish the rest
            for i in range(expected_length - len(thelist)):
                thelist += [thelist[-1]*default_reduction]

        return thelist[:expected_length]

    def generate_gears(self, modules=None, thicknesses=None, rod_diameters=None):
        '''
        modules - list of modules sizes, or -1 for auto. can be shorter than train and rest will be filled in
        thicknesses - list of thicknesses of gears, as per moduels -1 for auto. can be shorter than train and rest will be filled in
        '''

        self.modules = self.tidy_list(modules, expected_length=self.wheels, default_value=1, default_reduction=0.9)
        self.thicknesses = self.tidy_list(thicknesses, expected_length=self.wheels, default_value=5, default_reduction=0.9)
        if rod_diameters is None:
            rod_diameters = [3]*self.wheels