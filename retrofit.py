from clocks import *

outputSTL = False

if 'show_object' not in globals():
    #don't output STL when we're in cadquery editor
    outputSTL = True
    def show_object(*args, **kwargs):
        pass



'''
1 = {ArbourForPlate} <clocks.gearing.ArbourForPlate object at 0x000001677730A2B0>
arbor = {Arbour} <clocks.gearing.Arbour object at 0x000001677730A9D0>
      arbour_d = {int} 3
      clockwise_from_pinion_side = {bool} True
      combine_with_powered_wheel = {bool} False
      distance_to_next_arbour = {float} 55.625
      end_cap_thick = {float} 0.8
      escapement = {NoneType} None
      escapement_on_front = {bool} False
      hole_d = {int} 3
      loose_on_rod = {bool} False
      pinion = {Gear} <clocks.gearing.Gear object at 0x000001677730A760>
      pinion_at_front = {bool} True
      pinion_extension = {int} 0
      pinion_thick = {int} 12
      powered_wheel = {NoneType} None
      ratchet = {NoneType} None
      style = {GearStyle} GearStyle.FLOWER
      type = {ArbourType} ArbourType.WHEEL_AND_PINION
      use_ratchet = {bool} True
      wheel = {Gear} <clocks.gearing.Gear object at 0x000001677730A940>
      wheel_thick = {float} 5.4
arbor_d = {int} 3
arbour_bearing_standoff_length = {float} 0.4
arbour_extension_max_radius = {float} 14.498158519227623
back_plate_from_wall = {int} 31
back_plate_thick = {int} 6
bearing = {BearingInfo} 3x10.1x4
bearing_position = {list: 3} [47.32390341712906, 35.85859437242682, 8.700000000000001]
collet_screws = {MachineScrew} M2 (CS)
collet_thick = {int} 6
crutch_holder_slack_space = {int} 2
crutch_thick = {int} 8
cylinder_r = {float} 3.5
direct_arbour_d = {int} 7
distance_from_back = {float} 8.700000000000001
distance_from_front = {float} 19.700000000000003
endshake = {int} 1
escapement_on_front = {bool} False
friction_fit_bits = {FrictionFitPendulumBits} <clocks.gearing.FrictionFitPendulumBits object at 0x00000167790753D0>
front_anchor_from_plate = {int} 3
front_plate_thick = {int} 6
key_length = {int} 0
outer_d = {float} 7.175
pendulum_at_front = {bool} False
pendulum_fixing = {PendulumFixing} PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS
pendulum_fixing_extra_space = {float} 0.2
pendulum_holder_thick = {int} 15
pendulum_sticks_out = {int} 15
plate_distance = {float} 47.6
plates = {MantelClockPlates} <clocks.clock.MantelClockPlates object at 0x000001677730A430>
previous_bearing_position = {list: 3} [0, 0, 17.099999999999998]
ratchet_key_length = {int} 3
square_side_length = {float} 5.939696961966999
standoff_plate_thick = {int} 6
suspension_spring_bits = {SuspensionSpringPendulumBits} <clocks.gearing.SuspensionSpringPendulumBits object at 0x0000016779075E50>
total_plate_thickness = {float} 59.6
total_thickness = {float} 18.2
type = {ArbourType} ArbourType.WHEEL_AND_PINION

plates:

plates = {MantelClockPlates} <clocks.clock.MantelClockPlates object at 0x000001677730A430>
 allow_bottom_pillar_height_reduction = {bool} False
 angles_from_chain = {list: 2} [0.6484280078446779, 2.588238969031655]
 angles_from_minute = {list: 5} [2.429281890906516, 0.5326597965315742, 0.8465857647801163, 2.187878200674903, 1.5707963267948966]
 arbors_for_plate = {list: 7} [<clocks.gearing.ArbourForPlate object at 0x000001677730A280>, <clocks.gearing.ArbourForPlate object at 0x000001677730A2B0>, <clocks.gearing.ArbourForPlate object at 0x0000016779075460>, <clocks.gearing.ArbourForPlate object at 0x0000016779075C70>, <clocks.gearing.ArbourForPlate object at 0x0000016779075130>, <clocks.gearing.ArbourForPlate object at 0x0000016779075580>, <clocks.gearing.ArbourForPlate object at 0x0000016779075790>]
 arbourThicknesses = {list: 7} [29.5, 18.2, 14.000000000000002, 22.16, 14.224, 8.632, 12]
 arbour_d = {int} 3
 back_plate_from_wall = {int} 31
 back_plate_thick = {int} 6
 bearing_positions = {list: 7} [[0, 0, 17.099999999999998], [47.32390341712906, 35.85859437242682, 8.700000000000001], [7.105427357601002e-15, 65.09194502482795, 3.599999999999999], [-31.787852018763996, 92.54249081235577, 0.4], [1.0658141036401503e-14, 111.28128650560032, 17.439999999999998], [20.661445311882098, 134.63955918626115, 25.775999999999996], [3.552713678800501e-15, 163.760170639739, 20.775999999999996]]
 bearing_wall_thick = {int} 4
 bottom_pillar_positions = {list: 2} [(-48.115572382607574, -48.11557238260756), (48.11557238260757, -48.11557238260757)]
 bottom_pillar_r = {float} 10.860000000000001
 bottom_pillars = {int} 2
 centre_weight = {bool} False
 centred_second_hand = {bool} False
 chainThroughPillar = {bool} True
 chain_hole_d = {int} 4
 compact_zigzag = {bool} True
 crutch_space = {int} 10
 dial = {Dial} <clocks.dial.Dial object at 0x000001677730A460>
 dial_z = {float} 19.0
 direct_arbour_d = {int} 7
 embed_nuts_in_plate = {bool} False
 endshake = {int} 1
 escapement_on_front = {bool} False
 extra_heavy = {bool} False
 extra_support_for_escape_wheel = {bool} False
 fixing_screws = {MachineScrew} M4 (CS)
 fixing_screws_cutter = {NoneType} None
 foot_fillet_r = {int} 2
 front_z = {float} 59.6
 gear_gap = {int} 3
 going_train = {GoingTrain} <clocks.clock.GoingTrain object at 0x00000167580928E0>
 hands_position = {list: 2} [7.105427357601002e-15, 65.09194502482795]
 heavy = {bool} True
 huygens_maintaining_power = {bool} False
 huygens_wheel = {NoneType} None
 huygens_wheel_min_d = {int} 15
 huygens_wheel_y_offset = {int} 0
 key_hole_d = {float} 19.1
 key_offset_from_front_plate = {int} 1
 key_square_bit_height = {float} 23.0
 min_plate_width = {float} 18.1
 moon_complication = {NoneType} None
 moon_holder = {NoneType} None
 motion_works = {MotionWorks} <clocks.gearing.MotionWorks object at 0x000001677730A0A0>
 motion_works_angle = {float} 4.71238898038469
 motion_works_fixings_relative_pos = {list: 2} [(-5.430000000000001, 15.0), (5.430000000000001, -15.0)]
 motion_works_holder_length = {int} 30
 motion_works_holder_wide = {float} 21.720000000000002
 motion_works_pos = {tuple: 2} (2.6966988806705302e-15, 41.09194502482795)
 motion_works_relative_pos = {tuple: 2} (-4.408728476930472e-15, -24.0)
 motion_works_screws = {MachineScrew} M3 (CS)
 name = {str} 'Mantel 27'
 narrow_bottom_pillar = {bool} False
 need_motion_works_holder = {bool} False
 pendulum = {NoneType} None
 pendulum_at_front = {bool} False
 pendulum_at_top = {bool} True
 pendulum_fixing = {PendulumFixing} PendulumFixing.DIRECT_ARBOUR_SMALL_BEARINGS
 pendulum_sticks_out = {int} 15
 pillars_separate = {bool} True
 plate_bottom_fixings = {list: 2} [(-48.115572382607574, -48.11557238260756), (48.11557238260757, -48.11557238260757)]
 plate_distance = {float} 47.6
 plate_fixings = {list: 4} [(-35.536336128654526, 140.1714973629225), (46.723763595977516, 99.51681973592243), (-48.115572382607574, -48.11557238260756), (48.11557238260757, -48.11557238260757)]
 plate_thick = {int} 6
 plate_top_fixings = {list: 2} [(-35.536336128654526, 140.1714973629225), (46.723763595977516, 99.51681973592243)]
 plate_width = {float} 21.720000000000002
 powered_wheel_r = {float} 57.18569502482794
 rear_standoff_bearing_holder_thick = {int} 6
 reduce_bottom_pillar_height = {int} 0
 screws_from_back = {list: 2} [[True, False], [False, False]]
 second_hand = {bool} True
 small_gear_gap = {int} 2
 style = {ClockPlateStyle} ClockPlateStyle.COMPACT
 texts = {list: 4} ['Mantel 27', '2025-10-08', 'Luke Wallin', '11.0cm']
 top_of_hands_z = {float} 35.5
 top_pilars = {int} 1
 top_pillar_positions = {list: 2} [(-35.536336128654526, 140.1714973629225), (46.723763595977516, 99.51681973592243)]
 top_pillar_r = {float} 10.860000000000001
 using_pulley = {bool} False
 wall_fixing_screw_head_d = {int} 11
 weight_driven = {bool} False
 weight_on_right_side = {bool} True
 winding_key = {WindingKey} <clocks.power.WindingKey object at 0x000001677730A3A0>

[[66, 10], [76, 13]]
'''
ratios = [[66, 10], [76, 13]]
pairs = [WheelPinionPair(wheelTeeth=p[0], pinionTeeth=p[1],module=1.25) for p in ratios]

