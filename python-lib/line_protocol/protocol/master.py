from typing import Union, Literal, List
from ..network.schedule import Schedule
from .constants import *
from threading import Event, Thread
from queue import Queue, Empty
from dataclasses import dataclass
from .transport import LineSerialTransport, LineTransportTimeout
from .virtual_bus import VirtualBus
import time
from ..network import Network, Request
from .util import op_status_str, OperationStatus
import logging

logger = logging.getLogger(__name__)

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

    def __getitem__(self, key: str) -> int:
        return self.signals[key]
    
class RequestListener:

    def on_request(self, request: Request, signals):
        raise NotImplementedError()
    
    def on_error(self, request: Request, error_type):
        raise NotImplementedError()
    
class NodeStatusListener:

    def on_node_change(self, node: NodeStatus):
        raise NotImplementedError()

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

        self.request_listeners = []
        self.node_status_listeners = []

        self.virtual_bus = VirtualBus()

    def setup(self):
        # TODO: only have subscribed requests here?
        self.peripheral_frames = {}
        if self.network is not None:
            for request in self.network.requests:
                self.peripheral_frames[request.id] = PeripheralFrame(request)

        self.nodes = [NodeStatus(None, None, None, None) for _ in range(0, LINE_DIAG_UNICAST_BROADCAST_ID)]

    def add_request_listener(self, listener: RequestListener):
        """
        Adds a listener for request events. The listener will be called when a request is made.

        :param listener: The listener to add
        :type listener: RequestListener
        """
        self.request_listeners.append(listener)

    def add_node_status_listener(self, listener: NodeStatusListener):
        """
        Adds a listener for node status changes. The listener will be called when a node status changes.

        :param listener: The listener to add
        :type listener: NodeStatusListener
        """
        self.node_status_listeners.append(listener)

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
            self.nodes[request & LINE_DIAG_UNICAST_ID_MASK].op_status = op_status_str(data[0])
        elif (request & LINE_DIAG_UNICAST_REQUEST_ID_MASK) == LINE_DIAG_REQUEST_POWER_STATUS:
            # TODO: update format
            pass
            #self.nodes[request & LINE_DIAG_UNICAST_ID_MASK].power_status = PowerStatus(data[0], data[1], data[2])
        elif (request & LINE_DIAG_UNICAST_REQUEST_ID_MASK) == LINE_DIAG_REQUEST_SERIAL_NUMBER:
            self.nodes[request & LINE_DIAG_UNICAST_ID_MASK].serial_number = int.from_bytes(data[0:3], 'big')
        elif (request & LINE_DIAG_UNICAST_REQUEST_ID_MASK) == LINE_DIAG_REQUEST_SW_NUMBER:
            self.nodes[request & LINE_DIAG_UNICAST_ID_MASK].software_version = f"{data[0]}.{data[1]}.{data[2]}"

        if request in self.peripheral_frames:
            signals = self.peripheral_frames[request].request.decode(data)
            logger.debug(f"%s %s", request, signals)
            for listener in self.request_listeners:
                listener.on_request(self.peripheral_frames[request].request, signals)
            for signal, value in signals.items():
                self.peripheral_frames[request].signals[signal] = value

    def run(self):
        while self._running:
            try:
                event = self._queue.get(timeout=1)
                if isinstance(event.frame, TxFrame):
                    self.transport.send_data(event.frame.request, event.frame.data, event.frame.checksum)
                    
                    # TODO: handle checksum, checksum error, etc.
                    self.virtual_bus.on_request_complete(event.frame.request, event.frame.data)

                    event.event.set()
                else:
                    # 1st check if virtual bus has any response
                    #    if yes then encode and send it
                    #    if no then request data from transport

                    vbus_response = self.virtual_bus.on_request(event.frame.request)

                    if vbus_response is not None:
                        if self.transport is not None:
                            self.transport.send_data(event.frame.request, vbus_response)
                        self._process_response(event.frame.request, vbus_response)
                        self.virtual_bus.on_request_complete(event.frame.request, vbus_response)
                    else:
                        try:
                            if self.transport is not None:
                                response = self.transport.request_data(event.frame.request)
                                event.response = response
                                self._process_response(event.frame.request, response)
                                event.timestamp = time.time()
                                self.virtual_bus.on_request_complete(event.frame.request, response)

                            else:
                                raise LineTransportTimeout("Transport is not available, no vbus response.")

                        except Exception as e:
                            event.exception = e
                            event.timestamp = time.time()

                            # TODO: call with different error types
                            if event.frame.request in self.peripheral_frames:
                                for listener in self.request_listeners:
                                    listener.on_error(self.peripheral_frames[event.frame.request].request, "transport_error")
                            self.virtual_bus.on_error("transport_error")
                    event.event.set()
            except Empty as exc:
                pass

    def scheduler(self):
        while self._schedule_running:
            entry = self._active_schedule.next()
            if entry is not None:
                entry.perform(self)
            self._active_schedule.wait()

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
        self._active_schedule = schedule.create_executor()
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