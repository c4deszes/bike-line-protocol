from line_protocol.protocol.transport import LineSerialTransport
from line_protocol.protocol.master import LineMaster
import logging

logging.basicConfig(level=logging.DEBUG)

with LineSerialTransport('COM4', baudrate=19200, one_wire=True) as transport:
    master = LineMaster(transport)

    #master.wakeup()
    #master.get_operation_status(0)

    #master.transport._serial.write([0x55])
    #master.transport.request_data(0x1006)
    master.transport.send_data(0x1200, [0x00])
