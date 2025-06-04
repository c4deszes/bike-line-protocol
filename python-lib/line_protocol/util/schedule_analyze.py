from unittest.mock import patch
import time
from typing import Union
from line_protocol.network import Schedule

class ScheduleAnalysisResult:
    initial_delay: float
    minimum_delay: float
    maximum_delay: float
    average_delay: float
    count: int

def analyze_schedule(network, schedule: Union[str, Schedule], cycles):
    """
    """
    timestamp = 0

    request_data = {

    }

    class FakeLineMaster:

        def __init__(self, network):
            self._network = network

        def request(self, request, *args, **kwargs):
            nonlocal timestamp
            nonlocal request_data

            body = network.get_request(request)

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
            pass

        def idle(self):
            pass

        def shutdown(self):
            pass

        def get_operation_status(self, address):
            pass

        def get_power_status(self, address):
            pass

        def get_serial_number(self, address):
            pass

        def get_software_version(self, address):
            pass

    line_master = FakeLineMaster(network)

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

    return (request_data, timestamp)