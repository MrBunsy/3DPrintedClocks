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
    #very first attempt, using a traditional clutch but a knife edge instead of a suspension spring (no longer implemented fully)
    KNIFE_EDGE = "knife_edge"
    #idea - 3D printed suspension spring, works for the ratchet, might work for this?

class GearStyle(Enum):
    SOLID = None
    ARCS = "HAC"
    CIRCLES = "circles"
    SIMPLE4 = "simple4"
    SIMPLE5 = "simple5"
    #spokes these don't print nicely with petg - very stringy
    SPOKES = "spokes"
    STEAMTRAIN = "steamtrain"
    CARTWHEEL = "cartwheel"
    FLOWER = "flower"
    HONEYCOMB = "honeycomb"
    HONEYCOMB_SMALL = "honeycomb_small"

'''
ideas for new styles:
 - bicycle sprockets
 - bicycle disc brakes (both ideas knicked from etsy quartz clocks)
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
    #drop in for chain, using friction and a hemp rope
    ROPE = "rope"
    #thin synthetic cord, coiled multiple times
    CORD = "cord"
    # === Spring types ===
    SPRING = "spring" # either loop end or barrel