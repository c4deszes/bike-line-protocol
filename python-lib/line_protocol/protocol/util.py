from typing import List
from .constants import LINE_SYNC_BYTE

def request_code(request: int):
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

    return (((parity1 << 1) | parity2) << 13) | (request & 0x3FFF)

def data_checksum(data) -> int:
    return (sum(data) + len(data)) % 256

def create_header(request: int) -> bytearray:
    # request = request_code(request)
    return bytearray([LINE_SYNC_BYTE, (request & 0xFF00) >> 8, request & 0xFF])

def create_frame(request: int, data: List[int]) -> bytearray:
    request = request_code(request)
    checksum = data_checksum(data)
    return bytearray([LINE_SYNC_BYTE,
                      (request & 0xFF00) >> 8,
                      request & 0xFF,
                      len(data)] + data +
                      [checksum])
