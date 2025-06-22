from unittest.mock import patch
from dataclasses import dataclass
import time
from typing import Union
from line_protocol.network import Schedule, Network

@dataclass
class ScheduleAnalysisResult:
    initial_delay: float
    minimum_delay: float
    maximum_delay: float
    average_delay: float
    count: int

def analyze_schedule(schedule: Union[str, Schedule], cycles: int, network: Network | None = None) -> dict[str | int, ScheduleAnalysisResult]:
    timestamp = 0
    request_data = {}

    class FakeLineMaster:

        def __init__(self, network):
            self._network = network

        def request(self, request, *args, **kwargs):
            nonlocal timestamp
            nonlocal request_data

            #body = network.get_request(request)

            if request not in request_data:
                request_data[request] = {
                    'initial_delay': timestamp,
                    'last_timestamp': timestamp,
                    'min_delay': 0,
                    'max_delay': 0,
                    'total_delay': 0,
                    'count': 0
                }
            else:
                delay = timestamp - request_data[request]['last_timestamp']
                if delay < request_data[request]['min_delay'] or request_data[request]['min_delay'] == 0:
                    request_data[request]['min_delay'] = delay
                if delay > request_data[request]['max_delay']:
                    request_data[request]['max_delay'] = delay
                request_data[request]['total_delay'] += delay
                request_data[request]['count'] += 1
                request_data[request]['avg_delay'] = request_data[request]['total_delay'] / request_data[request]['count']
                request_data[request]['last_timestamp'] = timestamp

            #print("Requesting:", request, "at", timestamp)

        def wakeup(self):
            self.request('Wakeup')

        def idle(self):
            self.request('Idle')

        def shutdown(self):
            self.request('Shutdown')

        def get_operation_status(self, address):
            self.request(f'GetOperationStatus[{address}]')

        def get_power_status(self, address):
            self.request(f'GetPowerStatus[{address}]')

        def get_serial_number(self, address):
            self.request(f'GetSerialNumber[{address}]')

        def get_software_version(self, address):
            self.request(f'GetSoftwareVersion[{address}]')

    line_master = FakeLineMaster(network)

    if isinstance(schedule, str):
        if network is not None:
            schedule = network.get_schedule(schedule)
        else:
            raise ValueError("Network must be provided when schedule is a string.")

    # Mocking the function to return a fixed value for testing
    with patch('time.sleep') as sleep_mock:
        schedule_executor = schedule.create_executor()
        for x in range(cycles):
            entry = schedule_executor.next()
            if entry is not None:
                entry.perform(line_master)
                #print("Requesting:", entry, "at", timestamp)
            schedule_executor.wait()
            timestamp += sleep_mock.call_args.args[0]

    # Convert request_data to ScheduleAnalysisResult
    result = {}
    for request, data in request_data.items():
        result[request] = ScheduleAnalysisResult(
            initial_delay=data['initial_delay'],
            minimum_delay=data['min_delay'],
            maximum_delay=data['max_delay'],
            average_delay=data['avg_delay'],
            count=data['count']
        )

    return result
