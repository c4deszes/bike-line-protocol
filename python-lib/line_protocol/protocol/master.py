from typing import Union, Literal, List
from ..network.schedule import Schedule
from .constants import *
from threading import Event, Thread
from queue import Queue, Empty
from dataclasses import dataclass
from .transport import LineSerialTransport
import time
from ..network import Network, Request
from .util import op_status, OperationStatus

@dataclass
class PowerStatus():
    voltage: int
    op_current: int
    sleep_current: int

@dataclass
class NodeStatus():
    op_status: OperationStatus
    power_status: PowerStatus
    serial_number: int
    software_version: str

@dataclass
class RxFrame():
    request: int

@dataclass
class TxFrame():
    request: int
    data: List[int]
    checksum: int

@dataclass
class TransmitEvent():
    frame: TxFrame | RxFrame
    event_id: int
    event: Event
    # TODO: add response, timestamp, signals, exceptions
    response: List[int]
    timestamp: float
    exception: Exception

    def __init__(self, frame: TxFrame | RxFrame, event_id: int, event: Event) -> None:
        self.frame = frame
        self.event_id = event_id
        self.event = event
        self.response = []
        self.timestamp = None
        self.exception = None

class MasterFrame:
    def __init__(self, request: Request) -> None:
        self.enabled = True
        self.request = request
        self.signals = {signal.name: signal.initial for signal in request.signals}

class PeripheralFrame:
    def __init__(self, request: Request) -> None:
        self.request = request
        self.signals = {signal.name: signal.initial for signal in request.signals}

