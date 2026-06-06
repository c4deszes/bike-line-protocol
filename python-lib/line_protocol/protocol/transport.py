# System imports
from typing import List
import logging
import time

# Third-party imports
import serial

# Local imports
from line_protocol.protocol.util import create_frame, create_header, data_checksum
from line_protocol.protocol.constants import *

logger = logging.getLogger(__name__)

class LineTransportError(Exception):
    "Common exception type for transport errors"
    pass

class LineTransportTimeout(LineTransportError):
    """Raised when no response is received"""
    pass

class LineTransportRequestError(LineTransportError):
    """Raised when the request code parity is wrong"""
    pass

class LineTransportDataError(LineTransportError):
    """Raised when the data section of the response is invalid"""
    pass

class LineTrafficListener():
    """
    Interface for listening to traffic events
    """

    def on_request(self, timestamp: float, request: int, size: int, data: List[int], checksum: int):
        """Called when a complete request is received"""
        raise NotImplementedError()

    def on_error(self, timestamp: float, request: int, error: LineTransportError):
        """Called when an error occurs on the bus"""
        raise NotImplementedError()

class LineTransportListener():
    """
    Interface for devices listening and responding to bus events, effectively this is the same as
    the peripheral interface
    """

    def on_request(self, request: int) -> List[int] | None:
        """Called when a request is received"""
        raise NotImplementedError()

    def on_request_complete(self, request: int, data: List[int]):
        """Called when a request has been responded to"""
        raise NotImplementedError()

    def on_error(self, request: int, error_type: str):
        """Called when an error occurs on the bus (invalid request, bad checksum, timeout)"""
        raise NotImplementedError()

class LineSerialTransport():

    def __init__(self, port: str, baudrate: int = 19200, one_wire: bool = True) -> None:
        self.port = port
        self.baudrate = baudrate
        self.one_wire = one_wire
        self._serial = serial.Serial(None, self.baudrate, timeout=0.001)

    def __enter__(self) -> 'LineSerialTransport':
        self._serial.port = self.port
        self._serial.open()
        return self

    def request_data(self, request: int) -> List[int]:
        header = create_header(request)
        self._serial.write(header)
        #logger.debug("TX REQ 0x%04X", request)

        if self.one_wire:
            received = 0
            start = time.time()
            # TODO: timeout to prevent infinite loop
            while received < len(header):
                data = self._serial.read(1)
                if len(data) == 1:
                    received += 1
                if time.time() - start > 1.0:
                    #logger.error('RX No self response received!')
                    raise LineTransportTimeout("Self response timeout.")

        start = time.time()
        size = None
        while time.time() - start < LINE_REQUEST_TIMEOUT:
            a = self._serial.read(1)
            if len(a) == 1:
                size = a[0]
                break

        if size is None:
            #logger.error('RX Timeout!')
            raise LineTransportTimeout()

        data = []
        while time.time() - start < LINE_DATA_TIMEOUT and len(data) < size:
            a = self._serial.read(1)
            if len(a) == 1:
                data.append(a[0])
                start = time.time()

        if len(data) != size:
            #logger.error('RX Timeout! LEN=%d DATA=%s', size, data)
            raise LineTransportTimeout()

        checksum = None
        start = time.time()
        while time.time() - start < LINE_DATA_TIMEOUT:
            a = self._serial.read(1)
            if len(a) == 1:
                checksum = a[0]
                break

        if checksum is None:
            #logger.debug("RX LEN=%d DATA=%s", size, data)
            #logger.error('RX Timeout! No checksum received.')
            raise LineTransportTimeout('Missing checksum.')

        #logger.debug("RX LEN=%d DATA=%s CHK=%02X", size, data, checksum)
        if data_checksum(data) != checksum:
            #logger.error('RX Checksum error!')
            raise LineTransportDataError('Invalid checksum.')

        return data

    def send_data(self, request: int, data: List[int], checksum: int | None = None):
        frame = create_frame(request, data, checksum)

        self._serial.write(frame)
        #logger.debug("TX REQ 0x%04X LEN=%d DATA=%s CHK=%s",
        #             request, len(data), data, 'ok' if checksum is None else hex(checksum))

        time.sleep(0.1)

        if self.one_wire:
            self._serial.read(len(frame))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._serial.close()
