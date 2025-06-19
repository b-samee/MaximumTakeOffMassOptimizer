import enum

class ProcessStatus(enum.Enum):
    SLEEPING = 0
    STARTING = enum.auto()
    EXECUTING_QPROP = enum.auto()
    EXTRACTING_DATA = enum.auto()
    CALCULATING = enum.auto()
    UPDATING_COUNTERS = enum.auto()
    CHECKING_CONDITION = enum.auto()
    REJECTED = enum.auto()
    ACCEPTED = enum.auto()

    @classmethod
    def get(cls, index: int):
        return list(cls)[index]
