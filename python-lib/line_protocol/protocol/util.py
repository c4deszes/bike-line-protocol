from typing import List, Literal
from .constants import *

def request_code(request: int):
    if request > LINE_REQUEST_PARITY_MASK or request < 0:
        return ValueError('Invalid request code.')

    parity1 = 0
    tempData = request
    while tempData != 0:
        parity1 ^= (tempData & 1)
        tempData >>= 1

    parity2 = 0
    tempData = request
    for i in range(6):
        parity2 ^= (tempData & 1)
        tempData >>= 2

    return (((parity1 << 1) | parity2) << LINE_REQUEST_PARITY_POS) | (request & LINE_REQUEST_PARITY_MASK)

def data_checksum(data) -> int:
    return (LINE_DATA_CHECKSUM_OFFSET + sum(data) + len(data)) % 256

def create_header(request: int) -> bytearray:
    request = request_code(request)
    return bytearray([LINE_SYNC_BYTE, (request & 0xFF00) >> 8, request & 0xFF])

def create_frame(request: int, data: List[int], checksum: int = None) -> bytearray:
    request = request_code(request)
    checksum = data_checksum(data) if checksum is None else checksum
    return bytearray([LINE_SYNC_BYTE,
                      (request & 0xFF00) >> 8,
                      request & 0xFF,
                      len(data)] + data +
                      [checksum])

OperationStatus = Literal['Init', 'Ok', 'Warn', 'Error', 'Boot', 'BootError']

def op_status(status: int) -> OperationStatus:
    if status == LINE_DIAG_OP_STATUS_INIT:
        return 'Init'
    if status == LINE_DIAG_OP_STATUS_OK:
        return 'Ok'
    elif status == LINE_DIAG_OP_STATUS_WARN:
        return 'Earn'
    elif status == LINE_DIAG_OP_STATUS_ERROR:
        return 'Error'
    elif status == LINE_DIAG_OP_STATUS_BOOT:
        return 'Boot'
    elif status == LINE_DIAG_OP_STATUS_BOOT_ERROR:
        return 'BootError'
    return 'INVALID'