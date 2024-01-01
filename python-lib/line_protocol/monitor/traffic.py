from typing import List
from dataclasses_json import dataclass_json
from dataclasses import dataclass
import binascii
from ..protocol.transport import TransportListener

@dataclass_json
@dataclass
class TrafficBaseRecord:
    timestamp: float
    request: int

@dataclass_json
@dataclass
class TrafficRecord(TrafficBaseRecord):
    size: int
    data: List[int]
    checksum: int

    def __str__(self) -> str:
        return binascii.hexlify(self.data)

@dataclass_json
@dataclass
class TrafficErrorRecord(TrafficBaseRecord):
    error: str

    def __str__(self) -> str:
        return self.error
    
@dataclass_json
@dataclass
class TrafficLogs:
    logs: List[TrafficBaseRecord]

class TrafficLogger(TransportListener):

    def __init__(self) -> None:
        self.traffic = TrafficLogs([])
        self._changed = False

    def on_request(self, timestamp, request: int, size, data, checksum):
        self.traffic.logs.append(TrafficRecord(timestamp, request, size, data, checksum))
        self._changed = True

    def on_error(self, timestamp, request: int, error_type):
        self.traffic.logs.append(TrafficErrorRecord(timestamp, request, error_type))
        self._changed = True

    def has_changed(self):
        if self._changed:
            self._changed = False
            return True
        return False

    def dump_json(self, path):
        with open(path, 'w+') as f:
            f.write(self.traffic.to_json(indent=2))
