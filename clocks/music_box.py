import cadquery as cq

class BellowsTrain:
    '''
    A gear train designed to be limited by some sort of fly and drive a bellows
    '''
    def __init__(self, power_source=None, bellows_rpm=30, fly_rpm=120, error_fraction=0.1):
        self.power_source = power_source
        self.bellows_rpm = bellows_rpm
        self.fly_rpm = fly_rpm
        self.error_fraction = error_fraction