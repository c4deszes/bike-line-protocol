# System imports
from typing import List
from dataclasses_json import dataclass_json
from dataclasses import dataclass
import time

# Local imports
from line_protocol.protocol.transport import LineTrafficListener

@dataclass_json
@dataclass
class TrafficBaseRecord:
    """Common record type for all traffic records"""
    timestamp: float
    request: int

@dataclass_json
@dataclass
class TrafficRecord(TrafficBaseRecord):
    """TrafficRecord represents a valid request"""
    size: int
    data: List[int]
    checksum: int

    def __str__(self) -> str:
        return ' '.join(format(i, '02X') for i in self.data)

@dataclass_json
@dataclass
class TrafficErrorRecord(TrafficBaseRecord):
    """TrafficErrorRecord represents a failure on the bus"""
    error: str

    def __str__(self) -> str:
        return self.error
    
@dataclass_json
@dataclass
class TrafficLogs:
    """Container of traffic records"""
    start: float
    logs: List[TrafficBaseRecord]

class TrafficLogger(LineTrafficListener):

    def __init__(self) -> None:
        self.traffic = TrafficLogs(time.time(), [])
        self._changed = False

    def on_request(self, timestamp, request: int, size, data, checksum):
        self.traffic.logs.append(TrafficRecord(timestamp-self.traffic.start, request, size, data, checksum))
        self._changed = True

    def on_error(self, timestamp, request: int, error):
        error_type = type(error).__name__
        self.traffic.logs.append(TrafficErrorRecord(timestamp-self.traffic.start, request, error_type))
        self._changed = True

    def has_changed(self):
        if self._changed:
            self._changed = False
            return True
        return False

    def dump_json(self, path):
        with open(path, 'w+') as f:
            f.write(self.traffic.to_json(indent=2))
