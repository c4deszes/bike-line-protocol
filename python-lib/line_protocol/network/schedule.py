import time
from typing import List, TYPE_CHECKING, Literal, Union

if TYPE_CHECKING:
    from .request import Request
    from .network import Node
    from ..protocol import LineMaster

class ScheduleEntry():

    def perform(self, master: 'LineMaster'):
        raise NotImplementedError()
    
class RequestScheduleEntry(ScheduleEntry):

    def __init__(self, request: 'Request') -> None:
        self.request = request

    def perform(self, master: 'LineMaster'):
        master.request(self.request.name)
    
class WakeupScheduleEntry(ScheduleEntry):

    def perform(self, master: 'LineMaster'):
        master.wakeup()

class IdleScheduleEntry(ScheduleEntry):

    def perform(self, master: 'LineMaster'):
        master.idle()

class ShutdownScheduleEntry(ScheduleEntry):

    def perform(self, master: 'LineMaster'):
        master.shutdown()

class GetOperationStatusScheduleEntry(ScheduleEntry):

    def __init__(self, node: 'Node') -> None:
        self.node = node

    def perform(self, master: 'LineMaster'):
        master.get_operation_status(self.node.address)

class GetPowerStatusScheduleEntry(ScheduleEntry):

    def __init__(self, node: 'Node') -> None:
        self.node = node

    def perform(self, master: 'LineMaster'):
        master.get_power_status(self.node.address)

class GetSerialNumberScheduleEntry(ScheduleEntry):

    def __init__(self, node: 'Node') -> None:
        self.node = node

    def perform(self, master: 'LineMaster'):
        master.get_serial_number(self.node.address)

class GetSoftwareVersionScheduleEntry(ScheduleEntry):

    def __init__(self, node: 'Node') -> None:
        self.node = node

    def perform(self, master: 'LineMaster'):
        master.get_software_version(self.node.address)

class ScheduleExecutor:

    def next(self) -> ScheduleEntry:
        """
        Return the next entry to be executed. This is used by the schedule executor to determine
        which entry to execute.
        """
        raise NotImplementedError()
    
    def wait(self) -> None:
        """
        Wait for the next entry to be executed.
        """
        raise NotImplementedError()
    
    def disable_entry(self, entry: Union[int, ScheduleEntry]) -> None:
        raise NotImplementedError()
    
    def enable_entry(self, entry: Union[int, ScheduleEntry]) -> None:
        raise NotImplementedError()
    
class Schedule:
    
    def create_executor(self) -> ScheduleExecutor:
        """
        Create a schedule executor for this schedule. This is used to execute the schedule and
        manage the cycle counters.
        """
        raise NotImplementedError()

class FixedOrderSchedule(Schedule):
    """
    A schedule that executes a fixed order of entries. The schedule is executed in a loop, with a
    delay between each entry.

    The schedule consists of slots, a slot is when a request can be sent. In case of fixed slots,
    the slot time is fixed regardless of the request length, it's the longest request duration plus
    a delay. In case of variable slots, the slot time is the duration of the current request plus a
    delay.

    If reserve_slots is True, the schedule will insert a delay even for entries which are disabled.
    """

    def __init__(self, name: str, entries: List[ScheduleEntry], slots: Literal['variable', 'fixed'],
                 reserve_slots: bool, delay: float) -> None:
        self.name = name
        self.entries = entries
        self.slots = slots
        self.reserve_slots = reserve_slots
        self.delay = delay

    def create_executor(self) -> 'FixedOrderScheduleExecutor':
        """
        Create a schedule executor for this schedule. This is used to execute the schedule and
        manage the cycle counters.
        """
        return FixedOrderScheduleExecutor(self)

class FixedOrderScheduleExecutor(ScheduleExecutor):
    """
    A schedule executor that executes a FixedOrderSchedule. The executor is responsible for
    executing the schedule and managing the cycle counters.
    """

    def __init__(self, schedule: FixedOrderSchedule) -> None:
        self.schedule = schedule
        self.entry_index = 0

    def next(self) -> ScheduleEntry:
        entry = self.schedule.entries[self.entry_index]
        self.entry_index += 1
        if self.entry_index >= len(self.schedule.entries):
            self.entry_index = 0
        return entry

    def wait(self) -> None:
        if self.schedule.slots == 'variable':
            time.sleep(self.schedule.delay)
        else:
            # TODO: Implement fixed slot scheduling
            # sleep based on last request length
            pass

class PriorityScheduleEntry(ScheduleEntry):
    def __init__(self, entry: ScheduleEntry, cycle: int, max_age: int) -> None:
        self.entry = entry
        self.cycle = cycle
        self.max_age = max_age

    def perform(self, master: 'LineMaster'):
        self.entry.perform(master)

class PriorityAgingSchedule(Schedule):
    """
    A schedule that executes a set of entries in order of priority.

    Similar to the FixedOrderSchedule the slots are either fixed or variable. The schedule is
    executed in a loop, with a delay between each entry.

    Each entry has a priority, this is set by the cycle value, a lower cycle value means a higher
    priority. For every slot a cycle counter for each entry is decremented, when the counter is
    higher or equal to the cycle value of the entry then the entry is executed and the cycle counter
    is reset.

    Every entry also has a maximum age, if any of the entries has a cycle counter higher than the
    maximum age then the entry is executed. This is used to prevent starvation of entries with a
    high cycle value.
    """

    def __init__(self, name: str, entries: List[PriorityScheduleEntry], slots: Literal['dynamic', 'fixed'],
                 phase: Literal['zero', 'adjusted'], reserve_slots: bool, delay: float) -> None:
        self.name = name
        self.entries = entries
        self.slots = slots
        self.phase = phase
        self.reserve_slots = reserve_slots
        self.delay = delay

    def create_executor(self) -> 'PriorityAgingScheduleExecutor':
        """
        Create a schedule executor for this schedule. This is used to execute the schedule and
        manage the cycle counters.
        """
        return PriorityAgingScheduleExecutor(self)

class PriorityAgingScheduleExecutor(ScheduleExecutor):
    """
    A schedule executor that executes a PriorityAgingSchedule. The executor is responsible for
    executing the schedule and managing the cycle counters.
    """

    def __init__(self, schedule: PriorityAgingSchedule) -> None:
        self.schedule = schedule
        if schedule.phase == 'zero':
            self.cycle_counters = [0] * len(schedule.entries)
        elif schedule.phase == 'adjusted':
            self.cycle_counters = [entry.cycle / 2 for entry in schedule.entries]
    
    def next(self) -> ScheduleEntry:
        # Increment all cycle counters
        for i in range(len(self.schedule.entries)):
            self.cycle_counters[i] += 1

        # Check if any entry has a cycle counter higher than the maximum age
        for i in range(len(self.schedule.entries)):
            if self.cycle_counters[i] >= self.schedule.entries[i].max_age:
                # Reset the cycle counter and return the entry
                self.cycle_counters[i] = 0
                return self.schedule.entries[i].entry
            
        # Check if any entry has a cycle counter higher than the cycle value
        for i in range(len(self.schedule.entries)):
            if self.cycle_counters[i] >= self.schedule.entries[i].cycle:
                # Reset the cycle counter and return the entry
                self.cycle_counters[i] = 0
                return self.schedule.entries[i].entry

        return None

    def wait(self) -> None:
        if self.schedule.slots == 'variable':
            time.sleep(self.schedule.delay)
        else:
            # TODO: Implement fixed slot scheduling
            # sleep based on last request length
            pass
