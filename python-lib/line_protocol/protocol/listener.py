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

class LineSerialSniffer():

    def __init__(self, port: str, baudrate: int = 19200, one_wire: bool = True) -> None:
        self.port = port
        self.baudrate = baudrate
        self.one_wire = one_wire
        self._serial = serial.Serial(None, self.baudrate, timeout=0.00001)
        self.traffic_listeners = []

    def __enter__(self) -> 'LineSerialSniffer':
        self._serial.port = self.port
        self._serial.open()
        return self

    def add_traffic_listener(self, listener: LineTrafficListener):
        self.traffic_listeners.append(listener)

    # enters loop to monitor traffic
    def listen(self, listener: LineTransportListener | None = None):
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
                    request = received << 8
                    state = 'wait_request_lsb'
                elif state == 'wait_request_lsb':
                    request |= received
                    # TODO: cleanup
                    if request_code(request & LINE_REQUEST_PARITY_MASK) != request:
                        logger.error("RX Request parity error! 0x%04X", request)
                        if listener:
                            listener.on_error('header_error')

                        for traffic_listener in self.traffic_listeners:
                            traffic_listener.on_error(timestamp,
                                                      request & LINE_REQUEST_PARITY_MASK,
                                                      'header_error')

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
                    logger.debug("%s LEN=%d DATA=%s CHK=%02X",
                                 'TX' if responding else 'RX', size, frame, checksum)

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