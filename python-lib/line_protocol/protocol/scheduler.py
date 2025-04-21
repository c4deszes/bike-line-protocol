
class Scheduler:

    def step(self, master: 'LineMaster') -> None:
        raise NotImplementedError()
    
class FixedOrderScheduler:

    def __init__(self, entries: List[ScheduleEntry],
                 interframe_delay: float, reserve_slots: bool, reserve_response: bool) -> None:
        pass

    def step(self, master: 'LineMaster') -> None:
        pass