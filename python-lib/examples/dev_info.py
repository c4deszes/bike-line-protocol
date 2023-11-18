from line_protocol.protocol.transport import LineSerialTransport
from line_protocol.protocol.master import LineMaster
import logging
import time

logging.basicConfig(level=logging.DEBUG)

with LineSerialTransport('COM4', baudrate=19200, one_wire=True) as transport:
    master = LineMaster(transport)

    master.wakeup()
    #master.get_operation_status(0)
    
    # master.transport.request_data(0x1006)

    for _ in range(10):
        master.transport.send_data(0x1200, [0x00])
        time.sleep(0.5)
        master.transport.request_data(0x1006)
        time.sleep(0.5)
        master.transport.send_data(0x1200, [0x01])
        time.sleep(0.5)
