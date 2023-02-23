from .utility import *
from .power import *
from .gearing import *
from .cosmetics import *
from .leaves import *
from .dial import *
import cadquery as cq
from pathlib import Path
from cadquery import exporters
import math
from math import sin, cos, pi, floor
import numpy as np
import os
import datetime

'''
Aim is to make a mechanical bird song - whistle driven by double action bellows with levers to control volume and pitch.
First attempt will be hand-cranked

I'd like to make it use detachable music discs to drive the song, so I can easily experiment with different songs
'''


class AirPipe:
    '''
    info about dimensions of a pipe
    '''
    def __init__(self, internal_diameter=5, external_diameter=8):
        self.internal_diameter = internal_diameter
        self.external_diameter = external_diameter

class DoubleActionBellows:
    '''
    A triple-bellow mechanism which can provide a constant stream of air from a reciprocal motion
    Real world examples I've seen use a spring but I'm wondering about putting them upright and using a weight

    Many thanks to melvyn Wright for his double action (organ!) bellows design: http://www.melright.com/busker/jsart119.htm
    '''

    def __init__(self, width=4, length=8, height=5, thickness=2.4, pipe=None):
        self.width = width
        self.length = length
        self.height = height
        self.pipe = pipe
        self.thickness = thickness
        if self.pipe is None:
            self.pipe = AirPipe()

        #internal valves
        self.valve_circle_r = self.width*0.1
        self.valve_circle_count=6
        self.valve_circle_rows=2

class BirdSong:

    def __init__(self, plate_thick=5):
        '''
        Hand-cranked birdsong generator. Will stand upright with handle on one side and all the birdsong mechanism on the other
        '''
        self.plate_thick = plate_thick
