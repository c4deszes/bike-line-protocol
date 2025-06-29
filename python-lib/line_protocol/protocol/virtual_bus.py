import logging
from typing import List, Union, TYPE_CHECKING, Dict
from types import SimpleNamespace
from dataclasses import dataclass

from line_protocol.protocol.transport import LineTransportListener
from line_protocol.protocol.util import op_status_code, op_status_str, sw_version_str
from line_protocol.network.nodes import Node
from line_protocol.protocol.constants import *
from line_protocol.network import Request

logger = logging.getLogger(__name__)

class VirtualBus(LineTransportListener):
    """
    VirtualBus shares a transport channel with multiple listeners.

    Every request is forwarded to all participants which then decide whether they're going to
    respond to it. In case multiple peripherals would try to respond a bus contention error is
    sent to all nodes.
    """

    def __init__(self) -> None:
        self.members: List[LineTransportListener] = []

    def add(self, listener: LineTransportListener):
        """
        Adds a listener to the virtual bus.
        This listener will receive all requests sent to the bus and can respond to them.

        :param listener: Listener to add to the bus
        :type listener: LineTransportListener
        """
        self.members.append(listener)

    def on_request(self, request: int) -> List[int] | None:
        """
        Handles a request by forwarding it to all members of the bus.
        If multiple members respond, a bus contention error is raised.

        :param request: Request code
        :type request: int
        :return: Response data from the member that responded
        :rtype: List[int]
        """
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
        """
        Handles the completion of a request by notifying all members of the bus.
        This method is called when a request has been processed and the data is ready to be sent
        back to the requester.
        This is typically used to notify all members that a request has been completed and to
        provide them with the data that was returned.

        :param request: Request code that was processed
        :type request: int
        :param data: Data returned by the member that processed the request
        :type data: List[int]
        """
        for member in self.members:
            member.on_request_complete(request, data)

    def on_error(self, request: int, error_type: str):
        """
        Handles an error that occurred during the processing of a request.
        This method is called when an error occurs while processing a request. It notifies all
        members of the bus about the error, allowing them to handle it appropriately.

        :param request: Request code that caused the error
        :type request: int
        :param error_type: Type of error that occurred, e.g., 'bus contention', 'timeout', etc.
        :type error_type: str
        """
        for member in self.members:
            member.on_error(request, error_type)

