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


class GearTrainBase:
    '''
    Plan - the new generate_arbors mechanism used for the slide whistle is so much cleaner to use and maintain than the old gen_gears, so abstract it out
    and enable it to be shared by multiple types of trains
    '''

    @staticmethod
    def tidy_list(thelist, expected_length, default_value, default_reduction=0.9):
        '''
        Given a list of modules or thicknesses, tidy up, fill in the gaps, trim.
        replace -1s with expected values and fatten up list to full expected length
        '''
        if thelist is None:
            # none provided, calculate entirely default train
            thelist = [default_value * default_reduction ** i for i in range(expected_length)]

        for i, module in enumerate(thelist):
            # check for any -1s and fill them in
            if module < 0:
                if i == 0:
                    thelist[i] = default_value
                else:
                    thelist[i] = thelist[i - 1] * default_reduction

        if len(thelist) < expected_length:
            # only some provided, finish the rest
            for i in range(expected_length - len(thelist)):
                thelist += [thelist[-1] * default_reduction]

        return thelist[:expected_length]

    def __init__(self, total_arbors, default_thickness=5.0, default_module=1.0, default_rod_diameter=3, default_reduction=0.9, default_pinion_thick_extra=3):
        self.total_arbors=total_arbors
        self.default_thickness = default_thickness
        self.default_module = default_module
        self.default_rod_diameter = default_rod_diameter
        self.default_reduction = default_reduction
        self.default_pinion_thick_extra = default_pinion_thick_extra
        self.arbors = []

    def get_all_arbors(self):
        return self.arbors

    def generate_arbors_internal(self, arbor_info):
        raise NotImplementedError("Implement generate_arbors_internal in sub classes")

    def generate_arbors_dicts(self, arbor_info, reduction=-1, pinion_thick_extra=-1):
        '''
        It should have been obvious, but passing a whole load of lists in is a messier way of just passing a list of dicts
        any of the below can be missing and will be automatically filled in as best as possible

        arbor_info =
            [
                {
                "module": float, (for this wheel and the next arbor's pinion)
                "wheel_thick": float,
                "pinion_thick": float,
                "pinion_type": PinionType (for the pinion on this arbor, which engages with the previous wheel)
                "style": GearStyle enum,
                "pinion_faces_forwards": bool,
                "wheel_outside_plates":  SplitArborType, #escapement on front or back only one supported currently. Note that if used, both escape wheel and anchor must have this set the same
                "pinion_extension": float,
                "rod_diameter": float
                },
            ]
        '''

        if pinion_thick_extra < 0:
            pinion_thick_extra = self.default_pinion_thick_extra

        if len(arbor_info) < self.total_arbors:
            for i in range(self.total_arbors - len(arbor_info)):
                arbor_info.append({})


        if reduction < 0:
            reduction = self.default_reduction
        # fill in any missing info
        for i, info in enumerate(arbor_info):
            if "module" not in info:
                if i ==0:
                    info["module"] = self.default_module
                else:
                    info["module"] = arbor_info[i-1]["module"]*reduction

            if "wheel_thick" not in info:
                if i ==0:
                    info["wheel_thick"] = self.default_thickness
                else:
                    info["wheel_thick"] = arbor_info[i-1]["wheel_thick"]*reduction

            if "rod_diameter" not in info:
                info["rod_diameter"] = self.default_rod_diameter

            if "pinion_thick" not in info:
                if i == 0:
                    #no pinion on the great wheel
                    info["pinion_thick"] = -1
                else:
                    #the previous wheel thick + extra
                    info["pinion_thick"] = arbor_info[i-1]["wheel_thick"] + pinion_thick_extra

            if "pinion_type" not in info:
                #previously lantern
                info["pinion_type"] = PinionType.PLASTIC

            if "style" not in info:
                if i == 0:
                    info["style"] = None
                else:
                    info["style"] = arbor_info[i-1]["style"]

            if "pinion_faces_forwards" not in info:
                if i <= 1:
                    #default to first two facing forwards
                    info["pinion_faces_forwards"] = True
                else:
                    #otherwise flip backwards and forwards
                    info["pinion_faces_forwards"] = not arbor_info[i-1]["pinion_faces_forwards"]
                print(i,"info[\"pinion_faces_forwards\"]", info["pinion_faces_forwards"])

            if "wheel_outside_plates" not in info:
                info["wheel_outside_plates"] = SplitArborType.NORMAL_ARBOR

            if "pinion_extension" not in info:
                info["pinion_extension"] = 0

        self.generate_arbors_internal(arbor_info)



    def generate_arbors_lists(self, modules=None, thicknesses=None, rod_diameters=None, pinion_thicks=None, lanterns=None, styles=None, pinions_face_forwards=None,
                              reduction=None, wheel_outside_plates=None, pinion_extensions=None):
        '''
        New interface idea - lists of all features. However I've realised it probably makes more sense to instead have a list of dicts, so this will be deprecated

        Base function to take potentially incomplete lists of requirements and fill them all out, then call the class-specific functions

        modules - list of modules sizes, or -1 for auto. Can be shorter than train and rest will be filled in
        thicknesses - list of thicknesses of gears, as per modules -1 for auto. can be shorter than train and rest will be filled in
        rod diameters - list of diameters for the rods, or -1 for auto. Can be shorter than train and rest will be filled in
        pinion_thicks - list of sizes of pinion, or -1 for auto. Can be shorter than train and rest will be filled in
        pinion_extensions - list of extensions for each pinion
        lanterns - list of indexes. Any arbor in this list will have a lantern pinion. (should this be a boolean list to be consistent?)
        styles - list of styles. If a non-list is presented it will be used for all arbors
        pinions_face_forwards - list of True, False or None for auto Can be shorter than train and rest will be filled in
        reduction - for any non-specified thicknesses or modules, multiply previous thickness or module by this to get the next
        wheel_outside_plates - list of SplitArborType. only splitting escapement currently supported, but API ready for any
        '''


        if reduction is None:
            reduction = self.default_reduction

        self.modules = self.tidy_list(modules, expected_length=self.total_arbors, default_value=self.default_module, default_reduction=reduction)
        self.thicknesses = self.tidy_list(thicknesses, expected_length=self.total_arbors, default_value=self.default_thickness, default_reduction=reduction)
        self.rod_diameters = self.tidy_list(rod_diameters, expected_length=self.total_arbors, default_value=self.default_rod_diameter, default_reduction=1)
        self.pinion_extensions = pinion_extensions#self.tidy_list(pinion_extensions, expected_length=self.total_arbors, default_value=0, default_reduction=1)
        self.lanterns = lanterns
        if self.lanterns is None:
            self.lanterns = []

        self.wheel_outside_plates = wheel_outside_plates

        if self.pinion_extensions is None:
            self.pinion_extensions = []
        if len(self.pinion_extensions) < self.total_arbors:
            for i in range(self.total_arbors - len(self.pinion_extensions)):
                self.pinion_extensions += [0]

        if self.wheel_outside_plates is None:
            self.wheel_outside_plates = []

        if len(self.wheel_outside_plates) < self.total_arbors:
            for i in range(self.total_arbors - len(self.wheel_outside_plates)):
                self.wheel_outside_plates += [SplitArborType.NORMAL_ARBOR]

        self.styles = styles

        if not isinstance(self.styles, list):
            #support different style per arbor
            self.styles = [self.styles] * self.total_arbors

        #can't use tidy_list without major refactor to support non-numbers, easier to just do this to expand a short styles list:
        if len(self.styles) < self.total_arbors:
            for i in range(self.total_arbors - len(self.styles)):
                self.styles += [self.styles[-1]]

        #first "pinion" is the side of the powered wheel with the power mechanism, be it barrel or sprocket or anything else
        #auto filled in will just alternate true and false through the train
        self.pinions_face_forwards = pinions_face_forwards
        if self.pinions_face_forwards is None:
            #Everything I've made so far has the next wheel stack behind the powered wheel, so that's the default here
            self.pinions_face_forwards = [True, True]
        if len(self.pinions_face_forwards) < self.total_arbors:
            self.pinions_face_forwards += [None] * (self.total_arbors - len(self.pinions_face_forwards))
        for i, pinion_face_forward in enumerate(self.pinions_face_forwards):
            if pinion_face_forward is None:
                self.pinions_face_forwards[i] = not self.pinions_face_forwards[i-1]

        self.pinion_thicks = pinion_thicks
        if self.pinion_thicks is None:
            self.pinion_thicks = [min(wheel_thick+3, wheel_thick*2) for wheel_thick in self.thicknesses]
        else:
            if len(self.pinion_thicks) < self.total_arbors:
                self.pinion_thicks += [-1]*(self.total_arbors - len(self.pinion_thicks))
            for i, pinion_thick in enumerate(self.pinion_thicks):
                if pinion_thick < 0:
                    wheel_thick = self.thicknesses[i]
                    pinion_thick = min(wheel_thick+3, wheel_thick*2)
                    self.pinion_thicks[i] = pinion_thick

        print(f"Modules: {self.modules}, wheel thicknesses: {self.thicknesses}, rod diameters: {self.rod_diameters}, pinion thicknesses: {self.pinion_thicks}, pinions on front: {self.pinions_face_forwards}")

        arbors = []

        for i in range(self.total_arbors):
            arbors.append({
                "module":self.modules[i],
                "wheel_thick": self.thicknesses[i],
                "rod_diameter": self.rod_diameters[i],
                "pinion_thick": self.pinion_thicks[i],
                "pinion_faces_forwards": self.pinions_face_forwards[i],
                #i-1 because we now put pinino type (eg lantern) with the arbor of the pinion, not the wheel which meshes with that pinion. This is consistent with pinion_thick
                "pinion_type": PinionType.LANTERN if i-1 in self.lanterns else PinionType.PLASTIC,
                "wheel_outside_plates": self.wheel_outside_plates[i],
                "pinion_extension": self.pinion_extensions[i],
                "style": self.styles[i]
            })


        # self.pairs = [WheelPinionPair(pair[0], pair[1], self.modules[i], lantern=i in self.lanterns) for i, pair in enumerate(self.trains[0]["train"])]
        self.generate_arbors_internal(arbors)
    
