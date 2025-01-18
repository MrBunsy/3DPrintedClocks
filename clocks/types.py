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
from enum import Enum

'''
This is in a separate file to avoid circular dependencies
'''

class RomanNumeralStyle(Enum):
    CUCKOO = "cuckoo"
    SIMPLE_ROUNDED = "simple_rounded"
    SIMPLE_SQUARE = "simple_square"

class HandStyle(Enum):
    SQUARE = "square"
    SIMPLE = "simple"
    SIMPLE_ROUND = "simple_rounded"
    SIMPLE_POINTED = "simple_pointed"
    CUCKOO = "cuckoo"
    SPADE = "spade"
    BREGUET = "breguet" # has a single circle on each hand
    SYRINGE="syringe"
    SWORD="sword"
    CIRCLES="circles" # very much inspired by the same clock on the horological journal that inspired the circle style gears
    XMAS_TREE="xmas_tree"
    BAROQUE="baroque"
    ARROWS="arrows"#specicially for Tony the Clock
    MOON = "moon"#Brequet but with crescents instead of circles
    INDUSTRIAL = "industrial"#based on a Siemens slave clock
    FANCY_WATCH = "fancy_watch" #inspired by rolex explorer
    TWIRLY = "twirly"
    THIN_DIAMOND = "thin_diamond"

class HandType(Enum):
    HOUR = "hour"
    MINUTE = "minute"
    SECOND = "second"

class EscapementType(Enum):
    DEADBEAT = "deadbeat"
    RECOIL = "recoil" # new recoil is still untested
    GRASSHOPPER = "grasshopper"
    BROCOT = "brocot"
    NOT_IMPLEMENTED = None

class GearTrainLayout(Enum):
    '''
    how to lay out gear train
    '''
    #gear train directly vertical
    VERTICAL = "vertical"
    #gear train points on a circle (not printed since clock 05, but still broadly functional, might be worth ressurecting properly)
    ROUND = "round"
    #gear train approximately vertical but zigzagged to reduce height
    COMPACT = "compact"
    #new design that attemps to put the seconds wheel in the centre and doesn't care where the minute wheel goes
    #designed with round clock plates in mind
    COMPACT_CENTRE_SECONDS = "compact centre seconds"

class PlateStyle(Enum):
    '''
    fancy detailing, if any, for clock plates
    '''
    SIMPLE = "simple"
    #based on a clock I saw on ebay with raised brass edging and black plates
    RAISED_EDGING = "raised_edging"

class PlateShape(Enum):
    SIMPLE_VERTICAL = "simple_vertical"
    SIMPLE_ROUND = "simple_round" # clock 5, offset hands and pendulum. probably won't use again
    MANTEL = "mantel"
    ROUND = "round" #wall or on legs

class PendulumFixing(Enum):
    #the first reliable mechanism, with the anchor and rod-holder both on the same threaded rod held with friction, the pendulum slots into the fixing on the anchor arbour rod
    #works, but setting the beat is a right nuscance and it's easily knocked out of alignment
    FRICTION_ROD = "friction_rod"
    #using a 10mm bearing for the front anchor arbour, a long extension from the anchour arbour will end in a square and the rod will slot onto this like the minute hand slots
    #onto the cannon pinion
    #DEPRECATED and mostly removed from the codebase. large bearings had way too much friction to hold the anchor and pendulum
    DIRECT_ARBOR = "direct_arbour"
    '''
    Same as direct arbour - but avoiding the use of the large (high friction) bearings. Now the recommended solution for all new designs
    TODO remove DIRECT_ARBOR, it was unreliable so I have no reason to ever print again
    ...or would degreased stainless steel large bearings work? might be handy for mantel clocks to avoid having a whole peice to hold the rear bearing
    '''
    DIRECT_ARBOR_SMALL_BEARINGS = "direct_arbour_small_bearings"
    #very first attempt, using a traditional clutch but a knife edge instead of a suspension spring (no longer implemented fully)
    #since using degreased stainless steel EZO bearings I'm not sure I've got any need to go back to this or even try suspension springs
    KNIFE_EDGE = "knife_edge"
    #idea - 3D printed suspension spring, works for the ratchet, might work for this?
    #might try with real steel spring too
    #two types of suspension spring because I'm not sure which will work best - I may need both anyway if I want to ressurect front pendulum
    #a large hole in the back/front plate for the crutch to slot through
    SUSPENSION_SPRING_WITH_PLATE_HOLE = "suspension_spring_with_plate_hole"
    #same small hole in plate as direct arbour, and the rear standoff or front bearing holder holds the bearing
    SUSPENSION_SPRING = "suspension_spring"

