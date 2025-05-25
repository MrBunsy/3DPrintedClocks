from enum import Enum


class GearTrainLayout(Enum):
    '''
    how to lay out gear train
    '''
    #gear train directly vertical
    VERTICAL = "vertical"
    #gear train points on a circle (not printed since clock 05, but still broadly functional, might be worth ressurecting properly)
    ROUND = "round"
    # gear train approximately vertical but zigzagged to reduce height
    VERTICAL_COMPACT = "vertical compact"
    # more compact, without escape wheel at top if that makes it smaller
    COMPACT = "compact"
    #new design that attemps to put the seconds wheel in the centre and doesn't care where the minute wheel goes
    #designed with round clock plates in mind
    COMPACT_CENTRE_SECONDS = "compact centre seconds"

class NotGearTrainLayout(Enum):
    '''
    how to lay out gear train
    '''
    FRED = "fred"

bob = GearTrainLayout.VERTICAL
fred = NotGearTrainLayout.FRED

is_enum = isinstance(bob, Enum)

# print(is_enum)

def function1(firstarg, kwargs_dict):
    function2(firstarg, **kwargs_dict)

def function2(firstarg, **kwargs):
    function3(firstarg, **kwargs)

def function3(firstarg, bob="bob"):
    print(f"{firstarg}, {bob}")

# function1("fred", {"bob": "robert"})

function3("fred")