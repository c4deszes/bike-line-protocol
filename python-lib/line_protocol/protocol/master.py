from typing import Literal, List, Union, TYPE_CHECKING
from types import SimpleNamespace
import logging
import argparse
import sys
import time

from .constants import *
from ..monitor.config import SignalRef
if TYPE_CHECKING:
    from .transport import LineSerialTransport
    from ..network import Network
    from ..monitor.measurement import SignalListener

logger = logging.getLogger(__name__)

class LineMaster():

    def __init__(self, transport: 'LineSerialTransport', network: 'Network' = None) -> None:
        self.transport = transport
        self.network = network
        self.listener = None
        self.requests = {}
        if network:
            for request in network.requests:
                self.requests[request.name] = {}
                for signal in request.signals:
                    # TODO: initial value support
                    self.requests[request.name][signal.name] = 0

    def add_listener(self, listener: 'SignalListener'):
        self.listener = listener

    def request_data(self, id: str):
        request = self.network.get_request(id)
        data = self.transport.request_data(request.id)
        signals = request.decode(data)

        if self.listener:
            current_time = time.time()
            for (name, value) in signals.items():
                self.listener.on_signal(current_time, SignalRef(request, request.get_signal(name)), value)

        strings = []
        for (name, value) in signals.items():
            self.requests[request.name][name] = value
            strings.append(f"{name}={value}")
        logger.debug('%s', ', '.join(strings))

        # TODO: support for

    def send_data(self, request, data):
        self.transport.send_data(request, data)

    def request(self, request):
        return self.transport.request_data(request)

    def wakeup(self):
        """
        Sends a wakeup request to all peripherals
        """
        self.transport.send_data(LINE_DIAG_REQUEST_WAKEUP, [])
        logger.info("Wakeup.")

    def sleep(self):
        """
        Sends all peripherals to sleep
        """
        self.transport.send_data(LINE_DIAG_REQUEST_SLEEP, [])
        logger.info("Go to sleep.")

    def shutdown(self):
        """
        Sends a shutdown request to all peripherals
        """
        self.transport.send_data(LINE_DIAG_REQUEST_SHUTDOWN, [])
        logger.info("Shutdown.")

    def conditional_change_address(self, serial: int, new_address: int):
        self.transport.send_data(LINE_DIAG_REQUEST_COND_CHANGE_ADDRESS, list(int.to_bytes(serial, 4, 'little')) + [new_address])
        logger.info("Assigned Node=%01X to SN=0x%08X", new_address, serial)

    def diag_unicast_request(self, diag_code, id: int) -> List[int]:
        return self.transport.request_data(diag_code | id)

    def get_operation_status(self, id: int) -> Literal['init', 'ok', 'warn', 'error', 'boot', 'boot_error']:
        response = self.diag_unicast_request(LINE_DIAG_REQUEST_OP_STATUS, id)
        if len(response) != 1:
            logger.error('Unexpected response to op. status request! %s', response)
            raise ValueError('Unexpected response.')
        status = 'INVALID'
        if response[0] == LINE_DIAG_OP_STATUS_INIT:
            status = 'init'
        if response[0] == LINE_DIAG_OP_STATUS_OK:
            status = 'ok'
        elif response[0] == LINE_DIAG_OP_STATUS_WARN:
            status = 'warn'
        elif response[0] == LINE_DIAG_OP_STATUS_ERROR:
            status = 'error'
        elif response[0] == LINE_DIAG_OP_STATUS_BOOT:
            status = 'boot'
        elif response[0] == LINE_DIAG_OP_STATUS_BOOT_ERROR:
            status = 'boot_error'
        logger.info('Node=%01X, Status=%s', id, status)
        return status

    def get_power_status(self, id: int):
        response = self.diag_unicast_request(LINE_DIAG_REQUEST_POWER_STATUS, id)
        if response[0] == LINE_DIAG_POWER_STATUS_VOLTAGE_OK:
            volts_status = 'ok'
        elif response[0] == LINE_DIAG_POWER_STATUS_VOLTAGE_LOW:
            volts_status = 'low'
        elif response[0] == LINE_DIAG_POWER_STATUS_VOLTAGE_HIGH:
            volts_status = 'high'
        else:
            volts_status = 'invalid'

        if response[1] == LINE_DIAG_POWER_STATUS_BOD_NONE:
            bod_status = 'none'
        elif response[1] == LINE_DIAG_POWER_STATUS_BOD_DETECTED:
            bod_status = 'detected'

        # TODO: move conversion elsewhere
        op_current = (response[2] * 25) / 1000.0
        sleep_current = (response[3] * 10)

        logger.info('Node=%01X, Voltage=%s, BOD=%s, I_op=%.02fA, I_sleep=%.02fuA', id, volts_status, bod_status, op_current, sleep_current)
        # TODO: return

    def get_serial_number(self, id: int) -> int:
        response = self.diag_unicast_request(LINE_DIAG_REQUEST_SERIAL_NUMBER, id)
        sn = int.from_bytes(response, byteorder='little')

        logger.info('Node=%01X, Serial=%s', id, hex(sn))

        return sn

    def get_software_version(self, id: int) -> str:
        response = self.diag_unicast_request(LINE_DIAG_REQUEST_SW_NUMBER, id)
        sw_version = f"{response[0]}.{response[1]}.{response[2]}"

        logger.info('Node=%01X, SW_Version=%s', id, sw_version)

        return sw_version
