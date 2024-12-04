import os

import cadquery as cq
from cadquery import exporters
from .cq_svg import exportSVG

from .types import *
from .utility import *
import string

class Assembly:
    '''
    Produce a fully (or near fully) assembled clock
    likely to be fragile as it will need to delve into the detail of basically everything

    currently assumes pendulum and chain wheels are at front - doesn't listen to their values
    '''
    def __init__(self, plates, hands=None, time_mins=10, time_hours=10, time_seconds=0, pulley=None, weights=None, pretty_bob=None, pendulum=None, with_mat=False):
        self.plates = plates
        self.hands = hands
        self.dial= plates.dial
        self.going_train = plates.going_train
        #+1 for the anchor
        self.arbour_count = self.going_train.powered_wheels + self.going_train.wheels + 1
        self.pendulum = pendulum
        self.motion_works = self.plates.motion_works
        self.time_mins = time_mins
        self.time_hours = time_hours
        self.time_seconds = time_seconds
        self.pulley=pulley
        self.moon_complication = self.plates.moon_complication
        self.plaque = self.plates.plaque
        #weights is a list of weights, first in the list is the main weight and second is the counterweight (if needed)
        self.weights=weights
        if self.weights is None:
            self.weights = []

        #cosmetic parts taht override the defaults

        self.pretty_bob = pretty_bob

        if self.plaque is not None:
            self.plaque_shape = self.plaque.get_plaque().rotate((0,0,0), (0,0,1), rad_to_deg(plates.plaque_angle)).translate(plates.plaque_pos).translate((0,0,-self.plaque.thick))
            self.plaque_text_shape = self.plaque.get_text().rotate((0,0,0),(1,0,0),180).rotate((0, 0, 0), (0, 0, 1), rad_to_deg(plates.plaque_angle)).translate(plates.plaque_pos)

        self.with_mat = with_mat

        if self.with_mat:
            # assume mantel clock

            self.base_of_clock = (0, plates.bottom_pillar_positions[0][1] - plates.bottom_pillar_r, plates.plate_distance / 2 + plates.get_plate_thick(back=True))



        # =============== shared geometry (between clock model and show_clock) ================
        self.front_of_clock_z = self.plates.get_plate_thick(True) + self.plates.get_plate_thick(False) + self.plates.plate_distance

        self.hands_pos = self.plates.bearing_positions[self.going_train.powered_wheels][:2]

        # where the nylock nut and spring washer would be (6mm = two half size m3 nuts and a spring washer + some slack)
        self.motion_works_z_offset = TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - self.motion_works.inset_at_base + self.plates.endshake / 2
        if self.plates.calc_need_motion_works_holder():
            self.motion_works_z_offset = self.plates.motion_works_holder_thick
        self.motion_works_z = self.front_of_clock_z + self.motion_works_z_offset

        self.motion_works_pos = self.plates.hands_position[:]
        self.second_hand_pos = None
        # total, not relative, height because that's been taken into accounr with motionworksZOffset
        self.minute_hand_z = self.front_of_clock_z + self.motion_works_z_offset + self.motion_works.get_cannon_pinion_total_height() - self.hands.thick
        if self.plates.has_seconds_hand():
            self.second_hand_pos = self.plates.get_seconds_hand_position()
            self.second_hand_pos.append(self.front_of_clock_z + self.hands.second_fixing_thick)

        self.minuteAngle = - 360 * (self.time_mins / 60)
        self.hourAngle = - 360 * (self.time_hours + self.time_mins / 60) / 12
        self.secondAngle = -360 * (self.time_seconds / 60)

        if self.plates.dial is not None:
            if self.plates.has_seconds_hand():
                self.second_hand_pos[2] = self.front_of_clock_z + self.plates.dial.support_length + self.plates.dial.thick + self.plates.endshake / 2 + 0.5

            #position of the front centre of the dial
            self.dial_pos = (self.plates.hands_position[0], self.plates.hands_position[1], self.plates.dial_z + self.dial.thick + self.front_of_clock_z)
            #for eyes
            self.wire_to_arbor_fixer_pos = (self.plates.bearing_positions[-1][0], self.plates.bearing_positions[-1][1], self.front_of_clock_z + self.plates.endshake + 1)
        if self.plates.centred_second_hand:
            self.second_hand_pos = self.plates.hands_position.copy()
            self.second_hand_pos.append(self.minute_hand_z - self.motion_works.hour_hand_slot_height)# + self.hands.thick + self.hands.secondFixing_thick)
        if self.plates.pendulum_at_front:

            pendulumRodCentreZ = self.plates.get_plate_thick(back=True) + self.plates.get_plate_thick(back=False) + self.plates.plate_distance + self.plates.pendulum_sticks_out
        else:
            pendulumRodCentreZ = -self.plates.pendulum_sticks_out

        pendulumBobCentreY = self.plates.bearing_positions[-1][1] - self.going_train.pendulum_length_m * 1000

        self.pendulum_bob_centre_pos = (self.plates.bearing_positions[-1][0], pendulumBobCentreY, pendulumRodCentreZ)

        self.ring_pos = [0,0,self.pendulum_bob_centre_pos[2]]
        self.has_ring = False

        self.ratchet_on_plates = None

        if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL:
            #rotated so the screwhole lines up - can't decide where that should be done
            self.ratchet_on_plates = self.going_train.powered_wheel.get_ratchet_gear_for_arbor().rotate((0, 0, 0), (0, 0, 1), 180)\
                .add(self.going_train.powered_wheel.ratchet.get_pawl()).add(self.going_train.powered_wheel.ratchet.get_click())
            if self.plates.little_plate_for_pawl:
                self.ratchet_on_plates = self.ratchet_on_plates.add(self.going_train.powered_wheel.ratchet.get_little_plate_for_pawl()).translate(self.plates.bearing_positions[0][:2])
            if self.going_train.powered_wheel.ratchet_at_back:
                self.ratchet_on_plates = self.ratchet_on_plates.rotate((0,0,0),(0,1,0),180).translate((0,0,-self.plates.endshake/2))
            else:
                self.ratchet_on_plates = self.ratchet_on_plates.translate((0, 0, self.front_of_clock_z + self.plates.endshake/2))

        if self.plates.pendulum_at_front:
            # if the hands are directly below the pendulum pivot point (not necessarily true if this isn't a vertical clock)
            if self.plates.gear_train_layout != GearTrainLayout.ROUND:
                # centre around the hands by default
                self.ring_pos[1] = self.plates.bearing_positions[self.going_train.powered_wheels][1]
                if self.going_train.powered_wheel.type == PowerType.CORD and self.going_train.powered_wheel.use_key:
                    # centre between the hands and the winding key
                    self.ring_pos[1] = (self.plates.bearing_positions[self.going_train.powered_wheels][1] + self.plates.bearing_positions[0][1]) / 2

                # ring is over the minute wheel/hands
                self.ring_pos[2] = pendulumRodCentreZ - self.pendulum.hand_avoider_thick / 2
                self.has_ring = True
        else:
            # pendulum is at the back, hand avoider is around the bottom pillar (unless this proves too unstable) if the pendulum is long enough to need it
            if len(self.plates.bottom_pillar_positions) == 1 and np.linalg.norm(np.subtract(self.plates.bearing_positions[-1][:2], self.plates.bottom_pillar_positions[0][:2])) < self.going_train.pendulum_length_m*1000:
                self.ring_pos = (self.plates.bottom_pillar_positions[0][0], self.plates.bottom_pillar_positions[0][1], -self.plates.pendulum_sticks_out - self.pendulum.hand_avoider_thick / 2)
                self.has_ring = True
        self.weight_positions = []
        if len(self.weights) > 0:
            for i, weight in enumerate(self.weights):
                #line them up so I can see if they'll bump into each other
                weightTopY = self.pendulum_bob_centre_pos[1] + weight.height

                holePositions = self.going_train.powered_wheel.get_chain_positions_from_top()

                #side the main weight is on
                side = 1 if self.going_train.is_weight_on_the_right() else -1

                if i == 1:
                    #counterweight
                    side*=-1

                #in X,Y,Z
                weightPos = None

                for holeInfo in holePositions:
                    if (holeInfo[0][0] > 0) == (side > 0):
                        #hole for the weight
                        weightPos = (holeInfo[0][0], weightTopY - weight.height, self.plates.bearing_positions[0][2] + self.plates.get_plate_thick(back=True) + self.going_train.powered_wheel.get_height() + holeInfo[0][1])
                        self.weight_positions.append(weightPos)

        self.pulley_model = None
        if self.pulley is not None:
            #put the pulley model in position
            chainWheelTopZ = self.plates.bearing_positions[0][2] + self.going_train.get_arbor(-self.going_train.powered_wheels).get_total_thickness() + self.plates.get_plate_thick(back=True) + self.plates.endshake / 2

            chainZ = chainWheelTopZ + self.going_train.powered_wheel.get_chain_positions_from_top()[0][0][1]

            # TODO for two bottom pillars
            pulleyY = self.plates.bottom_pillar_positions[0][1] - self.plates.bottom_pillar_r - self.pulley.diameter

            if self.plates.huygens_maintaining_power:
                pulley = self.pulley.get_assembled().translate((0, 0, -self.pulley.getTotalThick() / 2)).rotate((0, 0, 0), (0, 1, 0), 90)
                self.pulley_model = pulley.translate((self.going_train.powered_wheel.diameter / 2, pulleyY, chainZ + self.going_train.powered_wheel.diameter / 2))
                if self.going_train.powered_wheel.type == PowerType.ROPE:
                    # second pulley for the counterweight
                    self.pulley_model = self.pulley_model.add(pulley.translate((-self.going_train.powered_wheel.diameter / 2, pulleyY, chainZ + self.going_train.powered_wheel.diameter / 2)))
            else:

                self.pulley_model = self.pulley.get_assembled().rotate((0, 0, 0), (0, 0, 1), 90).translate((0, pulleyY, chainZ - self.pulley.getTotalThick() / 2))


        key = self.plates.get_winding_key()
        self.key_model = None
        if key is not None:
            key_model = key.get_assembled()
            #put the winding key on the end of the key shape, should be most simple way of getting it in the right place!
            self.key_model = key_model.translate(
                (self.plates.bearing_positions[0][0],
                 self.plates.bearing_positions[0][1],
                 self.front_of_clock_z + self.plates.key_length )#+ self.plates.endshake / 2 # not sure why I used to add endshake to leave a gap
            )

        self.vanity_plate = None
        if self.plates.has_vanity_plate:
            self.vanity_plate = self.plates.get_vanity_plate(for_printing=False).translate((self.hands_pos[0], self.hands_pos[1], self.front_of_clock_z))


    def printInfo(self):

        for holeInfo in self.going_train.powered_wheel.get_chain_positions_from_top():
            #TODO improve this a bit for cordwheels which have a slot rather than just a hole
            z = self.plates.bearing_positions[0][2] + self.plates.get_plate_thick(back=True) + self.going_train.powered_wheel.get_height() + self.plates.endshake / 2 + holeInfo[0][1]
            print("{} hole from wall = {}mm".format(self.going_train.powered_wheel.type.value, z))

    def get_arbor_rod_lengths(self):
        '''
        Calculate the lengths to cut the steel rods - stop me just guessing wrong all the time!
        '''

        # for i,arbor in enumerate(self.plates.arbors_for_plate):
        #     if arbor.type in [ArborType.WHEEL_AND_PINION, ArborType.ESCAPE_WHEEL] and arbor.arbor.pinion.lantern:
        #         #calculate length of lantern pinion
        #         diameter = arbor.arbor.pinion.trundle_r*2
        #         min_length = arbor.arbor.pinion_thick
        #         #assumed knowledge, the default value of offset in get_lantern_cap is 1. TODO improve this
        #         max_lenth = arbor.arbor.pinion_thick + (arbor.arbor.end_cap_thick - 1) +  (arbor.arbor.wheel_thick - 1)
        #
        #         print("for arbor {} need lantern trundles of diameter {:.2f}mm and length {:.1f}-{:.1f}mm".format(i, diameter, min_length, max_lenth))


        total_plate_thick = self.plates.plate_distance + self.plates.get_plate_thick(True) + self.plates.get_plate_thick(False)
        plate_distance =self.plates.plate_distance
        front_plate_thick = self.plates.get_plate_thick(back=False)
        back_plate_thick = self.plates.get_plate_thick(back=True)



        #how much extra to extend out the bearing
        #used to be 3mm, but when using thinner plates this isn't ideal.
        spare_rod_length_rear=self.plates.endshake*1.5
        #extra length out the front of hands, or front-mounted escapements
        spare_rod_length_in_front=2
        rod_lengths = []
        rod_zs = []
        #for measuring where to put the arbour on the rod, how much empty rod should behind the back of the arbour?
        beyond_back_of_arbours = []



        for i in range(self.arbour_count):

            rod_length = -1

            arbor_for_plate = self.plates.arbors_for_plate[i]
            arbor = arbor_for_plate.arbor
            bearing = arbor_for_plate.bearing
            bearing_thick = bearing.height

            rod_in_front_of_hands = WASHER_THICK_M3 + get_nut_height(arbor.arbor_d) + M3_DOMED_NUT_THREAD_DEPTH - 1

            length_up_to_inside_front_plate = spare_rod_length_rear + bearing_thick + plate_distance

            plain_rod_rear_length = spare_rod_length_rear + bearing_thick# + self.plates.endshake
            #true for nearly all of it
            rod_z = back_plate_thick - (bearing_thick + spare_rod_length_rear)

            #"normal" arbour that does not extend out the front or back
            simple_arbour_length = length_up_to_inside_front_plate + bearing_thick + spare_rod_length_rear
            # hand_arbor_length = length_up_to_inside_front_plate + front_plate_thick + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT + self.plates.motionWorks.get_cannon_pinion_effective_height() + getNutHeight(arbour.arbourD) * 2 + spare_rod_length_in_front
            hand_arbor_length = length_up_to_inside_front_plate + front_plate_thick + (self.minute_hand_z + self.hands.thick - total_plate_thick) + rod_in_front_of_hands

            #trying to arrange all the additions from back to front to make it easy to check
            if arbor.type == ArborType.POWERED_WHEEL:
                powered_wheel = arbor.powered_wheel
                if powered_wheel.type == PowerType.CORD:
                    if powered_wheel.use_key:
                        square_bit_out_front = powered_wheel.key_square_bit_height - (front_plate_thick - powered_wheel.key_bearing.height) - self.plates.endshake / 2
                        rod_length = length_up_to_inside_front_plate + front_plate_thick + square_bit_out_front
                elif powered_wheel.type == PowerType.SPRING_BARREL:
                    rod_length=-1
                else:
                    #assume all other types of powered wheel lack a key and thus are just inside the plates
                    rod_length = simple_arbour_length


            elif self.plates.second_hand and ((arbor.type == ArborType.ESCAPE_WHEEL and self.plates.going_train.has_seconds_hand_on_escape_wheel()) or (
                    i == self.going_train.wheels + self.going_train.powered_wheels - 2 and self.plates.going_train.has_second_hand_on_last_wheel())):
                #this has a second hand on it
                if self.plates.escapement_on_front:
                    raise ValueError("TODO calculate rod lengths for escapement on front")
                elif self.plates.centred_second_hand:
                    #safe to assume mutually exclusive with escapement on front?
                    rod_length = hand_arbor_length + self.hands.second_fixing_thick + CENTRED_SECOND_HAND_BOTTOM_FIXING_HEIGHT
                else:
                    if self.dial is not None and self.dial.has_seconds_sub_dial():
                        #if the rod doesn't go all the way through the second hand
                        hand_thick_accounting = self.hands.second_thick - self.hands.second_rod_end_thick
                        if self.hands.seconds_hand_through_hole:
                            hand_thick_accounting = self.hands.second_thick
                        #rod_length = length_up_to_inside_front_plate + front_plate_thick + self.dial.support_length + self.dial.thick + self.hands.secondFixing_thick + hand_thick_accounting
                        rod_length = length_up_to_inside_front_plate + front_plate_thick + (self.second_hand_pos[2] - total_plate_thick )+ hand_thick_accounting
                    else:
                        #little seconds hand just in front of the plate
                        rod_length = length_up_to_inside_front_plate + front_plate_thick + self.hands.second_fixing_thick + self.hands.second_thick
            elif arbor.type == ArborType.WHEEL_AND_PINION:
                if i == self.going_train.powered_wheels:
                    #minute wheel
                    if self.plates.centred_second_hand:
                        #only goes up to the canon pinion with hand turner
                        minimum_rod_length = (length_up_to_inside_front_plate + front_plate_thick + self.plates.endshake / 2 + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT +
                                              self.plates.motion_works.get_cannon_pinion_pinion_thick() + rod_in_front_of_hands)
                                              # + WASHER_THICK_M3 + getNutHeight(arbour.arbor_d, halfHeight=True) * 2)
                        # if self.plates.dial is not None:
                        #     #small as possible as it might need to fit behind the dial (...not sure what I was talking about here??)
                        #     rod_length = minimum_rod_length + 1.5
                        # else:
                        #     rod_length = minimum_rod_length + spare_rod_length_in_front
                        rod_length = minimum_rod_length
                    else:
                        rod_length = hand_arbor_length
                else:
                    # "normal" arbour
                    rod_length = simple_arbour_length#length_up_to_inside_front_plate + bearing_thick + spare_rod_length_beyond_bearing

            elif arbor.type == ArborType.ESCAPE_WHEEL:
                if self.plates.escapement_on_front:
                    rod_length = length_up_to_inside_front_plate + front_plate_thick + arbor_for_plate.front_anchor_from_plate - arbor.escapement.get_wheel_base_to_anchor_base_z() + arbor.wheel_thick + get_nut_height(round(arbor_for_plate.bearing.inner_d)) + 1
                else:
                    #"normal" arbour
                    rod_length = simple_arbour_length
            elif arbor.type == ArborType.ANCHOR:
                if self.plates.escapement_on_front:
                    holder_thick = self.plates.get_lone_anchor_bearing_holder_thick(self.plates.arbors_for_plate[-1].bearing)
                    out_front = self.plates.get_front_anchor_bearing_holder_total_length() - holder_thick
                    out_back = self.plates.back_plate_from_wall - self.plates.get_plate_thick(standoff=True)
                    extra = spare_rod_length_rear
                    if self.plates.dial is not None:
                        #make smaller since there's not much space on the front
                        extra = self.plates.endshake
                    rod_length = out_back + total_plate_thick + out_front + self.plates.arbors_for_plate[-1].bearing.height*2 + extra*2
                    rod_z = -out_back - self.plates.arbors_for_plate[-1].bearing.height - extra
                elif self.plates.back_plate_from_wall > 0 and not self.plates.pendulum_at_front:
                    rod_length_to_back_of_front_plate = spare_rod_length_rear + bearing_thick + (self.plates.back_plate_from_wall - self.plates.get_plate_thick(standoff=True)) + self.plates.get_plate_thick(back=True) + plate_distance

                    if self.dial is not None and self.dial.has_eyes():
                        rod_length = rod_length_to_back_of_front_plate + front_plate_thick + self.plates.endshake + 1 + self.dial.get_wire_to_arbor_fixer_thick() + 5
                    else:
                        rod_length = rod_length_to_back_of_front_plate + bearing_thick + spare_rod_length_rear
                    rod_z = -self.plates.back_plate_from_wall + (self.plates.get_plate_thick(standoff=True) - bearing_thick - spare_rod_length_rear)
                else:
                    raise ValueError("TODO calculate rod lengths for pendulum on front")
            rod_lengths.append(rod_length)
            rod_zs.append(rod_z)
            beyond_back_of_arbours.append(plain_rod_rear_length)
            if rod_length > 0:
                print("Arbor {} rod (M{}) length: {:.1f}mm with {:.1f}mm plain rod rear of arbor".format(i, self.plates.arbors_for_plate[i].bearing.inner_d, rod_length, plain_rod_rear_length))
            if arbor.pinion is not None and arbor.pinion.lantern:
                diameter = arbor.pinion.trundle_r * 2
                min_length = arbor.pinion_thick + arbor.pinion_extension
                max_lenth = arbor.pinion_thick  + arbor.pinion_extension + (arbor.end_cap_thick - arbor.get_lantern_trundle_offset()) + (arbor.wheel_thick - arbor.get_lantern_trundle_offset())
                print("Arbor {} has a lantern pinion and needs steel rod of diameter {:.2f}mm and length {:.1f}-{:.1f}mm".format(i,  diameter, min_length, max_lenth))


        return rod_lengths, rod_zs

    def get_pendulum_rod_lengths(self):
        '''
        Calculate lengths of threaded rod needed to make the pendulum
        returns list of dicts of info (different to get_arbor_rod_lengths as it's harder to position these without knowing all the internal logic here)
        this is likely to be brittle
        '''
        rod_infos = []

        # assume beat setting holder and m3 threaded rod and pendulum at x=0
        anchor_top_y = self.plates.bearing_positions[-1][1]
        pendulum_rod_d = 3
        holder = self.plates.arbors_for_plate[-1].beat_setting_pendulum_bits
        holder_hole_top_y = anchor_top_y + holder.top_of_pendulum_holder_hole_y
        # bodgey, copied from get_pendulum_holder_cutter
        hole_height = get_nut_height(pendulum_rod_d, nyloc=True) + get_nut_height(pendulum_rod_d) + 1
        #the slot at the bottom of the hole is designed to be a nyloc nut tall, so we can ignore it and just go for a half nut taller
        holder_hole_bottom_y = holder_hole_top_y - hole_height
        top_y = holder_hole_bottom_y + get_nut_height(pendulum_rod_d, half_height=True)

        pendulum_centre_z = self.pendulum_bob_centre_pos[2]


        if self.has_ring:

            ring_centre_y = self.plates.bottom_pillar_positions[0][1]
            #top rod
            bottom_y = ring_centre_y + self.pendulum.hand_avoider_inner_d/2 + self.pendulum.rod_screws.get_nut_height() - self.pendulum.rod_screws.get_nut_height(nyloc=True)
            length = top_y - bottom_y
            rod_infos.append({"length": length, "pos":(0, (bottom_y + top_y)/2, pendulum_centre_z)})

            lower_rod_top_y =ring_centre_y - self.pendulum.hand_avoider_inner_d/2 - self.pendulum.rod_screws.get_nut_height() + self.pendulum.rod_screws.get_nut_height(nyloc=True)
            print("Pendulum needs rod length {:.1f}mm from holder to hand avoider ring".format(length))
        else:
            lower_rod_top_y = top_y

        pendulum_bottom_y = anchor_top_y - self.plates.arbors_for_plate[-1].pendulum_length*1.1
        length = lower_rod_top_y - pendulum_bottom_y
        print("Pendulum needs rod length {:.1f}mm to hold the bob".format(length))
        rod_infos.append({"length": length, "pos":(0, (lower_rod_top_y + pendulum_bottom_y)/2, pendulum_centre_z)})

        return rod_infos

    def get_clock(self, with_rods=False, with_key=False, with_pendulum=False):
        '''
        Probably fairly intimately tied in with the specific clock plates, which is fine while there's only one used in anger
        '''

        clock = self.plates.get_assembled()

        for a,arbour in enumerate(self.plates.arbors_for_plate):
            clock = clock.add(arbour.get_assembled())


        time_min = self.time_mins
        time_hour = self.time_hours




        motionWorksModel = self.motion_works.get_assembled(motionWorksRelativePos=self.plates.motion_works_relative_pos, minuteAngle=self.minuteAngle)

        clock = clock.add(motionWorksModel.translate((self.plates.hands_position[0], self.plates.hands_position[1], self.motion_works_z)))

        if self.moon_complication is not None:
            clock = clock.add(self.moon_complication.get_assembled().translate((self.motion_works_pos[0], self.motion_works_pos[1], self.front_of_clock_z)))
            moon = self.moon_complication.get_moon_half()
            moon = moon.add(moon.rotate((0,0,0),(0,1,0),180))
            clock = clock.add(moon.translate((0, self.plates.moon_holder.get_moon_base_y() + self.moon_complication.moon_radius, self.moon_complication.get_relative_moon_z() + self.front_of_clock_z)))

        if self.plates.centred_second_hand:
            #the bit with a knob to set the time
            clock = clock.add(self.motion_works.get_cannon_pinion_pinion(standalone=True).translate((self.plates.bearing_positions[self.going_train.powered_wheels][0], self.plates.bearing_positions[self.going_train.powered_wheels][1], self.motion_works_z)))


        if self.dial is not None:
            dial = self.dial.get_assembled()#get_dial().rotate((0,0,0),(0,1,0),180)
            clock = clock.add(dial.translate(self.dial_pos))
            if self.dial.has_eyes():
                clock = clock.add(self.dial.get_wire_to_arbor_fixer(for_printing=False).translate((self.plates.bearing_positions[-1][0], self.plates.bearing_positions[-1][1], self.front_of_clock_z + self.plates.endshake + 1)))


        #hands on the motion work, showing the time
        hands = self.hands.get_assembled(time_minute = time_min, time_hour=time_hour, include_seconds=False, gap_size =self.motion_works.hour_hand_slot_height - self.hands.thick)


        # clock = clock.add(minuteHand.translate((self.plates.bearingPositions[self.goingTrain.chainWheels][0], self.plates.bearingPositions[self.goingTrain.chainWheels][1], minuteHandZ)))

        clock = clock.add(hands.translate((self.plates.hands_position[0], self.plates.hands_position[1],
                                           self.minute_hand_z - self.motion_works.hour_hand_slot_height)))

        if self.plates.has_seconds_hand():
            #second hand!! yay
            secondHand = self.hands.get_hand(hand_type=HandType.SECOND).mirror().translate((0, 0, self.hands.thick)).rotate((0, 0, 0), (0, 0, 1), self.secondAngle)

            clock = clock.add(secondHand.translate(self.second_hand_pos))

        if with_key:
            if self.key_model is not None:
                clock = clock.add(self.key_model)

        if self.with_mat:
            mat, mat_detail = self.plates.get_mat()
            clock = clock.add(mat.rotate((0, 0, 0), (1, 0, 0), -90).translate((0, -self.plates.mat_thick, 0)).translate(self.base_of_clock))
            clock = clock.add(mat_detail.rotate((0, 0, 0), (1, 0, 0), -90).translate((0, -self.plates.mat_thick, 0)).translate(self.base_of_clock))

        if with_pendulum:
            bob = self.pendulum.get_bob(hollow=False)

            if self.pretty_bob is not None:
                bob = self.pretty_bob.get_model()

            clock = clock.add(bob.rotate((0, 0, self.pendulum.bob_thick / 2), (0, 1, self.pendulum.bob_thick / 2), 180).translate(self.pendulum_bob_centre_pos))

            clock = clock.add(self.pendulum.get_bob_nut().translate((0, 0, -self.pendulum.bob_nut_thick / 2)).rotate((0, 0, 0), (1, 0, 0), 90).translate(self.pendulum_bob_centre_pos))


        if len(self.weights) > 0:
            for i, weight in enumerate(self.weights):
                #line them up so I can see if they'll bump into each other
                weightTopY = self.pendulum_bob_centre_pos[1]

                holePositions = self.going_train.powered_wheel.get_chain_positions_from_top()

                #side the main weight is on
                side = 1 if self.going_train.is_weight_on_the_right() else -1

                if i == 1:
                    #counterweight
                    side*=-1

                #in X,Y,Z
                weightPos = None

                for holeInfo in holePositions:
                    if (holeInfo[0][0] > 0) == (side > 0):
                        #hole for the weight
                        weightPos = (holeInfo[0][0], weightTopY - weight.height, self.plates.bearing_positions[0][2] + self.plates.get_plate_thick(back=True) + self.going_train.powered_wheel.get_height() + holeInfo[0][1])

                if weightPos is not None:
                    weightShape = weight.getWeight().rotate((0,0,0), (1,0,0),-90)

                    clock = clock.add(weightShape.translate(weightPos))


        #vector from minute wheel to the pendulum
        minuteToPendulum = (self.plates.bearing_positions[-1][0] - self.plates.bearing_positions[self.going_train.powered_wheels][0], self.plates.bearing_positions[-1][1] - self.plates.bearing_positions[self.going_train.powered_wheels][1])

        if abs(minuteToPendulum[0]) < 50:
            ring = self.pendulum.get_hand_avoider()
            if self.plates.pendulum_at_front:
                #if the hands are directly below the pendulum pivot point (not necessarily true if this isn't a vertical clock)

                #centre around the hands by default
                ringY = self.plates.bearing_positions[self.going_train.powered_wheels][1]
                if self.going_train.powered_wheel.type == PowerType.CORD and self.going_train.powered_wheel.use_key:
                    #centre between the hands and the winding key
                    ringY = (self.plates.bearing_positions[self.going_train.powered_wheels][1] + self.plates.bearing_positions[0][1]) / 2


                handAvoiderExtraZ = (self.pendulum.pendulumTopThick - self.pendulum.hand_avoider_thick) / 2
                #ring is over the minute wheel/hands
                clock = clock.add(ring.translate((self.plates.bearing_positions[self.going_train.powered_wheels][0], ringY, self.plates.get_plate_thick(back=True) + self.plates.get_plate_thick(back=False) + self.plates.plate_distance + self.plates.pendulum_sticks_out + handAvoiderExtraZ)))
            else:
                #pendulum is at the back, hand avoider is around the bottom pillar (unless this proves too unstable)
                if len(self.plates.bottom_pillar_positions) == 1:
                    ringCentre = self.plates.bottom_pillar_positions[0]
                    clock = clock.add(ring.translate(ringCentre).translate((0, 0, -self.plates.pendulum_sticks_out - self.pendulum.hand_avoider_thick / 2)))


        if self.pulley is not None:
            clock = clock.add(self.pulley_model)


        if self.plates.huygens_maintaining_power:
            #assumes one pillar
            clock = clock.add(self.plates.huygens_wheel.get_assembled().translate(self.plates.bottom_pillar_positions[0]).translate((0, self.plates.huygens_wheel_y_offset, self.plates.get_plate_thick(True) + self.plates.get_plate_thick(False) + self.plates.plate_distance + WASHER_THICK_M3)))

        #TODO pendulum bob and nut?

        #TODO weight?

        if with_rods:
            rod_lengths, rod_zs = self.get_arbor_rod_lengths()
            for i in range(len(rod_lengths)):
                if rod_lengths[i] <= 0:
                    continue
                rod = cq.Workplane("XY").circle(self.going_train.get_arbour_with_conventional_naming(i).arbor_d / 2 - 0.2).extrude(rod_lengths[i]).translate((self.plates.bearing_positions[i][0], self.plates.bearing_positions[i][1], rod_zs[i]))
                clock = clock.add(rod)

        return clock


    def show_clock(self, show_object, gear_colours=None, dial_colours=None, plate_colours=None, hand_colours=None,
                   bob_colours=None, motion_works_colours=None, with_pendulum=True, ring_colour=None, huygens_colour=None, weight_colour=Colour.PURPLE,
                   text_colour=Colour.WHITE, with_rods=False, with_key=False, key_colour=Colour.PURPLE, pulley_colour=Colour.PURPLE, ratchet_colour=None,
                   moon_complication_colours=None, vanity_plate_colour=Colour.WHITE, plaque_colours=None, moon_angle_deg=45):
        '''
        use show_object with colours to display a clock, will only work in cq-editor, useful for playing about with colour schemes!
        hoping to re-use some of this to produce coloured SVGs
        '''
        if gear_colours is None:
            gear_colours = Colour.RAINBOW
        if dial_colours is None:
            dial_colours = ["white", "black"]
        if hand_colours is None:
            #main hand, outline, second hand if different
            hand_colours = ["white", "black"]
        if motion_works_colours is None:
            #cannonpinion, hour holder, arbor, time-setting pinion
            motion_works_colours = [gear_colours[self.going_train.wheels]]
        if ring_colour is None:
            ring_colour = gear_colours[(self.going_train.wheels + self.going_train.powered_wheels + 1) % len(gear_colours)]
        if huygens_colour is None:
            huygens_colour = gear_colours[(self.going_train.wheels + self.going_train.powered_wheels + 2) % len(gear_colours)]
        if bob_colours is None:
            offset = 2
            if self.going_train.huygens_maintaining_power:
                offset = 3
            default_bob_colour = gear_colours[(self.going_train.wheels + self.going_train.powered_wheels + offset) % len(gear_colours)]
            #default to bob and nut are same colour and any text is black
            bob_colours = [default_bob_colour,default_bob_colour, Colour.BLACK]

        if plate_colours is None:
            plate_colours = [Colour.LIGHTGREY]
        if moon_complication_colours is None:
            moon_complication_colours = [Colour.BRASS]

        if not isinstance(plate_colours, list):
            #backwards compatibility
            plate_colours = [plate_colours]

        if ratchet_colour is None:
            ratchet_colour = plate_colours[0]
        if plaque_colours is None:
            plaque_colours = [Colour.GOLD, Colour.BLACK]

        plates, pillars, plate_detail, standoff_pillars = self.plates.get_assembled(one_peice=False)

        show_object(plates, options={"color":plate_colours[0]}, name= "Plates")
        show_object(pillars, options={"color": plate_colours[1 % len(plate_colours)]}, name="Pillars")
        show_object(standoff_pillars, options={"color": plate_colours[1 % len(plate_colours)]}, name="Standoff Pillars")

        if plate_detail is not None:
            show_object(plate_detail, options={"color": plate_colours[2 % len(plate_colours)]}, name="Plate Detail")

        if self.plaque is not None:
            show_object(self.plaque_shape, options={"color": plaque_colours[0]}, name="Back Plaque")
            show_object(self.plaque_text_shape, options={"color": plaque_colours[1]}, name = "Back Plaque Text")
        else:
            if not self.plates.text_on_standoffs:
                show_object(self.plates.get_text(), options={"color":text_colour}, name="Text")
            else:
                show_object(self.plates.get_text(top_standoff=True), options={"color": text_colour}, name="Top Standoff Text")
                show_object(self.plates.get_text(top_standoff=False), options={"color": text_colour}, name="Bottom Standoff Text")

        for a, arbor in enumerate(self.plates.arbors_for_plate):
            show_object(arbor.get_assembled(), options={"color": gear_colours[(len(self.plates.arbors_for_plate) - 1 - a) % len(gear_colours)]}, name="Arbour {}".format(a))

        # return
        # # motionWorksModel = self.motionWorks.get_assembled(motionWorksRelativePos=self.plates.motionWorksRelativePos, minuteAngle=self.minuteAngle)
        # #
        # # show_object(motionWorksModel.translate((self.plates.hands_position[0], self.plates.hands_position[1], self.motionWorksZ)), options={"color":motion_works_colour})
        motion_works_parts = self.motion_works.get_parts_in_situ(motionWorksRelativePos=self.plates.motion_works_relative_pos, minuteAngle=self.minuteAngle)

        for i,part in enumerate(motion_works_parts):
            colour = motion_works_colours[i % len(motion_works_colours)]
            show_object(motion_works_parts[part].translate((self.plates.hands_position[0], self.plates.hands_position[1], self.motion_works_z)), options={"color":colour}, name="Motion Works {}".format(i))

        if self.motion_works.cannon_pinion_friction_ring:
            show_object(self.plates.get_cannon_pinion_friction_clip().translate(self.plates.cannon_pinion_friction_clip_pos).translate((0,0,self.front_of_clock_z + self.plates.motion_works_holder_thick )), options={"color":plate_colours[0]}, name="Friction Clip")

        if self.moon_complication is not None:
            #TODO colours of moon complication arbors
            # show_object(self.moon_complication.get_assembled().translate((self.motion_works_pos[0], self.motion_works_pos[1], self.front_of_clock_z)), name="Moon Complication", options={"color":moon_complication_colour})
            moon_parts_dict = self.moon_complication.get_parts_in_situ()
            for i,moon_part in enumerate(moon_parts_dict):
                friendly_name = string.capwords(moon_part.replace("_"," "))
                show_object(moon_parts_dict[moon_part].translate((self.motion_works_pos[0], self.motion_works_pos[1], self.front_of_clock_z)), name=f"Moon Complication {friendly_name}", options={"color":moon_complication_colours[i%len(moon_complication_colours)]})

            moon = self.moon_complication.get_moon_half()
            # moon = moon.add(moon.rotate((0,0,0),(0,1,0),180))
            moon_z = self.moon_complication.get_relative_moon_z() + self.front_of_clock_z
            show_object(moon.rotate((0,0,0),(0,1,0), moon_angle_deg).translate((0, self.plates.moon_holder.get_moon_base_y() + self.moon_complication.moon_radius, moon_z)),
                        options={"color":"gray"}, name="Light Side of the Moon")
            show_object(moon.rotate((0,0,0),(0,1,0),180 + moon_angle_deg).translate((0, self.plates.moon_holder.get_moon_base_y() + self.moon_complication.moon_radius, moon_z)),
                        options={"color":"black"}, name="Dark Side of the Moon")

            holder_parts = self.plates.moon_holder.get_moon_holder_parts(for_printing=False)
            for i,holder in enumerate(holder_parts):
                show_object(holder.translate((0, 0, self.front_of_clock_z)), name="moon_holder_part{}".format(i), options={"color":plate_colours[0]})
        # return
        if self.dial is not None:
            dial = self.dial.get_dial().rotate((0,0,0),(0,1,0),180).translate(self.dial_pos)
            detail = self.dial.get_all_detail().rotate((0,0,0),(0,1,0),180).translate(self.dial_pos)

            show_object(dial, options={"color": dial_colours[0]}, name="Dial")
            show_object(detail, options={"color": dial_colours[1]}, name="Dial Detail")

            if self.dial.style == DialStyle.TONY_THE_CLOCK:
                extras = self.dial.get_extras()
                #TODO - excessive since I'm probably never going to print tony again?

            if self.dial.has_eyes():
                show_object(self.dial.get_wire_to_arbor_fixer(for_printing=False).translate(self.wire_to_arbor_fixer_pos), options={"color": gear_colours[0]}, name="Eye Wire Fixer")
                eye, pupil = self.dial.get_eye()

                for i,eye_pos in enumerate(self.dial.get_eye_positions()):
                    show_object(eye.translate(eye_pos).translate(self.dial_pos).translate((0,0,-self.dial.thick - self.dial.eye_pivot_z)), options={"color": "white"}, name="Eye {} Whites".format(i))
                    show_object(pupil.translate(eye_pos).translate(self.dial_pos).translate((0,0,-self.dial.thick - self.dial.eye_pivot_z)), options={"color": "black"}, name="Eye Pupil".format(i))

        if self.vanity_plate is not None:
            show_object(self.vanity_plate, options={"color": vanity_plate_colour}, name="Vanity Plate")

        #hands on the motion work, showing the time
        #mirror them so the outline is visible (consistent with second hand)
        hands_position = (self.plates.hands_position[0], self.plates.hands_position[1], self.minute_hand_z - self.motion_works.hour_hand_slot_height)
        self.hands.show_hands(show_object, hand_colours=hand_colours, position=hands_position, second_hand_pos=self.second_hand_pos, hour_hand_slot_height=self.motion_works.hour_hand_slot_height,
                              time_hours=self.time_hours, time_minutes=self.time_mins, time_seconds=self.time_seconds, show_second_hand=self.plates.has_seconds_hand())

        if self.has_ring:

            show_object(self.pendulum.get_hand_avoider().translate(self.ring_pos), options={"color": ring_colour}, name="Pendulum Ring")

        if self.plates.huygens_maintaining_power:
            #assumes one pillar
            show_object(self.plates.huygens_wheel.get_assembled().translate(self.plates.bottom_pillar_positions[0]).
                        translate((0, self.plates.huygens_wheel_y_offset, self.front_of_clock_z + WASHER_THICK_M3)), options={"color": huygens_colour}, name="Huygens Wheel")

        if self.ratchet_on_plates is not None:
            show_object(self.ratchet_on_plates, options={"color": ratchet_colour}, name="ratchet")

        if with_pendulum:
            # bob_colour = gear_colours[len(self.plates.bearingPositions) % len(gear_colours)]
            bob_colour = bob_colours[0]
            nut_colour = bob_colours[ 1 % len(bob_colours)]
            text_colour = bob_colours[ 2 % len(bob_colours)]
            bob = self.pendulum.get_bob(hollow=False)

            if self.pretty_bob is not None:
                bob = self.pretty_bob.get_model()

            bob_text = self.pendulum.get_bob_text()
            if bob_text is not None:
                show_object(bob_text.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, self.pendulum.bob_thick / 2)).translate(self.pendulum_bob_centre_pos), options={"color": text_colour}, name="Pendulum Bob Text")

            show_object(bob.rotate((0,0,0),(0,1,0),180).translate((0, 0, self.pendulum.bob_thick / 2)).translate(self.pendulum_bob_centre_pos), options={"color": bob_colour}, name="Pendulum Bob")

            show_object(self.pendulum.get_bob_nut().translate((0, 0, -self.pendulum.bob_nut_thick / 2)).rotate((0, 0, 0), (1, 0, 0), 90).translate(self.pendulum_bob_centre_pos), options={"color": nut_colour}, name="Pendulum Bob Nut")


        if len(self.weights) > 0:
            for i, weight_pos in enumerate(self.weight_positions):

                weightShape = self.weights[i].getWeight().rotate((0,0,0), (1,0,0),-90)

                show_object(weightShape.translate(weight_pos), options={"color": weight_colour}, name="Weight_{}".format(i))

        if self.with_mat:
            mat, mat_detail = self.plates.get_mat()

            show_object(mat.rotate((0, 0, 0), (1, 0, 0), -90).translate((0, -self.plates.mat_thick, 0)).translate(self.base_of_clock), options={"color": plate_colours[0]}, name="Mat")
            show_object(mat_detail.rotate((0, 0, 0), (1, 0, 0), -90).translate((0, -self.plates.mat_thick, 0)).translate(self.base_of_clock), options={"color": plate_colours[2 % len(plate_colours)]}, name="Mat Detail")

        if with_rods:
            #show with diameter slightly smaller so it's clearer on the render what's rod and what's hole
            rod_colour = Colour.SILVER
            rod_lengths, rod_zs = self.get_arbor_rod_lengths()
            for i in range(len(rod_lengths)):
                if rod_lengths[i] <= 0:
                    continue
                rod = cq.Workplane("XY").circle(self.going_train.get_arbour_with_conventional_naming(i).arbor_d / 2 - 0.2).extrude(rod_lengths[i]).translate((self.plates.bearing_positions[i][0], self.plates.bearing_positions[i][1], rod_zs[i]))
                show_object(rod, options={"color": rod_colour}, name="Arbor Rod {}".format(i))
            pillar_rod_lengths, pillar_rod_zs = self.plates.get_rod_lengths()
            for p, length in enumerate(pillar_rod_lengths):
                pos = self.plates.all_pillar_positions[p]
                rod = cq.Workplane("XY").circle(self.plates.fixing_screws.metric_thread/2 - 0.2).extrude(length).translate((pos[0], pos[1], pillar_rod_zs[p]))
                show_object(rod, options={"color": rod_colour}, name="Fixing Rod {}".format(p))

            pendulum_rods = self.get_pendulum_rod_lengths()

            for i,rod_info in enumerate(pendulum_rods):
                rod = cq.Workplane("XY").circle(3/2).extrude(rod_info["length"]).translate((0,0,-rod_info["length"]/2)).rotate((0,0,0),(1,0,0),90)

                show_object(rod.translate(rod_info["pos"]), options={"color": rod_colour}, name=f"Pendlum Rod {i}")

        if with_key:
            if self.key_model is not None:
                show_object(self.key_model, options={"color": key_colour}, name="Key")

        if self.pulley is not None:
            show_object(self.pulley_model, options={"color": pulley_colour}, name="Pulley")

    def output_STLs(self, name="clock", path="../out"):
        out = os.path.join(path, "{}.stl".format(name))
        print("Outputting ", out)
        exporters.export(self.get_clock(), out)

    def outputSVG(self, name="clock", path="../out"):
        out = os.path.join(path, "{}.svg".format(name))
        print("Outputting ", out)
        exportSVG(self.get_clock(), out, opts={"width":720, "height":1280})
