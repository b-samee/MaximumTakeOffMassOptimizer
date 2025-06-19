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
    
    def __repr__(self) -> str:
        match self:
            case ProcessStatus.SLEEPING:
                return f'SLEEPING'
            case ProcessStatus.STARTING:
                return f'STARTING'
            case ProcessStatus.EXECUTING_QPROP:
                return f'EXECUTING_QPROP'
            case ProcessStatus.EXTRACTING_DATA:
                return f'EXTRACTING_DATA'
            case ProcessStatus.CALCULATING:
                return f'CALCULATING'
            case ProcessStatus.UPDATING_COUNTERS:
                return f'UPDATING_COUNTERS'
            case ProcessStatus.CHECKING_CONDITION:
                return f'CHECKING_CONDITION'
            case ProcessStatus.REJECTED:
                return f'REJECTED'
            case ProcessStatus.ACCEPTED:
                return f'ACCEPTED'
        raise ValueError(f'Missing ProcessStatus match case for [{self}]')
