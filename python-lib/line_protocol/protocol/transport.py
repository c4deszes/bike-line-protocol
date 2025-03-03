from typing import List
import serial
from .util import create_frame, create_header, data_checksum, request_code
import logging
import time
from .constants import *

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

    def on_request(self, timestamp, request: int, size: int, data: List[int], checksum: int):
        """Called when a complete request is received"""
        raise NotImplementedError()

    def on_error(self, timestamp, request: int, error_type: str):
        """Called when an error occurs on the bus"""
        raise NotImplementedError()
    
class LineTransportListener():
    """
    Interface for devices listening and responding to bus events, effectively this is the same as
    the peripheral interface
    """

    def on_request(self, request: int) -> List[int]:
        """Called when a request is received"""
        raise NotImplementedError()

    def on_request_complete(self, request: int, data: List[int]):
        """Called when a request has been responded to"""
        raise NotImplementedError()

    def on_error(self, error_type: str):
        """Called when an error occurs on the bus (invalid request, bad checksum, timeout)"""
        raise NotImplementedError()
    
class LineTransportImpl():

    def listen(self, listener: LineTransportListener):
        raise NotImplementedError()
    
    def request(self, request: int):
        pass

class LineSerialSniffer():

    def __init__(self, port: str, baudrate: int = 19200, one_wire: bool = True) -> None:
        self.port = port
        self.baudrate = baudrate
        self.one_wire = one_wire
        self._serial = serial.Serial(None, self.baudrate, timeout=0.00001)
        self.traffic_listeners = []

    def __enter__(self) -> 'LineSerialTransport':
        self._serial.port = self.port
        self._serial.open()
        return self
    
    def add_traffic_listener(self, listener: LineTrafficListener):
        self.traffic_listeners.append(listener)

    # enters loop to monitor traffic
    def listen(self, listener: LineTransportListener = None):
        state = 'wait_sync'
        request = None
        responding = False
        size = 0
        frame = []
        checksum = 0
        timestamp = time.time()

        # TODO: add stop signal
        while True:
            data = self._serial.read(1)

            if len(data) == 1:
                timestamp = time.time()
                received = data[0]
                if state == 'wait_sync' and received != LINE_SYNC_BYTE:
                    logger.debug('RX Garbled data 0x%02X', received)
                elif state == 'wait_sync' and received == LINE_SYNC_BYTE:
                    state = 'wait_request_msb'
                elif state == 'wait_request_msb':
                    request = (received << 8)
                    state = 'wait_request_lsb'
                elif state == 'wait_request_lsb':
                    request |= received
                    # TODO: cleanup
                    if request_code(request & LINE_REQUEST_PARITY_MASK) != request:
                        logger.error("RX Request parity error! 0x%04X", request)
                        if listener:
                            listener.on_error('header_error')

                        for traffic_listener in self.traffic_listeners:
                            traffic_listener.on_error(timestamp, request & LINE_REQUEST_PARITY_MASK, 'header_error')

                        state = 'wait_sync'
                        frame = bytearray()
                        request = None
                        responding = False
                        checksum = 0
                    else:
                        request = request  & LINE_REQUEST_PARITY_MASK

                        logger.debug("RX Request 0x%04X", request)

                        if listener:
                            response = listener.on_request(request)

                            if response != None:
                                checksum = data_checksum(response)
                                self._serial.write([len(response)] + response + [checksum])
                                if self.one_wire:
                                    state = 'wait_size'
                                    responding = True
                                else:
                                    state = 'wait_sync'
                                    frame = bytearray()
                                    request = None
                                    responding = False
                                    checksum = 0
                            else:
                                state = 'wait_size'
                        else:
                            state = 'wait_size'

                elif state == 'wait_size':
                    size = received
                    state = 'wait_data'
                elif state == 'wait_data':
                    frame.append(received)
                    if len(frame) >= size:
                        state = 'wait_checksum'
                elif state == 'wait_checksum':
                    checksum = received
                    logger.debug("%s LEN=%d DATA=%s CHK=%02X", 'TX' if responding else 'RX', size, frame, checksum)

                    if data_checksum(frame) == checksum:
                        if listener:
                            listener.on_request_complete(request, frame)

                        for traffic_listener in self.traffic_listeners:
                            traffic_listener.on_request(timestamp, request, size, frame, checksum)
                    else:
                        logger.error("RX Data checksum error.")
                        if listener:
                            listener.on_error('checksum_error')

                        for traffic_listener in self.traffic_listeners:
                            traffic_listener.on_error(timestamp, request, 'checksum_error')

                    state = 'wait_sync'
                    frame = []
                    request = None
                    checksum = 0
                    responding = False

            if state != 'wait_sync' and time.time() - timestamp > LINE_DATA_TIMEOUT:
                logger.error("RX Timeout.")
                state = 'wait_sync'
                responding = False
                if listener:
                    listener.on_error('timeout')
                # TODO: what should request value be?
                for traffic_listener in self.traffic_listeners:
                    traffic_listener.on_error(timestamp, request, 'timeout')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._serial.close()

