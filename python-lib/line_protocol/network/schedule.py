import time
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .request import Request
    from .network import Node
    from ..protocol import LineMaster

class ScheduleEntry():

    def perform(self, master: 'LineMaster'):
        raise NotImplementedError()
    
class RequestScheduleEntry():

    def __init__(self, request: 'Request') -> None:
        self.request = request

    def perform(self, master: 'LineMaster'):
        master.request_data(self.request.name)
    
class WakeupScheduleEntry():

    def perform(self, master: 'LineMaster'):
        master.wakeup()

class IdleScheduleEntry():

    def perform(self, master: 'LineMaster'):
        master.idle()

class ShutdownScheduleEntry():

    def perform(self, master: 'LineMaster'):
        master.shutdown()

class GetOperationStatusScheduleEntry():

    def __init__(self, node: 'Node') -> None:
        self.node = node

    def perform(self, master: 'LineMaster'):
        master.get_operation_status(self.node.address)

class GetPowerStatusScheduleEntry():

    def __init__(self, node: 'Node') -> None:
        self.node = node

    def perform(self, master: 'LineMaster'):
        master.get_power_status(self.node.address)

class GetSerialNumberScheduleEntry():

    def __init__(self, node: 'Node') -> None:
        self.node = node

    def perform(self, master: 'LineMaster'):
        master.get_serial_number(self.node.address)

class GetSoftwareVersionScheduleEntry():

    def __init__(self, node: 'Node') -> None:
        self.node = node

    def perform(self, master: 'LineMaster'):
        master.get_software_version(self.node.address)

class Schedule:

    def __init__(self, name: str, delay: float, entries: List[ScheduleEntry]) -> None:
        self.name = name
        self.delay = delay
        self.entries = entries

    def perform(self, master: 'LineMaster'):
        for entry in self.entries:
            # TODO: error handling
            entry.perform(master)
            time.sleep(self.delay)
