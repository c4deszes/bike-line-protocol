import time
import logging

from typing import Union, Dict, List
from threading import Event, Thread
from queue import Queue, Empty
from enum import Enum
from dataclasses import dataclass

from line_protocol.protocol.constants import *
from line_protocol.protocol.transport import LineSerialTransport, LineTransportTimeout
from line_protocol.protocol.virtual_bus import VirtualBus
from line_protocol.network import (Network, Request, SignalValueContainer, SignalValue, NodeRef,
                                   ScheduleExecutor, Schedule)
from line_protocol.protocol.util import op_status_str, OperationStatus

logger = logging.getLogger(__name__)

@dataclass
class PowerStatus():
    voltage: float
    op_current: float
    sleep_current: float

@dataclass
class NodeStatus():
    op_status: OperationStatus | None
    power_status: PowerStatus | None
    serial_number: int | None
    software_version: str | None

@dataclass
class RxRequest():
    request: int

@dataclass
class TxRequest():
    request: int
    data: List[int]
    checksum: int | None = None

@dataclass
class TransmitEvent():
    frame: TxRequest | RxRequest
    event_id: int
    event: Event

    timestamp: float | None
    response: List[int] | None
    signals: SignalValueContainer | None
    exception: Exception | None

    def __init__(self, frame: TxRequest | RxRequest, event_id: int, event: Event) -> None:
        self.frame = frame
        self.event_id = event_id
        self.event = event
        self.timestamp = None
        self.response = None
        self.signals = None
        self.exception = None

class NodeStatusProperty(Enum):
    OP_STATUS = "op_status"
    POWER_STATUS = "power_status"
    SERIAL_NUMBER = "serial_number"
    SOFTWARE_VERSION = "software_version"

    def __str__(self):
        return self.value

class UserRequest:
    """
    Used to buffer responses to user requests
    """

    def __init__(self, request: Request) -> None:
        self.last_timestamp: float | None = None
        self.request = request
        self.exception: Exception | None = None
        # TODO: set phy and raw values to initial values
        self.signals = SignalValueContainer([SignalValue(signal, signal.initial, 0) for signal in request.signals])

    def reset(self):
        """
        Resets the request to its initial state.
        """
        self.last_timestamp = None
        # TODO: set phy and raw values to initial values
        self.signals = SignalValueContainer([SignalValue(signal, signal.initial, 0) for signal in self.request.signals])
    
class RequestListener:
    """
    Interface for request listeners. The listener will be called when a request is made or an error
    occurs. It should implement the on_request and on_error methods.
    """

    def on_user_request(self, timestamp: float, request: Request, signals: SignalValueContainer) -> None:
        """
        Called when a request is made. The listener should process the request and signals.

        :param timestamp: Timestamp of the request
        :type timestamp: float
        :param request: The request that was made
        :type request: Request
        :param signals: Signals that were received with the request
        :type signals: SignalValueContainer
        """
        raise NotImplementedError()

    # TODO: standardize error types
    def on_error(self, timestamp: float, request: Request, error_type):
        """
        Called when an error occurs during the request. The listener should handle the error.
        :param timestamp: Timestamp of the error
        :type timestamp: float
        :param request: The request that caused the error
        :type request: Request
        :param error_type: Type of the error, e.g. 'transport_error', 'checksum_error', etc.
        :type error_type: str
        """
        raise NotImplementedError()
    
class NodeStatusListener:
    """
    Interface for node status listeners. The listener will be called when a node status changes.
    It should implement the on_node_change method.
    """

    def on_node_change(self, timestamp: float, ref: NodeRef, node: NodeStatus,
                       property: NodeStatusProperty) -> None:
        """
        Called when a response is received to the standard diagnostic requests, such as
        get_operation_status, the callback receives when the request was made, the node that changed
        and the property that changed.

        :param timestamp: Timestamp of the node status change
        :type timestamp: float
        :param ref: Reference to the node that changed
        :type ref: NodeRef
        :param node: Node status that changed
        :type node: NodeStatus
        :param property: The property that changed, e.g. op_status, power_status, serial_number, software_version
        :type property: NodeStatusProperty
        """
        raise NotImplementedError()