class LineMaster():

    def __init__(self, transport: 'LineSerialTransport', network: 'Network' = None) -> None:
        self.transport = transport
        self.network = network
        self._queue = Queue(100)
        self._event_id = 0
        self._running = False

        self._schedule_thread = None
        self._schedule_running = False
        self._active_schedule = None
    
    def setup(self):
        self.master_frames = {}
        for request in self.network.master.publishes:
            self.master_frames[request.id] = MasterFrame(request)

        self.peripheral_frames = {}
        for request in self.network.requests:
            if request not in self.network.master.publishes:
                self.peripheral_frames[request.id] = PeripheralFrame(request)

        self.nodes = [NodeStatus(None, None, None, None) for _ in range(0, LINE_DIAG_UNICAST_BROADCAST_ID-1)]

    def __enter__(self):
        self.setup()

        self._running = True
        self._thread = Thread(target=self.run)
        self._thread.start()
        return self

    def _schedule_frame(self, frame: RxFrame | TxFrame) -> TransmitEvent:
        event = TransmitEvent(frame, self._event_id, Event())
        self._queue.put(event)
        self._event_id += 1 # TODO: thread safety
        return event

    def _process_response(self, request: int, data: List[int]) -> None:
        if (request & LINE_DIAG_UNICAST_REQUEST_ID_MASK) == LINE_DIAG_REQUEST_OP_STATUS:
            self.nodes[request & LINE_DIAG_UNICAST_ID_MASK].op_status = op_status(data[0])
        elif (request & LINE_DIAG_UNICAST_REQUEST_ID_MASK) == LINE_DIAG_REQUEST_POWER_STATUS:
            # TODO: update format
            pass
            #self.nodes[request & LINE_DIAG_UNICAST_ID_MASK].power_status = PowerStatus(data[0], data[1], data[2])
        elif (request & LINE_DIAG_UNICAST_REQUEST_ID_MASK) == LINE_DIAG_REQUEST_SERIAL_NUMBER:
            self.nodes[request & LINE_DIAG_UNICAST_ID_MASK].serial_number = data[0:3]
        elif (request & LINE_DIAG_UNICAST_REQUEST_ID_MASK) == LINE_DIAG_REQUEST_SW_NUMBER:
            self.nodes[request & LINE_DIAG_UNICAST_ID_MASK].software_version = f"{data[0]}.{data[1]}.{data[2]}"

    def run(self):
        while self._running:
            try:
                event = self._queue.get(timeout=1)
                if isinstance(event.frame, TxFrame):
                    self.transport.send_data(event.frame.request, event.frame.data, event.frame.checksum)
                    event.event.set()
                else:
                    if event.frame.request in self.master_frames:
                        # TODO: encode raw instead
                        data = self.master_frames[event.frame.request].request.encode(self.master_frames[event.frame.request].signals)
                        self.transport.send_data(event.frame.request, data)
                    else:
                        try:
                            response = self.transport.request_data(event.frame.request)
                            event.response = response
                            self._process_response(event.frame.request, response)
                            event.timestamp = time.time()
                        except Exception as e:
                            event.exception = e
                            event.timestamp = time.time()
                    event.event.set()
            except Empty as exc:
                pass

    def scheduler(self):
        entry_cnt = 0
        while self._schedule_running:
            self._active_schedule.entries[entry_cnt].perform(self)
            time.sleep(self._active_schedule.delay)
            entry_cnt += 1
            if entry_cnt >= len(self._active_schedule.entries):
                entry_cnt = 0

    def __exit__(self, exc_type, exc_value, traceback):
        if self._schedule_running:
            self.disable_schedule()

        self._running = False
        self._thread.join()

    # Schedule commands
    def enable_schedule(self, schedule: Union[str, Schedule]):
        if self._schedule_running:
            self.disable_schedule()

        if isinstance(schedule, str):
            schedule = self.network.get_schedule(schedule)
        self._schedule_running = True
        self._active_schedule = schedule
        self._schedule_thread = Thread(target=self.scheduler)
        self._schedule_thread.start()

    def disable_schedule(self):
        if self._schedule_running:
            self._schedule_running = False
            self._schedule_thread.join()

    # Signal control
    def set_signal(self, request: Union[int, str], signal: str, value: int):
        if isinstance(request, str):
            request = self.network.get_request(request).id
        self.master_frames[request].signals[signal] = value

    # Node control
    def get_node_status(self, node: Union[int, str]) -> NodeStatus:
        """
        Returns the status of a node, the node parameter may be either the node address or
        the node name.

        Example:
        >>> master.get_node_status(0x01)
        NodeStatus(op_status='init', power_status=PowerStatus(voltage=12.0, op_current=0, sleep_current=100), serial_number=0, software_version='0.0.0')

        :param node: Node address or name
        :type node: Union[int, str]
        :return: Node status
        :rtype: NodeStatus
        """
        if isinstance(node, str):
            node = self.network.get_node(node).address
        return self.nodes[node]

    # Frame insertion
    def request(self, request: Union[int, str], wait: bool = False, timeout: float = None) -> List[int]:
        if isinstance(request, str):
            request = self.network.get_request(request).id
        event = self._schedule_frame(RxFrame(request))
        if wait:
            event.event.wait(timeout)
            if event.exception:
                raise event.exception
            # TODO: anything we want to do with the timestamp?
            return event.response

    def send_request(self, request: int, data: List[int], checksum: int = None, wait: bool = False, timeout: float = None) -> None:
        event = self._schedule_frame(TxFrame(request, data, checksum))
        if wait:
            event.event.wait(timeout)

    # Broadcast commands
    def wakeup(self, wait: bool = False, timeout: float = None) -> None:
        event = self._schedule_frame(TxFrame(LINE_DIAG_REQUEST_WAKEUP, [], None))
        if wait:
           event.event.wait(timeout)

    def idle(self, wait: bool = False, timeout: float = None) -> None:
        event = self._schedule_frame(TxFrame(LINE_DIAG_REQUEST_IDLE, [], None))
        if wait:
           event.event.wait(timeout)

    def shutdown(self, wait: bool = False, timeout: float = None) -> None:
        event = self._schedule_frame(TxFrame(LINE_DIAG_REQUEST_SHUTDOWN, [], None))
        if wait:
           event.event.wait(timeout)

    # Diagnostic unicast commands
    def conditional_change_address(self, serial: int, new_address: int, wait=True, timeout=1):
        event = self._schedule_frame(TxFrame(LINE_DIAG_REQUEST_COND_CHANGE_ADDRESS,
                                             list(serial.to_bytes(4, 'little')) + [new_address], None))
        if wait:
           event.event.wait(timeout)

    def get_operation_status(self, node: Union[int, str], wait=True, timeout: float=1) -> OperationStatus:
        """
        Returns the operation status of a node, the node parameter may be either the node address
        or the node name.

        By default the function waits for the response and it will either return the operation status
        or raise an exception if the node did not respond.

        :param node: Node address or name
        :type node: Union[int, str]
        :param wait: When enabled waits for a response, defaults to True
        :type wait: bool, optional
        :param timeout: Time to wait for a response, defaults to 1sec
        :type timeout: float, optional
        :raises event.exception: If an error occurs during the request
        :return: Node's operation status
        :rtype: OperationStatus
        """
        if isinstance(node, str):
            node = self.network.get_node(node).address
        event = self._schedule_frame(RxFrame(LINE_DIAG_REQUEST_OP_STATUS | node))
        if wait:
            event.event.wait(timeout)
            if event.exception:
                raise event.exception
            return self.nodes[node].op_status
        return None

    def get_power_status(self, node: Union[int, str], wait=True, timeout=1) -> PowerStatus:
        """
        Returns the power status of a node, the node parameter may be either the node address
        or the node name.

        By default the function waits for the response and it will either return the power status
        or raise an exception if the node did not respond.

        :param node: Node address or name
        :type node: Union[int, str]
        :param wait: When enabled waits for a response, defaults to True
        :type wait: bool, optional
        :param timeout: Time to wait for a response, defaults to 1
        :type timeout: int, optional
        :raises event.exception: If an error occurs during the request
        :return: Node's power status
        :rtype: PowerStatus
        """
        if isinstance(node, str):
            node = self.network.get_node(node).address
        event = self._schedule_frame(RxFrame(LINE_DIAG_REQUEST_POWER_STATUS | node))
        if wait:
            event.event.wait(timeout)
            if event.exception:
                raise event.exception
            return self.nodes[node].power_status
        return None

    def get_serial_number(self, node: Union[int, str], wait=True, timeout=1) -> int:
        """
        Returns the serial number of a node, the node parameter may be either the node address or
        the node name.

        By default the function waits for the response and it will either return the serial number
        or raise an exception if the node did not respond.

        :param node: Node address or name
        :type node: Union[int, str]
        :param wait: When enabled waits for a response, defaults to True
        :type wait: bool, optional
        :param timeout: Time to wait for a response, defaults to 1
        :type timeout: int, optional
        :raises event.exception: If an error occurs during the request
        :return: Serial number
        :rtype: int
        """
        if isinstance(node, str):
            node = self.network.get_node(node).address
        event = self._schedule_frame(RxFrame(LINE_DIAG_REQUEST_SERIAL_NUMBER | node))
        if wait:
            event.event.wait(timeout)
            if event.exception:
                raise event.exception
            return self.nodes[node].serial_number
        return None

    def get_software_version(self, node: Union[int, str], wait=True, timeout=1) -> str:
        """
        Returns the software version of a node, the node parameter may be either the node address
        or the node name.

        :param node: Node address or name
        :type node: Union[int, str]
        :param wait: When enabled waits for a response, defaults to True
        :type wait: bool, optional
        :param timeout: Time to wait for a response, defaults to 1
        :type timeout: int, optional
        :raises event.exception: If an error occurs during the request
        :return: Software version
        :rtype: str
        """
        if isinstance(node, str):
            node = self.network.get_node(node).address
        event = self._schedule_frame(RxFrame(LINE_DIAG_REQUEST_SW_NUMBER | node))
        if wait:
            event.event.wait(timeout)
            if event.exception:
                raise event.exception
            return self.nodes[node].software_version
        return None