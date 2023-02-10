from enum import Enum

'''
This is in a separate file to avoid circular dependencies
'''

class EscapementType(Enum):
    #only one fully implemented is deadbeat, recoil has been broken since deadbeat was introduced
    DEADBEAT = "deadbeat"
    RECOIL = "recoil"
    GRASSHOPPER = "grasshopper"
    NOT_IMPLEMENTED = None

class PendulumFixing(Enum):
    #the first reliable mechanism, with the anchor and rod-holder both on the same threaded rod held with friction, the pendulum slots into the fixing on the anchor arbour rod
    FRICTION_ROD = "friction_rod"
    #using a 10mm bearing for the front anchor arbour, a long extension from the anchour arbour will end in a square and the rod will slot onto this like the minute hand slots
    #onto the cannon pinion
    DIRECT_ARBOUR = "direct_arbour"
    '''
    Same as direct arbour - but avoiding the use of the large (high friction) bearings. Experimental.
    '''
    DIRECT_ARBOUR_SMALL_BEARINGS = "direct_arbour_small_bearings"
    #very first attempt, using a traditional clutch but a knife edge instead of a suspension spring (no longer implemented fully)
    KNIFE_EDGE = "knife_edge"
    #idea - 3D printed suspension spring, works for the ratchet, might work for this?

class GearStyle(Enum):
    SOLID = None
    ARCS = "HAC"
    CIRCLES = "circles"
    SIMPLE4 = "simple4"
    SIMPLE5 = "simple5"
    #spokes these don't print nicely with petg - very stringy (might be fine on anything other than the mini?)
    SPOKES = "spokes"
    STEAMTRAIN = "steamtrain"
    CARTWHEEL = "cartwheel"
    FLOWER = "flower"
    HONEYCOMB = "honeycomb"
    HONEYCOMB_SMALL = "honeycomb_small"
    #psuedorandom with global seed
    SNOWFLAKE = "snowflake"
    CURVES = "curves"
    DIAMONDS = "diamonds"

class StrokeStyle(Enum):
    ROUND = "rounded"

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

class ArbourType(Enum):
    WHEEL_AND_PINION = "WheelAndPinion"
    CHAIN_WHEEL = "ChainWheel"
    ESCAPE_WHEEL = "EscapeWheel"
    ANCHOR = "Anchor"
    UNKNOWN = "Unknown"

class PowerType(Enum):
    NOT_CONFIGURED = None
    # === Weight types ===
    CHAIN = "chain"
    CHAIN2 = "chain2"
    #drop in for chain, using friction and a hemp rope
    ROPE = "rope"
    #thin synthetic cord, coiled multiple times
    CORD = "cord"
    # === Spring types ===
    SPRING = "spring" # either loop end or barrel

class DialStyle(Enum):
    #simple lines that are actually slightly wedge shaped
    LINES_ARC = "lines_arc"
    #simple lines that are just rectangles
    LINES_RECT = "lines_rect"
    ROMAN = "roman"
    #flat cuckoo style (not the fully 3D cuckoo style in cuckoo bits)
    CUCKOO = "cuckoo"
    DOTS = "dots"
    #two concentric circles joined by lines along spokes
    CONCENTRIC_CIRCLES="concentric_circles"