class LineMaster():

    def __init__(self, transport: 'LineSerialTransport', network: 'Network | None' = None) -> None:
        self.transport = transport
        self.network = network
        self.virtual_bus = VirtualBus()
        # Master thread
        self._queue: 'Queue[TransmitEvent]' = Queue(maxsize=0)
        self._event_id = 0
        self._running = False

        # Schedule thread
        self._schedule_running: bool = False
        self._schedule_thread: Thread | None = None
        self._active_schedule: ScheduleExecutor | None = None

        # Status buffers
        self._user_requests: Dict[int, UserRequest] = {}
        self._node_status: Dict[int, NodeStatus] = {}

        # Listeners
        self.request_listeners: List[RequestListener] = []
        self.node_status_listeners: List[NodeStatusListener] = []

    def reset_user_requests(self):
        """
        Resets all user requests to their initial state. This is useful when the master is restarted
        or when the network configuration changes.
        """
        for request in self._user_requests.values():
            request.reset()

    def reset_nodestatus(self):
        """
        Resets all node statuses to their initial state. This is useful when the master is restarted
        or when the network configuration changes.
        """
        for node in self._node_status.values():
            node.op_status = None
            node.power_status = None
            node.serial_number = None
            node.software_version = None

        # Notify all listeners that the node statuses have been reset
        for node_id, node_status in self._node_status.items():
            for listener in self.node_status_listeners:
                listener.on_node_change(time.time(), NodeRef("Unset", node_id), node_status, NodeStatusProperty.OP_STATUS)
                listener.on_node_change(time.time(), NodeRef("Unset", node_id), node_status, NodeStatusProperty.POWER_STATUS)
                listener.on_node_change(time.time(), NodeRef("Unset", node_id), node_status, NodeStatusProperty.SERIAL_NUMBER)
                listener.on_node_change(time.time(), NodeRef("Unset", node_id), node_status, NodeStatusProperty.SOFTWARE_VERSION)

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

    def _setup(self):
        if self.network is not None:
            for request in self.network.requests:
                self._user_requests[request.id] = UserRequest(request)

        self._node_status = {x: NodeStatus(None, None, None, None) for x in range(0, LINE_DIAG_UNICAST_BROADCAST_ID)}

    def __enter__(self):
        self._setup()

        self._running = True
        self._thread = Thread(target=self.run)
        self._thread.start()
        return self

    def _process_diagnostic_request(self, request: int, data: List[int]) -> None:
        """
        Processes a diagnostic request and updates the node status accordingly.
        This method is called when a diagnostic request is received from the transport layer.
        """
        # TODO: resolve node name
        if (request & LINE_DIAG_UNICAST_REQUEST_ID_MASK) == LINE_DIAG_REQUEST_OP_STATUS:
            node_id = request & LINE_DIAG_UNICAST_ID_MASK
            self._node_status[node_id].op_status = op_status_str(data[0])
            for listener in self.node_status_listeners:
                listener.on_node_change(time.time(), NodeRef("Unset", node_id), self._node_status[node_id], NodeStatusProperty.OP_STATUS)
        elif (request & LINE_DIAG_UNICAST_REQUEST_ID_MASK) == LINE_DIAG_REQUEST_POWER_STATUS:
            node_id = request & LINE_DIAG_UNICAST_ID_MASK
            self._node_status[node_id].power_status = PowerStatus(data[0] / 10.0, data[1], data[2])
            for listener in self.node_status_listeners: 
                listener.on_node_change(time.time(), NodeRef("Unset", node_id), self._node_status[node_id], NodeStatusProperty.POWER_STATUS)
        elif (request & LINE_DIAG_UNICAST_REQUEST_ID_MASK) == LINE_DIAG_REQUEST_SERIAL_NUMBER:
            node_id = request & LINE_DIAG_UNICAST_ID_MASK
            self._node_status[node_id].serial_number = int.from_bytes(data[0:3], 'big')
            for listener in self.node_status_listeners:
                listener.on_node_change(time.time(), NodeRef("Unset", node_id), self._node_status[node_id], NodeStatusProperty.SERIAL_NUMBER)
        elif (request & LINE_DIAG_UNICAST_REQUEST_ID_MASK) == LINE_DIAG_REQUEST_SW_NUMBER:
            node_id = request & LINE_DIAG_UNICAST_ID_MASK
            self._node_status[node_id].software_version = f"{data[0]}.{data[1]}.{data[2]}"
            for listener in self.node_status_listeners:
                listener.on_node_change(time.time(), NodeRef("Unset", node_id), self._node_status[node_id], NodeStatusProperty.SOFTWARE_VERSION)

    def _process_user_request(self, timestamp: float, request: int, data: List[int]) -> None:
        if request in self._user_requests:
            signals = self._user_requests[request].request.decode(data)
            self._user_requests[request].signals = signals
            self._user_requests[request].last_timestamp = timestamp

    def _process_user_request_error(self, timestamp: float, request: int, exception: Exception) -> None:
        if request in self._user_requests:
            self._user_requests[request].exception = exception
            self._user_requests[request].last_timestamp = timestamp

    def _do_transmit(self, event: TransmitEvent) -> None:
        timestamp = time.time()

        # Send the data on the transport layer
        if self.transport is not None:
            self.transport.send_data(event.frame.request, event.frame.data, event.frame.checksum)

        # TODO: process the response
        # e.g. if the request is a peripheral request then decode it and notify listeners

        self.virtual_bus.on_request_complete(event.frame.request, event.frame.data)

        # Notify the listeners that the request was made
        # TODO: implement

        event.timestamp = timestamp
        #event.response = ??
        #event.signals = ??
        #event.exception = ??
        event.event.set()

    def _do_receive(self, event: TransmitEvent) -> None:
        vbus_response = self.virtual_bus.on_request(event.frame.request)

        if vbus_response is not None:
            timestamp = time.time()
            # If the virtual bus has a response then send that over the transport
            if self.transport is not None:
                self.transport.send_data(event.frame.request, vbus_response)
            
            # Process the response
            self._process_diagnostic_request(event.frame.request, vbus_response)
            self._process_user_request(timestamp, event.frame.request, vbus_response)
            
            # Notify every virtual bus member that the request is complete
            self.virtual_bus.on_request_complete(event.frame.request, vbus_response)

            # Notify the listeners that the request was made
            if event.frame.request in self._user_requests:
                for listener in self.request_listeners:
                    listener.on_user_request(timestamp, self._user_requests[event.frame.request].request,
                                             self._user_requests[event.frame.request].signals)

            event.timestamp = timestamp
            event.response = vbus_response
            # event.signals = ??
            # event.exception = None
            event.event.set()
        else:
            timestamp = time.time()
            try:
                if self.transport is not None:
                    # Send the request on the transport layer
                    response = self.transport.request_data(event.frame.request)

                    # Process the response
                    self._process_diagnostic_request(event.frame.request, response)
                    self._process_user_request(timestamp, event.frame.request, response)

                    # Notify every virtual bus member that the request is complete
                    self.virtual_bus.on_request_complete(event.frame.request, response)

                    # Notify the listeners that the request was made
                    if event.frame.request in self._user_requests:
                        for listener in self.request_listeners:
                            listener.on_user_request(timestamp, self._user_requests[event.frame.request].request,
                                                     self._user_requests[event.frame.request].signals)

                    event.response = response
                else:
                    raise LineTransportTimeout("No bus response.")

            except Exception as e:
                event.exception = e

                # Notify the virtual bus of the error
                self.virtual_bus.on_error(event.frame.request, "transport_error")

                self._process_user_request_error(timestamp, event.frame.request, e)

                # Notify the listeners of the error
                if event.frame.request in self._user_requests:
                    for listener in self.request_listeners:
                        listener.on_error(timestamp, self._user_requests[event.frame.request].request, "transport_error")

            event.timestamp = time.time()
            event.event.set()

    def run(self):
        while self._running:
            try:
                event = self._queue.get(timeout=1)
                if isinstance(event.frame, TxRequest):
                    self._do_transmit(event)
                else:
                    self._do_receive(event)
            except Empty as exc:
                pass

    def __exit__(self, exc_type, exc_value, traceback):
        if self._schedule_running:
            self.disable_schedule()

        self._running = False
        self._thread.join()

    # Schedule commands
    def _schedule_frame(self, frame: RxRequest | TxRequest) -> TransmitEvent:
        event = TransmitEvent(frame, self._event_id, Event())
        self._queue.put(event)
        self._event_id += 1 # TODO: thread safety
        return event

    def _scheduler(self):
        while self._schedule_running:
            entry = self._active_schedule.next()
            if entry is not None:
                entry.perform(self)
            self._active_schedule.wait()

    def enable_schedule(self, schedule: Union[str, Schedule]):
        """
        Starts the schedule and runs it in a separate thread. The schedule can be either a string
        representing the schedule name or a Schedule object. If a string is provided, it will be
        resolved to a Schedule object from the network.

        :param schedule: The schedule to run, can be a string or a Schedule object
        :type schedule: Union[str, Schedule]
        """
        if self._schedule_running:
            self.disable_schedule()

        if isinstance(schedule, str):
            if self.network is None:
                raise ValueError("Network is not set, cannot resolve schedule by name.")
            schedule = self.network.get_schedule(schedule)
        self._schedule_running = True
        self._active_schedule = schedule.create_executor()
        self._schedule_thread = Thread(target=self._scheduler)
        self._schedule_thread.start()

    def disable_schedule(self):
        """
        Stops the schedule and waits for the schedule thread to finish.
        """
        if self._schedule_running and self._schedule_thread is not None:
            self._schedule_running = False
            self._schedule_thread.join()

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
            if self.network is None:
                raise ValueError("Network is not set, cannot resolve node by name.")
            node = self.network.get_node(node).address
        return self._node_status[node]

    # Frame insertion
    def request(self, request: Union[int, str], wait: bool = False, timeout: float | None = None) -> List[int] | None:
        """
        Sends a request to the bus and waits for a response. The request can be either an integer
        representing the request code or a string representing the request name. If the request is
        a string, it will be resolved to the corresponding request code from the network.

        :param request: The request to send
        :type request: Union[int, str]
        :param wait: Whether to wait for a response, defaults to False
        :type wait: bool, optional
        :param timeout: Time to wait for a response, defaults to None
        :type timeout: float | None, optional
        :raises event.exception: If an error occurs during the request
        :return: The response from the bus or None if not waiting
        :rtype: List[int] | None
        """
        if isinstance(request, str):
            if self.network is None:
                raise ValueError("Network is not set, cannot resolve request by name.")
            request = self.network.get_request(request).id

        event = self._schedule_frame(RxRequest(request))

        if wait:
            event.event.wait(timeout)
            if event.exception:
                raise event.exception
            return event.response

        return None

    def send_request(self, request: int, data: List[int], checksum: int | None = None,
                     wait: bool = False, timeout: float | None = None) -> None:
        """
        Sends a request to the bus with the specified data and checksum. The request is scheduled
        and can be waited for a response. If wait is True, the method will block until the response
        is received or the timeout is reached.

        The primary use of this method is to send requests by the diagnostics extensions.

        :param request: The request code to send
        :type request: int
        :param data: Data to send with the request
        :type data: List[int]
        :param checksum: Checksum value, defaults to None in which case the checksum is calculated
        :type checksum: int, optional
        :param wait: Wait for the transmission to complete, defaults to False
        :type wait: bool, optional
        :param timeout: Time to wait for a response, defaults to None
        :type timeout: float, optional
        """
        event = self._schedule_frame(TxRequest(request, data, checksum))
        if wait:
            event.event.wait(timeout)

    # Broadcast commands
    def wakeup(self, wait: bool = False, timeout: float | None = None) -> None:
        """
        Sends a wakeup request to all nodes on the bus. This is used to wake up the nodes from sleep mode.

        :param wait: Whether to wait for a response, defaults to False
        :type wait: bool, optional
        :param timeout: Time to wait for a response, defaults to None
        :type timeout: float | None, optional
        """
        event = self._schedule_frame(TxRequest(LINE_DIAG_REQUEST_WAKEUP, [], None))
        if wait:
           event.event.wait(timeout)

    def idle(self, wait: bool = False, timeout: float | None = None) -> None:
        """
        Sends an idle request to all nodes on the bus. This is used to put the nodes into idle mode.

        :param wait: Whether to wait for a response, defaults to False
        :type wait: bool, optional
        :param timeout: Time to wait for a response, defaults to None
        :type timeout: float | None, optional
        """
        event = self._schedule_frame(TxRequest(LINE_DIAG_REQUEST_IDLE, [], None))
        if wait:
           event.event.wait(timeout)

    def shutdown(self, wait: bool = False, timeout: float | None = None) -> None:
        """
        Sends a shutdown request to all nodes on the bus. This is used to shut down the nodes.

        :param wait: Whether to wait for a response, defaults to False
        :type wait: bool, optional
        :param timeout: Time to wait for a response, defaults to None
        :type timeout: float | None, optional
        """
        event = self._schedule_frame(TxRequest(LINE_DIAG_REQUEST_SHUTDOWN, [], None))
        if wait:
           event.event.wait(timeout)

    # Diagnostic unicast commands
    def conditional_change_address(self, serial: int, new_address: int, wait=True, timeout=1):
        """
        Sends a conditional change address request to a node with the specified serial number.

        :param serial: The serial number of the node
        :type serial: int
        :param new_address: The new address to assign to the node
        :type new_address: int
        :param wait: Whether to wait for a response, defaults to True
        :type wait: bool, optional
        :param timeout: Time to wait for a response, defaults to 1
        :type timeout: int, optional
        """
        event = self._schedule_frame(TxRequest(LINE_DIAG_REQUEST_COND_CHANGE_ADDRESS,
                                             list(serial.to_bytes(4, 'little')) + [new_address], None))
        if wait:
           event.event.wait(timeout)

    def get_operation_status(self, node: Union[int, str], wait=True, timeout: float=1) -> OperationStatus | None:
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
            if self.network is None:
                raise ValueError("Network is not set, cannot resolve node by name.")
            node = self.network.get_node(node).address
        event = self._schedule_frame(RxRequest(LINE_DIAG_REQUEST_OP_STATUS | node))
        if wait:
            event.event.wait(timeout)
            if event.exception:
                raise event.exception
            return self._node_status[node].op_status
        return None

    def get_power_status(self, node: Union[int, str], wait=True, timeout=1) -> PowerStatus | None:
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
            if self.network is None:
                raise ValueError("Network is not set, cannot resolve node by name.")
            node = self.network.get_node(node).address
        event = self._schedule_frame(RxRequest(LINE_DIAG_REQUEST_POWER_STATUS | node))
        if wait:
            event.event.wait(timeout)
            if event.exception:
                raise event.exception
            return self._node_status[node].power_status
        return None

    def get_serial_number(self, node: Union[int, str], wait=True, timeout=1) -> int | None:
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
            if self.network is None:
                raise ValueError("Network is not set, cannot resolve node by name.")
            node = self.network.get_node(node).address
        event = self._schedule_frame(RxRequest(LINE_DIAG_REQUEST_SERIAL_NUMBER | node))
        if wait:
            event.event.wait(timeout)
            if event.exception:
                raise event.exception
            return self._node_status[node].serial_number
        return None

    def get_software_version(self, node: Union[int, str], wait=True, timeout=1) -> str | None:
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
            if self.network is None:
                raise ValueError("Network is not set, cannot resolve node by name.")
            node = self.network.get_node(node).address
        event = self._schedule_frame(RxRequest(LINE_DIAG_REQUEST_SW_NUMBER | node))
        if wait:
            event.event.wait(timeout)
            if event.exception:
                raise event.exception
            return self._node_status[node].software_version
        return None
