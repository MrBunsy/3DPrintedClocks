import cadquery as cq
from pathlib import Path
from cadquery import exporters


class SmithsClip:
    def __init__(self, thick=0.8, diameter=2.3):
        '''
        I've seen two different thickenesses, 0.8 on the older striking movements and 0.5 on the time only spare movement
        inner diameter of the clip (rather than the post) appears to be about 2.35, entry wide about 2.8


        realised I can use bog standard c-clips!
        '''