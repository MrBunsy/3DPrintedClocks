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
    SIMPLE = "simple"

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

class HandType(Enum):
    HOUR = "hour"
    MINUTE = "minute"
    SECOND = "second"

class EscapementType(Enum):
    DEADBEAT = "deadbeat"
    #recoil was broken when deadbeat introduced, in theory not hard to fix, I've just had no reason to do so
    RECOIL = "recoil"
    GRASSHOPPER = "grasshopper"
    BROCOT = "brocot"
    NOT_IMPLEMENTED = None

class ClockPlateStyle(Enum):
    #gear train directly vertical
    VERTICAL = "vertical"
    #gear train points on a circle (not printed since clock 05, but still broadly functional, might be worth ressurecting properly)
    ROUND = "round"
    #gear train approximately vertical but zigzagged to reduce height
    COMPACT = "compact"

class PendulumFixing(Enum):
    #the first reliable mechanism, with the anchor and rod-holder both on the same threaded rod held with friction, the pendulum slots into the fixing on the anchor arbour rod
    FRICTION_ROD = "friction_rod"
    #using a 10mm bearing for the front anchor arbour, a long extension from the anchour arbour will end in a square and the rod will slot onto this like the minute hand slots
    #onto the cannon pinion
    #DEPRECATED and mostly removed from the codebase. large bearings had way too much friction to hold the anchor and pendulum
    DIRECT_ARBOUR = "direct_arbour"
    '''
    Same as direct arbour - but avoiding the use of the large (high friction) bearings. Experimental.
    '''
    DIRECT_ARBOUR_SMALL_BEARINGS = "direct_arbour_small_bearings"
    #very first attempt, using a traditional clutch but a knife edge instead of a suspension spring (no longer implemented fully)
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
    WHEEL_AND_PINION = "WheelAndPinion"
    POWERED_WHEEL = "PoweredWheel"
    ESCAPE_WHEEL = "EscapeWheel"
    ANCHOR = "Anchor"
    UNKNOWN = "Unknown"

class PowerType(Enum):
    NOT_CONFIGURED = None
    # === Weight types ===
    CHAIN = "chain"
    #the better version
    CHAIN2 = "chain2"
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
