from typing import Literal, List, Union
from .transport import LineSerialTransport
from .constants import *
from ..network import Network
from types import SimpleNamespace
import logging
import argparse
import sys

logger = logging.getLogger(__name__)

class LineMaster():

    def __init__(self, transport: LineSerialTransport) -> None:
        self.transport = transport

    def setup(self, network: Network):
        self.network = network
        self.requests = SimpleNamespace()

    def request_data(self, id: Union[int, str]):
        data = self.transport.request_data(id)

    # def send_data(self, id, data):
    #     pass

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

    def diag_unicast_request(self, diag_code, id: int) -> List[int]:
        return self.transport.request_data(diag_code | id)

    def get_operation_status(self, id: int) -> Literal['ok', 'warn', 'error']:
        response = self.diag_unicast_request(LINE_DIAG_REQUEST_OP_STATUS, id)
        if len(response) != 1:
            logger.error('Unexpected response to op. status request! %s', response)
            raise ValueError('Unexpected response.')
        if response[0] == LINE_DIAG_OP_STATUS_OK:
            status = 'ok'
        elif response[0] == LINE_DIAG_OP_STATUS_WARN:
            status = 'warn'
        elif response[0] == LINE_DIAG_OP_STATUS_ERROR:
            status = 'error'
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
