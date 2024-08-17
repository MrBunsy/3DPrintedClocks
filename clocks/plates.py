'''
Copyright Luke Wallin 2023

This source describes Open Hardware and is licensed under the CERN-OHL-S v2.

You may redistribute and modify this source and make products using it under
the terms of the CERN-OHL-S v2 or any later version (https://ohwr.org/cern_ohl_s_v2.txt).

This source is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY,
INCLUDING OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A
PARTICULAR PURPOSE. Please see the CERN-OHL-S v2 for applicable conditions.

Source location: https://github.com/MrBunsy/3DPrintedClocks

As per CERN-OHL-S v2 section 4, should you produce hardware based on this
source, You must where practicable maintain the Source Location visible
on the external case of the clock or other products you make using this
source.
'''
import numpy.linalg.linalg

from .utility import *
from .power import *
from .gearing import *
from .hands import *
from .escapements import *
from .cosmetics import *
from .leaves import *
from .dial import *
from .pillars import fancy_pillar
import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
from math import sin, cos, pi, floor
import numpy as np
import os
import datetime
from .cuckoo_bits import roman_numerals
from .cq_svg import exportSVG

# if 'show_object' not in globals():
#     #don't output STL when we're in cadquery editor
#     outputSTL = True
#     def show_object(*args, **kwargs):
#         pass



'''
Long term plan: this will be a library of useful classes to generate all the components and bits of clock plates
But another script will generate specific clock plates and arbours (note - the GoingTrain class has become a bit of a jack of all trades generating most of the arbours)
(note - arbours have been spun out into their own class, but the goingtrain, arbours and plates are still fairly strongly coupled)

Note: naming conventions I can find for clock gears seem to assume you always have the same number of gears between the chain and the minute hand
this is blatantly false (I can see this just looking at the various clocks I have) so I originally adopted a different naming convention:

The minute hand arbour is arbour 0.
In the direction of the escapement is +=ve
in the direction of the chain/spring wheel is -ve

UPDATE - although I thought it would be useful to always have the minute wheel as 0, it has actually proven to be more of a bother
A lot of operations require looping through all the bearings, and it would have been much easier to stick with the convention
getArbourWithConventionalNaming has been added to address this, but be aware that both are in play (although it should be clear which is being used) 


So for a very simple clock where the minute arbour is also the chain wheel, there could be only three arbours: 0, 1 and 2 (the escape wheel itself)

This way I can add more gears in either direction without confusing things too much.

The gears that drive the hour hand are the motion work. The cannon pinion is attached to the minute hand arbour, this drives the minute wheel.
The minute wheel is on a mini arbour with the hour pinion, which drives the hour wheel. The hour wheel is on the hour shaft.
The hour shaft fits over the minute arbour (on the clock face side) and the hour hand is friction fitted onto the hour shaft

Current plan: the cannon pinion will be loose over the minute arbour, and have a little shaft for the minute hand.
A nyloc nut underneath it (or two nuts locked against each other) and a normal nut on top (found nyloc or two nuts locked works better, you can turn hands backwards) 
of the minute hand will provide friction from the minute arbour to the motion work.
I think this is similar to older cuckoos I've seen. It will result in a visible nut, but a more simple time train. Will try it
for the first clock and decide if I want to switch to something else later. 
update - it works really well, I'm planning to keep doing it until there's reason not to.


Plan: spin out GoingTrain to gearing and a new file for the plates. keep this just for the clock assembly (and maybe dial and any future cases?)
'''



class MoonHolder:
    '''
    This might be worth splitting into different classes for each class of supported clock plate?

    bolts to the front of the front plate to hold the moon on a stick for the moon complication.
    needs both moon complication and SimpleClockPlates objects to calculate all the relevant dimensions
    highly coupled to both

    this needs to be able to be screwed into the front plate from the front - so i think space for the nuts behind the front plate

    current thinking: two peices. Print both with the bottom side facing forwards. One nearest the clock plates will have two branches on either side for the top of the dial to screw into
     and will be the moon spoon
    top peice will just be to clamp the steel tube in the right place.

    '''
    def __init__(self, plates, moon_complication, fixing_screws):
        self.plates = plates
        self.moon_complication = moon_complication
        self.fixing_screws = fixing_screws
        self.arbor_d = self.moon_complication.arbor_d
        self.moon_inside_dial = moon_complication.moon_inside_dial
        #prefer 3, but mantel clock struggles to auto generate the edging with 3 for some reason
        self.fillet_r = 2.5#3

        self.moon_extra_space = 1.5
        self.moon_spoon_thick = 1.6
        self.lid_thick = 6
        #centre_y is centre of the holding mechanism - this screws to the front plate and holds the steel pipe


        plate_shape = self.plates.get_plate_shape()

        if self.moon_inside_dial:
            self.moon_extra_space = 1
        #trying to be a bit less plate-dependant, putting that logic into the plates class
        moon_info = self.plates.get_moon_holder_info()

        self.centre_y = moon_info["y"]
        self.height = moon_info["height"]
        self.width = moon_info["wide"]

        self.moon_y = self.centre_y + self.height/2 + self.moon_complication.moon_radius

        if self.moon_inside_dial:
            self.moon_y = self.plates.hands_position[1] + self.moon_complication.moon_from_hands


        print("Screw length for moon fixing: {}mm".format(self.moon_complication.get_relative_moon_z() + self.plates.get_plate_thick(back=False) + self.lid_thick))

    def get_moon_base_y(self):
        return self.moon_y - self.moon_complication.moon_radius

    def get_fixing_positions(self):
        if self.moon_inside_dial:
            top_fixing_y = bottom_fixing_y = self.centre_y
        else:
            #between pillar screws and anchor arbor
            top_fixing_y = (self.plates.top_pillar_positions[0][1] + self.plates.bearing_positions[-1][1]) / 2 - 1
            #just inside the dial, by fluke
            bottom_fixing_y = self.centre_y - self.height / 2 + 8
        return [(-self.plates.plate_width / 3, top_fixing_y), (self.plates.plate_width / 3, bottom_fixing_y)]

    def get_moon_holder_parts(self, for_printing=True):
        '''
        piece screwed onto the front of the front plate with a steel tube slotted into it to take the moon on a threaded rod

        combined "moon spoon" to cup aroudn the back of the moon and a part to screw into the plates
        '''

        lid_thick = self.lid_thick

        moon_z = self.moon_complication.get_relative_moon_z()# + self.plates.get_front_z()
        moon_r = self.moon_complication.moon_radius
        width = self.width#self.plates.plate_width
        # top_y = self.plates.top_pillar_positions[1] + self.plates.top_pillar_r



        # not a full spoon as i think this will be hard to print with the bridging
        # not so deep that it will be behind the front plates
        moon_spoon_deep = moon_z
        if moon_spoon_deep > moon_r * 0.75:
            # for smaller moons (likely moon-inside-plate) still limit to not being a full hemisphere
            moon_spoon_deep = moon_r * 0.75
        moon_centre_pos = (0, self.moon_y, moon_z)

        if self.moon_inside_dial and self.plates.get_plate_shape() in [PlateShape.ROUND, PlateShape.MANTEL]:
            #TODO this only works for the RoundClockPlates, need to think of better way of sorting out what logic to run
            #extend this class for each plate type maybe?
            fillet_r=self.fillet_r
            # width = moon_r*2
            outer_radius = self.centre_y - self.plates.hands_position[1] + self.height/2
            if self.plates.get_plate_shape() == PlateShape.ROUND:
                outer_radius = self.plates.radius + self.height/2

            inner_radius = outer_radius - self.height

            holder = (cq.Workplane("XY").moveTo(self.plates.hands_position[0], self.plates.hands_position[1]).circle(outer_radius).circle(inner_radius)
                      .extrude(moon_z).intersect(cq.Workplane("XY").moveTo(0, self.plates.hands_position[1] + outer_radius - self.height/2).rect(width,outer_radius).extrude(moon_z)))
            holder = holder.edges("|Z").fillet(fillet_r)

            lid = (cq.Workplane("XY").moveTo(self.plates.hands_position[0], self.plates.hands_position[1]).circle(outer_radius).circle(inner_radius)
                      .extrude(moon_z).intersect(cq.Workplane("XY").moveTo(0, self.plates.hands_position[1] + outer_radius - self.height/2).rect(width,outer_radius).extrude(lid_thick)))
            lid = lid.edges("|Z").fillet(fillet_r)
            lid = lid.translate((0, 0, moon_z))
            #something to link spoon with the holder, don't worry about overlapping as the moon hole will be cut out later
            link_height = self.centre_y - self.moon_y
            holder = holder.union(cq.Workplane("XY").rect(self.plates.plate_width, link_height).extrude(moon_spoon_deep).translate((0,(self.centre_y + self.moon_y)/2,moon_z - moon_spoon_deep)))
        # elif self.moon_inside_dial and self.plates.get_plate_shape() == PlateShape.MANTEL:
        #     fillet_r = self.plates.foot_fillet_r
        #
        else:
            r = self.moon_complication.get_last_wheel_r()
            sagitta = r - math.sqrt(r ** 2 - 0.25 * width ** 2)

            bottom_r = r + sagitta
            # designed to be inline with the top of the vertical clock plate
            holder = cq.Workplane("XY").moveTo(-width / 2, self.centre_y + self.height/2 -width/2).radiusArc((width/2, self.centre_y + self.height/2-width/2), width/2).lineTo(width/2,self.centre_y-self.height/2).\
                    radiusArc((-width/2, self.centre_y - self.height/2), -bottom_r).close().extrude(moon_z)

            lid = cq.Workplane("XY").moveTo(-width / 2, self.centre_y + self.height / 2 - width / 2).radiusArc((width / 2, self.centre_y + self.height / 2 - width / 2), width / 2).lineTo(width / 2, self.centre_y - self.height / 2). \
                radiusArc((-width / 2, self.centre_y - self.height / 2), -bottom_r).close().extrude(lid_thick)
            lid = lid.cut(cq.Workplane("XY").circle(moon_r + self.moon_extra_space).extrude(lid_thick).translate((0, moon_centre_pos[1], 0)))
            lid = lid.translate((0, 0, moon_z))

        moon_and_more = cq.Workplane("XY").sphere(moon_r + self.moon_extra_space + self.moon_spoon_thick)
        #just the back half
        moon_spoon = moon_and_more.cut(cq.Workplane("XY").rect(moon_r*4, moon_r*4).extrude(moon_r*4))
        moon_spoon = moon_spoon.translate(moon_centre_pos)

        moon_spoon = moon_spoon.intersect(cq.Workplane("XY").rect(moon_r*4,moon_r*4).extrude(moon_spoon_deep).translate(moon_centre_pos).translate((0,0,-moon_spoon_deep)))


        #moon spoon!
        holder = holder.union(moon_spoon)




        #moon hole
        cutter = cq.Workplane("XY").sphere(self.moon_complication.moon_radius + self.moon_extra_space).translate(moon_centre_pos)


        for screw_pos in self.get_fixing_positions():
            cutter = cutter.union(self.fixing_screws.get_cutter(with_bridging=True, layer_thick=self.plates.layer_thick).rotate((0, 0, 0), (1, 0, 0), 180).translate((screw_pos[0], screw_pos[1], moon_z + lid_thick)))

        #the steel tube
        cutter = cutter.add(cq.Workplane("XY").circle(STEEL_TUBE_DIAMETER/2).extrude(1000).translate((0,0,-500)).rotate((0,0,0),(1,0,0), 90).translate((0,0,moon_z)))

        # space_d = self.fixing_screws.get_washer_diameter()+1
        space_d = max(self.fixing_screws.get_nut_containing_diameter(), self.fixing_screws.get_washer_diameter()) + 1

        # space for the two nuts, spring washer and normal washer at the bottom of the moon and nut at the top of the moon
        # nut_space = cq.Workplane("XY").circle(space_d/2).extrude(moon_r)
        # #space for nuts at the top of the moon (like on the front of the hands)
        # nut_space = nut_space.union(cq.Workplane("XY").circle(self.fixing_screws.get_nut_containing_diameter() / 2 + 0.5).extrude(self.moon_complication.moon_radius * 2).translate((0, 0, moon_r)))
        nut_space = cq.Workplane("XY").circle(space_d/2).extrude(moon_r*2 + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT*2)
        #.faces(">Z").workplane().circle(self.fixing_screws.get_nut_containing_diameter()/2+0.5)).extrude(self.moon_complication.moon_radius*2)

        nut_space = nut_space.rotate((0,0,0),(1,0,0),-90).translate(moon_centre_pos).translate((0,-moon_r-TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT, 0))

        cutter = cutter.union(nut_space)

        if self.moon_inside_dial:
            final_wheel_pos = np_to_set3( np.add(self.moon_complication.get_arbor_positions_relative_to_motion_works()[2], (self.plates.hands_position[0], self.plates.hands_position[1], 0)))
            bevel_r = self.moon_complication.bevel_pair.wheel_teeth * self.moon_complication.bevel_pair.module / 2
            # bevel_gear_pair = self.moon_complication.bevel_pair.bevel_gear_pair
            # #from _build_tooth_faces
            # pc_h = np.cos(bevel_gear_pair.gamma_r) * bevel_gear_pair.gs_r  # pitch cone height
            # pc_f = pc_h / np.cos(bevel_gear_pair.gamma_f)  # extended pitch cone flank length
            # pc_rb = pc_f * np.sin(bevel_gear_pair.gamma_f)  # pitch cone base radius

            padding = 3
            increase_fraction = (bevel_r + padding)/bevel_r


            #using a sphere as a rough measure for not clashing with the bevel gear
            bevel_sphere = cq.Workplane("XY").sphere(bevel_r + 2)
            bevel_cone = cq.Solid.makeCone(radius2=0, radius1=bevel_r + padding, height=self.moon_complication.bevel_pair.bevel_gear_pair.gear.cone_h * increase_fraction)
            cutter = cutter.union(bevel_cone.translate(final_wheel_pos).translate((0,0,self.moon_complication.gear_thick)))
            # holder = holder.union(bevel_cone.translate(final_wheel_pos).translate((0,0,self.moon_complication.gear_thick)))

        #experiment, as it looks a bit clunky right now
        # lid = lid.edges(">Z").fillet(1)

        holder = holder.cut(cutter)
        lid = lid.cut(cutter)



        if for_printing:
            holder = holder.rotate((0,0,0),(0,1,0),180)
        else:
            lid = lid.translate((0,0,0.1))

        return [holder, lid]




