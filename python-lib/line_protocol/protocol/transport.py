from typing import List
import serial
from .util import create_frame, create_header, request_code
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

class LineSerialTransport():

    def __init__(self, port: str, baudrate: int = 19200, one_wire: bool = True) -> None:
        # TODO: add one wire option
        self.port = port
        self.baudrate = baudrate
        self.one_wire = one_wire
        self._serial = serial.Serial(None, self.baudrate, timeout=0.001)

    def __enter__(self) -> 'LineSerialTransport':
        self._serial.port = self.port
        self._serial.dtr = False
        self._serial.open()
        return self

    def request_data(self, request: int) -> List[int]:
        header = create_header(request)
        self._serial.write(header)
        logger.debug("TX DATA %s", hex(int.from_bytes(header)))
        logger.debug("TX REQ 0x%04X", request)

        if self.one_wire:
            time.sleep(0.1)
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
            raise LineTransportTimeout()
        
        data = []
        while time.time() - start < LINE_DATA_TIMEOUT and len(data) < size:
            a = self._serial.read(1)
            if len(a) == 1:
                data.append(a)

        if len(data) != size:
            logger.error('RX Timeout! data=%s', data)
            raise LineTransportTimeout()

        logger.debug("RX LEN=%d DATA=%s", size, data)

        return data

    def send_data(self, request: int, data: List[int]):
        frame = create_frame(request, data)

        self._serial.write(frame)
        logger.debug("TX REQ 0x%04X LEN=%d DATA=%s", request, len(data), data)
        
        time.sleep(0.1)
        # TODO: only read in one wire mode
        self._serial.read(len(frame))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._serial.close()