class GoingTrain(GearTrainBase):
    '''
    This sets which direction the gears are facing and does some work about setting the size of the escape wheel, which is getting increasingly messy
    and makes some assumptions that are no longer true, now there's a variety of power sources and train layouts.

    I propose instead moving this logic over to the plates and therefore out of Arbor and into ArborForPlate.
    Maybe even going as far as this class not generating any actual geometry? just being ratios?

    TODO just provide a powered wheel to the constructor, like the escapement, and get rid of the myriad of gen_x_wheel methods.
    (partially done, with support for cord and spring barrel)

    '''

    def __init__(self, pendulum_period=-1, pendulum_length_m=-1, wheels=3, fourth_wheel=None, escapement_teeth=30, powered_wheels=0, runtime_hours=30, chain_at_back=True, max_weight_drop=1800,
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

        super().__init__(total_arbors=wheels + powered_wheels + 1)
        self.total_wheels = wheels + powered_wheels

        # in seconds
        self.pendulum_period = pendulum_period
        # in metres
        self.pendulum_length_m = pendulum_length_m

        self.set_pendulum_info(pendulum_length_m, pendulum_period)

        # was experimenting with having the minute wheel outside the powered wheel to escapement train - but I think it's a dead
        # end as it will end up with some slop if it's not in the train
        self.minute_wheel_ratio = minute_wheel_ratio

        self.support_second_hand = support_second_hand

        self.huygens_maintaining_power = huygens_maintaining_power
        self.arbors = []


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
        # if zero, the minute hand is directly driven by the chain, otherwise, how many gears from minute hand to chain wheel
        self.powered_wheels = powered_wheels

        if self.powered_wheel is not None:
            self.powered_by = self.powered_wheel.type
            self.powered_wheel.configure_direction(power_clockwise=self.powered_wheels % 2 == 0)
            if PowerType.is_weight(self.powered_by):
                self.powered_wheel.configure_weight_drop(weight_drop_mm=max_weight_drop, pulleys = 1 if use_pulley else 0)
        else:
            self.powered_by = PowerType.NOT_CONFIGURED


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

    def set_pendulum_info(self, pendulum_length_m=-1, pendulum_period=-1):
        if pendulum_length_m < 0 and pendulum_period > 0:
            # calulate length from period
            self.pendulum_length_m = getPendulumLength(pendulum_period)
        elif pendulum_period < 0 and pendulum_length_m > 0:
            self.pendulum_period = getPendulumPeriod(pendulum_length_m)
        else:
            raise ValueError("Must provide either pendulum length or perioud, not neither or both")
        print("Pendulum length {}cm and period {}s".format(self.pendulum_length_m * 100, self.pendulum_period))

    def has_seconds_hand_on_escape_wheel(self):
        # not sure this should work with floating point, but it does...
        return self.escapement_time == 60

    def has_second_hand_on_last_wheel(self):

        last_pair = self.get_gear_train()[-1]
        return self.escapement_time / (last_pair[1] / last_pair[0]) == 60

    def get_gear_train(self):
        '''
        [[wheel teeth, pinion teeth], ...]
        '''
        return self.trains[0]["train"]

    def recalculate_pendulum_period(self):
        '''
        Recalculte the pendulum period from the train. Useful if the train was calculated with a large error
        (which enables a smaller set of gears to be calculated when pendulum period doesn't need to be exact)

        engineering period of there and back again
        '''
        train = self.get_gear_train()

        total_wheel_teeth_prod = math.prod([pair[0] for pair in train])
        total_pinion_teeth_prod = math.prod([pair[1] for pair in train])

        total_ratio = total_wheel_teeth_prod / total_pinion_teeth_prod

        #total_time = total_ratio * self.escapement_time

        #escape wheel rotates one hour * total_ratio times per hour
        escape_wheel_seconds = 60*60/total_ratio

        pendulum_period = escape_wheel_seconds / self.escapement.teeth

        self.set_pendulum_info(pendulum_period=pendulum_period)

        return pendulum_period


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

            #ensure we don't choose a slightly dodgy one over a better one (unless we've got a large max error in which case this was deliberate)
            if max_error < 0.1:
                weighting += 100* abs(error)


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

        all_times.sort(key=lambda x: x["weighting"])
        # print(all_times)

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
                                       prefer_large_second_wheel=True, tooth_ratio=-1):
        '''
        Calcualte the ratio of the chain wheel based on the desired runtime and chain drop
        used to prefer largest wheel, now is hard coded to prefer smallest.

        size ratio: first wheel teeth / second wheel teeth, so we can calculate sizes that are useful

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
                    if tooth_ratio > 0:
                        weighting +=abs(tooth_ratio - allTrains[c][0][0]/allTrains[c][1][0])*100
                    else:
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

    def set_powered_wheel_ratios(self, pinionPairs):
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
        if self.powered_wheel is not None:
            self.powered_wheel.configure_direction(self.powered_wheel_clockwise)

    '''
    note - the gen_x_wheel methods are deprecated. Provide the power mehcanism straight into the constructor and then either set or calculation the ratios
    with set_powered_wheel_ratios or calculate_powered_wheel_ratios
    '''
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
                                               power_clockwise=self.powered_wheel_clockwise, chain=chain, max_diameter=self.powered_wheel_diameter, fixing_screws=fixing_screws, ratchet_outer_thick=ratchetOuterThick)

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
            diameter = CordBarrel.get_min_diameter()

        if self.huygens_maintaining_power:
            raise ValueError("Cannot use cord wheel with huygens maintaining power")

        # if cap_diameter < 0:
        #     cap_diameter = ratchet_diameter

        self.calculate_powered_weight_wheel_info(diameter)
        bearing = get_bearing_info(15) if use_key else get_bearing_info(3)
        self.powered_wheel = CordBarrel(self.powered_wheel_diameter, ratchet_thick=ratchet_thick, power_clockwise=self.powered_wheel_clockwise,
                                        rod_metric_size=rod_metric_thread, thick=cord_coil_thick, use_key=use_key, cord_thick=cord_thick, style=style, loose_on_rod=loose_on_rod,
                                        cap_diameter=cap_diameter, traditional_ratchet=traditional_ratchet, ratchet_diameter=ratchet_diameter, bearing=bearing)
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
            hole_d = STEEL_TUBE_DIAMETER_CUTTER
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
        # if PowerType.is_weight(self.powered_wheel.type):
        #     print("Powered wheel diameter: {}".format(self.powered_wheel_diameter))
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
            # so, on second thoughts, I'm just plain wrong here? it's always going to be the same number of turns as the barrel had made?
            # as it's equivilant to turning the barrel backwards by how far it's just turned.
            rewinding_turns = turns*2# self.powered_wheel.get_key_turns_to_rewind_barrel_turns(turns)
            print("Over a runtime of {:.1f}hours the spring barrel ({:.1f}mm diameter) will make {:.1f} full rotations which is {:.1f}% of the maximum number of turns ({:.1f}) and will take {:.1f} key half turns to wind back up"
                  .format(for_runtime_hours, self.powered_wheel.barrel_diameter, turns, 100.0 * turns / max_barrel_turns, max_barrel_turns, rewinding_turns))
            return

        runtime_hours = self.powered_wheel.get_run_time(power_ratio, self.get_cord_usage())

        drop_m = self.max_weight_drop / 1000
        power = weight_kg * GRAVITY * drop_m / (runtime_hours * 60 * 60)
        power_uW = power * math.pow(10, 6)
        # for reference, the hubert hurr eight day cuckoo is aproximately 34uW
        print("runtime: {:.1f}hours using {:.1f}m of cord/chain for a weight drop of {}. Chain wheel multiplier: {:.1f} ({})".format(runtime_hours, self.get_cord_usage() / 1000, self.max_weight_drop, power_ratio, power_wheel_ratios))
        print("With a weight of {}kg, this results in an average power usage of {:.1f}uW".format(weight_kg, power_uW))

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

    def generate_arbors_internal(self, arbor_infos):
        '''
        replacement for gen_gears. Everything has been specified for each arbor and is customisable via generate_arbors, as inherited from GearTrainBase
        '''

        # this has been assumed for a while
        self.pendulum_fixing = PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS
        arbors = []

        pairs = [WheelPinionPair(wheel[0], wheel[1], arbor_infos[i + self.powered_wheels]["module"], lantern=arbor_infos[i + self.powered_wheels + 1]["pinion_type"].is_lantern()) for i, wheel in enumerate(self.trains[0]["train"])]

        powered_pairs = [WheelPinionPair(wheel[0], wheel[1], arbor_infos[i]["module"], lantern=arbor_infos[i + 1]["pinion_type"].is_lantern()) for i, wheel in enumerate(self.chain_wheel_ratios)]

        all_pairs = powered_pairs + pairs

        # make the escape wheel as large as possible, by default
        escape_wheel_by_arbor_extension = arbor_infos[-2]["pinion_faces_forwards"] == arbor_infos[-3]["pinion_faces_forwards"]
        if escape_wheel_by_arbor_extension or arbor_infos[self.total_wheels - 1]["pinion_extension"] > 0:
            # assume if a pinion extension has been added that the escape wheel doesn't clash with pinion.
            # avoid previous arbour extension (BODGE - this has no knowledge of how thick that is)
            escape_wheel_diameter = (pairs[len(pairs) - 1].centre_distance - arbor_infos[-2]["rod_diameter"] - 2) * 2
        else:
            # avoid previous pinion
            escape_wheel_diameter = (pairs[len(pairs) - 1].centre_distance - pairs[len(pairs) - 2].pinion.get_max_radius() - 2) * 2

        # escapement may or may not accept us changing the diameter based on its own config
        self.escapement.set_diameter(escape_wheel_diameter)

        for i in range(self.total_wheels + 1):



            # works both +ve and -ve from centre wheel
            arbors_from_centre_wheel = abs(self.powered_wheels - i)
            clockwise = arbors_from_centre_wheel % 2 == 0
            clockwise_from_pinion_side = clockwise == arbor_infos[i]["pinion_faces_forwards"]
            powered_wheel = None
            escapement = None
            pinion = None
            wheel = None
            distance_to_next_arbor = -1
            type = ArborType.WHEEL_AND_PINION
            if i == 0:
                powered_wheel = self.powered_wheel
                wheel = all_pairs[i].wheel
                distance_to_next_arbor = all_pairs[i].centre_distance
                type = ArborType.POWERED_WHEEL
            elif i < self.total_wheels - 1:
                # normal wheel-pinion pairs
                pinion = all_pairs[i - 1].pinion
                wheel = all_pairs[i].wheel
                distance_to_next_arbor = all_pairs[i].centre_distance
            elif i == self.total_wheels - 1:
                # escape wheel
                pinion = all_pairs[i - 1].pinion
                escapement = self.escapement
                distance_to_next_arbor = escapement.anchor_centre_distance
                type = ArborType.ESCAPE_WHEEL
            else:
                # anchor
                escapement = self.escapement
                type = ArborType.ANCHOR
            arbor = Arbor(powered_wheel=powered_wheel,
                          wheel=wheel,
                          wheel_thick=arbor_infos[i]["wheel_thick"],
                          arbor_d=arbor_infos[i]["rod_diameter"],
                          pinion=pinion,
                          pinion_thick=arbor_infos[i]["pinion_thick"],
                          end_cap_thick=-1,
                          escapement=escapement,
                          distance_to_next_arbor=distance_to_next_arbor,
                          style=arbor_infos[i]["style"],
                          pinion_at_front=arbor_infos[i]["pinion_faces_forwards"],
                          clockwise_from_pinion_side=clockwise_from_pinion_side,
                          use_ratchet=not self.huygens_maintaining_power,
                          pinion_extension=arbor_infos[i]["pinion_extension"],
                          arbor_split=arbor_infos[i]["wheel_outside_plates"],
                          pinion_type=arbor_infos[i]["pinion_type"],
                          type = type
                          )
            arbors.append(arbor)

        # TODO overhaul so this is always from zero
        self.arbors = arbors[self.powered_wheels:]
        self.powered_wheel_arbors = arbors[:self.powered_wheels]
        self.all_arbors = arbors

    def gen_gears(self, module_size=1.5, rod_diameters=None, module_reduction=0.5, thick=6, powered_wheel_thick=-1, escape_wheel_max_d=-1,
                  powered_wheel_module_increase=None, pinion_thick_multiplier=2.5, style="HAC", powered_wheel_pinion_thick_multiplier=2, thickness_reduction=1,
                  ratchet_screws=None, pendulum_fixing=PendulumFixing.FRICTION_ROD, module_sizes=None, stack_away_from_powered_wheel=False, pinion_extensions=None,
                  powered_wheel_module_sizes=None, lanterns=None, pinion_thick_extra=-1, override_powered_wheel_distance=-1, powered_wheel_thicks = None, escapement_split=SplitArborType.NORMAL_ARBOR):
        '''
        Deprecated - old interface for generating the arbors. It's messy and doesn't provide the ability to override everything. The original intention was to do everything
        automatically but one by one I needed to override little bits and bobs. use generate_arbors_dicts instead

        What's provided to teh constructor and what's provided here is a bit scatty and needs tidying up. Might be worth breaking some backwards compatibility to do so
        Also this assumes a *lot* about the layout, which really should be in the control of the plates
        Might even be worth making it entirely user-configurable which way the gears stack as layouts get more complicated, rather than assume we can calculate the best


        escapement_split - escapement is on the front or back, so the escape wheel isn't attached to its driving pinion (affects some of the calculations this class performs)

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

        if escapement_split == True:
            #backwards compatibility
            escapement_split = SplitArborType.WHEEL_OUT_FRONT
        if escapement_split == False:
            escapement_split = SplitArborType.NORMAL_ARBOR

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
                    raise RuntimeError(f"Trying to change module size for a lantern pinion, will likely not support available steel rods. Minute wheel {minute_wheel_space} last powered wheel {last_chain_wheel_space}")
            else:
                fits = True

        power_at_front = not self.chain_at_back
        first_chainwheel_clockwise = self.powered_wheels % 2 == 0
        for i in range(self.powered_wheels):

            if i == 0:
                clockwise_from_powered_side = first_chainwheel_clockwise and power_at_front
                # the powered wheel
                pinion_type =PinionType.LANTERN if i in lanterns else PinionType.PLASTIC
                self.powered_wheel_arbors.append(Arbor(powered_wheel=self.powered_wheel, wheel=self.powered_wheel_pairs[i].wheel, wheel_thick=powered_wheel_thicks[i], arbor_d=self.powered_wheel.arbor_d,
                                                       distance_to_next_arbor=self.powered_wheel_pairs[i].centre_distance, style=style, ratchet_screws=ratchet_screws,
                                                       use_ratchet=not self.huygens_maintaining_power, pinion_at_front=power_at_front, clockwise_from_pinion_side=clockwise_from_powered_side,
                                                       pinion_type=pinion_type, type=ArborType.POWERED_WHEEL))
            else:
                # just a bog standard wheel and pinion TODO take into account direction of stacking?!? urgh, this will do for now
                clockwise_from_pinion_side = first_chainwheel_clockwise == (i % 2 == 0)
                pinion_thick = self.powered_wheel_arbors[i - 1].wheel_thick * powered_wheel_pinion_thick_multiplier
                if pinion_thick_extra > 0 and powered_wheel_pinion_thick_multiplier < 0:
                    pinion_thick = self.powered_wheel_arbors[i - 1].wheel_thick + pinion_thick_extra
                cap_thick = gear_pinion_end_cap_thick
                wheel_thick = powered_wheel_thicks[i]
                pinion_type = PinionType.PLASTIC
                if self.powered_wheel_pairs[i - 1].pinion.lantern:
                    cap_thick = wheel_thick
                    pinion_type = PinionType.LANTERN
                self.powered_wheel_arbors.append(Arbor(wheel=self.powered_wheel_pairs[i].wheel, wheel_thick=wheel_thick, arbor_d=rod_diameters[i], pinion=self.powered_wheel_pairs[i - 1].pinion,
                                                       pinion_thick=pinion_thick, end_cap_thick=cap_thick,
                                                       distance_to_next_arbor=self.powered_wheel_pairs[i].centre_distance, style=style, pinion_at_front=pinion_at_front,
                                                       clockwise_from_pinion_side=clockwise_from_pinion_side, pinion_type=pinion_type, type=ArborType.WHEEL_AND_PINION))
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
                # == centre wheel ==
                if self.powered_wheels == 0:
                    # the centre wheel also has the chain with ratchet
                    arbour = Arbor(powered_wheel=self.powered_wheel, wheel=pairs[i].wheel, wheel_thick=powered_wheel_thick, arbor_d=self.powered_wheel.arbor_d, distance_to_next_arbor=pairs[i].centre_distance,
                                   style=style, pinion_at_front=not self.chain_at_back, ratchet_screws=ratchet_screws, use_ratchet=not self.huygens_maintaining_power,
                                   clockwise_from_pinion_side=not self.chain_at_back, type=ArborType.POWERED_WHEEL)
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
                    arbour = Arbor(wheel=pairs[i].wheel, pinion=self.powered_wheel_pairs[-1].pinion, arbor_d=rod_diameters[i + self.powered_wheels],
                                   wheel_thick=thick, pinion_thick=pinion_thick, end_cap_thick=cap_thick,distance_to_next_arbor=pairs[i].centre_distance,
                                   style=style, pinion_at_front=pinion_at_front, clockwise_from_pinion_side=clockwise_from_pinion_side, pinion_extension=pinion_extension,
                                   type=ArborType.WHEEL_AND_PINION)

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
                                     distance_to_next_arbor=pairs[i].centre_distance, style=style, pinion_at_front=pinion_at_front, clockwise_from_pinion_side=clockwise_from_pinion_side,
                                     type=ArborType.WHEEL_AND_PINION))
            else:
                # == escape wheel ==
                # Using the manual override to try and ensure that the anchor doesn't end up against the back plate (or front plate)
                # automating would require knowing how far apart the plates are, which we don't at this point, so just do it manually
                pinion_at_front = self.escape_wheel_pinion_at_front
                pinion_thick = arbours[-1].wheel_thick * pinion_thick_multiplier

                if pinion_thick_extra > 0:
                    pinion_thick = arbours[-1].wheel_thick + pinion_thick_extra
                # last pinion + escape wheel, the escapment itself knows which way the wheel will turn
                # escape wheel has its thickness controlled by the escapement, but we control the arbor diameter
                arbours.append(Arbor(escapement=self.escapement, pinion=pairs[i - 1].pinion, arbor_d=rod_diameters[i + self.powered_wheels], pinion_thick=pinion_thick, end_cap_thick=gear_pinion_end_cap_thick,
                                     distance_to_next_arbor=self.escapement.get_distance_beteen_arbours(), style=style, pinion_at_front=pinion_at_front, clockwise_from_pinion_side=escape_wheel_clockwise_from_pinion_side,
                                     pinion_extension=pinion_extension, arbor_split=escapement_split, type=ArborType.ESCAPE_WHEEL))
            if not stack_away_from_powered_wheel:
                pinion_at_front = not pinion_at_front

        # anchor is the last arbour
        # "pinion" is the direction of the extended arbour for fixing to pendulum
        # this doesn't need arbourD or thickness as this is controlled by the escapement
        arbours.append(Arbor(escapement=self.escapement, pinion_at_front=self.penulum_at_front, clockwise_from_pinion_side=escape_wheel_clockwise, arbor_d=rod_diameters[self.powered_wheels + self.wheels],
                             type=ArborType.ANCHOR, arbor_split=escapement_split))

        self.wheelPinionPairs = pairs
        self.arbors = arbours

        # self.chainWheelArbours = []
        # if self.chainWheels > 0:
        #     self.chainWheelArbours=[getWheelWithRatchet(self.ratchet,self.chainWheelPair.wheel,holeD=holeD, thick=chainWheelThick, style=style)]

    def get_arbor_with_conventional_naming(self, i):
        '''
        Use the traditional naming of the chain wheel being zero
        if -ve, count from the anchor backwards (like array indexing in python, so -1 is the anchor, -2 is the escape wheel)
        '''
        if i < 0:
            i = i + len(self.arbors) + len(self.powered_wheel_arbors)
        return self.get_arbor(i - self.powered_wheels)

    def get_all_arbors(self):
        return self.powered_wheel_arbors + self.arbors

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

