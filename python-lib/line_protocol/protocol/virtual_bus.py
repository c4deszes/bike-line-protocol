import logging
from typing import List, Union, TYPE_CHECKING, Dict
from types import SimpleNamespace
from dataclasses import dataclass

from line_protocol.protocol.transport import LineTransportListener
from line_protocol.protocol.util import op_status_code, op_status_str, sw_version_str
from line_protocol.network.nodes import Node
from line_protocol.protocol.constants import *
from line_protocol.network import Request

if TYPE_CHECKING:
    from .master import PowerStatus

logger = logging.getLogger(__name__)

class VirtualBus(LineTransportListener):
    """
    VirtualBus shares a transport channel with multiple listeners.

    Every request is forwarded to all participants which then decide whether they're going to
    respond to it. In case multiple peripherals would try to respond a bus contention error is
    sent to all nodes.
    """

    def __init__(self) -> None:
        self.members = []

    def add(self, listener: LineTransportListener):
        self.members.append(listener)

    def on_request(self, request: int) -> List[int]:
        response = None
        for member in self.members:
            r = member.on_request(request)

            if r != None and response != None:
                # TODO: notify of error rather than exception
                raise RuntimeError('Bus contention')
            
            if r != None:
                response = r

        return response

    def on_request_complete(self, request: int, data: List[int]):
        for member in self.members:
            member.on_request_complete(request, data)

    def on_error(self, error_type: str):
        for member in self.members:
            member.on_error(error_type)

class SimulatedPeripheral(LineTransportListener):

    def __init__(self, node: Node) -> None:
        self.node = node
        self.connected = True

        self.address = node.address
        self.requests = SimpleNamespace()
        self._op_status = None
        self._power_status = None
        self._software_version = None
        self._serial_number = None

        for request in node.publishes:
            signals = SimpleNamespace()
            for signal in request.signals:
                signals.__setattr__(signal.name, signal.initial)
            self.requests.__setattr__(request.name, signals)

    def on_request(self, request: int) -> List[int]:
        if self.connected is False:
            return None

        # Application
        for x in self.node.publishes:
            if x.id == request:
                return x.encode(vars(self.requests.__getattribute__(x.name)))

        # Diagnostics
        if self.address is None or self.address == LINE_DIAG_UNICAST_UNASSIGNED_ID:
            return None

        if request == LINE_DIAG_REQUEST_OP_STATUS | self.address:
            if self._op_status is not None:
                return [self._op_status]
            else:
                return None
        elif request == LINE_DIAG_REQUEST_SERIAL_NUMBER | self.address:
            if self._serial_number is not None:
                return list(int.to_bytes(self._serial_number, 4, 'little'))
            else:
                return None
        elif request == LINE_DIAG_REQUEST_SW_NUMBER | self.address:
            if self._software_version is not None:
                return [self._software_version[0], self._software_version[1], self._software_version[2]]
            else:
                return None
        elif request == LINE_DIAG_REQUEST_POWER_STATUS | self.address:
            if self._power_status is not None:
                return [self._power_status.voltage,
                        self._power_status.op_current & 0xFF, self._power_status.op_current >> 8,
                        self._power_status.sleep_current]
            else:
                return None
        
        return None

    def on_request_complete(self, request: int, data: List[int]):
        if self.connected is False:
            return

        if request == LINE_DIAG_REQUEST_WAKEUP:
            self.on_wakeup()
        elif request == LINE_DIAG_REQUEST_IDLE:
            self.on_idle()
        elif request == LINE_DIAG_REQUEST_SHUTDOWN:
            self.on_shutdown()
        elif request == LINE_DIAG_REQUEST_COND_CHANGE_ADDRESS:
            target = int.from_bytes(data[0:4], 3)
            if self._serial_number == target:
                old = self.address
                self.address = target[4]
                self.on_conditional_change_address(old, self.address)
            elif self.address == target[4]:
                self.address = LINE_DIAG_UNICAST_UNASSIGNED_ID
                # TODO: callout unassign
        else:
            for s in self.node.subscribes:
                if s.id == request:
                    signals = s.decode(data)
                    self.on_subscriber_event(s, signals)

    def on_error(self, error_type: str):
        pass

    # Diagnostic properties

    @property
    def op_status(self) -> int:
        return self._op_status
    
    @op_status.setter
    def op_status(self, value: Union[int, str]) -> None:
        if isinstance(value, str):
            self._op_status = op_status_code(value)
        else:
            self._op_status = value

    @property
    def power_status(self) -> 'PowerStatus':
        return self._power_status
    
    @property
    def software_version(self) -> str:
        return sw_version_str(self._software_version) if self._software_version else None
    
    @software_version.setter
    def software_version(self, value: str) -> None:
        if isinstance(value, str):
            parts = value.split('.')
            if len(parts) != 3:
                raise ValueError('Software version must be in format "major.minor.patch"')
            self._software_version = [int(part) for part in parts]
        else:
            self._software_version = value

    @property
    def serial_number(self) -> int:
        return self._serial_number
    
    @serial_number.setter
    def serial_number(self, value: int) -> None:
        self._serial_number = value

    def on_subscriber_event(self, request: Request, signals: Dict[str, Union[int, str, float]]):
        pass

    # Diagnostic events

    def on_wakeup(self):
        """
        Called when the peripheral is woken up from sleep mode.
        """
        pass

    def on_idle(self):
        """
        Called when the peripheral is put into idle mode.
        """
        pass

    def on_shutdown(self):
        """
        Called when the peripheral is put into shutdown mode.
        """
        pass

    def on_conditional_change_address(self, old: int, new: int):
        pass
