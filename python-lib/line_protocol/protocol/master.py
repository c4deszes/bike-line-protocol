from typing import Literal
from .transport import LineSerialTransport
from .constants import *

class LineMaster():

    def __init__(self, transport: LineSerialTransport) -> None:
        self.transport = transport

    def wakeup(self):
        self.transport.send_data(LINE_DIAG_REQUEST_WAKEUP, [])
    
    def sleep(self):
        self.transport.send_data(LINE_DIAG_REQUEST_SLEEP, [])
    
    def shutdown(self):
        self.transport.send_data(LINE_DIAG_REQUEST_SHUTDOWN, [])
    
    def get_operation_status(self, id: int) -> Literal['ok', 'warn', 'error']:
        self.transport.request_data(0x0110 | id)

    def get_power_status(self, id: int):
        raise NotImplementedError()

    def get_serial_number(self, id: int) -> int:
        raise NotImplementedError()
    
    def get_software_version(self, id: int) -> str:
        self.transport.request_data(0x0140 | id)