class SlideWhistleTrain(GearTrainBase):
    '''
    Going to write this completely independently of GoingTrain, but with the idea of re-writing GoingTrain later using this to test out neater ways to do it
    and maybe some sort of base class for calculating gear trains

    Current plan:
     - spring barrel (or other powered wheel)
     - cam wheel
     - bellows driving wheel
     - wheel with pin for stopping mechanism
     - fly

     was considering reverse worm gear for fly, but I'm not sure how easy that will be to 3D print and this way we can get an extra
     wheel ready for a stopping mechanism

     this is pretty much the striking train! likely be able to reuse or unify with striking mechanism in future

     how to calculate good gear ratios?
    '''

    def __init__(self, powered_wheel, fly, arbors=6, cam_index=1):

        '''
        arbor 0: spring barrel
        arbor 1: intermediate wheel
        arbor 2: would be the star wheel in a striking train, turns the cam on teh whistle
        arbor 3: gathering pallet on striking train, here drives the bellows
        arbor 4: warning wheel, provides means to stop the train
        arbor 5: fly
        '''
        super().__init__(total_arbors=arbors)
        # going to be a spring to develop this, but might eventually be any other source of power if it ends up in a clock
        #think it's much easier to just provide this in the constructor than the mess in goingtrain
        self.powered_wheel = powered_wheel
        #original plan was a fan for the airflow, but I now think that a convential bellows and fly might be easier
        self.fly = fly
        self.bellows = None
        # decided that this will be total wheels, not just wheels from the minute wheel this might become a gotcha, or might be worth refactoring the
        # time going train
        #"total_wheels" so we can be consistent with going_train for any shared code.
        # self.total_wheels = wheels
        # self.total_arbors = wheels + 1
        #arbor which holds the cams, all arbors before that are just for power
        self.cam_index = cam_index
        # self.powered_wheels = cam_index
        #debug only
        self.trains = []
        self.arbors = []
        self.gear_train = []

    def calculate_ratios(self, module_reduction=1, min_pinion_teeth=9, max_wheel_teeth=120, pinion_max_teeth=15, wheel_min_teeth=50,
                         max_error=10, loud=False, cam_rpm = 1, fly_rpm=120, runtime=180):

        '''
        TODO also calc power ratios for now this can be helpful info but not directly usable
        '''

        all_gear_pair_combos = []

        total_relevant_wheels = self.total_arbors-self.cam_index

        for p in range(min_pinion_teeth, pinion_max_teeth):
            for w in range(wheel_min_teeth, max_wheel_teeth):
                all_gear_pair_combos.append([w, p])
        # [ [[w,p],[w,p],[w,p]] ,  ]
        all_trains = []
        all_trains_length = 1
        for i in range(total_relevant_wheels):
            all_trains_length *= len(all_gear_pair_combos)
        allcombo_count = len(all_gear_pair_combos)

        def add_combos(pair_index=0, previous_pairs=None):
            if previous_pairs is None:
                previous_pairs = []
            # one fewer pair than wheels, and if we're the last pair then add the combos, else recurse
            final_pair = pair_index == total_relevant_wheels - 2
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

        desired_ratio = fly_rpm / cam_rpm

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
        print(all_times)
        if len(all_times) == 0:
            raise RuntimeError("Unable to calculate valid going train")
        print(all_times[0])
        self.gear_train = all_times[0]

        #TODO power ratios

    def set_ratios(self, train, cam_arbor_to_cam_train):
        '''
        plan is the cam arbor isn't directly connected to the cam but via another pinion and wheel to gear it DOWN
        so we can get the ~25 ratio between cam and bellows pump
        '''
        self.gear_train = train
        self.cam_arbor_to_cam_train = cam_arbor_to_cam_train

        power_ratio = 1
        cam_to_fly_ratio =1
        for pair in train[:self.cam_index]:
            power_ratio*=pair[0]/pair[1]

        for pair in train[self.cam_index:]:
            cam_to_fly_ratio *= pair[0]/pair[1]
        print(f"Power ratio: {power_ratio} cam to fly: {cam_to_fly_ratio}")


    def generate_arbors_internal(self, arbor_infos):

        '''
        arbor_info =
            [
                {
                "module": float, (for this wheel and the next arbor's pinion)
                "wheel_thick": float,
                "pinion_thick": float,
                "pinion_type": PinionType (for the pinion on this arbor, which engages with the previous wheel)
                "style": GearStyle enum,
                "pinion_faces_forwards": bool,
                "wheel_outside_plates":  SplitArborType, #escapement on front or back only one supported currently
                "pinion_extension": float,
                "rod_diameter": float
                },
            ]
        Take the gear ratios calculated in calculate_ratios and generate a list of Arbors - which can be handed to the plates

        '''


        # print(f"Modules: {self.modules}, wheel thicknesses: {self.thicknesses}, rod diameters: {self.rod_diameters}, pinion thicknesses: {self.pinion_thicks}, pinions on front: {self.pinions_face_forwards}")

        self.pairs = [WheelPinionPair(pair[0], pair[1], arbor_infos[i]["module"], lantern=arbor_infos[i+1]["pinion_type"].is_lantern()) for i, pair in enumerate(self.gear_train)]



        #TODO check this works - I'm ignoring chain at back/front like in old going train, just using the first pinion face forward to decide instead.
        clockwise = self.powered_wheel.is_clockwise() and arbor_infos[0]["pinion_faces_forwards"]

        for i in range(self.total_arbors):
            pinion_at_front = arbor_infos[i]["pinion_faces_forwards"]
            print(f"{i}: forwards {arbor_infos[i]['pinion_faces_forwards']}")
            arbor_d = arbor_infos[i]["rod_diameter"]
            powered_wheel = None
            fly=None
            type= ArborType.WHEEL_AND_PINION
            if i == 0:
                powered_wheel = self.powered_wheel
                arbor_d = self.powered_wheel.arbor_d
                pinion = None
                wheel = self.pairs[i].wheel
                distance_to_next_arbour = self.pairs[i].centre_distance
                type = ArborType.POWERED_WHEEL
            elif i == self.total_arbors - 1:
                wheel = None
                pinion = self.pairs[i - 1].pinion
                distance_to_next_arbour = -1
                fly = self.fly
                type = ArborType.FLY
            else:
                pinion = self.pairs[i-1].pinion
                wheel = self.pairs[i].wheel
                distance_to_next_arbour = self.pairs[i].centre_distance

            clockwise_from_powered_side = clockwise == pinion_at_front


            self.arbors.append(Arbor(powered_wheel=powered_wheel, wheel=wheel, pinion=pinion, pinion_thick=arbor_infos[i]["pinion_thick"], wheel_thick=arbor_infos[i]["wheel_thick"], arbor_d=arbor_d,
                                     distance_to_next_arbor=distance_to_next_arbour, style=arbor_infos[i]["style"], pinion_at_front=pinion_at_front,
                                     clockwise_from_pinion_side=clockwise_from_powered_side, fly=fly, type=type, end_cap_thick=-1, pinion_extension=arbor_infos[i]["pinion_extension"],
                                     pinion_type=arbor_infos[i]["pinion_type"]))