class SimpleClockPlates:
    '''
    This took a while to settle - clocks before wall_clock_4 will be unlikely to work anymore.

    This produces viable simple wall clocks and also supports being extended for other types of clock plate

    This has become a monster of a class. I think it's better to try and simplify this class and extend it for new types of clock plate, rather than adding yet more options
    to this class.

    TODO in future abstract out just all the useful re-usable bits into a ClockPlatesBase?
    '''


    def __init__(self, going_train, motion_works, pendulum, gear_train_layout=GearTrainLayout.VERTICAL, default_arbor_d=3, pendulum_at_top=True, plate_thick=5, back_plate_thick=None,
                 pendulum_sticks_out=20, name="", heavy=False, extra_heavy=False, motion_works_above=False, pendulum_fixing = PendulumFixing.FRICTION_ROD,
                 pendulum_at_front=True, back_plate_from_wall=0, fixing_screws=None, escapement_on_front=False, chain_through_pillar_required=True,
                 centred_second_hand=False, pillars_separate=True, dial=None, direct_arbor_d=DIRECT_ARBOR_D, huygens_wheel_min_d=15, allow_bottom_pillar_height_reduction=False,
                 bottom_pillars=1, top_pillars=1, centre_weight=False, screws_from_back=None, moon_complication=None, second_hand=True, motion_works_angle_deg=-1, endshake=1,
                 embed_nuts_in_plate=False, extra_support_for_escape_wheel=False, compact_zigzag=False, layer_thick=LAYER_THICK_EXTRATHICK, top_pillar_holds_dial=False,
                 override_bottom_pillar_r=-1, vanity_plate_radius=-1, small_fixing_screws=None, force_escapement_above_hands=False, style=PlateStyle.SIMPLE, pillar_style=PillarStyle.SIMPLE,
                 standoff_pillars_separate=False, texts=None, plaque=None, split_detailed_plate=False):
        '''
        Idea: provide the train and the angles desired between the arbours, try and generate the rest
        No idea if it will work nicely!

        escapement_on_front: if true the escapement is mounted on the front of teh clock (helps with laying out a grasshopper) and if false, inside the plates like the rest of the train
        vanity_plate_radius - if >0 then there's an extra "plate" on the front to hide the motion works
        split_detailed_plate - if the detail is raised on the front plate we'd have to print using hole-in-hole supports for the bearing holes. Some filaments this isn't as clean as others
        so with this option instead the plate is printed in two halves without needing the hole-in-hole supports and relies upon being bolted together.
        '''

        self.pillar_style = pillar_style
        self.style = style
        #for raised edging style
        self.edging_wide = 3
        self.edging_thick=LAYER_THICK*2

        self.export_tolerance = 0.1

        self.split_detailed_plate = split_detailed_plate

        #for other clock plates to override
        self.text_on_standoffs = False
        self.standoff_pillars_separate = standoff_pillars_separate
        #if provided then the text is on a little plaque screwed onto the back instead of printed MMU style
        #TODO front and back plaque options?
        self.plaque = plaque
        self.plaque_pos = (0,0)
        self.plaque_angle = 0

        self.vanity_plate_fixing_positions = []
        #how the pendulum is fixed to the anchor arbour. TODO centralise this
        self.pendulum_fixing = pendulum_fixing
        self.pendulum_at_front = pendulum_at_front

        #if the dial would stick off the top of the front plate the default is to extend the front plate
        #however this can result in plates taht are too large, so instead have a little arm that sticks out the top pillar and extend the length of the dial pillar
        self.top_pillar_holds_dial = top_pillar_holds_dial

        self.layer_thick = layer_thick

        #if spring powered and little_plate_for_pawl is false (only in sub-classes so far)
        self.beefed_up_pawl_thickness = 7.5

        #diameter of the cylinder that forms the arbour that physically links pendulum holder (or crutch in future) and anchor
        self.direct_arbor_d = direct_arbor_d

        self.dial = dial

        #are the main pillars attached to the back plate or independent? currently needs backPlateFromWall to create wall standoffs in order to screw to back plate
        self.pillars_separate = pillars_separate

        #try and put the weight central to the clock. Only currently affects the compact style when using two pillars
        self.centre_weight = centre_weight

        #if the going train supports it, put a second hand on the clock
        self.second_hand = second_hand
        #second hand is centred on the motion works
        self.centred_second_hand = centred_second_hand

        #does the chain/rope/cord pass through the bottom pillar?
        self.chainThroughPillar = chain_through_pillar_required

        #None or a MoonComplication object
        self.moon_complication = moon_complication

        #if escapementOnFront then extend out the front plate to hold the bearing - reduces wobble when platedistance is low
        self.extra_support_for_escape_wheel = extra_support_for_escape_wheel

        # if this is powered by a spring barrel, do we want to support the pawl with a little extra sticky out bit?
        #TODO apply to cord power too?
        self.little_plate_for_pawl = True

        angles_from_minute = None
        anglesFromChain = None

        self.gear_train_layout=gear_train_layout
        self.compact_zigzag = compact_zigzag

        #to print on the back
        self.name = name

        # how much the arbours can wobble back and forth. aka End-shake.
        # 2mm seemed a bit much
        # I've been using 1mm for ages, but clock 12 seemed to have gears binding, but wondering if actually it was gears wedged between the bearings (keeping an eye on it)
        # after the plates flexed over time - new technique of m4 bolts all the way through the pillars may help, but maybe a bit more endshake too?
        self.endshake = endshake

        # override default position of the motion works (for example if it would be in the way of a keywind and it can't go above because there's a moon complication)
        self.motion_works_angle = deg_to_rad(motion_works_angle_deg)

        self.little_arm_to_motion_works = True

        if self.motion_works_angle < 0:
            # is the motion works arbour above the cannon pinion? if centred_second_hand then this is not user-controllable (deprecated - motion_works_angle is more flexible)
            if motion_works_above:
                self.motion_works_angle = math.pi/2
            else:
                #below
                self.motion_works_angle = math.pi*1.5

        #escapement is on top of the front plate
        self.escapement_on_front = escapement_on_front
        self.front_anchor_holder_part_of_dial = False

        #many designs have thet escapement above the hands anyway, but do we force it? currently I think this is a 1:1 mapping with escapement_on_front
        self.force_escapement_above_hands = escapement_on_front or force_escapement_above_hands
        self.going_train = going_train
        #we can have the escape wheel and wheel before that at same y level and both same distance from y axis
        #IDEA - why not with 3 wheels as well? would be less wide
        self.no_upper_wheel_in_centre = self.going_train.wheels > 3 and not self.second_hand

        #if true, mount the escapment on the front of the clock (to show it off or help the grasshopper fit easily)
        #if false, it's between the plates like the rest of the gear train
        #not sure much actually needs to change for the plates?
        # self.escapementOnFront = goingTrain.escapementOnFront
        #use the weight on a pulley with a single loop of chain/rope, going over a ratchet on the front of the clock and a counterweight on the other side from the main weight
        #easiest to implement with a chain
        self.huygens_maintaining_power = going_train.huygens_maintaining_power
        #for plates with very little distance (eg grasshopper) the bottom pillar will be small - but we still need a largeish wheel for the chain
        self.huygens_wheel_min_d = huygens_wheel_min_d

        #is the weight heavy enough that we want to chagne the plate design?
        #will result in wider plates up to the chain wheel
        self.heavy = heavy
        #beef up the pillars as well
        self.extra_heavy = extra_heavy

        if self.extra_heavy:
            self.heavy = True

        #2 or 1?
        self.bottom_pillars = bottom_pillars
        self.top_pillars = top_pillars

        #make the bottom pillar long a thin rather than round?
        self.narrow_bottom_pillar = self.bottom_pillars > 1

        #is the weight danging from a pulley? (will affect screwhole and give space to tie other end of cord)
        self.using_pulley = going_train.use_pulley

        #how much space the crutch will need - used for work out where to put the bearing for the anchor
        self.crutch_space = 10

        self.motion_works = motion_works

        #TODO this is deprecated, remove it
        self.pendulum=pendulum
        #up to and including the anchor
        self.angles_from_minute = angles_from_minute
        self.angles_from_chain=anglesFromChain
        self.plate_thick=plate_thick
        self.back_plate_thick = back_plate_thick
        if self.back_plate_thick is None:
            self.back_plate_thick = self.plate_thick
        #default for anchor, overriden by most arbours
        self.arbor_d=default_arbor_d
        #how chunky to make the bearing holders
        self.bearing_wall_thick = 4

        #for fixing to teh wall
        self.wall_fixing_screw_head_d = 11

        self.pendulum_at_top = pendulum_at_top
        #how far away from the relevant plate (front if pendulumAtFront) the pendulum should be
        self.pendulum_sticks_out = pendulum_sticks_out
        #if this is 0 then pendulumAtFront is going to be needed
        self.back_plate_from_wall = back_plate_from_wall
        self.fixing_screws = fixing_screws
        if self.fixing_screws is None:
            #PREVIOUSLY longest pozihead countersunk screws I can easily get are 25mm long. I have some 40mm flathead which could be deployed if really needed
            #now found supplies of pozihead countersunk screws up to 60mm, so planning to use two screws (each at top and bottom) to hold everything together
            self.fixing_screws = MachineScrew(metric_thread=3, countersunk=True)#, length=25)

        self.motion_works_screws = MachineScrew(metric_thread=self.arbor_d, countersunk=True)
        self.small_fixing_screws = small_fixing_screws
        if self.small_fixing_screws is None:
            #TODO switch over lots of the little bits that currently use motion_works_screws to use small_fixing_screws
            self.small_fixing_screws = MachineScrew(metric_thread=3, countersunk=True)

        self.vanity_plate_radius = vanity_plate_radius
        self.has_vanity_plate = self.vanity_plate_radius > 0
        self.vanity_plate_thick = 2
        self.vanity_plate_pillar_r = self.small_fixing_screws.metric_thread
        self.vanity_plate_base_z = self.front_of_motion_works_wheels_z()

        #for some dials (filled-in ones like tony) it won't be possible to get a screwdriver (or the screw!) in from the front, so instead screw in from the back
        #currently this also implies that the nuts will be sticking out the front plate (I don't want to embed them in the plate and weaken it)
        #originally just a boolean, now a list of booleans for each pillar, starting at hte top. eg top pillar only screws from back: [True, False]
        #now it's a list of list of booleans! [[top0, top1],[bottom0, bottom1]]
        #I should really re-think this.
        self.screws_from_back = screws_from_back
        if self.screws_from_back is None:
            self.screws_from_back = [[False, False], [False, False]]
        #ignore lengths of screws and just put the nuts in the back of the back plate (or wall standoff)
        self.embed_nuts_in_plate = embed_nuts_in_plate
        #by default we assume bolts from front or back with the head embedded in the plate
        #so if you provide pan head screws instead the logic will detect that and instead just put a plain hole and embed nuts in teh back

        # how thick the bearing holder out the back or front should be
        # can't use bearing from ArborForPlate yet as they haven't been generated
        # bit thicker than the front bearing thick because this may have to be printed with supports
        if pendulum_fixing == PendulumFixing.SUSPENSION_SPRING:
            self.rear_standoff_bearing_holder_thick = get_bearing_info(going_train.get_arbour_with_conventional_naming(-1).arbor_d).height + 2
        else:
            self.rear_standoff_bearing_holder_thick = self.plate_thick

        # how much space to leave around the edge of the gears for safety
        self.gear_gap = 3
        # if self.style == ClockPlateStyle.COMPACT:
        #     self.gearGap = 2
        self.small_gear_gap = 2

        self.ideal_key_length = 35

        #if the bottom pillar radius is increased to allow space for the chains to fit through, do we permit the gear wheel to cut into that pillar?
        self.allow_bottom_pillar_height_reduction = allow_bottom_pillar_height_reduction

        if self.allow_bottom_pillar_height_reduction and self.bottom_pillars > 1:
            raise ValueError("Does not support pillar height reduction with more than one pillar")

        self.weight_on_right_side = self.going_train.is_weight_on_the_right()

        self.calc_bearing_positions()
        self.generate_arbours_for_plate()

        if PowerType.is_weight(self.going_train.powered_wheel.type):
            self.weight_driven = True
            self.chain_hole_d = self.going_train.powered_wheel.get_chain_hole_diameter()
        else:
            self.weight_driven = False
        self.chain_hole_d =0

        if self.chain_hole_d < 4:
            self.chain_hole_d = 4

        #set in calc_winding_key_info()
        self.winding_key = None

        self.powered_wheel_r = self.going_train.get_arbor(-self.going_train.powered_wheels).get_max_radius() + self.gear_gap

        self.reduce_bottom_pillar_height = 0
        self.calc_pillar_info(override_bottom_pillar_r)


        #calcualte the positions of the bolts that hold the plates together
        self.calc_fixing_info()


        self.huygens_wheel = None
        #offset in y? This enables the plate to stay smaller (and fit on the print bed) while still offering a large huygens wheel
        self.huygens_wheel_y_offset = 0
        if self.huygens_maintaining_power:
            max_circumference = self.bottom_pillar_r * 1.25 * math.pi
            max_diameter = max_circumference/math.pi
            ratchetOuterD = self.bottom_pillar_r * 2

            if max_diameter < self.huygens_wheel_min_d:
                max_diameter = self.huygens_wheel_min_d
                max_circumference = max_diameter*math.pi
                ratchetOuterD = max_diameter+15
                if ratchetOuterD < self.bottom_pillar_r*2:
                    #have seen this happen, though I think it's rare
                    ratchetOuterD = self.bottom_pillar_r * 2
                self.huygens_wheel_y_offset = ratchetOuterD / 2 - self.bottom_pillar_r

            ratchetOuterThick = 3
            ratchet_thick=5
            #need a powered wheel and ratchet on the front!
            if self.going_train.powered_wheel.type == PowerType.CHAIN:

                self.huygens_wheel = PocketChainWheel(ratchet_thick=5, max_circumference=max_circumference, wire_thick=self.going_train.powered_wheel.chain_thick,
                                                      width=self.going_train.powered_wheel.chain_width, inside_length=self.going_train.powered_wheel.chain_inside_length,
                                                      tolerance=self.going_train.powered_wheel.tolerance, ratchetOuterD=self.bottom_pillar_r * 2, ratchetOuterThick=ratchetOuterThick)
            elif self.going_train.powered_wheel.type == PowerType.CHAIN2:
                self.huygens_wheel = PocketChainWheel2(ratchet_thick=5, max_diameter=max_diameter, chain=self.going_train.powered_wheel.chain, loose_on_rod=True,
                                                       ratchetOuterD=ratchetOuterD, ratchetOuterThick=ratchetOuterThick, arbor_d=self.going_train.powered_wheel.arbor_d)
            elif self.going_train.powered_wheel.type == PowerType.ROPE:
                huygens_diameter = max_diameter*0.95
                print("Huygens wheel diameter",huygens_diameter)
                self.huygens_wheel = RopeWheel(diameter=huygens_diameter, ratchet_thick=ratchet_thick, rope_diameter=self.going_train.powered_wheel.rope_diameter, o_ring_diameter=get_o_ring_thick(huygens_diameter - self.going_train.powered_wheel.rope_diameter * 2),
                                               hole_d=self.going_train.powered_wheel.hole_d, ratchet_outer_d=self.bottom_pillar_r * 2, ratchet_outer_thick=ratchetOuterThick)
            else:
                raise ValueError("Huygens maintaining power not currently supported with {}".format(self.going_train.powered_wheel.type.value))

        self.hands_position = self.bearing_positions[self.going_train.powered_wheels][:2]

        if self.centred_second_hand:

            seconds_arbor = -2
            if self.going_train.has_second_hand_on_last_wheel():
                seconds_arbor = -3

            self.hands_position = [self.bearing_positions[seconds_arbor][0], self.bearing_positions[seconds_arbor][1]]
            minute_wheel_pos = self.bearing_positions[self.going_train.powered_wheels][:2]

            #adjust motion works size
            minute_wheel_to_hands = np_to_set(np.subtract(minute_wheel_pos, self.hands_position))

            minute_wheel_to_hands_distance = np.linalg.norm(minute_wheel_to_hands)
            minute_wheel_to_hands_angle = math.atan2(minute_wheel_to_hands[1], minute_wheel_to_hands[0])

            arbor_distance = minute_wheel_to_hands_distance / 2

            if abs(self.motion_works_angle - minute_wheel_to_hands_angle) - math.pi > 0.01:
                #motion works angle will offset the centre arbor

                line_from_hands = Line(self.hands_position, angle=self.motion_works_angle)
                mid_line = Line(average_of_two_points(minute_wheel_pos, self.hands_position), angle=minute_wheel_to_hands_angle + math.pi / 2)

                mid_arbor_pos = line_from_hands.intersection(mid_line)
                arbor_distance = np.linalg.norm(np.subtract(mid_arbor_pos, minute_wheel_pos))


            self.motion_works.calculate_size(arbor_distance=arbor_distance)

            #override motion works position
            #note - new idea, allow this to function like the compact design of the plates
            # self.motion_works_angle = math.pi/2 if not self.pendulum_at_top else math.pi * 1.5





        motionWorksDistance = self.motion_works.get_arbor_distance()
        # get position of motion works relative to the minute wheel
        if gear_train_layout == GearTrainLayout.ROUND:
            # place the motion works on the same circle as the rest of the bearings
            angle = self.hands_on_side*2 * math.asin(motionWorksDistance / (2 * self.compact_radius))
            compactCentre = (0, self.compact_radius)
            minuteAngle = math.atan2(self.bearing_positions[self.going_train.powered_wheels][1] - compactCentre[1], self.bearing_positions[self.going_train.powered_wheels][0] - compactCentre[0])
            motionWorksPos = polar(minuteAngle - angle, self.compact_radius)
            motionWorksPos = (motionWorksPos[0] + compactCentre[0], motionWorksPos[1] + compactCentre[1])
            self.motion_works_relative_pos = (motionWorksPos[0] - self.bearing_positions[self.going_train.powered_wheels][0], motionWorksPos[1] - self.bearing_positions[self.going_train.powered_wheels][1])
        elif self.gear_train_layout == GearTrainLayout.COMPACT and motion_works_above and self.has_seconds_hand() and not self.centred_second_hand and self.extra_heavy:
            '''
            niche case maybe?
            put the motion works along the arm to the offset gear
            '''
            direction = np.subtract(self.bearing_positions[self.going_train.powered_wheels + 1][:2], self.bearing_positions[self.going_train.powered_wheels][:2])
            #make unit vector
            direction = np.multiply(direction, 1/np.linalg.norm(direction))

            self.motion_works_relative_pos = np_to_set(np.multiply(direction, motionWorksDistance))
        else:
            # motion works is directly below the minute rod by default, or whatever angle has been set
            self.motion_works_relative_pos = polar(self.motion_works_angle, motionWorksDistance)

        self.motion_works_pos = np_to_set(np.add(self.hands_position, self.motion_works_relative_pos))

        #calculate position even if it's not applicable to this clock
        friction_clip_dir = np.multiply(self.motion_works_relative_pos, -1/np.linalg.norm(self.motion_works_relative_pos))
        friction_clip_distance = self.motion_works.friction_ring_r*2.5
        self.cannon_pinion_friction_clip_pos = np_to_set(np.add(self.hands_position, np.multiply(friction_clip_dir, friction_clip_distance)))
        self.cannon_pinion_friction_clip_fixings_pos = [
            np_to_set(np.add(self.cannon_pinion_friction_clip_pos, (-self.plate_width / 5, -self.plate_width /  5))),
            np_to_set(np.add(self.cannon_pinion_friction_clip_pos, (self.plate_width / 5, self.plate_width / 5)))
        ]

        #even if it's not used:

        #TODO calculate so it's always just big enough?
        self.motion_works_holder_length = 30
        self.motion_works_holder_wide = self.plate_width
        self.motion_works_fixings_relative_pos = [(-self.plate_width / 4, self.motion_works_holder_length / 2) ,
                                                  (self.plate_width / 4, -(self.motion_works_holder_length / 2))]

        self.top_of_hands_z = self.motion_works.get_cannon_pinion_effective_height() + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT

        self.dial_top_above_front_plate = False
        self.dial_fixing_positions = []
        self.top_dial_fixing_y = -1

        if self.dial is not None:
            #calculate dial height after motion works gears have been generated, in case the height changed with the bearing
            # height of dial from top of front plate
            # previously given 8mm of clearance, but this was more than enough, so reducing down to 4
            # looks like I later reduced it to 3 (I think after clock 12?)
            self.dial_z = self.bottom_of_hour_hand_z() - self.dial.thick - self.dial.get_hand_space_z()
            if self.has_seconds_hand() and not self.centred_second_hand:
                #mini second hand! give a smidge more clearance
                self.dial_z -= 2

            print("dial z", self.dial_z)
            dial_support_d = self.plate_width

            if self.dial.is_full_dial():
                #free placement of the dial fixings
                if self.bottom_pillars > 1 and self.gear_train_layout == GearTrainLayout.COMPACT:
                    #put two fixings on either side of the chain wheel
                    #currently this is designed around tony the clock, and should be made more generic in the future
                    from_pillar_x = self.bottom_pillar_width if self.narrow_bottom_pillar else self.bottom_pillar_r * 1.5
                    dial_fixings = [
                        (abs(self.bottom_pillar_positions[0][0]) - from_pillar_x, self.bottom_pillar_positions[0][1]),
                        (-abs(self.bottom_pillar_positions[0][0]) + from_pillar_x, self.bottom_pillar_positions[0][1]),
                        (0, self.bearing_positions[-2][1])
                    ]

                    dial_fixings_relative_to_dial = []
                    dial_centre = tuple(self.bearing_positions[self.going_train.powered_wheels][:2])
                    # for fixing in dial_fixings:
                    #     relative_pos = npToSet(np.subtract(fixing, tuple(dial_centre)))
                    #     dial_fixings_relative_to_dial.append(relative_pos)
                    #array of arrays because we only want one screw per pillar here
                    dial_fixings_relative_to_dial = [[np_to_set(np.subtract(pos, dial_centre))] for pos in dial_fixings]

                    for dial_fixing in dial_fixings_relative_to_dial:
                        if np.linalg.norm(dial_fixing) > self.dial.outside_d*0.9:
                            #TODO actually relocate them, for now: cry
                            print("Dial fixings probably aren't inside dial!")

                    self.dial.override_fixing_positions(dial_fixings_relative_to_dial)
                    dial_support_d = 15


            if self.has_seconds_hand():
                second_hand_relative_pos = np_to_set(np.subtract(self.get_seconds_hand_position(), self.hands_position))

                if self.centred_second_hand:
                    # second_hand_mini_dial_d = -1
                    second_hand_relative_pos = None
                # else:
                    # distance_to_seconds = np.linalg.norm(second_hand_relative_pos)
                    #just overlapping a tiny bit
                    # second_hand_mini_dial_d = (self.dial.inner_r - distance_to_seconds + 2)*2
                    # print("second_hand_mini_dial_d: {}".format(second_hand_mini_dial_d))

                self.dial.configure_dimensions(support_length=self.dial_z, support_d=dial_support_d,second_hand_relative_pos=second_hand_relative_pos )
            else:
                self.dial.configure_dimensions(support_length=self.dial_z, support_d=dial_support_d)


              # [npToSet(np.add(pos, self.hands_position)) for pos in self.dial.get_fixing_positions()]
            for pos_list in self.dial.get_fixing_positions():
                for pos in pos_list:
                    # inverting x because dial is "backwards"
                    self.dial_fixing_positions.append(np_to_set(np.add((-pos[0], pos[1]), self.hands_position)))

            if len(self.dial_fixing_positions) > 0:
                self.top_dial_fixing_y = max([pos[1] for pos in self.dial_fixing_positions])

                self.dial_top_above_front_plate = self.top_dial_fixing_y > self.top_pillar_positions[0][1] and self.top_dial_fixing_y > self.bearing_positions[-1][1]
            else:
                self.dial_top_above_front_plate = False


            '''
            getting messy - if dial_top_above_front_plate then we need to lengthen the supports, but we couldn't do this when we called configure_dimensions because we
            didn't know where those supports were. could probably refactor, for now just hack it
            '''

            if self.dial_top_above_front_plate and self.top_pillar_holds_dial:
                front_plate_thick = self.get_plate_thick(back=False)
                self.dial.support_length += front_plate_thick
                #cut out for the front plate
                self.dial.subtract_from_supports = (cq.Workplane("XY").circle(self.top_pillar_r+0.5).extrude(front_plate_thick+0.5)
                                                    .translate(np_to_set(np.subtract(self.top_pillar_positions[0], self.hands_position)))
                                                    .translate((0,0, self.dial.thick + self.dial.support_length - front_plate_thick - 0.5)))






        # if this has a key (do after we've calculated the dial z)
        if (self.going_train.powered_wheel.type == PowerType.CORD and self.going_train.powered_wheel.use_key) or not self.weight_driven:
            self.calc_winding_key_info()


        self.front_z = self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False)

        self.moon_holder = None

        if self.moon_complication is not None:
            self.moon_holder = MoonHolder(self, self.moon_complication, self.motion_works_screws)

        #cache stuff that's needed multiple times to speed up generating clock
        self.fixing_screws_cutter = None
        self.need_motion_works_holder = self.calc_need_motion_works_holder()

        self.texts = texts
        if self.texts is None:
            self.texts = [
                self.name,
                "{:.1f}cm".format(self.going_train.pendulum_length_m * 100),
                "{}".format(datetime.date.today().strftime('%Y-%m-%d')),
                "Luke Wallin",
            ]

        if self.plaque is not None:
            self.calc_plaque_config()

    def get_moon_holder_info(self):
        '''
        assumes moon is on a little stick above the dial
        TODO support inside dial
        '''
        if self.moon_complication is None:
            raise ValueError("There is no moon")

        max_y = self.top_pillar_positions[0][1] + self.top_pillar_r

        # top of the last wheel in the complication
        min_y = self.moon_complication.get_arbor_positions_relative_to_motion_works()[-1][1] + self.hands_position[1] + self.moon_complication.pairs[2].wheel.get_max_radius()

        height = max_y - min_y
        centre_y = (max_y + min_y) / 2
        return {"y": centre_y, "wide": self.plate_width, "height": height}

    def get_rod_lengths(self):
        '''
        TODO
        returns ([rod lengths, in same order as all_pillar_positions] , [base of rod z])
        '''
        return ([], [])
    def get_plate_shape(self):

        if self.gear_train_layout == GearTrainLayout.ROUND:
            # plate classes and gear train layouts are all a bit muddled and closely coupled, needs tidying up
            return PlateShape.SIMPLE_ROUND

        return PlateShape.SIMPLE_VERTICAL

    def generate_arbours_for_plate(self):

        self.arbors_for_plate = []

        print("Plate distance", self.plate_distance)

        #configure stuff for the arbours, now we know their absolute positions
        # poweredWheel=self.goingTrain.getArbourWithConventionalNaming(0)
        # poweredWheelBracingR = poweredWheel.distanceToNextArbour - self.goingTrain.getArbourWithConventionalNaming(1).getMaxRadius() - self.gearGap
        #
        # #no need for it to be massive
        # poweredWheelBracingR = min(10,poweredWheelBracingR)
        # poweredWheel.setArbourExtensionInfo(rearSide=self.bearingPositions[0][2], maxR=poweredWheelBracingR)

        for i,bearingPos in enumerate(self.bearing_positions):
            arbour = self.going_train.get_arbour_with_conventional_naming(i)
            if i < self.going_train.wheels + self.going_train.powered_wheels - 2:
                maxR = arbour.distance_to_next_arbour - self.going_train.get_arbour_with_conventional_naming(i + 1).get_max_radius() - self.small_gear_gap
            else:
                maxR = 0

            #deprecated way of doing it - passing loads of info to the Arbour class. still used only for the chain wheel
            # arbour.setPlateInfo(rearSideExtension=bearingPos[2], maxR=maxR, frontSideExtension=self.plateDistance - self.endshake - bearingPos[2] - arbour.getTotalThickness(),
            #                     frontPlateThick=self.getPlateThick(back=False), pendulumSticksOut=self.pendulumSticksOut, backPlateThick=self.getPlateThick(back=True), endshake=self.endshake,
            #                     plateDistance=self.plateDistance, escapementOnFront=self.escapementOnFront)

            try:
                bearing = get_bearing_info(arbour.arbor_d)
            except:
                #mega bodge, TODO
                #for the spring barrel the arbor isn't a threaded rod, so isn't a nice number for a bearing.
                #need to work out what to do properly here
                bearing = get_bearing_info(round(arbour.arbor_d))
            front_anchor_from_plate = -1

            if self.escapement_on_front:
                front_anchor_from_plate = 8 + self.endshake - self.going_train.escapement.get_anchor_thick()/2
                # if self.style in [PlateStyle.RAISED_EDGING]:
                #     front_anchor_from_plate += self.edging_thick
                if self.has_vanity_plate:
                    front_anchor_from_plate = self.vanity_plate_base_z + self.vanity_plate_thick + self.endshake + 2
                if self.going_train.escapement.get_anchor_thick() < 10:
                    #this won't be thick enough for the escape wheel to have much of a cylinder to grip the rod - so it might be wonky.
                    #so stick the esacpement out a bit further#
                    front_anchor_from_plate = 10


            #new way of doing it, new class for combining all this logic in once place
            arbourForPlate = ArborForPlate(arbour, self, bearing_position=bearingPos, arbour_extension_max_radius=maxR, pendulum_sticks_out=self.pendulum_sticks_out,
                                           pendulum_at_front=self.pendulum_at_front, bearing=bearing, escapement_on_front=self.escapement_on_front, back_from_wall=self.back_plate_from_wall,
                                           endshake=self.endshake, pendulum_fixing=self.pendulum_fixing, direct_arbor_d=self.direct_arbor_d, crutch_space=self.crutch_space,
                                           previous_bearing_position=self.bearing_positions[i - 1], front_anchor_from_plate=front_anchor_from_plate,
                                           pendulum_length=self.going_train.pendulum_length_m*1000)
            self.arbors_for_plate.append(arbourForPlate)


    def calc_pillar_info(self, override_bottom_pillar_r=-1):
        '''
        Calculate (and set) topPillarPos, topPillarR, bottomPillarPos, bottomPillarR, holderWide, reduce_bottom_pillar_height
        '''


        bearingInfo = get_bearing_info(self.arbor_d)
        # width of thin bit
        self.plate_width = bearingInfo.outer_d + self.bearing_wall_thick * 2
        self.min_plate_width = self.plate_width
        if self.heavy or self.extra_heavy:
            self.plate_width *= 1.2

        # original thinking was to make it the equivilant of a 45deg shelf bracket, but this is massive once cord wheels are used
        # so instead, make it just big enough to contain the holes for the chains/cord
        if self.weight_driven :
            furthest_x = max([abs(holePos[0][0]) for holePos in self.going_train.powered_wheel.get_chain_positions_from_top()])

            # juuust wide enough for the small bits on the edge of the bottom pillar to print cleanly
            min_distance_for_chain_holes = (furthest_x * 2 + self.chain_hole_d + 5) / 2
        else:
            min_distance_for_chain_holes = 0

        if self.heavy:
            self.bottom_pillar_r = self.plate_distance / 2
        else:
            self.bottom_pillar_r = min_distance_for_chain_holes

        if self.bottom_pillar_r < self.plate_width/2:
            #rare, but can happen
            self.bottom_pillar_r = self.plate_width / 2

        self.reduce_bottom_pillar_height = 0
        if self.bottom_pillar_r < min_distance_for_chain_holes and self.chainThroughPillar:
            if self.allow_bottom_pillar_height_reduction:
                self.reduce_bottom_pillar_height = min_distance_for_chain_holes - self.bottom_pillar_r
            self.bottom_pillar_r = min_distance_for_chain_holes

        #I've needed to reprint pillars more than I would like, this helps when changing endshake
        if override_bottom_pillar_r > 0:
            self.bottom_pillar_r = override_bottom_pillar_r

        print("bottom pillar r: {}".format(self.bottom_pillar_r))

        if self.narrow_bottom_pillar:
            self.bottom_pillar_height = self.bottom_pillar_r * 2
            # I hadn't measured an m4 nut, and now I've printed half the clock!
            #TODO fix this later!
            self.bottom_pillar_width = 14.46854441470986
            # self.bottom_pillar_width = self.fixingScrews.get_nut_containing_diameter() + 5
            print("bottom_pillar_width", self.bottom_pillar_width)

        self.top_pillar_r = self.plate_width / 2

        anchorSpace = bearingInfo.outer_d / 2 + self.gear_gap
        if self.pendulum_fixing == PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS:
            anchorSpace = self.direct_arbor_d*2 + self.gear_gap

        # find the Y position of the bottom of the top pillar
        topY = self.bearing_positions[0][1]
        if self.gear_train_layout == GearTrainLayout.ROUND:
            # find the highest point on the going train
            # TODO for potentially large gears this might be lower if they're spaced right
            for i in range(len(self.bearing_positions) - 1):
                y = self.bearing_positions[i][1] + self.going_train.get_arbour_with_conventional_naming(i).get_max_radius() + self.gear_gap
                if y > topY:
                    topY = y
        else:

            topY = self.bearing_positions[-1][1] + max(self.arbors_for_plate[-1].get_max_radius(above=True), bearingInfo.outer_d / 2) + self.gear_gap

        if self.bottom_pillars > 1:
            #TODO optimal placement of pillars, for now let's just get them working
            # #take into account the chain wheel might not be directly below the minute wheel
            # from_lowest_wheel = self.arboursForPlate[0].arbour.getMaxRadius() + self.bottomPillarR + self.gearGap
            # from_next_wheel = self.arboursForPlate[1].arbour.getMaxRadius() + self.bottomPillarR + self.gearGap
            # between_wheels = np.linalg.norm(np.subtract(self.bearingPositions[0][:2], self.bearingPositions[1][:2]))
            pillar_width = self.bottom_pillar_width if self.narrow_bottom_pillar else self.bottom_pillar_r * 2
            chain_wheel_r = self.arbors_for_plate[0].arbor.get_max_radius() + self.gear_gap
            self.bottom_pillar_positions=[
                (self.bearing_positions[0][0] - (chain_wheel_r + pillar_width / 2), self.bearing_positions[0][1]),
                (self.bearing_positions[0][0] + (chain_wheel_r + pillar_width / 2), self.bearing_positions[0][1]),
            ]
        else:
            self.bottom_pillar_positions = [[self.bearing_positions[0][0], self.bearing_positions[0][1] - self.powered_wheel_r - self.bottom_pillar_r + self.reduce_bottom_pillar_height]]
        
        self.top_pillar_positions = [(self.bearing_positions[0][0], topY + self.top_pillar_r)]

        if self.bottom_pillars > 1 and self.huygens_maintaining_power:
            raise ValueError("Don't currently support huygens with multiple bottom pillars")
        self.huygens_wheel_pos = self.bottom_pillar_positions[0]

    def calc_fixing_info(self):
        # fixing positions to plates and pillars together
        self.plate_top_fixings = []
        # (self.top_pillar_positions[0] - self.top_pillar_r / 2, self.top_pillar_positions[1]), (self.top_pillar_positions[0] + self.top_pillar_r / 2, self.top_pillar_positions[1])]
        for top_pillar_pos in self.top_pillar_positions:
            self.plate_top_fixings += [
                (top_pillar_pos[0] - self.top_pillar_r / 2, top_pillar_pos[1]),
                (top_pillar_pos[0] + self.top_pillar_r / 2, top_pillar_pos[1])
            ]

        self.plate_bottom_fixings = []
        for bottom_pillar_pos in self.bottom_pillar_positions:
            self.plate_bottom_fixings += [
                (bottom_pillar_pos[0], bottom_pillar_pos[1] + self.bottom_pillar_r * 0.5 - self.reduce_bottom_pillar_height / 3),
                (bottom_pillar_pos[0], bottom_pillar_pos[1] - self.bottom_pillar_r * 0.5)
            ]
        self.plate_fixings = self.plate_top_fixings + self.plate_bottom_fixings


    def calc_bearing_positions(self):
        '''
        TODO, with an overhaul of GoingTrain this should layout the gears in 2D, then lay them out vertically
        GoingTrain should then be free from figuring out all the pinion in front/rear and front/back powered wheel stuff


        '''
        # if angles are not given, assume clock is entirely vertical, unless overriden by style below

        if self.angles_from_minute is None:
            # assume simple pendulum at top
            angle = math.pi / 2 if self.pendulum_at_top else math.pi / 2

            # one extra for the anchor
            self.angles_from_minute = [angle for i in range(self.going_train.wheels + 1)]
        if self.angles_from_chain is None:
            angle = math.pi / 2 if self.pendulum_at_top else -math.pi / 2

            self.angles_from_chain = [angle for i in range(self.going_train.powered_wheels)]

        if self.gear_train_layout == GearTrainLayout.COMPACT:
            '''
            idea for even more compact: in a loop guess at the first angle, then do all the next angles such that it's as compact as possible without the wheels touching each other
            then see if it's possible to put the pendulum directly above the hands
            if it's not, tweak the first angle and try again
            
            current implementation: a line of gears vertically and then every other gear is just off to one side
            Not sure if peak compactness but keeps the plate design easier
            '''
            # if self.goingTrain.chainWheels > 0:

            #thoughts: make which side the gears stick out adjustable?
            on_side = +1

            if self.compact_zigzag:
                on_side = -1
            '''
            Have a line of gears vertical from hands to anchor, and any gears in between off to one side
            '''


            if self.going_train.powered_wheels == 2:
                first_powered_wheel_to_second_powered_wheel = self.going_train.get_arbour_with_conventional_naming(0).distance_to_next_arbour
                second_powered_wheel_to_minute_wheel = self.going_train.get_arbour_with_conventional_naming(1).distance_to_next_arbour
                first_powered_wheel_to_minute_wheel = self.going_train.get_arbour_with_conventional_naming(0).get_max_radius() + self.going_train.get_arbour_with_conventional_naming(2).pinion.get_max_radius() + self.small_gear_gap
                b = first_powered_wheel_to_second_powered_wheel
                c = second_powered_wheel_to_minute_wheel
                a = first_powered_wheel_to_minute_wheel
                # cosine law
                angle = math.acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b))
                self.angles_from_chain[0] = math.pi / 2 + on_side * angle
                minute_wheel_relative_pos = (0,first_powered_wheel_to_minute_wheel)
                second_powered_wheel_pos =  polar(self.angles_from_chain[0], first_powered_wheel_to_second_powered_wheel)
                minute_wheel_from_second_powered_wheel = np_to_set(np.subtract(minute_wheel_relative_pos, second_powered_wheel_pos))
                self.angles_from_chain[1] = math.atan2(minute_wheel_from_second_powered_wheel[1], minute_wheel_from_second_powered_wheel[0])
                if self.compact_zigzag:
                    on_side *= -1

            '''
            4 wheels and escape wheel would not be directly above hands using above logic
            Place the escape wheel directly above the hands and then put the second and third wheel off to the side
            Trying putting the third wheel directly left of the escape wheel and using the normal compact logic to place the second wheel
            
            
            PLAN: when we don't have a second hand or need escapement above the hands we can do compact with 4 wheels better:
            basically rotate the third wheel and escape wheel around slightly to the right so they're both equidistant from the line above the hands
            this will be useful for the moon escapement (so the fixing doesn't clash with a bearing) and I think will result in an even more compact design
            '''
            forcing_escape_wheel_above_hands = self.going_train.wheels > 3 and self.force_escapement_above_hands
            forcing_escape_wheel_slightly_off_centre = self.no_upper_wheel_in_centre#self.going_train.wheels > 3 and not self.second_hand



            #if we're forcing the escapement above the hands and have more than 3 wheels, we don't want to default to this logic as the escape wheel
            #will be off to one side
            #if we do have 3 wheels then the escape wheel is above the hands
            minute_wheel_to_second_wheel = self.going_train.get_arbor(0).distance_to_next_arbour
            second_wheel_to_third_wheel = self.going_train.get_arbor(1).distance_to_next_arbour

            third_wheel_pinion_r = self.going_train.get_arbor(2).pinion.get_max_radius()
            #bit of hackery here, we should really work out exactly where all the pinions and wheels will line up, then we don't need to guess
            if self.going_train.get_arbor(1).pinion_extension > 0:
                #...this is guessing how thick the arbor extension will be, which is calcualted in ArborForPlate. TODO
                third_wheel_pinion_r = self.going_train.get_arbor(2).arbor_d

            minute_wheel_to_third_wheel = self.going_train.get_arbor(0).get_max_radius() + third_wheel_pinion_r + self.small_gear_gap
            minute_wheel_pos = (0, 0)
            if forcing_escape_wheel_above_hands or forcing_escape_wheel_slightly_off_centre:
                minute_wheel_r = self.going_train.get_arbor(0).get_max_radius()
                escape_wheel_arbor_r = self.going_train.get_arbor(3).get_arbor_extension_r()
                # #HACK HACK HACK TEMP instead of self.going_train.get_arbor(3).get_arbor_extension_r() use the old value of 2
                # escape_wheel_arbor_r = self.going_train.get_arbor(3).get_rod_d()
                # #MORE HACK TODO REMOVE ME
                # escape_wheel_arbor_r = 2
                minute_wheel_to_escape_wheel = self.going_train.get_arbor(0).get_max_radius() + escape_wheel_arbor_r + self.small_gear_gap
                third_wheel_to_escape_wheel = self.going_train.get_arbor(2).distance_to_next_arbour
                escape_wheel_to_anchor = self.going_train.get_arbor(3).distance_to_next_arbour

                if forcing_escape_wheel_slightly_off_centre:
                    escape_wheel_angle_from_hands = math.pi/2 - on_side*math.asin((third_wheel_to_escape_wheel/2)/minute_wheel_to_escape_wheel)
                    escape_wheel_relative_pos = polar(escape_wheel_angle_from_hands, minute_wheel_to_escape_wheel)
                    #arbitarily choosing mirror of escape wheel
                    third_wheel_pos = (-escape_wheel_relative_pos[0], escape_wheel_relative_pos[1])
                    # anchor is directly above minutes
                    #TODO does htis work if we're on the right hand side?
                    self.angles_from_minute[3] = math.pi - on_side*math.acos(escape_wheel_relative_pos[0]/escape_wheel_to_anchor)
                else:


                    escape_wheel_relative_pos = (0, minute_wheel_to_escape_wheel)

                    third_wheel_pos = ( -on_side*third_wheel_to_escape_wheel, minute_wheel_to_escape_wheel)
                    # anchor is directly above escape wheel
                    self.angles_from_minute[3] = math.pi / 2


                minute_wheel_to_third_wheel = distance_between_two_points(minute_wheel_pos, third_wheel_pos)
                #escape wheel is directly right of third wheel
                self.angles_from_minute[2] = math.pi if on_side < 0 else 0
            else:
                third_wheel_pos = (0, minute_wheel_to_third_wheel)

            #this is the same regardless of forcing_escape_wheel_location, only the position of the third wheel changes
            b = minute_wheel_to_second_wheel
            c = second_wheel_to_third_wheel
            a = minute_wheel_to_third_wheel
            # cosine law
            angle = math.acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b))

            # third_wheel_line = Line(minute_wheel_pos, anotherPoint=third_wheel_pos)
            # self.angles_from_minute[0] = third_wheel_line.getAngle() + on_side * angle
            third_wheel_angle = math.atan2(third_wheel_pos[1], third_wheel_pos[0])
            self.angles_from_minute[0] = third_wheel_angle + on_side * angle

            if self.compact_zigzag:
                on_side *= -1

            second_wheel_pos = polar(self.angles_from_minute[0], minute_wheel_to_second_wheel)
            third_wheel_from_second_wheel = np_to_set(np.subtract(third_wheel_pos, second_wheel_pos))
            self.angles_from_minute[1] = math.atan2(third_wheel_from_second_wheel[1], third_wheel_from_second_wheel[0])



            #TODO if the second wheel would clash with the powered wheel, push the third wheel up higher
            #
            if self.going_train.wheels > 3 and not (forcing_escape_wheel_above_hands or forcing_escape_wheel_slightly_off_centre):
                #stick the escape wheel out too
                third_wheel_to_escape_wheel = self.going_train.get_arbor(2).distance_to_next_arbour
                escape_wheel_to_anchor = self.going_train.get_arbor(3).distance_to_next_arbour
                #third_wheel_to_anchor is a bit tricky to calculate. going to try instead just choosing an angle
                #TODO could make anchor thinner and then it just needs to avoid the rod
                third_wheel_to_anchor = self.going_train.get_arbour_with_conventional_naming(-1).get_max_radius() + self.going_train.get_arbor(2).get_max_radius() + self.small_gear_gap

                b = third_wheel_to_escape_wheel
                c = escape_wheel_to_anchor
                a = third_wheel_to_anchor
                # cosine law
                angle = math.acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b))
                self.angles_from_minute[2] = math.pi / 2 + on_side * angle

                # #choosing an angle manually:
                # self.anglesFromMinute[2] = math.pi/2 + on_side*self.goingTrain.escapement.escaping_arc*4

                escape_wheel_pos = polar(self.angles_from_minute[2], third_wheel_to_escape_wheel)
                angle = math.acos(abs(escape_wheel_pos[0])/escape_wheel_to_anchor)
                angle = abs(math.pi/2 - angle)
                self.angles_from_minute[3] = math.pi/2 - on_side*angle



            #aim: have pendulum directly above hands
            positions = [(0,0)]
            for i in range(1, self.going_train.wheels):
                positions.append(np_to_set(np.add(positions[i - 1], polar(self.angles_from_minute[i - 1], self.going_train.get_arbor(i - 1).distance_to_next_arbour))))

            escape_wheel_to_anchor = self.going_train.get_arbor(-2).distance_to_next_arbour
            if escape_wheel_to_anchor < abs(positions[-1][0]):
                #need to re-think how this works
                raise ValueError("Cannot put anchor above hands without tweaking")

            if self.bottom_pillars > 1 and not self.using_pulley and self.going_train.powered_wheels > 0 and self.centre_weight:
                #put chain in the centre. this works (although lots of things assume the bottom bearing is in the centre)
                #but I'm undecided if I actually want it - if we have two screwholes is that sufficient? the reduction in height is minimal
                x = self.going_train.powered_wheel.diameter / 2
                r = self.going_train.get_arbour_with_conventional_naming(0).distance_to_next_arbour
                angle = math.acos(x/r)
                if self.weight_on_right_side:
                    self.angles_from_chain[0] = math.pi - angle
                else:
                    self.angles_from_chain[0] = angle



        if self.gear_train_layout == GearTrainLayout.ROUND:

            # TODO decide if we want the train to go in different directions based on which side the weight is
            self.hands_on_side = -1 if self.going_train.is_weight_on_the_right() else 1
            arbours = [self.going_train.get_arbour_with_conventional_naming(arbour) for arbour in range(self.going_train.wheels + self.going_train.powered_wheels)]
            distances = [arbour.distance_to_next_arbour for arbour in arbours]
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
                '''
                Calculate angle of the isololese triangle with the distance at the base and radius as the other two sides
                then work around the arc to get the positions
                then calculate the relative angles so the logic for finding bearing locations still works
                bit over complicated
                '''
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

        # [[x,y,z],]
        # for everything, arbours and anchor
        self.bearing_positions = []
        # TODO consider putting the anchor on a bushing
        # self.bushingPositions=[]
        self.arbourThicknesses = []

        # height of the centre of the wheel that will drive the next pinion
        drivingZ = 0
        for i in range(-self.going_train.powered_wheels, self.going_train.wheels + 1):
            # print(str(i))
            if i == -self.going_train.powered_wheels:
                # the wheel with chain wheel ratchet
                # assuming this is at the very back of the clock
                # note - this is true when chain *is* at the back, when the chain is at the front the bearingPositions will be relative, not absolute
                pos = [0, 0, 0]
                self.bearing_positions.append(pos)
                # note - this is the chain wheel, which has the wheel at the back, but only pretends to have the pinion at the back for calculating the direction of the rest of the train
                drivingZ = self.going_train.get_arbor(i).get_wheel_centre_z()
                self.arbourThicknesses.append(self.going_train.get_arbor(i).get_total_thickness())
                # print("pinionAtFront: {} wheel {} drivingZ: {}".format(self.goingTrain.getArbour(i).pinionAtFront, i, drivingZ), pos)
            else:
                r = self.going_train.get_arbor(i - 1).distance_to_next_arbour
                # print("r", r)
                # all the other going wheels up to and including the escape wheel
                if i == self.going_train.wheels:
                    # the anchor
                    if self.escapement_on_front:
                        # there is nothing between the plates for this
                        self.arbourThicknesses.append(0)
                        # don't do anything else
                    else:
                        escapement = self.going_train.get_arbor(i).escapement
                        baseZ = drivingZ - self.going_train.get_arbor(i - 1).wheel_thick / 2 + escapement.get_wheel_base_to_anchor_base_z()
                        self.arbourThicknesses.append(escapement.get_anchor_thick())
                    # print("is anchor")
                else:
                    # any of the other wheels
                    # pinionAtBack = not pinionAtBack
                    # print("drivingZ at start:{} pinionToWheel: {} pinionCentreZ: {}".format(drivingZ, self.goingTrain.getArbour(i).getPinionToWheelZ(), self.goingTrain.getArbour(i).getPinionCentreZ()))
                    pinionToWheel = self.going_train.get_arbor(i).get_pinion_to_wheel_z()
                    pinionZ = self.going_train.get_arbor(i).get_pinion_centre_z()
                    baseZ = drivingZ - pinionZ

                    drivingZ = drivingZ + pinionToWheel
                    # massive bodge here, the arbour doesn't know about the escapement being on the front yet
                    self.going_train.get_arbor(i).escapement_on_front = self.escapement_on_front
                    arbourThick = self.going_train.get_arbor(i).get_total_thickness()

                    self.arbourThicknesses.append(arbourThick)

                if i <= 0:
                    angle = self.angles_from_chain[i - 1 + self.going_train.powered_wheels]
                else:
                    angle = self.angles_from_minute[i - 1]
                v = polar(angle, r)
                # v = [v[0], v[1], baseZ]
                lastPos = self.bearing_positions[-1]
                # pos = list(np.add(self.bearingPositions[i-1],v))
                pos = [lastPos[0] + v[0], lastPos[1] + v[1], baseZ]
                # if i < self.goingTrain.wheels:
                #     print("pinionAtFront: {} wheel {} r: {} angle: {}".format( self.goingTrain.getArbour(i).pinionAtFront, i, r, angle), pos)
                # print("baseZ: ",baseZ, "drivingZ ", drivingZ)

                self.bearing_positions.append(pos)

        # print(self.bearingPositions)

        topZs = [self.arbourThicknesses[i] + self.bearing_positions[i][2] for i in range(len(self.bearing_positions))]

        bottomZs = [self.bearing_positions[i][2] for i in range(len(self.bearing_positions))]

        bottomZ = min(bottomZs)
        if bottomZ < 0:
            # positions are relative (chain at front), so readjust everything
            topZs = [z - bottomZ for z in topZs]
            # bottomZs = [z - bottomZ for z in bottomZs]
            for i in range(len(self.bearing_positions)):
                self.bearing_positions[i][2] -= bottomZ

        '''
        something is always pressed up against both the front and back plate. If it's a powered wheel that's designed for that (the chain/rope wheel is designed to use a washer,
        and the key-wound cord wheel is specially shaped) then that's not a problem.

        However if it's just a pinion (or a wheel - somehow?), or and anchor (although this should be avoided now by choosing where it goes) then that's extra friction

        TODO - I assumed that the chainwheel was alays the frontmost or backmost, but that isn't necessarily true.
        '''
        needExtraFront = False
        needExtraBack = False

        preliminaryPlateDistance = max(topZs)
        for i in range(len(self.bearing_positions)):
            # check front plate
            canIgnoreFront = False
            canIgnoreBack = False
            if self.going_train.get_arbour_with_conventional_naming(i).get_type() == ArborType.POWERED_WHEEL:
                if self.going_train.chain_at_back:
                    canIgnoreBack = True
                else:
                    # this is the part of the chain wheel with a washer, can ignore
                    canIgnoreFront = True
            # topZ = self.goingTrain.getArbourWithConventionalNaming(i).getTotalThickness() + self.bearingPositions[i][2]
            if topZs[i] >= preliminaryPlateDistance - LAYER_THICK * 2 and not canIgnoreFront:
                # something that matters is pressed up against the top plate
                # could optimise to only add the minimum needed, but this feels like a really rare edgecase and will only gain at most 0.4mm
                needExtraFront = True

            if self.bearing_positions[i][2] == 0 and not canIgnoreBack:
                needExtraBack = True

        extraFront = 0
        extraBack = 0
        if needExtraFront:
            extraFront = LAYER_THICK * 2
        if needExtraBack:
            extraBack = LAYER_THICK * 2

        for i in range(len(self.bearing_positions)):
            self.bearing_positions[i][2] += extraBack

        # print(self.bearingPositions)
        self.plate_distance = max(topZs) + self.endshake + extraFront + extraBack

    def bottom_of_hour_hand_z(self):
        '''
        relative to the front of the front plate
        '''
        return self.motion_works.get_hand_holder_height() + TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - self.motion_works.inset_at_base

    def front_of_motion_works_wheels_z(self):
        '''
        relative to the front of the front plate
        the closest something like a vanity plate could be to the front of the clock without causing problems for the motion works
        '''
        return TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - self.motion_works.inset_at_base + self.motion_works.get_wheels_thick()

    def front_plate_has_flat_front(self):
        '''
        If there's nothing sticking out of the front plate it can be printed the other way up - better front surface and no hole-in-hole needed for bearings
        '''
        if self.pendulum_at_front and self.pendulum_sticks_out > 0:
            #arm that holds the bearing (old designs)
            return False
        if self.style in [PlateStyle.RAISED_EDGING]:
            return False

        if self.huygens_maintaining_power:
            #ratchet is on the front
            return False
        return True

    def front_plate_printed_front_face_down(self):
        if self.front_plate_has_flat_front():
            return True
        else:
            #sort of true, the bulk of the front plate is printed face down
            return self.split_detailed_plate

    def get_seconds_hand_position(self):
        if self.centred_second_hand:
            return self.hands_position.copy()

        if self.going_train.has_seconds_hand_on_escape_wheel():
            return self.bearing_positions[-2][:2]

        if self.going_train.has_second_hand_on_last_wheel():
            #wheel before the escape wheel
            return self.bearing_positions[-3][:2]
        return None

    def has_seconds_hand(self):
        return self.second_hand and (self.going_train.has_seconds_hand_on_escape_wheel() or self.going_train.has_second_hand_on_last_wheel())

    def need_front_anchor_bearing_holder(self):
        #no longer supporting anything that doesn't (with the escapement on the front) - the large bearings have way too much friction so we have to hold the anchor arbour from both ends
        return self.escapement_on_front# and self.pendulumFixing == PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS

    def get_front_anchor_bearing_holder_total_length(self, bearing_holder_thick=-1):
        '''
        full length (including bit that holds bearing) of the peice that sticks out the front of the clock to hold the bearing for a front mounted escapment
        '''
        if bearing_holder_thick < 0:
            bearing_holder_thick = self.get_lone_anchor_bearing_holder_thick(self.arbors_for_plate[-1].bearing)

        if self.need_front_anchor_bearing_holder():
            holder_long = self.arbors_for_plate[-1].front_anchor_from_plate + self.arbors_for_plate[-1].arbor.escapement.get_anchor_thick() \
                          + bearing_holder_thick + SMALL_WASHER_THICK_M3
        else:
            holder_long = 0
        return holder_long


    @staticmethod
    def get_lone_anchor_bearing_holder_thick(bearing = None):
        '''
        static so it can be used to adjust the thickness of the frame
        '''
        if bearing is None:
            bearing = get_bearing_info(3)
        return bearing.height + 1

    def get_front_anchor_bearing_holder(self, for_printing=True):

        holder_thick = self.get_lone_anchor_bearing_holder_thick(self.arbors_for_plate[-1].bearing)

        pillar_tall = self.get_front_anchor_bearing_holder_total_length() - holder_thick
        if self.top_pillars > 1:
            raise ValueError("front anchor bearing holder only supports one top pillar TODO")
        holder = cq.Workplane("XY").moveTo(-self.top_pillar_r, self.top_pillar_positions[0][1]).radiusArc((self.top_pillar_r, self.top_pillar_positions[0][1]), self.top_pillar_r)\
            .lineTo(self.top_pillar_r, self.bearing_positions[-1][1]).radiusArc((-self.top_pillar_r, self.bearing_positions[-1][1]), self.top_pillar_r).close().extrude(holder_thick)

        holder = holder.union(cq.Workplane("XY").moveTo(self.top_pillar_positions[0][0], self.top_pillar_positions[0][1]).circle(self.plate_width / 2 + 0.0001).extrude(pillar_tall + holder_thick))


        holder = holder.cut(self.get_bearing_punch(holder_thick, bearing=get_bearing_info(self.arbors_for_plate[-1].arbor.arbor_d)).translate((self.bearing_positions[-1][0], self.bearing_positions[-1][1])))
        #rotate into position to cut fixing holes
        holder = holder.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, pillar_tall + holder_thick))
        holder= holder.cut(self.get_fixing_screws_cutter().translate((0,0,-self.front_z)))

        if for_printing:
            #rotate back
            holder = holder.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, pillar_tall + holder_thick))
            holder = holder.translate(np_to_set(np.multiply(self.top_pillar_positions[0], -1)))
        else:
            holder = holder.translate((0,0, self.front_z))

        return holder



    def calc_need_motion_works_holder(self):
        '''
        If we've got a centred second hand then there's a chance that the motino works arbour lines up with another arbour, so there's no easy way to hold it in plnace
        in this case we have a separate peice that is given a long screw and itself screws onto the front of the front plate
        '''

        if self.gear_train_layout ==GearTrainLayout.VERTICAL and self.has_seconds_hand() and self.centred_second_hand:
            #potentially

            motion_works_arbour_y = self.motion_works_pos[1]

            for i,bearing_pos in enumerate(self.bearing_positions):
                #just x,y
                bearing_pos_y = bearing_pos[1]
                bearing = get_bearing_info(self.going_train.get_arbour_with_conventional_naming(i).arbor_d)
                screw = MachineScrew(3, countersunk=True)
                if abs(bearing_pos_y - motion_works_arbour_y) < bearing.outer_d/2 + screw.get_head_diameter()/2:
                    print("motion works holder would clash with bearing holder for arbour", i)
                    return True

        return False

    def get_cannon_pinion_friction_clip(self):
        '''
        holds two "brake pads" - experimental sprung peice that can add a small amount of friction to the cannon pinion so the minute hand
        doesn't have too much slack when the second hand is centred. Without it the minute hand is about 30s fast on the half past and 30s slow on the half to.
        '''
        centre_z = TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - self.motion_works.inset_at_base + self.endshake / 2 - self.motion_works.friction_ring_thick/2

        #thick here being height as printed
        clip_thick = self.motion_works.friction_ring_thick/2
        total_thick = centre_z + clip_thick/2

        clip_holder_r = self.plate_width/2

        clip = cq.Workplane("XY").circle(clip_holder_r).extrude(total_thick)



        cannon_pinion_relative_pos = np_to_set(np.subtract(self.hands_position, self.cannon_pinion_friction_clip_pos))
        from_holder_to_cannon_pinion = Line(self.cannon_pinion_friction_clip_pos, anotherPoint=self.hands_position)
        angle_to_cannon_pinion = from_holder_to_cannon_pinion.get_angle()

        arc = math.pi/4
        brake_angles = [angle_to_cannon_pinion+math.pi/2, angle_to_cannon_pinion - math.pi/2]
        angle_pairs = [[angle - arc/2, angle + arc/2, angle] for angle in brake_angles]
        brake_pads = cq.Workplane("XY")

        #needs to be thicker than arm
        brake_pad_thick = 3
        #not sure what to name this - this is how far "inside" the cannon pinion the brake pads want to be
        # brake_pad_offset = 1.5
        # #thick here being width of arm (strength of spring)
        # arm_thick = 1.5 #0.8 seemed a bit weedy
        brake_pad_offset = 1
        arm_thick = 2.4

        inner_r = self.motion_works.friction_ring_r# - brake_pad_offset
        outer_r = inner_r + brake_pad_thick

        for angles in angle_pairs:

            '''
            new plan:
            build brake pad in the post-bend position, then rotate it into the pre-bend position by rotating around the mid point of the arm
            
            then when printed and bent into position the brake pad should line up properly - ideally want it to just be clamping the 
            cannon pinion, not pushing it downwards
            '''

            start_inner = polar(angles[0], inner_r)
            start_outer = polar(angles[0], outer_r)
            end_inner = polar(angles[1], inner_r)
            end_outer = polar(angles[1], outer_r)

            outer_radius_arc = (self.motion_works.friction_ring_r + brake_pad_thick)
            #sagitta - the outside arc isn't the outside radius as the brake pads are built, only once bent into place
            l = distance_between_two_points(start_outer, end_outer)
            r = (self.motion_works.friction_ring_r + brake_pad_thick)
            sagitta_1 = r - math.sqrt(r**2 - 0.25*l**2)
            sagitta_2 = outer_r - math.sqrt(outer_r**2 - 0.25*l**2)

            #the arm is at an angle, so taking this isn't account doesn't make it perfectly line up with the tangent of the outside the brake pad anyway, but it looks
            #better than not doing it.
            arm_start = polar(angles[2], outer_r - arm_thick/2 - abs(sagitta_2 - sagitta_1))
            arm_finish = np_to_set(np.add(np.multiply(cannon_pinion_relative_pos, -1), polar(angles[2], clip_holder_r - arm_thick/2)))

            arm_centre = average_of_two_points(arm_start, arm_finish)

            brake_pad = (cq.Workplane("XY").moveTo(start_inner[0], start_inner[1]).radiusArc(end_inner, -self.motion_works.friction_ring_r).lineTo(end_outer[0], end_outer[1])
                     .radiusArc(start_outer, outer_radius_arc).close().extrude(clip_thick))

            half_arm_length = np.linalg.norm(np.subtract(arm_centre, arm_start))


            relative_angle = rationalise_angle(angles[2]) - rationalise_angle(angle_to_cannon_pinion)
            quad = get_quadrant(relative_angle)

            bend_angle = brake_pad_offset/half_arm_length

            # if quad[0] > 0:
            if relative_angle > 0:
                #which direction to rotate?
                bend_angle *= -1

            arm_start_bent = np_to_set(np.add(arm_start, polar(angles[2]+math.pi, brake_pad_offset)))

            brake_pad = brake_pad.rotate((arm_centre[0], arm_centre[1], 0), (arm_centre[0], arm_centre[1], 1), rad_to_deg(bend_angle))

            arm = get_stroke_line([arm_start_bent, arm_finish], wide=arm_thick, thick=clip_thick)
            brake_pad = brake_pad.union(arm)

            brake_pads = brake_pads.union(brake_pad.translate(cannon_pinion_relative_pos).translate((0,0,total_thick-clip_thick)))

        # arms = cq.Workplane("XY")
        # for x in [-1,1]:
        #     arms = arms.union(get_stroke_line([(x*(outer_r -arm_thick/2), ),]))


        clip = clip.union(brake_pads)

        #cutting out screws afterwards so they don't overlap with the arms
        for pos in self.cannon_pinion_friction_clip_fixings_pos:
            relative_pos = np_to_set(np.subtract(pos, self.cannon_pinion_friction_clip_pos))
            clip = clip.cut(self.motion_works_screws.get_cutter().rotate((0, 0, 0), (0, 1, 0), 180).translate((relative_pos[0], relative_pos[1], total_thick)))

        return clip

    def get_motion_works_holder(self):
        if not self.need_motion_works_holder:
            return None



        standoff_thick = 1
        holder_thick = TWO_HALF_M3S_AND_SPRING_WASHER_HEIGHT - WASHER_THICK_M3 - standoff_thick
        w = self.motion_works_holder_wide
        l = self.motion_works_holder_length
        #holder = cq.Workplane("XY").rect(self.motion_works_holder_wide, self.motion_works_holder_length).extrude(holder_thick)
        holder = cq.Workplane("XY").moveTo(w/2, l/2).radiusArc((-w/2,l/2), -w/2).line(0,-l).radiusArc((w/2, -l/2), -w/2).close().extrude(holder_thick)

        #small standoff for motion works arbour
        holder = holder.faces(">Z").workplane().circle(self.motion_works_screws.metric_thread).extrude(standoff_thick)

        holder = holder.cut(self.motion_works_screws.get_cutter(with_bridging=True, layer_thick=self.layer_thick, for_tap_die=True))

        for pos in self.motion_works_fixings_relative_pos:
            holder = holder.cut(self.motion_works_screws.get_cutter().rotate((0, 0, 0), (0, 1, 0), 180).translate((pos[0], pos[1], holder_thick)))

        return holder


    def get_plate_thick(self, back=True, standoff=False):
        if standoff:
            #TODO separate value
            return self.plate_thick
        if back:
            return self.back_plate_thick
        return self.plate_thick

    def get_plate_distance(self):
        '''
        how much space there is between the front and back plates
        '''
        return self.plate_distance

    def get_front_z(self):
        return self.get_plate_thick(True) + self.get_plate_thick(False) + self.plate_distance

    def get_screwhole_positions(self):
        '''
        returns [(x,y, supported),]
        for where the holes to fix the clock to the wall will be

        The older logic (when there is no wall standoff) is a bit of a mess, it was pulled out of the tangle in clock plates and could do with tidying up
        '''
        if self.back_plate_from_wall > 0:

            slotLength = 7

            # just above the pillar
            # TODO consider putting the screwhole INSIDE the pillar?
            topScrewHolePos = (self.bearing_positions[-1][0], self.top_pillar_positions[0][1] + self.top_pillar_r + self.wall_fixing_screw_head_d / 2 + slotLength)

            if self.bottom_pillars == 1:
                bottomScrewHolePos = (0, self.bottom_pillar_positions[0][1] + self.bottom_pillar_r + self.wall_fixing_screw_head_d / 2 + slotLength)
            else:
                bottomScrewHolePos = (0, self.bottom_pillar_positions[0][1])

            if self.heavy or True:
                return [topScrewHolePos, bottomScrewHolePos]
            else:
                return [topScrewHolePos]


        else:
            #old messy logic

            bottomScrewHoleY = self.bearing_positions[0][1] + (self.bearing_positions[1][1] - self.bearing_positions[0][1]) * 0.6

            extraSupport = True
            if self.using_pulley and self.heavy:
                # the back plate is wide enough to accomodate
                extraSupport = False

            weightX = 0
            weightOnSide = 1 if self.weight_on_right_side else -1
            if self.heavy and not self.using_pulley:
                # line up the hole with the big heavy weight
                weightX = weightOnSide * self.going_train.powered_wheel.diameter / 2

            if self.gear_train_layout == GearTrainLayout.ROUND:
                #screwHoleY = chainWheelR * 1.4
                #raise NotImplementedError("Haven't fixed this for round clocks")
                print("TODO: fix screwholes for round clocks properly")
                return [(weightX, self.compact_radius, True)]

            elif self.gear_train_layout == GearTrainLayout.VERTICAL:
                if self.extra_heavy:

                    # below anchor
                    topScrewHoleY = self.bearing_positions[-2][1] + (self.bearing_positions[-1][1] - self.bearing_positions[-2][1]) * 0.6
                    return [(weightX, bottomScrewHoleY, extraSupport), (weightX, topScrewHoleY, True)]
                else:
                    # just below anchor
                    screwHoleY = self.bearing_positions[-2][1] + (self.bearing_positions[-1][1] - self.bearing_positions[-2][1]) * 0.6

                    return [(weightX, screwHoleY, extraSupport)]

    def get_drill_template(self, drillHoleD=7, layer_thick=LAYER_THICK_EXTRATHICK):

        screwHoles = self.get_screwhole_positions()

        if len(screwHoles) <= 1:
            raise ValueError("Can't make template without at least two screwholes")
        #assumes aligned vertically
        ys = [hole[1] for hole in screwHoles]
        xs = [hole[0] for hole in screwHoles]
        maxY = max(ys)
        minY = min(ys)
        minX = min(xs)
        maxX = max(xs)

        minWidth = maxX - minX
        minHeight = maxY - minY

        print("screw hole distance", minHeight)

        border = drillHoleD*2
        thick = 2

        width = minWidth + border*2

        template = cq.Workplane("XY").moveTo(minX + minWidth/2, minY + minHeight/2).rect(width, minHeight + border*2).extrude(thick)

        for hole in screwHoles:
            template = template.faces(">Z").workplane().moveTo(hole[0], hole[1]).circle(drillHoleD/2).cutThruAll()
        # text = cq.Workplane("XY").text(txt=self.name, fontsize=int(minWidth*0.5), distance=LAYER_THICK, cut=False, halign='center', valign='center', kind="bold").rotate((0,0,0), (0,0,1),90).translate((0,0,thick))
        text = cq.Workplane("XY").text(self.name, fontsize=width*0.5, distance=layer_thick, cut=False, halign='center', valign='center', kind="bold").rotate((0, 0, 0), (0, 0, 1), 90).translate(((minX + maxX)/2, (minY + maxY)/2, thick))
        template = template.add(text)

        return template

    def cut_anchor_bearing_in_standoff(self, standoff):
        bearingInfo = self.arbors_for_plate[-1].bearing


        # standoff = standoff.cut(self.getBearingPunchDeprecated(bearingOnTop=True, standoff=True, bearingInfo=bearingInfo).translate((self.bearing_positions[-1][0], self.bearing_positions[-1][1], 0)))
        support = self.standoff_pillars_separate
        standoff = standoff.cut(self.get_bearing_punch(plate_thick=self.get_plate_thick(standoff=True), bearing=bearingInfo, bearing_on_top=True, with_support=support)
                                .translate((self.bearing_positions[-1][0], self.bearing_positions[-1][1], 0)))

        return standoff

    def get_wall_standoff(self, top=True, for_printing=True):
        '''
        I suppose the top wall standoff is technically the back cock

        If the back plate isn't directly up against the wall, we need two more peices that attach to the top and bottom pillars on the back
        if the pendulum is at the back (likely given there's not much other reason to not be against the wall) the bottom peice will need
        a large gap or the hand-avoider

        this is in position with the xy plate at the TOP of the standoff

        I had considered linking the top and bottom standoffs together with another plate for strength, but an eight day clock (clock 12) has demonstrated that they're
        fine as two independant little pillars

        In the case of a suspension spring the top pillar standoff is only the bit that holds the bearing for the anchor arbor. There is (will be) a separate
        peice behind that to hold the suspension spring. This is because it's the same piece as the older standoff, just with a different length.
        SECOND THOUGHTS - could I just have a big round hole in the back plate and have the crutch extend through that?

        '''

        pillarPositions = self.top_pillar_positions if top else self.bottom_pillar_positions
        pillarR = self.top_pillar_r if top else self.bottom_pillar_r

        pillarWallThick = 2
        pillarInnerR = pillarR-pillarWallThick

        standoff = cq.Workplane("XY").tag("base")

        back_thick = self.get_plate_thick(standoff=True)
        screwhole_back_thick = back_thick - 2
        if top:
            #assuming 1 pillar fow now


            standoff = standoff.add(self.get_pillar(top=top, flat=True).extrude(self.back_plate_from_wall).translate(pillarPositions[0]))
        else:
            if self.bottom_pillars > 1:
                # make back thinner, not needed for strength so much as stability
                back_thick = 5
                screwhole_back_thick = back_thick
                for pillarPos in pillarPositions:
                    standoff = standoff.union(self.get_pillar(top=top, flat=True).extrude(self.back_plate_from_wall).translate(pillarPos))
                standoff = standoff.union(get_stroke_line(pillarPositions, wide=pillarR, thick=back_thick, style=StrokeStyle.SQUARE))


            else:
                #round works fine, no need to copy the heavy duty lower pillar
                standoff = standoff.moveTo(pillarPositions[0][0], pillarPositions[0][1]).circle(pillarR).extrude(self.back_plate_from_wall)


        if top or self.heavy or True:

            #screwholes to hang on wall
            #originally only at the top, but now I think put them everywhere
            # #TODO consider putting the screwhole INSIDE the pillar?

            if top:
                screwHolePos = self.get_screwhole_positions()[0]
            else:
                #bottom pillar, heavy
                screwHolePos = self.get_screwhole_positions()[1]

            screwHoleSupportR = self.top_pillar_r  # (self.wallFixingScrewHeadD + 6)/2

            addExtraSupport = False

            #extend a back plate out to the screwhole
            if len(pillarPositions) == 1:
                screwhole_support_start = pillarPositions[0]
                standoff = standoff.union(get_stroke_line([screwhole_support_start, screwHolePos], wide=self.plate_width, thick=back_thick))
            else:
                #we have two pillars and the screwhole is in the link between them
                addExtraSupport = True

            #can't decide if to add backThick or not - it recesses the screw which looks nice in some situations but not convinced for teh standoff
            standoff = self.cut_wall_fixing_hole(standoff, screwHolePos, screw_head_d=self.wall_fixing_screw_head_d, add_extra_support=addExtraSupport, plate_thick=back_thick)#, backThick=screwhole_back_thick)

            if self.pendulum_fixing in [PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS, PendulumFixing.SUSPENSION_SPRING] and top:
                # extend a back plate out to the bearing holder and wall fixing
                #note assumes one top pillar, might not work with two
                bearingHolder = cq.Workplane("XY").tag("base").moveTo((screwHolePos[0] + self.bearing_positions[-1][0]) / 2, (self.bearing_positions[-1][1] + self.top_pillar_positions[0][1]) / 2). \
                    rect(self.top_pillar_r * 2, self.top_pillar_positions[0][1] - self.bearing_positions[-1][1]).extrude(self.rear_standoff_bearing_holder_thick)
                bearingHolder = bearingHolder.workplaneFromTagged("base").moveTo(self.bearing_positions[-1][0], self.bearing_positions[-1][1]).circle(screwHoleSupportR).extrude(self.rear_standoff_bearing_holder_thick)
                bearingHolder = self.cut_anchor_bearing_in_standoff(bearingHolder)

                z = 0
                if self.pendulum_fixing == PendulumFixing.SUSPENSION_SPRING:
                    #TODO
                    z = self.back_plate_from_wall - self.crutch_space - self.rear_standoff_bearing_holder_thick - self.endshake
                standoff = standoff.union(bearingHolder.translate((0,0,z)))

        #we're currently not in the right z position
        standoff = standoff.cut(self.get_fixing_screws_cutter().translate((0,0,self.back_plate_from_wall)))

        if for_printing:
            if not top:
                standoff = standoff.rotate((0,0,0), (1,0,0), 180)
            standoff = standoff.translate((-pillarPositions[0][0], -pillarPositions[0][1]))
        else:
            standoff = standoff.translate((0,0,-self.back_plate_from_wall))

        return standoff

    def get_text(self, top_standoff=False, for_printing=False):

        all_text = cq.Workplane("XY")

        # (x,y,width,height, horizontal)
        spaces = self.get_text_spaces()

        max_text_size = min([textSpace.get_text_max_size() for textSpace in spaces])

        for space in spaces:
            space.set_size(max_text_size)
        any_text = False
        for space in spaces:
            if self.text_on_standoffs:
                if top_standoff and space.y < self.hands_position[1]:
                    continue
                if not top_standoff and space.y > self.hands_position[1]:
                    continue

            all_text = all_text.add(space.get_text_shape())
            any_text = True

        if not any_text:
            #would fail to cut shapes below and everything assumes text exists
            raise ValueError("No text available, something has gone wrong")

        if self.text_on_standoffs:
            all_text = all_text.cut(self.get_fixing_screws_cutter().translate((0,0,self.back_plate_from_wall)))
            all_text = all_text.translate((0, 0, -self.back_plate_from_wall))
        else:
            all_text = self.punch_bearing_holes(all_text, back=True, make_plate_bigger=False)

        # if for_printing and self.standoff_pillars_separate:
        #     all_text = all_text.translate((0, 0, self.back_plate_from_wall))
        #     all_text = all_text.rotate((0,0,0),(1,0,0),180).translate((0,0, spaces[0].thick + self.get_plate_thick(standoff=True)))

        return all_text

    def get_text_spaces(self):
        '''
        get a list of TextSpace objects with text assigned, assuming no plaque is being used
        '''

        texts = self.texts

        #(x,y,width,height, horizontal)
        spaces = []



        if self.bottom_pillars > 1:
            #along the bottom of the plate between the two pillars

            pillar_wide_half = self.bottom_pillar_width / 2 if self.narrow_bottom_pillar else self.bottom_pillar_r
            bearing_wide_half = self.arbors_for_plate[0].bearing.outer_d / 2

            for pillarPos in self.bottom_pillar_positions:

                if pillarPos[0] > 0:
                    offset = bearing_wide_half - pillar_wide_half
                else:
                    offset = -(bearing_wide_half - pillar_wide_half)

                spaces.append(TextSpace(pillarPos[0] / 2 + offset, pillarPos[1] + self.bottom_pillar_height/4, abs(pillarPos[0]) - pillar_wide_half - bearing_wide_half, self.bottom_pillar_height, horizontal=True))
                spaces.append(TextSpace(pillarPos[0] / 2 + offset, pillarPos[1] - self.bottom_pillar_height/4, abs(pillarPos[0]) - pillar_wide_half - bearing_wide_half, self.bottom_pillar_height, horizontal=True))

        else:
            '''
            vertical long the plate between bearings
            '''
            #between bottom pillar and lowest bearing
            bottom_pos = (self.bottom_pillar_positions[0][0], self.bottom_pillar_positions[0][1] + self.bottom_pillar_r)
            chain_pos = self.bearing_positions[0][:2]
            first_arbour_pos = self.bearing_positions[1][:2]

            chain_space = self.arbors_for_plate[0].bearing.outer_d / 2
            arbour_space = self.arbors_for_plate[1].bearing.outer_d / 2

            if self.heavy:
                text_height = self.bottom_pillar_r * 2 * 0.3
                #three along the wide bit at the bottom and one above
                spaces.append(TextSpace(bottom_pos[0] - self.bottom_pillar_r + self.bottom_pillar_r / 3, (bottom_pos[1] + chain_pos[1]) / 2, text_height, chain_pos[1] - bottom_pos[1], horizontal=False))
                spaces.append(TextSpace(bottom_pos[0], (bottom_pos[1] + (chain_pos[1]-chain_space)) / 2, text_height, chain_pos[1] - chain_space - bottom_pos[1], horizontal=False))
                spaces.append(TextSpace(bottom_pos[0] + self.bottom_pillar_r - self.bottom_pillar_r / 3, (bottom_pos[1] + chain_pos[1]) / 2, text_height, chain_pos[1] - bottom_pos[1], horizontal=False))

                spaces.append(TextSpace(chain_pos[0], (first_arbour_pos[1]-arbour_space + chain_pos[1] + chain_space) / 2, self.plate_width * 0.9, first_arbour_pos[1] - arbour_space - (chain_pos[1] + chain_space), horizontal=False))
            else:
                #two and two
                spaces.append(TextSpace(bottom_pos[0] - self.plate_width / 4, (bottom_pos[1] + chain_pos[1]) / 2, self.plate_width / 2, chain_pos[1] - bottom_pos[1], horizontal=False))
                spaces.append(TextSpace(bottom_pos[0] + self.plate_width / 4, (bottom_pos[1] + chain_pos[1]) / 2, self.plate_width / 2, chain_pos[1] - bottom_pos[1], horizontal=False))

                spaces.append(TextSpace(chain_pos[0] - self.plate_width / 4, (first_arbour_pos[1] + chain_pos[1]) / 2, self.plate_width / 2, first_arbour_pos[1] - chain_pos[1], horizontal=False))
                spaces.append(TextSpace(chain_pos[0] + self.plate_width / 4, (first_arbour_pos[1] + chain_pos[1]) / 2, self.plate_width / 2, first_arbour_pos[1] - chain_pos[1], horizontal=False))


        for i,text in enumerate(texts):
            spaces[i].set_text(text)

        return spaces

    def calc_plaque_config(self):
        '''
        if this clock has a little plaque, calculate where it goes and what size it should be
        side effect: sets width and height on teh plaque itself (lazy but simple)

        will be similar to get_text_spaces, not sure how to abstract anything out to share code yet

        '''

        raise NotImplementedError("TODO implement plaque for this clock plate")

    def get_plate_detail(self, back=True, for_printing=False, for_this_shape=None):
        '''
        For styles of clock plate which might have ornate detailing. Similar to dial detail or text, this is a separate 3d shape
        designed to be sliced as a multicolour object
        '''

        #undecided - might be easier to just not put this on the back plate? it's going to be hard to see and makes it harder to print and work out how to do standoffs
        if self.style == PlateStyle.RAISED_EDGING and not back:
            if for_this_shape is not None:
                plate = for_this_shape
            else:
                #not for printing so we know it's got its back on the plane with bearing holes facing up
                plate = self.get_plate(back = back, for_printing=False, just_basic_shape=True, thick_override=self.edging_wide*10)

            shell = plate.shell(-self.edging_wide)
            # return shell
            # return cq.Workplane("XY").rect(50000, 50000).extrude(self.edging_thick)
            edging = shell.translate((0,0,-self.edging_wide)).intersect(cq.Workplane("XY").rect(500, 500).extrude(self.edging_thick))

            if self.moon_complication is not None:
                #not for printing we actually want this in the position it will be when assembled
                edging = edging.cut(self.moon_holder.get_moon_holder_parts(for_printing=False)[0])

            # this is on the xy plane sticking up +ve z, will need translating to be useful

            if for_printing and not back:
                edging = edging.translate((0,0,self.get_plate_thick(back=False)))

            return edging
            # return edging.translate((0,0,self.get_plate_thick(back=back)))

        return None
    def get_plate(self, back=True, for_printing=True, just_basic_shape=False, thick_override=-1):
        '''
        Two plates that are almost idential, with pillars at the very top and bottom to hold them together.
        Designed to be flat up against the wall, with everything offset to avoid the wall and picture rail

        styles: round or vertical
        round minimises total height by placing the gear train in a circle, so more complicated clocks can still fit on the print bed
        vertical just has everything directly above each other.

        The screwhole is placed directly above the weight to make the clock easier to hang straight

        '''
        top_pillar_positions, top_pillar_r, plate_width = (self.top_pillar_positions, self.top_pillar_r, self.plate_width)

        if self.top_pillars > 1:
            raise ValueError("simple clock plates don't yet support multiple top pillars")

        thick = self.get_plate_thick(back)
        if thick_override > 0:
            thick = thick_override

        #the bulk material that holds the bearings
        plate = cq.Workplane("XY").tag("base")
        if self.gear_train_layout==GearTrainLayout.ROUND:
            radius = self.compact_radius + plate_width / 2
            #the ring that holds the gears
            plate = plate.moveTo(self.bearing_positions[0][0], self.bearing_positions[0][1] + self.compact_radius).circle(radius).circle(radius - plate_width).extrude(thick)
        elif self.gear_train_layout in [GearTrainLayout.VERTICAL, GearTrainLayout.COMPACT]:
            #rectangle that just spans from the top bearing to the bottom pillar (so we can vary the width of the bottom section later)
            plate = plate.moveTo((self.bearing_positions[0][0] + self.bearing_positions[-1][0]) / 2, (self.bearing_positions[0][1] + self.bearing_positions[-1][1]) / 2).rect(plate_width, abs(self.bearing_positions[-1][1] - self.bearing_positions[0][1])).extrude(self.get_plate_thick(back))

        if self.gear_train_layout == GearTrainLayout.COMPACT:
            '''
            need some extra bits to hold the bearings that are off to one side
            '''
            #second wheel will be off to one side
            # side_shoots = 1 if self.goingTrain.wheels < 4 else 2
            # for i in range(side_shoots):
            #
            #     points = [self.bearingPositions[self.goingTrain.chainWheels+i*2],self.bearingPositions[self.goingTrain.chainWheels+1+i*2], self.bearingPositions[self.goingTrain.chainWheels+2+i*2]]
            #     points = [(x,y) for x,y,z in points]
            #     plate = plate.union(get_stroke_line(points,self.minPlateWidth, self.getPlateThick(back=back)))
            points = []



            sticky_out_bearing_indexes = []
            if self.going_train.wheels == 4:
                sticky_out_bearing_indexes = [self.going_train.powered_wheels + 1, self.going_train.powered_wheels + 3]
            else:
                sticky_out_bearing_indexes = [self.going_train.powered_wheels + 1]

            if self.going_train.powered_wheels == 2:
                sticky_out_bearing_indexes += [1]

            for bearing_index in sticky_out_bearing_indexes:
                sticky_out_ness = abs(self.bearing_positions[self.going_train.powered_wheels][0] - self.bearing_positions[bearing_index][0])
                if sticky_out_ness > 30:
                    #a-frame arms
                    #reducing to thin arms and chunky circle around bearings
                    points = [ #bearing_pos[:2]for bearing_pos in self.bearing_positions[bearing_index - 1:bearing_index + 1 + 1 ]]
                        self.bearing_positions[bearing_index - 1][:2],
                        self.bearing_positions[bearing_index][:2],
                        self.bearing_positions[bearing_index + 1][:2]
                    ]
                    plate = plate.union(cq.Workplane("XY").circle(self.min_plate_width / 2).extrude(thick).translate(self.bearing_positions[bearing_index][:2]))
                    # points = [(x, y) for x, y, z in points]
                    plate = plate.union(get_stroke_line(points, self.min_plate_width / 2, thick))

                else:
                    #just stick a tiny arm out the side for each bearing
                    bearing_pos = self.bearing_positions[bearing_index]
                    points = [(0, bearing_pos[1]), (bearing_pos[0], bearing_pos[1])]
                    plate = plate.union(get_stroke_line(points, self.min_plate_width, thick))




        plate = plate.tag("top")

        bottom_pillar_joins_plate_pos = self.bearing_positions[0][:2]

        screwHolePositions = self.get_screwhole_positions()

        bottomScrewHoleY = min([hole[1] for hole in screwHolePositions])

        if self.heavy and self.using_pulley and back and self.back_plate_from_wall == 0:
            #instead of an extra circle around the screwhole, make the plate wider extend all the way up
            #because the screwhole will be central when heavy and using a pulley
            #don't do this if we're offset from the wall
            bottom_pillar_joins_plate_pos = (0, bottomScrewHoleY)

        #supports all the combinations of round/vertical and chainwheels or not
        bottom_pillar_link_has_rounded_top = self.gear_train_layout in [GearTrainLayout.VERTICAL, GearTrainLayout.COMPACT]
        #narrow = self.goingTrain.chainWheels == 0
        bottomBitWide = plate_width# if narrow else self.bottomPillarR*2

        if self.going_train.powered_wheels > 0:
            bottomBitWide = self.bottom_pillar_r * 2

        #link the bottom pillar to the rest of the plate
        if self.narrow_bottom_pillar and self.bottom_pillars == 2:
            #rectangle between the two and round off teh ends
            # plate = plate.union(cq.Workplane("XY").rect(abs(self.bottomPillarPositions[0][0] - self.bottomPillarPositions[1][0])), self.bottom_pillar_height)
            plate = plate.union(get_stroke_line(self.bottom_pillar_positions, wide=self.bottom_pillar_height, thick = thick, style=StrokeStyle.SQUARE))
            for bottomPillarPos in self.bottom_pillar_positions:
                plate = plate.union(get_stroke_line([(bottomPillarPos[0], bottomPillarPos[1] + self.bottom_pillar_height/2-self.bottom_pillar_width/2), (bottomPillarPos[0], bottomPillarPos[1] - self.bottom_pillar_height/2+self.bottom_pillar_width/2)], thick = thick, wide=self.bottom_pillar_width))
        else:
            for bottomPillarPos in self.bottom_pillar_positions:
                plate = plate.union(get_stroke_line([bottomPillarPos, bottom_pillar_joins_plate_pos], wide=bottomBitWide, thick = thick))
                plate = plate.union(cq.Workplane("XY").moveTo(bottomPillarPos[0], bottomPillarPos[1]).circle(self.bottom_pillar_r - 0.00001).extrude(thick))




        if self.gear_train_layout == GearTrainLayout.ROUND:
            #centre of the top of the ring
            topOfPlate = (self.bearing_positions[0][0], self.bearing_positions[0][1] + self.compact_radius * 2)
        else:
            #topmost bearing
            topOfPlate = self.bearing_positions[-1]

        # link the top pillar to the rest of the plate
        plate = plate.workplaneFromTagged("base").moveTo(topOfPlate[0] - top_pillar_r, topOfPlate[1]) \
            .lineTo(top_pillar_positions[0][0] - top_pillar_r, top_pillar_positions[0][1]).radiusArc((top_pillar_positions[0][0] + top_pillar_r, top_pillar_positions[0][1]), top_pillar_r) \
            .lineTo(topOfPlate[0] + top_pillar_r, topOfPlate[1]).close().extrude(thick)

        #not sure this will print well
        # if not back and self.front_plate_has_flat_front():
        #     plate = plate.edges(">Z").fillet(1)

        plate = plate.tag("top")
        # #for the screwhole
        # screwHeadD = 9
        # screwBodyD = 6
        # slotLength = 7

        if back:
            #the hole for holding the clock to the wall - can inset the head of the screw if the plate is thick enough
            screwHolebackThick = max(thick - 5, 4)


            if self.back_plate_from_wall == 0:
                for screwPos in screwHolePositions:
                    plate = self.cut_wall_fixing_hole(plate, (screwPos[0], screwPos[1]), back_thick=screwHolebackThick, screw_head_d=self.wall_fixing_screw_head_d, add_extra_support=screwPos[2])

            #the pillars
            if not self.pillars_separate:
                for bottomPillarPos in self.bottom_pillar_positions:
                    plate = plate.union(self.get_bottom_pillar().translate(bottomPillarPos).translate((0, 0, thick)))
                plate = plate.union(self.get_top_pillar().translate(self.top_pillar_positions[0]).translate((0, 0, thick)))

            plate = plate.cut(self.get_text())








        if not back:
            #front
            plate = self.front_additions_to_plate(plate, plate_thick=thick, moon=True)


        if just_basic_shape:
            return plate

        plate = self.punch_bearing_holes(plate, back)

        #screws to fix the plates together, with embedded nuts in the pillars
        if back:
            plate = plate.cut(self.get_fixing_screws_cutter())
        else:
            plate = plate.cut(self.get_fixing_screws_cutter().translate((0, 0, -self.get_plate_thick(back=True) - self.plate_distance)))

        plate = self.apply_style_to_plate(plate, back=back)

        if for_printing and not back and self.front_plate_printed_front_face_down():
            '''
            front plate is generated front-up, but we can flip it for printing
            '''
            plate = plate.rotate((0,0,0), (0,1,0),180).translate((0,0,thick))




        return plate

    def apply_style_to_plate(self, plate, back=True, addition_allowed=False):
        #assuming here that plates are in the default orentation, with back plate back down and front plate front up

        if self.style == PlateStyle.RAISED_EDGING:
            if not addition_allowed:
                return plate
            detail = self.get_plate_detail(back=back)
            if detail is None:
                return plate
            z = - self.edging_thick
            if not back:
                z = self.get_plate_thick(back=False)
            try:
                combined = plate.union(detail.translate((0,0,z)))
            except:
                combined = plate.union(detail.translate((0, 0, z)), clean=False)

            return combined

        return plate

    def get_fixing_screw_length_info(self):
        bottom_total_length = self.back_plate_from_wall + self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False)
        tal_length = self.back_plate_from_wall + self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False)
        top_total_length = bottom_total_length + self.get_front_anchor_bearing_holder_total_length()

        if not self.screws_from_back[0][0] and self.back_plate_from_wall > 0:
            # space to embed the nut in the standoff
            top_screw_length = top_total_length - (top_total_length % 10)
        else:
            # nut will stick out the front or back
            top_screw_length = top_total_length + self.fixing_screws.get_nut_height() - (top_total_length + self.fixing_screws.get_nut_height()) % 10

        if not self.screws_from_back[1][0] and self.back_plate_from_wall > 0:
            # space to embed the nut in the standoff
            bottom_screw_length = bottom_total_length - (bottom_total_length % 10)
        else:
            # nut will stick out the front or back
            bottom_screw_length = bottom_total_length + self.fixing_screws.get_nut_height() - (bottom_total_length + self.fixing_screws.get_nut_height()) % 10

        # top and bottom screws are different lengths if there is a front-mounted escapement

        # TODO - could easily have a larger hole in the standoff so the screw or nut starts deeper and thus need shorter screws

        # hacky logic that shouldn't live here
        if top_screw_length > 100 and self.fixing_screws.metric_thread <= 4:
            print("top screw length exceeds 100mm, limiting to 100mm, check design to make sure it fits")
            top_screw_length = 100

        # TODO add option to use threaded rod with nuts on both sides. I've bodged this for tony by printing half with screws from back, and the rest with screws from front
        print(
            "Total length of front to back of clock is {}mm at top and {}mm at bottom. Assuming top screw length of {}mm and bottom screw length of {}mm".format(top_total_length, bottom_total_length, top_screw_length, bottom_screw_length))
        if top_screw_length > 60 and self.fixing_screws.metric_thread < 4:
            print("WARNING may not be able to source screws long enough, try M4")

        return (bottom_total_length, top_total_length, bottom_screw_length, top_screw_length)

    def get_fixing_screw_nut_info(self):
        bottom_total_length, top_total_length, bottom_screw_length, top_screw_length = self.get_fixing_screw_length_info()

        top_nut_base_z = -self.back_plate_from_wall
        bottom_nut_base_z = -self.back_plate_from_wall
        top_nut_hole_height = bottom_nut_hole_height = self.fixing_screws.get_nut_height() + 1

        if self.back_plate_from_wall > 0 and not self.embed_nuts_in_plate:
            # depth of the hole in the wall standoff before the screw head or nut, so specific sizes of screws can be used
            # extra nut height just in case
            top_nut_hole_height = (top_total_length - top_screw_length) + self.fixing_screws.get_nut_height() + 5
            bottom_nut_hole_height = (bottom_total_length - bottom_screw_length) + self.fixing_screws.get_nut_height() + 5

        return (bottom_nut_base_z, top_nut_base_z, bottom_nut_hole_height, top_nut_hole_height)

    def get_spring_ratchet_screws_cutter(self, back_plate=True):
        plate_thick = self.get_plate_thick(back=back_plate)
        if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL and self.going_train.powered_wheel.ratchet_at_back == back_plate:
            #spring powered, need the ratchet!
            screw = self.going_train.powered_wheel.ratchet.fixing_screws

            cutter = cq.Workplane("XY")

            positions = self.going_train.powered_wheel.ratchet.get_screw_positions()
            if self.little_plate_for_pawl:
                positions += self.going_train.powered_wheel.ratchet.get_little_plate_for_pawl_screw_positions()
            for relative_pos in positions:
                extra_z = 0
                if relative_pos == self.going_train.powered_wheel.ratchet.get_pawl_screw_position():
                    extra_z = -self.beefed_up_pawl_thickness
                pos = np_to_set(np.add(self.bearing_positions[0][:2], relative_pos))
                pos = (pos[0], pos[1], extra_z)
                #undecided if they need to be for tap die, they mgiht be enough without now there's a little plate for the pawl
                cutter = cutter.add(screw.get_cutter(with_bridging=True).translate(pos)) # for_tap_die=True,

            if back_plate:
                cutter = cutter.rotate((0,0,0),(0,1,0),180).translate((0,0,plate_thick))

            return cutter
        return None

    def get_fixing_screws_cutter(self):
        '''
        in position, assuming back of back plate is resting on the XY plane

        Previously used two sets of screws: one to attach the front plate and one to attach the rear standoffs, both with embedded nuts.
        Now assumes you've got screws long enough to attach everything. This should make it stronger
        especially as the pillars are now separate and the new suspension spring will result in two bits of standoff

        bit messy since adding the option for screws_from_back to be different for each pillar (needed to make the moon clock assembleable and look neat)
        '''



        if self.fixing_screws_cutter is not None:
            #fetch from cache if possible
            return self.fixing_screws_cutter

        # bottom_total_length, top_total_length, bottom_screw_length, top_screw_length = self.get_fixing_screw_length_info()


        bottom_nut_base_z, top_nut_base_z, bottom_nut_hole_height, top_nut_hole_height = self.get_fixing_screw_nut_info()

        cutter = cq.Workplane("XY")
        # elif self.embed_nuts_in_plate:
        #     # unlikely I'll be printing any wall clocks without this standoff until I get to striking longcase-style clocks and then I can just use rod and nuts anyway
        #     print("you may have to cut the fixing screws to length in the case of no back standoff")
        #     if self.screws_from_back[0][0]:
        #         top_nut_base_z = self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False) - self.fixing_screws.getNutHeight()
        #     if self.screws_from_back[1][0]:
        #         bottom_nut_base_z = self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False) - self.fixing_screws.getNutHeight()


        for pillar in [0, 1]:



            if pillar == 0:
                plate_fixings = self.plate_top_fixings
                nut_base_z = top_nut_base_z
            else:
                plate_fixings = self.plate_bottom_fixings
                nut_base_z = bottom_nut_base_z

            for i,fixingPos in enumerate(plate_fixings):
                this_screw_from_back = self.screws_from_back[pillar][i]

                if self.embed_nuts_in_plate:
                    # this was previously a mechanism to always put the nuts in the literal back plate. now it's a command to ignore lengths of bolts
                    # and put the nuts in the back of the rear plate or wallstandoff (or front if screws from back)
                    if this_screw_from_back:
                        nut_base_z = self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False) - self.fixing_screws.get_nut_height()

                nut_bridging = True

                if self.back_plate_from_wall > 0 and self.standoff_pillars_separate:
                    nut_bridging = False

                z = self.front_z
                if self.embed_nuts_in_plate or (self.back_plate_from_wall > 0 and not this_screw_from_back):
                    #make a hole for the nut
                    if fixingPos in self.plate_top_fixings and self.need_front_anchor_bearing_holder():
                        z += self.get_front_anchor_bearing_holder_total_length()
                        cutter = cutter.union(self.fixing_screws.get_nut_cutter(height=top_nut_hole_height, with_bridging=nut_bridging, layer_thick=self.layer_thick, rod_loose=True)
                                              .translate(fixingPos).translate((0, 0, nut_base_z)))
                    else:
                        cutter = cutter.union(self.fixing_screws.get_nut_cutter(height=bottom_nut_hole_height, with_bridging=nut_bridging, layer_thick=self.layer_thick, rod_loose=True)
                                              .translate(fixingPos).translate((0, 0, nut_base_z)))
                # holes for the screws
                if this_screw_from_back:
                    if pillar == 0:
                        screw_start_z = top_nut_hole_height
                    else:
                        screw_start_z = bottom_nut_hole_height

                    cutter = cutter.add(self.fixing_screws.get_cutter(loose=True, layer_thick=self.layer_thick).translate(fixingPos).translate((0, 0, -self.back_plate_from_wall + screw_start_z)))
                else:
                    cutter = cutter.add(self.fixing_screws.get_cutter(loose=True, layer_thick=self.layer_thick).rotate((0, 0, 0), (1, 0, 0), 180).translate(fixingPos).translate((0, 0, z)))




        if self.huygens_maintaining_power:
            #screw to hold the ratchetted chainwheel

            #hold a nyloc nut
            nyloc = True
            bridging = False
            base_z = 0
            nutZ = self.get_plate_thick(back=True) + self.plate_distance - self.fixing_screws.get_nut_height(nyloc=True)

            if self.huygens_wheel_y_offset > self.bottom_pillar_r - self.fixing_screws.get_nut_containing_diameter()/2:
                #nut is in the back of the front plate rather than the top of the bottom pillar, but don't make it as deep as we need the strength
                #making it normal nut deep but will probably still use nyloc
                # nutZ = self.getPlateThick(back=True) + self.plateDistance - (self.fixingScrews.getNutHeight(nyloc=True) - self.fixingScrews.getNutHeight(nyloc=False))

                if self.huygens_wheel_y_offset > self.bottom_pillar_r:
                    #just the front plate
                    bridging = True
                    base_z = self.get_plate_thick(back=True) + self.plate_distance
                    nutZ = self.get_plate_thick(back=True) + self.plate_distance - (self.fixing_screws.get_nut_height(nyloc=True) - self.fixing_screws.get_nut_height(nyloc=False))

            cutter = cutter.add(cq.Workplane("XY").moveTo(self.huygens_wheel_pos[0], self.huygens_wheel_pos[1] + self.huygens_wheel_y_offset).circle(self.fixing_screws.metric_thread / 2).extrude(1000).translate((0, 0, base_z)))
            cutter = cutter.add(self.fixing_screws.get_nut_cutter(nyloc=nyloc, with_bridging=bridging, layer_thick=self.layer_thick).translate(self.huygens_wheel_pos).translate((0, self.huygens_wheel_y_offset, nutZ)))




        #cache to avoid re-calculating (this is reused all over the plates)
        self.fixing_screws_cutter = cutter

        return cutter

    def get_bottom_pillar(self, flat=False):
        '''
        centred on 0,0 flat on the XY plane
        '''

        #for chainholes and things which assume one pillar
        bottomPillarPos = self.bottom_pillar_positions[0]
        if self.extra_heavy and self.bottom_pillars == 1:
            '''
            beef up the bottom pillar
            bottomPillarR^2 + x^2 = chainWheelR^2
            x = sqrt(chainWheelR^2 - bottomPilarR^2)
            
            assumes only one bottom pillar, below the chain wheel
            '''

            pillarTopY = self.bearing_positions[0][1] - math.sqrt(self.powered_wheel_r ** 2 - self.bottom_pillar_r ** 2) - bottomPillarPos[1]

            bottom_pillar = cq.Workplane("XY").moveTo(0 - self.bottom_pillar_r, 0).radiusArc((0 + self.bottom_pillar_r, 0), -self.bottom_pillar_r). \
                lineTo(0 + self.bottom_pillar_r, pillarTopY).radiusArc((0 - self.bottom_pillar_r, pillarTopY), self.powered_wheel_r).close()

            if flat:
                return bottom_pillar

            bottom_pillar = bottom_pillar.extrude(self.plate_distance)



        else:

            if self.narrow_bottom_pillar:
                bottom_pillar = cq.Workplane("XY").moveTo(-self.bottom_pillar_width/2, self.bottom_pillar_height/2 - self.bottom_pillar_width/2)\
                    .radiusArc((self.bottom_pillar_width/2,self.bottom_pillar_height/2 - self.bottom_pillar_width/2), self.bottom_pillar_width/2)\
                    .lineTo(self.bottom_pillar_width/2, -self.bottom_pillar_height/2 + self.bottom_pillar_width/2).\
                    radiusArc((-self.bottom_pillar_width/2,-self.bottom_pillar_height/2 + self.bottom_pillar_width/2),self.bottom_pillar_width/2).close()
            else:
                bottom_pillar = cq.Workplane("XY").moveTo(0, 0).circle(self.bottom_pillar_r)

            if flat:
                return bottom_pillar

            bottom_pillar = bottom_pillar.extrude(self.plate_distance)

            if self.reduce_bottom_pillar_height > 0:
                #assumes one pillar
                #bottom pillar has been moved upwards a smidge, cut out a space for the chain wheel
                r = abs(self.bearing_positions[0][1] - (self.bottom_pillar_positions[0][1] + self.bottom_pillar_r - self.reduce_bottom_pillar_height))
                bottom_pillar = bottom_pillar.cut(cq.Workplane("XY").moveTo(0, r - self.reduce_bottom_pillar_height + self.bottom_pillar_r).circle(r).extrude(self.plate_distance))

        if self.bottom_pillars == 1 and self.weight_driven:
            chainHoles = self.get_chain_holes()
            bottom_pillar = bottom_pillar.cut(chainHoles.translate((-bottomPillarPos[0], -bottomPillarPos[1], self.endshake / 2)))

        #hack - assume screws are in the same place for both pillars for now
        bottom_pillar = bottom_pillar.cut(self.get_fixing_screws_cutter().translate((-bottomPillarPos[0], -bottomPillarPos[1], -self.get_plate_thick(back=True))))
        return bottom_pillar

    def get_standoff_pillar(self, top=True, left=True):
        plate_thick = self.get_plate_thick(standoff=True)
        pillar_r = self.top_pillar_r if top else self.bottom_pillar_r
        if self.pillar_style is not PillarStyle.SIMPLE:
            pillar = fancy_pillar(pillar_r, self.back_plate_from_wall - plate_thick, clockwise=left, style=self.pillar_style)
        else:
            pillar = cq.Workplane("XY").circle(pillar_r).extrude(self.back_plate_from_wall - plate_thick)

        if top:
            # TODO care about left and right
            pillar_pos = self.top_pillar_positions[0 if left else 1]
        else:
            pillar_pos = self.bottom_pillar_positions[0 if left else 1]

        pillar = pillar.cut(self.get_fixing_screws_cutter().translate((-pillar_pos[0], -pillar_pos[1], self.back_plate_from_wall - plate_thick)))

        return pillar

    def get_standoff_pillars(self, top=True):
        pillar_positions = self.top_pillar_positions if top else self.bottom_pillar_positions
        plate_thick = self.get_plate_thick(standoff=True)

        standoff = cq.Workplane("XY")

        clockwise = True
        for pillar_pos in pillar_positions:
            standoff = standoff.union(self.get_standoff_pillar(left=clockwise).translate(pillar_pos).translate((0, 0, plate_thick - self.back_plate_from_wall)))
            clockwise = not clockwise

        return standoff

    def get_pillar(self, top=True, flat=False):
        if top:
            return self.get_top_pillar(flat=flat)
        else:
            return self.get_bottom_pillar(flat=flat)

    def get_top_pillar(self, flat=False):
        '''
        centred on 0,0 flat on the XY plane

        if flat returns a 2D shape

        TODO support two pillars?
        '''
        top_pillar_pos, top_pillar_r, bottom_pillar_pos, bottom_pillar_r, holder_wide = (self.top_pillar_positions[0], self.top_pillar_r, self.bottom_pillar_positions, self.bottom_pillar_r, self.plate_width)
        if self.extra_heavy:
            #sagitta looks nice, otherwise arbitrary at the moment, should really check it leaves enough space for the anchor
            sagitta = top_pillar_r * 0.25
            top_pillar = cq.Workplane("XY").moveTo(0 - top_pillar_r, 0).radiusArc((0 + top_pillar_r, 0), top_pillar_r)\
                .lineTo(0 + top_pillar_r, 0 - top_pillar_r - sagitta). \
                sagittaArc((0 - top_pillar_r, 0 - top_pillar_r - sagitta), -sagitta).close()#.extrude(self.plateDistance)
            if flat:
                return top_pillar

            top_pillar = top_pillar.extrude(self.plate_distance)
        else:
            top_pillar = cq.Workplane("XY").moveTo(0, 0).circle(top_pillar_r)
            if flat:
                return top_pillar
            top_pillar = top_pillar.extrude(self.plate_distance)

        if self.pillar_style is not PillarStyle.SIMPLE and not flat:
            top_pillar = fancy_pillar(self.top_pillar_r, self.plate_distance, style=self.pillar_style)


        if not flat and self.dial and self.dial_top_above_front_plate and self.top_pillar_holds_dial:
            #this pillar also supports the dial!

            screws_apart = self.top_dial_fixing_y - top_pillar_pos[1]
            thick = self.get_plate_thick(back=False)

            dial_holder = cq.Workplane("XY").rect(top_pillar_r*2,screws_apart).extrude(thick).translate((0,screws_apart/2))
            dial_holder = dial_holder.union(cq.Workplane("XY").circle(top_pillar_r).extrude(thick).translate((0,screws_apart)))

            for pos in self.dial_fixing_positions:
                dial_holder = dial_holder.cut(self.dial.fixing_screws.get_cutter(loose=True, with_bridging=True, layer_thick=self.layer_thick).translate(np_to_set(np.subtract(pos, top_pillar_pos))))

            top_pillar = top_pillar.union(dial_holder.translate((0,0,self.plate_distance - thick)))

        top_pillar = top_pillar.cut(self.get_fixing_screws_cutter().translate((-top_pillar_pos[0], -top_pillar_pos[1], -self.get_plate_thick(back=True))))

        return top_pillar

    def get_chain_holes(self):
        '''
        These chain holes are relative to the front of the back plate - they do NOT take plate thickness or wobble into account
        '''

        holePositions = self.going_train.powered_wheel.get_chain_positions_from_top()
        topZ = self.bearing_positions[0][2] + self.going_train.get_arbor(-self.going_train.powered_wheels).get_total_thickness()

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
                chainHole = cq.Workplane("XZ").moveTo(chainX, (chainZTop + chainZBottom)/2).rect(self.chain_hole_d, abs(chainZTop - chainZBottom)).extrude(1000)
                chainHoles.add(chainHole)
            else:
                chainHole = cq.Workplane("XZ").moveTo(holePosition[0][0], holePosition[0][1] + topZ).circle(self.chain_hole_d / 2).extrude(1000)
                chainHoles.add(chainHole)

        if self.using_pulley and self.going_train.powered_wheel.type == PowerType.CORD:
            #hole for cord to be tied in

            #not using a screw anymore, using a bit of steel rod so it won't cut the cord
            cord_holding_screw = MachineScrew(3, countersunk=True)

            chainX = holePositions[0][0][0]
            chainZTop = topZ + holePositions[0][0][1]
            pulleyX = -chainX
            # might want it as far back as possible?
            # for now, as far FORWARDS as possible, because the 4kg weight is really wide!
            pulleyZ = chainZTop - self.chain_hole_d / 2  # chainZBottom + self.chainHoleD/2#(chainZTop + chainZBottom)/2
            if self.back_plate_from_wall > 0:
                #centre it instead
                pulleyZ = topZ + (holePositions[0][0][1] + holePositions[0][1][1])/2
            # and one hole for the cord to be tied
            pulleyHole = cq.Workplane("XZ").moveTo(pulleyX, pulleyZ).circle(self.chain_hole_d / 2).extrude(1000)
            chainHoles.add(pulleyHole)
            # print("chainZ min:", chainZBottom, "chainZ max:", chainZTop)

            # original plan was a screw in from the side, but I think this won't be particularly strong as it's in line with the layers
            # so instead, put a screw in from the front
            pulleyY = self.bottom_pillar_positions[0][1]# + self.bottomPillarR / 2
            if self.extra_heavy:
                #bring it nearer the top, making it easier to tie the cord around it
                pulleyY = self.bottom_pillar_positions[0][1] + self.bottom_pillar_r - cord_holding_screw.metric_thread
            # this screw will provide something for the cord to be tied round
            #TODO there is a bug where the countersink isn't right - cannot fathmon how, but since I'm now using steel rod instead of a screw I'll leave it
            pulleyScrewHole = cord_holding_screw.get_cutter(length=self.plate_distance-5).rotate((0, 0, 0), (1, 0, 0), 180).translate((pulleyX, pulleyY, self.plate_distance))

            #but it's fiddly so give it a hole and protect the screw
            max_extra_space = self.bottom_pillar_r - pulleyX - 1
            if max_extra_space > cord_holding_screw.metric_thread*2:
                max_extra_space = cord_holding_screw.metric_thread*2
            extra_space = cq.Workplane("XY").circle(max_extra_space).extrude(self.chain_hole_d).translate((pulleyX, pulleyY, pulleyZ - self.chain_hole_d / 2))
            #make the space open to the top of the pillar
            extra_space = extra_space.union(cq.Workplane("XY").rect(max_extra_space*2, 1000).extrude(self.chain_hole_d).translate((pulleyX, pulleyY + 500, pulleyZ - self.chain_hole_d / 2)))
            #and keep it printable
            extra_space = extra_space.union(get_hole_with_hole(inner_d=self.fixing_screws.metric_thread, outer_d=max_extra_space * 2, deep=self.chain_hole_d, layer_thick=self.layer_thick)
                                            .rotate((0,0,0),(0,0,1),90).translate((pulleyX, pulleyY, pulleyZ - self.chain_hole_d / 2)))

            #I'm worried about the threads cutting the thinner cord, but there's not quite enough space to add a printed bit around the screw
            # I could instead file off the threads for this bit of the screw?

            chainHoles.add(extra_space)


            chainHoles.add(pulleyScrewHole)
        return chainHoles

    def get_bearing_holder(self, height, addSupport=True, bearingInfo=None):
        '''
        cylinder with bearing holder on the end for putting on the front of a front plate
        '''

        #height from base (outside) of plate, so this is inclusive of base thickness, not in addition to
        if bearingInfo is None:
            bearingInfo = get_bearing_info(self.arbor_d)
        wallThick = self.bearing_wall_thick
        # diameter = bearingInfo.outer_d + wallThick*2
        outerR = bearingInfo.outer_d/2 + wallThick
        innerInnerR = bearingInfo.outer_safe_d/2
        innerR = bearingInfo.outer_d/2
        holder = cq.Workplane("XY").circle(outerR).extrude(height)

        # holder = holder.faces(">Z").workplane().circle(diameter/2).circle(bearingInfo.outer_d/2).extrude(bearingInfo.height)
        # extra support?
        if addSupport:
            support = cq.Workplane("YZ").moveTo(0,0).lineTo(-height-outerR,0).lineTo(-outerR,height).lineTo(0,height).close().extrude(wallThick).translate((-wallThick/2,0,0))
            holder = holder.add(support)
        holder = holder.cut(cq.Workplane("XY").circle(innerInnerR).extrude(height))
        holder = holder.cut(cq.Workplane("XY").circle(innerR).extrude(bearingInfo.height).translate((0,0,height - bearingInfo.height)))

        return holder

    def get_bearing_punch(self, plate_thick, bearing, bearing_on_top=True , with_support=False):
        '''
        General purpose bearing punch, aligned for cutting into the plate
        '''
        if bearing.height >= plate_thick:
            raise ValueError("plate not thick enough to hold bearing: {}".format(bearing))

        punch = bearing.get_cutter(layer_thick=self.layer_thick, with_bridging=with_support)

        if bearing_on_top:
            punch = punch.rotate((0,0,0),(1,0,0),180).translate((0,0,plate_thick))

        return punch

    def punch_bearing_holes(self, plate, back, make_plate_bigger=True):
        for i, pos in enumerate(self.bearing_positions):
            bearing = self.arbors_for_plate[i].bearing
            bearing_on_top = back

            if not back and i == 0:
                try:
                    bearing = self.going_train.powered_wheel.key_bearing
                except:
                    pass

            needs_plain_hole = False
            if self.pendulum_fixing in [PendulumFixing.DIRECT_ARBOR, PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS, PendulumFixing.SUSPENSION_SPRING] and i == len(self.bearing_positions)-1:
                #if true we just need a hole for the direct arbour to fit through

                if self.escapement_on_front and not back:
                    '''
                    need the bearings to be on the back of front plate and back of the back plate
                    so endshake will be between back of back plate and front of the wall standoff bearing holder
                    this way there doesn't need to be a visible bearing on the front
                    '''
                    needs_plain_hole = True

                if not self.pendulum_at_front and back:
                    needs_plain_hole = True


            outer_d =  bearing.outer_d
            if needs_plain_hole:
                outer_d = self.direct_arbor_d + 3

            if outer_d > self.plate_width - self.bearing_wall_thick*2 and make_plate_bigger and not needs_plain_hole:
                #this is a chunkier bearing, make the plate bigger
                try:
                    plate = plate.union(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(outer_d / 2 + self.bearing_wall_thick).extrude(self.get_plate_thick(back=back)))
                except:
                    print("wasn't able to make plate bigger for bearing")

            if needs_plain_hole:
                plate = plate.cut(cq.Workplane("XY").circle(outer_d/2).extrude(self.get_plate_thick(back=back)).translate((pos[0], pos[1], 0)))
            else:
                bridging = False
                if not back and not self.front_plate_printed_front_face_down():
                    bridging = True
                plate = plate.cut(self.get_bearing_punch(plate_thick=self.get_plate_thick(back=back),bearing=bearing, bearing_on_top=bearing_on_top, with_support=bridging)
                                  .translate((pos[0], pos[1], 0)))
        return plate

    def cut_wall_fixing_hole(self, plate, screwhole_pos, screw_head_d = 9, screw_body_d = 6, slot_length = 7, back_thick = -1, add_extra_support=False, plate_thick=-1):
        '''
        screwholePos is the position the clock will hang from
        this is an upside-down-lollypop shape

        if backThick is default, this cuts through the whole plate
        if not, backthick is the thickness of the plastic around the screw


          /-\   circle of screwBodyD diameter (centre of the circle is the screwholePos)
          |  |  screwbodyD wide
          |  |  distance between teh two circle centres is slotLength
        /     \
        |     |  circle of screwHeadD diameter
        \_____/
        '''
        if plate_thick < 0:
            plate_thick = self.get_plate_thick(back=True)

        if add_extra_support:
            #a circle around the big hole to strengthen the plate
            #assumes plate has been tagged
            #removing all the old bodges and simplifying
            # extraSupportSize = screwHeadD*1.25
            extraSupportR = self.plate_width * 0.5
            supportCentre=[screwhole_pos[0], screwhole_pos[1] - slot_length]

            # if self.heavy:
            #     extraSupportSize*=1.5
            #     supportCentre[1] += slotLength / 2
            #     #bodge if the screwhole is off to one side
            #     if screwholePos[0] != 0:
            #         #this can be a bit finnickity - I think if something lines up exactly wrong with the bearing holes?
            #         supportCentre[0] += (-1 if screwholePos[0] > 0 else 1) * extraSupportSize*0.5
            #
            # plate = plate.workplaneFromTagged("base").moveTo(supportCentre[0], supportCentre[1] ).circle(extraSupportSize).extrude(plate_thick)
            plate = plate.union(get_stroke_line([(screwhole_pos[0], screwhole_pos[1] - slot_length), (screwhole_pos[0], screwhole_pos[1])], wide=extraSupportR * 2, thick=plate_thick))

        #big hole
        plate = plate.faces(">Z").workplane().tag("top").moveTo(screwhole_pos[0], screwhole_pos[1] - slot_length).circle(screw_head_d / 2).cutThruAll()
        #slot
        plate = plate.workplaneFromTagged("top").moveTo(screwhole_pos[0], screwhole_pos[1] - slot_length / 2).rect(screw_body_d, slot_length).cutThruAll()
        # small hole
        plate = plate.workplaneFromTagged("top").moveTo(screwhole_pos[0], screwhole_pos[1]).circle(screw_body_d / 2).cutThruAll()

        if back_thick > 0 and back_thick < plate_thick:
            extraY = screw_body_d * 0.5
            cutter = cq.Workplane("XY").moveTo(screwhole_pos[0], screwhole_pos[1] + extraY).circle(screw_head_d / 2).extrude(self.get_plate_thick(back=True) - back_thick).translate((0, 0, back_thick))
            cutter = cutter.add(cq.Workplane("XY").moveTo(screwhole_pos[0], screwhole_pos[1] - slot_length / 2 + extraY / 2).rect(screw_head_d, slot_length + extraY).extrude(plate_thick - back_thick).translate((0, 0, back_thick)))
            plate = plate.cut(cutter)

        return plate

    def get_moon_complication_fixings_absolute(self):
        return [np_to_set(np.add(self.hands_position, relative_pos[:2])) for relative_pos in self.moon_complication.get_arbor_positions_relative_to_motion_works()]

    def rear_additions_to_plate(self, plate, plate_thick=-1):
        if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL and self.going_train.powered_wheel.ratchet_at_back:
            # beef up the plate where the pawl screw goes through so we don't need to have an extra plate on the back to make it strong enough
            # only possible at the back unless I change where the barrel is (TODO support power at back again...)
            pawl_pos = np_to_set(np.add(self.bearing_positions[0][:2], self.going_train.powered_wheel.ratchet.get_pawl_screw_position()))
            # should probably do somethign sensible like work out how much space there actually is between the nearby wheel and the plate


            plate = (plate.faces(">Z").workplane().moveTo(-pawl_pos[0], pawl_pos[1]).circle(self.plate_width / 2)
                     .workplane(offset=self.beefed_up_pawl_thickness).moveTo(-pawl_pos[0], pawl_pos[1]).circle(self.plate_width * 0.4).loft(combine=True))

        if self.plaque is not None:
            for relative_pos in self.plaque.get_screw_positions():
                pos = rotate_vector(relative_pos, (0, 0, 1), self.plaque_angle)
                pos = np_to_set(np.add(self.plaque_pos, pos))
                plate = plate.cut(self.plaque.screws.get_cutter().translate((pos[0], pos[1], - self.plaque.thick)))

        else:
            plate = plate.cut(self.get_text())

        return plate

    def add_motion_works_arm(self, plate, plate_thick, cut_holes=False):
        mini_arm_width = self.motion_works_screws.get_nut_containing_diameter() * 2

        if self.need_motion_works_holder:
            # screw would be on top of a bearing, so there's a separate peice to hold it
            for pos in self.motion_works_fixings_relative_pos:
                screw_pos = np_to_set(np.add(self.motion_works_pos, pos))
                if cut_holes:
                    plate = plate.cut(cq.Workplane("XY").circle(self.motion_works_screws.get_diameter_for_die_cutting() / 2).extrude(plate_thick).translate(screw_pos))
        else:
            if self.little_arm_to_motion_works:
                # extra material in case the motion works is at an angle off to one side
                plate = plate.union(get_stroke_line([self.hands_position, self.motion_works_pos], wide=mini_arm_width, thick=plate_thick))
            # hole for screw to hold motion works arbour
            if cut_holes:
                plate = plate.cut(self.motion_works_screws.get_cutter().translate(self.motion_works_pos))
        return plate

    def front_additions_to_plate(self, plate, plate_thick=-1, moon=False):
        '''
        stuff only needed to be added to the front plate
        '''
        if plate_thick < 0:
            plate_thick = self.get_plate_thick(back=False)
        # FRONT

        # note - works fine with the pendulum on the same rod as teh anchor, but I'm not sure about the long term use of ball bearings for just rocking back and forth
        # suspensionBaseThick=0.5
        # suspensionPoint = self.pendulum.getSuspension(False,suspensionBaseThick ).translate((self.bearingPositions[len(self.bearingPositions)-1][0], self.bearingPositions[len(self.bearingPositions)-1][1], plateThick-suspensionBaseThick))
        #         #
        #         # plate = plate.add(suspensionPoint)
        # new plan: just put the pendulum on the same rod as the anchor, and use nyloc nuts to keep both firmly on the rod.
        # no idea if it'll work without the rod bending!

        #not using anymore - don't want extra bearings on the pendulum (adds too much friction and it doesn't really droop much)
        #but unlikely to ever re-print a clock with the friction fitting pendulum anyway
        # if self.pendulumAtFront and self.pendulumSticksOut > 0 and self.pendulumFixing == PendulumFixing.FRICTION_ROD:
        #     #a cylinder that sticks out the front and holds a bearing on the end
        #     extraBearingHolder = self.getBearingHolder(self.pendulumSticksOut, False).translate((self.bearingPositions[len(self.bearingPositions) - 1][0], self.bearingPositions[len(self.bearingPositions) - 1][1], plateThick))
        #     plate = plate.add(extraBearingHolder)

        mini_arm_width = self.motion_works_screws.get_nut_containing_diameter() * 2

        plate = self.add_motion_works_arm(plate, plate_thick, cut_holes=True)

        if self.motion_works.cannon_pinion_friction_ring:
            for pos in self.cannon_pinion_friction_clip_fixings_pos:
                plate = plate.cut(cq.Workplane("XY").circle(self.motion_works_screws.get_diameter_for_die_cutting()/2).extrude(plate_thick).translate(pos))

        #embedded nut on the front so we can tighten this screw in
        #decided against this - I think it's might make the screw wonky as there's less plate for it to be going through.
        #if it's loose, use superglue.
        # nutDeep =  self.fixingScrews.getNutHeight(half=True)
        # nutSpace = self.fixingScrews.getNutCutter(half=True).translate(motionWorksPos).translate((0,0,self.getPlateThick(back=False) - nutDeep))
        #
        # plate = plate.cut(nutSpace)

        if self.dial is not None:

            if self.dial_top_above_front_plate and not self.top_pillar_holds_dial:
                # need to extend the front plate off the top of teh clock to hold the dial
                # TODO make this more robust (assumes vertical or compact plates with one top pillar)

                dial_support_pos = (self.hands_position[0], self.hands_position[1] + self.dial.outside_d/2- self.dial.dial_width/2)
                # plate = plate.union(cq.Workplane("XY").circle(self.plate_width / 2).extrude(plate_thick).translate(dial_support_pos))
                # plate = plate.union(cq.Workplane("XY").rect(self.plate_width, dial_support_pos[1] - self.top_pillar_positions[0][1]).extrude(plate_thick).translate((self.bearing_positions[-1][0], (self.top_pillar_positions[0][1] + dial_support_pos[1]) / 2)))
                plate = plate.union(get_stroke_line([dial_support_pos, self.bearing_positions[-1][:2]], wide=self.plate_width, thick = plate_thick))

            #TODO bottom extension (am I ever going to want it?)


            for pos in self.dial_fixing_positions:
                plate = plate.cut(self.dial.fixing_screws.get_cutter(loose=True, with_bridging=True, layer_thick=self.layer_thick).translate(pos))

        if self.moon_complication is not None and moon:

            #screw holes for the moon complication arbors
            for i, pos in enumerate(self.get_moon_complication_fixings_absolute()):
                # extra bits of plate to hold the screw holes for extra arbors

                #skip the second one if it's in the same place as the extra arm for the extraheavy compact plates (old very specific logic...)
                if i != 1 or (self.gear_train_layout != GearTrainLayout.COMPACT and self.extra_heavy) or not self.moon_complication.on_left:

                    plate = plate.union(get_stroke_line([self.hands_position, pos], wide=mini_arm_width, thick=plate_thick))


                plate = plate.cut(self.moon_complication.screws.get_cutter(with_bridging=True, layer_thick=self.layer_thick).translate(pos))


        # need an extra chunky hole for the big bearing that the key slots through
        #should now be done as part of punch_bearing_holes
        # if self.winding_key is not None:
        #     powered_wheel = self.going_train.powered_wheel
        #
        #     if self.front_plate_printed_front_face_down():
        #         #can print front-side on the build plate, so the bearing holes are printed on top
        #         cord_bearing_hole = cq.Workplane("XY").circle(powered_wheel.key_bearing.outer_d / 2).extrude(powered_wheel.key_bearing.height)
        #     else:
        #         cord_bearing_hole = get_hole_with_hole(self.key_hole_d, powered_wheel.key_bearing.outer_d, powered_wheel.key_bearing.height, layer_thick=self.layer_thick)
        #
        #     cord_bearing_hole = cord_bearing_hole.faces(">Z").workplane().circle(self.key_hole_d / 2).extrude(plate_thick)
        #
        #     plate = plate.cut(cord_bearing_hole.translate((self.bearing_positions[0][0], self.bearing_positions[0][1], 0)))

        #can't decide where the best place is to do this, currently it lives in the MantelClockPlates
        # if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL and not self.going_train.powered_wheel.ratchet_at_back:
        #     #spring powered, need the ratchet!
        #     screw = self.going_train.powered_wheel.ratchet.fixing_screws
        #
        #     for relative_pos in self.going_train.powered_wheel.ratchet.get_screw_positions():
        #         pos = npToSet(np.add(self.bearing_positions[0][:2],relative_pos))
        #         plate = plate.cut(screw.get_cutter(for_tap_die=True, with_bridging=True).translate(pos))


        if self.huygens_maintaining_power:

            #designed with a washer to be put under the chain wheel to reduce friction (hopefully)


            #add an extra bit at the bottom so the chain can't easily fall off
            chainholeD = self.huygens_wheel.get_chain_hole_diameter()
            holePositions = self.huygens_wheel.get_chain_positions_from_top()
            relevantChainHoles = [ pair[0] for pair in holePositions ]

            minThickAroundChainHole = 2
            #make a fancy bit that sticks out the bottom with holes for the chain - this makes it hard for the chain to detatch from the wheel

            extraHeight = relevantChainHoles[0][1] + self.huygens_wheel.get_height() - self.huygens_wheel.ratchet.thick + chainholeD / 2 + minThickAroundChainHole
            ratchetD = self.huygens_wheel.ratchet.outsideDiameter
            # ratchet for the chainwheel on the front of the clock
            ratchet = self.huygens_wheel.ratchet.getOuterWheel(extraThick=WASHER_THICK_M3)

            ratchet = ratchet.faces(">Z").workplane().circle(ratchetD/2).circle(self.huygens_wheel.ratchet.toothRadius).extrude(extraHeight)

            totalHeight = extraHeight + WASHER_THICK_M3 + self.huygens_wheel.ratchet.thick


            cutter = cq.Workplane("YZ").moveTo(-ratchetD/2,totalHeight).spline(includeCurrent=True,listOfXYTuple=[(ratchetD/2, totalHeight-extraHeight)], tangents=[(1,0),(1,0)])\
                .lineTo(ratchetD/2,totalHeight).close().extrude(ratchetD).translate((-ratchetD/2,0,0))
            for holePosition in holePositions:
                #chainholes are relative to the assumed height of the chainwheel, which includes a washer
                chainHole = cq.Workplane("XZ").moveTo(holePosition[0][0], holePosition[0][1] + (self.huygens_wheel.get_height() + WASHER_THICK_M3)).circle(chainholeD / 2).extrude(1000)
                cutter.add(chainHole)


            ratchet = ratchet.cut(cutter)

            if self.bottom_pillars > 1:
                raise ValueError("Hyugens wheel not yet supported with more than 1 bottom pillar")
            #assumes single pillar
            huygens_pos = self.bottom_pillar_positions[0]
            plate = plate.union(ratchet.translate(huygens_pos).translate((0, self.huygens_wheel_y_offset, plate_thick)))
            if ratchetD > self.bottom_pillar_r:
                plate = plate.union(cq.Workplane("XY").circle(ratchetD/2).extrude(plate_thick).translate(huygens_pos).translate((0, self.huygens_wheel_y_offset)))

        if (self.going_train.powered_wheel.type in [PowerType.CHAIN2, PowerType.CHAIN] and not self.escapement_on_front
                and not self.huygens_maintaining_power and not self.pendulum_at_front and self.bottom_pillars > 1
                and not self.going_train.chain_at_back):
            #add a semicircular bit under the chain wheel (like on huygens) to stop chain from being able to fall off easily
            #TODO support cord wheels and chain at back

            powered_wheel = self.going_train.powered_wheel

            chainholeD = powered_wheel.get_chain_hole_diameter()
            holePositions = powered_wheel.get_chain_positions_from_top()
            relevantChainHoles = [pair[0] for pair in holePositions]


            minThickAroundChainHole = 3
            thick = 3


            outer_r = powered_wheel.ratchet.outsideDiameter / 2 + self.gear_gap + thick
            deep = powered_wheel.get_height()-powered_wheel.ratchet.thick/2

            extra_plate = cq.Workplane("XY").circle(outer_r).extrude(plate_thick)
            extra_plate = extra_plate.union(cq.Workplane("XY").circle(outer_r).circle(outer_r - thick).extrude(deep).translate((0,0,-deep)))

            extra_plate = extra_plate.intersect(cq.Workplane("XY").moveTo(0,-outer_r - self.bottom_pillar_height/2).rect(outer_r*2, outer_r*2).extrude(self.plate_distance + plate_thick).translate((0, 0, -self.plate_distance)))
            cutter = cq.Workplane("XY")
            for holePosition in relevantChainHoles:
                #chainholes are relative to the assumed height of the chainwheel, which includes a washer
                chainHole = cq.Workplane("XZ").moveTo(holePosition[0], holePosition[1] - self.endshake/2).circle(chainholeD / 2).extrude(1000)
                cutter.add(chainHole)

            extra_plate = extra_plate.cut(cutter)

            plate = plate.union(extra_plate.translate(self.bearing_positions[0][:2]))



        if self.escapement_on_front and self.extra_support_for_escape_wheel:
            #this is a bearing extended out the front, helps maintain the geometry for a grasshopper on plates with a narrow plateDistance
            plate = plate.add(self.get_bearing_holder(-self.going_train.escapement.get_wheel_base_to_anchor_base_z()).translate((self.bearing_positions[-2][0], self.bearing_positions[-2][1], self.get_plate_thick(back=False))))

        if self.moon_complication is not None:
            moon_screws = self.moon_holder.get_fixing_positions()

            for pos in moon_screws:
                bridging = not self.front_plate_printed_front_face_down()
                # pos = (pos[0], pos[1], self.get_plate_thick(back=True) + self.plate_distance)
                # cutter = cutter.add(self.motion_works_screws.getCutter(headSpaceLength=0).translate(pos))
                # putting nuts in the back of the plate so we can screw the moon holder on after the clock is mostly assembled
                plate = plate.cut(self.moon_holder.fixing_screws.get_nut_cutter(with_bridging=bridging).rotate((0, 0, 0), (0, 0, 1), 360 / 12).translate(pos))
                plate = plate.cut(cq.Workplane("XY").circle(self.moon_holder.fixing_screws.get_rod_cutter_r()).extrude(1000).translate(pos))


        return plate

    def get_diameter_for_pulley(self):

        holePositions = self.going_train.powered_wheel.get_chain_positions_from_top()

        if self.huygens_maintaining_power:

            chainWheelTopZ = self.bearing_positions[0][2] + self.going_train.get_arbor(-self.going_train.powered_wheels).get_total_thickness() + self.get_plate_thick(back=True) + self.endshake / 2
            chainWheelChainZ = chainWheelTopZ + holePositions[0][0][1]
            huygensChainPoses = self.huygens_wheel.get_chain_positions_from_top()
            #washer is under the chain wheel
            huygensChainZ = self.get_plate_thick(True) + self.get_plate_thick(False) + self.plate_distance + self.huygens_wheel.get_height() + WASHER_THICK_M3 + huygensChainPoses[0][0][1]

            return huygensChainZ - chainWheelChainZ
        else:
            return abs(holePositions[0][0][0] - holePositions[1][0][0])

    def key_is_inside_dial(self):
        '''
        Very crude, assumes user has ensured the key doesn't intersect with the dial
        '''
        if self.dial is None:
            return False

        key_pos = self.bearing_positions[0][:2]
        dial_centre = self.hands_position

        distance = np.linalg.norm(np.subtract(dial_centre, key_pos))

        return distance < self.dial.outside_d/2



    def calc_winding_key_info(self):
        '''
        set front_plate_has_key_hole and key_offset_from_front_plate

        hacky side effect: will set key length on cord wheel
        '''

        if (self.weight_driven and not (self.going_train.powered_wheel.type == PowerType.CORD and self.going_train.powered_wheel.use_key)):
            raise ValueError("No winding key on this clock!")

        powered_wheel = self.going_train.powered_wheel
        key_bearing = powered_wheel.key_bearing


        self.key_hole_d = key_bearing.outer_safe_d

        #on the old cord wheel, which didn't know the plate thickness, account for how much of the square bit is within the plate
        key_within_front_plate = self.get_plate_thick(back=False) - key_bearing.height

        # self.key_hole_d = self.going_train.powered_wheel.keyWidth + 1.5
        if self.bottom_of_hour_hand_z() < 25 and (self.weight_driven or self.going_train.powered_wheel.ratchet_at_back):# and self.key_hole_d > front_hole_d and self.key_hole_d < key_bearing.outer_d - 1:
            # only if the key would otherwise be a bit too short (for dials very close to the front plate) make the hole just big enough to fit the key into
            #can't do this for spring driven as the ratchet is on the front (could move it to the back but it would make letting down the spring harder)
            print("Making the front hole just big enough for the cord key")
            #offset *into* the front plate
            self.key_offset_from_front_plate = -key_within_front_plate
        else:
            self.key_offset_from_front_plate = 1

        #HACK remove this once cord wheel works like the spring barrel (where ArborForPlate provides all the info about how long the key is)
        if not self.weight_driven:
            key_within_front_plate = 0

        if self.key_is_inside_dial():
            key_length = self.bottom_of_hour_hand_z() - 4 + key_within_front_plate
        else:
            key_length = key_within_front_plate + self.ideal_key_length
        #hack - set key size here
        #note - do this relative to the hour hand, not the dial, because there may be more space for the hour hand to avoid the second hand
        #TODO remove this for cord wheel

        self.going_train.powered_wheel.key_square_bit_height = key_length
        #the slightly less hacky way... (although now I think about it, is it actually? we're still reaching into an object to set something)
        self.arbors_for_plate[0].key_length = key_length

        #how much of the key sticks out the front of the front plate
        self.key_length = key_length - key_within_front_plate

        square_bit_inside_front_plate_length = self.get_plate_thick(back=False) - key_bearing.height
        key_hole_deep = key_length - (square_bit_inside_front_plate_length + self.key_offset_from_front_plate) - self.endshake



        if self.dial is not None and not self.key_is_inside_dial() and self.weight_driven:
            # just so the crank (only for weights) doesn't clip the dial (the key is outside the dial)
            cylinder_length = self.dial_z + self.dial.thick + 6 - self.key_offset_from_front_plate
            # reach to the centre of the dial (just miss the hands)
            handle_length = self.hands_position[1] - (self.dial.outside_d / 2 - self.dial.dial_width / 2) - self.bearing_positions[0][1] - 5
        else:
            # above the hands (the key is inside the dial)
            cylinder_length = self.top_of_hands_z + 6 - self.key_offset_from_front_plate
            # avoid the centre of the hands (but make as long as possible to ease winding)
            handle_length = self.hands_position[1] - self.bearing_positions[0][1] - 6  # 10

        crank = self.weight_driven
        key_wiggle_room = 0.75 # the default
        wall_thick = 2.5 # the default
        sideways = False
        if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL and not self.going_train.powered_wheel.ratchet_at_back:
            #take into accuont the ratchet on the front
            ratchet_thickness = self.going_train.powered_wheel.ratchet.thick + self.going_train.powered_wheel.ratchet_collet_thick
            key_hole_deep -= ratchet_thickness
            cylinder_length -= ratchet_thickness
            #trying a bit less for the hex key (now trying more again since I'm printing it sideways
            # key_wiggle_room = 0.5
            #this was a bit too much, going back to default
            # key_wiggle_room = 1

        if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL:
            wall_thick = 5
            sideways = True

        self.winding_key = WindingKey(key_containing_diameter=powered_wheel.get_key_size(), cylinder_length = cylinder_length, key_hole_deep=key_hole_deep,
                                      handle_length=handle_length, crank=crank, key_sides=powered_wheel.get_key_sides(), key_wiggle_room=key_wiggle_room, wall_thick=wall_thick,
                                      print_sideways=sideways)

        if self.key_offset_from_front_plate < 0:
            self.key_hole_d = self.winding_key.body_wide+1.5

        print("winding key length {:.1f}mm".format(key_length))

    def get_winding_key(self):
        return self.winding_key


    def get_assembled(self, one_peice = True):
        '''
        3D model of teh assembled plates
        '''
        bottom_plate = self.get_plate(True, for_printing=False)
        top_plate = self.get_plate(False, for_printing=False)
        front_of_clock_z = self.get_plate_thick(True) + self.get_plate_thick(False) + self.plate_distance

        plates = bottom_plate.add(top_plate.translate((0, 0, self.plate_distance + self.get_plate_thick(back=True))))

        pillars = cq.Workplane("XY")
        standoff_pillars = cq.Workplane("XY")
        if self.pillars_separate:
            for bottom_pillar_pos in self.bottom_pillar_positions:
                pillars = pillars.add(self.get_pillar(top=False).translate(bottom_pillar_pos).translate((0, 0, self.get_plate_thick(back=True))))
            for top_pillar_pos in self.top_pillar_positions:
                pillars = pillars.add(self.get_pillar(top=True).translate(top_pillar_pos).translate((0, 0, self.get_plate_thick(back=True))))



        if self.back_plate_from_wall > 0:
            # need wall standoffs
            top_standoff = self.get_wall_standoff(top=True, for_printing=False)
            if top_standoff is not None:
                plates = plates.add(top_standoff)
            bottom_standoff = self.get_wall_standoff(top=False, for_printing=False)
            if bottom_standoff is not None:
                plates = plates.add(bottom_standoff)
            if self.standoff_pillars_separate:
                standoff_pillars = standoff_pillars.add(self.get_standoff_pillars(top=True))
                if bottom_standoff is not None:
                    standoff_pillars = standoff_pillars.add(self.get_standoff_pillars(top=False))

        if self.need_front_anchor_bearing_holder() and not self.front_anchor_holder_part_of_dial:
            plates = plates.add(self.get_front_anchor_bearing_holder(for_printing=False))

        if self.need_motion_works_holder:
            plates = plates.add(self.get_motion_works_holder().translate((self.motion_works_pos[0], self.motion_works_pos[1], front_of_clock_z)))

        detail = None
        if self.style in [PlateStyle.RAISED_EDGING]:
            detail = self.apply_style_to_plate(cq.Workplane("XY"), back=True, addition_allowed=True).add(self.apply_style_to_plate(cq.Workplane("XY"), back=False, addition_allowed=True)
                                                                                  .translate((0,0,self.get_plate_thick(back=True) + self.plate_distance)))

        if one_peice:
            whole =  plates.union(pillars)
            if detail is not None:
                whole= whole.union(detail)
            return whole

        return (plates, pillars, detail, standoff_pillars)


    def get_front_plate_in_parts(self):
        '''
        if self.split_detailed_plate divide the front plate into two parts to be printed seperately to avoid needing bridging
        '''
        tallest_bearing = max([arbor.bearing.height for arbor in self.arbors_for_plate])

        plate_thick = self.get_plate_thick(back=False)

        main_chunk_thick = (tallest_bearing + 1)
        main_chunk_thick = main_chunk_thick - main_chunk_thick % self.layer_thick

        front_plate = self.get_plate(back=False, for_printing=True)

        plane = cq.Workplane("XY").rect(1000,1000).extrude(main_chunk_thick)

        base = front_plate.intersect(plane)
        top = front_plate.cut(plane).translate((0,0,-main_chunk_thick))
        detail = self.get_plate_detail(back=False, for_printing=True).translate((0,0,-main_chunk_thick))

        return base, top, detail


    def output_STLs(self, name="clock", path="../out"):

        if self.dial is not None:
            self.dial.output_STLs(name, path)

        front_detail = self.get_plate_detail(back=False, for_printing=True)
        export_STL(self.get_plate(True, for_printing=True), "plate_back", name, path, tolerance=self.export_tolerance)


        if self.split_detailed_plate:
            front_plate_main, front_plate_top, front_plate_detail = self.get_front_plate_in_parts()
            export_STL(front_plate_main, "plate_front_main", name, path, tolerance=self.export_tolerance)
            export_STL(front_plate_top, "plate_front_top", name, path, tolerance=self.export_tolerance)
            export_STL(front_plate_detail, "plate_front_detail", name, path, tolerance=self.export_tolerance)
        else:
            export_STL(self.get_plate(False, for_printing=True), "plate_front", name, path, tolerance=self.export_tolerance)
            export_STL(front_detail, "plate_front_detail", name, path, tolerance=self.export_tolerance)


        if not self.text_on_standoffs and self.plaque is None:
            export_STL(self.get_text(for_printing=True), "plate_back_text", name, path)

        if self.pillars_separate:
            export_STL(self.get_pillar(top=False), "pillar_bottom", name, path, tolerance=0.05)
            export_STL(self.get_pillar(top=True), "pillar_top", name, path, tolerance=0.05)

        if self.motion_works.cannon_pinion_friction_ring:
            out = os.path.join(path, "{}_friction_clip.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_cannon_pinion_friction_clip(), out)

        if len(self.get_screwhole_positions()) > 1:
            #need a template to help drill the screwholes!
            out = os.path.join(path, "{}_drill_template_6mm.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_drill_template(6, layer_thick=0.4), out)

        if self.back_plate_from_wall > 0:
            export_STL(self.get_wall_standoff(top=True), "wall_standoff_top", clock_name=name, path=path)

            bottom_standoff = self.get_wall_standoff(top=False)
            export_STL(bottom_standoff, "wall_standoff_bottom", clock_name=name, path=path)

            if self.text_on_standoffs:
                export_STL(self.get_text(top_standoff=True, for_printing=True), "wall_standoff_top_text", clock_name=name, path=path)
                export_STL(self.get_text(top_standoff=False, for_printing=True), "wall_standoff_bottom_text", clock_name=name, path=path)

            if self.standoff_pillars_separate:
                for left in [True, False]:
                    for top in [True, False]:
                        pillar_name = "{}_{}".format("left" if left else "right", "top" if top else "bottom")
                        export_STL(self.get_standoff_pillar(top=top, left=left), pillar_name, clock_name=name, path=path, tolerance=0.05)

        if self.huygens_maintaining_power:
            self.huygens_wheel.output_STLs(name + "_huygens", path)

        for i,arbourForPlate in enumerate(self.arbors_for_plate):
            shapes = arbourForPlate.get_shapes()
            #TODO maybe include powered wheel in shapes? not sure if it's worth the effort
            if arbourForPlate.type == ArborType.POWERED_WHEEL:
                arbourForPlate.arbor.powered_wheel.output_STLs(name + "_arbour_{}".format(i), path)
            for shapeName in shapes.keys():
                out = os.path.join(path, "{}_arbour_{}_{}.stl".format(name, i, shapeName))
                print("Outputting ", out)
                if shapes[shapeName] is not None:
                    exporters.export(shapes[shapeName], out)
                else:
                    print("WARNING {} is None".format(shapeName))

        if self.need_motion_works_holder:
            out = os.path.join(path, "{}_motion_works_holder.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_motion_works_holder(), out)

        key = self.get_winding_key()
        if key is not None:
            key.output_STLs(name, path)

        if self.need_front_anchor_bearing_holder():
            out = os.path.join(path, "{}_anchor_front_bearing_holder.stl".format(name))
            print("Outputting ", out)
            exporters.export(self.get_front_anchor_bearing_holder(), out)

        if self.moon_holder is not None:
            holder_parts = self.moon_holder.get_moon_holder_parts()
            for i, holder in enumerate(holder_parts):
                out = os.path.join(path, "{}_moon_holder_part{}.stl".format(name,i))
                print("Outputting ", out)
                exporters.export(holder, out)

        # for arbour in range(self.goingTrain.wheels + self.goingTrain.chainWheels + 1):
        #     for top in [True, False]:
        #         extensionShape=self.getArbourExtension(arbour, top=top)
        #         if extensionShape is not None:
        #             out = os.path.join(path, "{}_arbour_{}_{}_extension.stl".format(name, arbour, "top" if top else "bottom"))
        #             print("Outputting ", out)
        #             exporters.export(extensionShape, out)

class MantelClockPlates(SimpleClockPlates):
    '''
    Skeleton mantel clock
    '''
    def __init__(self, going_train, motion_works, plate_thick=8, back_plate_thick=None, pendulum_sticks_out=15, name="", centred_second_hand=False, dial=None,
                 moon_complication=None, second_hand=True, motion_works_angle_deg=-1, screws_from_back=None, layer_thick=LAYER_THICK, escapement_on_front=False,
                 symetrical=False, style=PlateStyle.SIMPLE, pillar_style = PillarStyle.SIMPLE, standoff_pillars_separate=True, fixing_screws=None, embed_nuts_in_plate=True,
                 plaque = None, vanity_plate_radius=-1, prefer_tall = False, split_detailed_plate=False):
        self.symetrical = symetrical
        #if we've got the moon sticking out the top, can arrange the pillars in such a way that we'rea taller
        self.can_be_extra_tall = (moon_complication is not None) or prefer_tall
        if fixing_screws is None:
            fixing_screws = MachineScrew(4, countersunk=True)
        # enshake smaller because there's no weight dangling to warp the plates! (hopefully)
        #ended up having the escape wheel getting stuck, endshake larger again (errors from plate and pillar thickness printed with large layer heights?)
        super().__init__(going_train, motion_works, pendulum=None, gear_train_layout=GearTrainLayout.COMPACT, pendulum_at_top=True, plate_thick=plate_thick, back_plate_thick=back_plate_thick,
                         pendulum_sticks_out=pendulum_sticks_out, name=name, heavy=True, pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS,
                         pendulum_at_front=False, back_plate_from_wall=pendulum_sticks_out + 10 + plate_thick, fixing_screws=fixing_screws,
                         centred_second_hand=centred_second_hand, pillars_separate=True, dial=dial, bottom_pillars=2, moon_complication=moon_complication,
                         second_hand=second_hand, motion_works_angle_deg=motion_works_angle_deg, endshake=1.5, compact_zigzag=True, screws_from_back=screws_from_back,
                         layer_thick=layer_thick, escapement_on_front=escapement_on_front, style=style, pillar_style= pillar_style,
                         standoff_pillars_separate = standoff_pillars_separate, embed_nuts_in_plate=embed_nuts_in_plate, plaque = plaque, vanity_plate_radius=vanity_plate_radius,
                         split_detailed_plate=split_detailed_plate)
        self.narrow_bottom_pillar = False
        self.foot_fillet_r = 2
        # self.moon_holder_y = -1
        # self.moon_holder_wide = self.plate_width*1.5

        self.little_plate_for_pawl = False

        self.little_arm_to_motion_works = False

        if self.symetrical:
            self.little_arm_to_motion_works = True

        if self.dial is not None:
            #hacky, cut away a bit from the top support so it won't crash into the anchor rod


            self.dial.subtract_from_supports = cq.Workplane("XY")
            #cut out bits from the pillars so they don't clash with any of the rods
            for arbor in self.arbors_for_plate:
                bearing_relative_to_dial = np_to_set(np.subtract(arbor.bearing_position[:2], self.hands_position))
                tall = 5
                #mirror because the dial is printed upside down
                bearing_relative_to_dial = (-bearing_relative_to_dial[0], bearing_relative_to_dial[1])
                self.dial.subtract_from_supports = self.dial.subtract_from_supports.add(cq.Workplane("XY").moveTo(bearing_relative_to_dial[0], bearing_relative_to_dial[1])\
                    .circle(arbor.bearing.outer_safe_d / 2).extrude(tall).translate((0, 0, self.dial.thick + self.dial.support_length - tall)))

            if self.centred_second_hand or True:
                #I'm not sure why this was only for centred second hand, it makes a lot of sense for all mantel dials?
                pillar_positions = []
                for side in [0,1]:
                    #relocate the pillars holding the dial
                    line = Line(self.bottom_pillar_positions[side], anotherPoint=self.top_pillar_positions[side])
                    intersections = line.intersection_with_circle(self.hands_position, self.dial.outside_d/2 - self.dial.dial_width/2)
                    pillar_positions += intersections


                self.dial_fixing_positions = pillar_positions
                dial_fixing_positions = []

                for pos in pillar_positions:
                    pos_relative_to_hands = np_to_set(np.subtract(pos, self.hands_position))
                    # NOTE dial is "upside down" so invert x (not done consistently as most clocks are symmetric, so it goes unnoticed)
                    # single screw in each pillar ought to be enoguh, hence putting each element in its own list
                    dial_fixing_positions.append([(-pos_relative_to_hands[0], pos_relative_to_hands[1])])

                self.dial.override_fixing_positions(dial_fixing_positions)
                self.dial.support_d=15
                if self.style == PlateStyle.RAISED_EDGING:
                    self.dial.support_d = self.plate_width - self.edging_wide*2 - 1

    def get_moon_holder_info(self):
        if self.moon_complication is None:
            raise ValueError("there is no moon")
        if self.dial is None:
            raise NotImplementedError("TODO support moon holder without dial")
        #may want to extend upwards to hold the moon holder
        if self.hands_position[1] + self.dial.outside_d/2 > self.bearing_positions[-1][1] + self.plate_width/2:
            #dial is above top of plate
            y = self.hands_position[1] + self.dial.outside_d/2 - self.plate_width/2

            return {"y": y, "wide": self.plate_width*1.5, "height": self.plate_width}
        else:
            raise NotImplementedError("TODO moon support for larger plates that stick above dial")

    def get_plate_shape(self):
        return PlateShape.MANTEL

    def calc_pillar_info(self, override_bottom_pillar_r=-1):
        '''
        current plan: asymetric to be compact, with anchor arbor sticking out the top above the topmost pillar

        This is completely hard coded around a spring powered clock with 4 wheels and 2 powered wheels using the compact layout.
        if the spring clock is a success, it'll be worth making it more flexible
        '''

        bearingInfo = get_bearing_info(self.arbor_d)
        # TODO review this from old logic width of thin bit
        self.plate_width = bearingInfo.outer_d + self.bearing_wall_thick * 2
        self.min_plate_width = self.plate_width
        if self.heavy or self.extra_heavy:
            self.plate_width *= 1.2

        self.bottom_pillar_positions = []
        self.top_pillar_positions = []
        self.bottom_pillar_r = self.plate_width/2
        self.top_pillar_r = self.min_plate_width/2
        if self.pillar_style is not PillarStyle.SIMPLE:
            #I keep changing my mind over this
            self.top_pillar_r = self.bottom_pillar_r

        a = self.bearing_positions[self.going_train.powered_wheels + 1][:2]
        b = self.bearing_positions[self.going_train.powered_wheels + 2][:2]
        distance_to_a = self.arbors_for_plate[self.going_train.powered_wheels + 1].get_max_radius() + self.top_pillar_r + self.small_gear_gap
        distance_to_b = self.arbors_for_plate[self.going_train.powered_wheels + 2].get_max_radius() + self.top_pillar_r + self.small_gear_gap
        top_left = get_point_from_two_points(pos0=a, pos1=b, distance0=distance_to_a, distance1=distance_to_b)

        bottom_distance = self.arbors_for_plate[0].get_max_radius() + self.small_gear_gap + self.bottom_pillar_r
        #TODO check this doesn't collide with next wheel
        bottom_angle = -math.pi/4
        self.bottom_pillar_positions = [polar(math.pi - bottom_angle, bottom_distance), polar(bottom_angle, bottom_distance)]

        if top_left[0] < self.bottom_pillar_positions[0][0] and self.symetrical:
            if self.can_be_extra_tall:
                #raise the pillars upwards by rotating around the left-top gear until we're inline with the bottom pillar
                left_line = Line(self.bottom_pillar_positions[0], direction=(0,1))
                # from_gear = abs(self.bottom_pillar_positions[0] - self.bearing_positions[self.going_train.powered_wheels + 2][0])
                points = left_line.intersection_with_circle(b, distance_to_b)
                y = max([p[1] for p in points])
                top_left = [self.bottom_pillar_positions[0][0], y]
            else:
                #widen out the bottom pillars
                self.bottom_pillar_positions[0] = (top_left[0], self.bottom_pillar_positions[0][1])
                self.bottom_pillar_positions[1] = (-top_left[0], self.bottom_pillar_positions[0][1])

        right_pillar_line = Line(self.bottom_pillar_positions[1], anotherPoint=self.bearing_positions[1][:2])


        if self.symetrical:
            # y = self.bearing_positions[-2][1] + self.arbors_for_plate[self.going_train.powered_wheels + 1].get_max_radius() + self.gear_gap + self.top_pillar_r
            # self.top_pillar_positions = [
            #     (self.bottom_pillar_positions[0][0], y),
            #     (self.bottom_pillar_positions[1][0], y)
            # ]
            #probably only works when there's no second hand
            # top_left = np_to_set(np.add(self.bearing_positions[self.going_train.powered_wheels + 1][:2], np.multiply(polar(math.pi * 0.55), self.arbors_for_plate[self.going_train.powered_wheels + 1].get_max_radius() + self.gear_gap + self.top_pillar_r)))

            self.top_pillar_positions = [top_left, (-top_left[0], top_left[1])]


        else:
            self.top_pillar_positions = [
                # np_to_set(np.add(self.bearing_positions[self.going_train.powered_wheels + 1][:2], np.multiply(polar(math.pi * 0.525), self.arbors_for_plate[self.going_train.powered_wheels + 1].get_max_radius() + self.gear_gap + self.top_pillar_r))),
                top_left,
                np_to_set(np.add(self.bearing_positions[1][:2], np.multiply(right_pillar_line.dir, self.arbors_for_plate[1].get_max_radius() + self.small_gear_gap + self.top_pillar_r))),
            ]
        print("top pillar distance gap: ", np.linalg.norm(np.subtract(self.top_pillar_positions[1], self.bearing_positions[-1][:2])) - self.top_pillar_r - self.arbors_for_plate[-1].get_max_radius())

    def calc_fixing_info(self):
        # fixing positions to plates and pillars together
        self.plate_top_fixings = []
        # (self.top_pillar_positions[0] - self.top_pillar_r / 2, self.top_pillar_positions[1]), (self.top_pillar_positions[0] + self.top_pillar_r / 2, self.top_pillar_positions[1])]
        for top_pillar_pos in self.top_pillar_positions:
            self.plate_top_fixings.append((top_pillar_pos[0], top_pillar_pos[1]))


        self.plate_bottom_fixings = []
        for bottom_pillar_pos in self.bottom_pillar_positions:
            self.plate_bottom_fixings.append((bottom_pillar_pos[0], bottom_pillar_pos[1]))

        self.plate_fixings = self.plate_top_fixings + self.plate_bottom_fixings

    def get_plate(self, back=True, for_printing=True, just_basic_shape=False, thick_override=-1):

        plate_thick = self.get_plate_thick(back=back)
        if thick_override > 0:
            plate_thick = thick_override

        plate = cq.Workplane("XY")

        main_arm_wide = self.plate_width
        medium_arm_wide = get_bearing_info(3).outer_d + self.bearing_wall_thick * 2
        small_arm_wide = 8

        pillar_positions = self.top_pillar_positions + self.bottom_pillar_positions

        # for pillar in range(len(pillar_positions)):
        #     pillar_pos = pillar_positions[pillar]
        #     next_pillar_pos = pillar_positions[(pillar + 1)% len(pillar_positions)]
        #
        #link up the side pillars with each other
        for side in [0,1]:
            plate = plate.union(get_stroke_line([self.top_pillar_positions[side], self.bottom_pillar_positions[side]], wide=main_arm_wide, thick = plate_thick))
            plate = plate.union(get_stroke_line([self.bottom_pillar_positions[side], self.bearing_positions[0][:2]], wide=main_arm_wide, thick=plate_thick))

        # plate = plate.union(get_stroke_line([self.top_pillar_positions[side], self.bearing_positions[-2][:2]], wide=main_arm_wide, thick=plate_thick))
        if not back:
            #arch over the top
            #not for back because point holding the bearing that isn't there for the anchor arbor!
            if self.symetrical:
                plate = plate.union(get_stroke_line([self.top_pillar_positions[0], self.bearing_positions[-1][:2], self.top_pillar_positions[1]], wide=main_arm_wide, thick=plate_thick))
            else:
                plate = plate.union(get_stroke_line([self.bearing_positions[-2][:2], self.bearing_positions[-1][:2]], wide=main_arm_wide, thick=plate_thick))
                plate = plate.union(get_stroke_line([self.top_pillar_positions[0], self.bearing_positions[-1][:2]], wide=main_arm_wide, thick=plate_thick))
                plate = plate.union(get_stroke_line([self.top_pillar_positions[1], self.bearing_positions[-2][:2]], wide=main_arm_wide, thick=plate_thick))

        if back and not self.symetrical:
            #can't immediately remember what this is for
            plate = plate.union(get_stroke_line([self.top_pillar_positions[1],self.bearing_positions[-2][:2]], wide=main_arm_wide, thick=plate_thick))

        for foot_pos in self.bottom_pillar_positions:
            #give it little feet
            plate = plate.union(cq.Workplane("XY").rect(self.bottom_pillar_r*2, self.bottom_pillar_r).extrude(plate_thick).edges("|Z and <Y").fillet(self.foot_fillet_r)
                                .translate(foot_pos).translate((0,-self.bottom_pillar_r/2)))

        #barrel to minute wheel
        plate = plate.union(get_stroke_line([self.bearing_positions[0][:2], self.bearing_positions[self.going_train.powered_wheels][:2]], wide=medium_arm_wide, thick=plate_thick))

        #across the front of the plate
        plate = plate.union(get_stroke_line([self.bearing_positions[self.going_train.powered_wheels+1][:2], self.bearing_positions[1][:2]], wide=medium_arm_wide, thick=plate_thick))

        #idea - 3 thin arms all linking to the second hand arbor? medium from barrel to minute wheel, thick just for the edges
        links = [self.bearing_positions[self.going_train.powered_wheels][:2],
                 self.bearing_positions[self.going_train.powered_wheels+3][:2],
                 self.top_pillar_positions[0]
                 ]
        for link_pos in links:
            plate = plate.union(get_stroke_line([self.bearing_positions[self.going_train.powered_wheels + 2][:2], link_pos], wide=small_arm_wide, thick=plate_thick))

        if self.symetrical and self.no_upper_wheel_in_centre:
            links = [self.hands_position,
                     self.top_pillar_positions[1]
                     ]
            for link_pos in links:
                plate = plate.union(get_stroke_line([self.bearing_positions[-2][:2], link_pos], wide=small_arm_wide, thick=plate_thick))

        for i, pos in enumerate(self.bearing_positions):

            bearing_info = self.arbors_for_plate[i].bearing

            if not (i == len(self.bearing_positions)-1 and back):
                #only if not the back plate and the hole for the anchor arbor
                plate = plate.union(cq.Workplane("XY").circle(bearing_info.outer_d / 2 + self.bearing_wall_thick).extrude(plate_thick).translate(pos[:2]))

        plate = plate.union(cq.Workplane("XY").circle(self.going_train.powered_wheel.key_bearing.outer_d / 2 + self.bearing_wall_thick * 1.5).extrude(plate_thick))

        if not back and self.moon_complication is not None:
            #little arm that sticks off the top to hold the moon holder
            moon_holder_wide = self.get_moon_holder_info()["wide"]
            moon_holder_arm = get_stroke_line([self.bearing_positions[-1][:2], [0, self.hands_position[1] + self.dial.outside_d/2]],
                                                wide=moon_holder_wide, thick=plate_thick, style=StrokeStyle.SQUARE)
            moon_holder_arm = moon_holder_arm.intersect(cq.Workplane("XY").moveTo(self.hands_position[0], self.hands_position[1]).circle(self.dial.outside_d/2).extrude(plate_thick))
            moon_holder_arm = moon_holder_arm.edges("|Z").fillet(self.moon_holder.fillet_r)
            plate = plate.union(moon_holder_arm)

            for i,pos in enumerate(self.get_moon_complication_fixings_absolute()):
                plate = plate.union(cq.Workplane("XY").moveTo(pos[0], pos[1]).circle(self.moon_complication.arbor_d*2).extrude(plate_thick))
                if i == 1 and not self.moon_complication.on_left:
                    #the little arm on the right
                    plate = plate.union(get_stroke_line([pos, (self.bottom_pillar_positions[1][0], pos[1])], wide=small_arm_wide, thick=plate_thick))
                if not just_basic_shape:
                    plate = plate.cut(self.moon_complication.screws.get_cutter(with_bridging=True, layer_thick=self.layer_thick).translate(pos))



        if just_basic_shape:
            return plate

        if back:
            plate = plate.cut(self.get_fixing_screws_cutter())

            plate = self.rear_additions_to_plate(plate)



        else:
            plate = plate.cut(self.get_fixing_screws_cutter().translate((0, 0, -self.get_plate_thick(back=True) - self.plate_distance)))

        ratchet_screws_cutter = self.get_spring_ratchet_screws_cutter(back_plate=back)
        if ratchet_screws_cutter is not None:
            plate = plate.cut(ratchet_screws_cutter)

        if not back:
            #don't add the arms, we'll do that ourselves so they fit better with the style
            plate = self.front_additions_to_plate(plate, plate_thick, moon=False)

        plate = self.punch_bearing_holes(plate, back)



        if for_printing:
            plate = self.apply_style_to_plate(plate, back=back)

        return plate

    def get_text_spaces(self):
        '''
        default shapehas a short and long space for text, symmetric plates can have long on both
        '''
        # (x,y,width,height, horizontal)
        spaces = []


        if self.symetrical:
            texts = ["\n".join(self.texts[2:]), "\n".join(self.texts[:2])]
        else:
            texts = [" ".join(self.texts[1:]), self.texts[0]]

        #in line with the pillar, but length just to the bearing
        long_line = Line(self.bottom_pillar_positions[0], anotherPoint=self.top_pillar_positions[0])
        long_space_length = np.linalg.norm(np.subtract( self.bearing_positions[3][:2], self.bottom_pillar_positions[0]))
        long_line_length = long_space_length - self.top_pillar_r - self.bottom_pillar_r - 1
        text_height = self.plate_width * 0.9
        long_centre = np_to_set(np.add(long_line.start, np.multiply(long_line.dir, long_space_length / 2)))
        long_angle = long_line.get_angle()

        short_line = Line(self.bottom_pillar_positions[1], anotherPoint=self.top_pillar_positions[1])
        short_space_length = np.linalg.norm(np.subtract(self.bearing_positions[1][:2], self.bottom_pillar_positions[1]))
        if self.symetrical:
            # short_space_length = np.linalg.norm(np.subtract(self.top_pillar_positions[1], self.bottom_pillar_positions[1])) - self.top_pillar_r
            text_height = self.plate_width * 0.8
        short_line_length = short_space_length - 10
        short_centre = np_to_set(np.add(short_line.start, np.multiply(short_line.dir, short_space_length / 2)))
        short_angle = short_line.get_angle() + math.pi


        # three along the wide bit at the bottom and one above
        spaces.append(TextSpace(long_centre[0], long_centre[1], text_height,long_line_length, angle_rad=long_angle))
        spaces.append(TextSpace(short_centre[0], short_centre[1], text_height, short_line_length, angle_rad=short_angle))
        # spaces.append(TextSpace(bottom_pos[0], (bottom_pos[1] + (chain_pos[1] - chain_space)) / 2, text_height, chain_pos[1] - chain_space - bottom_pos[1], horizontal=False))
        # spaces.append(TextSpace(bottom_pos[0] + self.bottom_pillar_r - self.bottom_pillar_r / 3, (bottom_pos[1] + chain_pos[1]) / 2, text_height, chain_pos[1] - bottom_pos[1], horizontal=False))
        #
        # spaces.append(TextSpace(chain_pos[0], (first_arbour_pos[1] - arbour_space + chain_pos[1] + chain_space) / 2, self.plate_width * 0.9, first_arbour_pos[1] - arbour_space - (chain_pos[1] + chain_space), horizontal=False))

        for i, text in enumerate(texts):
            spaces[i].set_text(text)
        return spaces

    def calc_plaque_config(self):
        '''
        if this clock has a little plaque, calculate where it goes and what size it should be
        side effect: sets width and height on teh plaque itself (lazy but simple)

        will be similar to get_text_spaces, not sure how to abstract anything out to share code yet
        '''

        long_line = Line(self.bottom_pillar_positions[0], anotherPoint=self.top_pillar_positions[0])
        long_space_length = np.linalg.norm(np.subtract(self.bearing_positions[3][:2], self.bottom_pillar_positions[0]))
        long_line_length = long_space_length - self.top_pillar_r - self.bottom_pillar_r - 1
        text_height = self.plate_width * 0.9
        long_centre = np_to_set(np.add(long_line.start, np.multiply(long_line.dir, long_space_length / 2)))
        long_angle = long_line.get_angle()

        self.plaque.set_dimensions(long_line_length, self.bottom_pillar_r*2*0.9)

        self.plaque_pos = long_centre
        self.plaque_angle = long_angle


    def get_screwhole_positions(self):
        '''
        this doesn't hang on the wall, so no wall fixings
        '''
        return []

    def get_wall_standoff(self, top=True, for_printing=True):
        '''
        not really a wall standoff, but the bit that holds the pendulum at the top
        '''
        if not top:
            return None

        width = self.top_pillar_r*2

        plate_thick = self.get_plate_thick(standoff=True)
        #to match the plate
        standoff = get_stroke_line([self.top_pillar_positions[0], self.bearing_positions[-1][:2], self.top_pillar_positions[1]], wide=width, thick=plate_thick)
        clockwise = True

        if not self.standoff_pillars_separate:
            for pillar_pos in self.top_pillar_positions:
                if self.pillar_style != PillarStyle.SIMPLE:
                    standoff = standoff.union(fancy_pillar(self.top_pillar_r, self.back_plate_from_wall - plate_thick, clockwise=clockwise, style=self.pillar_style).translate(pillar_pos).translate((0, 0, plate_thick)))
                    clockwise = not clockwise
                else:
                    standoff = standoff.union(cq.Workplane("XY").circle(self.top_pillar_r-0.0001).extrude(self.back_plate_from_wall-plate_thick).translate((0,0,plate_thick)).translate(pillar_pos))
        standoff = self.cut_anchor_bearing_in_standoff(standoff)

        standoff = standoff.translate((0,0,-self.back_plate_from_wall))
        standoff = standoff.cut(self.get_fixing_screws_cutter())

        return standoff

    def get_mat(self):
        '''
        little mat to sit under the clock, felt backed to make it less loud
        returns array of objects if detail is involved
        '''
        rounded_r = 10

        extra_space = rounded_r*2 + self.edging_wide*2 + 10

        width = abs(self.bottom_pillar_positions[0][0] - self.bottom_pillar_positions[1][0]) + self.plate_width + extra_space
        length = self.plate_distance + self.get_plate_thick(True) + self.get_plate_thick(False) + extra_space
        thick = 4

        def get_mat_shape(mat_thick):
            return cq.Workplane("XY").rect(width,length).extrude(mat_thick).edges("|Z").fillet(rounded_r)

        mat = get_mat_shape(thick)

        #thicker mat because otherwise the shell won't work
        detail = self.get_plate_detail(back=False, for_this_shape=get_mat_shape(self.edging_wide*10)).translate((0,0,thick))
        # detail = None
        return [mat, detail]


    def get_bottom_pillar(self, flat=False):
        '''
        centred on 0,0 flat on the XY plane

        overriding default pillars to give ones with flat bottoms
        '''
        pillar = cq.Workplane("XY").moveTo(self.bottom_pillar_r,0).lineTo(self.bottom_pillar_r, -self.bottom_pillar_r + self.foot_fillet_r)\
            .radiusArc((self.bottom_pillar_r - self.foot_fillet_r, -self.bottom_pillar_r), self.foot_fillet_r).\
            lineTo(-self.bottom_pillar_r + self.foot_fillet_r, -self.bottom_pillar_r).radiusArc((-self.bottom_pillar_r, -self.bottom_pillar_r+self.foot_fillet_r), self.foot_fillet_r).\
            lineTo(-self.bottom_pillar_r, 0).radiusArc((self.bottom_pillar_r,0), self.bottom_pillar_r).close()



        if flat:
            return pillar


        if self.pillar_style != PillarStyle.SIMPLE:
            pillar = fancy_pillar(self.bottom_pillar_r, self.plate_distance, style=self.pillar_style)
        else:
            pillar = pillar.extrude(self.plate_distance)

        # hack - assume screws are in the same place for both pillars for now
        pillar = pillar.cut(self.get_fixing_screws_cutter().translate((-self.bottom_pillar_positions[0][0], -self.bottom_pillar_positions[0][1], -self.get_plate_thick(back=True))))


        return pillar

class RoundClockPlates(SimpleClockPlates):
    '''
    Plan for a traditional-ish movement shape on legs, so the pendulum will be visible below the dial.
    Inspired by some Brocot clocks I've seen

    Original plan was for a circular movement, but ended up with semicircular when adding legs, set fully_round True for fully round

    Only been designed to work well with springs so far - wouldn't be much work to support cord

    This was based on a copy of MantelClockPlates - I think it's going to be similar, but not similar enough to warrant extending or being a set of options
    '''
    def __init__(self, going_train, motion_works, plate_thick=8, back_plate_thick=None, pendulum_sticks_out=15, name="", centred_second_hand=False, dial=None,
                 moon_complication=None, second_hand=True, layer_thick=LAYER_THICK, escapement_on_front=False, vanity_plate_radius=-1, motion_works_angle_deg=-1,
                 leg_height=150, endshake=1.5, fully_round=False, style=PlateStyle.SIMPLE, pillar_style=PillarStyle.SIMPLE, standoff_pillars_separate=True, plaque=None,
                 front_anchor_holder_part_of_dial = False, split_detailed_plate=False):
        '''
        only want endshake of about 1.25, but it's really hard to push the bearings in all the way because they can't be reached with the clamp, so
        bumping up the default to 1.5
        '''
        self.leg_height = leg_height
        #review this later, but for now at least its a different variable
        self.wall_mounted = leg_height == 0
        self.fully_round = fully_round
        # enshake smaller because there's no weight dangling to warp the plates! (hopefully)
        #ended up having the escape wheel getting stuck, endshake larger again (errors from plate and pillar thickness printed with large layer heights?)
        #was force_escapement_above_hands because the gear train looks better on a circular plate that way ( now got forcing_escape_wheel_slightly_off_centre in bearing placement)
        super().__init__(going_train, motion_works, pendulum=None, gear_train_layout=GearTrainLayout.COMPACT, pendulum_at_top=True, plate_thick=plate_thick, back_plate_thick=back_plate_thick,
                         pendulum_sticks_out=pendulum_sticks_out, name=name, heavy=True, pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS,
                         pendulum_at_front=False, back_plate_from_wall=pendulum_sticks_out + 10 + plate_thick, fixing_screws=MachineScrew(4, countersunk=True),
                         centred_second_hand=centred_second_hand, pillars_separate=True, dial=dial, bottom_pillars=2, moon_complication=moon_complication,
                         second_hand=second_hand, motion_works_angle_deg=motion_works_angle_deg, endshake=endshake, compact_zigzag=True, screws_from_back=None,
                         layer_thick=layer_thick, escapement_on_front=escapement_on_front, vanity_plate_radius=vanity_plate_radius, force_escapement_above_hands=escapement_on_front, style=style,
                         pillar_style=pillar_style, standoff_pillars_separate=standoff_pillars_separate, plaque=plaque, split_detailed_plate=split_detailed_plate)

        if self.wall_mounted:
            #I liked the idea, but it just didn't print well being face-up, and I really want to print those standoffs that way to print the nut without bridging
            #so it's as strong as possible
            self.text_on_standoffs=False

        #overide whatever simple clock plates said, we don't need to worry for the round clock plates as the pillars are placed on the outer circle
        self.dial_top_above_front_plate = False

        #much more noticable on the round plate
        self.export_tolerance = 0.01
        self.narrow_bottom_pillar = False
        self.foot_fillet_r = 2
        self.little_arm_to_motion_works = True
        self.little_plate_for_pawl = False
        fixings = 3
        # self.vanity_plate_fixing_positions = [polar(angle, self.vanity_plate_radius-self.vanity_plate_pillar_r) for angle in [math.pi/6 + i*(math.pi*2/fixings) for i in range(fixings)]]
        #ended up using pillar positions instead
        self.vanity_plate_fixing_positions = []#[(-self.radius,self.hands_position[1]), (self.radius, self.hands_position[1])]
        self.vanity_plate_pillar_r=self.pillar_r

        #was an experiment, could still be useful
        self.front_anchor_holder_part_of_dial = front_anchor_holder_part_of_dial

        if self.front_anchor_holder_part_of_dial:
            #front anchor holder will have little arms extended from the front plate
            anchor_distance = distance_between_two_points(self.hands_position, self.bearing_positions[-1][:2])
            anchor_holder_arc_angle = math.pi * 0.3
        else:
            anchor_distance = self.radius
            anchor_holder_arc_angle = self.plate_width*2/self.radius
        self.anchor_holder_fixing_points = [np_to_set(np.add(self.hands_position, polar(math.pi/2 + i*anchor_holder_arc_angle/2, anchor_distance))) for i in [-1, 1]]


        # centre = self.bearing_positions[self.going_train.powered_wheels][:2]
        # self.radius = 1
        # for bearing_pos in self.bearing_positions:
        #     distance = distance_between_two_points(centre, bearing_pos[:2])
        #     if distance > self.radius:
        #         self.radius = distance
        '''
        TODO
        set ratchet and pawl angle here, rather than user config
        consider extra thick inside plate just to hold the screws for the ratchet? avoid the extra mini plate DONE
        
        '''

        if self.dial is not None and self.escapement_on_front and self.front_anchor_holder_part_of_dial:
            self.dial.add_to_back = self.get_front_anchor_bearing_holder().translate((-self.hands_position[0],-self.hands_position[1], self.dial.thick))


        if self.dial is not None:
            #TODO more general purpose support for different relative sizes of plates and dial and different pillar locations.
            #this works for now

            #not evenly space so we don't clash with pillars
            angles = [math.pi/2 + math.pi/8, math.pi/2 - math.pi/8, math.pi*1.5 + math.pi/8, math.pi*1.5 - math.pi/8]
            if self.gear_train_layout == GearTrainLayout.COMPACT and not self.escapement_on_front and self.no_upper_wheel_in_centre:
                #line up dial supports with the little arms
                for i in range(2):
                    bearing_relative_pos = np_to_set(np.subtract(self.bearing_positions[-3 + i][:2], self.hands_position))
                    bearing_angle = math.atan2(bearing_relative_pos[1], bearing_relative_pos[0])
                    angles[i] = bearing_angle

            dial_fixings_relative_to_dial = [polar(angle, self.radius) for angle in angles]

            self.dial_fixing_positions = [np_to_set(np.add(pos, self.hands_position)) for pos in dial_fixings_relative_to_dial]

            # array of arrays because we only want one screw per pillar here
            #invert x because dial is constructed upside down
            self.dial.override_fixing_positions([[(-pos[0], pos[1])] for pos in dial_fixings_relative_to_dial])
            self.dial.support_d = 15
            if self.style == PlateStyle.RAISED_EDGING:
                self.dial.support_d = self.plate_width - self.edging_wide * 2 - 1

        # self.front_anchor_holder_part_of_dial = True

    def get_moon_holder_info(self):
        if self.moon_complication is None:
            raise ValueError("there is no moon")
        if self.dial is None:
            raise NotImplementedError("TODO support moon holder without dial")
        #may want to extend upwards to hold the moon holder
        if self.hands_position[1] + self.dial.outside_d/2 > self.bearing_positions[-1][1] + self.plate_width/2:
            #dial is above top of plate

            centre_y = self.hands_position[1] + self.radius
            height = self.pillar_r * 2
            return {"y": centre_y, "wide": self.moon_complication.moon_radius*2, "height": height}
        else:
            raise NotImplementedError("TODO moon support for larger plates that stick above dial")

    def calc_plaque_config(self):
        '''
        if this clock has a little plaque, calculate where it goes and what size it should be
        side effect: sets width and height on teh plaque itself (lazy but simple)

        will be similar to get_text_spaces, not sure how to abstract anything out to share code yet

        this is copy pasted and tweaked from mantleclockplates - TODO think about how to abstract out the useful bits
        '''
        long_line = Line(self.hands_position, anotherPoint=self.bearing_positions[self.going_train.powered_wheels + 1][:2])
        long_space_length = self.radius
        long_line_length = long_space_length - self.plate_width
        text_height = self.plate_width * 0.9
        long_centre = np_to_set(np.add(long_line.start, np.multiply(long_line.dir, long_space_length / 2)))
        long_angle = long_line.get_angle()

        self.plaque.set_dimensions(long_line_length, text_height)

        self.plaque_pos = long_centre
        self.plaque_angle = long_angle

    def get_plate_shape(self):
        return PlateShape.ROUND

    def get_pillar(self, top=True, flat=False):
        '''
        they're all the same on this design!
        '''

        pillar_length = self.plate_distance

        if self.pillar_style is not PillarStyle.SIMPLE:
            pillar = (fancy_pillar(self.pillar_r, pillar_length, clockwise=top, style=self.pillar_style)
                      .cut(cq.Workplane("XY").circle(self.fixing_screws.get_rod_cutter_r(layer_thick=self.layer_thick, loose=True)).extrude(pillar_length)))
        else:
            pillar = cq.Workplane("XY").circle(self.pillar_r).circle(self.fixing_screws.get_rod_cutter_r(layer_thick=self.layer_thick, loose=True)).extrude(pillar_length)

        return pillar

    def get_legs_pillar(self):

        pillar_length = self.get_plate_thick(back=True) + self.get_plate_thick(back=False) + self.plate_distance

        pillar = cq.Workplane("XY").circle(self.pillar_r).extrude(pillar_length)
        pillar = pillar.union(cq.Workplane("XY").moveTo(0, -(self.pillar_r + self.foot_fillet_r)/2).rect(self.pillar_r*2, self.pillar_r + self.foot_fillet_r).extrude(pillar_length).edges("|Z and <Y").fillet(self.foot_fillet_r))

        pillar = pillar.faces(">Z").workplane().circle(self.fixing_screws.get_rod_cutter_r(layer_thick=self.layer_thick, loose=True)).cutThruAll()

        return pillar


    def calc_pillar_info(self, override_bottom_pillar_r=-1):
        '''
        All pillars on this clock will be identical, with no real meanign behind top and bottom pillar, but to fit in with the other plate designs they'll still
        be divided into top and bottom pillars

        currently assumes spring powered with two powered wheels, TODO make more robust
        '''

        # can make it big enough to fully encompass everything, but we still barely have space for a bottom right pillar and then its' just lots of empty space
        # so instead, make it big enough to hold the barrel and I'll poke a bit out the top for the anchor, and just skip the bottom right pillar entirely
        # worth a shot, anyway
        #



        bearingInfo = get_bearing_info(self.arbor_d)
        self.plate_width = bearingInfo.outer_d + self.bearing_wall_thick * 2
        self.min_plate_width = self.plate_width
        barrel_distance = distance_between_two_points(self.bearing_positions[self.going_train.powered_wheels][:2], self.bearing_positions[0][:2])

        # used in base class
        self.pillar_r = self.plate_width / 2
        # various shared bits expect these
        self.top_pillar_r = self.pillar_r
        self.bottom_pillar_r = self.pillar_r

        # self.radius = (self.arbors_for_plate[0].get_max_radius() + self.pillar_r + 3)
        self.bottom_pillar_distance = (self.arbors_for_plate[0].get_max_radius() + self.pillar_r + 3)*2
        self.radius = self.bottom_pillar_distance/2



        # self.radius = barrel_distance + self.arbors_for_plate[0].bearing.outer_d/2 + self.bearing_wall_thick - self.plate_width/2





        centre = self.bearing_positions[self.going_train.powered_wheels][:2]
        # lines_to_bearings = [Line(centre, anotherPoint=bearing_pos[:2]) for bearing_pos in self.bearing_positions]
        #
        # barrel_angle = self.arbors_for_plate[0].get_max_radius()/self.radius
        # pillar_angle = (self.pillar_r*2) / self.radius
        #
        # # #put the bottom pillar as close as we can (ish cba to calculate this exactly) to the barrel wheel
        # # bottom_pillar_angle = math.pi*1.5 - barrel_angle - pillar_angle*0.75
        # #above the second powered wheel
        # second_pillar_angle = lines_to_bearings[1].get_angle() * 0.5 + lines_to_bearings[5].get_angle() * 0.5

        #find where wheels 3 and 4 meet, then put the pillar in that direction
        points = get_circle_intersections(self.bearing_positions[3][:2], self.arbors_for_plate[3].get_max_radius(),
                                          self.bearing_positions[4][:2], self.arbors_for_plate[4].get_max_radius())
        #find furthest point
        if distance_between_two_points(points[0], centre) > distance_between_two_points(points[1], centre):
            point = points[0]
        else:
            point = points[1]
        line_to_point = Line(centre, anotherPoint=point)

        self.bottom_arm_wide = self.arbors_for_plate[0].bearing.outer_d + self.bearing_wall_thick*2


        barrel_pos = self.bearing_positions[0]

        y = barrel_pos[1] - self.bottom_arm_wide/2 + self.pillar_r
        pillar_distance = self.radius

        if self.fully_round:
            #pillars inline with the powered wheel
            y = barrel_pos[1]
            pillar_distance = self.bottom_pillar_distance/2

            if not self.going_train.powered_wheels > 1:
                raise ValueError("TODO calculate pillar positions for non eight day spring clocks")
            #assuming spring driven here
            b = self.arbors_for_plate[0].get_max_radius() + self.pillar_r + 1
            a = self.arbors_for_plate[0].arbor.distance_to_next_arbour
            c = self.arbors_for_plate[1].get_max_radius() + self.pillar_r + 1
            # cosine law
            angle = math.acos((a ** 2 + b ** 2 - c ** 2) / (2 * a * b))
            second_wheel_from_first = np_to_set(np.subtract(self.bearing_positions[1][:2], self.bearing_positions[0][:2]))
            second_wheel_from_first_angle = math.atan2(second_wheel_from_first[1], second_wheel_from_first[0])
            final_angle = second_wheel_from_first_angle - angle
            bottom_pillar_pos = np_to_set(np.add(self.bearing_positions[0][:2], polar(final_angle, b)))
            self.radius = distance_between_two_points(bottom_pillar_pos, self.bearing_positions[self.going_train.powered_wheels][:2])
            self.bottom_pillar_positions = [
                bottom_pillar_pos,
                (-bottom_pillar_pos[0], bottom_pillar_pos[1]),
            ]
        else:

            self.bottom_pillar_positions = [
                (barrel_pos[0] - pillar_distance, y),
                (barrel_pos[0] + pillar_distance, y),
            ]



        #just above second power wheel
        # right_pillar_pos = np_to_set(np.add(centre, polar(second_pillar_angle, self.radius)))

        left_pillar_pos = np_to_set(np.add(centre, polar(line_to_point.get_angle(), self.radius)))
        if self.going_train.wheels == 3:
            #mirror the bottom pillars
            bottom_y_from_centre = self.bearing_positions[self.going_train.powered_wheels][1] - self.bottom_pillar_positions[0][1]
            left_pillar_pos = (-self.bottom_pillar_positions[0][0], bottom_y_from_centre + self.bearing_positions[self.going_train.powered_wheels][1])

        #no real need to treat pillars differently, but the base class does so it makes some of the other logic easier
        self.top_pillar_positions = [
            #top two first because the anchor arbor holder assumes two top pillars
            #just above (ish) the second power wheel
            # try making them symetric instead
            (-left_pillar_pos[0], left_pillar_pos[1]),
            left_pillar_pos,


            # np_to_set(np.add(centre, polar(bottom_pillar_angle, self.radius))),
        ]


        self.all_pillar_positions = self.bottom_pillar_positions + self.top_pillar_positions
        if self.wall_mounted:
            self.leg_pillar_positions = []
        else:
            self.leg_pillar_positions = [np_to_set(np.add((0, -self.leg_height), pillar)) for pillar in self.bottom_pillar_positions]

    def get_fixing_screws_cutter(self):
        '''
        much more simple on this clock
        '''
        cutter = cq.Workplane("XY")

        # bottom_total_length = self.back_plate_from_wall + self.get_plate_thick(back=True) + self.plate_distance + self.get_plate_thick(back=False)
        # top_total_length = bottom_total_length + self.get_front_anchor_bearing_holder_total_length()
        bottom_total_length = top_total_length = 1000
        for pillar in self.all_pillar_positions:
            pillar_cutter = cq.Workplane("XY").circle(self.fixing_screws.get_rod_cutter_r(layer_thick=self.layer_thick, loose=True)).extrude(top_total_length).translate(pillar).translate((0,0,-top_total_length/2))
            cutter = cutter.add(pillar_cutter)

        # for screw_pos in self.anchor_holder_fixing_points:
        #     #these are symetric so don't need to worry much about mixing up which side they're on
        #     cutter = cutter.add(self.fi)

        if self.wall_mounted:
            #TODO make this more properly configurable for all plates, but for now we're using threaded rod rather than screws so we can attach the dial
            #and have shiny brass dome nuts on the front
            # bottom_nut_base_z, top_nut_base_z, bottom_nut_hole_height, top_nut_hole_height = self.get_fixing_screw_nut_info()
            top_nut_base_z = - self.back_plate_from_wall
            #THOUGHT: this might be thin enough that the standoff pillars could be seperate
            top_nut_hole_height = self.fixing_screws.get_nut_height() + 1
            #if the pillars are separate we can print this upside down, no briding needed for nuts
            bridging = not self.standoff_pillars_separate
            for pos in self.all_pillar_positions:
                cutter = cutter.add(self.fixing_screws.get_nut_cutter(height=top_nut_hole_height, with_bridging=bridging, rod_loose=True).translate((pos[0], pos[1], top_nut_base_z)))

        return cutter

    def calc_fixing_info(self):
        #not sure if we actually need this in this class
        self.plate_top_fixings = self.top_pillar_positions[:]
        self.plate_bottom_fixings = self.bottom_pillar_positions[:]
        self.plate_fixings = self.all_pillar_positions[:]

    def get_vanity_plate(self, for_printing=True):

        centre_hole_r = self.motion_works.get_widest_radius() + 2

        plate = cq.Workplane("XY").circle(self.vanity_plate_radius).circle(centre_hole_r).extrude(self.vanity_plate_thick)

        # for pillar_pos in self.vanity_plate_fixing_positions:
        #     #invert x because we're upside down
        #     plate = plate.union(cq.Workplane("XY").moveTo(-pillar_pos[0] - self.hands_position[0], pillar_pos[1] - self.hands_position[1]).circle(self.vanity_plate_pillar_r).extrude(self.vanity_plate_base_z + self.vanity_plate_thick))
        #     plate = plate.faces(">Z").workplane().moveTo(-pillar_pos[0] - self.hands_position[0], pillar_pos[1] - self.hands_position[1]).circle(self.fixing_screws.get_rod_cutter_r(loose=True)).cutThruAll()

        hole_r = self.fixing_screws.get_rod_cutter_r(loose=True)
        #removing the front legs
        pillar_height = self.vanity_plate_base_z - self.plate_thick

        for pillar_pos in self.bottom_pillar_positions:
            pillar_pos = np_to_set(np.subtract(pillar_pos, self.hands_position))
            plate = plate.union(get_stroke_line([self.hands_position, pillar_pos], wide=self.pillar_r*2, thick=self.vanity_plate_thick))
            plate = plate.union(cq.Workplane("XY").circle(self.pillar_r).circle(hole_r).extrude(pillar_height + self.vanity_plate_thick).translate(pillar_pos))
            plate = plate.faces(">Z").workplane().moveTo(pillar_pos[0], pillar_pos[1]).circle(hole_r).cutThruAll()

        if self.escapement_on_front:
            #gaps for the front anchor holder
            for pos in self.anchor_holder_fixing_points:
                relative_pos = np_to_set(np.subtract(pos, self.hands_position))
                plate = plate.cut(cq.Workplane("XY").moveTo(relative_pos[0], relative_pos[1]).circle(self.pillar_r + 1).extrude(self.vanity_plate_thick))

        #key hole
        key_hole_d = self.winding_key.get_key_outer_diameter() + 4
        key_hole_pos = np_to_set(np.subtract(self.bearing_positions[0][:2], self.hands_position))
        plate = plate.faces(">Z").workplane().moveTo(key_hole_pos[0], key_hole_pos[1]).circle(key_hole_d/2).cutThruAll()

        #hole for escape wheel
        if self.escapement_on_front:
            escapement_hole_pos = np_to_set(np.subtract(self.bearing_positions[-2][:2], self.hands_position))
            anchor_pos = np_to_set(np.subtract(self.bearing_positions[-1][:2], self.hands_position))

            #bit hacky, just assuming we know the diameters
            plate = plate.faces(">Z").workplane().moveTo(escapement_hole_pos[0], escapement_hole_pos[1]).circle(self.arbors_for_plate[-2].arbor_d*2 + 1).cutThruAll()

            anchor_hole_d = self.arbors_for_plate[-1].direct_arbor_d + 2

            #slot rather than hole so it should always be possible to assemble the clock
            plate = plate.cut(get_stroke_line([anchor_pos, (anchor_pos[0], anchor_pos[1]+100)], wide=anchor_hole_d, thick=self.vanity_plate_thick))

        if not for_printing:
            # return cq.Workplane("XY").circle(100).extrude(10)
            plate = plate.rotate((0,0,0), (0,1,0), 180)
            plate = plate.translate((0,0,self.vanity_plate_base_z + self.vanity_plate_thick))

        return plate

    def get_plate(self, back=True, for_printing=True, just_basic_shape=False, thick_override=-1):

        plate_thick = self.get_plate_thick(back=back)
        if thick_override > 0:
            plate_thick = thick_override

        centre = self.bearing_positions[self.going_train.powered_wheels][:2]

        main_arm_wide = self.plate_width
        medium_arm_wide = get_bearing_info(3).outer_d + self.bearing_wall_thick * 2
        # small_arm_wide = get_bearing_info(2).outer_d + self.bearing_wall_thick * 2
        small_arm_wide = get_bearing_info(3).outer_d + self.bearing_wall_thick * 2 - 1

        # plate = cq.Workplane("XY").moveTo(self.hands_position[0], self.hands_position[1]).circle(self.radius+main_arm_wide/2).circle(self.radius-main_arm_wide/2).extrude(plate_thick)

        if self.fully_round:
            plate = cq.Workplane("XY").circle(self.radius + main_arm_wide/2).circle(self.radius - main_arm_wide/2).extrude(plate_thick).translate(self.hands_position)

            #if there is only going to be a tiny gap under the arm, just make the whole bit solid
            extra_width_at_bottom = 0
            bottom_of_arm_y = self.bearing_positions[0][1] - self.bottom_arm_wide/2
            top_of_circle_y = self.hands_position[1] - self.radius + main_arm_wide/2
            if bottom_of_arm_y - top_of_circle_y < 4:
                extra_width_at_bottom=5

            bottom_arm = cq.Workplane("XY").rect(self.radius * 2, self.bottom_arm_wide + extra_width_at_bottom).extrude(plate_thick).translate(self.bearing_positions[0][:2]).translate((0,-extra_width_at_bottom))
            plate = plate.union(bottom_arm.intersect(cq.Workplane("XY").circle(self.radius + main_arm_wide/2).extrude(plate_thick).translate(self.hands_position)))
        else:
            #semicircular with rectangle on the bottom
            plate = get_stroke_arc((self.radius,centre[1]), (-self.radius,centre[1]), self.radius, main_arm_wide, plate_thick)

            plate = plate.union(get_stroke_line([(self.radius,centre[1]), self.bottom_pillar_positions[1], self.bottom_pillar_positions[0], [-self.radius,centre[1]]], thick=plate_thick, wide=medium_arm_wide))

            #beef up bottom arm
            plate = plate.union(cq.Workplane("XY").rect(self.radius*2, self.bottom_arm_wide).extrude(plate_thick).translate(self.bearing_positions[0][:2]))

        #vertical link
        # plate = plate.union(cq.Workplane("XY").rect(medium_arm_wide, self.radius*2).extrude(plate_thick))
        line_wide = medium_arm_wide

        for i, bearing_pos in enumerate(self.bearing_positions):
            if i == self.going_train.powered_wheels:
                #the minute wheel, in the centre
                continue
            if i > self.going_train.powered_wheels:
                line_wide = small_arm_wide

            if distance_between_two_points(centre, bearing_pos[:2]) - self.arbors_for_plate[i].bearing.outer_d/2 > self.radius - self.pillar_r:
                #this bearing will be in the outer circle
                continue

            if back and i == len(self.bearing_positions) - 1 and self.no_upper_wheel_in_centre:
                #don't need a bit of plate to support just a hole for the anchor
                continue

            line = Line(centre, anotherPoint=bearing_pos[:2])
            end = np_to_set(np.add(polar(line.get_angle(), self.radius), centre))

            bearing_in_plate_space = self.plate_width - self.arbors_for_plate[i].bearing.outer_d
            bearing_from_radius = abs(distance_between_two_points(bearing_pos[:2], centre) - self.radius)

            if i == len(self.bearing_positions) - 1 and not back and not self.escapement_on_front and bearing_from_radius > bearing_in_plate_space:
                #the anchor needs something to support it on the front plate
                line = Line(centre, anotherPoint=bearing_pos[:2])
                end = tuple(np.add(centre, np.multiply(line.dir, self.radius)))

            plate = plate.union(get_stroke_line([centre, end], line_wide, plate_thick))




        if just_basic_shape:

            try:
                #done in punch_bearing holes, but repeated here for the detailing
                outer_d = self.going_train.powered_wheel.key_bearing.outer_d
                plate = plate.union(cq.Workplane("XY").moveTo(self.bearing_positions[0][0], self.bearing_positions[0][1]).circle(outer_d / 2 + self.bearing_wall_thick).extrude(plate_thick))
            except:
                '''
                not a key-wound clock
                '''
            plate = self.add_motion_works_arm(plate, plate_thick, cut_holes=False)
            return plate

        plate = plate.cut(self.get_fixing_screws_cutter())
        if back:

            plate = self.rear_additions_to_plate(plate)

        else:
            if self.need_front_anchor_bearing_holder():

                for pos in self.anchor_holder_fixing_points:
                    if self.front_anchor_holder_part_of_dial:
                        # if not part of dial it should be alined with radius and not need any extensions
                        # TODO review this
                        line = Line(centre, anotherPoint=pos)
                        start = np_to_set(np.add(centre, polar(line.get_angle(), self.radius)))
                        plate = plate.union(get_stroke_line([start, pos], wide=self.pillar_r*2, thick=plate_thick))
                    plate = plate.cut(self.small_fixing_screws.get_cutter().translate(pos))

            plate = self.front_additions_to_plate(plate, moon=True)


        plate = self.punch_bearing_holes(plate, back)

        ratchet_screws_cutter = self.get_spring_ratchet_screws_cutter(back_plate=back)
        if ratchet_screws_cutter is not None:
            plate = plate.cut(ratchet_screws_cutter)

        # if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL and self.going_train.powered_wheel.ratchet_at_back == back:
        #
        #     #think this was so we flip the front plate if the ratchet was at the front?
        #     if for_printing and not back:
        #         plate = plate.rotate((0,0,0),(0,1,0),180).translate((0,0,plate_thick))


        return plate

    def get_legs(self, back=True):
        '''

        '''
        thick = self.plate_thick
        width = self.pillar_r*2
        legs = get_stroke_line([self.bottom_pillar_positions[0], self.leg_pillar_positions[0], self.leg_pillar_positions[1], self.bottom_pillar_positions[1]], wide=width, thick=thick)

        for pos in self.leg_pillar_positions:
            legs = legs.union(cq.Workplane("XY").moveTo(pos[0], pos[1]).rect(width,width+self.foot_fillet_r*2).extrude(thick).edges("|Z and <Y").fillet(self.foot_fillet_r))

        legs = legs.cut(self.get_fixing_screws_cutter())

        for pillar_pos in self.leg_pillar_positions:
            if back:
                legs = legs.faces(">Z").workplane().moveTo(pillar_pos[0], pillar_pos[1]).circle(self.fixing_screws.get_rod_cutter_r(loose=True)).cutThruAll()
            else:
                legs = legs.cut(self.fixing_screws.get_cutter(loose=True).rotate((0,0,0),(0,1,0),180).translate((pillar_pos[0], pillar_pos[1],thick)))



        return legs

    def get_text_spaces(self):
        spaces = []
        texts = self.texts
        if not self.wall_mounted:
            # (x,y,width,height, horizontal)


            texts = ["{}\n{}".format(self.texts[0], self.texts[1]), "{}\n{}".format(self.texts[2], self.texts[3])]

            y_offset = 0
            if self.leg_height > 0:
                # shift up to avoid join with legs
                y_offset = self.pillar_r - abs(self.bearing_positions[0][1] - self.bottom_pillar_positions[0][1])

            text_centre_y = average_of_two_points(self.bearing_positions[0][:2], self.bearing_positions[self.going_train.powered_wheels][:2])[1] + y_offset/2
            text_length = distance_between_two_points(self.bearing_positions[0][:2], self.bearing_positions[self.going_train.powered_wheels][:2]) - y_offset

            spaces.append(TextSpace(-self.radius, text_centre_y, self.plate_width*0.9, text_length, angle_rad=math.pi/2))
            spaces.append(TextSpace(self.radius, text_centre_y, self.plate_width*0.9, text_length, angle_rad=math.pi/2))

        else:
            if self.text_on_standoffs:
                top_width = math.fabs(self.top_pillar_positions[0][0]) - self.fixing_screws.get_nut_containing_diameter()/2 - self.wall_fixing_screw_head_d/2 - 1

                spaces.append(TextSpace(self.top_pillar_positions[0][0] / 2, self.top_pillar_positions[0][1], top_width, self.pillar_r * 1.8, horizontal=True))
                spaces.append(TextSpace(self.top_pillar_positions[1][0] / 2, self.top_pillar_positions[1][1], top_width, self.pillar_r * 1.8, horizontal=True))

                bottom_width = math.fabs(self.bottom_pillar_positions[0][0]) - self.fixing_screws.get_nut_containing_diameter()/2 - self.wall_fixing_screw_head_d/2 - 1

                spaces.append(TextSpace(self.bottom_pillar_positions[0][0] / 2, self.bottom_pillar_positions[0][1], bottom_width, self.pillar_r * 1.8, horizontal=True))
                spaces.append(TextSpace(self.bottom_pillar_positions[1][0] / 2, self.bottom_pillar_positions[1][1], bottom_width, self.pillar_r * 1.8, horizontal=True))
            else:
                height = self.bottom_arm_wide*0.5
                top_y = self.bearing_positions[0][1] + self.bottom_arm_wide/4
                bottom_y = self.bearing_positions[0][1] - self.bottom_arm_wide / 4

                #start the lines at x=0 and remember the intersection with circle only does intersections from the origin on the line
                top_line = Line((0, top_y),direction=(1,0))
                bottom_line = Line((0, bottom_y), direction=(1, 0))
                #making wider than needed as I'm not sure what's going on with the text spacing
                top_end_x = top_line.intersection_with_circle(self.hands_position, self.radius + self.plate_width/2)[0][0]
                bottom_end_x = bottom_line.intersection_with_circle(self.hands_position, self.radius + self.plate_width/2)[0][0]

                #keep away from the potential ratchet or bearing
                start_x = self.bottom_arm_wide*0.3

                spaces.append(TextSpace(start_x / 2 + top_end_x / 2, top_y, top_end_x / 2 - start_x / 2, height, horizontal=True))
                spaces.append(TextSpace(start_x / 2 + bottom_end_x / 2, bottom_y, bottom_end_x / 2 - start_x / 2, height, horizontal=True))

                spaces.append(TextSpace(-start_x / 2 -top_end_x / 2, top_y, top_end_x / 2 - start_x / 2, height, horizontal=True))
                spaces.append(TextSpace(-start_x / 2 -bottom_end_x / 2, bottom_y, bottom_end_x / 2 - start_x / 2, height, horizontal=True))

        for i, text in enumerate(texts):
            spaces[i].set_text(text)
        return spaces

    def get_screwhole_positions(self):
        '''
        returns [(x,y, supported),]
        '''
        if not self.wall_mounted:
            return []

        top_y = self.hands_position[1] + self.radius
        #HACK TODO tidy up screwhole cutting and calculate size in the same place (use newish WoodScrew?)
        screwhole_length =  self.wall_fixing_screw_head_d/2 + 7# + 6/2
        if top_y - self.bearing_positions[-1][1] < self.arbors_for_plate[-1].bearing.outer_d/2 + screwhole_length + 1:
            top_y = self.bearing_positions[-1][1] + self.arbors_for_plate[-1].bearing.outer_d/2 + screwhole_length + 1

        # if self.bearing_positions[-1][1] - self.top_pillar_positions[0][1] < 20:
        #     #bearing position is sufficiently above the pillars
        #     top_y = self.top_pillar_positions[0][1]
        # else:
        #     #halway between top pillar y and anchor bearing
        #     top_y = (self.bearing_positions[-1][1] + self.top_pillar_positions[0][1]) / 2

        return [(0, top_y, True), (0, self.bottom_pillar_positions[0][1], True)]

    def get_front_anchor_bearing_holder(self, for_printing=True):
        '''
        Sufficiently different fron back holder to be a different function.
        This will be printed as part of the dial and it must be possible to attach after the rest of teh clock
        has been assembled (including the vanity plate). Otherwise I think it will
        be impossible to assemble the clock


        note assumes that anchor_holder_fixing_points are symetric
        '''
        holder = cq.Workplane("XY")


        holder_wide = self.pillar_r * 2
        if self.style == PlateStyle.RAISED_EDGING:
            holder_wide = self.plate_width - self.edging_wide*2


        anchor_distance = distance_between_two_points(self.hands_position, self.bearing_positions[-1][:2])
        anchor_holder_fixing_points = self.anchor_holder_fixing_points

        holder_thick = self.get_lone_anchor_bearing_holder_thick(self.arbors_for_plate[-1].bearing)

        top_z = self.get_front_anchor_bearing_holder_total_length()
        if self.dial is not None and self.front_anchor_holder_part_of_dial:
            #if a dial, butt up exactly to the bottom of the dial so the two peices can be combined
            if self.dial_z > top_z:
                need_extra = self.dial_z - top_z
                top_z = self.dial_z
                holder_thick += need_extra
            else:
                raise ValueError("Dial isn't far enough away to fit front anchor holder. Extend motion works extra_height by at least {}mm".format(top_z - self.dial_z))

        

        holder = get_stroke_arc(self.anchor_holder_fixing_points[0], self.anchor_holder_fixing_points[1], anchor_distance, holder_wide, holder_thick)
        if not self.front_anchor_holder_part_of_dial:
            #line to the bearing
            bearing_holder_wide = self.arbors_for_plate[-1].bearing.outer_d + 4
            holder = holder.union(get_stroke_line([self.bearing_positions[-1][:2], (0, self.radius + self.hands_position[1])], wide = bearing_holder_wide,
                                                  thick=holder_thick, style=StrokeStyle.SQUARE))
            holder = holder.union(cq.Workplane("XY").moveTo(self.bearing_positions[-1][0], self.bearing_positions[-1][1]).circle(bearing_holder_wide/2).extrude(holder_thick))

        holder = holder.cut(self.get_bearing_punch(holder_thick, bearing=get_bearing_info(self.arbors_for_plate[-1].arbor.arbor_d)).translate((self.bearing_positions[-1][0], self.bearing_positions[-1][1])))
        
        # TODO NUTS - embedded or try slot in from the side?
        for pos in self.anchor_holder_fixing_points:
            #don't need to take into account holder thick because wer're unioning with it
            holder = holder.union(cq.Workplane("XY").circle(holder_wide/2).extrude(top_z).translate(pos))
            holder = holder.faces(">Z").workplane().moveTo(pos[0], pos[1]).circle(self.small_fixing_screws.get_rod_cutter_r(loose=True)).cutThruAll()
            nut_hole_deep = self.small_fixing_screws.get_nut_height()+1
            holder = holder.cut(self.small_fixing_screws.get_nut_cutter(height=nut_hole_deep, with_bridging=True, layer_thick=self.layer_thick).translate((pos[0], pos[1], top_z/2 - nut_hole_deep/2)))

        if not for_printing:

            holder = holder.rotate((0,0,0), (0,1,0),180).translate((0,0,self.get_plate_thick(True) + self.get_plate_thick(False) + self.plate_distance + top_z))

        return holder

    def get_wall_standoff(self, top=True, for_printing=True):
        if not top:
            if self.wall_mounted:
                return self.get_bottom_wall_standoff(for_printing=for_printing)
            else:
                return cq.Workplane("XY")
        return self.get_back_cock(for_printing=for_printing)


    def get_bottom_wall_standoff(self, for_printing=True):
        plate_thick = self.get_plate_thick(standoff=True)

        standoff = get_stroke_line(self.bottom_pillar_positions, wide=self.pillar_r*2, thick = plate_thick)

        wall_fixing_pos = self.get_screwhole_positions()[1][:2]#(0, self.bottom_pillar_positions[0][1])

        #filled in semicircle. I think it might be overkill:
        # standoff = get_stroke_arc(self.bottom_pillar_positions[0], self.bottom_pillar_positions[1], self.radius, wide=self.pillar_r*2, thick=plate_thick, fill_in=self.wall_mounted)
        #
        # # sagitta (copypasted from get_stroke_arc)
        # l = distance_between_two_points(self.bottom_pillar_positions[1], self.bottom_pillar_positions[0])
        # s = self.radius - math.sqrt(self.radius ** 2 - 0.25 * l ** 2)
        # wall_fixing_pos = (0, self.bottom_pillar_positions[0][1] - s / 2)

        standoff = self.cut_wall_fixing_hole(standoff, wall_fixing_pos, screw_head_d=self.wall_fixing_screw_head_d, add_extra_support=True, plate_thick=plate_thick)

        if not self.standoff_pillars_separate:
            standoff = standoff.union(self.get_standoff_pillars(top=False).translate((0,0,self.back_plate_from_wall)))



        standoff = standoff.translate((0, 0, -self.back_plate_from_wall))
        if self.text_on_standoffs:
            standoff = standoff.cut(self.get_text(top_standoff=False))
        standoff = standoff.cut(self.get_fixing_screws_cutter())

        # if for_printing and self.standoff_pillars_separate:
        #     standoff = standoff.rotate((0,0,0),(1,0,0),180)

        return standoff
    def get_back_cock(self, for_printing=True):
        '''
        the bit that holds the pendulum at the top
        '''


        width = self.pillar_r*2

        anchor_distance = distance_between_two_points(self.hands_position, self.bearing_positions[-1][:2])


        anchor_holder_fixing_points = self.top_pillar_positions

        # curve_ends = []
        # for fixing_pos in anchor_holder_fixing_points:
        #     line_up = Line(fixing_pos, direction=(0,1))
        #     curve_ends += line_up.intersection_with_circle(circle_centre=self.hands_position, circle_r = anchor_distance)

        # curve_ends = [np_to_set(np.add(self.hands_position, polar(math.pi/2 + i*self.anchor_holder_arc_angle/2, anchor_distance))) for i in [-1, 1]]

        plate_thick = self.get_plate_thick(standoff=True)
        #
        # standoff = get_stroke_line([anchor_holder_fixing_points[0], curve_ends[0]], wide=width, thick=plate_thick)
        # standoff = standoff.union(get_stroke_line([anchor_holder_fixing_points[1], curve_ends[1]], wide=width, thick=plate_thick))
        # standoff = standoff.union(get_stroke_arc(curve_ends[0], curve_ends[1], anchor_distance, wide=width, thick=plate_thick))

        #using sagitta to work out radius of curve that links all points
        l = distance_between_two_points(anchor_holder_fixing_points[0], anchor_holder_fixing_points[1])
        s = abs(anchor_holder_fixing_points[0][1] - self.bearing_positions[-1][1])
        r_anchor_bearing = s/2 + (l**2)/(8*s)

        standoff = get_stroke_arc(anchor_holder_fixing_points[0], anchor_holder_fixing_points[1], r_anchor_bearing, wide=width, thick=plate_thick)#, fill_in=self.wall_mounted)


        if self.wall_mounted:
            # standoff = standoff.union(get_stroke_line(anchor_holder_fixing_points, width, plate_thick))
            # standoff = standoff.union(get_stroke_line([self.bearing_positions[-1][:2], (0, anchor_holder_fixing_points[0][1])], width*1.5, plate_thick, style=StrokeStyle.SQUARE))
            # wall_fixing_pos = (0, anchor_holder_fixing_points[0][1] + s/2)
            wall_fixing_pos = self.get_screwhole_positions()[0][:2]
            # using sagitta to work out radius of curve that links all points (again)
            s = abs(wall_fixing_pos[1] - anchor_holder_fixing_points[0][1])
            r_wall_fixing = s / 2 + (l ** 2) / (8 * s)

            standoff = standoff.union(get_stroke_arc(anchor_holder_fixing_points[0], anchor_holder_fixing_points[1], r_wall_fixing, wide=width, thick=plate_thick))

            gap_size = abs(wall_fixing_pos[1] - self.bearing_positions[-1][1]) - width
            if gap_size < 2:
                #don't leave little gaps
                standoff = standoff.union(get_stroke_arc(anchor_holder_fixing_points[0], anchor_holder_fixing_points[1], (r_anchor_bearing + r_wall_fixing)/2, wide=width, thick=plate_thick))



            standoff = self.cut_wall_fixing_hole(standoff, wall_fixing_pos, screw_head_d=self.wall_fixing_screw_head_d, add_extra_support=True)

        if not self.standoff_pillars_separate:
            standoff = standoff.union(self.get_standoff_pillars(top=True).translate((0,0,self.back_plate_from_wall)))
        standoff = self.cut_anchor_bearing_in_standoff(standoff)



        standoff = standoff.translate((0,0,-self.back_plate_from_wall))

        if self.text_on_standoffs:
            standoff = standoff.cut(self.get_text(top_standoff=True))

        standoff = standoff.cut(self.get_fixing_screws_cutter())#.translate(np_to_set(np.multiply(-1, self.bearing_positions[-1][:2]))


        # if for_printing and self.standoff_pillars_separate:
        #     standoff = standoff.rotate((0,0,0),(1,0,0),180)

        return standoff

    def get_rod_lengths(self):
        '''
        returns ([rod lengths, in same order as all_pillar_positions] , [base of rod z])
        '''
        lengths = []
        zs = []
        total_plate_distance = self.get_plate_thick(True) + self.get_plate_thick(False) + self.plate_distance
        if self.wall_mounted:

            from_back = 1

            length = total_plate_distance - from_back + self.back_plate_from_wall

            print("Need rod (M{}) of length {:.1f}mm + locked into a dome nut for all pillars".format(self.fixing_screws.metric_thread, length))

            zs = [-self.back_plate_from_wall + from_back for pillar in self.all_pillar_positions]
            lengths = [length for pillar in self.all_pillar_positions]
        else:
            extra_length = self.fixing_screws.get_nut_height()*2 + 2

            bottom_pillar_length = total_plate_distance
            if self.leg_height > 0:
                bottom_pillar_length += self.plate_thick*2

            if self.has_vanity_plate:
                bottom_pillar_length += self.vanity_plate_base_z + self.vanity_plate_thick
                if self.leg_height > 0:
                    #leg is included in the pillar that holds the vanity plate
                    bottom_pillar_length -= self.plate_thick

            bottom_pillar_length += extra_length

            top_pillar_length = total_plate_distance + self.back_plate_from_wall + extra_length

            print("Need rod (M{}) of length {}mm for top pillars and {}mm for bottom pillars".format(self.fixing_screws.metric_thread, math.ceil(top_pillar_length), math.ceil(bottom_pillar_length)))

            lengths = [bottom_pillar_length for pillar in self.bottom_pillar_positions] + [top_pillar_length for pillar in self.top_pillar_positions]

            zs = [-self.plate_thick - extra_length/2 for pillar in self.bottom_pillar_positions] + [-self.back_plate_from_wall - extra_length/2 for pillar in self.top_pillar_positions]

        return (lengths, zs)


    def get_assembled(self, one_peice=True):
        plates, pillars, detail, standoff_pillars = super().get_assembled(one_peice=False)

        if not self.wall_mounted:
            plates = plates.add(self.get_legs(back=True).translate((0,0,-self.plate_thick)))

            plates = plates.add(self.get_legs(back=False).translate((0, 0, self.get_plate_thick(back=True) + self.get_plate_thick(back=False) + self.plate_distance)))

            for pillar_pos in self.leg_pillar_positions:
                pillars = pillars.add(self.get_legs_pillar().translate(pillar_pos))

        # if self.escapement_on_front and not self.front_anchor_holder_part_of_dial:
        #     plates.add(self.get_front_anchor_bearing_holder())

        if one_peice:
            return plates.union(pillars).union(detail)
        return (plates, pillars, detail, standoff_pillars)

    def output_STLs(self, name="clock", path="../out"):
        super().output_STLs(name, path)

        if not self.wall_mounted:
            export_STL(self.get_legs(back=True), "legs_back", name, path)
            export_STL(self.get_legs(back=False), "legs_front", name, path)
            export_STL(self.get_legs_pillar(), "legs_pillar", name, path)
            export_STL(self.get_back_cock(), "back_cock", name, path)

        if self.has_vanity_plate:
            export_STL(self.get_vanity_plate(), "vanity_plate", name, path)

class RollingBallClock(SimpleClockPlates):
    '''
    Doing more than just the plates, this will create dials and hands and trains too
    '''


    def __init__(self, name="",layer_thick=0.4):
        '''
        plan:

        new type of motion works where the hands are fixed to the rod and we use a "clutch" to enable adjusting the hands
        then can use "real" arbors within the plates to hold the hour hand
        This will mean the motion works isn't visible on the front plate and the hands can be close to the front plate (so the dial can be printed as part of teh front plate)

        Assuming a user-provided going train we can then calculate the size required for the motion works so the seconds and hour dials are equally spaced

        Plan is to support two spring barrels, both at an angle underneath the minute wheel. I'll see if one spring is enough to power the clock, and if it isn't
        I can then easily double the power by adding in the second barrel

        I'm not worried about the exact timing of the ball on teh tray - since this clock has a second hand I can just adjust the ratio of the final wheel-pinion pair
        just like I would on a short pendulum clock.
        It would be ideal if the "escape wheel" rotated at 1rpm, then the plates could be more symetric. Maybe worth thinking about that a bit more.
        Or maybe have the esacpe wheel at 90deg below the seconds dial? or does it matter if the arbors aren't symetric so long as the plates are?


        TODO new fixing for hands with a nut embedded in teh back of the hands? one nut behind and a dome nut in front should be enough to fix them rigidly to the rod

        '''

        # super().__init__(self.gen_going_train(), motion_works=None, pendulum=None, style=ClockPlateStyle.COMPACT, pendulum_at_top=True, plate_thick=plate_thick, back_plate_thick=back_plate_thick,
        #                  pendulum_sticks_out=pendulum_sticks_out, name=name, heavy=True, pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS,
        #                  pendulum_at_front=False, back_plate_from_wall=0, fixing_screws=MachineScrew(4, countersunk=True),
        #                  centred_second_hand=False, pillars_separate=True, dial=None, bottom_pillars=2, top_pillars=2,
        #                  second_hand=second_hand, motion_works_angle_deg=math.pi, endshake=1.5, compact_zigzag=True, screws_from_back=None,
        #                  layer_thick=layer_thick)
        #
        # self.narrow_bottom_pillar=False
        # self.little_arm_to_motion_works=False
        # self.pillar_screwhole_r = self.fixing_screws.get_rod_cutter_r(layer_thick=self.layer_thick, loose=True)


    def gen_going_train(self):
        return None

    def gen_dials(self):
        #TODO work with generating the train to

        self.dial_minutes = Dial(150, DialStyle.ARABIC_NUMBERS, dial_width=20, font="Gill Sans Medium", font_scale=0.8, font_path="../fonts/GillSans/Gill Sans Medium.otf",
                                 inner_edge_style=DialStyle.LINES_RECT, minutes_only=True, top_fixing=False, bottom_fixing=False)
        # looks good for the hours
        self.dial_hours = Dial(100, DialStyle.ROMAN_NUMERALS, dial_width=15, font="Times New Roman", font_scale=0.6, inner_edge_style=DialStyle.LINES_RECT_LONG_INDICATORS, hours_only=True,
                               top_fixing=False, bottom_fixing=False)

        self.dial_seconds = Dial(100, dial_width=15, inner_edge_style=DialStyle.LINES_RECT_LONG_INDICATORS, style=DialStyle.ARABIC_NUMBERS, font="Gill Sans Medium", font_scale=0.9,
                                 font_path="../fonts/GillSans/Gill Sans Medium.otf", seconds_only=True, top_fixing=False, bottom_fixing=False)

    def calc_pillar_info(self, override_bottom_pillar_r=-1):
        '''
        current plan: asymetric to be compact, with anchor arbor sticking out the top above the topmost pillar

        This is completely hard coded around a spring powered clock with 4 wheels and 2 powered wheels using the compact layout.
        if the spring clock is a success, it'll be worth making it more flexible
        '''

        bearingInfo = get_bearing_info(self.arbor_d)
        # TODO review this from old logic width of thin bit
        self.plate_width = bearingInfo.outer_d + self.bearing_wall_thick * 2
        self.min_plate_width = self.plate_width
        self.pillar_r = self.plate_width/2

        self.bottom_pillar_positions = []
        self.top_pillar_positions = []
        self.bottom_pillar_r = self.pillar_r
        self.top_pillar_r = self.pillar_r

        bottom_distance = self.arbors_for_plate[0].get_max_radius() + self.gear_gap + self.bottom_pillar_r
        # TODO check this doesn't collide with next wheel
        bottom_angle = -math.pi / 4
        self.bottom_pillar_positions = [polar(math.pi - bottom_angle, bottom_distance), polar(bottom_angle, bottom_distance)]

        # right_pillar_line = Line(self.bearing_positions[1][:2], anotherPoint=self.bearing_positions[-2][:2])
        # #how far between the arbors 1 and -2
        # right_distance = np.linalg.norm(np.subtract(self.bearing_positions[1][:2], self.bearing_positions[-2][:2]))
        # #calculate how far along is "in the middle" of the empty space between them
        # right_bottom_distance = self.arbours_for_plate[1].get_max_radius()
        # along_distance = right_bottom_distance + (right_distance - self.arbours_for_plate[-2].get_max_radius() - right_bottom_distance)/2
        # right_bottom_equidistance_point = npToSet(np.add(self.bearing_positions[1][:2], np.multiply(right_pillar_line.dir, along_distance)))
        # #now go outwards from teh minute wheel along the line that goes through the minutewheel and this point
        # right_pillar_line2 = Line(self.bearing_positions[self.going_train.powered_wheels][:2], anotherPoint=right_bottom_equidistance_point)
        #
        # from_minute_wheel = self.arbours_for_plate[self.going_train.powered_wheels].get_max_radius() + self.gear_gap + self.top_pillar_r
        # right_pillar_pos = npToSet(np.add(right_pillar_line2.start,np.multiply(right_pillar_line2.dir, from_minute_wheel)))
        #
        # self.top_pillar_positions = [right_pillar_pos]
        right_pillar_line = Line(self.bottom_pillar_positions[1], anotherPoint=self.bearing_positions[1][:2])
        # left_pillar_line = Line(self.bottom_pillar_positions[1], anotherPoint=self.bearing_positions[self.going_train.powered_wheels+1][:2])
        self.top_pillar_positions = [
            np_to_set(
                np.add(self.bearing_positions[self.going_train.powered_wheels + 1][:2], np.multiply(polar(math.pi * 0.525), self.arbors_for_plate[self.going_train.powered_wheels + 1].get_max_radius() + self.gear_gap + self.top_pillar_r))),
            np_to_set(np.add(self.bearing_positions[1][:2], np.multiply(right_pillar_line.dir, self.arbors_for_plate[1].get_max_radius() + self.gear_gap + self.top_pillar_r))),
        ]
        print("top pillar distance gap: ", np.linalg.norm(np.subtract(self.top_pillar_positions[1], self.bearing_positions[-1][:2])) - self.top_pillar_r - self.arbors_for_plate[-1].get_max_radius())

    def calc_fixing_info(self):
        # fixing positions to plates and pillars together
        self.plate_top_fixings = []
        # (self.top_pillar_positions[0] - self.top_pillar_r / 2, self.top_pillar_positions[1]), (self.top_pillar_positions[0] + self.top_pillar_r / 2, self.top_pillar_positions[1])]
        for top_pillar_pos in self.top_pillar_positions:
            self.plate_top_fixings.append((top_pillar_pos[0], top_pillar_pos[1]))

        self.plate_bottom_fixings = []
        for bottom_pillar_pos in self.bottom_pillar_positions:
            self.plate_bottom_fixings.append((bottom_pillar_pos[0], bottom_pillar_pos[1]))

        self.plate_fixings = self.plate_top_fixings + self.plate_bottom_fixings

    def get_plate(self, back=True, for_printing=True):

        plate_thick = self.get_plate_thick(back=back)

        plate = cq.Workplane("XY").rect(100,100).extrude(plate_thick)
        return plate

        main_arm_wide = self.plate_width
        medium_arm_wide = get_bearing_info(3).outer_d + self.bearing_wall_thick * 2
        small_arm_wide = 8

        pillar_positions = self.top_pillar_positions + self.bottom_pillar_positions

        # for pillar in range(len(pillar_positions)):
        #     pillar_pos = pillar_positions[pillar]
        #     next_pillar_pos = pillar_positions[(pillar + 1)% len(pillar_positions)]
        #
        # link up the side pillars with each other
        for side in [0, 1]:
            plate = plate.union(get_stroke_line([self.top_pillar_positions[side], self.bottom_pillar_positions[side]], wide=main_arm_wide, thick=plate_thick))
            plate = plate.union(get_stroke_line([self.bottom_pillar_positions[side], self.bearing_positions[0][:2]], wide=main_arm_wide, thick=plate_thick))

        # plate = plate.union(get_stroke_line([self.top_pillar_positions[side], self.bearing_positions[-2][:2]], wide=main_arm_wide, thick=plate_thick))
        if not back:
            # arch over the top
            # no point holding the bearing that isn't there for the anchor arbor!
            plate = plate.union(get_stroke_line([self.bearing_positions[-2][:2], self.bearing_positions[-1][:2]], wide=main_arm_wide, thick=plate_thick))
            plate = plate.union(get_stroke_line([self.top_pillar_positions[0], self.bearing_positions[-1][:2]], wide=main_arm_wide, thick=plate_thick))
            plate = plate.union(get_stroke_line([self.top_pillar_positions[1], self.bearing_positions[-2][:2]], wide=main_arm_wide, thick=plate_thick))

        if back:
            plate = plate.union(get_stroke_line([self.top_pillar_positions[1], self.bearing_positions[-2][:2]], wide=main_arm_wide, thick=plate_thick))

        # barrel to minute wheel
        plate = plate.union(get_stroke_line([self.bearing_positions[0][:2], self.bearing_positions[self.going_train.powered_wheels][:2]], wide=medium_arm_wide, thick=plate_thick))

        # across the front of the plate
        plate = plate.union(get_stroke_line([self.bearing_positions[self.going_train.powered_wheels + 1][:2], self.bearing_positions[1][:2]], wide=medium_arm_wide, thick=plate_thick))

        # idea - 3 thin arms all linking to the second hand arbor? medium from barrel to minute wheel, thick just for the edges
        links = [self.bearing_positions[self.going_train.powered_wheels][:2],
                 self.bearing_positions[self.going_train.powered_wheels + 3][:2],
                 self.top_pillar_positions[0]
                 ]
        for link_pos in links:
            plate = plate.union(get_stroke_line([self.bearing_positions[self.going_train.powered_wheels + 2][:2], link_pos], wide=small_arm_wide, thick=plate_thick))

        for i, pos in enumerate(self.bearing_positions):

            bearing_info = self.arbors_for_plate[i].bearing

            if not (i == len(self.bearing_positions) - 1 and back):
                # only if not the back plate and the hole for the anchor arbor
                plate = plate.union(cq.Workplane("XY").circle(bearing_info.outer_d / 2 + self.bearing_wall_thick).extrude(plate_thick).translate(pos[:2]))

        plate = plate.union(cq.Workplane("XY").circle(self.going_train.powered_wheel.key_bearing.outer_d / 2 + self.bearing_wall_thick * 1.5).extrude(plate_thick))

        if back:
            plate = plate.cut(self.get_fixing_screws_cutter())
            if not self.text_on_standoffs:
                plate = plate.cut(self.get_text())
        else:
            plate = plate.cut(self.get_fixing_screws_cutter().translate((0, 0, -self.get_plate_thick(back=True) - self.plate_distance)))

        if not back:
            plate = self.front_additions_to_plate(plate)

        plate = self.punch_bearing_holes(plate, back)

        if self.going_train.powered_wheel.type == PowerType.SPRING_BARREL and self.going_train.powered_wheel.ratchet_at_back == back:
            # spring powered, need the ratchet!
            screw = self.going_train.powered_wheel.ratchet.fixing_screws

            cutter = cq.Workplane("XY")

            for relative_pos in self.going_train.powered_wheel.ratchet.get_screw_positions() + self.going_train.powered_wheel.ratchet.get_little_plate_for_pawl_screw_positions():
                pos = np_to_set(np.add(self.bearing_positions[0][:2], relative_pos))
                # undecided if they need to be for tap die, they mgiht be enough without now there's a little plate for the pawl
                cutter = cutter.add(screw.get_cutter(with_bridging=True).translate(pos))  # for_tap_die=True,

            if back:
                cutter = cutter.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, plate_thick))

            plate = plate.cut(cutter)

        return plate

    def get_text(self, top_standoff=False):

        all_text = cq.Workplane("XY")

        # (x,y,width,height, horizontal)
        spaces = []

        texts = [" ".join(self.texts[1:]), self.texts[0]]

        long_line = Line(self.bottom_pillar_positions[0], anotherPoint=self.top_pillar_positions[0])
        long_space_length = np.linalg.norm(np.subtract(self.top_pillar_positions[0], self.bottom_pillar_positions[0]))
        long_line_length = long_space_length - self.top_pillar_r - self.bottom_pillar_r - 1
        text_height = self.plate_width * 0.9
        long_centre = np_to_set(np.add(long_line.start, np.multiply(long_line.dir, long_space_length / 2)))
        long_angle = long_line.get_angle()

        short_line = Line(self.bottom_pillar_positions[1], anotherPoint=self.top_pillar_positions[1])
        short_space_length = np.linalg.norm(np.subtract(self.bearing_positions[1][:2], self.bottom_pillar_positions[1]))
        short_line_length = short_space_length - 10
        short_centre = np_to_set(np.add(short_line.start, np.multiply(short_line.dir, short_space_length / 2)))
        short_angle = short_line.get_angle() + math.pi

        # three along the wide bit at the bottom and one above
        spaces.append(TextSpace(long_centre[0], long_centre[1], text_height, long_line_length, angle_rad=long_angle))
        spaces.append(TextSpace(short_centre[0], short_centre[1], text_height, short_line_length, angle_rad=short_angle))
        # spaces.append(TextSpace(bottom_pos[0], (bottom_pos[1] + (chain_pos[1] - chain_space)) / 2, text_height, chain_pos[1] - chain_space - bottom_pos[1], horizontal=False))
        # spaces.append(TextSpace(bottom_pos[0] + self.bottom_pillar_r - self.bottom_pillar_r / 3, (bottom_pos[1] + chain_pos[1]) / 2, text_height, chain_pos[1] - bottom_pos[1], horizontal=False))
        #
        # spaces.append(TextSpace(chain_pos[0], (first_arbour_pos[1] - arbour_space + chain_pos[1] + chain_space) / 2, self.plate_width * 0.9, first_arbour_pos[1] - arbour_space - (chain_pos[1] + chain_space), horizontal=False))

        for i, text in enumerate(texts):
            spaces[i].set_text(text)

        max_text_size = min([textSpace.get_text_max_size() for textSpace in spaces])

        for space in spaces:
            space.set_size(max_text_size)

        for space in spaces:
            all_text = all_text.add(space.get_text_shape())

        all_text = self.punch_bearing_holes(all_text, back=True, make_plate_bigger=False)

        return all_text

    def get_screwhole_positions(self):
        '''
        this doesn't hang on the wall, so no wall fixings
        '''
        return []

    def get_wall_standoff(self, top=True, for_printing=True):
        '''
        not really a wall standoff, but the bit that holds the pendulum at the top
        '''
        return None

    def get_pillar(self,top=True, flat=True):
        '''
        this is a pillar in teh sense of the simple clock plate - this holds the front and back plates together
        we'll have front pillars that hold the base of the clock (with the marble run) to the movement, need to think of a new name for those
        '''



        return cq.Workplane("XY").circle(self.pillar_r).circle(self.pillar_screwhole_r).extrude(self.plate_distance)

    def get_top_pillar(self):
        return self.get_pillar()

    def get_bottom_pillar(self):
        return self.get_pillar()

class StrikingClockPlates(SimpleClockPlates):
    '''
    Striking clock plates, undecided yet if they'll be shelf mounted or wall mounted. I'll see how large they end up being first
    '''

    def __init__(self, going_train, motion_works, plate_thick=8, back_plate_thick=None, pendulum_sticks_out=15, name="", centred_second_hand=False, dial=None,
                 moon_complication=None, second_hand=True, motion_works_angle_deg=-1, screws_from_back=None, layer_thick=LAYER_THICK_EXTRATHICK):
        super().__init__(going_train, motion_works, pendulum=None, gear_train_layout=GearTrainLayout.COMPACT, pendulum_at_top=True, plate_thick=plate_thick, back_plate_thick=back_plate_thick,
                         pendulum_sticks_out=pendulum_sticks_out, name=name, heavy=True, pendulum_fixing=PendulumFixing.DIRECT_ARBOR_SMALL_BEARINGS,
                         pendulum_at_front=False, back_plate_from_wall=pendulum_sticks_out + 10 + plate_thick, fixing_screws=MachineScrew(4, countersunk=True),
                         centred_second_hand=centred_second_hand, pillars_separate=True, dial=dial, bottom_pillars=2, moon_complication=moon_complication,
                         second_hand=second_hand, motion_works_angle_deg=motion_works_angle_deg, endshake=1.5, compact_zigzag=True, screws_from_back=screws_from_back,
                         layer_thick=layer_thick)

class SlideWhistlePlates:
    '''
    Think I'll start fresh as there won't be a huge amount in common with the clocks. Probably abstract useful bits from SimpleClockPlates as I go
    '''
    def __init__(self):
        pass
