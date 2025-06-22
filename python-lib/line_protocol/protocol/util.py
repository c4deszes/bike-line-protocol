"""
Utility functions for the LINE protocol.
"""
from typing import List, Literal, Iterable, Sized

from line_protocol.protocol.constants import *

def request_code(request: int) -> int:
    """
    Generates a request code with parity bits for the LINE protocol.

    :param request: Request code
    :type request: int
    :return: Request code with parity bits
    :rtype: int
    """
    if request > LINE_REQUEST_PARITY_MASK or request < 0:
        raise ValueError('Invalid request code.')

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

def data_checksum(data: Iterable[int]) -> int:
    """
    Calculates the checksum for a given data list according to LINE protocol specifications.

    :param data: Request data as a list of integers
    :type data: _type_
    :return: Checksum value
    :rtype: int
    """
    return (LINE_DATA_CHECKSUM_OFFSET + sum(data) + len(data)) % 256

def create_header(request: int) -> bytearray:
    """
    Creates a header for a LINE protocol request that can be sent over the bus.

    Example:
    >>> create_header(LINE_DIAG_REQUEST_OP_STATUS)
    bytearray([0x55, 0x00, 0x01])

    :param request: Request code
    :type request: int
    :return: Header as a bytearray
    :rtype: bytearray
    """
    request = request_code(request)
    return bytearray([LINE_SYNC_BYTE, (request & 0xFF00) >> 8, request & 0xFF])

def create_frame(request: int, data: List[int], checksum: int | None = None) -> bytearray:
    """
    Creates a complete frame for a LINE protocol request that can be sent over the bus.

    Example:
    >>> create_frame(LINE_DIAG_REQUEST_OP_STATUS, [0x01])
    bytearray([0x55, 0x02, 0x00, 0x01, 0x01, 0xA5])

    :param request: Request code
    :type request: int
    :param data: Request data as a list of integers
    :type data: List[int]
    :param checksum: Checksum, calculated if not provided, defaults to None
    :type checksum: int, optional
    :return: Frame as a bytearray
    :rtype: bytearray
    """
    request = request_code(request)
    checksum = data_checksum(data) if checksum is None else checksum
    return bytearray([LINE_SYNC_BYTE,
                      (request & 0xFF00) >> 8,
                      request & 0xFF,
                      len(data)] + data +
                      [checksum])

OperationStatus = Literal['Init', 'Ok', 'Warn', 'Error', 'Boot', 'BootError']

# Bidirectional mapping for operation status
_OP_STATUS_MAP = {
    'Init': LINE_DIAG_OP_STATUS_INIT,
    'Ok': LINE_DIAG_OP_STATUS_OK,
    'Warn': LINE_DIAG_OP_STATUS_WARN,
    'Error': LINE_DIAG_OP_STATUS_ERROR,
    'Boot': LINE_DIAG_OP_STATUS_BOOT,
    'BootError': LINE_DIAG_OP_STATUS_BOOT_ERROR,
}
_OP_STATUS_MAP_INV = {v: k for k, v in _OP_STATUS_MAP.items()}

def op_status_code(status: OperationStatus) -> int:
    try:
        return _OP_STATUS_MAP[status]
    except KeyError:
        raise ValueError('Invalid operation status.')

def op_status_str(status: int) -> OperationStatus:
    return _OP_STATUS_MAP_INV.get(status, 'INVALID')

def sw_version_str(version: List[int]) -> str:
    """
    Converts a software version list to a string.

    :param version: Software version as a list of integers
    :type version: List[int]
    :return: Software version as a string
    :rtype: str
    """
    return '.'.join(str(x) for x in version if x is not None)