class GearLayout2D:

    @staticmethod
    def get_old_gear_train_layout(going_train, layout = GearTrainLayout.VERTICAL, **kwargs):
        '''
        for a quick solution for backwards compatibility
        '''
        # if extra_args is None:
        #     extra_args = {}
        layouts = {
            GearTrainLayout.VERTICAL : GearLayout2D.get_vertical_layout,
            GearTrainLayout.VERTICAL_COMPACT : GearLayout2D.get_compact_vertical_layout,
            GearTrainLayout.COMPACT: GearLayout2D.get_compact_layout,
            GearTrainLayout.COMPACT_CENTRE_SECONDS: GearLayout2DCentreSeconds,
        }
        return layouts[layout](going_train, **kwargs)

    @staticmethod
    def get_vertical_layout(going_train, **kwargs):
        '''
        All wheels in a line upright.
        The old GearTrainLayout.VERTICAL
        '''
        return GearLayout2D(going_train, centred_arbors=[i for i in range(len(going_train.get_all_arbors()))], **kwargs)

    @staticmethod
    def get_compact_vertical_layout(going_train,  all_offset_same_side=True, **kwargs):
        '''
        Most wheels in a line upright, with alternate wheels after the centre wheel offset.
        The old GearTrainLayout.VERTICAL_COMPACT
        '''
        #powered wheels and centre wheel
        centred_arbors = [0, going_train.powered_wheels]

        offset = True
        for i in range(len(going_train.get_all_arbors()) - (going_train.powered_wheels + 1)):
            if not offset:
                centred_arbors.append( i + going_train.powered_wheels + 1)
            offset = not offset

        #always have the pendulum centred
        pendulum_index = len(going_train.get_all_arbors()) - 1
        if pendulum_index not in centred_arbors:
            centred_arbors.append(pendulum_index)
        return GearLayout2D(going_train, centred_arbors, all_offset_same_side=all_offset_same_side, **kwargs)

    @staticmethod
    def get_compact_layout(going_train, start_on_right=True, **kwargs):
        '''
        Roughly the old GearTrainLayout.COMPACT
        '''
        pendulum_index = len(going_train.get_all_arbors()) - 1
        #first powered wheel and centre wheel
        centred_arbors = [0, going_train.powered_wheels]

        if going_train.has_seconds_hand_on_escape_wheel():
            centred_arbors.append(pendulum_index -1)
        if going_train.has_second_hand_on_last_wheel():
            centred_arbors.append(pendulum_index - 2)

        centred_arbors.append(pendulum_index)

        can_ignore_pinions = []
        #assume we can ignore them if the previous pinion has been extended
        for i, arbor in enumerate(going_train.get_all_arbors()[:-1]):
            if arbor.pinion_extension > 0:
                can_ignore_pinions.append(i+1)

        return GearLayout2D(going_train, centred_arbors, can_ignore_pinions=can_ignore_pinions, start_on_right=start_on_right, **kwargs)


    def __init__(self, going_train, centred_arbors=None, can_ignore_pinions=None, can_ignore_wheels=None, start_on_right=True, all_offset_same_side = False, gear_gap = 2,
                 anchor_distance_fudge_mm=0, minimum_anchor_distance=False, override_distances=None):
        '''
        centred_arbors: [list of indexes] which arbors must have x=0. Defaults to powered wheel, centre wheel and anchor
        can_ignore_pinions: [list of indexes] for spacing purposes, usually we make sure wheels avoid other pinions. For this pinion we can safely assume it won't collide
        can_ignore_wheels: [list of indexes] again for spacing purposes, we can ignore the size of these wheels. Probably because it's in front or behind the plates
        anchor_distance_fudge_mm: vertical extra distance to make anchor from escape wheel, bodge to compensate for escapement on front
        '''
        self.going_train = going_train
        self.centred_arbors = centred_arbors
        self.can_ignore_pinions = can_ignore_pinions
        self.can_ignore_wheels = can_ignore_wheels
        self.start_on_right = start_on_right
        self.arbors = self.going_train.get_all_arbors()
        self.all_offset_same_side = all_offset_same_side
        self.anchor_distance_fudge_mm = anchor_distance_fudge_mm
        #if true assume everything has been designed so the anchor just needs to avoid arbor extensions, not wheels
        self.minimum_anchor_distance = minimum_anchor_distance

        self.override_distances=override_distances
        '''
        {
        (from_index, to_index): distance
        }
        '''
        if self.override_distances is None:
            self.override_distances = {}

        #space in mm that must be left between all non-meshing gears
        self.gear_gap = gear_gap

        self.total_arbors = len(self.arbors)

        if self.centred_arbors is None:
            # power source, centre wheel, and anchor
            self.centred_arbors = [0, self.going_train.powered_wheels,self.total_arbors - 1]

        if self.can_ignore_pinions is None:
            # which arbors will be orentated so we don't need to worry about crashing into their pinions
            self.can_ignore_pinions = []

        if self.can_ignore_wheels is None:
            # which arbors will be orentated so we don't need to worry about crashing into their pinions
            self.can_ignore_wheels = []

        if self.total_arbors - 1 not in self.can_ignore_pinions:
            # add the anchor in automatically as it doens't have a pinion
            #TODO review this logic
            self.can_ignore_pinions.append(self.total_arbors - 1)

    def get_angle_between(self, from_index, to_index):
        positions = self.get_positions()
        return math.atan2(positions[to_index][1] - positions[from_index][1], positions[to_index][0] - positions[from_index][0])

    # @staticmethod
    # def check_too_close(positions, arbors, test_position):

    def get_positions(self):
        '''
        an attempt to produce a fully configable layout where we start on the assumption of "a line of gears vertical from hands to anchor, and any gears in between off to one side"
        but we can configure which gears are actually on the vertical line
        '''
        total_arbors = self.going_train.total_arbors
        positions_relative = [(0, 0) for i in range(total_arbors)]
        arbors = self.going_train.get_all_arbors()
        # anchor_index = -1
        # escape_wheel_index = -2
        # penultimate_wheel_index = -3
        # centre_wheel_index = self.going_train.powered_wheels

        on_side = +1 if self.start_on_right else -1

        #keep track of some history for some cases where we need it (example, vertical compact design with sticking out all on the same side)
        last_offset_side = on_side
        last_centred_arbor = 0

        def check_valid_position(check_index, check_until=-1):
            '''
            returns {valid: bool, clash_index: int, clash_distance: float}
            true if should be fine,
            false if it will definitely clash
            probably lots of false negatives and positives...
            '''
            if check_until < 0:
                check_until = check_index
            else:
                #need loop to run this one
                check_until+=1
            result = {
                'valid': True,
                'clash_index': -1,
                'clash_distance': -1.0,
                'clash_min_distance': -1.0
            }
            for i in range(1, check_until):
                if i == check_index - 1 or i == check_index + 1 or i == check_index:
                    #meshes with this one or is this one
                    continue
                # index 0 doesn't have a pinion, just skip it
                distance = get_distance_between_two_points(positions_relative[i], positions_relative[check_index])
                min_distance = arbors[check_index].get_max_radius() + get_pinion_r(i) + self.gear_gap
                if distance < min_distance:
                    result['valid'] = False
                    result['clash_distance'] = distance
                    result['clash_min_distance'] = min_distance
                    result['clash_index'] = i
                    break
            return result




        # proceed vertically from bottom but if there is more than one that is not central, apply more logic
        arbor_index = 0
        while arbor_index < total_arbors - 1:
            #in this loop the current arbor index is the one that has actually been placed successfully, and the "next arbor" is the one we're current trying to place

            def get_pinion_r(index):
                if index in self.can_ignore_pinions:
                    return arbors[index].get_arbor_extension_r()
                else:
                    return arbors[index].pinion.get_max_radius()
            #count how many arbors there are before the next centred arbor
            non_vertical_arbors_next = 0
            for next_arbor_index in range(arbor_index + 1, total_arbors):
                if next_arbor_index not in self.centred_arbors:
                    non_vertical_arbors_next += 1
                else:
                    break
            if non_vertical_arbors_next == 0:
                # next arbor is vertically above us
                distance_to_next_arbor = arbors[arbor_index].distance_to_next_arbor
                if arbor_index + 1 == total_arbors:
                    #this is the distance to the anchor
                    distance_to_next_arbor += self.anchor_distance_fudge_mm
                positions_relative[arbor_index + 1] = (0, positions_relative[arbor_index][1] + distance_to_next_arbor)
                arbor_index += 1
            else:
                # more complicated logic to place 1 or more arbors which aren't centred

                next_centred_index = arbor_index + non_vertical_arbors_next + 1
                distance_to_next_centred_arbor = arbors[arbor_index].get_max_radius() + get_pinion_r(next_centred_index) + self.gear_gap
                if (arbor_index, next_centred_index) in self.override_distances:
                    distance_to_next_centred_arbor = self.override_distances[(arbor_index, next_centred_index)]

                if next_centred_index == total_arbors - 1 and non_vertical_arbors_next == 1:
                    #this is one sticky-out wheel just before the anchor, need to take the anchor itself into account
                    # distance_to_next_centred_arbor = arbors[arbor_index].get_max_radius() + arbors[next_centred_index].get_max_radius()# + self.gear_gap


                    if self.minimum_anchor_distance:
                        #just avoid arbor extension
                        distance_to_next_centred_arbor =  arbors[next_centred_index].get_max_radius() + self.gear_gap + arbors[-1].get_arbor_extension_r()
                    # elif arbors[next_centred_index].type == ArborType.FLY:
                    #     #very hacky to be delving into this logic, but will do until I fix logic with arranging two spare arbors between centred arbors properly (this can clash and doesn't check)
                    #     distance_to_next_centred_arbor = arbors[next_centred_index].get_max_radius() + self.gear_gap + arbors[arbor_index].get_max_radius() + 5
                    else:
                        # old logic, needs review and really should be done properly with trig to work out where the anchor is.
                        distance_to_next_centred_arbor =  arbors[next_centred_index].get_max_radius() + self.gear_gap + arbors[arbor_index].get_max_radius()

                #default, but not always true
                positions_relative[next_centred_index] = (0, positions_relative[arbor_index][1] + distance_to_next_centred_arbor)

                if non_vertical_arbors_next == 1:

                    #simple case, just working out min distance between the current and next centred arbor and offset to the side
                    distance_from_next_to_next_centred = arbors[arbor_index + 1].distance_to_next_arbor

                    positions_relative[arbor_index + 1] = get_point_two_circles_intersect(positions_relative[arbor_index], arbors[arbor_index].distance_to_next_arbor,
                                                                                          positions_relative[next_centred_index], distance_from_next_to_next_centred,
                                                                                          in_direction=(on_side, 0))

                    # this seems to have been producing false positives, and the main problem was avioded by using the old logic for anchor spacing, so removing for now
                    # clash_info = check_valid_position(arbor_index + 1)
                    # if not clash_info['valid']:#last_centred_arbor == arbor_index -2:
                    #     #there was previously only one arbor stuck out the side, so the simple logic will put things too close
                    #     #(probably, designed to catch this case)
                    #     need_extra_space = clash_info['clash_min_distance'] - clash_info['clash_distance']
                    #     #crude, just extend upwards by double this much, should really do the proper trig
                    #     positions_relative[next_centred_index] = (0, positions_relative[arbor_index][1] + distance_to_next_centred_arbor + need_extra_space*2)
                    #     #copypaste from above, think refactoring to re-use would be too much of a faff and hard to follow
                    #     positions_relative[arbor_index + 1] = get_point_two_circles_intersect(positions_relative[arbor_index], arbors[arbor_index].distance_to_next_arbor,
                    #                                                                           positions_relative[next_centred_index], distance_from_next_to_next_centred,
                    #                                                                           in_direction=(on_side, 0))

                    # next arbor is sticking out to the side and the next next arbor is vertically above us
                elif next_centred_index in self.can_ignore_wheels:
                    #taking the idea from teh centre seconds clock, wrap the gears around the current arbor and next centred arbor in a circle around the next centre
                    for i in range(arbor_index+1, next_centred_index):
                        arbor = arbors[i]
                        previous_pos = positions_relative[i - 1][:]
                        previous_arbor = arbors[i - 1]
                        distance_to_previous_wheel = previous_arbor.distance_to_next_arbor
                        distance_to_next_centre = distance_to_next_centred_arbor
                        if i == next_centred_index - 1:
                            # this wheel will mesh with teh seconds pinion
                            distance_to_next_centre = arbor.distance_to_next_arbor
                        # going round the on_side side
                        #TODO this might fail if there are enough gears that we go over the top
                        positions_relative[i] = get_point_two_circles_intersect(positions_relative[next_centred_index], distance_to_next_centre,
                                                                                previous_pos, distance_to_previous_wheel, in_direction=(on_side, 0))

                elif non_vertical_arbors_next in [2,3]:
                    #two horizontally aligned above the last centred wheel, with the one before that off to one side
                    #with only 2 this isn't necessarily the most compact design vertically. TODO
                    # probably the escape wheel
                    last_wheel_index = next_centred_index - 1
                    penultimate_wheel_index = next_centred_index - 2
                    first_wheel_index = arbor_index + 1
                    horizontal_distance = arbors[penultimate_wheel_index].distance_to_next_arbor

                    last_wheel_pinion_r = get_pinion_r(last_wheel_index)
                    #however, it's likely that the pinion is on the front of both the last wheel and the current wheel so we can ignore it for that reason too
                    if arbors[arbor_index].pinion_at_front == arbors[last_wheel_index].pinion_at_front:
                        last_wheel_pinion_r = arbors[last_wheel_index].get_arbor_extension_r()
                    current_to_last = arbors[arbor_index].get_max_radius() + last_wheel_pinion_r + self.gear_gap

                    third_wheel_angle_from_current = math.pi / 2 + on_side * (math.asin((horizontal_distance / 2) / current_to_last))
                    positions_relative[last_wheel_index] = np_to_set(np.add(polar(third_wheel_angle_from_current, current_to_last), positions_relative[arbor_index]))
                    if non_vertical_arbors_next == 2:
                        #penultimate arbor meshes with current arbor
                        positions_relative[penultimate_wheel_index] = get_point_two_circles_intersect(positions_relative[arbor_index], arbors[arbor_index].distance_to_next_arbor,
                                                                                                      positions_relative[last_wheel_index], horizontal_distance, in_direction=(on_side, 0))
                        #check if the penultimate wheel clashes with the next centred, as this CAN happen
                        # clash_info = check_valid_position(penultimate_wheel_index)
                        # if not clash_info['valid']:


                    else:
                        # choosing mirror of escape wheel for penultimate arbor
                        positions_relative[penultimate_wheel_index] = (-positions_relative[last_wheel_index][0], positions_relative[last_wheel_index][1])
                        positions_relative[first_wheel_index] = get_point_two_circles_intersect(positions_relative[arbor_index], arbors[arbor_index].distance_to_next_arbor,
                                                                                                positions_relative[penultimate_wheel_index], arbors[first_wheel_index].distance_to_next_arbor,
                                                                                                in_direction=(on_side, 0))
                    #positions_relative[anchor_index] = (0, positions_relative[escape_wheel_index][1] + math.sqrt(escape_wheel_to_anchor ** 2 - (penultimate_wheel_to_escape_wheel / 2) ** 2))

                    last_wheel_to_next_centred = arbors[last_wheel_index].distance_to_next_arbor

                    last_wheel_x = positions_relative[last_wheel_index][0]
                    positions_relative[next_centred_index] = (0, positions_relative[last_wheel_index][1] + math.sqrt(last_wheel_to_next_centred ** 2 - (last_wheel_x) ** 2))

                    clash_info = check_valid_position(penultimate_wheel_index, check_until=next_centred_index)
                    if not clash_info['valid']:
                        #penultimate wheel crashes into the next centred
                        penultimate_wheel_to_next_centred = get_pinion_r(next_centred_index) + self.gear_gap + arbors[penultimate_wheel_index].get_max_radius()
                        penultimate_wheel_x = positions_relative[penultimate_wheel_index][0]
                        penultimate_wheel_y = positions_relative[penultimate_wheel_index][1]
                        positions_relative[next_centred_index] = (0, penultimate_wheel_y + math.sqrt(penultimate_wheel_to_next_centred ** 2 - penultimate_wheel_x ** 2))

                        positions_relative[last_wheel_index] = get_point_two_circles_intersect(positions_relative[penultimate_wheel_index], arbors[penultimate_wheel_index].distance_to_next_arbor,
                                                                                                      positions_relative[next_centred_index], arbors[last_wheel_index].distance_to_next_arbor, in_direction=(-on_side, 0))


                else:
                    raise NotImplementedError(f"TODO support {non_vertical_arbors_next} non_vertical_arbors_next in GearLayout2D")
                if not self.all_offset_same_side:
                    on_side *= -1
                arbor_index += 1 + non_vertical_arbors_next

                last_centred_arbor = next_centred_index


        return positions_relative

    def get_demo(self):
        demo = cq.Workplane("XY")
        for position,arbor in zip(self.get_positions(), self.arbors):
            demo = demo.add(arbor.get_assembled().translate(position))
        return demo


