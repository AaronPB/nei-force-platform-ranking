from enum import Enum, auto


class SStatus(Enum):
    IGNORED = auto()
    AVAILABLE = auto()
    NOT_FOUND = auto()


class SGStatus(Enum):
    IGNORED = auto()
    OK = auto()
    WARNING = auto()
    ERROR = auto()