pairs = [WheelPinionPair(wheelTeeth=ratios[0][0], pinionTeeth=ratios[0][1], module=1.5625, lantern=True), WheelPinionPair(wheelTeeth=ratios[1][0], pinionTeeth=ratios[1][1], module=1.25)]

#check pairs[1].centre_distance ==  55.625
#clockwise_from_pinion_side was wrong, don't think it matters
arbor = Arbor(rod_diameter=3, wheel=pairs[1].wheel, wheel_thick=5.4, pinion=pairs[0].pinion, pinion_thick=12, end_cap_thick=-1, style=GearStyle.FLOWER,
              distance_to_next_arbor=pairs[1].centre_distance, pinion_at_front=True, clockwise_from_pinion_side=True, pinion_type=PinionType.LANTERN_THIN, type=ArborType.WHEEL_AND_PINION)

class FakePlates:
    # def __init__(self):
    #     self.plate_distance=47.6
        # self.plate
    def get_plate_distance(self):
        return 47.6
    def get_plate_thick(self, back=False, standoff=False):
        return 6
fake_plates = FakePlates()
'''
self.plate_distance = self.plates.get_plate_distance()
        self.front_plate_thick = self.plates.get_plate_thick(back=False)
        self.back_plate_thick = self.plates.get_plate_thick(back=True)
        self.standoff_plate_thick = self.plates.get_plate_thick(standoff=True)
'''

replacement_arbor_for_plate = ArborForPlate(arbor, fake_plates, arbor_extension_max_radius=14.498158519227623, pendulum_sticks_out=15, pendulum_at_front=False, bearing=BEARING_3x10x4,
                                            back_from_wall=31, endshake=1, pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS,
                                            bearing_position=[47.32390341712906, 35.85859437242682, 8.700000000000001], direct_arbor_d=7,
                                            previous_bearing_position=[0, 0, 17.099999999999998])


if outputSTL:
    bom = replacement_arbor_for_plate.get_BOM()
    # bom = BillOfMaterials("Retrofitted wheel")
    # bom.add_printed_parts(replacement_arbor_for_plate.get_printed_parts())
    #
    bom.export(out_path="out/mantel_27_new_wheel")

else:
    show_object(replacement_arbor_for_plate.get_assembled())