class GearLayout2DCentreSeconds(GearLayout2D):
    def get_positions(self):
        '''
        Arranging the entire train around the seconds hand, intended to marry well with round clock plate but potentially re-usable for any layout
        some duplication of effort here with COMPACT layout and might be worth abstracting further in the future

        Thoughts - no reason why we couldn't use the standard GearLayout2D with the correct centred_wheels info? it would have to be a bit more flexible
        '''
        all_arbors_count = self.going_train.wheels + self.going_train.powered_wheels + 1
        positions_relative = [(0, 0) for i in range(all_arbors_count)]
        anchor_index = -1
        escape_wheel_index = -2
        penultimate_wheel_index = -3
        if self.going_train.has_seconds_hand_on_escape_wheel():
            second_hand_index = escape_wheel_index

        if self.going_train.has_second_hand_on_last_wheel():
            second_hand_index = penultimate_wheel_index

        # ignoring differences between powered wheels and wheels after the minute wheel for this
        arbors = [self.going_train.get_arbor_with_conventional_naming(i) for i in range(all_arbors_count)]

        # seconds_wheel_radius = arbors[second_hand_index].get_max_radius() + self.gear_gap
        # seconds_pinion_radius =  arbors[second_hand_index].pinion.get_max_radius() + self.gear_gap
        # actually let's assume we only need to avoid the arbor extensions
        seconds_pinion_radius = arbors[second_hand_index].arbor_d + self.gear_gap

        # place seconds directly above powered wheel
        positions_relative[second_hand_index] = (0, seconds_pinion_radius + arbors[0].get_max_radius())

        for i, arbor in enumerate(arbors):
            if i == 0:
                # powered wheel at (0,0)
                continue
            if i == all_arbors_count + second_hand_index:
                # reached the seconds wheel, bail out
                break
            previous_pos = positions_relative[i - 1][:]
            previous_arbor = arbors[i - 1]
            distance_to_previous_wheel = previous_arbor.distance_to_next_arbor
            distance_to_seconds_wheel = arbor.get_max_radius() + seconds_pinion_radius
            if i == all_arbors_count + second_hand_index - 1:
                # this wheel will mesh with teh seconds pinion
                distance_to_seconds_wheel = arbor.distance_to_next_arbor
            # going round the right hand side
            positions_relative[i] = get_point_two_circles_intersect(positions_relative[second_hand_index], distance_to_seconds_wheel,
                                                                    previous_pos, distance_to_previous_wheel, in_direction=(1, 0))

        if self.going_train.wheels > 3:
            offset_escape_wheel = False
            if offset_escape_wheel:
                # got the escape wheel to deal with
                seconds_to_anchor = seconds_pinion_radius + arbors[anchor_index].get_max_radius() + self.gear_gap
                # directly above hands
                positions_relative[anchor_index] = (0, positions_relative[second_hand_index][1] + seconds_to_anchor)
                # on the left hand side
                positions_relative[escape_wheel_index] = get_point_two_circles_intersect(positions_relative[anchor_index], arbors[escape_wheel_index].distance_to_next_arbor,
                                                                                         positions_relative[second_hand_index], arbors[second_hand_index].distance_to_next_arbor,
                                                                                         in_direction=(-1, 0))
            else:
                # actually found that we didn't need to be that compact, so trying stacking vertically instead
                # okay this ends upw ith the pendulum between the pillars, might have to go back to more compact
                positions_relative[escape_wheel_index] = (0, positions_relative[second_hand_index][1] + arbors[second_hand_index].distance_to_next_arbor)
                positions_relative[anchor_index] = (0, positions_relative[escape_wheel_index][1] + arbors[escape_wheel_index].distance_to_next_arbor)
        else:
            # seconds wheel is escape wheel, put anchor directly above
            positions_relative[anchor_index] = (0, positions_relative[second_hand_index][1] + arbors[escape_wheel_index].distance_to_next_arbor)

        return positions_relative


