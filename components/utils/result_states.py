import enum

class ResultState(enum.Enum):
    MASS_LOWERBOUND_BEYOND_MTOM = 0
    MASS_UPPERBOUND_BELOW_MTOM = enum.auto()
    MTOM_FOUND = enum.auto()
