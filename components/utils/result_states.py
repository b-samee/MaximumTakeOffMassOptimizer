import enum

class ResultState(enum.Enum):
    MASS_LOWERBOUND_BEYOND_MTOM = 0
    MTOM_FAILED_TOLERANCE = enum.auto()
    MASS_UPPERBOUND_BELOW_MTOM = enum.auto()
    MTOM_PASSED_TOLERANCE = enum.auto()