#TODO "circular" layout:
'''

        elif self.gear_train_layout == GearTrainLayout.ROUND:

           
 # TODO decide if we want the train to go in different directions based on which side the weight is
            self.hands_on_side = -1 if self.going_train.is_weight_on_the_right() else 1
            arbours = [self.going_train.get_arbor_with_conventional_naming(arbour) for arbour in range(self.going_train.wheels + self.going_train.powered_wheels)]
            distances = [arbour.distance_to_next_arbor for arbour in arbours]
            maxRs = [arbour.get_max_radius() for arbour in arbours]
            arcAngleDeg = 270

            foundSolution = False
            while (not foundSolution and arcAngleDeg > 180):
                arcRadius = getRadiusForPointsOnAnArc(distances, deg_to_rad(arcAngleDeg))

                # minDistance = max(distances)

                if arcRadius > max(maxRs):
                    # if none of the gears cross the centre, they should all fit
                    # pretty sure there are other situations where they all fit
                    # and it might be possible for this to be true and they still don't all fit
                    # but a bit of playing around and it looks true enough
                    foundSolution = True
                    self.compact_radius = arcRadius
                else:
                    arcAngleDeg -= 1
            if not foundSolution:
                raise ValueError("Unable to calculate radius for gear ring, try a vertical clock instead")

            angleOnArc = -math.pi / 2
            lastPos = polar(angleOnArc, arcRadius)

            for i in range(-self.going_train.powered_wheels, self.going_train.wheels):

                Calculate angle of the isololese triangle with the distance at the base and radius as the other two sides
                then work around the arc to get the positions
                then calculate the relative angles so the logic for finding bearing locations still works
                bit over complicated

                # print("angle on arc: {}deg".format(radToDeg(angleOnArc)))
                nextAngleOnArc = angleOnArc + 2 * math.asin(distances[i + self.going_train.powered_wheels] / (2 * arcRadius)) * self.hands_on_side
                nextPos = polar(nextAngleOnArc, arcRadius)

                relativeAngle = math.atan2(nextPos[1] - lastPos[1], nextPos[0] - lastPos[0])
                if i < 0:
                    self.angles_from_chain[i + self.going_train.powered_wheels] = relativeAngle
                else:
                    self.angles_from_minute[i] = relativeAngle
                lastPos = nextPos
                angleOnArc = nextAngleOnArc
'''


class RollingBallGearLayout(GearLayout2D):
    def __init__(self, going_train, go_right=True):
        '''
        Plan: spring barrel bellow centre wheel, then clutch-driven motion works off to the left and the going train off to the right
        '''

        #don't think this will be used as I'm planning to override get_positions
        #setting last to centred just so that the super class can succeed
        centred = [0, going_train.powered_wheels, going_train.total_arbors-1]
        self.go_right = go_right

        super().__init__(going_train, centred_arbors=centred)

    def get_positions(self):

        #lazy, this will sort out up to the centre wheel successfully
        positions = super().get_positions()
        arbors = self.going_train.get_all_arbors()

        #lazy for now, just go right, might want to consider making this compact
        dir = 1 if self.go_right else -1
        for i in range(self.going_train.powered_wheels+1, self.going_train.total_arbors):
            distance = arbors[i-1].distance_to_next_arbor
            positions[i] = (positions[i-1][0] + distance*dir, positions[i-1][1])

        return positions