class GearStyle(Enum):
    SOLID = None
    #arcs made from semicircles
    ARCS = "HAC"
    #more aggressive arcs, non-semicircular
    ARCS2 = "arcs"
    #punched out circles with little circles between
    CIRCLES = "circles"
    #just the outer edges of a ring of circles
    CIRCLES_HOLLOW = "circles_hollow"
    #circles but with variations of cresent moons
    MOONS = "moons"
    SIMPLE4 = "simple4"
    SIMPLE5 = "simple5"
    #spokes these don't print nicely with petg - very stringy (might be fine on anything other than the mini?)
    SPOKES = "spokes"
    STEAMTRAIN = "steamtrain"
    CARTWHEEL = "cartwheel"
    FLOWER = "flower"
    HONEYCOMB = "honeycomb"
    HONEYCOMB_SMALL = "honeycomb_small"
    HONEYCOMB_CHUNKY = "honeycomb_chunky"
    #psuedorandom with global seed
    SNOWFLAKE = "snowflake"
    CURVES = "curves"
    DIAMONDS = "diamonds"
    #planned - branching tree structure (not a million miles off snowflake) - probably best for a design with big wheels like grasshopper
    TREE = "tree"
    BENT_ARMS4 = "bent_arms4" # inspired by disc brakes
    BENT_ARMS5 = "bent_arms5"
    ROUNDED_ARMS5 = "rounded_arms5"

class StrokeStyle(Enum):
    ROUND = "rounded"
    SQUARE = "square"

class AnchorStyle(Enum):
    STRAIGHT = "straight" #the old default style
    CURVED = "curved" # from a make of my clock someone posted on printables - I love it so I'm pinching the idea
    CURVED_MATCHING_WHEEL = "curved2" # curved arms but of a radius that matches the escape wheel

'''
ideas for new styles:
 - bicycle sprockets
 - bicycle disc brakes (both ideas nicked from etsy quartz clocks)
 - honeycomb
 - Voronoi Diagram
 - curved arms
 - sine wave wraped around the circle?
'''

class ArborType(Enum):
    WHEEL_AND_PINION = "Wheel And Pinion"
    POWERED_WHEEL = "Powered Wheel"
    ESCAPE_WHEEL = "Escape Wheel"
    ANCHOR = "Anchor"
    #used for special things like fans or flys
    LONE_PINION = "Lone Pinion"
    UNKNOWN = "Unknown"

class PowerType(Enum):
    NOT_CONFIGURED = None
    # === Weight types ===
    CHAIN = "chain"
    #the better version
    CHAIN2 = "chain2"
    #third attempt to get a reliable chain wheel for heavy weights
    SPROCKET = "sprocket"
    #drop in for chain, using friction and a hemp rope (not great, needs massive counterweight)
    ROPE = "rope"
    #thin synthetic cord, coiled multiple times
    CORD = "cord"
    # === Spring types ===
    SPRING_BARREL = "spring" # either loop end or barrel

    @staticmethod
    def is_weight(type):
        return type in [PowerType.CHAIN, PowerType.CHAIN2, PowerType.ROPE, PowerType.CORD]

    @staticmethod
    def is_spring(type):
        return not PowerType.is_weight(type)

class PillarStyle(Enum):
    SIMPLE = "simple"
    SIMPLE_HEX = "simple_hex"
    BARLEY_TWIST = "barley_twist"
    COLUMN = "column"
    #uh this didn't quite come out as planned
    BLOBS = "blobs"
    #*love* this one but it doesn't fit with the old-fashioned style of RAISED_EDGING, need to think of a good plate design for it
    TWISTY = "twisty"
    CLASSIC = "classic"
    PLAIN = "modern" #simplified classic pillar


class DialStyle(Enum):
    '''
    Thoughts, there's lots here that could be abstracted out into options for the dial as a whole, rather than separate styles
    for example, shoudl hours_only, seconds_only, minutes_only be options to the dial, rather than styles?
    '''
    #simple lines that are actually slightly wedge shaped
    LINES_ARC = "lines_arc"
    #simple lines that are just rectangles
    LINES_RECT = "lines_rect"
    #same but long indicators rather than thick indicators
    LINES_RECT_LONG_INDICATORS = "lines_rect_long"
    #same but for an hours-only dial
    # LINES_RECT_HOURS = "lines_rect_hours"
    # #same but for a seconds-only dial
    # LINES_RECT_SECONDS = "lines_rect_seconds"
    #deprecated, replaced with ROMAN_NUMERALS as main style and CONCENTRIC_CIRCLES as outer edge style
    ROMAN = "roman"
    #flat cuckoo style (not the fully 3D cuckoo style in cuckoo bits)
    # CUCKOO = "cuckoo"
    # DOTS = "dots"
    #two concentric circles joined by lines along spokes
    CONCENTRIC_CIRCLES="concentric_circles"
    DOTS = "circles"
    DOTS_MAJOR_ONLY = "major_dots"
    TONY_THE_CLOCK="tony_the_clock"
    #just numbers
    ARABIC_NUMBERS= "simple_arabic"
    # ARABIC_NUMBERS_MINUTES = "simple_arabic_minutes"
    # ARABIC_NUMBERS_SECONDS = "simple_arabic_seconds"
    #just roman numerals
    ROMAN_NUMERALS = "roman_numerals"
    #just a solid ring
    RING = "ring"
    FANCY_WATCH_NUMBERS = "fancy_watch_numbers" #triangle at 12, numbers at 3,6,9 dashes at all other numbers
    LINES_INDUSTRIAL = "lines_industrial" # loosely based on an old siemens clock
    LINES_MAJOR_ONLY = "lines_major_only"
