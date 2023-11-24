from line_protocol.protocol.transport import LineSerialTransport
from line_protocol.protocol.master import LineMaster
import logging
import time

logging.basicConfig(level=logging.DEBUG)

with LineSerialTransport('COM4', baudrate=19200, one_wire=True) as transport:
    master = LineMaster(transport)

    #master.wakeup()
    #master.get_operation_status(0)

    #master.get_operation_status(0x4)
    #master.get_power_status(0x4)
    master.get_serial_number(0x4)
    #master.get_software_version(0x4)
    time.sleep(0.001)
    master.transport.send_data(0x1200, [0x00])
    
    # master.transport.request_data(0x1006)

    # for _ in range(5):
    #     master.transport.send_data(0x1200, [0x00])
    #     time.sleep(0.5)
    #     master.transport.request_data(0x1000)
    #     time.sleep(0.1)
    #     master.transport.send_data(0x1200, [0x01])
    #     time.sleep(0.5)
