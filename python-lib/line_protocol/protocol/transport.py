from typing import List
import serial
from .util import create_frame, create_header, data_checksum
import logging
import time
from .constants import LINE_REQUEST_TIMEOUT, LINE_DATA_TIMEOUT

logger = logging.getLogger(__name__)

class LineTransportError(Exception):
    pass

class LineTransportTimeout(LineTransportError):
    pass

class LineTransportRequestError(LineTransportError):
    pass

class LineTransportDataError(LineTransportError):
    pass

class TransportListener():

    def on_request(self, timestamp, request: int, size: int, data: List[int], checksum: int):
        raise NotImplementedError()

    def on_error(self, timestamp, request: int, error_type: str):
        raise NotImplementedError()

class LineSerialTransport():

    def __init__(self, port: str, baudrate: int = 19200, one_wire: bool = True) -> None:
        self.port = port
        self.baudrate = baudrate
        self.one_wire = one_wire
        self.listener = None
        self._serial = serial.Serial(None, self.baudrate, timeout=0.001)

    def __enter__(self) -> 'LineSerialTransport':
        self._serial.port = self.port
        self._serial.open()
        return self
    
    def add_listener(self, listener: TransportListener):
        self.listener = listener

    def request_data(self, request: int) -> List[int]:
        header = create_header(request)
        self._serial.write(header)
        logger.debug("TX REQ 0x%04X", request)

        if self.one_wire:
            time.sleep(0.5)     # TODO: adjust duration
            self._serial.read(len(header))

        start = time.time()
        size = None
        while time.time() - start < LINE_REQUEST_TIMEOUT:
            a = self._serial.read(1)
            if len(a) == 1:
                size = a[0]
                break

        if size is None:
            logger.error('RX Timeout!')
            if self.listener:
                self.listener.on_error(start, request, 'timeout')
            raise LineTransportTimeout()
        
        data = []
        while time.time() - start < LINE_DATA_TIMEOUT and len(data) < size:
            a = self._serial.read(1)
            if len(a) == 1:
                data.append(a[0])
                start = time.time()

        if len(data) != size:
            logger.error('RX Timeout! LEN=%d DATA=%s', size, data)
            if self.listener:
                self.listener.on_error(start, request, 'incomplete-response')
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
            if self.listener:
                self.listener.on_error(start, request, 'incomplete-response')
            raise LineTransportTimeout()

        logger.debug("RX LEN=%d DATA=%s CHK=%02X", size, data, checksum)

        if data_checksum(data) != checksum:
            logger.error('RX Checksum error!')
            if self.listener:
                self.listener.on_error(start, request, 'checksum error')
            raise LineTransportDataError('Invalid checksum.')
        
        if self.listener:
            self.listener.on_request(start, request, size, data, checksum)

        return data

    def send_data(self, request: int, data: List[int], checksum: int = None):
        frame = create_frame(request, data, checksum)

        self._serial.write(frame)
        logger.debug("TX REQ 0x%04X LEN=%d DATA=%s CHK=%s", request, len(data), data, 'ok' if checksum is None else hex(checksum))
        
        time.sleep(0.1)
        # TODO: only read in one wire mode
        if self.one_wire:
            self._serial.read(len(frame))

        if self.listener:
            self.listener.on_request(time.time(), request, len(data), data, checksum)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._serial.close()
