from line_protocol.protocol.transport import LineSerialTransport
from line_protocol.protocol.master import LineMaster
import logging

logging.basicConfig(level=logging.DEBUG)

with LineSerialTransport('COM4', baudrate=19200, one_wire=True) as transport:
    master = LineMaster(transport)

    master.wakeup()
    master.get_operation_status(0x1)
    master.get_power_status(0x1)
    master.get_serial_number(0x1)
    master.get_software_version(0x1)