# TODO: this class shall be replaced in favor of the bus listening solution
class LineSerialTransport():

    def __init__(self, port: str, baudrate: int = 19200, one_wire: bool = True) -> None:
        self.port = port
        self.baudrate = baudrate
        self.one_wire = one_wire
        self.traffic_listeners = []
        self._serial = serial.Serial(None, self.baudrate, timeout=0.001)

    def __enter__(self) -> 'LineSerialTransport':
        self._serial.port = self.port
        self._serial.open()
        return self
    
    def add_listener(self, listener: LineTrafficListener):
        self.traffic_listeners.append(listener)

    def request_data(self, request: int) -> List[int]:
        header = create_header(request)
        self._serial.write(header)
        logger.debug("TX REQ 0x%04X", request)

        if self.one_wire:
            received = 0
            start = time.time()
            # TODO: timeout to prevent infinite loop
            while received < len(header):
                data = self._serial.read(1)
                if len(data) == 1:
                    received += 1
                if time.time() - start > 1.0:
                    logger.error('RX No self response received!')
                    raise LineTransportTimeout("Self response timeout.")

        start = time.time()
        size = None
        while time.time() - start < LINE_REQUEST_TIMEOUT:
            a = self._serial.read(1)
            if len(a) == 1:
                size = a[0]
                break

        if size is None:
            logger.error('RX Timeout!')
            for traffic_listener in self.traffic_listeners:
                traffic_listener.on_error(start, request, 'timeout')
            raise LineTransportTimeout()
        
        data = []
        while time.time() - start < LINE_DATA_TIMEOUT and len(data) < size:
            a = self._serial.read(1)
            if len(a) == 1:
                data.append(a[0])
                start = time.time()

        if len(data) != size:
            logger.error('RX Timeout! LEN=%d DATA=%s', size, data)
            for traffic_listener in self.traffic_listeners:
                traffic_listener.on_error(start, request, 'incomplete-response')
            raise LineTransportTimeout()
        
        checksum = None
        start = time.time()
        while time.time() - start < LINE_DATA_TIMEOUT:
            a = self._serial.read(1)
            if len(a) == 1:
                checksum = a[0]
                break

        if checksum is None:
            logger.debug("RX LEN=%d DATA=%s", size, data)
            logger.error('RX Timeout! No checksum received.')
            for traffic_listener in self.traffic_listeners:
                traffic_listener.on_error(start, request, 'incomplete-response')
            raise LineTransportTimeout()

        logger.debug("RX LEN=%d DATA=%s CHK=%02X", size, data, checksum)

        if data_checksum(data) != checksum:
            logger.error('RX Checksum error!')
            for traffic_listener in self.traffic_listeners:
                traffic_listener.on_error(start, request, 'checksum error')
            raise LineTransportDataError('Invalid checksum.')
        
        for traffic_listener in self.traffic_listeners:
            traffic_listener.on_request(start, request, size, data, checksum)

        return data

    def send_data(self, request: int, data: List[int], checksum: int = None):
        frame = create_frame(request, data, checksum)

        self._serial.write(frame)
        logger.debug("TX REQ 0x%04X LEN=%d DATA=%s CHK=%s", request, len(data), data, 'ok' if checksum is None else hex(checksum))
        
        time.sleep(0.1)

        if self.one_wire:
            self._serial.read(len(frame))

        for traffic_listener in self.traffic_listeners:
            traffic_listener.on_request(time.time(), request, len(data), data, checksum)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._serial.close()
