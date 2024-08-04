from typing import List
from types import SimpleNamespace
from .transport import LineTransportListener
from ..network.nodes import Node
from .constants import *

class VirtualBus(LineTransportListener):
    """
    VirtualBus shares a transport channel with multiple listeners.

    Every request is forwarded to all participants which then decide whether they're going to
    respond to it. In case multiple peripherals would try to respond a bus contention error is
    sent to all nodes.
    """

    def __init__(self) -> None:
        self.listeners = []

    def add(self, listener: LineTransportListener):
        self.listeners.append(listener)

    # TODO: function to temporarily connect/disconnect nodes

    def on_request(self, request: int) -> List[int]:
        response = None
        for listener in self.listeners:
            r = listener.on_request(request)

            if r != None and response != None:
                # TODO: notify of error rather than exception
                raise RuntimeError('Bus contention')
            
            response = r

        return response

    def on_request_complete(self, request: int, data: List[int]):
        for listener in self.listeners:
            listener.on_request_complete(request, data)

    def on_error(self, error_type: str):
        for listener in self.listeners:
            listener.on_error(error_type)

class SimulatedPeripheral(LineTransportListener):

    def __init__(self, node: Node) -> None:
        self.node = node
        self.address = node.address
        self.signals = SimpleNamespace()

        for request in node.publishes:
            for signal in request.signals:
                self.signals.__setattr__(signal.name, signal.initial)

    def on_request(self, request: int) -> List[int]:
        # TODO: if publishing request then respond with encoded frame
        for x in self.node.publishes:
            if x.id == request:
                return x.encode(vars(self.signals))

        # Diagnostics
        if self.address == LINE_DIAG_UNICAST_UNASSIGNED_ID:
            return None
        if request == LINE_DIAG_REQUEST_OP_STATUS | self.address:
            status = self.get_operation_status()
            if status:
                return [status]
            else:
                return None
        elif request == LINE_DIAG_REQUEST_SERIAL_NUMBER | self.address:
            serial_number = self.get_serial_number()
            if serial_number:
                return list(int.to_bytes(serial_number, 4, 'little'))
            else:
                return None
        # TODO: sw number support
        # TODO: power status support
        
        return None
    
    def on_error(self, error_type: str):
        pass

    def on_request_complete(self, request: int, data: List[int]):
        # TODO: if subscribed to request then update the signals
        for s in self.node.subscribes:
            if s.id == request:
                signals = s.decode(data)
                self.on_subscriber_event(signals)

        if request == LINE_DIAG_REQUEST_WAKEUP:
            self.on_wakeup()
        elif request == LINE_DIAG_REQUEST_IDLE:
            self.on_idle()
        elif request == LINE_DIAG_REQUEST_SHUTDOWN:
            self.on_shutdown()
        elif request == LINE_DIAG_REQUEST_COND_CHANGE_ADDRESS:
            target = int.from_bytes(data[0:4], 3)
            if self.get_serial_number() == target:
                old = self.address
                self.address = target[4]
                self.on_conditional_change_address(old, self.address)
            elif self.address == target[4]:
                self.address = LINE_DIAG_UNICAST_UNASSIGNED_ID
                # TODO: callout unassign

    def get_operation_status(self):
        return LINE_DIAG_OP_STATUS_OK

    def get_serial_number(self):
        return 0xDEADBEEF

    def get_software_version(self):
        pass

    def on_subscriber_event(self, signals):
        pass

    def on_wakeup(self):
        pass

    def on_idle(self):
        pass

    def on_shutdown(self):
        pass

    def on_conditional_change_address(self, old: int, new: int):
        pass
